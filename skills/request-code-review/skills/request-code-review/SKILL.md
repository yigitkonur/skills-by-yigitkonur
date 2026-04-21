---
name: request-code-review
description: Use skill if you are handing off work — opening a pull request, authoring a self-review, or tidying dirty commits into a reviewable branch before requesting feedback.
---

# Request Code Review

Turn queued work into a reviewable handoff. Default path is a real GitHub PR on the current branch with a self-review body tailored to the diff's domain. Markdown-only mode (no PR) is available when the user explicitly asks for it.

## Trigger boundary

Use this skill when the task is to:

- open a pull request and author its body
- prepare a self-review doc before requesting feedback
- tidy a dirty working tree into clean conventional commits *ready* for review (not as a standalone cleanup)
- hand off work to a human, bot, or subagent reviewer with domain-aware context

Prefer another skill when:

- reviewing someone else's PR → `review-pr`
- cleaning a repo that has unrelated mess, multiple worktrees, or cross-branch debris without an imminent review handoff → `run-repo-cleanup`
- only writing a single commit with no review intent → use the commit workflow directly
- writing a CI config, release pipeline, or publish rules → `publish-*`, `init-*`

## Non-negotiable rules

1. **Commit dirty changes before opening the PR.** Not after. Not "I'll fix the commits in the PR comments later." Not on `main`. A PR against dirty tree is a broken handoff — the reviewer cannot tell what you meant to ship. See `references/rationalizations.md` for the counter to every excuse that shows up here.
2. **Default mode is PR creation.** Markdown-table mode fires only when the user *explicitly* asks for "review doc only" / "no PR" / "just the text". Do not infer markdown mode from vagueness.
3. **Never touch `main` directly.** Branch first. If the current branch is `main`, create a new branch from it before committing anything.
4. **Review text is a self-review, not a changelog.** Explain every change with a rationale, surface weaknesses the author knows about, and ask for explicit review attention on uncertain areas.
5. **PR body stays under 50,000 characters.** GitHub hard limit is 65,536; 50k leaves room for reviewer edits and quotes. If you're approaching it, split the PR.
6. **Domain drives the review lens.** A backend PR, a UI PR, and a content-markdown PR need different reviewer prompts and different self-review angles. Pick the domain before writing.
7. **Multi-domain diffs fan out.** When the diff spans 2+ domains, dispatch one subagent per domain, combine outputs into one coherent body.
8. **Push back when the reviewer is wrong.** With technical reasoning and evidence. Do not capitulate to save time.

## The two output modes

| Mode | Trigger phrase | What the skill produces |
|---|---|---|
| **PR handoff** (default) | "open a PR", "request a review", "hand this off", "ready for review", silence on format | Clean branch pushed to `origin`, `gh pr create` executed, self-review body posted |
| **Markdown review doc** | "just the text", "no PR", "give me a review doc", "write the review as markdown", "summarize for review" | Markdown file or inline output only; no git writes, no PR |

If the user's phrasing is ambiguous, ask once before acting. Default is **not** a license to skip the ask when intent is genuinely unclear.

## Required workflow

### 1. Classify the mode

Read the user's request for an explicit markdown-only signal. If absent, default to PR handoff. State the mode before proceeding. This is a commitment step — once declared, do not swap modes mid-workflow without re-stating.

### 2. Inspect the current state

Run in parallel:

```bash
git status --short
git branch --show-current
git log --oneline origin/main..HEAD 2>/dev/null || git log --oneline -5
git remote -v
gh pr list --head $(git branch --show-current) --json number,url
```

Capture:
- Is the working tree dirty? (modified / untracked / staged but uncommitted)
- Current branch name (and is it `main` / `master` / `default`?)
- Unpushed commit count
- Does a PR already exist for this branch?
- Origin URL (fork vs. upstream risk)

### 3. Handle dirty tree before anything else

If `git status --short` is empty, jump to Step 4.

If dirty:

- If the `run-repo-cleanup` skill is installed (check `~/.claude/skills/run-repo-cleanup/` or `~/.agents/skills/run-repo-cleanup/`), invoke its diff-walk discipline for Phase 1 (dirty tree → conventional commits). Return here when that completes.
- Otherwise, follow the inline tidy in `references/handoff-mechanics.md` — diff-walk the changes, group by domain, one conventional commit per concern. No `git commit -am`. No blind staging.
- If the current branch is `main` / `master`, create a branch first (`git switch -c <type>/<scope>-<slug>`), then commit. Never commit dirty changes to the default branch.

Before moving on, the tree must be clean (`git status --short` empty) and the branch must be pushed to a remote (`git push -u origin <branch>` if no tracking set).

