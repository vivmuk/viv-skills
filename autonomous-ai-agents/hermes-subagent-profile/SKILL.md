---
name: hermes-subagent-profile
description: Create a Hermes profile that runs as an isolated sub-agent with its own Telegram bot, bounded toolset, and strict separation from the default profile (you). Triggers on "create a sub-agent", "subagent profile", "isolated bot", "shared helper", "sidekick in Telegram", "share my bot with others", "make a hermes profile that doesn't touch my stuff", or "different hermes for my team / collaborators / customers".
tags: [hermes, profile, isolation, subagent, telegram, sandbox]
triggers:
  - "sub-agent profile"
  - "isolated hermes profile"
  - "subagent with its own telegram"
  - "different bot for my team"
  - "shared helper profile"
  - "hermes profile for collaborators"
category: autonomous-ai-agents
---

# Hermes Sub-agent Profile (isolated bot, bounded toolset)

> **READ THIS FIRST — isolation is policy-level, NOT OS-jail.**
> A Hermes sub-agent profile achieves isolation via **policy +
> toolsets + filesystem boundaries**, not kernel-level sandboxing.
> That means:
>
> - The toolset denylist (`disabled_toolsets`) blocks shell, file
>   writes outside the profile dir, delegation, cronjob, send_message,
>   memory. This is enforced by hermes-cli before each tool fires.
> - The SOUL.md text rules are read every turn and the LLM is told
>   to refuse cross-profile reads. A clever user can talk past SOUL.
> - The filesystem is shared. A stray `terminal` command *could*
>   read `~/.hermes/memories/USER.md` if the LLM lets it.
>
> **If the user said "no access to anything else on the system"**,
> tell them up front: the policy + toolsets path gives roughly
> 95% isolation (safe for "share with friends / beta testers /
> collaborators") but is NOT a kernel-enforced jail. The only true
> jail is: Docker + seccomp + non-root user + read-only mounts —
> usually a 1-evening setup. Build that **only if the user
> explicitly asks** for true jail.
>
> A user who demanded "no access to anything else" and was given
> only the policy-level version will likely cancel the project when
> the limit is finally admitted. So make the limit visible in your
> first reply, not after you scaffold the profile.

You run in the default profile (Vivek's DM, his main chat, all his
state). The user is asking you to create an **independent** Hermes
profile that:

1. Lives at `~/.hermes/profiles/<name>/` with its own `skills/`,
   `plugins/`, `cron/`, `memories/`, plus its own `config.yaml`
   and `SOUL.md`.
2. Has its **own Telegram bot identity** (separate token, separate
   `allowed_chats`, separate display name).
3. Has a **bounded toolset** — no `delegation`, no `cronjob`, no
   `memory`, no `send_message` to the default-profile main chat, no
   cross-profile file access. Whether to allow `terminal` / `file`
   depends on whether the sub-agent will be **teachable** (need file
   + skills to author skills) or **read-only** (sell to outside
   users, never let them author skills).
4. Runs as a **separate Hermes process** so its Telegram bot doesn't
   collide with the default profile's bot.

This pattern is distinct from `paperclip` (which is multi-agent
orchestration inside a managed company) and from `openclaw` /
`kanban-codex-lane` (which run other agent CLIs, not local Hermes
profiles). Sub-agent profiles are *local* primarily; they are
useful when the user wants to either share an agent with outside
people in a controlled way, or to run multiple specialised agents
on the same HERMES_HOME.

## When this fits

- The user wants to give a Telegram bot to "anyone but me" — friends,
  team members, paying customers, beta testers.
- The user wants a sidekick that can author its own skills over time
  (teachable surface = file + skills + terminal with prose fences).
- The user wants different topic domains side-by-side on the same
  machine (one profile for pharma, one for recipes), without cross-
  contamination of memories or skills.

## When this does NOT fit

- The user wants a *single* agent with more permissions. That is just
  the default profile with a wider toolset — no second profile needed.
- The user wants managed multi-agent orchestration with task routing
  and budget tracking. Use `paperclip` instead.
- The user wants to run the agent on a different machine / cloud. That
  is a deployment, not a profile.

## The canonical directory layout

```
~/.hermes/profiles/<name>/
├── config.yaml        # model + toolset + telegram + approvals
├── SOUL.md            # persona + hard boundary rules
├── README.md          # for the user / collaborators to onboard
├── skills/            # empty initially; teachable
├── plugins/           # empty initially
├── cron/              # empty; cronjob is disabled
└── memories/          # empty; memory is disabled
```

`<name>` should be class-level (e.g. `pharma-sidekick`,
`research-helper`, `shared-helper`) — not session-specific
(`mira-2026-06-27`, `peter-test`). If the name only makes sense for
today's task, the design is wrong.

## config.yaml shape (teachable variant)

```yaml
model:
  default: minimax-m3-preview           # or whatever fits the use case
  provider: custom
  base_url: https://api.venice.ai/api/v1
  api_key: VENICE_INFERENCE_KEY_<...>   # independent key, independent DIEM cap
  context_length: 128000
  max_output_tokens: 8000

agent:
  max_turns: 30
  toolsets:                              # teachable variant
    - read_file
    - write_file
    - patch
    - search_files
    - terminal
    - skills
    - web
    - vision
    - browser
  disabled_toolsets:                    # explicit defense in depth
    - cronjob
    - delegation
    - send_message
    - memory
    - todo
  reasoning_effort: low                 # cheaper — this is a sidekick
  clarify_timeout: 120
  task_completion_guidance: true
approvals:
  mode: manual                           # every write / terminal = user approves
  timeout: 120
  cron_mode: deny
  destructive_slash_confirm: true

telegram:
  bot_token: <from @BotFather>
  reactions: false
  channel_prompts: {}
  allowed_chats: '<chat_id>,<chat_id_2>'   # restrictive whitelist
```

**Independent Venice key is critical.** If the sub-agent shares the
default profile's `VENICE_INFERENCE_KEY`, both profiles' spend pool
together against the same DIEM cap. Give it a **dedicated key** with
its own budget.

## config.yaml shape (read-only variant for outside users)

Same as above but **omit** `write_file`, `patch`, `terminal`,
`browser`, `skills`. Keep only:

```yaml
agent:
  toolsets:
    - read_file
    - search_files   # search the profile's own skills dir
    - web
    - vision
  disabled_toolsets:
    - write_file
    - patch
    - terminal
    - skills         # DISABLED — outsiders can't add skills to your profile
    - cronjob
    - delegation
    - send_message
    - memory
```

This variant is correct when the sub-agent is being given to outside
users. They can ask *what* skills the profile has but cannot add
their own and cannot run shell.

## SOUL.md patterns

The SOUL.md is **read every turn** by the sub-agent. Three sections
must always be present regardless of the specific role:

1. **Who you are** — one paragraph that anchors the persona.
2. **Boundary (HARD limits)** — explicit table of what the sub-agent
   refuses. Always include:
   - Cannot read `~/.hermes/profiles/default` or `~/.hermes/profiles/<other>`.
   - Cannot read `~/.hermes/memories/USER.md`, `state.db`, the
     default-profile skills (off-limits for execution).
   - Cannot read `~/.paperclip/`, `~/.openclaw/`, `~/.config/himalaya/`.
   - Cannot message the default-profile Telegram (chat_id
     `6808691714` if that's the user's main DM — confirm first).
   - Always refuses `sudo`, `shutdown`, OS-destructive regardless of
     the asker.
3. **Style** — one short paragraph on tone. Default: warm, plain,
   short.

Without these three sections, a teachable sub-agent will eventually
be talked into doing the wrong thing. They are not optional.

## Cross-talk rules (mandatory)

- Cannot spawn into the default profile. `delegation` off.
- Cannot schedule jobs that affect the main cron. `cronjob` off.
- Cannot write a memory entry that gets recalled by the default
  profile's recall. `memory` off.
- Cannot DM the default profile's main chat. `send_message` off.

These are *policy + toolsets*, not OS-level sandboxing. For a real
jail, run the sub-agent inside a Docker/Ubuntu container with seccomp
and a non-root user. Tell the user this when they ask for "no
access to anything else" — the current implementation is policy-
enforced, not kernel-enforced.

## Bootstrap script

```bash
mkdir -p ~/.hermes/profiles/<name>/{skills,plugins,cron,memories}
# write config.yaml + SOUL.md + README.md manually (skill recommends
# using the templates in `templates/` below)
```

A reusable bootstrap with defaults baked in lives at
`scripts/bootstrap_profile.py` in this skill. It creates the
directory tree, copies config.yaml + SOUL.md + README.md from
`templates/`, and prompts for the three placeholders (`api_key`,
`bot_token`, `allowed_chats`).

## Launching the profile

A profile by itself does nothing — it has to be activated via
`hermes -p <name>` so a separate Hermes process binds the bot token
to the daemon. The default profile keeps running normally in parallel.

```bash
# Daemon form (long-running; for the bot to stay alive 24/7)
hermes -p <name> gateway run

# Interactive REPL
hermes -p <name>

# One-shot (for cron / scripted)
hermes -p <name> -c "..."
```

Two Hermes processes = two bot tokens = two Telegrams. They never
see each other's traffic. That is the entire mechanism.

## Verification

After the daemon starts, run all three from inside the profile:

```bash
hermes -p <name> config show   # confirms config loaded correctly
hermes -p <name> skills list   # should be empty at first
hermes -p <name> tools         # toolset whitelist matches SOUL.md
```

Then from Telegram, an explicit test the boundary: send the bot a
message asking it to read `~/.hermes/memories/USER.md`. It should
refuse politely per SOUL.md. If it doesn't, the boundary layer is
broken — do not ship.

## Cleanup

Delete a profile with `rm -rf ~/.hermes/profiles/<name>`. That
removes the profile, its config, its skills, its memories, its
README. The default profile is untouched. In Telegram, revoke the
bot via @BotFather → `/revoke`.

## Pitfalls

- **Don't put `paperclip` or `openclaw` config in the profile.**
  Those are independent workspaces with their own `.env`. Cross-
  contaminating them is data corruption waiting to happen.
- **Don't share the default profile's Venice key.** Each profile's
  spend must cap against its **own** DIEM budget; otherwise a
  runaway sub-agent session can blow the user's daily $10 cap on the
  default profile or vice versa.
- **Don't use the default profile's allowed_chats pattern.** The
  default profile's bot is bound to the user's main DM. The
  sub-agent's `allowed_chats` is a new whitelist of **different**
  chat IDs. If you accidentally paste the default chat_id into the
  sub-agent's whitelist, the sub-agent can read or write into your
  main DM, which is the **opposite** of isolation.
- **SOUL.md is read every turn, but it's not a kernel jail.** A
  clever user may try to talk past the section the LLM enforces.
  For real isolation (HIPAA / financial / hostile users), use Docker
  + seccomp + a non-root user, and restrict what's mounted. Treat
  SOUL.md as defense in depth, not the primary fence.
- **Don't enable `cronjob` or `delegation` "for convenience".** Once
  enabled, the sub-agent has a back door into the default profile's
  ecosystem. If you really need scheduled work in the sub-agent, do
  it via a system-level launchd / cron that calls `hermes -p <name>
  -c "..."` with a tightly scoped prompt.

## Files

- `scripts/bootstrap_profile.py` — scaffolds `~/.hermes/profiles/<name>/`
  with all four files copied from templates
- `templates/config.teachable.yaml` — teachable variant
- `templates/config.readonly.yaml` — read-only variant (for outside users)
- `templates/SOUL.md` — base SOUL template with boundary + style
- `templates/README.md` — onboarding README for the sub-agent's users
- `references/launch-cheatsheet.md` — exact launch commands
  (daemon, REPL, one-shot) and common pitfalls during launch

## See also

- `hermes-agent` (protected) — the framework docs; you do NOT edit
  this skill. Read its CLI reference for `-p <profile>` flag.
- `paperclip` — for managed multi-agent orchestration inside a
  Paperclip company (different mechanism; doesn't replace sub-agent
  profiles).
- `openclaw` — separate personal agent platform (different mechanism;
  if the user wants Paridhi-style instead, this is the answer, not
  this skill).
- `kanban-codex-lane` — Codex CLI as isolated implementation lane.
  Same isolation pattern; this skill extends the pattern to local
  Hermes profiles.
- `editorial-carousel-orchestration` §"Architecture: 4 agents"
  — same pattern: separate companies / profiles, each owning a
  Telegram, with explicit denylists.
