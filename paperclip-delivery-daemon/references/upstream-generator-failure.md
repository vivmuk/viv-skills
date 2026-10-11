# Upstream generator failure — when the daily cron never reaches the wrapper

The daemon and the wrapper only see issues that get PATCH'd to `done`. When
the upstream content generator (`daily_post_generator.py`, `eod_report.py`,
`weekly_newsletter_generator.py`, etc.) aborts BEFORE producing output, the
wrapper never runs, no issue is created, no email goes out. From the
recipient's box the effect is identical to "the daemon is broken" — but
the diagnosis is in a completely different place.

This file is the runbook for a cron operator who shows up, sees the daily
email is missing, and needs to figure out *which* layer broke.

## Signal triage — where did the run die?

Read the cron log top-down. Look for the first `[N/7]` (or whatever N
the generator runs) that has no `OK` line after it. That N is the
failure point:

| Pipeline step | Generator code (`daily_post_generator.py`) | What it does                              |
| ---           | ---                                         | ---                                       |
| 0/7           | `model_pricing.check_budget_and_alert`      | Daily Diem cap pre-flight                 |
| 1/7           | `model_pricing.refresh_pricing`             | Pull Venice text/image price lists        |
| 2/7           | `news_harvester.harvest`                    | Venice `augment/search` + `augment/scrape`|
| 3/7           | `content_factory.make_variants`             | Render LinkedIn/Newsletter variants       |
| 4/7           | `ab_judge.judge`                            | Pick a winner                             |
| 5/7           | `generate_assets_for_winner`                | flux-2-pro images                         |

The two failure modes that blow up *before any deliverable exists* are:

- **Budget pre-flight ABORT** — cap reached. `$0` spent after the abort.
  See "Budget pre-flight abort" below.
- **Harvest-step abort** — `news_harvester.harvest` returns empty (raised
  as `RuntimeError("news_harvester returned no items")` near line 297 of
  `daily_post_generator.py`). `$0` spent after the abort because no
  inference calls were attempted. See "Harvest 401" below.

Anything past step 2/7 (variants, judge, images) typically incurs *some*
spend even on failure, because tokens have already been burned.

## Budget pre-flight abort

`python3 -c "import model_pricing; s=model_pricing.check_budget_and_alert(); print(s['spent_usd'], s['cap_usd'])"`

If `spent >= cap` and the cron is configured to abort: **stop.** No retry
today. Telegram alert at 100% of the cap was already fired by the
pre-flight check (so the recipient knows). Do NOT silently retry — the
budget resets at 00:00 UTC.

If `spent < cap` but ≥ 50/75/90%: the preview alert already went out. The
generator itself decides whether to keep going. The pre-flight does not
auto-abort until `spent == cap`.

## Harvest 401 — the most common upstream failure

The harvester uses Venice's hosted search/scrape endpoints
(`/api/v1/augment/search`, `/api/v1/augment/scrape`). Both are billed
separately from the inference API and both can return 401 even when
inference works fine. Two keys live in `~/.paperclip/instances/default/.env`:

- `VENICE_API_KEY`        — used by the search/scrape calls (harvester)
- `VENICE_INFERENCE_KEY`  — used by `llama-3.1-8b-instruct` etc. (generator)

Key well-formedness is *not* a valid auth check — both are 63 chars and
look identical. **Probe the upstream API directly with `curl`** to confirm
401 is real and not a mislabeled-env-var mistake:

```bash
ENV=/Users/vivgatesai/.paperclip/instances/default/.env
probe() {
  local label="$1" key="$2"
  printf '=== %s ===\n' "$label"
  curl -sS -X POST 'https://api.venice.ai/api/v1/augment/search' \
    -H "Authorization: Bearer *** \
    -H 'Content-Type: application/json' \
    --data-binary '{"query":"AI pharma","limit":1}' \
    -w '\n[http_status=%{http_code}]\n'
}
probe 'VENICE_API_KEY'       "$(grep '^VENICE_API_KEY=***       "$ENV" | cut -d= -f2-)"
probe 'VENICE_INFERENCE_KEY' "$(grep '^VENICE_INFERENCE_KEY=' "$ENV" | cut -d= -f2-)"
```

