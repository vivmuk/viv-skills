# Venice API Endpoints Used

## Chat Completions
`POST /chat/completions`
- Used for scene planning
- OpenAI-compatible
- Fields: `model`, `messages`, `temperature`, `max_tokens`

## Image Generation
`POST /image/generate`
- Used for first/last frame generation
- Fields: `model`, `prompt`, `aspect_ratio`, `resolution`, `format`, `return_binary`
- Returns: `{ "images": ["base64_png_string"] }`

## TTS (Text-to-Speech)
`POST /audio/speech`
- Used for narration voiceover
- Fields: `model`, `input`, `voice`, `response_format`, `speed`
- Returns: raw audio bytes (mp3)

## Music Generation (async)
`POST /audio/queue` — queue music generation
- Fields: `prompt`, `duration`
- Returns: `{ "queue_id": "..." }`

`POST /audio/retrieve` — poll for completion
- Fields: `queue_id`
- Returns: raw audio bytes when complete

## Video Generation (async)
`POST /video/queue` — queue video generation
- Fields: `model`, `prompt`, `image_url` (first frame), `end_image_url` (last frame), `duration`
- Returns: `{ "model": "...", "queue_id": "...", "download_url": "..." }`
- Note: Seedance does NOT accept `aspect_ratio`

`POST /video/retrieve` — poll for completion
- Fields: `model`, `queue_id`
- Returns: `video/mp4` binary when complete, or `{ "status": "PROCESSING" }`

`POST /video/complete` — cleanup after download
- Fields: `model`, `queue_id`

## Base URL
`https://api.venice.ai/api/v1`

## Auth
`Authorization: Bearer <VENICE_API_KEY>`

## Model Discovery
`GET /models?type=video` — list video models with constraints
`GET /models?type=tts` — list TTS models with voices
`GET /models?type=image` — list image models with pricing

Never hardcode model IDs — they rotate. Use `GET /models/traits` for trait-based resolution.
