---
name: twilio-voice
description: "Build Twilio voice bots: phone call → STT → LLM task processing → Venice TTS → voice response. Covers webhook architecture, FastAPI server, TwiML Gather, caller allowlisting, Venice TTS integration, and deployment."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Twilio, voice, TTS, STT, phone, Venice]
    related_skills: [venice-audio-speech, venice-audio-transcription, railway]
---

# Twilio Voice Integration

Build a phone-in AI agent: user calls a Twilio number, speaks a task, the agent processes it via LLM, and responds with synthesized speech via Venice TTS.

## Architecture

```
RECORD mode (default, STT_METHOD=record) — ASYNC POLLING PATTERN:
  Phone Call → Twilio → POST /voice (TwiML: Say greeting + <Record>)
                     → POST /process_recording (RecordingUrl)
                         ↓  IMMEDIATELY return TwiML: <Say>"Let me think."</Say> + <Play>hold_music</Play> + <Redirect>/check_response/{call_sid}</Redirect>
                         ↓  Background task (asyncio.create_task):
                             Download recording → Venice STT → Chat → Venice TTS
                             Store result in pending_responses[call_sid]
                         ↓  Twilio follows redirect to /check_response/{call_sid}:
                             If processing  → <Play>hold_music</Play> + <Redirect>/check_response/{call_sid}</Redirect> (loop)
                             If done        → <Play>TTS_audio</Play> + <Say>"Go ahead."</Say> + <Record> (next turn)
                             If error       → <Say>"Sorry..."</Say> + <Record> (next turn)

GATHER mode (fallback, STT_METHOD=gather) — SAME ASYNC PATTERN:
  Phone Call → Twilio → POST /voice (TwiML <Gather speech>)
                     → POST /process (SpeechResult text)
                         ↓  IMMEDIATELY return TwiML: <Say>"Let me think."</Say> + <Play>hold_music</Play> + <Redirect>/check_response/{call_sid}</Redirect>
                         ↓  Background task: Chat → TTS → store in pending_responses
                         ↓  /check_response/{call_sid} polls → plays audio or loops hold music
```

**⚠️ CRITICAL: Why async polling?** The full pipeline (download recording → Whisper STT → LLM → Venice TTS) takes **15-30+ seconds** in practice. Twilio's webhook timeout is ~15 seconds. A synchronous response causes Twilio to show "Application error has occurred" and hang up. The async pattern responds in <1 second, then uses hold music + polling loops to deliver the response when ready.

## Prerequisites

- Twilio account with a phone number (E.164 format like +18703747844)
- Twilio Account SID and Auth Token
- Venice AI API key (for TTS and chat)
- Publicly reachable server (Railway, ngrok for dev, etc.)
- Python 3.11+

## Quick Start

Use the `templates/hermes-voice-server.py` template to scaffold a new project:

```bash
mkdir my-voice-bot && cd my-voice-bot
cp ~/.hermes/skills/devops/twilio-voice/templates/hermes-voice-server.py main.py
# Edit .env with your credentials
pip install -r requirements.txt  # fastapi, uvicorn, twilio, httpx, python-dotenv
uvicorn main:app --host 0.0.0.0 --port 5000
```

## Twilio Configuration

### Option A: Via Twilio Console (Manual)

1. Go to Phone Numbers → Manage → Active numbers → click your number
2. Under "Voice Configuration", set:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://your-server.com/voice`
   - **Method**: HTTP POST
3. Save

### Option B: Via Twilio Python SDK (Automated)

```python
from twilio.rest import Client

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
numbers = client.incoming_phone_numbers.list(phone_number='+18703747844')
if numbers:
    numbers[0].update(
        voice_url='https://voice.example.com/voice',
        voice_method='POST'
    )
```

**Important notes:**
- The Python SDK uses `incoming_phone_numbers` (with underscores), NOT `incoming_phonenumbers`
- `list()` accepts `phone_number` as a filter parameter
- `update()` returns the updated object — verify with `updated.voice_url`

