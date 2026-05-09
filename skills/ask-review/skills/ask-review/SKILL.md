---
name: ask-review
description: Use skill if you are opening a PR for your own branch, writing a self-review body, or tidying your dirty tree into clean commits before requesting feedback.
---

# Request Code Review

Hand off **your own** queued work as a reviewable artifact. Default mode is a real GitHub PR on the current branch with a domain-aware self-review body. Markdown-only mode (no PR, just the text) fires only on explicit request.

## When to use this skill

Trigger on any of these user phrases:

- *"open a PR / pull request for this"*
- *"hand this off for review"*
- *"this is ready for review"*
- *"write me a self-review"*
- *"clean up my commits and open a PR"*
- *"give me a review doc / no PR, just the markdown"*
- *"summarize this branch for the reviewer"*
- *"request review on this branch"*

Do NOT use this skill when:

- The user wants to **review someone else's PR** for merge readiness → use `do-review` instead.
- The user wants to **triage feedback already received** on a PR (comments, bot review, multi-reviewer streams) → use `evaluate-code-review` instead.
- The repo has unrelated dirty mess across multiple branches/worktrees with no imminent review → use `run-repo-cleanup`.
- The user only wants a single conventional commit with no review handoff → use the commit workflow directly.

## The two output modes

| Mode | Trigger phrase | What this skill produces |
|---|---|---|
| **PR handoff** (default) | "open a PR", "ready for review", "hand this off", silence on format | Clean branch pushed to `origin`, `gh pr create` executed, self-review body posted |
| **Markdown review doc** | "just the text", "no PR", "give me a review doc", "write the review as markdown" | Markdown file or inline output only — no git writes, no PR |

If the user's phrasing is ambiguous, ask once. Default is *not* a license to skip the ask when intent is genuinely unclear.

## Non-negotiable rules (load-bearing — do not skip)

1. **Commit dirty changes BEFORE opening the PR. Not after.** A PR against a dirty tree is a broken handoff — the reviewer cannot tell what you meant to ship. Counters to every excuse live in `references/rationalizations.md`.
2. **Default mode is PR creation.** Markdown-only mode fires only when the user *explicitly* asks for "review doc only" / "no PR" / "just the text". Do not infer markdown mode from vagueness.
3. **Never touch `main` / `master` / default branch directly.** If the current branch is the default branch, create a new branch *before* committing anything.
4. **Review text is a self-review, not a changelog.** Explain every change with a rationale, surface ≥2 weaknesses the author already knows about, ask ≥1 explicit question on something uncertain.
5. **PR body stays under 50,000 characters.** GitHub's hard limit is 65,536; 50k leaves room for reviewer edits and quoted replies. If approaching it, split the PR.
6. **Domain drives the review lens.** Backend, UI, and content-markdown PRs need different reviewer prompts and different self-review angles. Pick the domain *before* drafting.
7. **Multi-domain diffs fan out.** When the diff spans 2+ domains with ≥5% lines each, dispatch one subagent per domain and combine outputs.
8. **Pass `gh pr create --repo <owner>/<repo>` explicitly every time.** `gh` defaults are wrong often enough to bite.

## Required workflow

### 1. Classify the mode

Read the user's request for an explicit markdown-only signal. If absent, default to PR handoff. State the mode out loud before proceeding — once declared, do not swap mid-workflow without re-stating.

### 2. Inspect current state (run in parallel)

```bash
git status --short
git branch --show-current
git log --oneline origin/main..HEAD 2>/dev/null || git log --oneline -5
git remote -v
gh pr list --repo <owner>/<repo> --head $(git branch --show-current) --json number,url
```

Capture: dirty? branch name? on default branch? unpushed count? PR already exists for this branch? origin URL (fork vs. upstream risk).

### 3. Handle dirty tree before anything else

If `git status --short` is empty, jump to Step 4.

If dirty:

- If `run-repo-cleanup` is installed (`~/.claude/skills/run-repo-cleanup/` or `~/.agents/skills/run-repo-cleanup/`), invoke its diff-walk discipline for Phase 1 (dirty tree → conventional commits). Return here when done.
- Otherwise, follow the inline tidy in `references/handoff-mechanics.md` — diff-walk the changes, group by domain, one conventional commit per concern. **No `git commit -am`. No blind `git add -A`.**
- If the current branch is `main` / `master` / default, create a branch first (`git switch -c <type>/<scope>-<slug>`), then commit. Never commit dirty changes to the default branch.

