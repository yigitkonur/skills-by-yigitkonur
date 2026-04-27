# Reuse from run-repo-cleanup

Single discoverable index of which `run-repo-cleanup` file covers which concern. **Never duplicate** these files in this skill — point to them. Update this index when run-repo-cleanup adds material; otherwise the index drifts and the skill ends up with stale parallel docs.

`<run-repo-cleanup>` is the install path of the run-repo-cleanup skill. Pinned in this skill's `SKILL.md` Pinned Defaults table.

## References

| Concern | Canonical file |
|---|---|
| Pre-flight audit semantics, `.gitignore` hygiene, surprise-state triage | `skills/run-repo-cleanup/references/pre-flight-audit.md` |
| Diff-walk discipline, `git add -p` recipes, hunk-level splits | `skills/run-repo-cleanup/references/diff-walk-discipline.md` |
| Conventional Commits + gitmoji + type/scope registry | `skills/run-repo-cleanup/references/conventional-commits.md` |
| Fork safety, `--repo` rule, accidental-upstream recovery, secrets checklist | `skills/run-repo-cleanup/references/fork-safety.md` |
| `to-delete/` quarantine pattern | `skills/run-repo-cleanup/references/to-delete-folder.md` |
| Worktree / stash / branch recipes | `skills/run-repo-cleanup/references/worktree-and-stash.md` |
| Multi-worktree merge ordering (foundation → leaf) | `skills/run-repo-cleanup/references/multi-worktree-merge-order.md` |
| PR body template (worked example, length cap) | `skills/run-repo-cleanup/references/pr-body-template.md` |
| Post-PR verification (subagent dispatch, checklist, expected report) | `skills/run-repo-cleanup/references/post-pr-verification.md` |
| Receiving-review patterns (forbidden phrases, verification-first, YAGNI gate) | `skills/run-repo-cleanup/references/receiving-review-patterns.md` |
| General agent thinking steering (decompose / order / verify / when to stop) | `skills/run-repo-cleanup/references/agent-thinking-steering.md` |
| Scripts-and-docs layout convention (`.py` + `.md` pairing) | `skills/run-repo-cleanup/references/scripts-and-docs-layout.md` |

## Scripts

| Concern | Canonical script |
|---|---|
| Read-only state dump (Phase 0 base audit) | `skills/run-repo-cleanup/scripts/audit-state.py` |
| Worktree enumeration (Phase 0, Phase 2 verification) | `skills/run-repo-cleanup/scripts/list-worktrees.py` |
| `to-delete/` setup (Phase 0 if missing) | `skills/run-repo-cleanup/scripts/init-to-delete.py` |
| Foundation → leaf merge order heuristic (Phase 4) | `skills/run-repo-cleanup/scripts/suggest-merge-order.py` |
| PR body skeleton (referenced by `/ask-review`; not directly used) | `skills/run-repo-cleanup/scripts/draft-pr-body.py` |
| Retire merged local + remote branches (Phase 9) | `skills/run-repo-cleanup/scripts/retire-merged-branches.py` |

Phase 5's PR-Creator sub-agent uses the `/ask-review` **skill**, which internally produces a more comprehensive body than `draft-pr-body.py`. The script is still useful as a fallback or for manual inspection.

## Skills referenced (loaded via Skill tool)

| Skill | Used by | Purpose in this skill |
|---|---|---|
| `/ask-review` | Phase 5 PR-Creator sub-agent | Author the comprehensive PR body. Receives all known changes; produces a body with explicit reviewer questions, a per-commit breakdown, files-touched table, risks, follow-ups. Body cap is 50,000 chars (skill invariant). |
| `/do-review` | Phase 3 worker (per round); Phase 7 evaluator (per PR); Phase 8 main agent (direct apply) | Evaluate review feedback against actual code. Decides accepted / rejected / ambiguous per item. The single arbiter in the skill's "never apply review as-is" rule. |

Both skills are documented in their own `SKILL.md` files. This skill's invariants demand they be used as the primary instruments for PR creation and review evaluation; hand-rolling either step is forbidden.

## When to look here vs in this skill's references

