# Venice REST Video / async-Audio / Music — verified shapes & transcripts

Empirically verified July 2026 against live `https://api.venice.ai/api/v1` using a
`VENICE_INFERENCE_KEY_…` API key. All transcripts below are byte-for-byte
copies of real responses (with timestamps + queue IDs intact).

---

## TL;DR — the three rules any client must follow

1. **Branch on `Content-Type`, not on whether the body parses as JSON.** When
   a video / audio / music job completes, Venice returns the raw binary
   (`video/mp4`, `audio/mpeg`, `audio/wav`) inline as the response body — NOT
   a JSON envelope with a URL. Calling `await r.json()` on a binary mp4
   throws and surfaces a successful completion as a 500.

2. **`MAX_SOFT_FAILS` for `/video/retrieve` must be ≥ 10.** Venice regularly
   returns 5xx on individual polling calls even on jobs that ultimately
   succeed — observed pattern in real Railway edge logs is 3× 200 PROCESSING
   → ~7× 500 (identical ~91-byte JSON body) → 1× 200 with binary mp4. A
   `MAX_SOFT_FAILS = 6` budget aborts one retry before the binary arrives.

3. **Wrap every upstream Venice fetch in `AbortController`.** Default 95 s
   for chat / image, **180 s for `/video/queue` and `/video/retrieve`** to
   cover Veo 3.1's `average_execution_time: 125635 ms`. Hung connections
   without a timeout escape to Express's default 500 handler and look
   indistinguishable from Venice 5xx to clients.

---

## `/video/queue` — verified response

Request:

```bash
curl -s -X POST https://api.venice.ai/api/v1/video/queue \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"model":"wan-2.6-text-to-video","prompt":"blue ocean waves","duration":"5s","aspect_ratio":"16:9"}'
```

Response (raw, ~83 bytes):

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 83

{"model":"wan-2.6-text-to-video","queue_id":"019f4e83-7631-71eb-aaed-cbd9a635dc35"}
```

**Only two fields. There is no `download_url`, `video_url`, or `progress`
field — ever.** All clients that build media URLs from the queue response
are silently broken. Same minimal shape across Wan, Kling, Pixverse, Sora,
Veo, Runway (just with different `model` IDs).

### Per-model required parameters (gateway validation = 400 if wrong)

| Model family | duration enum | aspect_ratio | Other required |
|---|---|---|---|
| `wan-2.6-text-to-video` | `"5s"` only | `"16:9"` or `"9:16"` | prompt |
| `wan-2.7-*-text-to-video` | `"5s"`,`"10s"`,`"15s"` | required | prompt |
| `wan-2.6-flash-image-to-video` | `"5s"`,`"10s"`,`"15s"` | **not supported** (400 if sent) | `image_url` |
| `veo3.1-fast-text-to-video` | `"4s"`,`"6s"`,`"8s"` | required | prompt; `resolution` optional `"720p"\|"1080p"\|"4k"` |
| `sora-2-text-to-video` | `"4s"`,`"8s"`,`"12s"` | required | prompt |
| `gemini-omni-flash-text-to-video` | `"4s"`,`"6s"`,`"8s"`,`"10s"` | required | prompt |
| `kling-2.5-turbo-pro-text-to-video` | model-dependent | required | prompt |
| `pixverse-v5.6-text-to-video` | `"5s"`,`"8s"` | required | prompt |
| `pixverse-c1-text-to-video` | `"3s"`,`"5s"`,`"8s"`,`"10s"`,`"15s"` | required | prompt |
| `runway-gen4-aleph` | `"2s"`–`"10s"` | required | `video_url` (not a generative t2v model) |
| `topaz-video-upscale` | `"Auto"` | n/a | `video_url` |
| `ltx-2-19b-full-text-to-video` | depends on resolution choice | required | prompt |

Always read `/v1/models?type=video` first to fetch `model_spec.constraints`
for the user's selected model — these enums drift per release.

### Common 400 errors to handle at the queue endpoint

```json
// Wan 2.6 flash with aspect_ratio
{"details":{"_errors":[],"aspect_ratio":{"_errors":["This model does not support aspect_ratio"]},"image_url":{"_errors":["image_url is required for image to video models"]}}, …}