Before moving on: `git status --short` must be empty AND the branch must be pushed to a remote (`git push -u origin <branch>` if no upstream).

### 4. Classify the diff's domain

Run `git diff origin/main...HEAD --stat` (or `git diff --stat <base>..HEAD`). Match the changed paths against this table:

| Signal in path or diff | Domain | Reference |
|---|---|---|
| `server/`, `api/`, SQL migrations, `*.controller.ts`, `routes/`, auth/session, infra `.tf`/`.yaml` | **backend** | `references/domains/backend.md` |
| `*.ts`/`*.tsx`/`*.js`/`*.jsx` outside `server/`, hooks, client-side fetch, React/Vue/Svelte components | **frontend-ts-js** | `references/domains/frontend-ts-js.md` |
| `server.ts` with `Server`/`Tool` from `@modelcontextprotocol/sdk`, Zod tool schemas, SKILL.md authoring | **mcp-server** | `references/domains/mcp-server.md` |
| CSS, Tailwind classes, design tokens, a11y attributes, layout/spacing, component visuals | **ui-engineering** | `references/domains/ui-engineering.md` |
| `bin/`, `scripts/*.sh`, argparse/commander entrypoints, `src/main.rs`, flag parsing, exit codes | **cli-tool** | `references/domains/cli-tool.md` |
| `*.md` under `content/`, `posts/`, `docs/`, blog/docs prose, README bodies | **content-markdown** | `references/domains/content-markdown.md` |
| None of the above, or a clear mix that does not split cleanly | **generic** | `references/domains/generic.md` |

### 5. Fan out if multi-domain

If the diff touches **2+ domains AND each domain has ≥5% of the changed lines**, do not write a single review body alone:

- For each domain cluster, dispatch a subagent via the Task tool. Brief each with `BASE_SHA` + `HEAD_SHA`, restrict it to the cluster's paths, and hand it the matching domain reference.
- Each subagent returns: per-domain change summary, weaknesses to flag, 1-3 reviewer questions.
- Combine outputs into one coherent body — one section per domain under an `## Areas` heading, plus an overall summary.

Per-subagent prompt template and combination rules live in `references/subagent-dispatch.md`. Single-domain diffs skip this step.

### 6. Draft the review body

Follow the structure in `references/review-text-template.md`:

```
# <title matching commit style>

## Summary (2-4 sentences)
## Context / Why now
## The N items (per-item: files, rationale, verification)
## Files touched (aggregate table)
## Verification (what I ran, what I did NOT)
## Weaknesses and open questions
## Request to the reviewer
## Follow-ups (not in scope)
```

Hard requirements: under 50,000 chars; explain every change; surface **≥2 weaknesses** the author knows about; ask **≥1 explicit question** on something uncertain (this is the "please explain in depth" hook).

### 7. Ship it

**PR handoff mode:**

```bash
gh pr create \
  --repo <owner>/<repo> \           # Always explicit — gh defaults bite
  --base <target-branch> \
  --head <current-branch> \
  --title "<type>(<scope>): <subject>" \
  --body-file /tmp/pr-body.md
```

Verify immediately:

```bash
gh pr view <N> --repo <owner>/<repo> --json url,baseRefName,headRefName
```

URL must point to the intended repo. Base must be the intended target. If wrong, close the PR immediately and reopen on the correct target.

**Markdown mode:** write the review body to the path the user asked for (or inline it in the response). Do not push, do not run `gh pr create`, do not commit.

## Rationalizations to counter (RED baseline)

The "commit dirty changes before the PR" rule is the bypass point. Agents under pressure will say:

| Rationalization | Counter |
|---|---|
| "The PR is urgent; I'll tidy commits in PR comments later." | PR comments are not commits. Reviewers diff by commit. A broken commit history is a broken review. |
| "I'll squash on merge anyway." | Squash-on-merge hides mistakes *during* review, not after. Reviewers need clean history *now*. |
| "Just this once — the changes are small." | Rules don't bend for small. The small exception trains the large one. |
| "The working tree has WIP I don't want in the PR." | Stash it, or move it to a second branch. Do not open the PR on a dirty tree hoping nobody notices. |
| "I'll open as Draft and fix it up." | Draft PRs still get CI runs, bot reviews, and human skim. Open them clean or not at all. |

Full table with verbatim agent capture lines and counters: `references/rationalizations.md`.

## Output contract

Unless the user wants a different format, produce these artifacts in order — each at the step that produces it, *not batched at the end*:

1. **Mode declaration** (after Step 1) — "PR handoff" or "markdown review doc".
2. **State inspection summary** (after Step 2) — dirty? branch? unpushed? existing PR?
3. **Dirty-tree handling report** (after Step 3) — what was committed and how, or "tree was already clean".
4. **Domain classification** (after Step 4) — which domain reference(s) are in play.
5. **Fan-out decision** (after Step 5) — single-domain or which subagents were dispatched.
6. **Review body draft** (after Step 6) — visible *before* it is pushed anywhere.
7. **PR URL + verification output** (after Step 7, PR mode), or **markdown file path** (markdown mode).

## Do this, not that

| Do this | Not that |
|---|---|
| Check dirty tree first, commit, push, then open PR | `gh pr create` against a dirty tree |
| Name the domain before drafting the body | Generic body that ignores what the diff actually is |
| Fan out one subagent per domain when multi-domain | Monolithic body that blurs domain concerns |
| Pass `BASE_SHA` + `HEAD_SHA` + diff to subagents, not session history | Hand the subagent the full conversation context |
| Explain every change in the body | "Various improvements" / "Refactoring" as the summary |
| Flag ≥2 weaknesses + ≥1 explicit reviewer question | "LGTM, please merge" with no critique of your own work |
| Pass `gh pr create --repo` explicit every time | Rely on `gh` defaults for the target repo |
| Push back with evidence when the reviewer is wrong | Capitulate to clear the review and move on |
| Stay under 50,000 chars; split if larger | Single 60k-char monolith |

## Guardrails and recovery

**Do not:** open a PR on a dirty tree; commit to default branch; assume `gh` defaults to the right repo; skip the dirty-tree handoff because "the PR is urgent"; collapse a multi-domain diff into a single voice; claim tests passed when only type-check ran; write in "Thanks for reviewing!" voice.

**Recovery moves:**

- **PR opened on the wrong repo** — close immediately, reopen on the intended target. Always pass `--repo`.
- **Dirty tree committed to default branch accidentally** — do *not* force-push. Create a branch pointing to current commit, reset default back, continue on the branch.
- **Subagent fan-out returned conflicting recommendations** — surface the conflict in the body under "Weaknesses and open questions"; let the reviewer decide.
- **Body exceeds 50k chars** — split the PR. Do not truncate.

## Reference routing

Domain references (read the one that matches the diff):

- `references/domains/backend.md` — server routes, API handlers, SQL, auth, infra
- `references/domains/frontend-ts-js.md` — client-side TS/JS, state, data fetching, framework components
- `references/domains/mcp-server.md` — `@modelcontextprotocol/sdk` imports, tool/resource registration, SKILL.md authoring
- `references/domains/ui-engineering.md` — visual changes, CSS, design tokens, a11y, layout
- `references/domains/cli-tool.md` — command entrypoints, flag parsing, help text, exit codes
- `references/domains/content-markdown.md` — blog posts, docs, SKILL.md bodies, README prose
- `references/domains/generic.md` — anything that does not fit above

Cross-cutting references (read by step):

- `references/handoff-mechanics.md` — diff-walk commits, branching off default, pushing, opening the PR via `gh` (Step 3 + Step 7)
- `references/review-text-template.md` — PR body structure, severity sections, weakness language (Step 6)
- `references/subagent-dispatch.md` — per-domain subagent prompt template and output combination (Step 5)
- `references/rationalizations.md` — counters when tempted to skip commits, push to default, or shortcut the body

## Final checks

Before declaring done, confirm:

- [ ] Mode declared and matches the user's request
- [ ] `git status --short` empty on the author's branch
- [ ] Branch pushed and tracks `origin`
- [ ] PR URL returned (PR mode) or markdown path returned (doc mode)
- [ ] Body ≤ 50,000 characters
- [ ] Every change in the diff has an entry in the body
- [ ] ≥2 weaknesses surfaced
- [ ] ≥1 explicit reviewer question
- [ ] Domain reference actually matches the diff
- [ ] Multi-domain diffs fanned out to subagents (or explicitly justified single-voice)
- [ ] `gh pr view` confirms PR is on the intended repo and base branch (PR mode)