For development with ngrok:
```bash
ngrok http 5000
# Use the ngrok URL as your Twilio webhook
```

### Twilio Webhook Signatures (Security)

Always validate Twilio signatures in production:

```python
from twilio.request_validator import RequestValidator

def validate_twilio_request(request, url):
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    signature = request.headers.get("X-Twilio-Signature", "")
    params = dict(await request.form()) if hasattr(request, 'form') else {}
    return validator.validate(url, params, signature)
```

Skip validation during development; enforce in production.

## Key Design Decisions

### 1. Conversation Flow: Gather Loop vs Single-Shot

**Gather loop (recommended)**: After each response, ask "Anything else?" and loop back to `/voice`. This allows multi-turn calls.

**Single-shot**: One question, one answer, call ends. Simpler but limited.

### 2. TTS Strategy: Direct Play vs Cache

**Direct (short responses, <500 chars)**: Use Twilio's `<Say>` or generate Venice TTS audio and serve via `<Play>`.

**Cached (longer responses)**: Generate MP3 via Venice `/audio/speech`, cache with UUID filename, serve from `/audio_cache/{uuid}.mp3`. Faster on replay.

### STT: Twilio Gather vs Venice Transcription (Record)

**Method 1 — Twilio Gather** (`STT_METHOD=gather`): Twilio transcribes speech in real-time during `<Gather>` and sends `SpeechResult` in the webhook. Lowest latency but poor accuracy for accents, slang, and noisy environments. Callers with non-standard accents regularly get misunderstood.

**Method 2 — Venice Transcription** (`STT_METHOD=record`, **recommended**): Record audio via `<Record>`, download the recording from Twilio, transcribe with Venice `/audio/transcriptions`. Adds ~2-4s latency per turn but dramatically better comprehension for accents, slang, and real-world phone audio.

**Available STT models for Venice transcription:**
- `openai/whisper-large-v3` — Default. Large multilingual, highest accuracy, honors `language` hint. Best overall.
- `elevenlabs/scribe-v2` — Strong on noisy audio, good for phone calls with background noise.
- `nvidia/parakeet-tdt-0.6b-v3` — Fastest, English-first, good for real-time-ish flows.
- `stt-xai-v1` — xAI Speech-to-Text.

**Bottom line:** Use `STT_METHOD=record` with `openai/whisper-large-v3` for production phone bots. The 2-4s latency hit is acceptable — callers notice bad understanding far more than a brief pause. Switch to `gather` only if latency is absolutely critical.

**Architecture comparison:**

```
GATHER mode (STT_METHOD=gather):
  Call → Twilio <Gather> → POST /process (SpeechResult text) → Chat → TTS → <Play> → <Gather> loop

RECORD mode (STT_METHOD=record, recommended):
  Call → <Say greeting> → <Record> → POST /process_recording (RecordingUrl) 
       → Download recording from Twilio → Venice STT → Chat → TTS → <Play> → <Record> loop
```

**Recording URL auth:** Twilio recording URLs require HTTP Basic Auth with your Account SID and Auth Token. Append `.wav` to the URL for WAV format (better for STT). If WAV fails, fall back to the default format.

**Switching modes:** Set `STT_METHOD=record` (default) or `STT_METHOD=gather` as an env var. No code changes needed — the server supports both flows simultaneously.

## Venice Chat Integration (Phone Conversation)

### Reasoning Models and Token Budget

**Critical pitfall:** If using a reasoning/thinking model (like `mercury-2`), the model's internal chain-of-thought tokens count toward `max_tokens`. With `max_tokens: 256`, reasoning models spend ~90% of the budget on hidden thinking, leaving almost nothing for the visible response — producing empty or truncated output that falls through to "I wasn't able to generate a response."

