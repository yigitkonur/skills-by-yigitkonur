# Thinking Steering — this skill

Meta-cognition for the per-branch Codex review-fix-rereview loop, the post-PR review window, and the multi-source evaluation pipeline. Pairs with `skills/run-repo-cleanup/references/agent-thinking-steering.md` (general decompose/order/verify pattern) and `mission-protocol-integration.md` (brief-writing doctrine).

## The cycle

```
audit  →  decompose  →  spawn  →  loop (parallel branches)  →  converge  →
PR (sequential per branch)  →  codex rescue + adaptive wait  →
evaluator (per PR)  →  apply (main-agent direct)  →  merge  →  tidy
```

10 phases. Each follows the same structural pattern: audit → decompose → order → execute → verify → tidy.

## Phase-by-phase questions

Ask these before leaving each phase. If any answer is "I think so", you haven't finished the phase.

| Phase | Question |
|---|---|
| 0 | *What surprises me in the current state? Any orphan worktrees, manifests, or background jobs from a prior session?* |
| 1 | *For each commit on each branch, which concern does it serve? Can each branch be described in one sentence?* |
| 2 | *Does every branch have a worktree AND a remote ref on `origin`? Did `spawn-review-worktrees.py` emit a manifest entry for each?* |
| 3 | *Each branch has a coordinator running the loop. Workers dispatch fresh per round and use `/do-review` before applying. Have I dispatched and stepped back?* |
| 4 | *Which branches are mergeable (DONE)? Which need to surface (CAP-REACHED / BLOCKED / FAILED)? What's the merge order rationale?* |
| 5 | *Is each PR opened by a sub-agent using `/ask-review`? Is body ≤ 50,000 chars? Does it ask explicit reviewer questions?* |
| 6 | *Is codex rescue triggered immediately after PR creation? Is the adaptive wait in progress? Have the bots arrived?* |
| 7 | *Has the evaluator sub-agent decided every item across every source? Are cross-source contradictions flagged?* |
| 8 | *Am I applying the evaluator's accepted subset directly via `/do-review`? Are ambiguous items surfaced (BLOCKED) instead of silently merged?* |
| 9 | *Have I returned to clean state plus the intended delta? Does `audit-review-state.py` exit 0?* |

## Red-flag thoughts (this skill's set)

These are loop / PR / evaluator-specific. The general red-flag list lives in run-repo-cleanup; that one stands too. If any of these fires, **stop and re-run `audit-review-state.py`** and re-read this file.

### Phase 3 inner-loop reds

| Thought | Why it's a red flag |
|---|---|
| "I'll just squash these reviews into one round." | The round-counter is the loop's only stopping criterion. Squashing breaks convergence detection. |
| "I'll re-run review later, after merging." | Codex reviews the branch, not the merged main. Post-merge review is a different question. |
| "Good enough after 3 rounds, ship it." | The classifier + worker evaluator are the arbiters of DONE, not your patience. |
| "Let me skip background mode this once — it's faster inline." | Inline blocks the coordinator. Other branches stall. Defeats the skill. |
| "Let me check progress mid-loop instead of trusting loop-status." | `loop-status.py` reads the manifest. Peeking via filesystem races against worker writes. |
| "I'll have one worker fix two rounds." | Workers are fresh per round. The brief discipline assumes that. |
| "I'll have the coordinator do the work itself." | The coordinator orchestrates; workers act. Separation enforces brief discipline per round. |
| "I'll skip `/do-review` for the obvious items." | Direct-apply violates invariant 11. Every item needs a decision. |
| "The evaluator (worker) is being too strict; let me apply more." | If the worker rejected, it had a reason. Re-litigate via the policy file, not by overriding per round. |
| "I'll merge the cap-reached branch anyway, the issues are minor." | The classifier said major. Worker rejected, accepted, or marked ambiguous. None of those say "merge anyway". |

### Phase 5 PR-creation reds

