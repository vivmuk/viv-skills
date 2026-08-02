# Video-to-video composite session: adding a cowboy to a club video

Session: 2026-07-12  
Models tested: `grok-imagine-video-to-video-private`, `wan-2-7-video-to-video`

## Goal

Add a rugged muscular bearded cowboy (from a source photo) into an existing 7.4s vertical club video, positioned directly behind the woman with the white bag and grey shirt, dancing/grinding.

## Source media

- Input video: `/home/vivgates/.hermes/video_cache/video_94b4101e9f0a.mp4`
  - 720×1280, 7.4s, ~24 fps, indoor nightclub scene with two women dancing.
- Cowboy reference photo: `/home/vivgates/.hermes/cache/images/img_564a05d01e89.jpg`
  - Rugged muscular man, brown cowboy hat, sleeveless denim vest (later requested shirtless), coiled rope, cream enamel mug, ranch setting.

## Key API findings

### `grok-imagine-video-to-video-private`

- Accepts `video_url` (data URL), `prompt`, `negative_prompt`, `duration`, `resolution`.
- Queue response includes `download_url`:
  ```json
  {"model":"grok-imagine-video-to-video-private","queue_id":"019f5620-...","download_url":"https://private-share.venice.ai/v1/share/..."}
  ```
- In this session, `/video/retrieve` repeatedly returned `{"status": "COMPLETED"}` JSON and never switched to `video/mp4`. Download succeeded only by using the `download_url` fallback.
- Output: 720p, 7.4s, 4.0 MB.
- Result: cowboy appeared, but in an outdoor/ranch setting rather than the indoor club.

### `wan-2-7-video-to-video`

- Accepts `video_url`, `prompt`, `negative_prompt`, `resolution`.
- `duration` is auto-derived from input video; do not pass it.
- Queue response does **not** include a `download_url`:
  ```json
  {"model":"wan-2-7-video-to-video","queue_id":"019f5626-..."}
  ```
- `/video/retrieve` eventually returned `video/mp4` after ~6–7 minutes of polling.
- Output: 720p, 7.4s, 4.0–4.2 MB.
- Result: cowboy appeared inside the club, but too far in the background.

## Prompt evolution

1. **Grok attempt:** described ranch setting explicitly — model moved the scene outdoors. Wrong.
2. **Wan attempt 1:** described cowboy "joins them in the background" with relaxed western rhythm. Got cowboy inside club but distant.
3. **Wan attempt 3 — two shirtless cowboys + money shower:** user requested two shirtless cowboys (one Asian, one Caucasian) close behind the target woman, the other woman throwing dollar bills, and no coffee mug. The plan was confirmed before queueing, and the prompt explicitly counted the characters, removed the mug, and added the money. V2V still only loosely controls exact proximity/pose; for exact grinding/hands-on-waist placement, a keyframe composite would be required.

## Durable lessons

- **Plan before queueing.** The user explicitly asked to review the plan before the final run. For V2V positioning tasks, present the exact prompt and intended composition and get confirmation before spending credits.
- **Confirm character count.** When the user says "cowboys" ambiguously, ask whether they want one or multiple figures. V2V does not reliably add extra characters unless the prompt explicitly counts them.
- **Strip unwanted reference-image props/clothing in the prompt.** The cowboy photo included a denim vest and a cream mug. The user had to explicitly ask for "shirtless" and "not holding the coffee cup"; otherwise the model carried the vest/mug into the output.
- **V2V composition threshold:** V2V models preserve the original video well when asked to add **one simple character or element** (e.g. one cowboy joining a club scene). Once the prompt demands **multiple new characters + specific poses + new props** (e.g. two cowboys + dollar bills + exact hand placement), the model stops editing-in-place and rewrites the whole scene as a new tableau. Keep V2V prompts minimal; do multi-element compositions in post or via I2V/R2V.
- **Thin/detailed props in V2V:** V2V hallucinates flat, sticker-like versions of objects such as falling paper money, playing cards, or confetti. These lack physics, proper lighting, and temporal consistency. For realistic props, composite real stock footage overlays in FFmpeg/MoviePy instead of relying on V2V.
- **V2V spatial precision is limited.** Phrases like "directly behind her," "very close," "grinding," "hands near her waist" nudge composition but cannot guarantee exact pose or contact. For precise placement, composite a keyframe and use I2V/R2V instead.

## Reusable scripts

- `/home/vivgates/v2v_cowboy/run_grok_v2v.py`
- `/home/vivgates/v2v_cowboy/run_wan_v2v.py`
