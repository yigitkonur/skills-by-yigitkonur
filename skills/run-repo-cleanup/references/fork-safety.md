# Fork Safety Checklist

The single most common mistake in this flow is **opening a PR, issue, or comment on the upstream repo instead of the private fork**. Once it's posted, it's indexed — delete-and-reopen does not fully unring it. Everything here is about preventing that.

## Invariants

1. `origin` = the private fork. Every push and every `gh` mutation must hit origin.
2. `upstream` = the public repo we sync *from*. Read-only. Never push, never `pr create`, never `issue create`, never `pr comment`.
3. `gh` CLI defaults are not safe. It infers the repo from branch upstream; that inference is wrong often enough that **every mutating `gh` call passes `--repo <fork-owner>/<fork-repo>` explicitly**.

## Verify before every push or PR

```bash
# 1. Remotes are what you expect
git remote -v
# origin    git@github.com:<you>/<fork>.git  (fetch)
# origin    git@github.com:<you>/<fork>.git  (push)
# upstream  git@github.com:<them>/<repo>.git (fetch)
# upstream  git@github.com:<them>/<repo>.git (push)

# 2. Current branch tracks origin, not upstream
git branch -vv
# * feat/my-work abc1234 [origin/feat/my-work]   ✓
# * feat/my-work abc1234 [upstream/feat/my-work] ✗ STOP

# 3. gh CLI would post where?
gh repo view --json owner,name
# If this prints the upstream owner, your next gh call is about to go wrong.
```

## The `--repo` rule

Every mutating `gh` command takes `--repo`. No exceptions.

```bash
# PR creation
gh pr create --repo <fork-owner>/<fork-repo> --base main --head feat/x --title "..." --body-file /tmp/b.md

# Issue creation
gh issue create --repo <fork-owner>/<fork-repo> --title "..." --body "..."

# Comment on PR
gh pr comment <pr-number> --repo <fork-owner>/<fork-repo> --body "..."

# Reply to inline thread
gh api repos/<fork-owner>/<fork-repo>/pulls/<pr>/comments/<id>/replies -f body="..."

# Release
gh release create <tag> --repo <fork-owner>/<fork-repo> ...

# PR review
gh pr review <pr-number> --repo <fork-owner>/<fork-repo> --approve
```

Read-only `gh` calls (`gh pr list`, `gh pr view`, `gh repo view`) are safer but still benefit from explicit `--repo` so your brain practices the habit.

## If you mess up

You accidentally opened a PR / issue / comment on upstream.

1. **Immediately:**
   ```bash
   gh pr close <number> --repo <upstream-owner>/<upstream-repo> --delete-branch
   # or
   gh issue close <number> --repo <upstream-owner>/<upstream-repo>
   # or
   gh api repos/<upstream-owner>/<upstream-repo>/pulls/comments/<id> -X DELETE
   ```
2. **Reopen on the fork** with `--repo <fork>` explicit.
3. **If the accidental post revealed internal / commercial work**: notify whoever owns the leak-response process in the project. Deleted GitHub content is still cached in notification emails, mobile app feeds, and third-party indexers (search engines, GitHub Archive). Treat the leak as "posted", not "undone".
4. **Post-incident:** add a sentence to the root `AGENTS.md` about the specific failure mode you hit (e.g. "`gh pr create` from a branch tracking `upstream/*` defaults to upstream"), so the next person gets warned.

## Secrets checklist

Before pushing, scan for things that must never reach git:

- `.env`, `.env.local`, `.env.*.local` — never tracked.
- `*.pem`, `*.p12`, `id_rsa`, `id_rsa.pub`, `*.key` — never tracked.
- AWS / GCP / Azure credential JSON.
- Database URLs with real passwords inline.
- Third-party API keys inline in source (OpenAI, Anthropic, Stripe, …).
- Session artifacts from AI agents: `.continues-handoff.md`, `.claude-*`, `.cursor-*`, `.aider*`, in-progress TODO scratch files.
- Private notes / meeting transcripts / customer data.

**If the repo's constraint is "no `.env`"** (some private forks explicitly forbid `.env` to avoid divergent local config):

- Hardcode the concrete values directly into the scripts / code that need them.
- Keep those files in the repo only if the repo is **confirmed private** and will stay private.
- Document in root `AGENTS.md` that secrets are hardcoded so future agents don't try to "refactor into env vars".
- If the repo ever transitions to public, rotate every hardcoded value first and convert to env vars as a separate PR.

## `.gitignore` patterns to adopt once

Drop these into root `.gitignore` on the fork the first time this skill runs there. They prevent almost every common accidental commit.

```gitignore
# Secrets
.env
.env.local
.env.*.local
*.pem
*.p12
id_rsa
id_rsa.pub
*.key
credentials.json
service-account.json

# AI agent session artifacts
.continues-handoff.md
.claude-session*
.cursor-session*
.aider*
.design-soul/
derailment-notes/

# Editor scratch
.vscode/settings.local.json
.idea/workspace.xml
*.swp
*.swo
.DS_Store
Thumbs.db

# Local-only test / debug output
scratch/
tmp/
*.log
```

Commit this as `chore(git): ignore secrets and agent session artifacts` before any code commits.

## `git push` safety

- Always push to `origin`. If you're tempted to `git push upstream` for "testing", stop.
- Never `--force` or `--force-with-lease` on a branch that has a PR open unless you pushed it yourself in the last few minutes.
- Never push directly to `main`. Branch protection should block this; if it doesn't, treat that as an AGENTS.md bug to report.

## Auditing what happened

When in doubt, reconstruct the trace:

```bash
# Last 10 refs-update events (includes pushes)
git reflog --all | head -20

# What got pushed to origin in the last N commits
git log origin/<branch> --oneline -10

# What each branch tracks
git for-each-ref --format='%(refname:short) → %(upstream:short)'

# Which PRs are open on the fork
gh pr list --repo <fork-owner>/<fork-repo> --state open

# Which PRs are open on upstream (should almost always be 0)
gh pr list --repo <upstream-owner>/<upstream-repo> --author @me
```

The last command is the fastest sanity check. Run it after any session that created PRs.

## Bottom line

`--repo` every time. `origin` is the fork. `upstream` is read-only. Audit remotes before pushes. Never track secrets. One discipline, zero exceptions.
