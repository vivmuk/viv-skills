#!/usr/bin/env python3
"""
Kriya Email Helper — Reliable SMTP email sender for OpenClaw.

Sends HTML reports and file attachments directly via Gmail SMTP,
bypassing the OpenClaw email plugin's sharp dependency issue.

Usage:
  python3 kriya_email.py --to vivek@live.de --subject "Report Title" --html report.html
  python3 kriya_email.py --to vivek@live.de --subject "Report" --html report.html --attach image.png
  python3 kriya_email.py --to vivek@live.de --subject "Report" --body "Plain text" --attach file.pdf

Config comes from environment variables or defaults below:
  OPENCLAW_SMTP_HOST, OPENCLAW_SMTP_PORT, OPENCLAW_SMTP_USER, OPENCLAW_SMTP_PASS,
  OPENCLAW_FROM_NAME, OPENCLAW_FROM_EMAIL, OPENCLAW_DEFAULT_TO
"""

import argparse
import os
import smtplib
import sys
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path

# Defaults — override with env vars or OPENCLAW_EMAIL_* in openclaw.json
SMTP_HOST = os.environ.get("OPENCLAW_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("OPENCLAW_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("OPENCLAW_SMTP_USER", "vivgatesai@gmail.com")
SMTP_PASS = os.environ.get("OPENCLAW_SMTP_PASS", "hxup huaq tvfe vcxk")
FROM_NAME = os.environ.get("OPENCLAW_FROM_NAME", "Kriya")
FROM_EMAIL = os.environ.get("OPENCLAW_FROM_EMAIL", "vivgatesai@gmail.com")
DEFAULT_TO = os.environ.get("OPENCLAW_DEFAULT_TO", "vivek@live.de")


def send_email(to, subject, body=None, html=None, attachments=None, from_name=FROM_NAME):
    """Send an email via SMTP."""
    msg = MIMEMultipart("mixed")
    msg["From"] = f"{from_name} <{FROM_EMAIL}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)

    alt = MIMEMultipart("alternative")
    if body:
        body_path = Path(body)
        alt.attach(MIMEText(body_path.read_text("utf-8") if body_path.exists() else body, "plain"))
    elif html:
        alt.attach(MIMEText("View this email in HTML mode.", "plain"))

    if html:
        html_path = Path(html)
        alt.attach(MIMEText(html_path.read_text("utf-8") if html_path.exists() else html, "html"))

    msg.attach(alt)

    if attachments:
        for att_path in attachments:
            p = Path(att_path)
            if not p.exists():
                print(f"WARNING: Attachment not found: {att_path}", file=sys.stderr)
                continue
            with open(p, "rb") as f:
                part = MIMEApplication(f.read())
            part.add_header("Content-Disposition", "attachment", filename=p.name)
            msg.attach(part)

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_EMAIL, to, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {to}: {subject}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {type(e).__name__}: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Kriya Email Helper")
    parser.add_argument("--to", default=DEFAULT_TO, help="Recipient email")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", help="Plain text body (or path to text file)")
    parser.add_argument("--html", help="HTML body (or path to HTML file)")
    parser.add_argument("--attach", nargs="*", help="File paths to attach")
    parser.add_argument("--from-name", default=FROM_NAME, help="Sender name")
    args = parser.parse_args()

    if not args.body and not args.html:
        parser.error("Must provide --body or --html")

    ok = send_email(
        to=args.to,
        subject=args.subject,
        body=args.body,
        html=args.html,
        attachments=args.attach,
        from_name=args.from_name,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()