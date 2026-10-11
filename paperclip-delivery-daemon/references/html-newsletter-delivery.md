# Sending HTML newsletters / reports through the Paperclip delivery daemon

**Class of work**: any AIPharmaXchange deliverable that has a fully-rendered HTML body
(newsletter, EOD report with HTML, weekly infographic) and needs to land in
Gmail as a real, properly-rendered email — not as a file attachment.

**User preference (corrected 2026-06-14)**: newsletters and reports must be
delivered as inline HTML in the email body, not as a `.md` or `.html`
file attachment. The user said: *"I can't open the files in the email. Can
it be a proper newsletter as part of the email."* This is now a hard rule —
default to inline HTML for any content that has a rendered body.

## The pattern (works today)

The delivery daemon auto-detects an HTML email body from any work-product
or attachment whose filename contains `body.html` (or `email.html`). When
found, it is pulled out of the attachment list and used as the email's
`multipart/alternative` HTML part via `msg.add_alternative(html,
subtype='html')`. A matching `*body*.md` becomes the plain-text
alternative.

## The two paperclip-wrap gotchas you will hit

### 1. The `originalFilename` trap (silent failure)

Paperclip's API stores the upload filename in `originalFilename`, NOT in
`name` or `filename`. The daemon's attachment-name resolution in
`collect_attachments()` MUST try `originalFilename` first, otherwise
the `body.html` detection silently fails and the file ships as a
regular attachment.

**The fix lives in `delivery-daemon.py` lines ~140 and ~160**:

```python
# Work products
name = (
    wp.get("originalFilename")
    or wp.get("title")
    or wp.get("externalId", "").rsplit("/", 1)[-1]
    or wp.get("name")
    or wp.get("key")
    or f"work-product-{wp_id}"
)

# Attachments
name = (
    att.get("originalFilename")
    or att.get("name")
    or att.get("filename")
    or f"attachment-{att_id}"
)
```

If you skip `originalFilename`, the daemon silently attaches the
`body.html` file instead of rendering it inline. The email goes out,
the user sees a file, and they think the pipeline is broken. They
have to tell you. **Always verify after any daemon change.**

### 2. The daemon must be reloaded to pick up code changes

Just restarting the Python process isn't enough — launchd respawns it
with the OLD code. The daemon reads `delivery-daemon.py` at startup.
After editing the daemon, reload via launchd:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.aipharmaxchange.paperclip-delivery.plist
sleep 2
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.aipharmaxchange.paperclip-delivery.plist
sleep 3
launchctl list | grep paperclip-delivery   # confirm new PID
```

`launchctl kickstart -k` works too but the bootout+bootstrap form is
cleaner for picking up file changes. (Note: `kickstart -k` is fine for
*crash* restarts, but does not always pick up new code; bootout
guarantees it.)

## Wrapper-side pattern

The wrapper writes two files to `~/.hermes/scripts/` or
`/tmp/aipharmaxchange_assets/`:

```
newsletter_body_2026-06-14.html   # the rendered HTML — daemon detects this
newsletter_body_2026-06-14.md     # optional plain-text fallback
```

Then uploads them as **both** work-products and multipart attachments.
The daemon fetches from the attachment endpoint, so the work-product
URLs being `file://` (which the daemon can't fetch) is fine.

Naming MUST include `body.html` literally. The daemon's detection
checks `"body.html" in nl.lower()`. Other HTML filenames like
`report.html` or `newsletter.html` will be sent as attachments.

## Diagnostic traps

### State.json shows "delivered" but log shows no SMTP send

The daemon can mark an issue delivered in `delivery-state.json` even
when the SMTP log line is missing — usually because of Python stdout
buffering when not connected to a TTY. Always verify by checking the
**recipient inbox** (or the message-id returned by a direct `python3
smtplib` send) before declaring success.

The "right" check is the recipient. The state file just says the
daemon reached the end of the function; the log says the daemon wrote
a log line. Neither guarantees Gmail actually accepted the message.

### Daemon appears "hung" but is alive

`ps -p <pid>` shows the daemon is running, but no new log entries in
minutes. The most common cause: the daemon is in the middle of a long
sleep inside its 15-second poll loop, AND its stdout buffer hasn't
flushed. The daemon writes to `delivery.err.log` which is 11MB+ on
busy days. Use `wc -l` and `tail -c` to see the actual file state,
not just `tail -50`.

## What you should produce for any new HTML-content deliverable

1. A script that writes BOTH `*body*.html` (the rendered HTML) and
   `*body*.md` (the source markdown) to `/tmp/aipharmaxchange_assets/`
   or `~/.hermes/scripts/`.
2. A wrapper that creates a Paperclip issue, uploads both files as
   work-products AND multipart attachments, marks the issue done.
3. Daemon auto-detects `body.html`, renders it inline, ships the
   plain-text alternative from the `.md` file.
4. Cover image (PNG) uploads as a regular attachment — daemon sends
   it as a normal email attachment (Gmail inlines it for display).

## Files implementing this

- `~/.hermes/scripts/paperclip_wrap_newsletter.py` — the canonical
  example. Writes HTML + MD, uploads both, the daemon sends inline.
- `~/.paperclip/delivery-daemon.py` — has the originalFilename fix
  and the `add_alternative` logic.
- `~/.paperclip/workspaces/aipharmaxchange/weekly_newsletter_generator.py`
  — the generator that produces the HTML body.
