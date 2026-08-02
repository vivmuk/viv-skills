# Anniversary Dance Battle session recipe

Date: 2026-07-04

## What worked

Still-photo composite with generated patriotic background, side-by-side couple
photos, animated text in bottom third, red/white/blue border, and procedural
music.

## What failed

- Kling R2V with full photos: faces generic/waxy.
- Kling R2V with 4 face crops: invented a 5th person, changed clothing, still
  generic faces.

## Key commands

See project folder `/home/vivgates/anniversary-dance-battle/`:
- `scripts/assemble_video_v2.py` — FFmpeg composite
- `scripts/gen_music.py` — procedural music

## Lessons

- Kling R2V does not accept `resolution`.
- Face-crop R2V unreliable for 3+ people in dynamic scenes.
- Keep text in bottom third.
- Venice has no `/audio/music` endpoint.
