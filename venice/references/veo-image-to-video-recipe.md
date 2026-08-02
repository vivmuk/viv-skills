# Veo 3.1 Image-to-Video — Face Preservation Recipe

## When to use this

The user has a selected character portrait (a generated or real photo) and wants
to create a video of that exact person speaking dialogue. Text-to-video generates
a new face each time; `style_references` on krea/luma does NOT preserve identity.
Image-to-video with `veo3.1-fast-image-to-video` passes the photo as the starting
frame, so the character's face is the anchor.

## Model: `veo3.1-fast-image-to-video`

- **Endpoint:** `POST /api/v1/video/queue`
- **Key field:** `image_url` — data URL (`data:image/jpeg;base64,...`) or http URL
- **Aspect ratio:** Inherited from the input image (no `aspect_ratio` field needed)
- **Durations:** `"4s"`, `"6s"`, `"8s"`
- **Resolutions:** `"720p"`, `"1080p"`, `"4k"`
- **Audio:** `"audio": true` (native, configurable)
- **Retrieve:** `POST /api/v1/video/retrieve` with `model` + `queue_id` (both required)

## API call shape

```python
import json, base64, urllib.request, time

with open(os.path.expanduser("~/.openclaw/auth-profiles.json")) as f:
    key = json.load(f)["profiles"]["venice:default"]["key"]

# Read reference image
with open("selected_portrait.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

payload = {
    "model": "veo3.1-fast-image-to-video",
    "prompt": prompt,  # see prompt structure below
    "image_url": f"data:image/jpeg;base64,{img_b64}",
    "duration": "8s",
    "resolution": "720p",
    "audio": True
}

# Queue
req = urllib.request.Request(
    "https://api.venice.ai/api/v1/video/queue",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=30) as resp:
    queue_id = json.loads(resp.read())["queue_id"]

# Poll (MUST include model field)
for i in range(30):
    time.sleep(10)
    req2 = urllib.request.Request(
        "https://api.venice.ai/api/v1/video/retrieve",
        data=json.dumps({"model": "veo3.1-fast-image-to-video", "queue_id": queue_id}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req2, timeout=30) as resp2:
        ct = resp2.headers.get("content-type", "")
        rdata = resp2.read()
        if "video" in ct or "mp4" in ct:
            with open("output.mp4", "wb") as f:
                f.write(rdata)
            break
        # else: JSON with status "PROCESSING"
```

## Prompt structure for non-English dialogue reels

Structure the prompt in this order (validated with Kathiawadi Gujarati):

1. **Language lead** (native script) — tells Veo what language to speak
2. **Character description** — exact visual details from the reference image
   (face, skin tone, eyes, hair, jewelry, clothing). The image_url anchors
   identity, but the prompt guides clothing changes (e.g., different saree color)
   and scene setup.
3. **Action/camera** — what the character does (sitting, walking, gestures)
4. **Dialogue** (native script) — the exact line to speak, in quotes
5. **Delivery direction** — tone progression, expression at punchline
6. **Lighting/style** — diffuse, overcast, color grading, texture notes

### Example prompt (Kathiawadi Gujarati double-meaning reel)

```
ગુજરાતી કાઠિયાવાડી ભાષામાં બોલતી છોકરી મજાકિયા બમણા અર્થવાળો જોક કહે છે.

The woman from the reference image sits on a stone boundary wall of a sugarcane
field, legs dangling casually. She wears a deep red velvet bandhani saree with
small white and gold circular motifs, wide ornate gold zari border, draped in
classic Nivi style with pallu over left shoulder. Matching deep red velvet blouse
with thin spaghetti straps and deep V-neckline. Gold jhumka earrings with dangling
pearls, delicate gold pendant necklace, gold and red bangles. Long jet-black wavy
hair with white jasmine flowers tucked behind right ear. No bindi — bare forehead,
clean skin.

She holds the camera selfie-style in her right hand, slightly angled. She speaks
directly to camera with high-energy Kathiawadi Gujarati rural accent, animated
expressions, frequent smiles showing teeth, playful mischievous grin. She
gestures expressively with her left hand, occasionally kicking her dangling legs
playfully.

She says with perfect timing and naughty delivery: "જો બહેન, મારે ગામમાં વાળા
કહે છે - દૂધ તો બધા દોહે, પણ છાશ તો એને મળે છે જે મથાતા મથાતા ગરમ થઈ જાય!"

Build from casual conversational tone to cheeky punchline on "ગરમ થઈ જાય" with
a big naughty smile and sparkle in her eyes.

Overcast cloudy day, soft diffuse light, even illumination with no harsh shadows,
bright but not overwhelming. Vibrant saturated greens and reds, cinematic rural
beauty, authentic viral Instagram reel energy, playful naughty double-meaning
Kathiawadi comedy, sharp detail, realistic textures on saree and skin.
```

## User prompt preferences (July 2026)

1. **Show prompt before generating.** User wants to review and edit the full
   prompt before any video is generated. Present the prompt in a code block,
   note what changed from the previous version, then ask for edits or
   confirmation. Do NOT generate until the user says "let's create it" or
   similar.
2. **No commentary when asked for just the prompt.** When the user says "give me
   the prompt" or "don't try to say anything," return ONLY the prompt in a code
   block. No preface, no explanation, no "here's the prompt:" — just the prompt.
3. **Lighting preference: diffuse/overcast.** User does NOT want golden hour or
   harsh midday sun. Use "overcast cloudy day, soft diffuse light, even
   illumination with no harsh shadows, bright but not overwhelming."