| Thought | Why it's a red flag |
|---|---|
| "I'll just open the PR myself instead of dispatching a sub-agent." | Invariant: PR creator MUST be a sub-agent. The main agent never opens PRs in this workflow. |
| "I'll hand-roll the body — `/ask-review` is overhead." | Invariant: body MUST come from `/ask-review`. Hand-rolling produces shallower bodies. |
| "The body is over 50k, let me trim by removing the per-commit section." | Trim via `/ask-review`'s flags, not by deleting useful content. If it's still too long, the PR is too wide — split. |
| "I'll skip the explicit reviewer questions; the body is comprehensive enough." | The user's spec says questions are critical. Without them, the PR doesn't "ask for review" — it just describes. |
| "Let me open this on upstream as a courtesy." | Never. Fork-only. Invariant. |

### Phase 6 wait-window reds

| Thought | Why it's a red flag |
|---|---|
| "Skip the wait, merge fast." | The wait is the value. The whole skill exists to harvest reviewer feedback. |
| "Wait less than 900s by default — the bots are fast." | Bots that arrive at minute 13 are missed; their feedback is lost. 900s is the empirically-calibrated minimum. |
| "Wait more than the total cap." | Indefinite wait = dead session. The cap is the safety. |
| "Run codex rescue inline (not `--background`)." | Blocks the agent for 1–5 min. Defeats the parallel orchestration. |
| "Let me trigger codex rescue twice for extra coverage." | One rescue per PR. Twice is wasted compute and confuses the gather logic. |

### Phase 7 evaluator reds

| Thought | Why it's a red flag |
|---|---|
| "Trust copilot's items blindly because copilot is usually right." | Copilot is a reviewer like any other. Evaluator first. Always. |
| "The evaluator is overhead; just apply what the bots say." | The evaluator is the value. Without it, false positives ship. |
| "Auto-resolve the cross-source contradiction by picking the more recent." | Cross-source contradictions are information. Mark ambiguous; surface for human. |
| "Skip items the evaluator marked rejected — they're probably real." | The evaluator decided. Override via the policy file or by editing the brief, not by silently re-flagging. |
| "Let me dispatch a second evaluator for sanity-check." | One evaluator per PR. Two evaluators = two opinions = ambiguity all the way down. Trust the brief. |

### Phase 8 apply reds

| Thought | Why it's a red flag |
|---|---|
| "Let me dispatch a sub-agent for the apply step too." | Phase 8 is main-agent direct. The evaluator's answers are in main agent's context — apply directly. Sub-agent for apply re-loads context unnecessarily. |
| "Apply the ambiguous items 'just in case'." | Ambiguous means human-in-the-loop. Applying them silently is worse than not applying. |
| "Re-trigger Codex review after apply — paranoia." | Phase 8's commits are post-evaluator. Codex would re-flag items the evaluator already decided. Don't re-loop. |
| "Open a fresh PR for every accepted item." | The rubric in `post-pr-review-protocol.md` says: in-place by default; new PR only for divergent or scope-creep cases. |

### Cross-phase universals

| Thought | Why it's a red flag |
|---|---|
| "I'll start fresh and ignore the prior session's manifest." | Orphan worktrees, in-flight reviews, half-rewritten branches. The prior session's debris doesn't disappear by ignoring it. |
| "Let me peek at the worktree to see if the sub-agent is making progress." | The manifest is the heartbeat. Peeking via filesystem races against the sub-agent's writes. |
| "I'll write the brief later — this dispatch is simple." | The brief is the lever. Even simple dispatches benefit from the discipline. |
| "I can skip the failure protocol — the agent will figure it out." | Silent failure is the only unacceptable failure. Brief without failure protocol invites it. |
| "Soft DoD ('clean code', 'reasonable performance') — agents understand." | Banned. Two reviewers would interpret these differently. BSV only. |

## When to stop and re-audit

Same triggers as run-repo-cleanup, plus:

