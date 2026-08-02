# Twilio Voice: Async Polling Pattern

## The Problem

Twilio's webhook timeout is ~15 seconds. The full voice bot pipeline takes 15-30+ seconds:

| Step | Time |
|------|------|
| Download recording from Twilio | 0.3s |
| Venice Whisper STT | 1.5s |
| LLM chat (gemma-4-uncensored) | 4s |
| Venice TTS (tts-xai-v1, longer responses) | 5-24s |
| **Total** | **11-30s** |

A synchronous handler exceeds Twilio's timeout → 502 error → "Application error has occurred" to the caller.

## The Solution: Async Polling Pattern

Respond to Twilio **immediately** with a short TwiML, then process in the background. Use a polling endpoint that plays hold music while waiting.

### Architecture

```
POST /process_recording
  → Mark call_sid as "processing" in pending_responses dict
  → Launch asyncio.create_task(_process_recording_async(...))
  → Return immediately:
    <Response>
      <Say voice="Polly.Joanna-Neural">Let me think.</Say>
      <Play>{base_url}/audio/hold_music.mp3</Play>
      <Redirect method="POST">/check_response/{call_sid}</Redirect>
    </Response>

Background task (_process_recording_async):
  1. Download recording from Twilio (with auth)
  2. Transcribe via Venice /audio/transcriptions (Whisper)
  3. Get AI response via Venice /chat/completions
  4. Generate TTS audio via Venice /audio/speech
  5. Store result in pending_responses[call_sid] with action:
     - "respond" (has audio_url) — play TTS audio, then record next turn
     - "respond_tts_fallback" (no audio) — use <Say> with Polly voice
     - "reprompt" (STT failed) — ask caller to repeat
     - "hangup" (caller said goodbye) — say goodbye and hang up

POST /check_response/{call_sid}
  → If pending_responses[call_sid] doesn't exist: re-prompt
  → If status == "processing": play hold music, redirect back here (loop)
  → If status == "done": return full response TwiML (audio + next Record)
```

### Key Code Patterns

```python
# In-memory response tracking
pending_responses: dict[str, dict] = {}
# call_sid -> {"status": "processing"|"done", "audio_url": ..., "text": ..., "action": ...}

# Handler returns immediately
@app.post("/process_recording")
async def process_recording(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    recording_url = form_data.get("RecordingUrl", "")
    base_url = get_base_url(request)
    
    # Mark as processing, launch background task
    pending_responses[call_sid] = {"status": "processing", ...}
    asyncio.create_task(_process_recording_async(call_sid, recording_url, caller, base_url))
    
    # Return immediately with hold music
    response = VoiceResponse()
    response.say("Let me think.", voice="Polly.Joanna-Neural")
    response.play(f"{base_url}/audio/hold_music.mp3")
    response.redirect(f"/check_response/{call_sid}", method="POST")
    return Response(content=str(response), media_type="application/xml")

# Polling endpoint
@app.post("/check_response/{call_sid}")
async def check_response(call_sid: str, request: Request):
    base_url = get_base_url(request)
    result = pending_responses.get(call_sid)
    
    if result is None:
        # Lost context — re-prompt
        response = VoiceResponse()
        response.say("Let me listen again.", voice="Polly.Joanna-Neural")
        response.record(action="/process_recording", ...)
        return Response(content=str(response), media_type="application/xml")
    
    if result["status"] == "processing":
        # Still working — play hold music and check again
        response = VoiceResponse()
        response.play(f"{base_url}/audio/hold_music.mp3")
        response.redirect(f"/check_response/{call_sid}", method="POST")
        return Response(content=str(response), media_type="application/xml")
    
    # Response ready — play audio and set up next turn
    pending_responses.pop(call_sid, None)
    response = VoiceResponse()
    if result.get("audio_url"):
        response.play(result["audio_url"])
    else:
        response.say(result["text"], voice="Polly.Joanna-Neural")
    response.say("Go ahead.", voice="Polly.Joanna-Neural")
    response.record(action="/process_recording", ...)
    return Response(content=str(response), media_type="application/xml")
```

### Hold Music Generation

Use Venice's async music API (`/audio/quote` → `/audio/queue` → `/audio/retrieve` → `/audio/complete`) to generate a 30-second instrumental track. Save it as `static/hold_music.mp3`.

```bash
# 1. Quote
curl -s https://api.venice.ai/api/v1/audio/quote \
  -H "Authorization: Bearer $VENICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "elevenlabs-music", "duration_seconds": 30}'

# 2. Queue
curl -s https://api.venice.ai/api/v1/audio/queue \
  -H "Authorization: Bearer $VENICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "elevenlabs-music", "prompt": "Soft Spanish flamenco guitar, gentle fingerpicked arpeggios, warm and relaxing, no vocals, instrumental only", "duration_seconds": 30, "force_instrumental": true}'

# 3. Poll /audio/retrieve (every 5s, returns binary audio when done)
# 4. /audio/complete (cleanup)
```

Serve it from the `/audio/{filename}` endpoint, checking both `audio_cache/` (dynamic TTS) and `static/` (permanent assets like hold music).

### Diagnosing Twilio Errors

Use Twilio's Monitor API to check for webhook errors:

```python
from twilio.rest import Client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
alerts = client.monitor.alerts.list(limit=10)
for a in alerts:
    print(f"Code: {a.error_code} | Time: {a.date_generated} | {a.alert_text[:200]}")
```

Common error codes:
- **11200**: HTTP error from your server (502, 500, etc.) — verify server is up
- **13520**: "Say: Invalid text" — check for empty strings or special chars in `<Say>`
- **12100**: Invalid TwiML — check XML syntax

### Timing Benchmarks (May 2025)

Tested with a real Twilio recording (8 seconds):

| Step | Time |
|------|------|
| Download recording from Twilio | 0.3s |
| Venice Whisper STT (openai/whisper-large-v3) | 1.5s |
| Venice Chat (gemma-4-uncensored) | 4s |
| Venice TTS (tts-xai-v1/ara, longer response) | **5-24s** |
| Total pipeline | **11-30s** |

The TTS latency is highly variable. Short responses (~3 sentences) are 5-8s. Longer explanations can hit 24s+.

### Important: Import asyncio

The async pattern requires `asyncio.create_task()`. Make sure to import it:

```python
import asyncio
```

And use `pending_responses` as an in-memory dict (or Redis for multi-instance deployments).