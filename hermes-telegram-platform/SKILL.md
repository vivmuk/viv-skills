---
name: hermes-telegram-platform
version: 0.1.0
description: Authorize, share, and discover Telegram chat IDs in a Hermes-deployed Telegram platform. Covers the six auth env vars (TELEGRAM_ALLOWED_USERS, TELEGRAM_GROUP_ALLOWED_USERS, TELEGRAM_GROUP_ALLOWED_CHATS, plus wildcards), three sharing strategies, BotFather /setprivacy interaction, three chat-ID diagnostic paths, and the reasoning-model silent-bot case study from the Jiva deployment (2026-07-14).
tags: [hermes, telegram, sharing, auth, deploy, platform]
triggers:
  - share Jiva with others
  - add a friend to the bot
  - get the group chat_id
  - find a Telegram chat ID
  - telegram bot looks dead
  - only I can talk to my bot
  - reason on a Telegram agent
  - bot stopped responding
  - who is in the allowlist
  - TELEGRAM_GROUP_ALLOWED_USERS / TELEGRAM_GROUP_ALLOWED_CHATS
---

# Hermes Telegram Platform — Auth, Sharing, Chat-ID Discovery

A Hermes-deployed Telegram bot sits behind three stacked layers. Each can independently block or allow a message — diagnose all three when something looks wrong:

1. **Telegram network** — `@BotFather /setprivacy` (default: Enable → bot only sees `/commands`, `@`-mentions, replies to its own messages)
2. **Hermes adapter** — six `TELEGRAM_*` / `GATEWAY_*` auth env vars + the adapter-level `allow_from` config (the latter takes precedence over env vars)
3. **Agent / transport** — model behavior on reasoning-model LLMs (the most common "silent bot" cause)

## When to load this skill

- User asks how to share their deployed Hermes Telegram bot
- Reported "the bot is dead" / "stopped responding" / "only I can talk to it"
- You need to grant multi-user or group access on a freshly deployed agent
- You need a Telegram chat ID for env-var injection

Do **not** load this for: Discord, Slack, Signal (other platforms have separate skills in `autonomous-ai-agents/`).

## Quick decision tree

```
User wants multi-user / multi-group sharing?
├─ Just me + 1 friend anywhere → TELEGRAM_GROUP_ALLOWED_USERS='<me>,<friend>'
├─ Small known group of friends → TELEGRAM_GROUP_ALLOWED_USERS='<id1>,<id2>,<id3>'
├─ Specific Telegram group, anyone in it can drive → TELEGRAM_GROUP_ALLOWED_CHATS='<chat_id>'
├─ Open bot for anyone/anywhere → TELEGRAM_ALLOW_ALL_USERS=true + GATEWAY_ALLOW_ALL_USERS=true
└─ DM-only allowlist → TELEGRAM_ALLOWED_USERS='<id1>,<id2>'

After every `railway variable set`, run `railway service restart jiva`.
```

## The 6 auth env vars (and exactly what each gates)

Source: `plugins/platforms/telegram/adapter.py` lines 896–906 + 908–974.

| Env var | Scope | Effect on a user message |
|---|---|---|
| `TELEGRAM_ALLOWED_USERS` | DM, per-author | Comma-sep user_ids that may **DM** the bot |
| `TELEGRAM_GROUP_ALLOWED_USERS` | Group, per-author (chat-agnostic) | Comma-sep user_ids allowed to drive the bot **in any group** it's a member of |
| `TELEGRAM_GROUP_ALLOWED_CHATS` | Group, per-chat (user-agnostic) | Comma-sep negative group chat_ids — **anyone in those chats can drive it** |
| `TELEGRAM_ALLOW_ALL_USERS` | Wildcard (DM + Group) | `true` = anyone |
| `GATEWAY_ALLOWED_USERS` | Cross-platform per-author fallback | Hermes-gateway auth layer |
| `GATEWAY_ALLOW_ALL_USERS` | Cross-platform wildcard | Same scope, higher precedence |

### Precedence (from the source code)

1. Adapter-level `allow_from` config (in `cli-config.yaml` plugin block) → **sole authority** — env vars are ignored when this is set (lines 928–932).
2. Adapter-level callback override (test-only).
3. Runner `_is_user_authorized()` at the gateway runner layer.
4. Env-var fallback (`TELEGRAM_ALLOWED_USERS` at line 970). If empty, check `GATEWAY_ALLOW_ALL_USERS` for `true`/`1`/`yes` — **fail-closed otherwise** (line 826, comment "fixes #24457"):
   > The runner auth path in _is_user_authorized() handles GATEWAY_ALLOW_ALL_USERS; this fallback must not silently allow everyone.

