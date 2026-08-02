#!/usr/bin/env python3
"""Generate Jessica TTS audio and queue Seedance R2V hostess clips for AI Pharma Exchange."""
import base64, json, requests, yaml
from pathlib import Path

HOME = Path.home()
ROOT = HOME / "faces" / "aipharmaxchange_openevidence_30s"
HOST_DIR = ROOT / "host_video"
HOST_DIR.mkdir(parents=True, exist_ok=True)

with open(HOME / ".hermes/config.yaml") as f:
    cfg = yaml.safe_load(f)
api_key = cfg.get("api_key") or cfg.get("model", {}).get("api_key")
BASE = "https://api.venice.ai/api/v1"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

HOSTESS_REF = HOST_DIR / "hostess_reference_frame.jpg"
if not HOSTESS_REF.exists():
    raise FileNotFoundError(f"Place the canonical hostess reference image at {HOSTESS_REF}")


def to_data_url(path: Path, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def tts(text: str, out_path: Path):
    """Generate Jessica TTS via Venice ElevenLabs turbo."""
    resp = requests.post(
        f"{BASE}/audio/speech",
        headers=headers,
        json={"model": "tts-elevenlabs-turbo-v2-5", "voice": "Jessica", "input": text},
        timeout=120,
    )
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    print(f"TTS saved: {out_path} ({len(resp.content)} bytes)")


def queue_seedance(audio_path: Path, prompt: str, negative: str, duration: str = "15s") -> str:
    """Queue a Seedance R2V clip. Returns queue_id."""
    payload = {
        "model": "seedance-2-0-enhanced-reference-to-video",
        "prompt": prompt,
        "negative_prompt": negative,
        "duration": duration,
        "aspect_ratio": "3:4",
        "resolution": "720p",
        "reference_image_urls": [to_data_url(HOSTESS_REF, "image/jpeg")],
        "reference_audio_urls": [to_data_url(audio_path, "audio/mpeg")],
        "consents": {
            "seedance": {
                "confirmed_terms_and_privity": True,
                "confirmed_legal_right": True,
                "confirmed_screening_acknowledged": True,
            }
        },
    }
    resp = requests.post(f"{BASE}/video/queue", headers=headers, json=payload, timeout=120)
    print("Queue response:", resp.status_code, resp.text[:300])
    resp.raise_for_status()
    return resp.json()["queue_id"]


def main():
    # Example script for OpenEvidence paper summary; replace with your topic.
    seg1_text = (
        "OpenEvidence lets large language models answer clinical questions with trusted medical references. "
        "Researchers tested it on nearly three thousand real-world cases across specialties like cardiology, "
        "infectious disease, and oncology."
    )
    seg2_text = (
        "The system scored well above typical benchmarks, especially when questions needed deep reasoning. "
        "For a deeper dive, check the link in the description."
    )

    prompt = (
        "Cinematic talking-head portrait of a poised, warm, professional woman hosting a healthcare podcast "
        "from a sleek modern broadcast desk. She looks directly at the viewer with a subtle, confident smile "
        "and speaks with slow, deliberate facial motion for clear lip-sync. Natural subtle head nods, gentle "
        "hand gestures, and expressive but controlled eyebrows. Soft studio lighting, shallow depth of field, "
        "high production value, photorealistic. Upper-body framing, steady locked-off camera, no text overlays, "
        "no logos, no extra people, no fast cuts. Calm, authoritative, approachable delivery. Premium podcast aesthetic."
    )
    negative = (
        "blurry face, distorted face, extra limbs, deformed hands, text, watermark, logo, harsh lighting, "
        "overexposed, underexposed, fast motion, shaky camera, multiple people, cartoon, anime, painting, "
        "oversaturated, hand over mouth, looking away from camera"
    )

    audio1 = ROOT / "audio" / "seg1_jessica.mp3"
    audio2 = ROOT / "audio" / "seg2_jessica.mp3"
    audio1.parent.mkdir(parents=True, exist_ok=True)

    tts(seg1_text, audio1)
    tts(seg2_text, audio2)

    q1 = queue_seedance(audio1, prompt, negative, "15s")
    q2 = queue_seedance(audio2, prompt, negative, "15s")

    state = {
        "seg1_queue_id": q1,
        "seg2_queue_id": q2,
        "model": "seedance-2-0-enhanced-reference-to-video",
    }
    state_path = HOST_DIR / "queue_state.json"
    state_path.write_text(json.dumps(state, indent=2))
    print(f"Queue state saved to {state_path}")
    print("Run: python poll.py host_video/queue_state.json host_video")


if __name__ == "__main__":
    main()
