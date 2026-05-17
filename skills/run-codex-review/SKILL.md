---
name: run-codex-review
description: Use skill if you are running per-branch codex review fix loops, evaluating multi-bot review feedback, opening a self-review PR, or rescuing a stalled codex review run.
---

# run-codex-review

Deprecated compatibility shim for the legacy `/codex:review` install path. This skill no longer ships its own implementation — it routes the request to the canonical skill that owns the user's actual intent. Do not restore the old runner. Do not invent a new one. Pick the route, then load the target skill.

## When to use this skill

Trigger on any of these phrasings, branch shapes, or environment cues:

- *"run codex review on these branches", "converge these branches with codex", "fix-loop this branch list"*
- *"resume my codex review run", "the codex review crashed mid-run, pick it up", "rescue the review fleet"*
- *"open the PR / hand this off for review"* paired with intent to use codex review afterward
- *"the bots reviewed my PR — Copilot + CodeRabbit + Devin — sort it out"*
- *"go back over the codex review feedback and tell me what to act on"*
- *"installed run-codex-review but the slash command does nothing"* (legacy install-path users)
- A branch list (comma-separated, `branches.txt`, or ≥2 git refs) plus the words "review", "ship", "merge", "close out"
- `codex --version` succeeds AND the user names ≥1 branch and a review keyword

Do NOT use this skill when:

- The user wants to review *someone else's* GitHub PR for merge readiness → load `review-pr`
- The user wants generic non-codex parallel coding fan-out → load `run-codex-2` exec mode directly
- The work is opening a PR with no codex review involved → load `review-self` directly
- The repo is dirty across multiple worktrees with no immediate review intent → load `run-repo-cleanup`

## Routing table — pick the canonical skill, then exit this shim

Match the user's request against one row, surface the route, hand control to the named skill. The shim's job ends after routing.

| User intent | Canonical skill | Entry point |
|---|---|---|
| Per-branch codex review fix loop (branch list + review keyword) | `run-codex-2` review mode | `node skills/run-codex-2/skills/run-codex-2/scripts/run-codex-2.mjs review --branches <list>` |
| Resume / rescue an interrupted codex review run | `run-codex-2` rescue mode | `node skills/run-codex-2/skills/run-codex-2/scripts/run-codex-2.mjs rescue --manifest <path>` |
| Open a PR for the author's own branch (with self-review body) | `review-self` | Load `skills/review-self/skills/review-self/SKILL.md` |
| Triage received feedback from one or many reviewers (human, Copilot, CodeRabbit, Devin, Bito) | `review-feedback` | Load `skills/review-feedback/skills/review-feedback/SKILL.md` |
| Reviewer-side merge-risk review of a PR or diff | `review-pr` | Load `skills/review-pr/skills/review-pr/SKILL.md` |
| Worktrees + branches dirty after a review fleet | `run-repo-cleanup` | Load `skills/run-repo-cleanup/skills/run-repo-cleanup/SKILL.md` |

## Disambiguation rules (load-bearing)

1. **Codex review ≠ PR review.** `run-codex-2` review mode runs `codex exec review --base <base>` per branch and converges via classifier rounds. It does NOT open PRs. PR creation is `review-self`. Reviewer-side merge calls are `review-pr`.
2. **Branch list signal wins for fix loops.** If the user supplies ≥2 branches AND mentions "review/ship/merge/close out", route to `run-codex-2` review — even if the prompt also mentions PRs. PR handoff is a *separate* downstream step routed to `review-self` after convergence.
3. **Multi-bot evaluation ≠ codex convergence.** When the user names third-party reviewers (Copilot, CodeRabbit, Devin, Greptile, Bito) or says "the bots reviewed my PR", the work is feedback triage — route to `review-feedback`. This shim does not own bot-wait timing.
4. **Manifest existence forces rescue.** If `${CLAUDE_PLUGIN_DATA}/state/<slug>-<hash>/run-codex-2/manifest.json` (or the codex-companion fallback under `${TMPDIR:-/tmp}/codex-companion`) exists with non-terminal entries AND the user says "resume / continue / pick up / rescue / prior run", route to `run-codex-2` rescue. Do not overwrite a live manifest.
5. **No restoration of the old runner.** This shim does NOT spawn codex, does NOT write a manifest, does NOT arm a Monitor. Routing is the entire job. The canonical skill owns runtime.
6. **Slash-command boundary.** The vendored `/codex:review` lives inside `run-codex-2` under `scripts/codex-cc/` and is not used by review mode. Review mode uses native `codex exec review`. There is no slash command owned by *this* shim.

## Trigger-precision cues for the canonical route

When `run-codex-2` is the route (review or rescue mode), confirm these environment signals before handing off so the canonical skill does not bounce the request:

- `codex --version` exits 0 (skill assumes 0.130.0+ for `codex exec review` flags)
- `git rev-parse --is-inside-work-tree` succeeds in cwd
- Branch list resolves (comma-list, `branches.txt`, or positionals) — at least 2 refs for review mode
- `codex login status` is a soft probe; bearer-token / managed-companion / proxy auth is allowed even when status reports "Not logged in" (set `USE_CODEX_SKIP_CODEX_AUTH=1` to bypass the bash bootstrap hard-fail)
- For rescue: a manifest path exists under the resolved state dir and `manifest.mode == "review"` for review-fleet rescue

If any cue fails, surface the gap in one line and stop — do not auto-improvise into `run-codex-2` and let it fail downstream.

## Anti-patterns (do not repeat the legacy shim's old mistakes)

- Never restore the old `run-codex-review` runner. The old third-party bot-wait timing constants are retired; bot waits route to `review-feedback`.
- Never spawn `codex` from this shim. Routing is the entire job.
- Never bypass the routing table to "save a step" — wrong-route handoffs lose the user's manifest, branch list, or feedback context.
- Never collapse "codex converges branches" and "PR is ready for review" into one skill call — they are two routes (`run-codex-2` review → `review-self`).
- Never invent a `/codex:resc` or similar slash command. Rescue is a CLI subcommand of `run-codex-2`, not a slash command of this shim.

## Final behavior

Pick the row from the routing table, state the chosen route in one line, and load the canonical skill's `SKILL.md`. The shim itself produces no other artifacts — no manifest, no Monitor, no codex spawn, no PR. The canonical skill owns every downstream contract.
