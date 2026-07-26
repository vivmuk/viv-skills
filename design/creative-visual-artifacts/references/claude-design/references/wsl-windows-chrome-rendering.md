# WSL → Windows Chrome rendering for standalone HTML artifacts

Use this when creating a self-contained HTML/SVG artifact in WSL and you need a verified screenshot or PDF export for delivery.

## Pattern

1. Serve the artifact from its directory so Windows Chrome can load it reliably:

```bash
python3 -m http.server 8765 --bind 0.0.0.0
```

2. Render a screenshot from Windows Chrome. Use `http://localhost:<port>/file.html` or `http://127.0.0.1:<port>/file.html`:

```bash
powershell.exe -NoProfile -Command '& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --hide-scrollbars --window-size=1920,1400 --virtual-time-budget=5000 --screenshot="C:\Users\vivek\Downloads\artifact_preview.png" "http://localhost:8765/artifact.html"'
```

3. For PDF export, prefer `Start-Process` with a fresh `--user-data-dir`. Directly invoking Chrome can attach to an existing browser session or parse arguments strangely; `Start-Process` avoids the common “multiple targets” / “opening existing browser session” failure modes.

```bash
powershell.exe -NoProfile -Command '$out="C:\Users\vivek\Downloads\artifact.pdf"; $profile="C:\Users\vivek\Downloads\chrome-headless-"+[guid]::NewGuid(); $args=@("--headless=new","--disable-gpu","--no-sandbox","--user-data-dir=$profile","--print-to-pdf=$out","--no-pdf-header-footer","--run-all-compositor-stages-before-draw","--virtual-time-budget=8000","http://127.0.0.1:8765/artifact.html"); $p=Start-Process -FilePath "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList $args -NoNewWindow -PassThru -Wait; Write-Output "EXIT=$($p.ExitCode) OUT=$out"; if(Test-Path $out){ (Get-Item $out).Length }'
```

4. Verify the output exists and is non-trivial in size, then inspect at least the PNG preview with vision before claiming visual success.

```bash
python3 - <<'PY'
from pathlib import Path
for p in ['/mnt/c/Users/vivek/Downloads/artifact_preview.png','/mnt/c/Users/vivek/Downloads/artifact.pdf']:
    path=Path(p)
    print(p, path.exists(), path.stat().st_size if path.exists() else 0)
PY
```

## Notes

- Save Windows-delivered files under `/mnt/c/Users/vivek/Downloads/` when the user wants easy access on the host.
- Use `Start-Process` for PDF generation even if screenshot generation worked directly.
- Keep the server running only for verification/export; kill it when done.
- This is a rendering/export pattern, not a statement that Linux browser tools are unavailable. Prefer native tools if they are already configured and working.