**Fix — do both:**
1. Set `max_tokens: 4096+` so the model has full context understanding
2. Set `"disable_thinking": True` in `venice_parameters` so reasoning tokens don't consume the visible budget

**Recommended chat models for phone (speed prioritized):**
- `qwen3-5-9b` — **Fastest.** Small, snappy, good for brief phone responses. Best latency-to-quality ratio.
- `gemma-4-uncensored` — Balanced. Good quality, moderate latency. No thinking token issues.
- `mercury-2` — High quality but slow, and **requires `disable_thinking: True`** or it silently fails.

```python
resp = await client.post(
    "https://api.venice.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {VENICE_API_KEY}"},
    json={
        "model": CHAT_MODEL,
        "messages": conversations[call_sid],
        "max_tokens": 4096,           # High budget for context understanding
        "temperature": 0.7,
        "venice_parameters": {
            "enable_web_search": "auto",
            "include_venice_system_prompt": False,
            "disable_thinking": True,  # Essential for reasoning models on phone
        },
    },
)
```

### Phone Brevity Prompt — with Dynamic Mode Switching

Voice bots speak, not type. The default system prompt is forceful about brevity. However, callers sometimes want detailed explanations. Implement **dynamic mode switching** so the caller can toggle between brief and detailed modes within a single call.

#### System prompts

```python
BRIEF_SYSTEM = (
    "You are Vega, an AI assistant on a phone call. You speak, not type. "
    "CRITICAL: You are on a PHONE CALL. The caller is LISTENING, not reading. "
    "Your response MUST be brief — 1 to 3 short sentences. Period. No exceptions. "
    "Never use lists, bullet points, numbers, markdown, or code. Just talk naturally. "
    "If the user gives you a task, briefly confirm what you'll do — don't explain how. "
    "Be warm, direct, and concise. No filler, no hedging, no over-explaining. "
    "ERR ON THE SIDE OF BEING TOO SHORT rather than too long."
)

DETAILED_SYSTEM = (
    "You are Vega, an AI assistant on a phone call. You speak, not type. "
    "The caller has asked for a DETAILED response. Give thorough, informative answers. "
    "You can speak at length — 5 to 10 sentences is fine when the topic warrants it. "
    "Use a natural conversational tone, as if explaining something to a colleague. "
    "You may use structure like 'first... second...' or 'on one hand... on the other...' "
    "but keep it spoken, not written. No bullet points, markdown, or code. "
    "Be warm, knowledgeable, and engaging. Go deep when the topic calls for it. "
    "The caller will tell you when they want to switch back to brief mode."
)
```

#### Mode switch trigger words

```python
DETAILED_TRIGGERS = {"detailed", "detail", "in detail", "explain more", "elaborate",
    "deep dive", "go deep", "tell me more", "long answer", "long version",
    "thorough", "comprehensive", "in depth", "in-depth"}

BRIEF_TRIGGERS = {"brief", "quick", "short", "summarize", "summary",
    "short version", "short answer", "quick answer", "tldr", "bottom line",
    "just the gist"}
```

#### Per-call mode state

```python
call_modes: dict[str, str] = {}  # call_sid → "brief" or "detailed"

def get_system_prompt(call_sid: str, user_message: str) -> str:
    lower = user_message.lower().strip()
    for trigger in DETAILED_TRIGGERS:
        if trigger in lower:
            call_modes[call_sid] = "detailed"
            break
    for trigger in BRIEF_TRIGGERS:
        if trigger in lower:
            call_modes[call_sid] = "brief"
            break
    mode = call_modes.get(call_sid, "brief")
    return DETAILED_SYSTEM if mode == "detailed" else BRIEF_SYSTEM
```

On each user message, call `get_system_prompt()` and update `conversations[call_sid][0]` (the system message). Clean up `call_modes` alongside `conversations` when a call ends.

Keep `max_tokens` high (4096+) so the model has full context understanding, but rely on the prompt to constrain response length.