> **Critical trap:** `TELEGRAM_ALLOWED_USERS` does **not** extend to groups. The 3 scopes are independent. To grant the same user access in DMs *and* groups, list them in **both** `TELEGRAM_ALLOWED_USERS` and `TELEGRAM_GROUP_ALLOWED_USERS`.

## Sharing strategy — exact commands

### A. Per-user across all groups (small known groups)

```bash
unset RAILWAY_TOKEN RAILWAY_API_TOKEN
cd ~/tmp/jiva-deploy
railway variable set --service jiva --skip-deploys \
  'TELEGRAM_GROUP_ALLOWED_USERS=6808691714, 1234567890, 987654321'
railway service restart jiva
```

### B. Per-chat (anyone in listed groups)

```bash
railway variable set --service jiva --skip-deploys \
  'TELEGRAM_GROUP_ALLOWED_CHATS=-1001234567890, -1009876543210'
railway service restart jiva
```

Group chat IDs are negative integers; supergroups start with `-100…`. **Keep the negative sign** — try without and you'll be off-by-one-deep.

### C. Open bot (universal wildcard)

```bash
railway variable set --service jiva --skip-deploys 'TELEGRAM_ALLOW_ALL_USERS=true'
railway variable set --service jiva --skip-deploys 'GATEWAY_ALLOW_ALL_USERS=true'
railway service restart jiva
```

After applying env-only changes you **must** restart — Hermes doesn't hot-reload env.

## Layer 1 — `@BotFather /setprivacy` interaction

Even with Path B for chat-IDs, the **Telegram network** filters what reaches the bot before any of the above runs. In Telegram:

1. DM `@BotFather` → `/setprivacy` → pick the bot → **Disable** to make the bot see every group message.
2. With Enable (default new-bot setting), the bot sees only:
   - `/commands` invoked by anyone in the group
   - messages that `@<bot>`-mention it
   - replies to messages the bot itself sent

If a friend says "the bot is dead in the group", check both: (1) adapter allowlist (`TELEGRAM_GROUP_ALLOWED_USERS`/`CHATS` set correctly), (2) network privacy mode.

Verify platform preconditions with `getMe`:

```bash
TOKEN=$(awk -F= '/TELEGRAM_BOT_TOKEN/' ~/.config/railway/telegram-bot-token.env | head -1 | cut -d= -f2)
curl -s "https://api.telegram.org/bot${TOKEN}/getMe" \
  | jq -r '.result | "  bot:  @\(.username)  id=\(.id)  can_join_groups=\(.can_join_groups)"'
```

If `can_join_groups=False`, the bot cannot be added to any group regardless of Hermes setting.

## Layer 3 — reasoning-model silent-bot gotcha

**Case study, 2026-07-14 — Jiva on Railway**:

User reported `@JivaAIbot` stopped responding. Diagnosed:

```bash
# Direct probe — what Hermes sees
curl -s -X POST https://api.venice.ai/api/v1/chat/completions \
  -H "Authorization: Bearer ${VENICE_KEY}" -H 'Content-Type: application/json' \
  -d '{
    "model":"minimax-m3-preview",
    "messages":[{"role":"user","content":"ping"}],
    "max_tokens":16000
  }'
# → 200 OK, choices[0].message.content = ""  (empty)
# → choices[0].message.reasoning_content = "The user wants a ping reply..."
# → finish_reason: "length"
```

`minimax-m3-preview` (and other reasoning/preview models — `gemma-4-31b-it`, `gemini-3-5-*`, etc.) burn the entire output budget on a "thinking" pass before issuing any visible reply. With a normal max_tokens budget, only `reasoning_content` is filled and `content` is empty. Hermes' intake sees no text → bot appears silently dead even though the call returned HTTP 200.

**Fix:**

```diff
 # ~/tmp/jiva-deploy/hermes/cli-config.yaml
       context_length: 500000
       max_output_tokens: 120000
+      venice_parameters:
+        disable_thinking: true
+        strip_thinking_response: true
```

Then `cd ~/tmp/jiva-deploy && railway up --detach --service jiva --yes` to rebuild with the new image. Verify with `/info` or a fresh DM — the bot now writes its visible reply directly to `content` with `finish_reason="stop"`.

**Diagnostic proxy pattern (works for any reasoning model before rebuild):**

```bash
# Same call but with disable_thinking → it'll return content="pong" in ~2s
curl -s -X POST https://api.venice.ai/api/v1/chat/completions \
  -H "Authorization: Bearer ${VENICE_KEY}" -H 'Content-Type: application/json' \
  -d '{
    "model":"minimax-m3-preview",
    "messages":[{"role":"user","content":"ping"}],
    "max_tokens":16000,
    "venice_parameters": {"disable_thinking": true, "strip_thinking_response": true}
  }'
```

> Lesson: never trust `finish_reason: "length"` + `content: ""` as a token-budget issue. On reasoning/preview models, it's almost always the missing `disable_thinking` flag. See `mlops/venice-api` for the full reasoning-model pitfall catalog (don't go above `max_tokens=16384` even with the fix; 32K stalls 4+ min on slow models).