4. **Scene description can be separated from the prompt.** User may ask to
   remove the scene/location paragraph and control it separately. Be ready to
   strip or add paragraphs on request.
5. **I2V: don't re-describe facial features.** When using image-to-video, the
   reference image already anchors the character's identity. Do NOT include
   detailed facial descriptions (face shape, skin tone, eye shape, nose, lips,
   etc.) — just say "the exact same girl from the reference image." Keep
   clothing/jewelry/hair descriptions only if you need to CHANGE them from the
   reference (e.g., different saree color, remove bindi).
6. **No "raised eyebrows."** User does not want "raised eyebrows" in expression
   direction. Use "playful mischievous grin" and "big naughty smile and sparkle
   in her eyes" without the eyebrow cue.
7. **Dialect variants.** User has used both **Kathiawadi Gujarati** and
   **Surati Gujarati** dialects. The language lead line, accent description,
   and joke content should all match the requested dialect. Examples:
   - Kathiawadi: `ગુજરાતી કાઠિયાવાડી ભાષામાં બોલતી છોકરી...`
   - Surati: `ગુજરાતી સુરતી ભાષામાં બોલતી છોકરી...`
   Adjust the accent description ("Kathiawadi Gujarati rural accent" vs "Surati
   Gujarati accent") and comedy style tag accordingly.

### Example prompt (Surati Gujarati double-meaning reel, I2V with image_url)

When using image-to-video, the prompt does NOT need facial descriptions — the
reference image anchors identity. Just say "the exact same girl from the
reference image" and describe only what CHANGES (clothing, scene, action).

```
ગુજરાતી સુરતી ભાષામાં બોલતી છોકરી મજાકિયા બમણા અર્થવાળો જોક કહે છે.

The exact same girl from the reference image sits on a stone boundary wall of a
sugarcane field, legs dangling casually. She wears a deep red velvet bandhani
saree with small white and gold circular motifs, wide ornate gold zari border,
draped in classic Nivi style with pallu over left shoulder. Matching deep red
velvet blouse with thin spaghetti straps and deep V-neckline. Gold jhumka
earrings with dangling pearls, delicate gold pendant necklace, gold and red
bangles. Long jet-black wavy hair with white jasmine flowers tucked behind right
ear. No bindi — bare forehead, clean skin.

She holds the camera selfie-style in her right hand, slightly angled. She speaks
directly to camera with high-energy Surati Gujarati accent, animated expressions,
frequent smiles showing teeth, playful mischievous grin. She gestures
expressively with her left hand, occasionally kicking her dangling legs playfully.

She says with perfect timing and naughty delivery: "અરે બહેન, સુરતમાં તો વાળા
કહે ને - પાણી તો બધા પીએ, પણ ધાબળો એને જોઈએ જે બને ત્યારે ભીનો થઈ જાય!"

Build from casual conversational tone to cheeky punchline on "ભીનો થઈ જાય" with
a big naughty smile and sparkle in her eyes.

Overcast cloudy day, soft diffuse light, even illumination with no harsh shadows,
bright but not overwhelming. Vibrant saturated greens and reds, cinematic rural
beauty, authentic viral Instagram reel energy, playful naughty double-meaning
Surati comedy, sharp detail, realistic textures on saree and skin.
```

## I2V API pitfalls (learned July 2026)

- **`aspect_ratio` is rejected.** `veo3.1-fast-image-to-video` returns
  `400 {"details":{"aspect_ratio":{"_errors":["This model does not support
  aspect_ratio"]}}}`. The ratio is always derived from the input image. Omit
  the field entirely.
- **Poisoned queue → 500 on every retrieve.** If the queue submission somehow
  accepts a bad parameter and returns a `queue_id`, every subsequent
  `POST /video/retrieve` returns `500 {"error":"An unknown error occurred"}`
  indefinitely — not the normal `{"status":"PROCESSING"}` JSON. Do NOT keep
  polling. Fix: remove the offending parameter and submit a fresh queue.
- **Platform-wide I2V retrieve outage (July 2026).** ALL image-input video
  models returned 500 on every retrieve call (veo3.1, sora-2, kling-o3-pro,
  happyhorse). Queue submissions succeeded but retrieve always 500'd.
  Text-to-video retrieve worked fine at the same time. If I2V retrieve 500s
  on 2-3 polls, test T2V retrieve — if T2V works, the I2V retrieve path is
  down platform-wide. Fall back to T2V with detailed character description.
- **Sora-2 does NOT accept `audio` param.** Returns 400. Audio is on by default.
- **Reference-to-video needs `image_url`, not `reference_image_urls`.**
  `kling-o3-pro-reference-to-video` returns 400 if you pass
  `reference_image_urls`. Use `image_url` instead.
- **Video credits are separate from image credits.** Image generation can
  return `402 Payment Required` ("API key USD spend limit exceeded") while
  video generation still works. Do not assume all Venice API calls are blocked.

## What does NOT work for face preservation

- **gpt-image-2** (text-to-image): new face every generation, no reference input
- **krea-v2-large style_references** (strength 0.85): preserves aesthetic style,
  NOT face identity — user said "completely wrong face"
- **luma-uni-1-max style_references** (strength 1.0): same issue — "completely
  wrong face"
- **firered-image-edit** (`/image/edit` endpoint): outputs garbled/blurry 254KB
  images with no recognizable content. Both JSON and multipart uploads produce
  garbage.

## Timing

- Video generation: ~70-100 seconds (7-10 polls at 10s intervals)
- Submit + poll script should run as background process with notify_on_complete
