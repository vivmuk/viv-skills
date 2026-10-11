---
name: github-pr-workflow
description: "GitHub PR lifecycle: branch, commit, open, CI, merge."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, CI/CD, Git, Automation, Merge]
    related_skills: [github-auth, github-code-review]
---

# GitHub Pull Request Workflow

Complete guide for managing the PR lifecycle. Each section shows the `gh` way first, then the `git` + `curl` fallback for machines without `gh`.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository with a GitHub remote

### Quick Auth Detection

```bash
# Determine which method to use throughout this workflow
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  # Ensure we have a token for API calls
  if [ -z "$GITHUB_TOKEN" ]; then
    if _hermes_env="${HERMES_HOME:-$HOME/.hermes}/.env"; [ -f "$_hermes_env" ] && grep -q "^GITHUB_TOKEN=" "$_hermes_env"; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$_hermes_env" | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
echo "Using: $AUTH"
```

### Extracting Owner/Repo from the Git Remote

Many `curl` commands need `owner/repo`. Extract it from the git remote:

```bash
# Works for both HTTPS and SSH remote URLs
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"
```

---

## 1. Branch Creation

This part is pure `git` — identical either way:

```bash
# Make sure you're up to date
git fetch origin
git checkout main && git pull origin main

# Create and switch to a new branch
git checkout -b feat/add-user-authentication
```

Branch naming conventions:
- `feat/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

## 2. Making Commits

Use the agent's file tools (`write_file`, `patch`) to make changes, then commit:

```bash
# Stage specific files
git add src/auth.py src/models/user.py tests/test_auth.py

# Commit with a conventional commit message
git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes
- Add unit tests for auth flow"
```

Commit message format (Conventional Commits):
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

## 3. Pushing and Creating a PR

### Push the Branch (same either way)

```bash
git push -u origin HEAD
```

### Create the PR

**With gh:**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

The response JSON includes the PR `number` — save it for later commands.

To create as a draft, add `"draft": true` to the JSON body.

## 4. Monitoring CI Status

### Check CI Status

**With gh:**

```bash
# One-shot check
gh pr checks

# Watch until all checks finish (polls every 10s)
gh pr checks --watch
```

**With git + curl:**

```bash
# Get the latest commit SHA on the current branch
SHA=$(git rev-parse HEAD)