### 4. Classify the diff's domain

Open `git diff origin/main...HEAD --stat` (or `git diff --stat <base>..HEAD`). Classify each changed path:

| Signal in the path or diff | Domain |
|---|---|
| `server/`, `api/`, SQL migrations, `*.controller.ts`, `routes/`, auth/session code, infra `.tf`/`.yaml` | **backend** |
| `*.ts`/`*.tsx`/`*.js`/`*.jsx` outside `server/`, state hooks, client-side fetch, React/Vue/Svelte | **frontend** |
| `server.ts` with `Server`/`Tool` from `@modelcontextprotocol/sdk`, `SKILL.md` mentioning MCP, Zod schemas for tools | **mcp-server** |
| CSS, Tailwind classes, component visuals, design tokens, a11y attributes, layout/spacing | **ui-engineering** |
| `bin/`, `scripts/*.sh`, argparse/commander entrypoints, `*.rs` in `src/main.rs`, argument parsing | **cli-tool** |
| `*.md` under `content/`, `posts/`, `docs/`, blog/docs markdown | **content-markdown** |
| None of the above, or a clear mix that doesn't fit | **generic** |

Route to one of:

- `references/domains/backend.md`
- `references/domains/frontend-ts-js.md`
- `references/domains/mcp-server.md`
- `references/domains/ui-engineering.md`
- `references/domains/cli-tool.md`
- `references/domains/content-markdown.md`
- `references/domains/generic.md`

### 5. Fan out if multi-domain

If the diff touches **2+ domains** and each has ≥5% of the changed lines, do not write a single review body alone. Instead:

- For each domain cluster, dispatch a subagent via the Task tool. Brief each with the same BASE_SHA/HEAD_SHA, restrict it to the paths in its cluster, and hand it the matching domain reference.
- Each subagent returns: the per-domain change summary, the weaknesses it would flag, and 1-3 questions it would ask the reviewer.
- Combine the subagent outputs into one coherent review body — one section per domain under an `## Areas` heading, plus an overall summary.
- See `references/subagent-dispatch.md` for the per-subagent prompt template and combination rules.

Single-domain diffs skip this step.

### 6. Draft the review body

Follow the template in `references/review-text-template.md`. Structure:

```
# <title matching commit style>

## Summary (2-4 sentences)
## Context / Why now
## The N items (per-item: files, rationale, verification)
## Files touched (aggregate table)
## Verification (what I ran, what I did not)
## Weaknesses and open questions
## Request to the reviewer
## Follow-ups (not in scope)
```

Under 50,000 characters. Explain every change. Identify **at least two** weaknesses the author knows about. Ask **at least one** question on something the author is uncertain of — this is the "please explain in depth" hook.

### 7. Ship it

**PR handoff mode:**

```bash
gh pr create \
  --repo <owner>/<repo> \           # Always explicit — gh defaults are wrong often
  --base <target-branch> \
  --head <current-branch> \
  --title "<type>(<scope>): <subject>" \
  --body-file /tmp/pr-body.md
```

Then verify:

```bash
gh pr view <N> --repo <owner>/<repo> --json url,baseRefName,headRefName
```

URL must point to the intended repo. Base must be the intended target. If it's on the wrong repo or wrong base, close it immediately and reopen on the right target.

**Markdown mode:** write the review body to the path the user asked for (or inline it in the response). Do not push, do not run `gh pr create`, do not commit — the user said markdown-only.

## Domain routing

| Domain | Reference | When to read |
|---|---|---|
| backend service/API | `references/domains/backend.md` | Diff touches server routes, API handlers, SQL, auth, infra |
| frontend TS/JS | `references/domains/frontend-ts-js.md` | Client-side TypeScript/JavaScript, state, data fetching, framework components |
| MCP server | `references/domains/mcp-server.md` | `@modelcontextprotocol/sdk` imports, tool/resource registration, SKILL.md authoring |
| UI engineering | `references/domains/ui-engineering.md` | Visual changes, CSS, design tokens, a11y, layout |
| CLI tool | `references/domains/cli-tool.md` | Command entrypoints, flag parsing, help text, exit codes |
| content markdown | `references/domains/content-markdown.md` | Blog posts, docs, SKILL.md bodies, README prose |
| generic | `references/domains/generic.md` | Anything that does not fit above, or a mix the author cannot cleanly split |

## Supporting references

