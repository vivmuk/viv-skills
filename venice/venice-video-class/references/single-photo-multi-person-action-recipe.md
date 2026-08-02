---
name: single-photo-multi-person-action-recipe
description: |
  Worked recipe for extracting multiple people from a single photo and animating
  them together via Venice API reference-to-video (Kling O3 Pro). Covers
  background removal, cutout verification, model/field selection, prompt
  construction, queue/poll code, and post-generation checks.
tags:
  - venice
  - video
  - r2v
  - kling
  - multi-person
  - action-animation
  - background-remove
---

# Single Photo → Multi-Person Action Animation (Venice API)

Use this recipe when a user gives you one photo with two or more people and
asks to "extract them" and show them doing something together — karate,
dancing, sports, etc.

## Quick workflow

1. **Describe the image first.** Use a vision-capable Venice chat model
   (e.g. `grok-4-20`) to identify each person's age, ethnicity, hair, clothing,
   expression, and relative position. You need these details for the prompt.
2. **Background-remove the source** with `POST /image/background-remove` to get
   a pixel-exact RGBA cutout. Save it as an asset even if you queue with the
   original JPEG — the cutout is useful for downstream edits.
3. **Verify the cutout.** Composite it over a neutral grey background and, for
   production work, build the 3-panel comparison (original | cutout-on-grey |
   studio render) described in `r2v-reference-preparation.md`.
4. **Queue `kling-o3-pro-reference-to-video`.** Pass the **original photo** in
   the Kling R2V structure:
   - `elements[0].frontal_image_url`: data URL of the original photo
   - `elements[0].reference_image_urls`: same data URL (or tight crops if you
     want stronger face focus)
   - `aspect_ratio` and `duration` as supported by the model.
5. **Prompt construction.** Name each person concretely, describe clothing
   changes (e.g. "now wearing white karate gis with black belts"), and specify
   coordinated action, setting, and camera style.
6. **Poll with `POST /video/retrieve`.** Stop when `Content-Type` becomes
   `video/mp4` or `status` is terminal.
7. **Inspect the result** with `ffprobe` and, if acceptable, deliver it.

## Why Kling O3 Pro R2V for this case

- Handles multiple subjects in one reference image better than avatar-focused
  pipelines that assume a single face.
- `kling-o3-pro-reference-to-video` supports full-body action prompts and
  preserves likeness well when the prompt repeats distinctive traits.
- Seedance R2V variants frequently `422` on real-people photos; Wan I2V does not
  accept `reference_image_urls` for multi-person identity locking.

## Why the original photo, not the cutout

Kling R2V expects a normal photographic reference with background context to
infer scale and composition. The transparent cutout is for **verification and
reuse**, not as the primary `frontal_image_url`. If you queue the cutout, the
model may receive an unusual alpha channel and produce worse results.

## Example queue payload

```python
import base64, requests, yaml, time
from pathlib import Path

with open(Path.home() / ".hermes/config.yaml") as f:
    api_key = yaml.safe_load(f)["model"]["api_key"]

img_path = Path.home() / ".hermes/cache/images/img_d37d79f432ad.jpg"
b64 = base64.b64encode(img_path.read_bytes()).decode()
data_url = f"data:image/jpeg;base64,{b64}"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

payload = {
    "model": "kling-o3-pro-reference-to-video",
    "prompt": (
        "A man and a young boy, both wearing clean white karate gis with black belts, "
        "practice synchronized karate forms together in a bright modern dojo with wooden floors. "
        "They perform crisp punches, defensive blocks, low stances, and finish with a "
        "simultaneous high front kick. The man has short black hair, warm smile, "
        "medium-brown South Asian skin; the boy has short neat black hair with straight bangs, "
        "bright cheerful expression, lighter brown skin. "
        "Cinematic martial arts choreography, stable camera, photorealistic, full-body action."
    ),
    "duration": "10s",
    "aspect_ratio": "9:16",
    "elements": [
        {
            "frontal_image_url": data_url,
            "reference_image_urls": [data_url],
        }
    ],
}

q = requests.post(
    "https://api.venice.ai/api/v1/video/queue",
    headers=headers,
    json=payload,
    timeout=300,
).json()
queue_id = q["queue_id"]

# Poll
while True:
    r = requests.post(
        "https://api.venice.ai/api/v1/video/retrieve",
        headers=headers,
        json={"model": payload["model"], "queue_id": queue_id},
        timeout=120,
    )
    if r.headers.get("Content-Type") == "video/mp4":
        Path("karate_output.mp4").write_bytes(r.content)
        break
    status = r.json().get("status")
    if status in ("COMPLETED", "FAILED", "CANCELLED"):
        print("Terminal:", status, r.text)
        break
    time.sleep(30)
```

## Prompting tips

- **Repeat distinguishing features for each person.** Kling pays attention to
  what you name; generic descriptions drift.
- **State clothing changes explicitly.** The reference shows street clothes, but
  you want karate gis — say so.
- **Anchor the setting.** A "bright modern dojo" prevents the model from keeping
  the living-room couch from the source photo.
- **Specify camera behavior.** "Stable camera" reduces unwanted zoom or motion.
- **Use a `negative_prompt` if the model supports it** to exclude distortion,
   extra limbs, or cartoon styles.

## Field-name gotcha

Kling R2V uses `elements[].frontal_image_url` + `elements[].reference_image_urls`.
Grok R2V uses a flat `reference_image_urls[]`. Sending the flat array to Kling
returns `400` ("At least one visual input is required"). Always match the model
family to its documented structure.

## Output verification

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,avg_frame_rate,duration \
  -of default=noprint_wrappers=1 karate_output.mp4
```

Expected: width/height matching the requested aspect ratio, duration close to
`duration` value, non-zero frame rate.

## Variations

- **More than two people:** Same pattern works; keep descriptions short but
  distinctive per person. If face fidelity degrades, add tight face crops to
  `reference_image_urls`.
- **Landscape output:** Use `aspect_ratio: "16:9"` and adjust the prompt framing
  ("wide shot of both subjects").
- **Longer action:** Generate multiple 10–15s clips with overlapping action and
  concatenate in FFmpeg. R2V clips rarely loop perfectly; plan transitions or
  cuts between clips.

## Reuse

The transparent cutout saved in step 2 can also drive:

- Static composites (place subjects on a new background).
- Future avatar/talking-head clips via Wan I2V with a generated first frame.
- Marketing graphics where the subjects must stay pixel-exact.

Store cutouts in a project folder alongside the source image for easy reuse.
