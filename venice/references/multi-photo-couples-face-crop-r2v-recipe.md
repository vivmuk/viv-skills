---
name: multi-photo-couples-face-crop-r2v-recipe
description: |
  Worked recipe for combining multiple couples from separate photos into one
  coordinated scene using Venice Kling O3 Pro reference-to-video. The key
  technique is extracting tight face crops from each source photo and passing
  them as individual `elements[].frontal_image_url` references, which preserves
  face likeness far better than full-body or whole-photo references.
tags:
  - venice
  - video
  - r2v
  - kling
  - multi-person
  - couples
  - face-likeness
  - face-crop
  - anniversary
---

# Multi-Photo Couples → One Coordinated Scene (Face-Crop R2V Recipe)

Use this recipe when a user gives you **two or more separate photos**, each
containing one or more people, and asks to show all of them together in one
scene (e.g., a dance battle, celebration, group dance) while preserving face
likeness.

## Why this is different from single-photo multi-person

- Source people are in **different images**, so the model cannot infer their
  relative scale/composition from one shared background.
- Face likeness is usually the user's top priority.
- Full-body references often fail because the model gets distracted by
  clothing, pose, and background; **tight face crops** give a stronger identity
  signal.

## Worked example: Anniversary dance battle

Inputs:
- Photo 1: couple in outdoor garden, man in red kurta, woman in peach outfit
- Photo 2: couple at indoor garba, woman in orange/pink lehenga, man in orange
  kurta with dandiya stick

Desired output: 16:9 video, 20–30s, all four people dancing together in front
of a large American flag, patriotic 4th of July / anniversary celebration.

## Workflow

1. **Extract face crops.** For each person, crop a tight rectangle around the
   head and upper shoulders from their source photo. Save as individual JPEGs:
   `toshal.jpg`, `garima.jpg`, `april.jpg`, `div.jpg`.

   ```python
   from PIL import Image
   img = Image.open("photo1.jpg")
   w, h = img.size
   crop = img.crop((int(w*0.18), int(h*0.05), int(w*0.50), int(h*0.55)))
   crop.save("toshal.jpg", quality=95)
   ```

2. **Queue Kling O3 Pro R2V with one element per face.**

   ```python
   import base64, requests, yaml, time
   from pathlib import Path

   with open(Path.home() / ".hermes/config.yaml") as f:
       api_key = yaml.safe_load(f)["model"]["api_key"]

   faces = ["toshal.jpg", "garima.jpg", "april.jpg", "div.jpg"]

   def data_url(path):
       b64 = base64.b64encode(Path(path).read_bytes()).decode()
       return f"data:image/jpeg;base64,{b64}"

   headers = {
       "Authorization": f"Bearer {api_key}",
       "Content-Type": "application/json",
   }

   payload = {
       "model": "kling-o3-pro-reference-to-video",
       "prompt": (
           "Four friends, two couples, dancing together in a patriotic American celebration. "
           "A huge waving American flag fills the background. Red, white, and blue confetti. "
           "TikTok-style energetic dance battle, everyone smiling and moving to the beat. "
           "Bright cinematic lighting, photorealistic, 16:9, high energy, 4th of July party."
       ),
       "negative_prompt": "distorted faces, extra limbs, blurry, low quality, cartoon, anime",
       "duration": "10s",
       "aspect_ratio": "16:9",
       "elements": [
           {"frontal_image_url": data_url(f)} for f in faces
       ],
   }

   q = requests.post(
       "https://api.venice.ai/api/v1/video/queue",
       headers=headers,
       json=payload,
       timeout=300,
   ).json()
   queue_id = q["queue_id"]
   ```

3. **Poll with `/video/retrieve`.**

   ```python
   while True:
       r = requests.post(
           "https://api.venice.ai/api/v1/video/retrieve",
           headers=headers,
           json={"model": payload["model"], "queue_id": queue_id},
           timeout=120,
       )
       if r.headers.get("Content-Type") == "video/mp4":
           Path("output.mp4").write_bytes(r.content)
           break
       status = r.json().get("status")
       if status in ("FAILED", "CANCELLED"):
           print("Terminal:", status, r.text)
           break
       time.sleep(20)
   ```

4. **Verify face likeness before batching.** Generate one 10s test clip first.
   Extract frames and ask the user: "Do these faces look right?" Only after
   approval queue the remaining clips.

5. **Post-production.** Concatenate approved clips in FFmpeg. Add the flying
   text overlay and background music:

   ```bash
   ffmpeg -y -i clip1.mp4 -i clip2.mp4 -filter_complex \
     "[0:v][1:v]concat=n=2:v=1:a=0[v]; \
      [v]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf: \
      text='Happy anniversary to Toshal and Garima and April and Div': \
      fontcolor=white:fontsize=64:box=1:boxcolor=red@0.6:boxborderw=12: \
      x='(w-text_w)/2':y='(h*0.15)':enable='between(t,2,8)'[out]" \
     -map "[out]" -map 0:a -c:v libx264 -crf 23 -c:a aac final.mp4
   ```

### Limitation discovered 2026-07-04

Face-crop R2V works well for **one or two people** in a controlled scene. For a
**4-person dynamic TikTok-style dance battle** with a busy patriotic
background, Kling O3 Pro R2V:
- invented a 5th person,
- changed everyone's clothing,
- produced generic, smoothed faces that did not match the source people.

When face likeness is critical and the scene involves **more than 2 people in
fast motion**, fall back to a still-photo composite + animation instead of
forcing R2V to generate the whole scene. See
`references/still-photo-patriotic-composite-recipe.md`.

## Why face crops beat full-body references

| Reference type | Likeness quality | Best for |
|---|---|---|
| Original full-body photo | Medium | Single-person, scene context matters |
| Full-body cutout | Medium–Low | Compositing, not R2V input |
| **Tight face crop** | **High** | **Face-exact preservation in group scenes (1–2 people)** |
| Studio-style generated portrait | Low–Medium | Stylized output, not identity preservation |

The model's identity mechanism focuses on facial structure, skin tone, hair,
and expression. A tight crop removes competing signals (background, clothing,
limbs) and gives the cleanest reference.


## Field/model notes

- Use `kling-o3-pro-reference-to-video` for real-people face preservation.
- Kling R2V uses `elements[].frontal_image_url` — one element per face.
- **Do not pass `resolution`** to `kling-o3-pro-reference-to-video`; it returns
  `400 "This model does not support resolution"`. Use `aspect_ratio` and
  `duration` only.
- Seedance R2V frequently `422`s on real-people photos; avoid for this use
  case.

## Pitfalls

- **Queueing all clips before verifying one.** Always generate a single test
  clip and confirm likeness with the user.
- **Using generated reference portraits.** `gpt-image-2` stylized portraits do
  not preserve identity; use original photo face crops.
- **Expecting perfect hands/fingers in fast dance scenes.** R2V still struggles
  with rapid full-body motion; accept some blur or use slower, more posed dance
  prompts.
- **Assuming music generation exists.** Venice has no `/audio/music` endpoint.
  Source royalty-free music externally or from the user.

## Variations

- **More than 4 people:** Same pattern; add one face-crop element per person.
  Test one clip first — likeness degrades as group size grows.
- **Different themes:** Change the prompt and background. The face-crop
  reference pattern works for weddings, reunions, holiday cards, etc.
- **TikTok vertical:** Use `aspect_ratio: "9:16"` and prompt for vertical
  framing.

## Reuse

The same face crops can drive:

- Static anniversary/party graphics.
- Avatar-style talking-head clips via Wan I2V with a generated first frame.
- Future re-edits with different backgrounds or text overlays.
