# draft-pr-body.py

Generates a Phase-4 PR body skeleton from a commit range. Matches the structure in `references/pr-body-template.md` with per-commit item sections and an aggregated files-touched table. Pipe into `/tmp/pr-body.md` and edit the `TODO:` sections before `gh pr create --body-file`.

## Usage

```bash
python3 scripts/draft-pr-body.py --base main --head HEAD > /tmp/pr-body.md
$EDITOR /tmp/pr-body.md
gh pr create --repo <fork>/<repo> --base main --head <branch> \
  --title "<emoji> <type>(<scope>): <subject>" \
  --body-file /tmp/pr-body.md
```

Target: stay under **50,000 characters** (GitHub hard limit 65,536). Check with `wc -c /tmp/pr-body.md` before creating the PR.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--base <ref>` | required | Base branch of the PR (e.g. `main`, `origin/main`, `feat/parent`). |
| `--head <ref>` | `HEAD` | Head branch of the PR. |
| `--title <string>` | last-commit subject | Override the auto-derived PR title. |

## What it generates

- `# <title>` line.
- `## Summary` — bullet list of commit subjects + net diff stats.
- `## Context & motivation` — TODO placeholder.
- `## The N item(s)` — one subsection per non-merge commit in the range:
  - Commit subject as heading.
  - File list (first 6, overflow marker if more).
  - Commit body if present; otherwise a TODO placeholder.
- `## Files touched` — aggregate table (Domain | Path | Type), one row per touched file.
- `## Verification` — empty Automated + Manual sections with TODO placeholders.
- `## Risks & open items` — TODO placeholder.
- `## Follow-ups (not in scope)` — TODO placeholder.

Every `TODO:` line is a prompt for the agent to fill in. Don't leave them in the final body.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Skeleton printed successfully. |
| 1 | No commits in `<base>..<head>` range — nothing to draft. |
| 2 | Not a git repo / `git log` failed. |

## When to run

- **Phase 4**, just before `gh pr create`.
- **Per PR** — run once per branch. For stacked PRs, run once against each child branch with its parent as `--base`.

## Safety

Read-only. No mutation. No network. Pure `git log` + `git show --name-status` + `git diff --shortstat`.

## Example

For a branch `feat/wope-lockdown` with 2 commits on top of `main`:

```bash
python3 scripts/draft-pr-body.py --base main --head feat/wope-lockdown
```

Produces something like:

```markdown
# ✨ feat(wope-lockdown): brand + behavior lockdown layer

## Summary

- ✨ feat(wope-lockdown): brand + behavior lockdown layer
- 📝 docs(wope): document lockdown layer + GitHub policy in AGENTS.md

**Net diff:** 21 files, +338 / −403. Commits: 2.

## Context & motivation

> TODO: explain why this PR exists — the problem it solves, what prompted it,
> what the intended outcome is. 3–5 sentences.

## The 2 items
### 1. ✨ feat(wope-lockdown): brand + behavior lockdown layer

**File(s):** `src/initialize.ts`, `index.html`, …

…
```

Edit the `TODO:` sections. Everything else is a solid starting point.

## Extending

- To add additional sections (e.g. "Screenshots", "Rollback plan"), edit the `render()` function — add the section name + TODO placeholder.
- To change domain classification in the Files-Touched table, edit `domain_of()`.
