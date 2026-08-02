"""
Hermes Voice — Twilio Phone Integration Server

Call Hermes, give tasks, hear responses via Venice TTS.

Architecture:
  Phone → Twilio → /voice (TwiML Gather) → /process (transcript)
    → LLM processes task → Venice TTS generates audio
    → Twilio <Play> audio → loop for more or hang up

Requirements: fastapi, uvicorn, twilio, httpx, python-dotenv
"""

import os
import uuid
import time
import logging
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse, Gather, Play
from twilio.request_validator import RequestValidator
import httpx
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")
VENICE_API_KEY = os.environ["VENICE_API_KEY"]
VENICE_BASE_URL = os.environ.get("VENICE_BASE_URL", "https://api.venice.ai/api/v1")
ALLOWED_CALLERS = [n.strip() for n in os.environ.get("ALLOWED_CALLERS", "").split(",") if n.strip()]
TTS_VOICE = os.environ.get("TTS_VOICE", "ara")
TTS_MODEL = os.environ.get("TTS_MODEL", "tts-xai-v1")
TTS_SPEED = float(os.environ.get("TTS_SPEED", "1.0"))
CHAT_MODEL = os.environ.get("CHAT_MODEL", "gemma-4-uncensored")
BASE_URL = os.environ.get("BASE_URL", "https://your-server.com")  # Public URL for audio serving

AUDIO_CACHE_DIR = Path("audio_cache")
AUDIO_CACHE_DIR.mkdir(exist_ok=True)

CALL_STATE = {}  # call_sid -> { "history": [...], "turn_count": int }

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hermes-voice")

app = FastAPI(title="Hermes Voice", version="1.0.0")


# --- Helpers ---

async def validate_twilio(request: Request) -> bool:
    """Validate Twilio webhook signature. Skip in dev if no BASE_URL."""
    if os.environ.get("SKIP_TWILIO_VALIDATION", "false").lower() == "true":
        return True
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    form = await request.form()
    params = dict(form)
    return validator.validate(url, params, signature)


async def generate_tts_audio(text: str, voice: str = None, model: str = None) -> str:
    """Generate speech via Venice TTS. Returns the filename of the cached MP3."""
    voice = voice or TTS_VOICE
    model = model or TTS_MODEL
    filename = f"{uuid.uuid4()}.mp3"
    filepath = AUDIO_CACHE_DIR / filename

    # Venice input cap is 4096 chars
    text = text[:4096]

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{VENICE_BASE_URL}/audio/speech",
            headers={
                "Authorization": f"Bearer {VENICE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "voice": voice,
                "input": text,
                "response_format": "mp3",
                "speed": TTS_SPEED,
            },
        )
        response.raise_for_status()
        filepath.write_bytes(response.content)

    logger.info(f"TTS audio generated: {filename} ({len(text)} chars)")
    return filename


