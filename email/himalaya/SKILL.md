---
name: himalaya
description: "Himalaya CLI: IMAP/SMTP email from terminal."
version: 1.2.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya Email CLI

Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.

## References

- `references/configuration.md` (config file setup + IMAP/SMTP authentication)
- `references/message-composition.md` (MML syntax for composing emails)
- `references/sending-with-attachments.md` (three approaches — MML template, raw MIME via himalaya, Python smtplib fallback — and when to use each)
- `templates/send-via-python-smtplib.py` (copy-paste fallback when himalaya sender is misconfigured)

## Prerequisites

1. Himalaya CLI installed (`himalaya --version` to verify)
2. A configuration file at `~/.config/himalaya/config.toml`
3. IMAP/SMTP credentials configured (password stored securely)

### Installation

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## Configuration Setup

Run the interactive wizard to set up an account:

```bash
himalaya account configure
```

Or create `~/.config/himalaya/config.toml` manually:

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # or use keyring

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"

# Folder aliases (himalaya v1.2.0+ syntax). Required whenever the
# server's folder names don't match himalaya's canonical names
# (inbox/sent/drafts/trash). Gmail is the common case — see
# `references/configuration.md` for the `[Gmail]/Sent Mail` mapping.
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

> **Heads up on the alias syntax.** Pre-v1.2.0 docs used a
> `[accounts.NAME.folder.alias]` sub-section (singular `alias`).
> v1.2.0 silently ignores that form — TOML parses fine, but the
> alias resolver never reads it, so every lookup falls through to
> the canonical name. On Gmail this means save-to-Sent fails *after*
> SMTP delivery succeeds, and `himalaya message send` exits non-zero.
> Any caller (agent, script, user) that retries on that exit code
> will re-run the entire send — including SMTP — producing duplicate
> emails to recipients. Always use `folder.aliases.X` (plural, dotted
> keys, directly under `[accounts.NAME]`).

## Hermes Integration Notes

- **Reading, listing, searching, moving, deleting** all work directly through the terminal tool
- **Composing/replying/forwarding** — piped input (`cat << EOF | himalaya template send`) is recommended for reliability. Interactive `$EDITOR` mode works with `pty=true` + background + process tool, but requires knowing the editor and its commands
- Use `--output json` for structured output that's easier to parse programmatically
- The `himalaya account configure` wizard requires interactive input — use PTY mode: `terminal(command="himalaya account configure", pty=true)`

## Common Operations

### List Folders

```bash
himalaya folder list
```

### List Emails

List emails in INBOX (default):

```bash
himalaya envelope list
```

List emails in a specific folder:

```bash
himalaya envelope list --folder "Sent"
```

List with pagination:

```bash
himalaya envelope list --page 1 --page-size 20
```

### Search Emails

```bash
himalaya envelope list from john@example.com subject meeting
```

### Read an Email

Read email by ID (shows plain text):

```bash
himalaya message read 42
```

Export raw MIME:

```bash
himalaya message export 42 --full
```

### Reply to an Email

To reply non-interactively from Hermes, read the original message, compose a reply, and pipe it:

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

Or build the reply manually:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

Reply-all (interactive — needs $EDITOR, use template approach above instead):

```bash
himalaya message reply 42 --all
```

### Forward an Email

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### Write a New Email

**Non-interactive (use this from Hermes)** — pipe the message via stdin:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

Or with headers flag:

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

Note: `himalaya message write` without piped input opens `$EDITOR`. This works with `pty=true` + background mode, but piping is simpler and more reliable.

### Move/Copy Emails

Move to folder:

```bash
himalaya message move 42 "Archive"
```

Copy to folder:

```bash
himalaya message copy 42 "Important"
```

### Delete an Email

```bash
himalaya message delete 42
```

### Manage Flags

Add flag:

```bash
himalaya flag add 42 --flag seen
```

Remove flag:

```bash
himalaya flag remove 42 --flag seen
```

## Multiple Accounts

List accounts:

```bash
himalaya account list
```

Use a specific account:

```bash
himalaya --account work envelope list
```

## Attachments

Save attachments from a message:

```bash
himalaya attachment download 42
```

Save to specific directory:

```bash
himalaya attachment download 42 --dir ~/Downloads
```

## Output Formats

Most commands support `--output` for structured output:

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## Debugging

Enable debug logging:

```bash
RUST_LOG=debug himalaya envelope list
```

Full trace with backtrace:

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## Sending Emails with Attachments

### Approach A: MML Template (simple text-only emails)

Use `himalaya template send` with the full template (headers + body) as positional input:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Report Attached

Here is the report.
EOF
```

> **⚠️ `template send` does NOT accept `--subject`, `--to`, `--from` flags.** It takes the raw template (headers + body) as positional arguments piped via stdin. If you pass `--subject` you'll get `unexpected argument '--subject' found`. Use the piped-template syntax above, or switch to Approach B.

### Approach B: Raw MIME via Python (reliable for attachments)

When MML template send has issues with binary attachments or encoding, build a proper MIME message in Python and pipe to `himalaya message send`:

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

msg = MIMEMultipart()
msg['From'] = 'you@example.com'
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Report Attached'

msg.attach(MIMEText('Please find the report attached.', 'plain'))

with open('/path/to/report.pdf', 'rb') as f:
    pdf_part = MIMEApplication(f.read(), _subtype='pdf')
    pdf_part.add_header('Content-Disposition', 'attachment',
                        filename='Report.pdf')
    msg.attach(pdf_part)

raw = msg.as_string()
with open('/tmp/email_mime.txt', 'w') as f:
    f.write(raw)
```

Then send:

```bash
cat /tmp/email_mime.txt | himalaya message send
```

**Why two approaches?** `template send` compiles MML to MIME, but binary attachment handling can be fragile. `message send` accepts raw MIME directly — if you build it correctly in Python, it's guaranteed to arrive intact. For the full agent quick-send workflow (config → build MIME → send → wipe), see the **Agent Quick-Send Pattern** section below.

## Agent Quick-Send Pattern