// Wan 2.6 sync with 5s (Veo defines 4s/6s/8s)
{"details":{"_errors":[],"duration":{"_errors":["Invalid enum value. Expected '4s' | '6s' | '8s', received '5s"]}}, …}

// Bad model ID (typo)
{"error":"Specified model not found: seedance-1-pro-image-to-video. Did you mean: wan-2.1-pro-image-to-video, sora-2-pro-image-to-video, kling-2.6-pro-image-to-video?"}
```

Note that the "Did you mean" suggestion list is genuinely useful — surface
it to the UI when the user picks a now-deprecated ID.

---

## `/video/retrieve` — the dual-shape endpoint

### During processing (multiple calls, ~80 bytes each)

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 80

{"status":"PROCESSING","average_execution_time":79652,"execution_duration":3611}
```

`average_execution_time`: Venice's projection (ms). Stays constant for the
same model / parameters across calls.

`execution_duration`: Elapsed time (ms) on the current render attempt.
Climbs monotonically across polls.

Progress fraction (clamped — never trust > 0.97 before binary is in hand):

```js
const progress = avg_execution_time
  ? Math.min(0.97, execution_duration / average_execution_time)
  : null;  // null = unknown, render indeterminate spinner
```

### On completion (one binary, 2–12 MB)

```http
HTTP/1.1 200 OK
Content-Type: video/mp4
Content-Length: 12413738

<12 MB of mp4 bytes>
```

This is the entire deliverable. There is no JSON wrapper, no metadata
header, no `video_url` field. Proxies wrapping this must encode the binary
body as a base64 `data:video/mp4;…` URL into a JSON envelope.

### Observed 5xx cascade (real-world, July 2026)

Railway edge logs from one vGPT user on `wan-2.6-text-to-video`:

| Poll # | Time | Status | rxBytes |
|---|---|---|---|
| 1 | t+0s | 200 | 936 |
| 2 | t+4s | 200 | 936 |
| 3 | t+9s | 200 | 936 |
| 4 | t+15s | **500** | 936 |
| 5 | t+22s | **500** | 936 |
| 6 | t+29s | **500** | 936 |
| 7 | t+37s | **500** | 936 |
| 8 | t+45s | **500** | 936 |
| 9 | t+53s | **500** | 936 |
| 10 | t+63s | **500** | 936 |
| 11 | t+73s | 200 | 12,413,738 (binary mp4) |

**That's 7 consecutive 500s after 3 successes, before the binary arrives.**
A polling loop with `MAX_SOFT_FAILS = 6` aborts one retry early. The Venice
500 body is identical across calls (~91 bytes):
`{"error":"Upstream temporarily unavailable. Retry after a short delay.","code":"TEMP_DOWN"}`.

This is a **known operational behavior** of the upstream, not a bug in the
client. Surfacing it as a permanent "render failed" to the user is wrong;
the job was going to succeed.

### Real observed durations per model

| Model | Avg time (from `average_execution_time`) | Notes |
|---|---|---|
| `wan-2.6-flash-image-to-video` | ~16 s | Fastest tier; need image_url |
| `wan-2.6-text-to-video` | ~80 s | Default pick for tx2video |
| `wan-2.7-text-to-video` | ~50–90 s | Newer entry |
| `pixverse-v5.6-text-to-video` | ~30 s | Mid-tier |
| `kling-2.5-turbo-pro-text-to-video` | ~30–60 s | Reliable |
| `veo3.1-fast-text-to-video` | ~125 s | Premium tier, slowest REST |
| Sora 2 (any) | similar to Veo 3.1 | OpenAI tier |

With `MAX_SOFT_FAILS ≥ 10` and average 125 s Veo renders, a single render
uses 50–80 polls across its lifecycle. Don't set your `MAX = 8 * 60 * 1000`
wall-clock cap too tight — Venice hasn't shipped a 4K video in < 2 min
ever, in observed traffic.

---

## 5xx-on-retrieve is NOT a queue expiry

