# Wrapper Pattern: Design Rationale

Why a separate wrapper script for each cron job, instead of putting the
Paperclip issue lifecycle *inside* the existing content script?

## The decoupling argument

The original content scripts (`daily_post_generator.py`, `eod_report.py`,
`weekly_report.py`) were written before the Paperclip delivery pipeline
existed. They each had their own SMTP send logic — himalaya templates,
display-name logic, the wiped-password dance. Rewriting each script to
speak Paperclip's API would mean three substantial refactors, with risk
to the content-generation logic that already works.

A wrapper is an *adapter*. It calls the original script as a black box
(reading its stdout, parsing the last JSON block) and translates the
output into Paperclip's vocabulary. The content script doesn't know
Paperclip exists. If Paperclip's API changes tomorrow, only the wrapper
needs to update.

## Why no-agent cron mode

The original crons ran an LLM agent with `Skills: email/himalaya` and a
long prompt. The LLM was acting as a "smart glue" between the
content-generation script and the SMTP send. This works but has three
problems:

1. **Cost** — every cron tick burns LLM tokens for what is purely
   mechanical work.
2. **Nondeterminism** — the LLM might phrase the email differently each
   day, miss fields, or fail to attach the hero image.
3. **Hidden complexity** — the prompt is the spec, and it lives in
   `hermes cron list` as a giant string, easy to break with an edit.

`--no-agent` mode turns the cron into a deterministic script execution.
The cron becomes "every day at 9am, run this Python file." The
Python file is the spec, it's reviewable, and it costs nothing to run.

## Why multipart upload to `/api/issues/{id}/attachments`

Three upload paths exist on a Paperclip issue:

- **Work products** (`/api/issues/{id}/work-products`) — designed for
  "link to artifacts elsewhere" (preview URLs, PR refs, branches).
  Schema requires `type: document|artifact|preview_url|...`, `provider`,
  `title`, optional `url` and `externalId`. The daemon's
  `collect_attachments` tries `/api/work-products/{id}/content` first —
  404 in the current version — then falls through to `wp.get("url")`.
  But the daemon prepends `PAPERCLIP_BASE` to that URL, so `file://...`
  URLs become `http://127.0.0.1:3100file:///tmp/...` and fail.
- **Attachments** (`/api/companies/{id}/issues/{iid}/attachments`,
  multipart POST) — designed for "here's an actual file." The daemon
  fetches via `/api/attachments/{id}/content`. This works.
- **Documents** (`/api/issues/{iid}/documents/{key}`) — designed for
  inline collaborative content, not bulk file delivery.

Attachments is the right tool for "produce a file and email it."

## Why create with in_progress, then PATCH to done

The Paperclip issue create endpoint accepts `status: "done"` in its
schema, but in practice (2026.609.0) it silently downgrades to
`todo` for some calls. The daemon's filter `["done", "closed"]`
queries issues with status exactly matching, so a `todo` issue is
never picked up.

Creating with `in_progress` and then PATCHing to `done` after
attachments land avoids the silent downgrade and is the only path
the daemon reliably observes.

The cost of the two-step transition is one extra API call per cron
run (a few hundred ms). Worth it for the reliability.

## Why `--deliver local` on the cron

The cron's `--deliver` flag controls where the script's STDOUT goes.
For the wrapper pattern, the stdout is just diagnostic logs ("[1/5]
running ...", "uploaded foo.png 12345 bytes"). We don't want this
spammed to the user via Telegram on every cron tick — that would be
a notification per run, 3x/day. `--deliver local` keeps stdout in the
cron's log file (`~/.hermes/cron/output/<job_id>/...`).

The actual email — with the full summary and attachments — goes
through the daemon, not the cron.

## Why assign to a Paperclip agent

The issue must have an `assigneeAgentId` because the Paperclip
company hierarchy tracks ownership. The agent doesn't need to DO
anything (the wrapper did the work), but the assignment:

1. Makes the issue visible in the agent's issue list for the daily
   heartbeat review
2. Lets CMO/CEO override or follow up via Paperclip's UI
3. Provides a "who is responsible for this content" answer in the
   activity log

For Daily Post and EOD: assign to `ContentDirector` (the PM who
owns the daily content pipeline). For Weekly: assign to `CEO` (it's
the strategic weekly report).

## The trigger chain in one diagram

```
cron tick (9am daily)
    │
    ▼
hermes cron → paperclip_wrap_daily.py
    │
    │ runs: daily_post_generator.py (no LLM, no SMTP)
    ▼
    reads /tmp/daily_content_YYYY-MM-DD.json
    │
    │ POST /api/companies/.../issues  (status=in_progress, assignee=ContentDirector)
    │ PATCH /api/issues/.../          (status=done)
    │ POST /api/companies/.../issues/.../attachments  (multipart, hero.png)
    │ POST /api/issues/.../comments   (markdown summary)
    │
    ▼
[waits 0-15s for next poll]
    │
    ▼
delivery-daemon.py polls /api/companies/.../issues?status=done
    │
    │ finds new issue → fetches /api/attachments/.../content
    │ builds email with all attachments + comment body
    │ smtp.send_message() to vivek@live.de
    │ records issue id in delivery-state.json (idempotent)
    │
    ▼
vivek@live.de receives "Agni Agent Report — Daily Post ..."
    with FROM: AI CEO AIPharmaXchange <vivgatesai@gmail.com>
    and the hero image attached
```

## Cost

Each cron run: ~$0.61 (model cost from daily_post_generator),
plus 4 Paperclip API calls (a few hundred ms total, no monetary
cost). The original cron had the same $0.61 plus an LLM run for
the email-send step; the new pattern saves the LLM cost by removing
the LLM.

## Failure modes

- Wrapper fails to create issue → cron exits non-zero, no email.
  The cron output captures the error. User sees it in the next
  session if they check.
- Issue created but PATCH to done fails → daemon never sees it,
  no email. Visible by checking `delivery-state.json` (no entry
  for today's run).
- Issue created + PATCHed but attachment upload fails → daemon
  sees an issue with no attachments, skips, no email. The cron
  output captures the upload failure.
- Daemon finds the issue but SMTP fails (bad password) → daemon
  logs the error in `delivery.err.log`, doesn't update state, will
  retry on next cycle. After 535: update himalaya config + memory
  + restart daemon.

For each, the recovery is in the cron log (stdout) and the daemon
log (`~/.paperclip/logs/delivery.err.log`). Both are easy to read.
