---
name: paperclip-delivery-daemon
description: "Wire Paperclip's content generation pipeline to auto-send deliverables by email. Two patterns: (1) the daemon — long-running launchd service that polls for done/closed issues and emails attachments; (2) the wrapper pattern — how to route existing cron scripts (daily post, EOD report, weekly report) through Paperclip so the daemon delivers them. Use when the user says 'set up Paperclip to email at end of generation', 'auto-send the report', 'send the daily post through Paperclip', or wants deliverables to go out without a manual step."
tags: []
related_skills: [send-gmail-attachment]
---

# Paperclip → Gmail Auto-Delivery Pipeline

## When to use
- User wants Paperclip-generated content auto-emailed when generation finishes
- "At the end of the generation, the email gets sent" type request
- User wants an existing cron job (daily post, EOD report, weekly, anything that builds a file) to flow through Paperclip so the deliverable is auto-emailed from the right account
- Stand up the same pattern for a new company (copy the daemon + config)

## The two patterns

### Pattern A: Daemon (long-running, supervised by launchd)
A Python daemon polls Paperclip every 15s, detects issues that
transition to status=done/cancelled, collects their work products +
attachments, and emails them. This is the *delivery* side.

### Pattern B: Wrapper (one-shot, called by cron)
A wrapper script that the cron invokes, which:
1. Runs the existing content-generation script (unchanged)
2. Creates a Paperclip issue assigned to the right agent
3. Uploads the generated files as Paperclip attachments
4. Posts a markdown summary as an issue comment
5. Transitions the issue to status=done
6. Exits — the daemon (Pattern A) picks it up and emails

Both patterns are needed for a complete pipeline. The wrapper creates
*what* gets delivered; the daemon handles *how* it gets delivered. They
are deliberately decoupled.

## Architecture (the shape)

1. **`~/.paperclip/delivery-daemon.py`** — long-running Python daemon
   - Polls Paperclip `/api/companies/{id}/issues?status=done|cancelled` every 15s
   - For each company in `delivery-config.json`, checks for new done issues
   - For each candidate, fetches work products + attachments
   - Sends email via Gmail SMTP (FROM: `AI CEO AIPharmaXchange <vivgatesai@gmail.com>`)
   - Records the issue id in `delivery-state.json` so a restart doesn't re-send
   - If no attachments, skips (no email)

2. **`~/.paperclip/adapters/gmail-deliver-adapter.py`** — standalone CLI companion
   - Same SMTP code, but callable directly: `gmail-deliver-adapter.py --subject ... --attachment file.png`
   - Also supports `--issue-id` to pull a Paperclip issue's artifacts
   - Reads password from himalaya config (or `GMAIL_SMTP_PASS` env var)
   - Used by humans and by agents for one-off sends

3. **`~/.paperclip/delivery-config.json`** — per-company routing
   ```json
   {
     "pollIntervalSeconds": 15,
     "deliverStatuses": ["done", "cancelled"],
     "companies": [
       { "id": "...", "name": "...", "to": ["vivek@live.de"], "cc": [] }
     ]
   }
   ```
   Note: `cc` is empty array. The user removed the CC on 2026-06-14.

4. **`~/.paperclip/delivery-state.json`** — idempotency
   - `delivered.{companyId}`: list of issue ids already emailed
   - `lastSeenIssueId.{companyId}`: ISO timestamp of last poll
   - Atomic write via `tmp + os.replace`

5. **`~/Library/LaunchAgents/com.aipharmaxchange.paperclip-delivery.plist`** — supervisor
   - Keeps the daemon alive across reboots, restarts on crash
   - `KeepAlive.Crashed: true`, `RunAtLoad: true`
   - Logs to `~/.paperclip/logs/delivery.{out,err}.log`

## Pattern B: Wrapper (route existing cron scripts through Paperclip)

