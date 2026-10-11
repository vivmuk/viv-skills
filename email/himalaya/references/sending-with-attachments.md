# Sending Emails with Attachments — Three Approaches

This is the consolidated decision tree for sending emails with file attachments
through himalaya. Pick the right approach based on what you know about the
binary, the config, and the time budget.

## The three approaches

| Approach | Command | Best for | Failure mode |
|----------|---------|----------|--------------|
| **A. MML template** | `cat msg.mml \| himalaya template send` | Plain-text emails, quick sends, when config is known-good | MML attachment handling can be fragile for binary files; static builds may lack sender feature |
| **B. Raw MIME via himalaya** | `python build_mime.py \| himalaya message send` | Multi-attachment emails with mixed types (PDF, DOCX, images), when you want himalaya to log to Sent folder | Same himalaya config requirements as A |
| **C. Python smtplib direct** | `python send.py` | When himalaya is misconfigured or the static build lacks the sender feature; when you need clear send-verdict output | No Sent-folder copy (manual if needed) |

## Decision flow

```
1. Is himalaya's sender backend working?
   │
   ├─ YES  → A or B (see below)
   └─ NO   → C (Python smtplib)
              "feature not available" error
              "535 Bad Credentials" (stale password — verify first)
              old-style config ([accounts.X.smtp] flat block)
```

```
2. A or B?
   │
   ├─ Plain text only, no large binary attachments → A (MML is simpler)
   │
   └─ Mixed/binary attachments, want explicit control → B (raw MIME)
```

## Approach A — MML template

Pipe an MML message via stdin. MML is himalaya's native markup, compiles to
MIME. Headers in plain `Key: Value` form, body in plain text or MML tags for
multipart/attachments.

```bash
cat << 'EOF' | himalaya template send
From: sender@example.com
To: recipient@example.com
Subject: Report Attached

Here is the report.

<#part filename="/path/to/report.pdf"><#/part>
<#part filename="/path/to/chart.png"><#/part>
EOF
```

**Pitfall:** `template send` does NOT accept `--subject`, `--to`, `--from`,
`--attachment` flags. It takes the raw template (headers + body) as
positional input via stdin. `--from` etc. will produce
`unexpected argument '--from' found`.

See `references/message-composition.md` for full MML syntax (multipart,
inline images, etc.).

## Approach B — raw MIME via himalaya

Build a MIME message in Python, pipe it to `himalaya message send`. Use this
when you need explicit control over the MIME structure (mixed types, HTML +
text alternatives, inline images, custom headers) or when MML's binary
attachment handling feels fragile.

```python
# build_mime.py
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

msg = MIMEMultipart()
msg['From'] = 'sender@example.com'
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Report Attached'
msg.attach(MIMEText('See attached.', 'plain'))

for path, mime in [('/tmp/report.pdf', 'pdf'), ('/tmp/chart.png', 'png')]:
    with open(path, 'rb') as f:
        part = MIMEApplication(f.read(), _subtype=mime)
        part.add_header('Content-Disposition', 'attachment', filename=path.split('/')[-1])
        msg.attach(part)

print(msg.as_string())
```

```bash
python3 build_mime.py | himalaya message send
```

**Pitfall:** `message send` ALSO does NOT accept `--from`/`--to`/`--subject`/
`--attachment` flags — it takes raw MIME on stdin. Same error class as A.

**Pitfall:** If himalaya exits 0 but the email never arrives, the SMTP sender
backend is likely misconfigured (old-style config, or static build missing
the feature). Verify with `himalaya envelope list --folder "Sent"` — if the
message is missing from Sent, SMTP never ran.

## Approach C — Python smtplib (fallback)

When himalaya's sender backend is broken, skip himalaya entirely. The
`smtplib` + `email.message.EmailMessage` approach in stdlib needs no
external config — just SMTP creds inline.

**`templates/send-via-python-smtplib.py`** is a copy-paste script. Edit the
constants (user, password, to, subject, body, attachments) and run.

**When to use:**
- `himalaya template send` returns "feature not available, or backend
  configuration for this functionality is not set"
- The user is waiting and you don't have time to debug himalaya config
- The user explicitly provided SMTP creds and wants the email sent now

**Pitfall — Gmail app password rotation:** Google can rotate app passwords
without notice. The `smtplib` script's first action is a `login()` that
returns `535 Bad Credentials` if the password is stale. This is cheap to
detect — do it BEFORE writing attachments. A `535` after a config-writing
dance is a wasted round-trip.

**What you lose vs himalaya:**
- No automatic save-to-Sent (Gmail keeps a Sent copy server-side anyway,
  but himalaya's `folder.aliases` integration won't apply)
- No IMAP folder management from the same tool

**What you gain:**
- A clear "OK: sent" / "REFUSED: {recipient}" verdict
- The Message-ID printed for follow-up verification
- Independence from himalaya's config quirks

## Verification checklist (any approach)

After ANY send, confirm success by checking ONE of:

1. **Python smtplib:** `s.send_message(msg)` returned an empty `{}` dict
   (any key in the dict = refused recipient)
2. **Himalaya:** exit 0 AND `himalaya envelope list --folder "Sent"`
   shows the new message at the top with matching subject
3. **SMTP trace:** `smtplib.SMTP('smtp.gmail.com', 587)` with
   `set_debuglevel(1)` shows `DATA` followed by `250 OK`

If NONE of these confirm success, the email was NOT sent — re-verify
config, re-check password, or fall through to Approach C.

## Related

- `references/configuration.md` — modern v1.2.0 config shape (avoid the
  old flat `[accounts.X.smtp]` form)
- `templates/send-via-python-smtplib.py` — copy-paste fallback script
- SKILL.md "Agent Quick-Send Pattern" — the himalaya-only flow when
  config is known-good
