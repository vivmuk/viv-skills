# Launch cheatsheet — Hermes sub-agent profile

Activating a sub-agent profile requires a **separate Hermes process**
so the second Telegram bot doesn't collide with the default profile's.

## Daily-life commands

```bash
# Daemon (long-running; the bot stays alive 24/7)
hermes -p <NAME> gateway run

# Interactive REPL
hermes -p <NAME>

# One-shot prompt (cron, scripted)
hermes -p <NAME> -c "your one-shot prompt here"

# Resume a specific session
hermes -p <NAME> --resume <session_id>
hermes -p <NAME> -c "your prompt"   # starts a new session
```

**Do not** run the default profile's daemon and the sub-agent profile's
daemon in the same shell process unless you've verified `HERMES_HOME`
and the duplicate-process check passes. They DO share the same home
directory (config, sessions database, state), which can cause the
second process to bind to a different port automatically.

## Verifying the profile is active

If you're not sure which profile a `hermes` invocation is using,
the prompt prefix changes (the symbol shown beside the input box in
the TUI). Otherwise:

```bash
hermes -p <NAME> config show            # load the resolved config
hermes -p <NAME> profile active         # prints active profile name
```

Note: `profile active` may not be a built-in command. Use `config
show` for verification.

## Launch failure modes and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `hermes` not found | PATH missing the Hermes CLI bin | Add `~/.hermes/hermes-agent/bin` (or wherever `setup.py` puts the binary) to PATH |
| `Profile '<NAME>' not found` | typo in profile name or profile dir missing | `ls ~/.hermes/profiles/` — confirm name |
| Telegram bot token invalid | placeholder REPLACE_ME still in config.yaml | Edit config.yaml, swap real token, restart |
| Telegram bot never responds | Paperclip daemon or another Hermes instance bound to same bot token | Stop other instance; double-check `allowed_chats` |
| Tool call refused with "not authorized" | a tool in your prompt is in `disabled_toolsets` | Edit config.yaml, widen toolset only if the safety story still works |

## Sizing rules of thumb

| Profile purpose | `context_length` | `max_output_tokens` | `max_turns` | `reasoning_effort` |
|---|---|---|---|---|
| Read-only knowledge assistant | 64K-128K | 4K-8K | 15-25 | low |
| Teachable sidekick | 128K-256K | 8K-16K | 25-40 | low |
| Active operator (long runs) | 256K-500K | 16K-32K | 50-90 | medium |

`reasoning_effort: low` keeps responses cheap. Bump it to medium
for tasks that need careful multi-step planning.

## Spend caps

Each profile should have its own Venice key with its own DIEM cap.
Daily spend for a typical sub-agent is well under $1/day; setting a
DIEM cap of $5 per profile prevents a runaway session from blowing
your main $10 cap.

Track spend in `/tmp/aipharmaxchange_spend/spend_{date}.json` (or a
profile-dedicated ledger if you want per-profile accounting).