## Venice TTS Integration

```python
async def generate_tts_audio(text: str, voice: str = "if_sara", model: str = "tts-kokoro") -> bytes:
    """Generate speech audio via Venice TTS. Returns raw MP3 bytes."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.venice.ai/api/v1/audio/speech",
            headers={"Authorization": f"Bearer {VENICE_API_KEY}"},
            json={
                "model": model,
                "voice": voice,
                "input": text[:4096],  # Venice hard cap
                "response_format": "mp3",
                "speed": 1.0,
            },
        )
        response.raise_for_status()
        return response.content
```

### Voice Selection Tips

- **Default (high quality, moderate latency)**: `tts-xai-v1` / `ara` — natural, warm, ~4-5s latency. Best voice quality per user testing.
- **Fastest (best latency, slightly less natural)**: `tts-kokoro` — ~1s latency, 57 voices. Good for low-latency needs but some users find voices less natural than xAI.
- **Indian-accented English**: `tts-kokoro` / `if_sara` (~1.8s) or `tts-xai-v1` / `ara` (~5s)
- **Spanish/Latina English**: `tts-kokoro` / `pf_dora` (0.7s, fastest voice overall)
- **Emotional callers**: `tts-qwen3-1-7b` / `Vivian` — supports emotion/style via `prompt` param
- **Character personas**: `tts-inworld-1-5-max` / `Ashley` or `Craig`
- **Expressive conversations**: `tts-orpheus` / `leo` — expressive but 30s+ latency, **not suited for real-time phone**

#### TTS Model Latency Benchmarks (tested May 2025)

Benchmarked with a 25-word sentence on Venice API:

| Model | Latency | Voices | Notes |
|-------|---------|--------|-------|
| `tts-kokoro` | **1.0-2.7s** ⚡ | 57 voices (af_bella, af_nova, af_sarah, af_river, af_aoede, af_jadzia, af_heart, am_adam, am_liam, am_eric, bf_alice, bf_emma, ef_dora, em_alex, etc.) | **Best for phone bots.** Fast, natural, cheap. |
| `tts-xai-v1` | 4.0-5.7s | 5 voices (ara, eve, leo, rex, sal) | Good quality, moderate latency |
| `tts-elevenlabs-turbo-v2-5` | ~7.9s | 21+ voices (Alice, Aria, Brian, etc.) | Great quality but slow |
| `tts-orpheus` | 30s+ (timeout) | 8 voices (dan, jess, leah, leo, mia, etc.) | Too slow for real-time phone |

**Fastest Kokoro voices (benchmarked):** `af_river` (0.6s), `pf_dora` (0.7s), `am_liam` (0.7s), `af_sarah` (1.0s), `af_aoede` (1.0s), `af_bella` (1.4s)

**Kokoro accent prefixes (speak English with accent):** `ef_*` = Spanish-accented female (ef_dora), `pf_*` = Portuguese/Latina-accented female (pf_dora), `hf_*` = Hispanic female (hf_alpha, hf_beta), `if_*` = Indian female (if_sara), `bf_*` = British female (bf_alice, bf_emma, bf_lily). These all speak English but with their respective accents. Great for giving a bot personality without changing language.

**Recommendation (based on user testing):**
- **Highest quality:** `tts-xai-v1` with `ara` — most natural-sounding, ~4-5s latency. Use `speed: 1.15` for phone.
- **Fastest possible:** `tts-kokoro` with `af_river` (0.6s fastest) or `af_sarah` (1.0s, warm).
- **Indian-accented English:** `tts-xai-v1` with `ara` or `tts-kokoro` with `if_sara` (Indian female, ~1.8s).
- **Spanish/Latina English:** `tts-kokoro` with `pf_dora` (Portuguese/Latina, 0.7s).

Use `speed: 1.15` for phone bots. ~2.3x faster than `tts-xai-v1`.

See `venice-audio-speech` skill for full voice list and model capabilities.