When an agent needs to send an email programmatically (especially when delivering files that can't be sent via the messaging platform), use this proven workflow:

1. **Write config with `backend.auth.raw`** (temporary plaintext password for the session)
2. **Build MIME in Python** (handles HTML, attachments, encoding correctly)
3. **Pipe to `himalaya message send`** (not `template send` — more reliable)
4. **Wipe credentials from config** immediately after sending

```bash
# Step 1: Write config
cat > ~/.config/himalaya/config.toml << 'CONF'
[accounts.default]
email = "you@gmail.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.gmail.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@gmail.com"
backend.auth.type = "password"
backend.auth.raw = "xxxx xxxx xxxx xxxx"

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.gmail.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@gmail.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.raw = "xxxx xxxx xxxx xxxx"

# Gmail requires these aliases
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "[Gmail]/Sent Mail"
folder.aliases.drafts = "[Gmail]/Drafts"
folder.aliases.trash = "[Gmail]/Trash"

# Workaround: if folder aliases fail, disable save-copy
# message.send.save-copy = false
CONF

# Step 2+3: Build MIME in Python and pipe to himalaya message send
python3 -c "
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

msg = MIMEMultipart()
msg['From'] = 'you@gmail.com'
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'File Delivery'

msg.attach(MIMEText('<h1>Report</h1><p>See attached.</p>', 'html'))

with open('/path/to/file.pdf', 'rb') as f:
    part = MIMEApplication(f.read(), _subtype='pdf')
    part.add_header('Content-Disposition', 'attachment', filename='Report.pdf')
    msg.attach(part)

print(msg.as_string())
" | himalaya message send

# Step 4: Wipe credentials
cat > ~/.config/himalaya/config.toml << 'WIPE'
# Credentials removed after use. Re-configure before next send.
WIPE
```

> **Why not `himalaya template send`?** `template send` compiles MML (its own markup language) to MIME. It doesn't accept `--subject`/`--to` flags, and binary attachment handling via MML `<#part>` tags is fragile. `message send` accepts raw MIME directly — build it in Python and pipe it in, guaranteed correct.

> **Still failing? Skip himalaya entirely and use `smtplib` directly.** See the **Fallback: Python smtplib** section under Troubleshooting — `templates/send-via-python-smtplib.py` works without any himalaya config.

## Troubleshooting

### "Folder doesn't exist" error on send

When `himalaya message send` fails with `cannot add IMAP message / Folder doesn't exist`, it means himalaya is trying to save a copy to the Sent folder but the IMAP folder name doesn't match. Two fixes:

1. **Add folder aliases** (preferred — see Configuration section)
2. **Disable save-copy** as a quick workaround:
   ```toml
   message.send.save-copy = false
   ```

### "unexpected NO response" on send with Gmail

Gmail's Sent folder is `[Gmail]/Sent Mail`, not `Sent`. Without the correct `folder.aliases.sent` mapping, the IMAP save-copy step fails *after* SMTP delivery succeeds — the email is sent but himalaya reports an error. This can cause duplicate sends if the caller retries. Always include the Gmail folder aliases block.

### "feature not available, or backend configuration for this functionality is not set"

The SMTP sender backend isn't wired up. Two common causes:

1. **Old-style config.** A flat `[accounts.NAME.smtp]` / `[accounts.NAME.imap]` block (the pre-v1.0 shape) is silently ignored for sending. v1.2.0 requires the modern shape with `backend.type = "imap"` for reading and `message.send.backend.type = "smtp"` for sending. See the Quick-Send Pattern config and `references/configuration.md` for the modern shape.
2. **Static build without sender feature.** Some prebuilt binaries (e.g., the Nix flake `nix-build-himalaya-static-aarch64-apple-darwin`) ship without the SMTP sender feature compiled in, even when `himalaya --version` lists `+smtp`. Workaround: skip himalaya for sending and use Python `smtplib` directly — see `templates/send-via-python-smtplib.py`.

### SMTP `535 Bad Credentials` (Gmail app password)

Gmail app passwords are 16 chars, scoped to a single app, and **Google can rotate them without notice** (e.g., after a security event or a long idle period). If `s.login()` returns `535 5.7.8 Username and Password not accepted`, the password is stale. Verify before promising the user a send will work — a `535` after a config-writing dance is a wasted round-trip. The fix is a new app password from https://myaccount.google.com/apppasswords.

### "Did it actually send?" — verify before reporting success

The single most common follow-up after a "sent the email" reply is "did you send the email?" — usually because a previous attempt was claimed as sent but never reached SMTP. **Never report an email as sent unless you observed one of:**

- `s.send_message(msg)` returned an empty `{}` dict from Python `smtplib` (any recipient in the returned dict was refused)
- `himalaya message send` exited 0 *and* the message-id appears in the Sent folder (`himalaya envelope list --folder "Sent"`)
- A `250 OK` response after `DATA` in a `SMTP.debug` trace

Piping MIME into himalaya, exiting cleanly, and getting no stderr is **not** sufficient — himalaya can fail after SMTP delivery succeeds (see "unexpected NO response" above) and report non-zero, or succeed in build but never reach SMTP if the sender backend isn't configured (see "feature not available" above). When in doubt, also send via `smtplib` and report both results, or verify with `himalaya envelope list --folder "Sent"` immediately after.

## Fallback: Python smtplib (when himalaya is misconfigured)

If himalaya's sender backend is misconfigured (old-style config, static build missing the feature, etc.), Python `smtplib` works directly with no config file wrestling. See `templates/send-via-python-smtplib.py` for a copy-paste script that:

- Reads Gmail SMTP creds inline (not from a config file)
- Builds a proper MIME message with attachments
- Sends to To + Cc recipients
- Returns a clear "OK: sent" or "REFUSED: {recipient}" verdict
- Prints the Message-ID for follow-up verification

Use this when:
- The himalaya send returns "feature not available"
- You need to send immediately and don't have time to debug himalaya config
- The user already provided SMTP creds and just wants the email sent

## Tips

- Use `himalaya --help` or `himalaya <command> --help` for detailed usage.
- Message IDs are relative to the current folder; re-list after folder changes.
- For composing rich emails with attachments, use MML syntax (see `references/message-composition.md`) or the raw MIME approach above for binary files.
- Store passwords securely using `pass`, system keyring, or a command that outputs the password.
- **Always clean credentials from config after use** — don't leave `backend.auth.raw` in the config file.
