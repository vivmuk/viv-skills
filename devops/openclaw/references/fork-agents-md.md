# Paperclip Fork AGENTS.md — Key Excerpts

Source: `/home/vivgates/paperclip/AGENTS.md`

This is a condensed reference of the fork-specific and critical sections from AGENTS.md for quick consultation without reading the full file each session.

## Fork: HenkDz/paperclip

- Branch: `feat/externalize-hermes-adapter`
- Core has NO `hermes-paperclip-adapter` dependency
- NO built-in `hermes_local` registration
- Hermes installs via Adapter Plugin manager or `file:` path in `~/.paperclip/adapter-plugins.json`

## Local Dev Warnings

- Port auto-detects: skips 3100 if taken, uses 3101+
- `npx vite build` hangs on NTFS — use `node node_modules/vite/bin/vite.js build`
- Server startup 30-60s on NTFS — don't assume failure
- Kill ALL paperclip processes before restart: `pkill -f "paperclip"; pkill -f "tsx.*index.ts"`
- Vite cache survives `rm -rf dist` — delete both: `rm -rf ui/dist ui/node_modules/.vite`

## Fork QoL Patches (not in upstream)

1. **stderr_group** — amber accordion for MCP init noise in `RunTranscriptView.tsx`
2. **tool_group** — accordion for consecutive non-terminal tools
3. **Dashboard excerpt** — `LatestRunCard` strips markdown, shows first 3 lines/280 chars

## Plugin System (PR #2218: feat/external-adapter-phase1)

- External adapters loaded via `~/.paperclip/adapter-plugins.json`
- Plugin-loader has ZERO hardcoded adapter imports — pure dynamic loading
- `createServerAdapter()` must include ALL optional fields (especially `detectModel`)
- Built-in UI adapters can shadow external plugin parsers — remove built-in when fully externalizing
- Reference external adapter paths with `file:` protocol for local dev

## Core Engineering Rules

1. Keep changes company-scoped — every entity scoped to a company
2. Keep contracts synchronized — schema → shared types → server routes → UI
3. Preserve control-plane invariants: single-assignee tasks, atomic issue checkout, approval gates, budget auto-pause, activity logging
4. Don't replace strategic docs wholesale — additive updates, keep SPEC.md aligned with SPEC-implementation.md
5. Plan docs go in `doc/plans/` with `YYYY-MM-DD-slug.md` filenames

## PR Template Requirements

Every PR MUST fill in `.github/PULL_REQUEST_TEMPLATE.md` sections:
- Thinking Path
- What Changed
- Verification
- Risks
- Model Used (provider, exact model ID, context window, capabilities)
- Checklist (all items checked)