### Input Length Limit

Venice TTS has a **4096 character hard cap** on `input`. For longer responses, split on sentence boundaries and concatenate audio segments, or use streaming.

## Twilio Polly Fallback Voice

When Venice TTS fails, the bot falls back to Twilio's built-in `<Say>` with a Polly Neural voice. This is also used for greetings, "I didn't catch that", goodbyes, and the "One moment..." thinking prompt.

**Recommended female voices:**

| Voice | Style | Notes |
|-------|-------|-------|
| `Polly.Aditi` | Indian English bilingual | ⚠️ **Standard only — NOT Neural!** Using `Polly.Aditi-Neural` crashes Twilio with "Application error". |
| `Polly.Penelope-Neural` | US Spanish bilingual, Latina accent | Neural |
| `Polly.Aria-Neural` | Warm, natural American | Most popular, sounds like a real person |
| `Polly.Joanna-Neural` | Classic, warm American | Very natural, great personality |
| `Polly.Sofia-Neural` | Friendly, warm American | Casual and approachable |
| `Polly.Lupe-Neural` | US Spanish bilingual | Warm Latina accent |
| `Polly.Camila-Neural` | Brazilian Portuguese | LatAm accent in English |
| `Polly.Amy-Neural` | Posh British | If you want an accent |

**Male alternatives:** `Polly.Matthew-Neural`, `Polly.Joey-Neural`, `Polly.Justin-Neural`

Set in every `<Say>` tag with the voice string exactly as shown. Not all Polly voices have Neural variants — always verify the voice name exists before using it.

**⚠️ Critical: Polly voice naming.** Some Polly voices only exist in Standard quality, not Neural. Using `{VoiceName}-Neural` for a Standard-only voice (like `Polly.Aditi`) causes Twilio to crash with "Application error has occurred." Always verify the voice name is valid — when in doubt, use Standard (`Polly.Aditi`) not Neural (`Polly.Aditi-Neural`). The Neural variant is higher quality but not available for all voices.

**Pairing tip:** Match your Polly voice accent/region to your Venice TTS voice accent. Common pairings:
- Indian accent: `Polly.Aditi` (Twilio, Standard) + `ara` (xAI) or `if_sara` (Kokoro)
- Spanish/Latina accent: `Polly.Penelope-Neural` (Twilio) + `pf_dora` (Kokoro)
- Neutral American: `Polly.Aria-Neural` (Twilio) + `ara` (xAI) or `af_river`/`af_sarah` (Kokoro)

Callers hear the Polly voice for greetings/fallback, then the Venice TTS voice for AI responses. Mismatched accents are jarring, so pair consistently.

**User preference note:** When the user has tested multiple TTS models, they may prefer `tts-xai-v1` / `ara` over `tts-kokoro` even though Kokoro is faster. The xAI voice sounds more natural to some ears. Always defer to the user's tested preference over raw latency numbers.

## Environment Variables

```env
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_PHONE_NUMBER=+18703747844

# Venice AI
VENICE_API_KEY=vn_xxxxxx

# Security
ALLOWED_CALLERS=+16175104464   # Comma-separated E.164 numbers

# TTS settings (tts-kokoro/af_sarah for fastest phone response, tts-xai-v1/ara for highest quality)
TTS_VOICE=af_sarah
TTS_MODEL=tts-kokoro
TTS_SPEED=1.15

# Chat model for processing tasks (qwen3-5-9b recommended for phone — fast, no thinking token issues)
CHAT_MODEL=qwen3-5-9b
CHAT_MODEL=qwen3-5-9b

# STT settings — "record" uses Venice transcription (Whisper/Scribe), "gather" uses Twilio built-in
STT_METHOD=record
STT_MODEL=openai/whisper-large-v3

# Server
HOST=0.0.0.0
PORT=5000
BASE_URL=https://voice.example.com  # CRITICAL — must be set for Twilio audio playback
```

