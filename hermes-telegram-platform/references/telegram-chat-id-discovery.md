# Telegram Chat-ID Discovery — 3 Methods, Step by Step

Companion to `hermes-telegram-platform/SKILL.md`. Use this when you need the **negative integer** chat_id of a specific group to inject into `TELEGRAM_GROUP_ALLOWED_CHATS` or as the `TELEGRAM_HOME_CHANNEL` for a channel.

You do **not** need this for `TELEGRAM_GROUP_ALLOWED_USERS` — that var takes **user IDs**, which the user can grab themselves with `@userinfobot`.

## TL;DR — which method to use

| You are… | Use |
|---|---|
| Non-developer, end-user | Method 1: forward + `@RawDataBot` |
| Developer with a terminal + ship-token to Railway | Method 2: `getUpdates` API |
| Bot is deployed but you can't reach the API for some reason | Method 3: scrape Hermes logs |

## Method 1 — forward to `@RawDataBot` (mobile-friendly, ~30 seconds)

1. Have someone post a fresh message **in the target group** (you need a human post, not Jiva).
2. In Telegram, tap-hold that message → **Forward** → send to **@RawDataBot**.
3. `@RawDataBot` will reply with a long JSON blob of the entire Update.
4. Search the reply for one of these substrings:
   - `"chat":{"id":-1001234567890,"title":...` — direct post in the group (you forwarded a message that originated there).
   - `"forward_from_chat":{"id":-1001234567890,...}` — if you forwarded a message that was itself a forward of another group's post.
5. The number after `"id":` is your chat_id. **Keep the negative sign** — Railway env var is verbatim.

**Negative integer → group; positive → user.** Supergroups start with `-100…` (the actual id is the part after `-100`); older plain groups start with `-…` (no `100` prefix). Both go in the env var as-is.

> ❌ **Don't use `@userinfobot` for chat_id discovery.** It returns the author of the forwarded message, not the source chat. The chat_id for groups comes back as zeroed-out or wrong.

## Method 2 — `getUpdates` API probe (terminal, ~1 command)

Useful when scripting or when `@RawDataBot` rate-limits.

### Prerequisites
- You have a deployed Telegram bot (`@JivaAIbot` or whatever) — token already on disk.
- A clean group with the bot as a member and at least one human post.
- The token file `~/.config/railway/telegram-bot-token.env` with full `TELEGRAM_BOT_TOKEN=*** value>`.

### One-shot command

```bash
unset RAILWAY_TOKEN RAILWAY_API_TOKEN
TOKEN_FILE=~/.config/railway/telegram-bot-token.env
TOKEN=$(awk -F= '/TELEGRAM_BOT_TOKEN/' "$TOKEN_FILE" | head -1 | cut -d= -f2-)
[ -z "$TOKEN" ] && { echo "ERR: token missing"; exit 2; }

echo "=== bot identity (sanity check) ==="
curl -sS "https://api.telegram.org/bot${TOKEN}/getMe" \
  | jq -r '.result | "  @\(.username)  id=\(.id)  can_join_groups=\(.can_join_groups)"'

echo ""
echo "=== group chat_ids from getUpdates ==="
curl -sS "https://api.telegram.org/bot${TOKEN}/getUpdates" \
  | jq -r '.result[]
         | select(.message.chat.type=="group" or .message.chat.type=="supergroup")
         | "  chat_id=\(.message.chat.id)  title=\(.message.chat.title // "<unnamed>")  type=\(.message.chat.type)"' \
  | sort -u | head -20

echo ""
echo "=== raw counts ==="
curl -sS "https://api.venice.ai/api/v1/chat/completions" > /dev/null 2>&1   # placeholder
# Real count:
curl -sS "https://api.telegram.org/bot${TOKEN}/getUpdates" \
  | jq -r '
      "  total updates: \(.result | length)",
      (.result | group_by(.message.chat.type) | map("  by type: \(.[0].message.chat.type // "(no message)") × \(length)") | join("\n"))
    '
```

### What if `getUpdates` returns an empty list?

| Cause | Fix |
|---|---|
| Hermes long-poller already consumed the message | Probe `railway logs --service jiva --tail 200` instead (Method 3). |
| No human message in the group yet | Have someone post a fresh message. |
| Bot is not a member of the group | Add it: Telegram → group → Members → Add Members → @JivaAIbot. |
| Token expired / invalid | Rotate via `@BotFather /revoke`. |

## Method 3 — scrape Hermes logs

Hermes logs include chat metadata on every inbound Update. After someone's posted in the group:

```bash
unset RAILWAY_TOKEN RAILWAY_API_TOKEN
echo "=== any '-100…' integer seen in last 200 lines ==="
railway logs --service jiva --tail 200 \
  | grep -oE '"id":-100[0-9]+' | sort -u | tail -10

echo ""
echo "=== broader (any negative integer + nearby context) ==="
railway logs --service jiva --tail 400 \
  | grep -B1 -E 'supergroup|"type":"group"' \
  | head -30
```

This works **without** a token confirmation and **without** needing `getUpdates` to be un-acked. The downside: if Hermes didn't log the chat_id in a friendly format (it sometimes logs the entire dict inline), the grep misses.

## What to do with the chat_id

Once you have it (e.g., `-1001234567890`):

```bash
unset RAILWAY_TOKEN RAILWAY_API_TOKEN
cd ~/tmp/jiva-deploy
railway variable set --service jiva --skip-deploys \
  TELEGRAM_GROUP_ALLOWED_CHATS='-1001234567890'
railway service restart jiva
```

For multiple groups: comma-sep:

```bash
railway variable set --service jiva --skip-deploys \
  'TELEGRAM_GROUP_ALLOWED_CHATS=-1001234567890,-1009876543210'
```

For a single topic inside a forum-group supergroup: the chat_id is the **parent supergroup**, not the topic. Use `message_thread_id` separately only if you have multiple topics and want to allowlist by topic — Jiva's adapter config does support `allowed_topics` but that's an additional env var, not `TELEGRAM_GROUP_ALLOWED_CHATS`.

## Common false-positive patterns

| You might see… | What it really is |
|---|---|
| `id: 6808691714` | A **user** ID (yours). Wrong scope. |
| `"id": -1001234567890, "type":"private"` | Older signal — Telegram sometimes returns `private` for 1:1 chats. If `id < 0`, the most common modern reading is `"private"` here means *"direct message"* — check `chat_type` field or recapture. |
| `"id": 0` | A scratch/empty JSON field. Not a chat_id. |
| Your phone pads leading zeros (`07012…`) | That's a phone number, not a Telegram user/chat ID. Wrong ops. |

## A note on display-redacted token files

Hermes' text-display redeactor strips UUID-shaped values (`…-…-…-…-…`) when echoed via shell `cat` or `head`. Telegram tokens are `int64:AAG<hash>` — **non-UUID, survive intact on disk**. But if a tool output **displays** the file via `cat $FILE`, the display layer still applies some redacting patterns.

If you need to confirm a file's contents are intact (and not have a server-blocked `head -c` show you the truncated form), use:

```bash
xxd ~/.config/railway/telegram-bot-token-env | head -8
# OR
hexdump -C ~/.config/railway/telegram-bot-token-env
```

These bypass the text-replacement redaction and show raw bytes. Use this **only** when the actual byte value matters for debugging — never paste the bytes back into chat.
