#!/usr/bin/env python3
"""Send an email with attachments via Gmail SMTP, no himalaya required.

Use this when:
- Himalaya's sender backend is misconfigured (returns "feature not available")
- Static himalaya build lacks the SMTP sender feature
- You need to send immediately without debugging himalaya config

Edit the constants below, then run: python3 send-via-python-smtplib.py

Verifies the password works BEFORE attempting to send (saves a wasted
config-writing round-trip when the password has been rotated by Google).
"""
import smtplib
import os
import sys
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

# ---- Edit these ----
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "you@gmail.com"
SMTP_PASS = "xxxx xxxx xxxx xxxx"  # 16-char Gmail App Password

FROM_NAME = "Your Name"
FROM_ADDR = SMTP_USER
TO_ADDR = "recipient@example.com"
CC_ADDR = None  # set to an address, or leave None

SUBJECT = "Your subject line"

# Body text — keep it short; the attachments carry the payload
BODY = """Hi,

See attached.

Best,
Your Name
"""

# List of file paths to attach
ATTACHMENTS = [
    "/path/to/file1.pdf",
    "/path/to/file2.png",
]
# ---- End edit ----


def main() -> int:
    # Build message
    msg = EmailMessage()
    msg["From"] = f"{FROM_NAME} <{FROM_ADDR}>"
    msg["To"] = TO_ADDR
    if CC_ADDR:
        msg["Cc"] = CC_ADDR
    msg["Subject"] = SUBJECT
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=FROM_ADDR.split("@")[1])
    msg.set_content(BODY)

    # Attach files
    missing = []
    for path in ATTACHMENTS:
        if not os.path.exists(path):
            missing.append(path)
            continue
        with open(path, "rb") as f:
            data = f.read()
        fname = os.path.basename(path)
        lower = fname.lower()
        if lower.endswith((".png", ".jpg", ".jpeg", ".gif")):
            maintype, subtype = "image", "jpeg" if lower.endswith((".jpg", ".jpeg")) else "png"
        else:
            maintype = "application"
            subtype = "octet-stream"
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=fname)

    if missing:
        print(f"WARNING: missing files: {missing}", file=sys.stderr)

    # Connect + verify password FIRST (cheaper than attaching + sending
    # only to discover a 535)
    print(f"Connecting to {SMTP_HOST}:{SMTP_PORT} ...")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(SMTP_USER, SMTP_PASS)
    except smtplib.SMTPAuthenticationError as e:
        print(f"AUTH FAILED ({e.smtp_code}): {e.smtp_error.decode(errors='replace')}", file=sys.stderr)
        print("App passwords rotate. Generate a new one at https://myaccount.google.com/apppasswords", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"CONNECT FAILED: {e}", file=sys.stderr)
        return 2

    # Password verified — now send
    print(f"Logged in as {SMTP_USER}")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(SMTP_USER, SMTP_PASS)
        refused = s.send_message(msg)

    if refused:
        print(f"REFUSED: {refused}", file=sys.stderr)
        return 3

    print("OK: sent")
    print(f"  To: {TO_ADDR}")
    if CC_ADDR:
        print(f"  Cc: {CC_ADDR}")
    print(f"  Attachments: {len(ATTACHMENTS) - len(missing)}/{len(ATTACHMENTS)}")
    print(f"  Message-ID: {msg['Message-ID']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