## Deployment

### Railway + Custom Domain (Recommended)

Railway V2 on hobby plan **does not auto-assign a `.up.railway.app` domain**. You must either create one via `railway domain` CLI or set up a custom domain via Cloudflare. For production, always use a custom domain.

#### Step 1: Deploy to Railway

```bash
railway init --name hermes-voice
railway link
railway up
```

#### Step 2: Set Environment Variables

```bash
railway variable set TWILIO_ACCOUNT_SID=ACxxxxxx
railway variable set TWILIO_AUTH_TOKEN=xxxxxxxx
railway variable set BASE_URL=https://voice.example.com
# ... etc
```

Or via Railway GraphQL API (see `railway` skill for full API details):

```bash
mutation { variableUpsert(input: { projectId: "...", environmentId: "...", serviceId: "...", name: "BASE_URL", value: "https://voice.example.com" }) }
```

#### Step 3: Add Custom Domain

Use the Railway GraphQL API to create a custom domain, then add the required DNS records (CNAME + TXT verification) to Cloudflare. See `references/deployment-checklist.md` and `references/cloudflare-railway-dns.md` for the full automated setup.

Key steps:
1. `customDomainCreate` mutation → get domain ID and DNS record requirements
2. Add CNAME `voice` → `<hash>.up.railway.app` and TXT `_railway-verify.voice` in Cloudflare
3. Wait for `verified: true` and `certificateStatus: CERTIFICATE_STATUS_TYPE_VALID`
4. Set `BASE_URL=https://voice.example.com` in Railway env vars
5. Redeploy

#### Step 4: Configure Twilio Webhook

Use the Python SDK (Option B above) or Twilio Console to point your number's voice URL to `https://voice.example.com/voice`.

### Docker (Development Only)

```bash
docker compose up -d
```

See `templates/docker-compose.yml` in the hermes-voice template.

## Outbound Calls (Bot → User)

The bot can make outbound calls via `POST /call`. When Twilio answers, it hits the `outbound` endpoint which plays a message and enters the conversation loop.

**Critical:** Don't pass message text in URL query parameters — special characters (punctuation, quotes) break Twilio's URL parsing and return `400 Unable to create record: Url is not a valid URL`. Instead, store messages server-side with a short ID and use the ID in the URL path:

```python
# In-memory message store (or use Redis for multi-instance)
outbound_messages: dict[str, str] = {}

@app.post("/call")
async def make_call(request: Request):
    body = await request.json()
    to_number = body.get("to")
    message = body.get("message", "Hello, this is Vega calling you back.")
    if not to_number:
        return JSONResponse({"error": "Missing 'to' number"}, status_code=400)

    msg_id = str(uuid.uuid4())[:8]
    outbound_messages[msg_id] = message

    call = twilio_client.calls.create(
        to=to_number,
        from_=TWILIO_PHONE_NUMBER,
        url=f"{BASE_URL}/outbound/{msg_id}",  # Clean URL, no query params
        method="POST",
    )
    return JSONResponse({"call_sid": call.sid, "status": call.status, "message": message})

@app.post("/outbound/{msg_id}")
async def outbound_call(msg_id: str, request: Request):
    msg = outbound_messages.pop(msg_id, "Hello, this is Vega. How can I help?")
    response = VoiceResponse()
    gather = response.gather(input="speech", action="/process", method="POST",
                             speech_timeout="auto", language="en-US", timeout=10)
    gather.say(msg, voice="Polly.Aditi")
    response.redirect("/voice")
    return Response(content=str(response), media_type="application/xml")
```

### Testing Outbound Calls

```bash
curl -X POST "https://voice.example.com/call" \
  -H "Content-Type: application/json" \
  -d '{"to": "+16175551234", "message": "Hey, this is Vega. Just calling to say hello!"}'
```

The user picks up, hears the message, then can talk naturally in the same conversation loop.