| Question | File |
|---|---|
| "How do I commit one concern at a time?" | run-repo-cleanup `diff-walk-discipline.md` |
| "How do I run the per-branch fix loop?" | this skill `per-branch-fix-loop.md` |
| "What's the conventional commit format?" | run-repo-cleanup `conventional-commits.md` |
| "What's the contract for `/codex:review --background`?" | this skill `codex-review-contract.md` |
| "What's the contract for `/codex:resc --background --fresh --model gpt-5.5`?" | this skill `post-pr-review-protocol.md` |
| "How do I verify origin is the fork?" | run-repo-cleanup `fork-safety.md` |
| "How does the classifier decide major vs minor?" | this skill `major-vs-minor-policy.md` |
| "How does the worker decide accepted vs rejected vs ambiguous?" | this skill `review-evaluation-protocol.md` |
| "What's the mission brief skeleton?" | this skill `mission-protocol-integration.md` (and `~/MISSION_PROTOCOL.md`) |
| "What's the worker brief template? PR-creator? Evaluator?" | this skill `parallel-subagent-protocol.md` |
| "How do I split commits without losing work?" | this skill `commit-redistribution.md` (extends `worktree-and-stash.md` Recipe 4) |
| "Where do my session-artifact files go?" | run-repo-cleanup `to-delete-folder.md` |
| "How do I order N worktrees for merge?" | run-repo-cleanup `multi-worktree-merge-order.md` |
| "What does the manifest look like?" | this skill `branch-decomposition-ledger.md` |
| "What if a worker / coordinator / evaluator crashes?" | this skill `failure-recovery.md` |
| "What thoughts should make me re-audit?" | run-repo-cleanup `agent-thinking-steering.md` (general); this skill `thinking-steering.md` (workflow-specific) |
| "How do I write the PR body?" | `/ask-review` skill (via Phase 5 PR-Creator sub-agent) |
| "How do I evaluate a PR's reviews?" | `/do-review` skill (via Phase 7 evaluator sub-agent and Phase 8 main agent) |
| "How do I dispatch the final tidy subagent?" | run-repo-cleanup `post-pr-verification.md` |
| "How do I avoid 'thanks for the great review' phrases?" | run-repo-cleanup `receiving-review-patterns.md` |

## Anti-patterns (in this skill's docs)

If you ever feel the urge to:
- Restate run-repo-cleanup material in this skill's references for "convenience".
- Copy a run-repo-cleanup script and rename it.
- Maintain parallel versions of the same convention.
- Hand-roll the PR body instead of using `/ask-review`.
- Hand-roll review evaluation instead of using `/do-review`.

Don't. Add a row to this index instead, or invoke the canonical skill. The two skills (this one and run-repo-cleanup) plus the two utility skills (`/ask-review`, `/do-review`) must stay in lock-step on shared concerns.

## How this skill extends run-repo-cleanup

| Run-repo-cleanup concept | This skill's extension |
|---|---|
| Phase 0 audit | + `audit-review-state.py` for orphan worktrees / manifests / in-flight jobs |
| Phase 1 diff-walk per concern (dirty tree only) | + `commit-redistribution.md` for splitting committed history |
| Phase 2 commits per concern | + Phase 2 here = spawn N worktrees + push each to fork |
| Phase 3 PRs (open immediately) | + Phase 3 here = parallel inner loop (coordinator + worker) BEFORE PR |
| Phase 4 PR body = self-review | + Phase 5 here uses `/ask-review` skill via PR-Creator sub-agent |
| (no equivalent) | + Phase 6 codex rescue + adaptive 900s wait window |
| (no equivalent) | + Phase 7 evaluator sub-agent uses `/do-review` on multi-source feedback |
| (no equivalent) | + Phase 8 main-agent direct apply via `/do-review` |
| Phase 5 tidy + retire | + `cleanup-worktrees.py` for review-aware worktree removal |

In short: this skill inserts a **review-loop layer** (Phase 3) and a **multi-source post-PR evaluation layer** (Phases 5–8) into run-repo-cleanup's basic flow. Phases 0, 1, 2, 9 still use run-repo-cleanup's primitives directly.

## Skills bundled

The skill ecosystem this workflow depends on:

| Skill | Provides |
|---|---|
| `run-codex-review` (this) | Workflow orchestration, Phase 3 inner loop, Phase 6 wait, Phase 7 evaluation gate, Phase 8 apply |
| `run-repo-cleanup` | Diff-walk, conventional commits, fork-safety, worktree mgmt, merge order, retirement |
| `/ask-review` | Comprehensive PR body authoring |
| `/do-review` | Review evaluation (every gate uses this) |

If any of the four is missing, the workflow degrades:
- Without `run-codex-review`: no orchestration; manual per-branch loops.
- Without `run-repo-cleanup`: must duplicate diff-walk, fork-safety, etc. — discouraged.
- Without `/ask-review`: PR-Creator FAILS per its DoD; brief invariant says "do NOT hand-roll".
- Without `/do-review`: every evaluation gate FAILS per invariant 11; nothing applies.

Verify all four are registered before running the skill.
