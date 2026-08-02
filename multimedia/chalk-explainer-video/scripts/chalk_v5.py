#!/usr/bin/env python3
"""
Chalk v5 — Professional Watercolor Explainer Video Generator
First-frame/last-frame interpolation + TTS voiceover + background music

Pipeline:
  1. Scene Planner (Chat API) -> N content scenes + 1 summary scene
  2. Generate background music (Venice Music API)
  3. For each scene (parallel):
     a. First Frame: title-only image (Grok Imagine Pro)
     b. Last Frame: fully illustrated image (Grok Imagine Pro)
     c. TTS Voiceover: narration explaining the topic (ElevenLabs)
     d. Video Interpolation: first->last frame (Seedance 2.0)
  4. Combine video + TTS + background music (ffmpeg)
  5. Concatenate all scenes -> final MP4

Requirements:
  - Venice API key (env VENICE_API_KEY or hermes config)
  - ffmpeg + ffprobe
  - Python 3 with requests
"""

import requests, json, base64, subprocess, os, sys, time, re, concurrent.futures
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

# Read API key from hermes config or env
def get_api_key():
    if os.environ.get("VENICE_API_KEY"):
        return os.environ["VENICE_API_KEY"]
    try:
        result = subprocess.run(
            ["grep", "-o", "VENICE_INFERENCE_KEY_[A-Za-z0-9]*", os.path.expanduser("~/.hermes/config.yaml")],
            capture_output=True, text=True
        )
        return result.stdout.strip()
    except Exception:
        return os.environ.get("VENICE_API_KEY", "")

KEY = get_api_key()
HEADERS = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
BASE = "https://api.venice.ai/api/v1"

# ─── Config ──────────────────────────────────────────────────────────────────

CHAT_MODEL = "zai-org-glm-5-2"
IMAGE_MODEL = "grok-imagine-image-quality"
VIDEO_MODEL = "seedance-2-0-image-to-video"
VIDEO_FALLBACK = "kling-o3-pro-image-to-video"
TTS_MODEL = "tts-elevenlabs-turbo-v2-5"
TTS_VOICE = "Charlotte"

CLIP_DURATION = "6s"
IMAGE_RESOLUTION = "2K"
ASPECT_RATIO = "16:9"
NUM_SCENES = 6
MUSIC_VOLUME_DB = -20

# ─── Styles ──────────────────────────────────────────────────────────────────

PALETTE_AIPHARMA = (
    "Use ONLY this color palette: "
    "#F0E6D2 cream beige (dominant base, warm parchment-like), "
    "#E6E6D2 soft sand, #E6DCC8 tan, #E6DCD2 warm beige, "
    "#BED2C8 desaturated sage teal (accent, sparingly), "
    "#F0E6DC pale warm cream, "
    "#1B2A4A navy blue (all line art, icons, arrows, text), "
    "#2C4A3E dark teal (body text), "
    "#B2541A burnt orange (one accent element only)"
)

STYLE_PROFESSIONAL = (
    "Professional watercolor infographic illustration, medical scientific aesthetic, "
    "clean and refined, corporate editorial quality, NOT whimsical NOT storybook, "
    "warm parchment-like cream background with subtle paper texture, "
    "thin navy blue line art for all icons, diagrams, and arrows, "
    "soft watercolor washes in muted teal and warm beige tones as background fills, "
    "controlled professional watercolor, minimal bleeding, smooth gradients, "
    "scientific illustration quality, hand-drawn but precise and polished"
)

STYLE_WHIMSICAL = (
    "Professional watercolor whimsical illustration, storybook art style, "
    "soft flowing watercolor paints, visible brush strokes, warm and inviting palette, "
    "charming and delightful, Studio Ghibli meets Beatrix Potter aesthetic"
)

STYLE_CHALKBOARD = (
    "Chalkboard illustration, white and colored chalk on dark black-green slate, "
    "dusty chalk texture, hand-drawn chalk handwriting, educational chalkboard style"
)

STYLES = {
    "professional_watercolor": (STYLE_PROFESSIONAL, PALETTE_AIPHARMA),
    "watercolor_whimsical": (STYLE_WHIMSICAL, PALETTE_AIPHARMA),
    "chalkboard": (STYLE_CHALKBOARD, ""),
}

# ─── Venice API ─────────────────────────────────────────────────────────────

def venice_chat(msgs, model=CHAT_MODEL, temp=0.7, max_tokens=4096):
    r = requests.post(f"{BASE}/chat/completions", headers=HEADERS,
        json={"model": model, "messages": msgs, "temperature": temp, "max_tokens": max_tokens},
        timeout=300)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def venice_image(prompt, model=IMAGE_MODEL):
    r = requests.post(f"{BASE}/image/generate", headers=HEADERS, json={
        "model": model, "prompt": prompt, "aspect_ratio": ASPECT_RATIO,
        "resolution": IMAGE_RESOLUTION, "format": "png", "return_binary": False
    }, timeout=300)
    r.raise_for_status()
    return r.json()["images"][0]

