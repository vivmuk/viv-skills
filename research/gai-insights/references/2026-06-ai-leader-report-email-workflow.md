# 2026-06 GAI Insights batch report + email workflow notes

Session pattern: Vivek asked to emulate Drishti/GAI Insights summaries for six AI links and email the report to himself.

## Durable workflow lessons

- If a site blocks automated extraction but the user pastes the article text, save that pasted text as a source file with metadata noting `fetch_source: user-provided full article text` and continue. Treat it as the full extraction for verification purposes.
- Medium pages may return raw HTML with article text embedded. A lightweight Python `html.parser` pass can extract readable text sufficiently for analysis:
  - keep text from normal HTML data nodes
  - add line breaks around `p`, `h1`, `h2`, `h3`, `li`, `blockquote`
  - skip `script`, `style`, `noscript`
  - save a sibling `.clean.txt` file and use that for report source text.
- For multi-article GAI reports, a good artifact shape is:
  - executive summary card grid
  - one tab per article
  - Essential / Important / Optional badge
  - five rubric sections
  - applications, talking points, caveats
  - collapsible full extracted source text for auditability.
- Verification that worked well:
  - update `manifest.json` with `ok`, `chars`, `title`, and `path` per source
  - parse the final HTML with `html.parser`
  - assert expected count of tabs/article panels/details sections
  - assert every expected title is present
  - print total source characters and report byte size.
- Email verification via SMTP should include:
  - attachment exists and is non-trivially sized before send
  - `From: Netrak <sender>` display name
  - target defaults to `vivek@live.de` when Vivek says “send it to me”
  - print SMTP `refused_recipients`; `{}` means accepted by SMTP.

## Caveats

- Do not claim an automated scrape succeeded when a user-pasted article supplied the source text; say it clearly.
- Do not preserve or print SMTP app passwords or API keys. Only report that the configured local secret file was used.
- For source pages that are vendor-authored, explicitly caveat vendor benchmark/product claims in the analysis.