async def process_with_llm(transcript: str, call_sid: str) -> str:
    """Send transcript to Venice chat and return the assistant response."""
    # Get or create call state
    state = CALL_STATE.setdefault(call_sid, {"history": [], "turn_count": 0})
    state["turn_count"] += 1

    # Build conversation history
    system_prompt = (
        "You are Hermes, a helpful phone assistant. The user is calling you on the phone. "
        "CRITICAL: You are on a PHONE CALL. The caller is LISTENING, not reading. "
        "Your response MUST be brief — 1 to 3 short sentences. Period. No exceptions. "
        "Never use lists, bullet points, numbers, markdown, or code. Just talk naturally. "
        "If the user gives you a task, briefly confirm what you'll do — don't explain how. "
        "Be warm, direct, and concise. No filler, no hedging, no over-explaining. "
        "ERR ON THE SIDE OF BEING TOO SHORT rather than too long."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(state["history"])
    messages.append({"role": "user", "content": transcript})

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{VENICE_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {VENICE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": CHAT_MODEL,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.7,
                "venice_parameters": {
                    "enable_web_search": "auto",
                    "include_venice_system_prompt": False,
                },
            },
        )
        response.raise_for_status()
        data = response.json()

    assistant_message = data["choices"][0]["message"]["content"]

    # Update history
    state["history"].append({"role": "user", "content": transcript})
    state["history"].append({"role": "assistant", "content": assistant_message})

    # Keep history manageable (last 20 messages)
    if len(state["history"]) > 20:
        state["history"] = state["history"][-20:]

    return assistant_message


def cleanup_old_audio(max_age_seconds: int = 3600):
    """Remove audio files older than max_age_seconds."""
    now = time.time()
    for f in AUDIO_CACHE_DIR.glob("*.mp3"):
        if f.stat().st_mtime < now - max_age_seconds:
            f.unlink(missing_ok=True)


# --- Endpoints ---

@app.get("/")
async def health():
    return {"status": "ok", "service": "hermes-voice"}


@app.post("/voice")
async def voice_handler(request: Request):
    """Initial webhook — Twilio calls this when a call comes in."""
    form = await request.form()
    call_sid = form.get("CallSid", "")
    from_number = form.get("From", "")

    # Validate caller
    if ALLOWED_CALLERS and from_number not in ALLOWED_CALLERS:
        logger.warning(f"Rejected call from {from_number}")
        response = VoiceResponse()
        response.say("Sorry, you are not authorized to use this service. Goodbye.")
        return Response(content=str(response), media_type="application/xml")

    # Validate Twilio signature
    if not await validate_twilio(request):
        logger.warning(f"Invalid Twilio signature from {from_number}")
        response = VoiceResponse()
        response.say("Authentication failed. Goodbye.")
        return Response(content=str(response), media_type="application/xml")

    logger.info(f"Call from {from_number}, SID: {call_sid}")

    # Initialize call state
    CALL_STATE[call_sid] = {"history": [], "turn_count": 0}

    # Clean up old cached audio
    cleanup_old_audio()

    # Respond with Gather for speech input
    response = VoiceResponse()
    gather = Gather(
        input="speech",  # Use "input" as kwarg (not input_type — that's not a valid param)
        action="/process",
        method="POST",
        speech_timeout="auto",
        timeout=10,
        language="en-US",
    )
    gather.say("Hello, this is Hermes. What can I help you with today?")
    response.append(gather)

    # Fallback if no speech detected
    response.say("I didn't hear anything. Feel free to call back anytime. Goodbye.")
    response.hangup()

    return Response(content=str(response), media_type="application/xml")


@app.post("/process")
async def process_handler(request: Request):
    """Process speech transcript and respond with TTS audio."""
    form = await request.form()
    call_sid = form.get("CallSid", "")
    speech_result = form.get("SpeechResult", "")
    from_number = form.get("From", "")

    logger.info(f"Processing call {call_sid}: '{speech_result}'")

    # If no speech detected, ask again
    if not speech_result.strip():
        response = VoiceResponse()
        gather = Gather(
            input="speech",
            action="/process",
            method="POST",
            speech_timeout="auto",
            timeout=10,
            language="en-US",
        )
        gather.say("I didn't catch that. Could you repeat yourself?")
        response.append(gather)
        response.say("I still can't hear you. Goodbye.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Get LLM response
    try:
        llm_response = await process_with_llm(speech_result, call_sid)
    except Exception as e:
        logger.error(f"LLM error: {e}")
        response = VoiceResponse()
        response.say("I'm having trouble thinking right now. Please try again later.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Generate TTS audio
    try:
        audio_filename = await generate_tts_audio(llm_response)
        audio_url = f"{BASE_URL}/audio_cache/{audio_filename}"
    except Exception as e:
        logger.error(f"TTS error: {e}")
        # Fallback to Twilio Say if TTS fails
        response = VoiceResponse()
        gather = Gather(
            input="speech",
            action="/process",
            method="POST",
            speech_timeout="auto",
            timeout=10,
            language="en-US",
        )
        gather.say(llm_response[:500])  # Twilio Say has length limits
        response.append(gather)
        response.say("Goodbye!")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Respond with audio + gather loop for next input
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/process",
        method="POST",
        speech_timeout="auto",
        timeout=10,
        language="en-US",
    )
    gather.play(audio_url)
    response.append(gather)

    # Fallback if no further speech
    response.say("Thanks for calling. Goodbye!")
    response.hangup()

    return Response(content=str(response), media_type="application/xml")


@app.post("/hangup")
async def hangup_handler(request: Request):
    """Clean up when call ends."""
    form = await request.form()
    call_sid = form.get("CallSid", "")

    # Remove call state
    if call_sid in CALL_STATE:
        state = CALL_STATE.pop(call_sid)
        logger.info(f"Call {call_sid} ended after {state.get('turn_count', 0)} turns")

    response = VoiceResponse()
    return Response(content=str(response), media_type="application/xml")


# Serve cached audio files
@app.get("/audio_cache/{filename}")
async def serve_audio(filename: str):
    """Serve cached TTS audio files to Twilio."""
    filepath = AUDIO_CACHE_DIR / filename
    if not filepath.exists():
        return Response(status_code=404, content="Audio not found")
    return Response(
        content=filepath.read_bytes(),
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=3600"},
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)