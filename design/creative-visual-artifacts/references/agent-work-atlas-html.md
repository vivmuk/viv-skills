# Agent work-atlas HTML summaries

Use this reference when the user asks to turn an agent/session-history review into a polished HTML artifact.

## Artifact pattern

- Produce a single self-contained `.html` file with embedded CSS; save it under the relevant agent output folder when one exists (for Vivek's current AI Agents layout, Netrak summaries fit under `~/AIBrain/Netrak/Agent-Outputs/<slug>/`).
- Structure the artifact as an atlas, not a transcript dump:
  - hero: date range + one-sentence synthesis
  - key stats: sessions, active agents, folder-only agents, important counts
  - agent cards: each agent's role, main accomplishments, current status
  - themes: 5-8 durable patterns across the work
  - timeline: how the system evolved
  - ownership/next-moves: what should live where and what cleanup remains
- Keep sensitive details out: no API keys, tokens, hidden delivery targets, or raw private identifiers.
- Prefer strong visual hierarchy over dense tables: cards, timeline, ownership matrix, progress bars, badges.

## Verification pattern

1. Parse the HTML with Python's `html.parser` or another lightweight syntax check.
2. Render a screenshot before claiming the design is complete.
3. If Linux/WSL has no local Chromium/Playwright, use Windows Chrome/Edge from WSL via PowerShell:

```bash
powershell.exe -NoProfile -Command '& "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --headless=new --disable-gpu --hide-scrollbars --window-size=1440,1800 --screenshot="C:\\Users\\<user>\\OneDrive\\AI Agents\\Netrak\\Agent-Outputs\\<slug>\\preview.png" "file:///C:/Users/<user>/OneDrive/AI%20Agents/Netrak/Agent-Outputs/<slug>/artifact.html"'
```

4. Check the screenshot with vision before delivery: verify text is legible, hero/cards render, and no major clipping/blank page occurred.
5. Deliver both the HTML and PNG preview when possible.