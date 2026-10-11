# <NAME>

A Hermes sub-agent with its own Telegram, shareable with other people.
Operates inside `~/.hermes/profiles/<NAME>/` only — no access to the
default profile, to Paperclip, or to the rest of the system.

## Quick start

### 1. Create a Telegram bot

In your Telegram client, message **@BotFather** and run `/newbot`.
Give it a name + username. BotFather replies with an HTTP API token.

### 2. Find the chat ID(s) you want this bot to speak in

Add the bot to the chat/group. Send a message from inside the chat
(which gets received by the bot via webhook / long-polling). Visit:

```
https://api.telegram.org/bot<TOKEN>/getUpdates
```

The `message.chat.id` field is the chat ID. Group chat IDs are
negative integers; DMs are positive integers.

### 3. Edit `config.yaml`

Replace three placeholders:

```yaml
model.api_key:            VENICE_INFERENCE_KEY_<...>      # independent Venice key
telegram.bot_token:       <bot_token_from_botfather>
telegram.allowed_chats:   '<id1>,<id2>,<id3>'
```

**Each profile gets its own Venice key** so DIEM caps don't pool
with the default profile. Use the Paperclip `instances/default/.env`
mechanism or just paste a different `VENICE_INFERENCE_KEY=...`
into a new `~/.hermes/profiles/<NAME>/.env`.

### 4. Launch as a SEPARATE Hermes process

The default `~/.hermes/config.yaml` owns Vivek's DM. To give this
profile its own bot, run an entirely separate `hermes` invocation:

```bash
# Daemon form (long-running; for the bot to stay alive 24/7)
hermes -p <NAME> gateway run

# Interactive REPL
hermes -p <NAME>

# One-shot (for cron / scripted)
hermes -p <NAME> -c "draft a skill that..."
```

While that daemon runs, the default-profile gateway (already on)
stays operational. The two never see each other's traffic.

### 5. Verify the boundary

```bash
hermes -p <NAME> config show            # confirms overrides loaded
hermes -p <NAME> skills list            # empty initially
hermes -p <NAME> tools                  # toolset matches the SOUL
```

Send a Telegram message to your bot asking it to read
`~/.hermes/memories/USER.md`. It should refuse per SOUL.md. If it
doesn't, the boundary layer is broken.

### 6. Teach your first skill (teachable variant only)

From Telegram:

> "next time anyone asks me about X, do Y"

The bot drafts a `SKILL.md`, calls
`skill_manage(action='create', ...)`, and persists it under
`~/.hermes/profiles/<NAME>/skills/<slug>/SKILL.md`. Next time the
trigger phrase appears, the skill runs.

(readonly variant: skip this section — outsiders cannot teach.)

## What it can't do (defense-in-depth)

| Block | Why |
|---|---|
| `~/.hermes/profiles/` (other profiles) | SOUL.md hard ref |
| `~/.hermes/memories/`, `state.db`, global skills | SOUL.md hard ref |
| `~/.paperclip/`, `~/.config/himalaya/` | SOUL.md hard ref |
| `delegation`, `cronjob`, `memory`, `send_message` to default chat | `agent.disabled_toolsets` + SOUL.md |
| `sudo`, `shutdown`, OS-destructive | SOUL.md + `approvals.mode=manual` |

`make**` sure the process running this profile is the **only**
Hermes process that can register its bot. Another process running with
the default profile would still bind Vivek's DM bot and not collide.

## Files

```
profiles/<NAME>/
├── config.yaml        # profile config (edit me)
├── SOUL.md            # persona + boundary rules (read every turn)
├── README.md          # this file
├── skills/            # empty; teachable (teachable variant only)
├── plugins/           # empty
├── cron/              # empty; not writable from inside this profile
└── memories/          # empty; not writable from inside this profile
```

## Cleanup

Delete the profile with:

```bash
rm -rf ~/.hermes/profiles/<NAME>
```

That removes the profile, its config, its skills, its memories, and
its README. The default profile is untouched. In Telegram, revoke
the bot via @BotFather → `/revoke`.
