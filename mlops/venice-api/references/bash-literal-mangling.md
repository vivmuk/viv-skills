# Bash Literal Mangling: `***REDACTED***` and Similar Patterns

## The bug

When a file is written through bash heredocs, `write_file`, or any tool that
shells out, the literal string `***REDACTED***` has its closing characters
stripped. Result: a `***REDACTED***` literal in a Python source file becomes
an unterminated string, and the file fails to parse with:

```
SyntaxError: EOL while scanning string literal
```

The error points at the line that contains the mangled literal. The file looks
fine in the editor — the closing characters are simply missing on disk.

This bites **any** script that needs to read a secret from an `.env` file
where the key is referenced by the literal env var name. Specifically:
`VENICE_API_KEY=***REDACTED***` in `~/.paperclip/instances/default/.env`.

## Diagnosis

```bash
# 1. Does the file have a syntax error?
python3 -c "import ast; ast.parse(open('/path/to/script.py').read()); print('OK')"

# 2. Show the broken line
grep -n "REDACTED" /path/to/script.py | head -5

# 3. Compare what bash sees vs what's on disk
od -c /path/to/script.py | grep -A 1 "VENICE"
```

## Three workarounds (pick one)

### A. Build the string at runtime (preferred for short scripts)

```python
placeholder = "X" * 16
prefix = "VENICE_API_KEY=*** + placeholder

key = None
with open("/path/to/.env") as f:
    for line in f:
        if line.startswith(prefix):  # runtime-constructed string
            key = line.split("=", 1)[1].strip()
            break
```

This works because the `***REDACTED***` literal is never written to disk —
it's reconstructed at import time from the safe `placeholder` variable.

### B. Use a tiny bash helper script (preferred for reusable loaders)

Write the helper to disk first, separately from any Python that contains the
literal:

```bash
# /tmp/load_venice_key.sh
#!/bin/bash
prefix="VENICE_API_KEY=*** + "$(printf 'X%.0s' $(seq 1 16))
while IFS= read -r line; do
    if [[ "$line" == "$prefix"* ]]; then
        echo "${line#*=}"
        exit 0
    fi
done < /path/to/.env
# Fallback to the inference key if the main key isn't present
while IFS= read -r line; do
    if [[ "$line" == "VENICE_INFERENCE_KEY="* ]]; then
        v="${line#*=}"
        if [[ ${#v} -gt 20 ]]; then
            echo "$v"
            exit 0
        fi
    fi
done < /path/to/.env
```

Then call from Python:

```python
import subprocess
key = subprocess.check_output(["/tmp/load_venice_key.sh"]).decode().strip()
```

### C. Use environment variables (best for production)

Set the key in the shell:

```bash
export VENICE_API_KEY=***REDACTED***
```

Read it in Python:

```python
import os
key = os.environ.get("VENICE_API_KEY", "")
```

In Paperclip, the same pattern works via the agent's `adapterConfig.env`:
the key is set once in the agent's environment and the script reads it from
`os.environ`. This is the most robust because there's no literal in source
files at all.

## Why this matters

This isn't a Python issue — it's a bash heredoc / shell-expansion issue.
`***REDACTED***` in any context where bash or a shell-aware tool is processing
the file content will get its closing characters stripped. If you see
`SyntaxError: unterminated string literal` on a line that LOOKS like it has a
closed string, suspect this immediately.

The pattern catches you when:
- Writing Python via `write_file` tool (some tools shell out)
- Writing Python via `cat > file.py << EOF` heredocs
- Copy-pasting scripts that other LLMs wrote (some Markdown renderers also
  strip these)
- Reading a script from git history that was originally generated through
  any of the above

## When NOT to use this pattern

- Production code where the key comes from a secrets manager (Vault, AWS
  Secrets Manager, etc.) — just read directly.
- Scripts that need to be portable across machines with different key files.
  In that case, use Workaround C (env vars) and document the env var name.

## See Also

- `content-marketing-pipeline` SKILL.md pitfall #14 — the carousel workflow
  hit this exact issue
- `content-marketing-pipeline` SKILL.md pitfall #19 — separate surfacing of
  the same bug
