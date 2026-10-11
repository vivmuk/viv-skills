# Secure env / secret injection into CLI tools

The single most common mistake when working with hosted-platform CLIs (`maritime`, `gh`, `aws`, `gcloud`, `kubectl`, `fly`, `railway`, `npm config`, etc.) is leaking secrets onto the command line. The platform's audit log sees the shell's argv; so does `ps -ef`; so does shell history; so does an error message that includes argv.

## Traps

### Trap 1: malformed `export` with command substitution

```bash
# WRONG: bash sees two tokens, not one.
#   The leading "STARS" is treated as the value to assign; the $(cat …)
#   becomes a separate command. Bash emits an error line that contains the
#   literal secret bytes read from the file.
export VAR=STARS "$(cat /path)"
```

NOTE: never put placeholder strings (e.g. `STARS`, `***`, `<placeholder>`) before a `$(...)` substitution on the same command. Bash parses them as separate tokens. Use one of the patterns below instead.

Symptom in output:

```
export: `mk_xxx...REAL-SECRET': not a valid identifier
```

The secret bytes are visible to anyone reading the error stream.

### Trap 2: command lines like `cli --api-key $KEY` after assigning from a file

```bash
KEY=$(cat /path)        # OK in principle — key in shell variable, not in argv yet
cli --api-key "$KEY"    # BAD — KEY is now in argv of `cli`
```

The `cli` process sees the secret in its argv. `ps` lists it. Any error handler that logs argv leaks it.

### Trap 3: passing secrets via stdin but using `sh -c`

```bash
echo "$KEY" | cli login --with-token       # BAD if shell-expanded
sh -c "cli login --with-token=STARS $(< /path)"   # BAD: secret in argv of /bin/sh
```

### Trap 4: reading files inside shell loops

```bash
while read -r KEY; do
  cli login --key "$KEY"
done < /path/keys.txt    # BAD: secret in argv of every `cli` invocation
```

## Working patterns

### Pattern A — bash's single-token file slurp `$(< file)`

This is the simplest. It expands `$(< /path/file)` to the entire file content as a single token, with no subprocess.

```bash
export VAR=$(< /path/chmod600/file)
```

Properties:
- No `cat` subprocess.
- The variable is assigned in ONE shell expansion.
- After this line, the secret lives in the shell's env (or in this shell process). Subsequent commands reading `os.environ['VAR']` get the value without it appearing in their argv.
- This is the canonical form to copy when writing platform CLI integration helpers.

#### Equivalent forms (also correct)

```bash
# Same intent, with a `cat` subprocess. OK when the file path is the *only*
# thing on argv:
export VAR=$(cat /path/chmod600/file)

# Read with `read` (rarely needed but useful when reading line-by-line):
while IFS= read -r KEY; do ...; done < /path/chmod600/file
```

### Pattern B — heredoc + Python (preferred when the value isn't passable via env directly)

```bash
python3 -c "
import os
content = 'KEY=' + os.environ['KEY'] + '\n'
open('/path/.env', 'w').write(content)
os.chmod('/path/.env', 0o600)
"
cli upload-env /path/.env
```

Why this is safe:
- the secret stays in `os.environ` from Pattern A or from a previously sourced env-loader
- Python's `cli upload-env` reads the file as data — the file PATH is the only argv piece
- `cli upload-env`'s log shows the path, not the content

### Pattern C — a sourced env-loader script

```bash
# ~/.config/<platform>/env.sh
if [ -r /path/to/key ]; then
  PLATFORM_TOKEN=$(< /path/to/key)
  export PLATFORM_TOKEN
fi
```

Then from any shell that needs it:

```bash
source ~/.config/<platform>/env.sh
```

Add safety:

```bash
# At top of env.sh, prevent history capture of the assignment:
HISTFILE=/dev/null                  # bash
# And in zsh: setopt HIST_NO_STORE
```

### Pattern D — platform's built-in file-import subcommand

Most modern hosted platforms have an `env import` or `secrets` subcommand that takes a file path:

- `maritime env import <agent> <file>` — preferred for maritime.sh
- `gh auth login --with-token < /path/token` — reads from stdin
- `aws secretsmanager create-secret --secret-string file:///path`
- `fly secrets import < /path/secrets.env`

**Always prefer these.** They are the lowest-risk path because the tool itself was designed to receive the secret through file I/O.

## Operational hygiene rules

1. **Mirror keys to macOS keychain** on every successful auth:
   ```bash
   security add-generic-password -a <slug> -s <service> -w "$(< /path/key)" -U
   ```
   The `-U` flag updates if the entry already exists. The keychain is the canonical backup; chmod-600 files are convenience caches for non-interactive CLIs.

2. **On ANY exposure, rotate the leaked credential** via the platform's own CLI (`maritime keys revoke`, `gh auth logout --user <u>`, `aws iam delete-access-key`). The rotation command does **not** put the secret on argv; the platform's API only needs the *new* credential to authorize the rotation. Then verify whoami against the new credential, then revoke the old.

3. **Verify after rotation** with `maritime whoami --json`. The auth source should change from `env:MARITIME_TOKEN` to whatever new path; the *value* never needs to be touched by hand.

4. **Never log auth headers** to a debugging tool. `curl -v` outputs `Authorization: Bearer ...` to stderr. Use `-H "Authorization: Bearer $(< /path/key)"` so the secret is sourced at call time and not visible in `curl` debug output.

5. **Test the env-loading pattern in a non-secret-bearing file first** before applying to a real key. A broken pattern will print `export: 'X': not a valid identifier` in any test case.

6. **Use length-only sanity checks** for verification, never echo the value:
   ```bash
   [ -n "$VAR" ] && echo "loaded bytes=${#VAR}"   # length is fine; value is not
   ```

## What the platform itself does

Most platforms store keys in their own secret manager and reference them by ID internally.

- `maritime env list <agent>` shows masked values (`****XXXX`) on the CLI.
- The on-disk files in `~/.config/maritime/` are NOT the source of truth — they're convenience caches for non-interactive CLIs.
- The platform's encrypted at-rest store is rotated independently by the platform.

## The "do not write `***`" gotcha when authoring scripts

A working agent will often write `***` into a code block as a placeholder for a secret value. THIS IS A TRAP. A code block meant to be executed should never have `***` in place of a real bash substitute; the file will be broken at runtime.

When authoring a shell script that handles secrets:
- DO write `KEY=$(< /path/key)` as the actual literal characters in the code.
- DO write the comment ABOVE the line that explains the pattern.
- DO NOT write `KEY=*** "$VAR")` as a way of "showing where the secret goes". That's broken shell.

When documenting a secret-handling pattern:
- DO write the pattern with a clear placeholder like `<placeholder>` or `MY_KEY` (an obvious variable name), NOT `***`, in narrative text.
- DO NOT carry over the `***` shorthand from chat-redaction tooling into shell code blocks.
