---
name: evaluate-code-review
description: Use skill if you are evaluating code review feedback — PR comments from humans or bots, multi-agent review consolidation, or auditing a session's changes against a review doc.
---

# Evaluate Code Review

The opposite side of `request-code-review`. You have feedback in hand — from a human reviewer, one or more AI review bots, a previous self-review, or a markdown audit doc — and need to decide what to act on, what to push back on, and what to ask about. Discipline: **verify before implementing, technical correctness over social comfort, no performative agreement.**

## Trigger boundary

Use this skill when the task is to:

- evaluate review comments on a GitHub PR (single or multiple reviewers)
- consolidate feedback from multiple AI reviewers (Copilot + CodeRabbit + Devin + ...) on the same PR
- audit earlier messages in the current conversation — "go back and check the reviewer's notes", "self-eval what we just shipped"
- read a markdown review/audit doc (e.g. `review-notes.md`, `audit.md`) and produce an action plan
- handle ambiguous input: the user said "check the review" without pointing at a specific source → default to scanning prior messages, then PR comments on the current branch

Prefer another skill when:

- doing the review yourself (reviewer-side) → `review-pr`
- preparing a PR for review (author-side) → `request-code-review`
- tidying a dirty tree → `run-repo-cleanup`
- debugging runtime behavior via tools → `debug-*`

## Non-negotiable rules (discipline)

1. **Verify before implementing.** Do not start editing until you have confirmed the feedback against the actual code. Obra's rule: "check if breaks existing functionality; check if reviewer understands full context; check legacy/compatibility reasons."
2. **No performative agreement.** The phrases in `references/voice.md` are forbidden. If you catch yourself about to type "You're absolutely right" or "Thanks for catching that" — stop and state the fix instead. See `references/rationalizations.md` for why agents keep writing them anyway.
3. **Understand what was reviewed, from the ground truth.** Follow the fallback chain in `references/understand-changes.md`: commits → Edit/Write tool outputs → Bash rm/mv history. Do not trust the reviewer's description of "the changes" — they may be wrong.
4. **Always dispatch an Explore subagent for independent analysis.** Self-contained prompt, no session-history leakage. See `references/subagent-dispatch.md` for the template.
5. **Push back when the reviewer is wrong** — with technical reasoning, not defensiveness. "Can't verify X without Y; should I investigate / ask / proceed?" is a valid push-back.
6. **Cluster before acting on multi-agent feedback.** When 2+ reviewers comment on the same file+line, cluster them into a single item before evaluating. See `references/multi-agent-consolidation.md`.
7. **One item at a time during implementation.** Fix → test → next. Not "fix all four at once, run the suite once".
8. **Implementation order:** blocking (breaks, security) → simple (typos, imports) → complex (refactoring, logic). Never the other order.

## Input modes

The skill handles three input modes. Detect the mode from the user's phrasing; if genuinely ambiguous, check all three sources and report what was found.

| Mode | Trigger phrasing | Source |
|---|---|---|
| **PR mode** | "the review comments on PR #42", "what do the bots say on my PR", "address the review" | `gh pr view <N> --comments`, thread replies via `gh api` |
| **Session-audit mode** | "audit what we just did", "check the review notes from earlier", "go back and evaluate the reviewer's feedback" (without PR context) | Previous messages in this conversation |
| **Markdown-doc mode** | "read review.md and give me an action plan", "the reviewer's notes are in audit.md" | Named file(s) on disk |

**Ambiguous trigger** (user just says "evaluate the review" or "check what the reviewer said"): scan prior messages first, then `gh pr view` on the current branch, then look for obvious markdown candidates (`review*.md`, `audit*.md`, `feedback*.md`) in the working directory. Report what was found before proceeding.

## Required workflow

### 1. Identify the input mode and surface the feedback

State which mode is active. Extract every piece of review feedback as a flat list of items. Do not paraphrase yet — capture the verbatim text, its source (which reviewer, which comment ID, which line of which file in which message), and any code-range metadata.

For each item, record: `{source, file?, line?, severity_hint?, verbatim_text}`.

### 2. Understand what was actually reviewed (ground truth)

Before evaluating any feedback, reconstruct the set of changes the reviewer *should have been* reviewing. Use the fallback chain:

1. **If the current branch has commits ahead of the base branch** → `git log origin/main..HEAD` + `git diff origin/main...HEAD`. This is the gold standard.
2. **If no commits but the session has Edit/Write tool calls** → walk back through the conversation, collect every successful Edit and Write call's target file path. This reconstructs "what files the author changed, even without commits."
3. **If the session has Bash calls like `rm`, `mv`, `mkdir`, `cp`** → these imply file operations not visible via diff. Include them.
4. **If none of the above** → explicitly state the ground truth is uncertain before evaluating any feedback.