def venice_tts(text, model=TTS_MODEL, voice=TTS_VOICE):
    r = requests.post(f"{BASE}/audio/speech", headers=HEADERS, json={
        "model": model, "input": text, "voice": voice,
        "response_format": "mp3", "speed": 1.0
    }, timeout=300)
    r.raise_for_status()
    return r.content

def venice_music_queue(prompt, duration=30):
    r = requests.post(f"{BASE}/audio/queue", headers=HEADERS, json={
        "prompt": prompt, "duration": duration
    }, timeout=60)
    r.raise_for_status()
    return r.json()

def venice_music_retrieve(qid):
    r = requests.post(f"{BASE}/audio/retrieve", headers=HEADERS,
        json={"queue_id": qid}, timeout=60)
    ct = r.headers.get("Content-Type", "")
    if "audio" in ct:
        return r.content
    return None

def venice_video_queue(first_b64, last_b64, prompt, model=VIDEO_MODEL, duration=CLIP_DURATION):
    first_url = f"data:image/png;base64,{first_b64}"
    last_url = f"data:image/png;base64,{last_b64}"
    body = {"model": model, "prompt": prompt, "image_url": first_url,
            "end_image_url": last_url, "duration": duration}
    r = requests.post(f"{BASE}/video/queue", headers=HEADERS, json=body, timeout=60)
    if r.status_code != 200:
        body2 = {"model": VIDEO_FALLBACK, "prompt": prompt,
                 "image_url": first_url, "duration": duration}
        r = requests.post(f"{BASE}/video/queue", headers=HEADERS, json=body2, timeout=60)
    r.raise_for_status()
    return r.json()

def wait_for_video(qid, dl, model, timeout=600):
    start = time.time()
    polls = 0
    while time.time() - start < timeout:
        polls += 1
        r = requests.post(f"{BASE}/video/retrieve", headers=HEADERS,
            json={"model": model, "queue_id": qid}, timeout=60)
        ct = r.headers.get("Content-Type", "")
        if "video/mp4" in ct:
            return r.content
        try:
            data = r.json()
            status = data.get("status", "UNKNOWN")
        except:
            status = "UNKNOWN"
        if status == "COMPLETED" and dl:
            return requests.get(dl, timeout=120).content
        if polls % 6 == 1:
            print(f"    {status} ({time.time()-start:.0f}s)")
        time.sleep(5)
    return None

def get_duration(path):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True)
    return float(r.stdout.strip())

# ─── Scene Planning ─────────────────────────────────────────────────────────

def plan_scenes(topic, num_scenes):
    print(f"\nPlanning {num_scenes} scenes for: '{topic}'...")
    system = ("You are an expert scriptwriter for professional explainer videos. "
              "You break topics into clear, engaging scenes with voiceover narration. "
              "Respond with ONLY a JSON array.")
    user = f'''Create {num_scenes} content scenes + 1 summary scene about: "{topic}"

For each content scene:
  "title": short title (2-5 words)
  "narration": 2-4 sentences (25-50 words) explaining the concept, with a transition to the next scene
  "image_prompt": all visual elements for the fully illustrated frame
  "video_prompt": order elements should be drawn

For the summary scene (last):
  "title": "Key Takeaways"
  "narration": recap of all main points + closing thought (30-50 words)
  "image_prompt": summary card with 3-4 bullet points
  "video_prompt": "Each takeaway point appears one by one"

Return ONLY a JSON array of {num_scenes + 1} objects.'''
    raw = venice_chat([{"role": "system", "content": system}, {"role": "user", "content": user}])
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    scenes = json.loads(text)
    print(f"  Planned {len(scenes)} scenes:")
    for i, s in enumerate(scenes):
        print(f"    {i+1}. {s['title']}")
    return scenes

# ─── Frame Prompts ──────────────────────────────────────────────────────────

def first_prompt(scene, style, palette):
    return (f"{style}. {palette}. A clean surface with only the title at the top: "
            f'"{scene["title"]}". Thin accent line beneath. '
            "Rest is completely clean and empty. No icons, no diagrams. Minimalist, professional.")

def last_prompt(scene, style, palette):
    return (f"{style}. {palette}. Fully illustrated frame about {scene['title']}. "
            f'Title at top: "{scene["title"]}" with thin accent line. '
            f"{scene['image_prompt']}. "
            "Same layout and surface as first frame, just fully illustrated.")

def video_prompt(scene):
    return (f"The illustration is drawn progressively from just the title to fully illustrated. "
            f"{scene.get('video_prompt', '')}. "
            "Natural hand-drawing motion. Smooth progressive drawing.")

# ─── Pipeline ───────────────────────────────────────────────────────────────