# Query the combined status
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Overall: {data['state']}\")
for s in data.get('statuses', []):
    print(f\"  {s['context']}: {s['state']} - {s.get('description', '')}\")"

# Also check GitHub Actions check runs (separate endpoint)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/check-runs \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for cr in data.get('check_runs', []):
    print(f\"  {cr['name']}: {cr['status']} / {cr['conclusion'] or 'pending'}\")"
```

### Poll Until Complete (git + curl)

```bash
# Simple polling loop — check every 30 seconds, up to 10 minutes
SHA=$(git rev-parse HEAD)
for i in $(seq 1 20); do
  STATUS=$(curl -s \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])")
  echo "Check $i: $STATUS"
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failure" ] || [ "$STATUS" = "error" ]; then
    break
  fi
  sleep 30
done
```

## 5. Auto-Fixing CI Failures

When CI fails, diagnose and fix. This loop works with either auth method.

### Step 1: Get Failure Details

**With gh:**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

# List workflow runs on this branch
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python3 -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
    print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

# Get failed job logs (download as zip, extract, read)
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt
```

### Step 2: Fix and Push

After identifying the issue, use file tools (`patch`, `write_file`) to fix it:

```bash
git add <fixed_files>
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

### Step 3: Verify

Re-check CI status using the commands from Section 4 above.

### Auto-Fix Loop Pattern

When asked to auto-fix CI, follow this loop:

1. Check CI status → identify failures
2. Read failure logs → understand the error
3. Use `read_file` + `patch`/`write_file` → fix the code
4. `git add . && git commit -m "fix: ..." && git push`
5. Wait for CI → re-check status
6. Repeat if still failing (up to 3 attempts, then ask the user)

## 6. Merging

**With gh:**

```bash
# Squash merge + delete branch (cleanest for feature branches)
gh pr merge --squash --delete-branch

# Enable auto-merge (merges when all checks pass)
gh pr merge --auto --squash --delete-branch
```

**With git + curl:**

```bash
PR_NUMBER=<number>

# Merge the PR via API (squash)
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{
    \"merge_method\": \"squash\",
    \"commit_title\": \"feat: add user authentication (#$PR_NUMBER)\"
  }"

# Delete the remote branch after merge
BRANCH=$(git branch --show-current)
git push origin --delete $BRANCH

# Switch back to main locally
git checkout main && git pull origin main
git branch -d $BRANCH
```

Merge methods: `"merge"` (merge commit), `"squash"`, `"rebase"`

### Enable Auto-Merge (curl)

```bash
# Auto-merge requires the repo to have it enabled in settings.
# This uses the GraphQL API since REST doesn't support auto-merge.
PR_NODE_ID=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['node_id'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/graphql \
  -d "{\"query\": \"mutation { enablePullRequestAutoMerge(input: {pullRequestId: \\\"$PR_NODE_ID\\\", mergeMethod: SQUASH}) { clientMutationId } }\"}"
| Check out someone's PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |
| Enumerate review-bot comments | `gh api repos/$OWNER/$REPO/pulls/N/comments --jq '.[] | select(.user.type=="Bot")'` | `curl .../pulls/N/comments | jq '[.[] | select(.user.type=="Bot")]'` |

## 8. Triage review-bot inline comments (Codex / Gemini / Sonnet bots)

When a PR has inline comments from automated review bots (`chatgpt-codex-connector[bot]`, `gemini-code-assist[bot]`, `claude-sonnet[bot]`, etc.), a clean triage cadence is: enumerate → classify per-bucket (real bug / pre-existing / moot) → fix in-branch → re-CI. The bots leave severity tags (`P1`, `P2`), file paths, and line numbers — the output is highly structured, often more useful than a human review.

### Step 1 — enumerate PRs and comments

```bash
# List PRs (open or all states) with their number, title, author, state, and createdAt
gh pr list -R $OWNER/$REPO --state all \
  --json number,title,author,createdAt,state --limit 30

# Get all inline review comments (returns path, line, body, user, severity tag, etc.)
gh api repos/$OWNER/$REPO/pulls/$N/comments --jq '.[] | {
  comment_id: .id,
  path, line, original_line,
  author: .user.login,
  is_bot: .user.type,
  body_first: (.body | split("\n")[0])
}'

# Issue-style / general PR comments (different endpoint, same N)
gh api repos/$OWNER/$REPO/issues/$N/comments --jq '.[] | {
  author: .user.login,
  is_bot: .user.type,
  body_first: (.body | split("\n")[0])
}'
```

Inline review comments attach to a `path` + `line` (or `original_line` for out-of-date diffs) and are the most actionable — they point at specific code locations. Issue-style comments are conversation-volume only and rarely have action items.

### Step 2 — filter to review bots

Review bots almost always have `user.type == "Bot"`. The exact login names vary — common ones seen in 2026:

| Bot login | Origin | Common severity tags |
|---|---|---|
| `chatgpt-codex-connector[bot]` | OpenAI Codex via GitHub app | `P1` / `P2` / `P3` |
| `gemini-code-assist[bot]` | Google Gemini | `CRITICAL` / `HIGH` / `MEDIUM` |
| `claude-sonnet[bot]`, `claude-code[bot]` | Anthropic Claude | `BLOCKER` / `IMPORTANT` / `NIT` |
| `copilot-pull-request-reviewer[bot]` | GitHub Copilot | severity varies |

Filter for them concisely:

```bash
gh api repos/$OWNER/$REPO/pulls/$N/comments --jq '
  .[] | select(.user.type == "Bot")
       | { comment_id: .id, path, line, severity: (.body | capture("P[123]")?.string // "?"),
           body: (.body | split("\n")[0]) }
'
```

### Step 3 — fetch full bodies with file paths before triaging

The summary line is not enough — the body usually contains the bot's reasoning. Pull the full text along with the file path:

```bash
gh api repos/$OWNER/$REPO/pulls/$N/comments --jq '
  .[] | select(.user.type == "Bot") |
  "-------\n" +
  "comment_id=\(.id)  path=\(.path)  line=\(.line // .original_line // "?")\n" +
  "author=\(.user.login)\n" +
  "body:\n\(.body)\n"
'
```

Match the `path` against your local checkout to confirm whether the line is still current or stale:

```bash
# Show today's local file contents for quick reference while triaging
sed -n '107,135p' js/app.js
```

### Step 4 — triage each comment into one of three buckets

For each bot comment, decide:

| Bucket | Action | Examples |
|---|---|---|
| **1. Real current bug** | Fix on the existing branch | V2V branch was missing `reference_image_urls` forwarding — codex flagged, fixed in same branch |
| **2. Pre-existing / superseded** | Acknowledge in commit log + close without code change | Codex flagged `4:3` aspect pill removal — code now regenerates pills from constraints; live spec advertises `4:3` to zero models; close the finding |
| **3. Style / nit / out of scope** | Skip with a short comment if a thread reply is warranted | Naming choices, doc updates — only respond if the PR author has set up the workflow to care |

Don't auto-fix everything. Bots sometimes flag bugs that don't actually exist anymore (the bot doesn't see git history). Always verify the *current* state of the file path before patching.

### Step 5 — apply fixes in the same branch

Apply each fix as its own commit on the branch the PR is tracking. Prefix the commit message with `fix(codex):` or `fix(review):` so the AI attribution is honest and filterable:

```bash
# Fix 1: shipped
git add js/api.js
git commit -m "fix(codex): 3 review comments on PR #5 — P1 validation + 2 P2s

- validateForm: branch on appState.mode — V2V gets its own gate
  (uploadedVideoUrl + #video-motion-prompt), not image-validation
- buildGenerationParams V2V branch: forward reference_image_urls
- VeniceAPI.inputMode: also recognize constraints.video_input === true"

git push origin fix/codex-round-1

# Open a new PR if needed
gh pr create --base master --head fix/codex-round-1 \
  --title "fix(codex): 3 review comments on PR #5" --body "..."
```

For bucket-2 findings (no actual bug), close them in the PR description or a PR comment with one line:

> The render-aspect pills already regenerate from the model's constraints block; current live spec advertises `4:3` to zero models, so there's nothing in constraints to surface. Closed without code change.

### Step 6 — re-request review / poke CI

After the fix commits land on the branch, the original PR will pick them up automatically. If the bot is configured to re-review on push, that's all that's needed. If a bot review is required manually, request it via:

```bash
gh pr edit $N --add-reviewer $ORG/codex-bot
# or via REST
curl -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$N/requested_reviewers \
  -d '{"reviewers":["codex-bot"]}'
```

Trigger CI / pre-commit before merge if the workflow demands:

```bash
gh run list --branch $(git branch --show-current) --limit 5
gh pr checks
```

### Pitfalls — review-bot triage

- **Stale diffs**: bot comments often tag `line=1100` but the diff has moved. Always re-read the file at or near that path before applying the fix; don't blindly trust the line number.
- **`is_bot` filtering**: use `select(.user.type == "Bot")` — the GitHub `user.type` is reliable. Don't regex on `chatgpt-codex` substring; new bot login names appear every quarter.
- **`replies` endpoint**: review threads have nested replies you might miss. Pull `pulls/$N/comments?per_page=100` with pagination to get the full thread.
- **Don't auto-reply "thanks, will fix" without fixing**: humans skim bot threads. If the bot's call-out was real, ship the fix in the same PR or PR-thread the close-out reasoning.
- **Out-of-date comments after force-push**: review threads rebase strangely. Re-fetch right before merge for current state.

## 9. Complete Workflow Example

```bash
# 1. Start from clean main
git checkout main && git pull origin main

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (Agent makes code changes with file tools)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR (picks gh or curl based on what's available)
# ... (see Section 3)

# 7. Monitor CI (see Section 4)

# 8. Merge when green (see Section 6)
```

## Useful PR Commands Reference

| Action | gh | git + curl |
|--------|-----|-----------|
| List my PRs | `gh pr list --author @me` | `curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open"` |
| View PR diff | `gh pr diff` | `git diff main...HEAD` (local) or `curl -H "Accept: application/vnd.github.diff" ...` |
| Add comment | `gh pr comment N --body "..."` | `curl -X POST .../issues/N/comments -d '{"body":"..."}'` |
| Request review | `gh pr edit N --add-reviewer user` | `curl -X POST .../pulls/N/requested_reviewers -d '{"reviewers":["user"]}'` |
| Close PR | `gh pr close N` | `curl -X PATCH .../pulls/N -d '{"state":"closed"}'` |
| Check out someone's PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |
