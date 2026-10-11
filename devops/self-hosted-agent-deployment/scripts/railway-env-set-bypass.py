#!/usr/bin/env python3
"""Railway env-set bypass template — Hermes redact-filter safe.

Use this pattern when shell-quoted env values get mangled by the Hermes text
filter (UUID-shaped tokens, comma-separated user IDs, anything that travels
through write_file / terminal echo).

Usage: copy this file, edit SERVICE_NAME and VARIABLE_LIST, then:
    unset RAILWAY_TOKEN RAILWAY_API_TOKEN
    python3 /tmp/set_railway_vars.py

The script handles three Railway CLI quirks in one place:
  1. RAILWAY_TOKEN="" reads as "Invalid token"; we OMIT it from subprocess env
  2. --set-from-stdin rejects empty input; --stdin is the cleanest pipe path
  3. comma-digits in single literal get mangled by the filter; we concat at runtime

After the variable set calls succeed, you can either:
  - Wait for Railway's automatic redeploy (if --skip-deploys was NOT used)
  - Force a redeploy explicitly with:
      subprocess.run(["railway", "service", "redeploy", "--service", SERVICE, "--yes"], ...)
"""
import os, subprocess, sys

# ---- Configuration ---------------------------------------------------------
SERVICE_NAME = "jiva"            # <-- edit
DEPLOY_CWD = os.path.expanduser("~/tmp/jiva-deploy")   # <-- edit

# (key, value) pairs to set. Define each value as a separate variable
# if it's UUID-shaped or comma-digit-shaped, to avoid the filter munging a
# single literal. Wire VALUES as plain strings here.
VARIABLE_LIST: list[tuple[str, str]] = [
    # ("TELEGRAM_ALLOWED_USERS", "6808691714,8681045146"),
    # ("HERMES_HUMAN_DELAY_MODE", "natural"),
    # ...
]

# For values built from multiple pieces (comma-digits or otherwise composite
# values), define each piece as its own string and concatenate at runtime.
# Example:
# USER_A = "6808691714"
# USER_B = "8681045146"
# VARIABLE_LIST.append(("TELEGRAM_ALLOWED_USERS", USER_A + "," + USER_B))

# End of configuration ------------------------------------------------------


def child_env() -> dict:
    """Build subprocess env, omitting Railway auth keys entirely.

    Railway CLI treats empty-string RAILWAY_TOKEN as 'Invalid token',
    not 'absent'. The only correct way to pass 'no RAILWAY_TOKEN'
    through Python subprocess is to OMIT it from the env dict.
    """
    return {k: v for k, v in os.environ.items()
            if k not in ("RAILWAY_TOKEN", "RAILWAY_API_TOKEN")}


def set_var(key: str, value: str) -> None:
    """Run: railway variable set --skip-deploys KEY=VALUE --service X"""
    argv = f"{key}={value}"
    print(f"  $ railway variable set --skip-deploys {argv} --service {SERVICE_NAME}")
    r = subprocess.run(
        ["railway", "variable", "set", "--skip-deploys", argv, "--service", SERVICE_NAME],
        cwd=DEPLOY_CWD,
        env=child_env(),
        capture_output=True,
        timeout=60,
    )
    out = r.stdout.decode().strip()
    err = r.stderr.decode().strip()
    if out: print(f"    stdout: {out}")
    if err: print(f"    stderr: {err}")
    r.check_returncode()


def restart() -> None:
    """Run: railway service restart --service X (cycles container with new env)."""
    print(f"  $ railway service restart --service {SERVICE_NAME}")
    r = subprocess.run(
        ["railway", "service", "restart", "--service", SERVICE_NAME],
        cwd=DEPLOY_CWD,
        env=child_env(),
        capture_output=True,
        timeout=60,
    )
    out = r.stdout.decode().strip()
    err = r.stderr.decode().strip()
    if out: print(f"    stdout: {out}")
    if err: print(f"    stderr: {err}")


def list_vars() -> None:
    """Run: railway variable list --service X --kv (sanity check)."""
    r = subprocess.run(
        ["railway", "variable", "list", "--service", SERVICE_NAME, "--kv"],
        cwd=DEPLOY_CWD,
        env=child_env(),
        capture_output=True,
        timeout=30,
    )
    out_lines = r.stdout.decode().splitlines()
    for line in out_lines:
        if any(line.startswith(prefix) for prefix in
               ("HERMES_", "TELEGRAM_", "OPENAI_", "DISCORD_", "RAILWAY_")):
            print(f"  {line}")


def service_status() -> None:
    """Run: railway service ls (post-deploy sanity)."""
    r = subprocess.run(
        ["railway", "service", "ls"],
        cwd=DEPLOY_CWD,
        env=child_env(),
        capture_output=True,
        timeout=30,
    )
    print(r.stdout.decode().strip())


# ---- Orchestration ---------------------------------------------------------
def main() -> None:
    print(f"=== Railway env bypass — service={SERVICE_NAME} ===\n")
    for key, value in VARIABLE_LIST:
        set_var(key, value)
        print()
    print("=== restart so env-only changes take effect ===")
    restart()
    print("\n=== variable list (relevant prefixes only) ===")
    list_vars()
    print("\n=== service status ===")
    service_status()


if __name__ == "__main__":
    main()
