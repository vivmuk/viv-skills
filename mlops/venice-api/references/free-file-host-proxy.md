---
title: Free file host upload proxy pattern
description: When proxying file uploads to a free host (litterbox.catbox.moe and similar) from a backend, hit the canonical POST URL directly — most paths 301-redirect, and FormData POST bodies get dropped during cross-host redirects, producing 403s.
applies_to: node backend that accepts user uploads (images / videos / audios) and forwards them to a free third-party host for temporary public URL storage
related_skills: venice-api
---

# Free file host upload proxy pattern

When you need a public HTTPS URL for a user-uploaded file (image, video, audio) and don't want to host yourself, free file hosts offer a quick path: the user pays with TTL (typically 1 hour to 72 hours) and rate limits in exchange for hosted URL. Common picks:

| Host | TTL | Max size | Endpoint |
|---|---|---|---|
| `litterbox.catbox.moe` | 1h / 12h / 24h / 72h | 1 GB | `https://litterbox.catbox.moe/resources/internals/api.php` |
| `catbox.moe` | permanent | 200 MB | `https://catbox.moe/user/api.php` |
| `motherless` (image only) | permanent | image size limits | not recommended for general use |
| `0x0.st` | 30 days | 512 MB | `https://0x0.st` |

`litterbox.catbox.moe` is the canonical pick for Venice video pipelines because of the 72-hour TTL + 1 GB cap (matches Venice's `/video/queue` payload limits). The user is the catbox project — give credit in your UI's "uploaded via litterbox.catbox.moe" footer.

## The canonical URL gotcha — `/resources` is a 301 redirect, not the API

When integrating with `litterbox.catbox.moe`, the symmetric URLs that *look* like the API aren't:

```
POST /resources                     → 301 Location: /resources/internals/api.php
POST /resources/internals/api.php   → 200 with the hosted URL
```

Most HTTP clients follow `/resources → /resources/internals/api.php`. **But per HTTP spec, multipart FormData POST bodies are frequently dropped during cross-host redirects**. The upstream receives an empty request and answers **403 Forbidden**. The user-visible error in your app appears as:

```
Upload failed: litterbox 403: ×
```

This burned me in the Venice-Video `feature/v2v-tab` work in July 2026. The fix was a one-line change in the proxy:

```diff
- const upstream = await fetch('https://litterbox.catbox.moe/resources', { method: 'POST', body: formData });
+ const upstream = await fetch('https://litterbox.catbox.moe/resources/internals/api.php', { method: 'POST', body: formData });
```

After the fix, the upload route returned HTTP 200 with a real hosted URL (`https://litter.catbox.moe/<id>.mp4`) immediately.

**Lesson:** when integrating with any service whose documentation points to a "short" URL like `/api`, `/upload`, or `/resources`, always probe directly with `curl` first to verify it accepts POST with a body, *before* assuming a 200 / 301 is "fine, fetch will follow."

## Verification recipe (run before integration)

```bash
# Test 1: confirm the form-data fields and canonical URL
curl -sS -X POST \
  -F "reqtype=fileupload" -F "time=72h" -F "fileToUpload=@/tmp/test.bin" \
  "https://litterbox.catbox.moe/resources/internals/api.php" \
  -w "  HTTP %{http_code}\n"

# Test 2: confirm /resources is a redirect (not the API)
curl -sS -X POST \
  -F "reqtype=fileupload" -F "time=72h" -F "fileToUpload=@/tmp/test.bin" \
  "https://litterbox.catbox.moe/resources" \
  -w "  HTTP %{http_code}\n"
```

Test 1 should return 200 + an upload URL on its first byte line. Test 2 will return 301 (with `Location:` header). If you wire Test 2 URL by accident, you get 403s in production with the actual user in the loop.

## Express / multer proxy sketch (the working pattern)

```js
const express = require('express');
const multer  = require('multer');
const sharp   = require('sharp');

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 700 * 1024 * 1024 },   // 700 MB cap (under litterbox's 1 GB)
});

const LITTERBOX = 'https://litterbox.catbox.moe/resources/internals/api.php';

app.post('/api/upload', (req, res) => {
  upload.single('file')(req, res, async (err) => {
    if (err) {
      if (err.code === 'LIMIT_FILE_SIZE')
        return res.status(413).json({ error: 'file too large; max 700 MB' });
      return res.status(415).json({ error: err.message });
    }
    if (!req.file) return res.status(400).json({ error: 'no file field' });

    try {
      // Strip EXIF from image uploads server-side before forwarding.
      let payload = req.file.buffer;
      const isImage = (req.file.mimetype || '').startsWith('image/');
      if (isImage) {
        try { payload = await sharp(req.file.buffer).rotate().withMetadata({}).toBuffer(); }
        catch (e) { /* keep original on sharp failure */ }
      }

      const formData = new FormData();
      formData.append('reqtype', 'fileupload');
      formData.append('time', '72h');                              // TTL: 1h / 12h / 24h / 72h
      const blob = new Blob([payload], { type: req.file.mimetype });
      formData.append('fileToUpload', blob, req.file.originalname || `upload-${Date.now()}`);

      const upstream = await fetch(LITTERBOX, { method: 'POST', body: formData });
      const text = await upstream.text();
      if (!upstream.ok) {
        console.error('litterbox upstream', upstream.status, text.slice(0, 200));
        return res.status(502).json({ error: `litterbox ${upstream.status}: ${text.slice(0, 200)}` });
      }

      // litterbox returns the hosted URL as the response body — first line is the URL, rest is <br>.
      const url = text.split('\n')[0].trim();
      return res.json({ url, bytes: req.file.size, mime: req.file.mimetype, isImage, ttlHours: 72 });
    } catch (e) {
      console.error('/api/upload failed:', e);
      return res.status(500).json({ error: e.message });
    }
  });
});
```

## CSP implications

If your front-end `<meta http-equiv="Content-Security-Policy">` or response headers restrict `media-src` and `connect-src`, the catbox hosts need to be allowlisted from day one:

```html
<meta http-equiv="Content-Security-Policy" content="
  media-src 'self' https: blob: data: *  https://litterbox.catbox.moe https://files.catbox.moe;
  connect-src 'self' https://api.venice.ai https://api.imgbb.com https://litterbox.catbox.moe;
">
```

Without the catbox entries, the browser will block both the upload POST and the playback `<video src="https://litter.catbox.moe/...">` element. Symptom: silent upload failures, silent video playback failures. Always recheck CSP after integrating any third-party host.

## When NOT to use a free file host

- Long-lived references: 72-hour TTL is too short. Host yourself (e.g., an S3 bucket) and use signed URLs.
- Sensitive content: litterbox/catbox hosts strip or retain user content. Don't pass through PHI or PII.
- High-volume commercial traffic: litterbox has rate limits (unclear, but ~50/hr observed). Switch to Bunny / S3 for production.
- Videos >1 GB: out of scope for litterbox free tier. Self-host or use a streaming CDN.

## Quick reference — the fields the form expects

| Field | Required | Values |
|---|---|---|
| `reqtype` | yes | `fileupload` (the only upload verb free-tier exposes) |
| `time` | no | `1h`, `12h`, `24h`, `72h` (default `1h`) |
| `userhash` | optional | account-bound retention token; not used in free flow |
| `fileToUpload` | yes | the file bytes |

The response body is the hosted URL on its own (single line). Some versions tack trailing `<br>`s; strip newlines and trim if you parse defensively.
