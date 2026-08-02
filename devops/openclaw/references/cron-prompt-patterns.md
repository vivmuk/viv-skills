# Cron Prompt Patterns for OpenClaw

## Factual News/Research (Anti-Hallucination)

This is the **verified** pattern after fixing the hallucinated-news bug. Use this for any cron job that requires factual accuracy.

```json
{
  "name": "Daily AI News Summary",
  "schedule": { "kind": "cron", "expr": "0 18 * * *", "tz": "America/New_York" },
  "payload": {
    "kind": "agentTurn",
    "message": "You are an AI news curator. Your ONLY job is to find REAL, VERIFIED AI news from the past 24 hours and deliver it.\n\n## MANDATORY PROCESS (follow EXACTLY):\n\n### Step 1: Search for real news\nUse web_search to find today's AI news. Run MULTIPLE searches:\n- \"AI news today\" + current date\n- \"artificial intelligence announcements\" + current date\n- \"new AI model release\" + current date\n- \"AI funding round\" + current date\n- \"AI regulation policy\" + current date\n\n### Step 2: Verify each story\nFor EVERY story you want to include:\n1. Use web_fetch to visit the actual source URL and CONFIRM the article exists\n2. Check the publication date is within the last 24 hours\n3. If you cannot verify a story with web_fetch, DO NOT include it\n\n### Step 3: Write the report\nFormat each verified story as:\n- 📰 Headline (from the real article)\n- 📝 2-3 sentence summary (from verified facts only)\n- 🔗 Source URL (the real, working URL you verified)\n- ⏰ Published date (from the article)\n\n## CRITICAL RULES:\n- ONLY include stories where you successfully fetched and read the real source article\n- NEVER fabricate or guess URLs — only use URLs you actually visited\n- NEVER fabricate stories, timestamps, or details\n- If X Search returns claims without sources, treat them as UNVERIFIED and do NOT include them\n- If you find fewer than 10 real stories, that is FINE — report only what you verified\n- Quality over quantity: 3 verified real stories > 10 fabricated ones\n- Today's date is: [INJECT DATE]\n\n### Step 4: Generate Infographic\nAfter compiling all verified stories, use the venice-api-kit skill to generate an infographic image with model \"nano-banana-2\" and aspect_ratio \"16:9\".\n\n### Step 5: Save Report\nSave the full report to ~/.openclaw/workspace/ai-news-daily-report-[date].md\n\n### Step 6: Deliver\n- Send the text summary + infographic image to Telegram user 6808691714\n- Send the full report via email to vivek@live.de using the email plugin",
    "model": "venice/claude-sonnet-4-6",
    "thinking": "on",
    "timeoutSeconds": 600
  },
  "delivery": { "mode": "announce", "to": "6808691714" }
}
```

### Key design decisions:
- **Model**: `venice/claude-sonnet-4-6` with `thinking: on` — low hallucination, strong verification behavior
- **NOT `venice/grok-4-20-beta`** — this model fabricates plausible stories from X Search trends
- **NOT Venice X Search alone** — returns unverified social media that models embellish
- **web_search + web_fetch** — search finds candidates, fetch verifies they're real
- **600s timeout** — verification takes time; 420s was too short
- **Date injection** — the model needs to know what "past 24 hours" means

## What NOT To Do (Old Broken Pattern)

The original prompt told the agent to use "Venice X Search capability (enable_x_search: true)" and trusted the model to find and verify stories. Result: completely fabricated news with fake URLs, wrong dates, and hallucinated announcements.

Never use X Search as a sole source for factual claims in cron prompts.