A wrapper is a Python script that takes an existing content-generation
script and "wraps" it in a Paperclip issue lifecycle. The cron invokes
the wrapper; the wrapper invokes the original script; the wrapper
publishes the result to Paperclip; the daemon delivers it.

**When to build one:** every existing cron job that produces a
deliverable file (image, docx, pdf) that you want to auto-email
through the daemon. Replaces direct himalaya/smtplib sends in the
original script.

**Reference template:** `templates/paperclip_wrap_template.py` — copy
and adapt. Includes all the gotchas (status transition, multipart
upload, file:// URL trap) wired correctly.

**The five steps every wrapper does:**

1. **Run the existing script** (e.g. `daily_post_generator.py`,
   `eod_report.py --no-email`, `weekly_report.py`). Use `--no-email`
   flags where the original script has them, so the original script
   does NOT try to send via himalaya (which has the wiped-password
   problem).
2. **Create a Paperclip issue** via `POST /api/companies/{id}/issues`
   with `assigneeAgentId` set to the right content agent
   (ContentDirector for daily/EOD, CEO for weekly). Status=`in_progress`
   (NOT `done` — Paperclip silently rejects `done` on create in some
   versions and the issue ends up at `todo`).
3. **Upload the generated files** via multipart POST to
   `/api/companies/{id}/issues/{issueId}/attachments`. This is the ONLY
   upload path the daemon knows how to fetch from. The daemon pulls
   attachments via `/api/attachments/{id}/content`.
4. **Post a markdown comment** with the summary, scores, costs. The
   daemon includes the issue's most recent comment in the email body.
5. **PATCH the issue to `done`** via `PATCH /api/issues/{id}` with
   `{"status": "done"}`. This is the trigger for the daemon's next poll
   cycle.

**Wire the cron to the wrapper:**

```bash
hermes cron edit <job_id> \
  --name "... (via Paperclip)" \
  --script "paperclip_wrap_<name>.py" \
  --no-agent \
  --deliver local \
  --workdir /Users/vivgatesai/.paperclip/workspaces/<company>
```

- `--script` is relative to `~/.hermes/scripts/` (not absolute). Copy
  the wrapper there.
- `--no-agent` makes it a script-only cron (no LLM, no skill loading).
- `--deliver local` is intentional: the script's stdout goes to local
  logs, the actual email goes through the daemon.
- `--workdir` is critical so the script finds the workspace files
  (`daily_post_generator.py`, `output/`, etc.).

## Steps to set up Pattern A (daemon) — or replicate for a new instance

1. **Locate the Paperclip install** — `~/.hermes/node/lib/node_modules/paperclipai/` (npm global). Server entry point: `dist/index.js run --instance default` (NOT `bin/paperclip` — that doesn't exist in this version).
2. **Confirm Paperclip is running** — `curl http://127.0.0.1:3100/api/health` returns 200. If not, start it via `terminal(background=true)`.
3. **Find company ids** — `curl http://127.0.0.1:3100/api/companies` returns the JSON list.
4. **Confirm Gmail creds are persistent** in `~/.config/himalaya/config.toml` (the `passwd.cmd = "echo ..."` line). The user switched to "keep the password" on 2026-06-14 — do NOT wipe it.
5. **Write `delivery-config.json`** with the company list and recipients. `cc` must be empty.
6. **Copy `delivery-daemon.py` and `gmail-deliver-adapter.py`** to `~/.paperclip/`. Make them executable.
7. **Smoke test** — `python3 ~/.paperclip/delivery-daemon.py --once` — should log one clean cycle.
8. **Load launchd service**:
   - `launchctl unload ~/Library/LaunchAgents/com.aipharmaxchange.paperclip-delivery.plist` (ignore "unload failed" if first time)
   - `launchctl load -w ~/Library/LaunchAgents/com.aipharmaxchange.paperclip-delivery.plist`
   - Verify: `launchctl list | grep paperclip-delivery` (should show PID + status 0)
   - `tail ~/.paperclip/logs/delivery.err.log` to confirm it's polling
9. **Create a real test issue, mark it done with an attachment, watch the daemon email it.** If no attachment is created, the daemon correctly skips (no email).

**After editing `delivery-daemon.py`** (e.g. to add new file-handling
logic or fix a bug), the daemon must be reloaded for the new code to
take effect. launchd's `kickstart -k` sends SIGTERM but does not
guarantee the new code is loaded. The reliable form:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.aipharmaxchange.paperclip-delivery.plist
sleep 2
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.aipharmaxchange.paperclip-delivery.plist
sleep 3
launchctl list | grep paperclip-delivery   # confirm new PID
ps -p <new_pid> -o lstart=                  # confirm start time is AFTER the file edit
```

If you skip the bootout and just `kickstart -k`, you may find that
the daemon is alive but running the OLD code from the previous boot —
silent failures and inconsistent state.

## Pitfalls

- **`status: "done"` on issue CREATE is silently rejected** (Paperclip
  2026.609.0). The create call returns 200 but the issue ends up at
  status=`todo`. Always create with `status: "in_progress"`, then
  PATCH to `done` after attachments land.
- **`in_progress` issues require an `assigneeAgentId`** — minimum body
  for an in_progress issue is `{title, status, priority, assigneeAgentId}`.
  If you forget the assignee, you get a 400: *"in_progress issues
  require an assignee"*.
- **The daemon always prepends `PAPERCLIP_BASE` to work-product URLs.**
  If a work product's `url` is `file:///tmp/...`, the daemon tries
  `urllib.urlopen("http://127.0.0.1:3100file:///tmp/...")` — broken.
  Work products with `https://` URLs work; `file://` does not. For local
  files, use the attachments endpoint instead (multipart upload), which
  the daemon fetches via `/api/attachments/{id}/content`.
- **Work products at `/api/work-products/{id}/content` return 404** in
  the current Paperclip version. The daemon falls through to the URL
  check. If both fail, the issue is skipped as "no attachments."
- **The Paperclip attachment API stores the upload filename in
  `originalFilename`, not `name` or `filename`.** The daemon's
  attachment-name resolution MUST try `originalFilename` first or any
  filename-based detection (e.g. `*body.html*` for inline HTML
  delivery) silently fails. See
  `references/html-newsletter-delivery.md` for the full pattern.
- **`status: "closed"` is NOT in the issue status enum.** Valid values
  are `backlog | todo | in_progress | in_review | done | blocked | cancelled`.
  The daemon's filter `["done", "closed"]` still works because the
  Paperclip filter just returns whatever you ask for; it's harmless.
- **Don't run multiple daemon instances** — race conditions on
  `delivery-state.json`. Check `ps aux | grep delivery-daemon` before
  starting a second one.
- **The launchd plist path to Python must be the venv python**
  (`/Users/vivgatesai/.hermes/hermes-agent/venv/bin/python3`), not the
  system python. Wrong path = `ModuleNotFoundError` on import.
- **The 535 Bad Credentials trap**: if Google rotates the password,
  the daemon will fail sends silently in the log. Check
  `delivery.err.log` for `REFUSED` or auth errors. When this happens,
  update himalaya config + memory, restart daemon: `launchctl kickstart
  -k gui/$(id -u)/com.aipharmaxchange.paperclip-delivery`.
- **FROM display name for Paperclip work emails must be
  "AI CEO AIPharmaXchange"** (not "Dr. Apeksha Sharma"). The user
  corrected this on 2026-06-14. The change lives in
  `~/.paperclip/delivery-daemon.py` (line ~53, `FROM_NAME`) and the
  default in `gmail-deliver-adapter.py` (line ~53). Don't let himalaya
  config's `display-name = "Dr. Apeksha Sharma, AIPharmaXchange"`
  leak in — the daemon reads the constant, not himalaya.
- **The 30-50 queued runs trap**: when heartbeats pile up, the
  scheduler will spam Paperclip. If a heartbeat from one of the
  content agents is firing on a tight loop, it creates dozens of
  child issues. Watch the Paperclip `/api/companies/{id}/issues`
  count — if it grows unexpectedly, check the scheduler daemon and
  the heartbeat intervals in the agent configs.
- **Re-running a wrapper with the same date** creates duplicate
  issues, not idempotency. If the wrapper is run twice in a day, two
  emails go out. The daemon's state file prevents the second one
  from going out IF the issue ids differ (they always do for new
  runs), so each issue triggers one email. There's no "topic-keyed
  dedup" — if the user wants that, add it to the wrapper before
  creating the issue (e.g. check if a same-titled issue already
  exists for today).
- **Cron runs an LLM by default** — when migrating an existing cron
  to the wrapper pattern, the LLM agent was previously running with
  `Skills: email/himalaya` and a long prompt. After the migration,
  the LLM is gone (`--no-agent`). The old `Skills: email/himalaya`
  line stays in `hermes cron list` output but is ignored. Don't
  read it as the cron still being LLM-driven.
- **`--script` path must be relative to `~/.hermes/scripts/`** — the
  CLI rejects absolute or `~/`-prefixed paths. Place the script in
  that directory and pass just the filename. The actual file can
  also live in the workspace (e.g. `~/.paperclip/workspaces/.../`);
  the one in `~/.hermes/scripts/` is a copy or symlink.
- **HTML newsletter / report content must be inline, not as a file
  attachment.** The user corrected this on 2026-06-14 ("I can't open
  the files in the email"). The daemon auto-detects `*body.html*`
  attachments and uses them via `msg.add_alternative(html,
  subtype='html')`, but ONLY if the attachment-name resolution tries
  `originalFilename` first (Paperclip's actual field). See
  `references/html-newsletter-delivery.md` for the full pattern,
  including the `originalFilename` trap, the launchd
  bootout/bootstrap reload sequence, and the wrapper-side naming
  convention.

## Verification commands

```bash
# Daemon running?
launchctl list | grep paperclip-delivery
ps aux | grep delivery-daemon | grep -v grep

# Last poll cycle?
tail -10 ~/.paperclip/logs/delivery.err.log

# State of delivery tracking
python3 ~/.paperclip/delivery-daemon.py --status

# Manual one-shot poll
python3 ~/.paperclip/delivery-daemon.py --once

# Restart daemon (picks up code changes via bootout/bootstrap)
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.aipharmaxchange.paperclip-delivery.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.aipharmaxchange.paperclip-delivery.plist
```

## See also

- `templates/paperclip_wrap_template.py` — copy-paste wrapper template
  for routing a new cron script through Paperclip. All the gotchas
  baked in. Adapt the COMPANY_ID, ASSIGNEE_AGENT_ID, SCRIPT_NAME,
  and the run_content_script() body.
- `references/wrapper-pattern-rationale.md` — design decisions behind
  the wrapper pattern (why decoupled from daemon, why no-agent cron
  mode, why multipart upload vs work product URL, why create-then-
  patch, full trigger-chain diagram, cost analysis, failure modes).
- `references/html-newsletter-delivery.md` — how to ship rendered
  HTML newsletters/reports through the daemon (inline body via
  `*body.html*` detection, the `originalFilename` field-name trap,
  launchd bootout+bootstrap reload sequence, diagnostic traps when
  state.json shows delivered but the recipient sees nothing).
- `references/upstream-generator-failure.md` — what to do when the daily
  cron never reaches the wrapper (no email arrives). Step-table for
  finding the dying step, the curl-probe recipe for Venice
  `augment/search` 401s (`VENICE_API_KEY` vs `VENICE_INFERENCE_KEY`),
  401-vs-429-vs-5xx triage, no-silent-retry rule, what to / not to
  report when cost is $0 on a harvest-step abort.