| File | Read when |
|---|---|
| `references/review-text-template.md` | Drafting the PR body structure, severity sections, or weakness language |
| `references/subagent-dispatch.md` | Fanning out to per-domain specialist subagents and combining their output |
| `references/handoff-mechanics.md` | Running diff-walk commits, branching off `main`, pushing, opening the PR via `gh` |
| `references/rationalizations.md` | When the agent feels tempted to skip commits, push to `main`, or shortcut the review body |

## Rationalizations to counter (RED baseline, abridged)

The "commit dirty changes before the PR" rule is the bypass point. Agents under pressure say:

| Rationalization | Counter |
|---|---|
| "The PR is urgent; I'll tidy commits in the PR comments later." | PR comments are not commits. Reviewers diff by commit. A broken commit history is a broken review. |
| "I'll squash on merge anyway." | Squash-on-merge hides mistakes during review, not after. Reviewers need the clean history *now*. |
| "Just this once — the changes are small." | Rules don't bend for small. The small exception trains the large one. |
| "The working tree has WIP I don't want in the PR." | Stash it, or move it to a second branch. Do not open the PR on a dirty tree hoping nobody notices. |
| "I'll open as Draft and fix it up." | Draft PRs still get CI runs, bot reviews, and human skim. Open them clean or not at all. |

Full table with verbatim capture + counters: `references/rationalizations.md`.

## Output contract

Unless the user wants a different format, produce in this order:

1. Mode declaration (after Step 1) — "PR handoff" or "markdown review doc".
2. State inspection summary (after Step 2) — dirty? branch? unpushed? existing PR?
3. Dirty-tree handling report (after Step 3) — what was committed and how, or "tree was already clean".
4. Domain classification (after Step 4) — which domain reference(s) are in play.
5. Fan-out decision (after Step 5) — single-domain or which subagents were dispatched.
6. Review body draft (after Step 6) — visible before it is pushed anywhere.
7. PR URL + verification output (after Step 7, PR mode only), or the markdown file path (markdown mode).

Each artifact appears at the step that produces it. Do not batch to the end.

## Do this, not that

| Do this | Not that |
|---|---|
| check dirty tree first, commit, push, then open PR | `gh pr create` against a dirty tree |
| name the domain before drafting the body | write a generic body that ignores what the diff actually is |
| fan out to one subagent per domain when multi-domain | a single monolithic body that blurs domain concerns |
| pass BASE_SHA + HEAD_SHA + diff to subagents, not session history | hand the subagent the full conversation context |
| explain every change in the body | "Various improvements" or "Refactoring" as the summary |
| flag ≥2 weaknesses + ≥1 explicit question to the reviewer | "LGTM, please merge" with no critique of your own work |
| use `gh pr create --repo` explicit every time | rely on `gh` defaults for the target repo |
| push back with evidence when the reviewer is wrong | capitulate to clear the review and move on |
| stay under 50,000 chars | single monolithic 60k-char body — split the PR |

## Guardrails and recovery

- Do not open a PR on a dirty tree.
- Do not commit to `main` / `master` / default. Branch first.
- Do not assume `gh` defaults to the right repo. Pass `--repo` explicitly.
- Do not skip the dirty-tree handoff because "the PR is urgent."
- Do not collapse a multi-domain diff into a single-voice body. Fan out.
- Do not claim tests passed when you only ran type-check. State exactly what you ran.
- Do not write the review in "Thanks for reviewing!" voice. Actions over gratitude.

Recovery moves:

- **PR opened on the wrong repo** — close immediately, reopen on the intended target. Check `--repo` every time.
- **Dirty tree committed to `main` accidentally** — do not force-push. Create a branch pointing to the current commit, reset `main` back, then continue on the branch.
- **Subagent fan-out returned conflicting recommendations** — surface the conflict in the review body under "Weaknesses and open questions"; let the reviewer decide.
- **Body exceeds 50k chars** — split the PR. Do not truncate.

## Final checks

Before declaring done, confirm:

- [ ] mode declared and matched the user's request
- [ ] `git status --short` is empty on the author's branch
- [ ] branch is pushed and tracks `origin`
- [ ] PR URL returned (PR mode) or markdown path returned (doc mode)
- [ ] body ≤ 50,000 characters
- [ ] every change in the diff has an entry in the body
- [ ] ≥2 weaknesses surfaced
- [ ] ≥1 explicit question to the reviewer
- [ ] domain reference actually matches the diff
- [ ] multi-domain diffs were fanned out to subagents (or explicitly justified as single-voice)
- [ ] `gh pr view` confirms the PR is on the intended repo and base branch (PR mode)

Quick orphan check for this skill:

```bash
for f in $(find references -name '*.md' -type f); do grep -q "$(basename $f)" SKILL.md || echo "ORPHAN: $f"; done
```
