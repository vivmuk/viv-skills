# Git Website Refresh via Open Design

Session-derived workflow for updating a static/website repo after Open Design is already running locally.

## When this applies

- User asks to update a website in git/GitHub and the task is design-led.
- Repo can be cloned or is already local.
- The site is a static page or simple app where visual direction can be translated directly into source changes.

## Proven sequence

1. **Check Open Design first**
   ```bash
   ~/.local/bin/open-design-venice status
   ```
   If idle, start it with the normal launcher/ports from the main skill.

2. **Clone/fetch and branch before editing**
   ```bash
   mkdir -p ~/repos
   git clone https://github.com/<owner>/<repo>.git ~/repos/<repo> || git -C ~/repos/<repo> fetch origin --prune
   cd ~/repos/<repo>
   git status --short --branch
   git switch -c design/open-design-refresh
   ```

3. **Import the folder into Open Design**
   Use the daemon folder-import endpoint so Open Design works directly in the real git checkout (`metadata.baseDir`), not a shadow copy:
   ```bash
   python3 - <<'PY'
   import json, urllib.request
   body=json.dumps({
     "baseDir":"/absolute/path/to/repo",
     "name":"<Repo> site refresh"
   }).encode()
   req=urllib.request.Request(
     'http://127.0.0.1:7457/api/import/folder',
     data=body,
     headers={'Content-Type':'application/json'},
     method='POST',
   )
   data=json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
   print(json.dumps({
     "projectId": data.get('project',{}).get('id'),
     "conversationId": data.get('conversationId'),
     "entryFile": data.get('entryFile'),
   }, indent=2))
   PY
   ```

4. **Ask Venice/Open Design for direction, then implement**
   Keep the design ask concise and implementation-oriented: current site shape, audience, constraints, desired feel, files that can change. Convert the direction into source edits rather than stopping at a critique.

   **Make the delta visually undeniable.** For a design refresh, avoid only subtle polish over the existing content. Change at least several of: background/color system, hero composition, typography scale, navigation/control model, card layout, modal/detail treatment, and motion. If the user says it "looks the same," redo with a stronger art direction (e.g. dark gallery vs light editorial) while preserving data/content.

5. **Static-site verification checklist**
   - Extract inline scripts and run `node --check`.
   - Validate JSON with `python3 -m json.tool`.
   - Serve locally with `python3 -m http.server <port>`.
   - Fetch `/`, data JSON, and all referenced image/asset paths over HTTP. URL-quote non-ASCII paths (e.g. `appliqué`) during verification.
   - Run `git diff --check`.
   - Remove temporary `__pycache__`, local screenshots, and background server process.

6. **Commit locally, ask before push/PR**
   Pushing branches and opening PRs are external/public side effects. Commit locally if the change is coherent, then ask before `git push`/`gh pr create`.

## PR iteration after user review

When a user reviews a design PR and says it still looks the same, or asks for a redo after merge/push:

1. Check the PR state before pushing more commits:
   ```bash
   python3 - <<'PY'
   import json, os, urllib.request
   owner, repo, pr = '<owner>', '<repo>', '<number>'
   token = os.environ.get('GITHUB_TOKEN')
   headers={'Accept':'application/vnd.github+json'}
   if token: headers['Authorization']=f'Bearer {token}'
   data=json.loads(urllib.request.urlopen(urllib.request.Request(
     f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr}', headers=headers), timeout=30).read())
   print(json.dumps({'state':data['state'], 'merged':data.get('merged'), 'head':data['head']['ref'], 'sha':data['head']['sha'][:7]}, indent=2))
   PY
   ```
2. If the PR is still open, push the follow-up commit to the same branch.
3. If the PR was already merged/closed, base the follow-up branch on fresh `origin/main`, then create a new PR. Do **not** assume pushing to the old branch updates a merged PR; GitHub keeps the old PR closed and a new PR is needed.
4. After rebasing/resetting a feature branch to `origin/main`, use `--force-with-lease` only for that feature branch and only after preserving any intended edits.

## Pitfalls

- A design branch can be merged while the local branch continues to exist. Pushing another commit to that same branch does not reopen/update the merged PR; create a follow-up PR from a branch based on current `origin/main`.
- `POST /api/projects` cannot set `metadata.baseDir`; use `POST /api/import/folder` for existing folders.
- If a generated/legacy build script embeds old HTML, update it to preserve the redesigned page or it will clobber the refresh later.
- Python's `urllib` may fail on non-ASCII image paths unless you `urllib.parse.quote()` the path segment.
- Playwright may be installed without browser binaries; don't block the task on screenshots if HTTP/JS/data checks already verify the static site.