See `references/understand-changes.md` for the extraction recipes.

### 3. Dispatch an Explore subagent for independent evaluation

**Always.** Even for a single-item review. The subagent reads the code without your session's bias and returns its own assessment of each feedback item's correctness.

Per-subagent prompt is self-contained (no "as we discussed earlier", no "the user wants X", no session references). The subagent gets:

- The ground-truth change set (from Step 2)
- The flat feedback-item list (from Step 1)
- A pointer to this skill's `references/verification.md` for the lens

See `references/subagent-dispatch.md` for the exact prompt template.

The subagent returns: per-item `{verdict: correct | incorrect | unverifiable, evidence: file:line + reasoning, severity: critical | important | minor}`.

### 4. Consolidate multi-source feedback

If the input is a single reviewer, skip clustering and go to Step 5.

If 2+ reviewers (e.g., Copilot + CodeRabbit on the same PR, or human + two AI bots):

- **Line-range clustering** — group items that touch the same file + overlapping line range. A "+/-5 lines" fuzz is typical.
- **Deduplicate** — when two reviewers flag the same concern, merge into one item with both sources cited.
- **Resolve conflicts** — if two reviewers disagree, surface the disagreement explicitly in the action plan; do not silently pick one.
- **Discard noise** — obvious false positives (e.g., a bot flags a dependency it doesn't understand). Tag as "dismissed with reason".

See `references/multi-agent-consolidation.md`.

### 5. Evaluate each item against the codebase

For every feedback item (or consolidated cluster), combine the subagent's verdict with your own verification. Each item ends with one of:

- **ACCEPT** — the feedback is correct and worth acting on
- **PUSHBACK** — the feedback is wrong; respond with technical reasoning
- **CLARIFY** — the feedback is unclear or you lack information to verify; ask
- **DEFER** — correct but out of scope for this PR; log as follow-up
- **DISMISS** — noise, unambiguously wrong, or the reviewer lacks context

Verification lens (from google-gemini's 7-pillar and obra's pushback criteria):

| Check | Question |
|---|---|
| Correctness | Would this break existing functionality? |
| Scope (YAGNI) | Is the suggested feature actually used? Grep first. |
| Stack fit | Is this correct for THIS codebase's stack? |
| Compat | Legacy/compat reasons for the current implementation? |
| Context | Does the reviewer have the full context? |
| Architectural | Does this conflict with a prior architectural decision? |

See `references/verification.md` for the full lens.

### 6. Produce the action plan

Output format depends on mode:

- **PR mode** — post thread replies via `gh api repos/{o}/{r}/pulls/{pr}/comments/{id}/replies` for ACCEPT/PUSHBACK/CLARIFY. Top-level comment only for summary. Never reply with pure gratitude.
- **Session-audit mode** — markdown action plan as conversation output. Group by verdict.
- **Markdown-doc mode** — markdown action plan written to a file next to the source doc, e.g. `review.md` → `review-action-plan.md`.

See `references/action-plan-output.md` for the exact formats.

### 7. Implement the accepted items

Only after the action plan is produced and the user (or caller) has approved the plan, if the flow calls for implementation:

- **Order**: blocking (breaks, security) → simple (typos, imports) → complex (refactoring, logic)
- **Discipline**: one item at a time, test each before the next
- **Reply**: after implementing an item, reply in the PR thread (PR mode) or update the action plan (markdown mode) with "Fixed. <what changed>" — no gratitude.

If implementation is *not* requested in the user's ask ("just evaluate; I'll implement myself"), stop after Step 6 and hand over the action plan.

## The voice discipline (critical)

Obra's rule: **No performative agreement.** Actions speak; the diff says "you heard the feedback." Full forbidden list + alternatives in `references/voice.md`. Pressure-case counters: `references/rationalizations.md`.

Quick hits:

| Instead of | Use |
|---|---|
| "You're absolutely right!" | "Fixed. <description>" or just the change |
| "Great point!" | Acknowledge the technical content, not the point |
| "Thanks for catching that!" | "Fixed in `src/foo.ts:42`." |
| "Let me implement that now" (before verifying) | "Checking the codebase first — <specific check>." |
| "I'll address all six items" (without understanding them) | "Understood items 1, 2, 3, 6. Need clarification on 4 and 5 before proceeding." |

If you catch yourself about to write "Thanks" — DELETE IT. State the fix instead.

## Using `gh` for multi-agent review

When the feedback source is a PR with multiple AI reviewers (Copilot, CodeRabbit, Devin, Bito, Greptile), use `gh` to pull all comments before evaluation. The consolidation logic is in `references/multi-agent-consolidation.md`; the `gh` mechanics are in `references/gh-review-workflow.md`.

Key commands (full recipes in the reference):

```bash
# All top-level PR reviews (the summary comments)
gh pr view <N> --repo <o>/<r> --json reviews

# All inline review comments (the file+line comments)
gh api repos/<o>/<r>/pulls/<N>/comments

# All PR discussion (top-level, non-review comments)
gh api repos/<o>/<r>/issues/<N>/comments

# Reply in a thread
gh api repos/<o>/<r>/pulls/<N>/comments/<id>/replies \
  --method POST --field body="Fixed. <description>."
```

## Output contract

Unless the user wants a different format, produce artifacts in this order:

1. Input mode declaration (after Step 1)
2. Ground-truth change summary (after Step 2) — which fallback was used
3. Explore-subagent dispatch report (after Step 3) — subagent ID + summarized verdicts
4. Consolidation table (after Step 4) — only if multi-source; item ID → sources cited
5. Per-item evaluation (after Step 5) — ACCEPT / PUSHBACK / CLARIFY / DEFER / DISMISS with reasoning
6. Action plan output (after Step 6) — mode-specific
7. Implementation report (after Step 7) — only if implementation was requested

## Do this, not that

| Do this | Not that |
|---|---|
| verify each suggestion against the actual code | implement on faith because "the reviewer is probably right" |
| dispatch an Explore subagent with a self-contained prompt | ask the subagent "remember what we were just working on?" |
| cluster multi-agent feedback by file+line range | treat each bot's comments as a separate todo list |
| reconstruct what changed from commits or tool outputs | trust the reviewer's description of "the changes" |
| push back with technical reasoning when feedback is wrong | accept everything to avoid conflict |
| reply in the comment thread for inline comments | reply at top-level PR comment (wrong channel) |
| state exactly what you verified | claim you checked something you didn't |
| ask for clarification when an item is ambiguous | implement a partial understanding |
| one item at a time, test each | batch-fix, batch-test, and miss regressions |

## Guardrails and recovery

- Do not write "Thanks for the review" / "Thanks for catching that" / "Great point". Delete mid-sentence if you catch it.
- Do not implement before verifying. The pre-implement check is not optional.
- Do not dispatch subagent prompts that reference "earlier in this conversation" — they break as self-contained units.
- Do not silently pick a side when two reviewers conflict. Surface the conflict.
- Do not dismiss bot feedback without stating the reason.
- Do not capitulate on push-back to save time. Technical correctness over comfort.

Recovery moves:

- **Can't verify a suggestion** → state the limitation: "Can't verify without running X; should I investigate / ask / proceed?"
- **Reviewer and prior architectural decision conflict** → stop, discuss with the human first; do not silently re-decide
- **Pushed back, then realized you were wrong** → correction template: "You were right — I checked <X> and it does <Y>. Implementing." No long apology.
- **Ambiguous input with no PR / no messages / no markdown** → report the gap explicitly; ask the user which source to evaluate

## Reference routing

| File | Read when |
|---|---|
| `references/voice.md` | Writing any response — the forbidden-phrases list, the "Fixed." alternatives, pushback templates |
| `references/understand-changes.md` | Reconstructing what was reviewed — commits → tool trail → bash history fallback chain |
| `references/verification.md` | Evaluating a specific feedback item against the codebase; the 6-check verification lens |
| `references/subagent-dispatch.md` | Writing the Explore subagent prompt — self-contained template |
| `references/multi-agent-consolidation.md` | Combining feedback from 2+ reviewers; line-range clustering; conflict resolution |
| `references/gh-review-workflow.md` | Pulling PR comments via `gh`; thread replies; PR-discussion vs. review-comment channels |
| `references/action-plan-output.md` | Formatting the action plan — per mode (PR / session / markdown-doc) |
| `references/rationalizations.md` | RED-baseline excuses that bypass the verify-before-implement discipline; counters |

## Final checks

Before declaring done, confirm:

- [ ] input mode declared and matches the user's ask
- [ ] ground truth reconstructed with a named source (commits / tool trail / bash / uncertain)
- [ ] Explore subagent dispatched with a self-contained prompt (no session references)
- [ ] if multi-source: line-range clustering applied, conflicts surfaced
- [ ] every feedback item has a verdict (ACCEPT / PUSHBACK / CLARIFY / DEFER / DISMISS) with reasoning
- [ ] output matches the action-plan format for the mode
- [ ] zero forbidden phrases in the response (grep-checked)
- [ ] if PR mode: inline replies went in the correct thread, not at top level
- [ ] if implementation ran: order was blocking → simple → complex, one at a time

Quick orphan check:

```bash
for f in $(find references -name '*.md' -type f); do grep -q "$(basename $f)" SKILL.md || echo "ORPHAN: $f"; done
```
