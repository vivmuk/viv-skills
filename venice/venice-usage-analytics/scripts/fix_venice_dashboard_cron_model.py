#!/usr/bin/env python3
"""Verify and repair the Venice daily dashboard cron job model/provider.

When Venice retires a model ID, the Hermes cron job fails with HTTP 404.
This script checks the job config in ~/.hermes/cron/jobs.json and repairs it
to use a current Venice Claude Sonnet model.
"""

import json
import os
import sys

JOBS_PATH = os.path.expanduser("~/.hermes/cron/jobs.json")
JOB_ID = "4a378a1b2ef4"
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_PROVIDER = "venice"


def main() -> int:
    if not os.path.exists(JOBS_PATH):
        print(f"ERROR: jobs file not found: {JOBS_PATH}", file=sys.stderr)
        return 1

    with open(JOBS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    jobs = data.get("jobs", [])
    job = next((j for j in jobs if j.get("id") == JOB_ID), None)
    if job is None:
        print(f"ERROR: job {JOB_ID} not found in {JOBS_PATH}", file=sys.stderr)
        return 1

    original = {k: job.get(k) for k in ("model", "provider", "last_status", "last_error")}
    changed = False

    if job.get("model") != DEFAULT_MODEL:
        print(f"Updating model: {job.get('model')} -> {DEFAULT_MODEL}")
        job["model"] = DEFAULT_MODEL
        changed = True

    if job.get("provider") != DEFAULT_PROVIDER:
        print(f"Updating provider: {job.get('provider')} -> {DEFAULT_PROVIDER}")
        job["provider"] = DEFAULT_PROVIDER
        changed = True

    if job.get("last_status") == "error":
        print("Clearing stale error status")
        job["last_status"] = "scheduled"
        changed = True

    if job.get("last_error") is not None:
        print("Clearing stale last_error")
        job["last_error"] = None
        changed = True

    if changed:
        with open(JOBS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote updated jobs file: {JOBS_PATH}")
    else:
        print("Job config is already correct.")
        print(f"  model={job.get('model')}, provider={job.get('provider')}, status={job.get('last_status')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