- Any coordinator has been at the same `rounds` count for > `--stale-minutes`.
- Any branch's `last_classifier_summary.major_n` has been the same number for ≥3 rounds (oscillation — possible BLOCKED).
- Any push fails with non-fast-forward (someone or something else is on the branch).
- Any `gh pr list --repo <upstream> --author @me` is non-empty (fork-safety leak).
- The manifest's `branches` count diverges from `git worktree list`'s `*-wt-*` count.
- A PR has been open more than 30 min without a Phase 7 evaluator dispatch (the wait window stuck).
- Codex rescue has been "running" past the total cap with no result.
- The evaluator's output JSON is missing from `<rounds-dir>` after a Phase 7 dispatch.
- Phase 8 commits don't match Phase 7's accepted items (drift between decision and application).

Re-audit costs 30 seconds and snaps you back to ground truth.

## Escalation — when to ask the user

- Two branches' reviews contradict and there's no clean way to resolve via splitting.
- The classifier policy keeps mis-classifying a recurring item and no edit feels right.
- A coordinator or worker crashed with no recoverable state.
- A `BLOCKED` branch's `terminal_reason` requires architectural input.
- Codex rescue produces output the evaluator can't parse (schema drift in the wrapper).
- An external bot is missing that the user expected (greptile not installed; devin not authorized).
- Anything where moving forward without confirmation could leak to upstream or destroy work.

Asking is not failure. Wrong moves on these are irreversible.

## The decompose → step back → watch reflex

The single most important shift from `run-repo-cleanup`'s flow to this one: **after Phase 2, the main agent stops editing files** but stays in the driver's seat for orchestration. Phase 3: main agent runs codex review wrappers, evaluates major items via `Skill(do-review)` in own context, dispatches per-round Appliers. Phase 5: main agent dispatches PR-Creators; waits. Phase 7: main agent dispatches Evaluators; waits. Phase 8: main agent applies the evaluator's accepted subset directly. Editing inside worktrees is sub-agent territory; orchestration is main agent's territory throughout.

If you find yourself opening a worktree to "check on it" or "fix something quickly", you've already broken the protocol. The sub-agent's writes and yours can race. The classifier's exit code, the worker's handback, the evaluator's JSON — those are the only signals you should be acting on.

Stay out. Trust the sub-agents. Read `loop-status.py`.

## The brief discipline reflex

Before every Agent dispatch, run the brief discipline checklist (in `parallel-subagent-protocol.md`):

- [ ] Context block names files to read with reasons.
- [ ] Mission Objective is one observable outcome.
- [ ] Hard constraints are true non-negotiables.
- [ ] Research & Tool Guidance describes capabilities, not steps.
- [ ] DoD criteria are Binary, Specific, Verifiable.
- [ ] No soft language.
- [ ] Verification steps map 1:1 to DoD.
- [ ] Failure Protocol present.
- [ ] Handback structure present.
- [ ] Ceilings have release valves; no floors.
- [ ] Brief ≤ 5,000 words.

If any unchecked, revise. Cost: 1 minute. Saves: hours of wrong work.

## Forbidden inventions

Do **not**, under any phase, propose:

- **A "smoke test" or pilot before Phase 3 fan-out.** The skill prescribes parallel dispatch from round 1. A smoke test is not in the workflow. If the codex plugin is unavailable, you find out at dispatch time and surface FAILED — you do not pre-test.
- **Re-introducing a Coordinator sub-agent layer.** That pattern was tried; it does not work in production (long-lived sub-agents drift, depth-2 dispatch is brittle). Main agent IS the coordinator across all branches — see `parallel-subagent-protocol.md` "Coordinator role". If your instinct says "I should dispatch a coordinator subagent per branch", you are recreating the old pattern.
- **Writing a custom MISSION_PROTOCOL brief inline** rather than instantiating one of the four templates in `parallel-subagent-protocol.md` (Coordinator / Worker / PR-Creator / Evaluator). If the brief feels off, fix the *template*; do not bypass it.
- **A shim, wrapper, or fallback for any slash command.** `/codex:review`, `/codex:resc`, `/ask-review`, `/do-review` either exist (use them via `Skill(...)`) or do not (surface and stop). There is no third path.
- **Confirming a pinned default with the user.** Defaults in the Pinned Defaults table are pinned. Auto-detect (repo mode, manifest path) or proceed. Only ask when a destructive choice is genuinely ambiguous and not derivable from local state.
- **Reading `scripts/run-codex-review.py` or `scripts/trigger-codex-rescue.py` looking for the "real" invocation.** The wrappers ARE the active path: `run-codex-review.py` is what sub-agents call (it bridges to `codex-companion.mjs review --json` because `/codex:review` is `disable-model-invocation: true` for sub-agents). For main agent, `/codex:resc` is the slash command for Phase 6. Either way, do not invent a parallel script.
- **Multi-question opening confirmations** ("OK to proceed with B1–B5? Max rounds 20? Codex CLI ready?"). The user's first prompt is the authorization. Detect what's detectable and execute.
- **Pre-flight environment probing for tool reachability.** No `codex login status`, `codex --version`, `codex doctor`, `ls .../node_modules`, `command -v <tool>`, or other "is the environment ready" probes. Such probes assume a default configuration (one specific auth path, one package manager, one project layout) that often doesn't match the user's actual setup — users routinely run with custom providers, alternate auth, or atypical layouts where the probe reports "broken" while the real workflow runs fine. The slash-command dispatch and the worker's own validation step are the only valid tests; if they truly fail you hand back FAILED with `terminal_reason` and surface to the user. **Never** present a multi-option resolution menu (A/B/C…) to fix an environment configuration the user did not ask you to touch.
- **Bridging plugin-internal scripts with a "small shim".** Shims are forbidden by invariant 17. The right path per surface is in the SKILL.md invocation matrix.
- **End-of-phase option menus** ("Full Phase 5-8 / Phase 5 only / Foundation only / Pause"). The user authorized full flow at skill invocation. Proceed phase-to-phase without checkpoint. (See SKILL.md "Authorization rule".)
- **Cost-and-time paralysis prefaces** ("multi-hour, multi-thousand-token operation"). The user knows; the user authorized. Stating it again is stalling, not transparency. Just execute.
- **Verbose end-of-phase state tables.** The Final Deliverable in Phase 9 is the place for per-branch summaries. Mid-flight, one sentence: "Phase X complete; entering X+1."
- **Inventing terminal states** like `DONE-PRAGMATIC`, `READY-ENOUGH`, `MOSTLY-DONE`. The taxonomy is fixed: `DONE`, `CONVERGED-AT-CAP`, `CAP-REACHED`, `BLOCKED`, `FAILED`. If reality doesn't fit, surface a real `BLOCKED` with `terminal_reason`.
- **`/do-review` framing in worker briefs.** Empirically causes 100% decision-only failure. Decisions are made by main agent before dispatch; workers are appliers.
- **Hand-rolled bash polling loops** (`until grep -qE "Reviewer (finished|failed)" …`) for codex review status. Use the wrapper script's exit code; use Monitor for terminal markers; use Bash `run_in_background` for the dispatch itself. Polling loops are a sign the wrapper contract is broken — fix the wrapper, don't paper it over.

These inventions cost the user 10–15 minutes per session in the wild. Don't.

## The bottom line

The skill's commands and scripts are mechanical. What separates a good run from a bad one is **how the agent thinks about the parallel state**: trusting the manifest, not memory; trusting the classifier and evaluator, not judgement; staying out of sub-agent worktrees while they work; writing comprehensive briefs that make sub-agents great; never applying review feedback without `/do-review` first. Audit → decompose → spawn → step back → watch → PR → wait → evaluate → apply → merge → tidy. Reflex.

> *Context → Gravity → Standards → Verification → Trust the path, own the destination.*
