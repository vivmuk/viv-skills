# HTML summary atlas pattern

Use this pattern when the user asks to turn a long operational summary, agent history, work log, or strategy synthesis into a polished standalone HTML artifact.

## When to use

- “Make this into a nice / beautiful HTML summary.”
- Multi-agent work summaries, timelines, ownership maps, dashboards, or retrospective reports.
- User expects an actual file plus visual proof, not just Markdown.

## Structure that worked well

1. **Sticky rounded nav** with anchor links to major sections.
2. **Hero section** with a short date/source line, large gradient headline, and one paragraph explaining the artifact.
3. **Visual system map** using CSS only: central node + surrounding agent/domain nodes.
4. **Metric cards** for grounding counts such as sessions, agents, folders, open issues.
5. **Agent/work cards** with concise bullet lists and live/folder/status badges.
6. **Theme grid** with icons + paragraph summaries.
7. **Timeline** with dated milestones.
8. **Ownership/status matrix** with OK/warn/bad states.
9. **Next-step callout** with concrete cleanup checklist.
10. **Footer** stating data sources and that secrets were excluded.

## Implementation tips

- Make it self-contained: inline CSS, no external fonts/assets unless the user asks.
- Use CSS gradients, glass panels, cards, badges, and a dark background for a polished executive-dashboard feel.
- Keep PII/secrets out. Summarize sensitive sources rather than embedding raw drafts, tokens, or personal identifiers.
- Save under the relevant agent output folder when the artifact is about agent work, e.g. `~/Netrak/Agent-Outputs/...` or the OneDrive equivalent.

## Verification pattern from WSL

If Linux browser tooling is absent but Windows Chrome is installed, render a screenshot from WSL with PowerShell:

```bash
powershell.exe -NoProfile -Command '& "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --headless=new --disable-gpu --hide-scrollbars --window-size=1440,1800 --screenshot="C:\\path\\preview.png" "file:///C:/path/artifact.html"'
```

Then verify file size and inspect the screenshot with vision before claiming completion.

## Delivery

Return both:

```text
MEDIA:/absolute/path/to/artifact.html
MEDIA:/absolute/path/to/preview.png
```

Say how it was verified: HTML parsed, screenshot rendered, visually checked.