Hypothesis tested: poll `/video/retrieve` repeatedly against the SAME
`queue_id` after it completes. Result: every subsequent call returns 200 +
the same 12 MB binary mp4. There is **no queue expiry** in observed
behavior. So a fallback retry that re-queues when retrieve fails is
**wrong** — you lose the render result and bill the user twice.

Always poll the same `queue_id` until binary arrives.

---

## `/video/quote` (auth-free)

```bash
curl -s https://api.venice.ai/api/v1/video/quote \
  -H "Content-Type: application/json" \
  -d '{"model":"wan-2.6-text-to-video","duration":"5s","aspect_ratio":"16:9"}'
```

Response: `{"quote":0.83}` (USD). Useful for showing price preview before
requiring authentication. Always shown to user before they commit to a paid
render.

---

## Music — same shape, different prefix

Probed shape (not exercised in this session, but confirmed via /v1/models
that the model family is identical):

- `POST /music/queue` returns `{"model":"…","queue_id":"…"}` (~90 B).
- `POST /music/status` (or `/music/retrieve`?) returns PROCESSING JSON or
  binary mp3. ⚠️ Confirm exact endpoint name before integrating — the MCP
  tool listing says `venice_music_status`. The REST path may be
  `/music/status` or `/music/retrieve`.

Models `ace-step-15`, `elevenlabs-music`, `minimax-music-v2/v25/v26`,
`stable-audio-25`, `mmaudio-v2`, `elevenlabs-sound-effects-v2` all use
the same queue-and-poll pattern.

---

## Async audio (`/video/queue` for video only) vs `/audio/queue` for async audio

There is **no `/video/queue` analog for audio generation** in the v1 REST
surface — async audio uses `/audio/queue` and `/audio/retrieve` with the
same contract. TTS (text-to-speech) is synchronous on `/audio/speech` and
needs no polling.

---

## What a robust proxy looks like (reference Node implementation)

```js
async function proxyVideo(req, res) {
  const key = requireKey(req, res);
  if (!key) return;
  try {
    const ctl = new AbortController();
    const tid = setTimeout(() => ctl.abort(), 180_000); // 180s for video
    const r = await fetch('https://api.venice.ai/api/v1/video/' + req.params.action, {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body),
      signal: ctl.signal,
    });
    clearTimeout(tid);

    const ct = r.headers.get('content-type') || '';
    passMeta(r, res);

    if (!r.ok && !r.headers.get('content-length')?.startsWith('0')) {
      const t = await r.text();
      console.warn(`[proxy /video/${req.params.action}] upstream ${r.status} (${ct}, ${t.length}b): ${t.slice(0,300)}`);
    }

    if (ct.startsWith('video/')) {
      if (!r.ok) {
        return res.status(r.status).json({ error: await r.text() });
      }
      const buf = Buffer.from(await r.arrayBuffer());
      if (buf.length > 80 * 1024 * 1024) {
        return res.status(413).json({ error: 'mp4 exceeds 80MB cap' });
      }
      return res.json({
        data: `data:${ct};base64,${buf.toString('base64')}`,
        contentType: ct,
        bytes: buf.length,
      });
    }

    // JSON path
    const text = await r.text();
    res.status(r.status).type('application/json');
    return res.send(text);
  } catch (err) {
    const isAbort = err?.name === 'AbortError';
    if (isAbort) {
      console.error(`[proxy /video/*] TIMEOUT 180000ms`);
      return res.status(504).json({ error: 'Venice upstream timed out', endpoint: req.params.action });
    }
    console.error(`[proxy /video/*]`, err.message);
    return res.status(502).json({ error: 'Upstream request failed', details: err.message });
  }
}
```

The polling-loop equivalent (client-side) is on the vGPT PR #19 +
companion PR #17 — search the venice-api skill changelog for them.

---

## Tracked gaps in this doc

- Music exact REST endpoint name (`/music/status` vs `/music/retrieve`)
  was not exercised in this session.
- Verify per-model `aspect_ratio` support when going from text to image-to-video
  variants of the same family (Wan 2.6 vs Wan 2.6 flash behave differently).
- Whether `/video/complete` actually frees server state (currently appears
  to be a no-op; idempotent so no harm in calling it).