**Shell-escaping pitfall:** the auth-header value contains backticks
in many env formats and `$` in others. Wrap the `-H` argument in
**double quotes** and put the literal `*** on the right of the
right side, but encapsulate the value in your command with shell quoting
that survives backtick expansion (e.g. build the value in a subshell into
a variable, then pass `-H "Authorization: Bearer $VAR"`). Backticks in
key strings can corrupt the header under subshell expansion; double-quote
the entire `-H` argument to prevent word-splitting.

**What 401 means:** the key is revoked, expired, or the account has lost
access to the `augment/*` feature. It will **not** clear by retrying.
Confirming with both keys rules out "wrong env var name" and points the
operator to the credential refresh path.

**Distinguishing 401 from 429:**

- **401** = auth. Don't retry. Don't re-probe. Open the rotate-key path.
- **429** = rate-limit. The harvester degrades to empty on its own;
  retries with backoff MAY clear it. Re-run the cron in ~15min if the
  budget allows.
- **5xx** = upstream outage. Retries DO make sense; the next cron slot
  will almost certainly succeed.

In every case, compute the actual `$` spent today:

```bash
python3 -c "import model_pricing; s=model_pricing.check_budget_and_alert(); print(f\"${s['spent_usd']:.4f} / ${s['cap_usd']:.2f}\")"
```

A harvest-step failure means **$0.00 spent** for that run because no
inference was attempted. Reporting a non-zero cost is fabrication.

## What to report to the user

When the daily cron fails *before deliverable exists*, the report goes
back to the recipient's mail channel, NOT through the wrapper (which is
downstream of the failing step). Three rules, in order:

1. **Do NOT silently retry.** The user-configured cron run is
   deterministic. Re-running on a 401 will produce the same 401 and
   burn cycle budget. If retrying is warranted, do it once, alone, with
   a comment explaining why.
2. **Do NOT fabricate output.** A failed run cannot celebrate "variant
   X won from `<source>`." That phrasing applies only to successful
   runs. For failures, report the failing step, the upstream status
   code, and the actual `$` spent today (almost always $0 for a
   harvest-step failure).
3. **Telegram alert coverage gap:** the 50/75/90% Telegram alerts are
   *budget* alerts, fired by the pre-flight check or by a successful
   mid-run cost update. A complete harvest-step abort with $0 spent
   bypasses them entirely. Explicit reporting is the only path.

A tight failure report contains:

- Pipeline step number/name where the run died
- Upstream status code (e.g. `HTTP 401 from Venice augment/search`)
- The exact `$` spent today (`$0.0000 / $10.00` for harvest-failure)
- The two-line reason + one-line fix (e.g. "rotate VENICE_API_KEY in
  `~/.paperclip/instances/default/.env`; cron will pick it up next slot")

## Reporting — what NOT to include

- Past successful runs of the same cron (irrelevant to failure diagnosis)
- The full traceback beyond the first error line
- "Will retry later" speculation (the cron controls retry, not the agent)
- Suggested alternatives that don't exist in the codebase (e.g. "we
  could use Tavily instead" — there is no Tavily path in
  `news_harvester.py`, only Venice; proposing a hypothetical fallback
  is fabrication)

## When to suggest changing the code

Almost never. The harvester raises on empty output for a reason — silent
fallbacks to `random_topic` libraries tend to produce carousel copy that
contradicts itself or cites nonexistent papers. If the operator wants a
fallback, that's a real scope change that warrants its own skill
(`spike` → design review → `plan`), not a mid-cron band-aid.

## Verification once the env is fixed

After rotating the key in the env file, re-probe with the curl recipe
above (should return HTTP 200 + a JSON `results` array). Then re-run
the cron manually:

```bash
cd /Users/vivgatesai/.paperclip/workspaces/aipharmaxchange
set -a && . /Users/vivgatesai/.paperclip/instances/default/.env && set +a
python3 -c "import model_pricing; s=model_pricing.check_budget_and_alert(); print(s)"
python3 daily_post_generator.py --no-budget-cap
```

If both succeed, the next scheduled cron slot will pick up the fix
automatically — no daemon reload, no wrapper change.

## Related

- `paperclip-delivery-daemon/SKILL.md` — when the daemon IS the cause
  (auth, attachment-name, launchd reload), this is the upstream-side
  counterpart.
- `paperclip-status-transition/SKILL.md` — when wrappers claim success
  but state.json shows reverted (a different class of "absent email"
  symptoms).
