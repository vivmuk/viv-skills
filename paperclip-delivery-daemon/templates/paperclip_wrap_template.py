"""
Paperclip wrapper template — for routing a cron-driven content script
through Paperclip so the auto-delivery daemon emails the deliverable.

ADAPT FOR YOUR CRON: replace SCRIPT_NAME, the run_<name>() function body,
and the comment template. Everything else is the standard pattern.

The 5 steps the wrapper does:
  1. Run the existing content-generation script (NO emailing — the
     wrapper handles delivery, the daemon handles the email).
  2. Create a Paperclip issue assigned to the right agent.
  3. Upload the generated files as Paperclip attachments (multipart).
  4. Post a markdown summary as a comment.
  5. PATCH the issue to status=done (so the daemon picks it up).

Gotchas this template handles correctly:
  - in_progress issues REQUIRE an assigneeAgentId
  - "done" on CREATE is silently rejected — create as in_progress, PATCH
    to done
  - The daemon can't read file:// URLs (it prepends PAPERCLIP_BASE to
    everything). Use the multipart attachments endpoint, not the work
    product endpoint with a file:// url field.
  - --from-existing=<path> flag for testing without re-running the
    expensive pipeline.
"""
import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
import datetime

PAPERCLIP_BASE = os.environ.get("PAPERCLIP_BASE", "http://127.0.0.1:3100")

# ── Adapt these three constants for your cron job ──
COMPANY_ID = "REPLACE_WITH_YOUR_COMPANY_ID"  # Paperclip company UUID
ASSIGNEE_AGENT_ID = "REPLACE_WITH_AGENT_ID"  # ContentDirector, CEO, etc.
SCRIPT_NAME = "my_content_generator.py"      # the existing script
SCRIPT_CWD = "/path/to/script/workspace"
SCRIPT_EXTRA_ARGS = []  # e.g. ["--no-email"] for scripts that have it

DATE = datetime.date.today().isoformat()


# ── Standard helpers (don't change unless you know why) ──

def call(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{PAPERCLIP_BASE}{path}", data=data, method=method)
    if body: req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")
    except Exception as e:
        return 0, str(e)


def upload_attachment(issue_id, path):
    """Multipart upload — the ONLY path the daemon can fetch from."""
    if not os.path.exists(path):
        print(f"  missing: {path}")
        return False
    filename = os.path.basename(path)
    with open(path, "rb") as f:
        data = f.read()
    boundary = "----paperclip" + os.urandom(8).hex()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{PAPERCLIP_BASE}/api/companies/{COMPANY_ID}/issues/{issue_id}/attachments",
        data=body, method="POST",
    )
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            print(f"  uploaded {filename} ({len(data)} bytes) HTTP {r.status}")
            return True
    except Exception as e:
        print(f"  FAILED {filename}: {e}")
        return False


# ── Adapt this function for your script ──

def run_content_script():
    """Run the existing content-generation script.

    Returns: a result object (any JSON-serializable dict) that the rest
    of the wrapper can use, or None to fail.

    The result must include:
      - report_path (str): path to the main deliverable file
      - image_attachments (list of str): paths to any images
      - summary_text (str): markdown for the comment
    """
    print(f"[1/5] running {SCRIPT_NAME} ...")
    r = subprocess.run(
        ["python3", SCRIPT_NAME] + SCRIPT_EXTRA_ARGS,
        cwd=SCRIPT_CWD, capture_output=True, text=True, timeout=900,
    )
    if r.returncode != 0:
        print(f"  FAILED: {r.stderr[:500]}")
        return None
    # Parse the last JSON block from stdout (your script prints a dict at the end)
    out = r.stdout
    i = out.rfind("{")
    if i < 0:
        print("  no JSON in output")
        return None
    return json.loads(out[i:])


# ── Standard functions (don't change) ──

def create_issue(title, description):
    print("[3/5] creating Paperclip issue...")
    s, issue = call("POST", f"/api/companies/{COMPANY_ID}/issues", {
        "title": title,
        "description": description,
        "status": "in_progress",  # NOT done — silently rejected on create
        "priority": "high",
        "assigneeAgentId": ASSIGNEE_AGENT_ID,
    })
    if s != 201:
        print(f"  HTTP {s}: {json.dumps(issue)[:200]}")
        return None
    print(f"  created {issue.get('identifier')}  id={issue['id'][:8]}")
    s2, _ = call("PATCH", f"/api/issues/{issue['id']}", {"status": "done"})
    if s2 == 200:
        print("  transitioned to done (daemon will email)")
    return issue


def add_comment(issue_id, body):
    print("[4/5] posting summary comment...")
    s, _ = call("POST", f"/api/issues/{issue_id}/comments", {"body": body})
    print(f"  comment: HTTP {s}")


def main():
    # 1. Run the existing script
    result = run_content_script()
    if not result:
        print("ERROR: content script failed. Exiting.")
        sys.exit(1)

    # 2. Resolve the deliverable
    report_path = result["report_path"]
    images = result.get("image_attachments", [])
    summary = result.get("summary_text", "")

    # 3. Create the issue
    title = f"{SCRIPT_NAME.replace('.py','')} — {DATE}"
    description = (
        f"**Date:** {DATE}\n"
        f"**Main deliverable:** {os.path.basename(report_path)}\n"
        f"**Image attachments:** {len(images)}\n"
    )
    issue = create_issue(title, description)
    if not issue:
        sys.exit(1)

    # 4. Upload files (main deliverable + images)
    print(f"[2/5] uploading {1 + len(images)} file(s)...")
    upload_attachment(issue["id"], report_path)
    for img in images:
        upload_attachment(issue["id"], img)

    # 5. Post summary comment
    add_comment(issue["id"], summary)

    print(f"\n[done] issue {issue.get('identifier')} closed; daemon will email.")


if __name__ == "__main__":
    # Support --from-existing=<path> for testing without re-running the pipeline
    existing = None
    for arg in sys.argv[1:]:
        if arg.startswith("--from-existing="):
            existing = arg.split("=", 1)[1]
            break
    if existing:
        print(f"using existing result: {existing}")
        # Inject as the result
        with open(existing) as f:
            sys.modules[__name__].__dict__["_TEST_RESULT"] = json.load(f)
        # Patch run_content_script to return the injected result
        run_content_script = lambda: sys.modules[__name__].__dict__["_TEST_RESULT"]
    main()
