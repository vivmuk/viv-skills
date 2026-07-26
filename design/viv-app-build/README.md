# Viv Design + Grill Bundle (v2)

A unified frontend-craft + interview-driven build workflow packaged for installation on any agent that supports the `SKILL.md` format (Hermes, Claude Code, Cursor, Gemini CLI, Codex, Kiro, OpenCode, etc.).

## What's in this bundle

```
viv-skill-bundle-v2/
├── README.md                                  # you are here
├── SOURCES.md                                 # attribution + re-sync strategy
├── viv-app-build/
│   └── SKILL.md                               # the orchestrator: grilling -> viv-design
├── viv-design/
│   ├── SKILL.md                               # main doctrine (~48 KB)
│   └── references/
│       ├── animation-rules.md                 # citable animation values
│       ├── animation-vocabulary.md            # "what's it called when..."
│       ├── anti-slop-checks.md                # production-tested LLM tells
│       ├── brand-register.md                  # brand slop test + font reject list
│       ├── design-systems-map.md              # brief -> official package map
│       ├── origin-notes.md                    # upstream sources
│       └── product-register.md                # product slop test + accessibility
├── mattpocock-grill-me/                       # user-invoked /grill-me shim
│   └── SKILL.md
├── mattpocock-grilling/                       # the actual interview primitive
│   └── SKILL.md
└── mattpocock-grill-with-docs/                # stateful variant (writes ADRs as it grills)
    └── SKILL.md
```

Three skill families, one workflow:

| Family | What it does | When to invoke |
|---|---|---|
| `mattpocock-grill-me` | User-invoked front door (`/grill-me` equivalent). Stateless. | You type `/grill-me` and the interview starts. |
| `mattpocock-grilling` | The actual interview primitive. Walks every branch of the decision tree, one question at a time, with the agent's recommendation. | Model-invoked; loaded automatically when `grill-me` or `viv-app-build` runs. |
| `mattpocock-grill-with-docs` | Stateful sibling: same interview + writes ADRs and a glossary as it goes. | Run `/grill-with-docs` when you want the decisions captured. |
| `viv-design` | Unified frontend craft doctrine. Brief inference → three dials → register → color/typography/layout/motion → anti-slop preflight. | Auto-triggers on any UI/frontend request. |
| `viv-app-build` | Orchestrator. **Always starts with grilling**, then chains into viv-design for the UI portion. | Auto-triggers on any "build me X / develop X / ship X / scaffold X." |

## Workflow

```
User:  "Build me a SaaS dashboard for managing freelance contracts"
                        │
                        ▼
              viv-app-build loads          (auto-trigger on app-build language)
                        │
                        ▼
              mattpocock-grilling          (relentless interview)
              ├─ walks every branch of the design tree
              ├─ asks one question at a time
              ├─ states my recommended answer alongside each question
              ├─ explores codebase for FACTs (not DECISIONs)
              └─ waits until user confirms shared understanding
                        │
                        ▼
              grilling recap                (3-5 bullet brief)
                        │
                        ▼
              viv-design doctrine           (apply craft)
              ├─ state the design read in one line
              ├─ set the three dials (VARIANCE / MOTION / DENSITY)
              ├─ pick the register (brand vs product)
              ├─ apply color / typography / layout / motion
              ├─ run anti-slop preflight
              └─ deliver with before/after review format if revising
```

Sub-commands also compose: `viv-app-build craft my-feature`, `viv-app-build polish auth-modal`. Add `no-grill` to skip the interview for clear, well-specified work.

## Install on a target agent

Pick the destination your agent reads skills from. Drop the **entire** `viv-skill-bundle-v2/` contents into the agent's skills directory.

```bash
# Pick your agent's skills directory
DEST=~/.claude/skills       # Claude Code
# or:  ~/.cursor/skills      # Cursor
# or:  ~/.gemini/skills      # Gemini CLI
# or:  ~/.codex/skills       # Codex CLI
# or:  ~/.opencode/skills    # OpenCode
# or:  ~/.kiro/skills        # Kiro
# or:  ~/.hermes/skills      # Hermes Agent (default)

mk="mkdir"
for d in viv-app-build viv-design mattpocock-grill-me mattpocock-grilling mattpocock-grill-with-docs; do
  $mk -p "$DEST/$d"
done

# Then copy files from this bundle's top-level into $DEST/.
```

After install:

- Any **app build** request → `viv-app-build` auto-triggers, runs grilling, then applies viv-design.
- Any **pure UI / page / component** request → `viv-design` auto-triggers directly.
- Explicit invocation: `/grill-me`, `/grilling`, `/grill-with-docs`, `viv-design <command> [target]`, `viv-app-build <command> [target]`.

## Verification after install

1. Open the target agent's skills directory and confirm the five folders are present.
2. Run a probe request: `"Build me a personal todo app"` — verify the agent asks ONE question at a time and waits for your answer before coding.
3. Run a pure-UI request: `"Design a marketing landing page for a coffee shop"` — verify the agent skips grilling and lands directly in viv-design's design-read + dials + register flow.

## Re-syncing from upstream

The doctrine evolves. Three upstream repos feed this bundle:

| Repo | What it ships | Pull command |
|---|---|---|
| `github.com/emilkowalski/skills` | Animation doctrine, before/after review format | `git clone --depth=1 https://github.com/emilkowalski/skills.git` |
| `github.com/pbakaus/impeccable` | Brand vs product register split, anti-slop bans, command taxonomy | `git clone --depth=1 https://github.com/pbakaus/impeccable.git` |
| `github.com/Leonxlnx/taste-skill` | Brief inference, three dials, hero discipline, LLM tells | `git clone --depth=1 https://github.com/Leonxlnx/taste-skill.git` |
| `github.com/mattpocock/skills` | Grilling interview primitive, grill-with-docs | `git clone --depth=1 https://github.com/mattpocock/skills.git` |

When any source ships a meaningful update, re-pull, then re-extract into the corresponding folder under this bundle and re-zip. See `SOURCES.md` for the precise mapping.

## License

This bundle is packaged as MIT-licensed by Viv (Hermes Agent for Vivek M). Upstream content retains its original license — see `SOURCES.md` for each repo's license.