def run_pipeline(topic, output_dir, num_scenes=NUM_SCENES, style_name="professional_watercolor",
                  voice=TTS_VOICE, music=True):
    start = time.time()
    style, palette = STYLES.get(style_name, STYLES["professional_watercolor"])
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"{'='*60}")
    print(f"  Chalk v5 | {topic}")
    print(f"  {num_scenes} scenes + summary | {style_name} | Voice: {voice}")
    print(f"  Image: {IMAGE_MODEL} | Video: {VIDEO_MODEL} | TTS: {TTS_MODEL}")
    print(f"{'='*60}")

    # 1. Plan scenes
    scenes = plan_scenes(topic, num_scenes)
    (out / "scenes.json").write_text(json.dumps(scenes, indent=2))
    total_scenes = len(scenes)

    # 2. Background music
    music_path = None
    if music:
        print(f"\nGenerating background music...")
        try:
            music_prompt = ("Soft ambient corporate background music, gentle piano with light strings, "
                           "calm and professional, medical documentary style, no drums, "
                           "very subtle and unobtrusive, warm and inviting")
            mq = venice_music_queue(music_prompt, duration=30)
            mqid = mq.get("queue_id")
            if mqid:
                time.sleep(5)
                music_bytes = venice_music_retrieve(mqid)
                if music_bytes:
                    music_path = out / "music.mp3"
                    music_path.write_bytes(music_bytes)
                    print(f"  Saved music.mp3")
        except Exception as e:
            print(f"  Music generation failed: {e}, continuing without...")

    # 3. Process all scenes in parallel
    print(f"\nProcessing {total_scenes} scenes in parallel...")
    results = [None] * total_scenes

    def process_scene(i):
        scene = scenes[i]
        sdir = out / f"scene_{i+1:02d}"
        sdir.mkdir(exist_ok=True)
        print(f"  Scene {i+1}/{total_scenes}: {scene['title']}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            f1 = ex.submit(venice_image, first_prompt(scene, style, palette))
            f2 = ex.submit(venice_image, last_prompt(scene, style, palette))
            fa = ex.submit(venice_tts, scene["narration"], TTS_MODEL, voice)
            b64_1 = f1.result()
            b64_2 = f2.result()
            audio = fa.result()

        (sdir / "first_frame.png").write_bytes(base64.b64decode(b64_1))
        (sdir / "last_frame.png").write_bytes(base64.b64decode(b64_2))
        (sdir / "narration.mp3").write_bytes(audio)

        vdata = venice_video_queue(b64_1, b64_2, video_prompt(scene))
        qid = vdata["queue_id"]; dl = vdata.get("download_url"); vmodel = vdata["model"]
        print(f"    Queued: {qid[:12]}... ({vmodel})")

        video = wait_for_video(qid, dl, vmodel)
        if video:
            (sdir / "raw_video.mp4").write_bytes(video)
            print(f"    Video ready ({len(video)/1024/1024:.1f}MB)")

            vp = sdir / "raw_video.mp4"
            ap = sdir / "narration.mp3"
            cp = sdir / "combined.mp4"
            v_dur = get_duration(vp)
            a_dur = get_duration(ap)
            if a_dur > v_dur:
                extra = a_dur - v_dur
                vf = f"tpad=stop_mode=clone:stop_duration={extra:.2f},fade=t=out:st={max(a_dur-0.5,0):.2f}:d=0.5"
            else:
                vf = f"fade=t=out:st={max(a_dur-0.5,0):.2f}:d=0.5"
            subprocess.run(["ffmpeg", "-y", "-i", str(vp), "-i", str(ap),
                "-vf", vf, "-t", f"{a_dur:.2f}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                "-map", "0:v:0", "-map", "1:a:0", str(cp)],
                capture_output=True, text=True, timeout=120)
            return cp
        else:
            print(f"    Video FAILED for scene {i+1}")
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(process_scene, i): i for i in range(total_scenes)}
        for f in concurrent.futures.as_completed(futures):
            results[futures[f]] = f.result()

    # 4. Concatenate
    clips = [r for r in results if r is not None]
    if not clips:
        print("No videos generated!")
        return None

    print(f"\nAssembling {len(clips)} clips...")
    final = out / "final.mp4"
    concat = out / "concat.txt"
    with open(concat, "w") as f:
        for c in clips:
            f.write(f"file '{c.absolute()}'\n")

    if music_path and music_path.exists():
        temp_video = out / "temp_no_music.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat), "-c", "copy", str(temp_video)],
            capture_output=True, text=True, timeout=120)
        total_dur = get_duration(temp_video)
        subprocess.run(["ffmpeg", "-y",
            "-i", str(temp_video), "-i", str(music_path),
            "-filter_complex", f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{total_dur},volume={MUSIC_VOLUME_DB}dB,afade=t=out:st={max(total_dur-2,0):.1f}:d=2[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", str(final)],
            capture_output=True, text=True, timeout=120)
        temp_video.unlink(missing_ok=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat), "-c", "copy", str(final)],
            capture_output=True, text=True, timeout=120)

    concat.unlink(missing_ok=True)
    elapsed = time.time() - start
    total_dur = get_duration(final)
    print(f"\n{'='*60}")
    print(f"  Done in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"  Video: {final}")
    print(f"  Duration: {total_dur:.1f}s")
    print(f"  {total_scenes} scenes, {style_name}")
    print(f"  Voiceover: {voice}")
    print(f"  Background music: {'yes' if music_path else 'no'}")
    print(f"{'='*60}")
    return final

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "AI in Pharma"
    out = sys.argv[2] if len(sys.argv) > 2 else "output/chalk_video"
    run_pipeline(topic, out)