## Chat-ID discovery — 3 paths

| # | Method | When to use |
|---|---|---|
| **1. `@RawDataBot` redirect** | Mobile-friendly. Tap-hold a **human post** in the target group → Forward → send to `@RawDataBot`. The JSON reply contains `forward_from_chat.id` (negative integer for groups). | Non-developers, one-shot discovery. |
| **2. `getUpdates` API probe** | Need ≥1 human post in the group after bot joined. Pull token silently from `~/.config/railway/telegram-bot-token.env` — **AWS `int64:AAG<hash>` shape** is non-UUID; survives `write_file` and bash. jq filters `select(.message.chat.type=="group" or .message.chat.type=="supergroup")`. | Developers / when scripting. |
| **3. Hermes logs after a recent message** | `railway logs --service jiva --tail 200 \| grep -iE 'chat_id\|supergroup' \| grep -oE '"id":-?[0-9]+' \| sort -u`. | When getUpdates races with Hermes long-poll. |

❌ Do **not** use `@userinfobot` for chat IDs — it returns the **author** of the forwarded message (which is your own user ID when you forward your own post), not the **source chat**. It's a known misstep.

### Working `getUpdates` shell snippet (reads token from disk, never echoes)

```bash
unset RAILWAY_TOKEN RAILWAY_API_TOKEN
TOKEN_FILE=~/.config/railway/telegram-bot-token.env
TOKEN=$(awk -F= '/TELEGRAM_BOT_TOKEN/' "$TOKEN_FILE" | head -1 | cut -d= -f2-)
curl -sS "https://api.telegram.org/bot${TOKEN}/getUpdates" \
  | jq -r '.result[]
         | select(.message.chat.type=="group" or .message.chat.type=="supergroup")
         | "  chat_id=\(.message.chat.id)  title=\(.message.chat.title // "<unnamed>")" | sort -u | head
```

> Display note: `head -c 80` on Telegram `.env` files may be **redacted by the host's UUID-secret filter at display time**. To read raw bytes when debugging ("is the file really intact?"), use `xxd ~/.config/railway/telegram-bot-token-env` — its hex output is not subject to the same display redaction. Telegram tokens are `int64:AAG…` shape (non-UUID) so this redacting rule doesn't apply at the byte-level — it's purely a display artifact.

## Pitfalls (the cheap fixes that took me minutes to find)

1. **Group privacy defaults to Enable** (most common "bot is dead in my group" report). Fix: `@BotFather /setprivacy Disable`.
2. **`@userinfobot` returns the *forwarded-from author*, not the *chat*. The right bot to extract a chat_id is `@RawDataBot`.**
3. **`TELEGRAM_ALLOWED_USERS` does not extend to groups.** Each of the 6 scopes is independent — list in both DM and Group scopes if needed.
4. **Reasoning-model silent-bot fails silently.** Add `disable_thinking: true, strip_thinking_response: true` to your `model.venice_parameters:` block before any meaningful reasoning/preview model (minimax-m3-preview, gemma-*-it, gemini-*-preview).
5. **Env-only edits don't hot-reload.** Always `railway service restart jiva` after `railway variable set`. (Full image changes need `railway up`.)
6. **`getUpdates` races with Hermes long-poll.** After Hermes consumes the message, `getUpdates` returns `[]`. Probe Hermes logs as fallback.
7. **`allowed_chats` in `cli-config.yaml` overrides every env var.** When both exist at the same scope, the config wins. Pick one source of truth per scope.
8. **Adapter-level `allow_from` makes env vars a no-op.** When you set `telegram.allow_from: [<id1>, <id2>]` in the config, the 6 env vars are ignored — you must edit the config to grant new users.

## Post-change verification

```bash
# 1. Confirm env is what you set
railway variable get --service jiva TELEGRAM_GROUP_ALLOWED_USERS
railway variable get --service jiva TELEGRAM_GROUP_ALLOWED_CHATS

# 2. Confirm fresh container restarted
railway logs --service jiva --tail 50 | grep -E 'Starting Container|HERMES_HOME'

# 3. End-to-end: friend DMs or @-mentions the bot and you see the response in their DM thread
#    AND in logs:
railway logs --service jiva --tail 80 | grep -iE 'inbound|@JivaAIbot|/start'
```

If a fresh message still doesn't get a reply, walk the decision tree top-to-bottom — every layer must be open.

## See also

- `mlops/venice-api` — full reasoning-model pitfall catalog + `disable_thinking` patterns
- `devops/self-hosted-agent-deployment` — Railway provisioning + volume attach (where this Telegram channel sits)
- `autonomous-ai-agents/hermes-agent` (bundled) — base Hermes config, prompt engineering