## Pitfalls

- **Twilio webhook timeout causes 502 / "application error"**: The full pipeline (download → Whisper STT → LLM → Venice TTS) takes 15-30+ seconds in practice. Twilio's default webhook timeout is ~15 seconds. If the handler doesn't return TwiML quickly, Twilio shows "Application error has occurred" and hangs up. **FIX: Use the async polling pattern** — respond immediately with "Let me think." TwiML + hold music, process in a background task, poll via `/check_response/{call_sid}`.
- **TTS latency scales with response length**: `tts-xai-v1` takes ~4-5s for a 25-word sentence but **24+ seconds** for a 3-4 sentence response. Always use the async polling pattern, never block the webhook on TTS.
- **Hold music while processing**: Generate a static MP3 (flamenco guitar, ambient, etc.) via Venice `/audio/music` API and serve it from the `static/` dir. Use `<Play>{base_url}/audio/hold_music.mp3</Play>` in the "processing" TwiML so callers hear music instead of silence. The `/check_response` polling loop also plays hold music while waiting.
- **Recording URL auth and format**: Twilio recording URLs require HTTP Basic Auth with Account SID and Auth Token. Append `.wav` for WAV format (better for STT). If `.wav` returns non-200, fall back to the base URL (Twilio defaults to WAV anyway). Check `len(content) > 100` as a sanity check — a 0-byte or tiny response means the recording isn't ready yet.
- **Record mode latency trade-off**: `<Record>` + Venice STT adds ~2-4s per turn vs `<Gather>` but comprehension is much better. Always prefer `STT_METHOD=record` for production. The async pattern makes the latency invisible to the caller (they hear hold music instead of dead air).
- **Reasoning models eat all tokens**: `mercury-2` and other thinking models spend reasoning tokens from `max_tokens`. With `max_tokens: 256`, the model produces empty/truncated responses. Fix: set `max_tokens: 4096` and `disable_thinking: True`.
- **`ImportError: cannot import name 'VoiceResponse' from 'twilio.twiml'`**: Use `from twilio.twiml.voice_response import VoiceResponse` — NOT `from twilio.twiml import VoiceResponse`.
- **Venice TTS 404 "model not found: venice/tts"**: Use exact IDs like `tts-kokoro`. Never prefix with `venice/`.
- **`BASE_URL` not set**: Critical — without it, Twilio can't fetch TTS audio files. Set `BASE_URL=https://your-domain.com` in Railway env vars.
- **Railway 404 "Application not found"**: Hobby plan doesn't auto-assign public domains. Add a custom domain via `customDomainCreate` mutation or `railway domain` CLI.
- **`deployment.url` returns `null` in Railway API**: Normal for hobby plan. Use custom domain URLs instead.
- **Railway CLI `Unauthorized`**: Project-scoped tokens don't work for CLI. Use account-level tokens from railway.app/account/tokens.
- **Twilio can't reach audio URLs**: Audio files must be publicly accessible via `BASE_URL/audio/`. Check that `BASE_URL` is set and the `/audio_cache/` directory is writable.
- **TTS audio cut off**: Venice input cap is 4096 chars. Truncate or split response.
- **`Gather(input_type="speech")` TypeError**: Use `input="speech"` as kwarg, NOT `input_type`.
- **`Polly.Aditi-Neural` crashes Twilio**: Aditi is a **Standard-only** Polly voice. Using `Polly.Aditi-Neural` causes Twilio to return "Application error has occurred" and hang up. Always use `Polly.Aditi` (without `-Neural`). Other voices that are Standard-only: check AWS docs before assuming `-Neural` is valid.
- **Outbound call URL encoding breaks Twilio**: Never put message text in Twilio URL query params — special characters (punctuation, quotes) cause `400 Unable to create record: Url is not a valid URL`. Store messages server-side with a UUID key, use `/outbound/{msg_id}` path param instead.
- **Kokoro voices may sound worse to some users**: Despite lower latency (~1s vs ~4-5s for xAI), some users find Kokoro voices less natural. Always test with the actual listener and defer to their preference. Don't assume faster = better voice quality.
- **Kokoro TTS files look small**: `tts-kokoro` produces ~19KB MP3s for a 25-word sentence vs ~100-125KB for other models. Don't be surprised by the smaller file sizes — quality is still good and network transfer is faster.
- **Twilio recording download needs auth**: Recording URLs require HTTP Basic Auth (`SID:Auth_Token`). Use `httpx.AsyncClient().get(url, auth=(SID, Auth_Token))`. Append `.wav` for WAV format (better for STT accuracy). If WAV returns non-200, fall back to the default format. Check `len(content) > 100` as a sanity check.
- **Twilio `<Record>` doesn't have `input` param**: Unlike `<Gather>`, `<Record>` uses `action`, `method`, `timeout`, `max_length`, `play_beep`, `trim`, `finish_on_key` params. Don't accidentally pass `input="speech"` to `<Record>`.
- **Railway env vars override code defaults**: Changing `CHAT_MODEL`, `TTS_MODEL`, etc. in `main.py` only affects the fallback when the Railway env var is not set. If the env var is configured on Railway, it always wins. To change the active model, you MUST update the Railway env var (via `railway variable set` or GraphQL `variableUpsert`). Changing code defaults alone won't take effect.
- **Railway CLI auth fails with project-scoped tokens**: Tokens like `892faa4f-...` (project-scoped) work for GraphQL API reads AND mutations (including `variableUpsert`) but fail for CLI commands (`whoami`, `link`, `variables`). Use the GraphQL API at `https://backboard.railway.app/graphql/v2` for env changes when CLI auth fails.
- **In-memory state leaks on long-running instances**: `conversations`, `call_modes`, and `outbound_messages` dicts are in-memory. If Railway redeploys mid-call, the conversation context is lost. For production, use Redis or a persistent store.
- **Himalaya `template send` fails with Gmail**: Gmail's IMAP rejects APPEND to `[Gmail]/Sent Mail` with `NO: Folder doesn't exist`. Setting `message.save.copy = false` doesn't reliably fix it. For sending emails from the bot, use Python `smtplib` directly (see email skill).
- **Railway GraphQL variableUpsert requires `projectId`**: The mutation needs `projectId`, `environmentId`, `serviceId`, `name`, and `value`. Omitting `projectId` causes a validation error.
- **Cloudflare CNAME already exists**: Use PATCH instead of POST to update the existing record. Set `proxied: false` initially.
- **Railway domain verification stuck at `VALIDATING_OWNERSHIP`**: TXT verification record may not have propagated yet. Check with Cloudflare DoH: `curl https://1.1.1.1/dns-query?name=_railway-verify.voice.example.com&type=TXT -H "Accept: application/dns-json"`.

## References

- `references/async-polling-pattern.md` — **Critical**: The async polling pattern for preventing Twilio webhook timeouts. Includes architecture, code patterns, hold music generation, timing benchmarks, and Twilio error diagnostics.
- `references/deployment-checklist.md` — Full Railway + Cloudflare custom domain deployment walkthrough (DNS automation, Twilio webhook, verification steps)
- `references/cloudflare-railway-dns.md` — Cloudflare DNS + Railway custom domain API automation (CNAME, TXT verification, domain status polling)
- `references/twilio-webhook-flow.md` — Detailed webhook lifecycle, TwiML response patterns, and error handling
- `references/railway-graphql-api.md` — Railway GraphQL API for env var management when CLI auth fails: queries, variableUpsert mutations, batch updates, deploy verification
- `templates/hermes-voice-server.py` — Complete FastAPI server template with all endpoints
- `templates/docker-compose.yml` — Docker deployment config
- `templates/requirements.txt` — Python dependencies