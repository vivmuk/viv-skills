# Design PR Visibility Checks

Use this when a design refresh is implemented through git/PR and the user will judge it visually.

## Lesson

A large code diff is not the same as an obvious visual change. If a site still uses the same content/images/data, a user may say it "looks the same" even when layout/CSS/JS changed. Before presenting a design PR as a redesign, verify and communicate the visible delta.

## Required checks before saying the redesign is done

1. Compare deployed/live branch vs PR branch, not just local files:
   - `git diff --stat origin/main...HEAD`
   - inspect old/new `index.html` titles, byte sizes, and major CSS/HTML markers
   - if a public deployed URL exists, fetch it and confirm whether it is still serving `main`
2. Generate or capture a visual preview when possible:
   - browser screenshot with Playwright/Chromium if available
   - WSL fallback: run a local HTTP server and invoke Windows Chrome/Edge headless via `powershell.exe`; the reusable helper is `scripts/capture-wsl-windows-chrome-screenshot.ps1`
   - deliver the generated PNG directly in chat with `MEDIA:/absolute/path` when the conversation surface supports media
   - fallback of last resort: provide the localhost URL plus concrete visible changes
3. Check whether the original PR was already merged before iterating:
   - if merged, branch/PR state may point at the pre-merge head SHA and a follow-up PR from the same branch can become `mergeable_state: dirty`
   - reset/rebase the design branch onto current `origin/main`, reapply the follow-up visual changes, force-push with lease, then verify the new PR is `mergeable_state: clean`
4. Be explicit about deployment state:
   - "PR branch changed" is different from "live site changed"
   - if PR is unmerged, the public site may still look identical
4. Be explicit about deployment state:
   - "PR branch changed" is different from "live site changed"
   - if PR is unmerged, the public site may still look identical
5. If the visual delta is subtle, say so and offer a stronger pass before merge:
   - stronger hero, more dramatic typography, color system, card layout, motion, navigation, etc.
6. Avoid over-claiming from line counts alone. Use line counts only as supporting evidence, never as proof of visual improvement.

## Good response pattern

- "Yes, changes are on the PR branch, not live on main yet."
- List 4-6 visible changes in plain language.
- Explain how to preview the exact branch.
- If the user says it still looks the same, treat that as design feedback and iterate rather than defending the diff.
