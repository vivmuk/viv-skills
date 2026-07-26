# Hermes Venice Skills Setup Notes

Use this when configuring Venice.ai skills inside Hermes from the upstream `veniceai/skills` repository.

## Install/update upstream skill set

```bash
hermes skills tap add https://github.com/veniceai/skills
rm -rf /tmp/venice-skills
git clone --depth 1 https://github.com/veniceai/skills.git /tmp/venice-skills
python3 - <<'PY'
from pathlib import Path
import subprocess, sys
root = Path('/tmp/venice-skills/skills')
failed = []
for p in sorted(root.glob('*/SKILL.md')):
    name = p.parent.name
    url = f'https://raw.githubusercontent.com/veniceai/skills/main/skills/{name}/SKILL.md'
    r = subprocess.run(
        ['hermes', 'skills', 'install', url, '--category', 'veniceai', '--yes'],
        text=True, capture_output=True, timeout=120,
    )
    if r.returncode != 0 or 'blocked' in (r.stdout + r.stderr).lower():
        failed.append(name)
for name in failed:
    url = f'https://raw.githubusercontent.com/veniceai/skills/main/skills/{name}/SKILL.md'
    # Upstream docs-only skills can be blocked by cautious supply-chain/obfuscation examples.
    # Inspect output before forcing if the source is not trusted.
    subprocess.run(
        ['hermes', 'skills', 'install', url, '--category', 'veniceai', '--yes', '--force'],
        check=True, timeout=120,
    )
print('forced:', failed)
PY
```

## Environment convention

Store the same Venice bearer key under both names in Hermes' env file because older/imported scripts vary:

```bash
VENICE_API_KEY=...
VENICE_INFERENCE_KEY=...
```

Never hard-code raw Venice keys into skill markdown or scripts. If imported OpenClaw-era skills contain old literals, replace them with `process.env.VENICE_API_KEY || process.env.VENICE_INFERENCE_KEY` or equivalent Python `os.environ` lookups.

## Verification

After editing the env file, verify without printing the key:

```bash
set -a; . "$(hermes config env-path)"; set +a
curl -sS -o /tmp/venice_models_check.json -w '%{http_code}' \
  https://api.venice.ai/api/v1/models \
  -H "Authorization: Bearer ${VENICE_API_KEY}"
```

Expected: HTTP 200 and a parseable JSON model list. Count models with Python if desired.

## Pitfalls

- `hermes skills search venice` may not show a newly added tap immediately; direct `hermes skills install <raw SKILL.md URL>` works reliably.
- Some skills may be quarantined with a CAUTION verdict because docs contain `fetch`, `npm install`, or base64 examples. Use `--force` only after confirming the source is the official Venice repository.
- Older imported skills may mention `VENICE_API_KEY` in metadata but use `VENICE_INFERENCE_KEY` in scripts; keep both env aliases configured.
