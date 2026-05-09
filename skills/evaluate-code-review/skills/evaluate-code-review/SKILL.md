---
name: evaluate-code-review
description: Use skill if you are triaging received review feedback - PR comments, multi-bot reviews, markdown audit docs, or earlier session feedback - into accept/pushback/clarify/defer/dismiss.
---

# Evaluate Code Review

Feedback is already in hand from a human reviewer, one or more AI bots (Copilot, CodeRabbit, Devin, Bito, Greptile), a prior self-review, or a markdown audit doc. The job is triage, not authoring. Discipline: **verify before implementing, technical correctness over social comfort, no performative agreement.**

## When to use this skill

Trigger when the user is:

- *triaging received PR comments on a GitHub pull request* ("evaluate the review", "address the comments on PR #42", "what do the bots say on my PR")
- *consolidating feedback from multiple reviewers* on the same PR ("Copilot and CodeRabbit disagree", "merge what the three reviewers said", "cluster the bot comments")
- *auditing earlier review feedback in this conversation* ("go back and check the reviewer's notes", "self-eval the review comments from earlier")
- *converting a markdown review/audit doc into an action plan* (`review.md`, `audit.md`, `feedback.md`, `*-review-notes.md`)
- *handling ambiguous "check the review" prompts* with no source pointer — scan prior messages, then PR comments on the current branch, then markdown candidates
- *deciding whether to implement, push back, or defer* a specific suggestion against the actual code
- *replying in PR threads* with technical reasoning rather than gratitude

Do **NOT** use this skill when:

- *performing the review yourself* (reviewer-side, producing findings) → use `do-review`
- *preparing a PR for review* (author-side, asking for feedback) → use `ask-review`
- *checking what work is done vs. claimed done* with no review feedback in hand → use `check-completion`
- *running `orchestrate-codex` per-branch convergence loops* — major-finding evaluation routes through `do-review`, not this skill

## Non-negotiable rules

| # | Rule | Why |
|---|---|---|
| 1 | **Verify before implementing.** Confirm each suggestion against the actual code before any edit. | Reviewers (human and bot) are sometimes wrong, stale, or missing context. |
| 2 | **No performative agreement.** No gratitude, praise, apology, or agreement-before-verification. The diff is the acknowledgment. | See `references/voice.md` for forbidden phrases and `references/rationalizations.md` for why agents keep writing them anyway. |
| 3 | **Reconstruct ground truth before reading feedback.** Use the fallback chain in `references/understand-changes.md`: commits → tool-trail → bash history → uncertain. | Reviewer descriptions of "the changes" can be wrong. |
| 4 | **Always dispatch an Explore subagent for independent analysis.** Self-contained prompt — no session-history leakage. See `references/subagent-dispatch.md`. | Parent context biases verdicts; a clean reader catches bias. |
| 5 | **Cluster multi-source feedback before evaluating.** When 2+ reviewers comment on the same file+line, cluster into one item before triage. See `references/multi-agent-consolidation.md`. | Treating duplicates as separate todos triples the work and hides conflicts. |
| 6 | **One item at a time during implementation.** Fix → test → next. | Batch-fix + batch-test misses regressions. |
| 7 | **Implementation order: blocking → simple → complex.** Breakage and security first; typos and imports next; refactors last. | Prevents merge-blocking work from waiting behind cosmetic edits. |
| 8 | **Push back when the reviewer is wrong.** Technical reasoning, not defensiveness or capitulation. | Correctness over comfort. |
| 9 | **Evidence wins over source authority.** Human context, bot severity labels, and repeated bot agreement are signals, not verdicts. | All sources go through the same verification lens. |

## Source confidence model

| Source | Carries | Caveat |
|---|---|---|
| Human reviewers | Product, rollout, architectural context | Line comments may be stale or based on an older commit |
| AI bots (Copilot, CodeRabbit, Devin, Bito, Greptile) | Broad coverage, consistent pattern matching | Severity labels are `severity_hint` only |
| Self-review / markdown docs | Useful prior analysis | Often missing current code state |

**Same truth standard for every source.** Source type affects parsing, triage priority, and reply channel — not correctness. Tie-breakers when code evidence is equal: human product/architecture context. Repeated bot agreement raises priority but never decides correctness.

## Input modes

Detect the mode from the user's phrasing. If genuinely ambiguous, check all three sources and report what was found.

| Mode | Trigger phrasing | Source |
|---|---|---|
| **PR mode** | "the review comments on PR #42", "what do the bots say on my PR", "address the review" | `scripts/parse-pr-comments.sh --repo <owner/name> --pr <N> --out <dir>`, then thread replies via `gh api`. See `scripts/parse-pr-comments.md`. |
| **Session-audit mode** | "audit what we just did", "check the review notes from earlier", "go back and evaluate the reviewer's feedback" | Previous messages in this conversation |
| **Markdown-doc mode** | "read review.md and give me an action plan", "the reviewer's notes are in audit.md" | Named file(s) on disk |

**Ambiguous trigger** ("evaluate the review" with no source): scan prior messages first, then `gh pr view` on the current branch, then look for `review*.md`, `audit*.md`, `feedback*.md` in the working directory. Report what was found before proceeding.

## Required workflow

### Step 1 — Identify the input mode and surface the feedback

State which mode is active. Extract every piece of review feedback as a flat list of items. Capture verbatim text — do not paraphrase yet — plus source, location, and code-range metadata.

For each item, record: `{id?, channel?, source, source_type, file?, line?, original_line?, commit_id?, severity_hint?, verbatim_text}`.

For PR mode, run `scripts/parse-pr-comments.sh` to fetch all three GitHub feedback channels (top-level reviews, inline review comments, PR-discussion comments) before evaluating. See `scripts/parse-pr-comments.md` for invocation and output schema.

### Step 2 — Reconstruct ground truth

Before evaluating any feedback, reconstruct the change set the reviewer *should have been* looking at. Fallback chain:

1. **Branch has commits ahead of base** → `git log origin/main..HEAD` + `git diff origin/main...HEAD`. Gold standard.
2. **No commits but session has Edit/Write calls** → walk the conversation, collect every successful Edit/Write target path.
3. **Session has Bash `rm`/`mv`/`mkdir`/`cp` calls** → include them; they imply file ops not visible via diff.
4. **None of the above** → state that ground truth is uncertain before evaluating any feedback.

See `references/understand-changes.md` for the full extraction recipes.

### Step 3 — Dispatch an Explore subagent

**Always.** Even for a single-item review. The subagent reads the code without parent-session bias.

The prompt is self-contained: no "as we discussed earlier", no "the user wants X", no session references. Hand the subagent:

- The ground-truth change set (from Step 2)
- The flat feedback-item list (from Step 1)
- A pointer to `references/verification.md` for the lens

The subagent returns per-item: `{verdict: correct | incorrect | unverifiable, evidence: file:line + reasoning, severity: critical | important | minor}`.

See `references/subagent-dispatch.md` for the exact prompt template.

### Step 4 — Consolidate multi-source feedback

If only one reviewer, skip to Step 5.

For 2+ reviewers (e.g., Copilot + CodeRabbit on one PR, or human + two AI bots):

- **Line-range clustering** — group items that touch the same file + overlapping line range (±5 lines is typical fuzz)
- **Deduplicate** — when two reviewers flag the same concern, merge into one item citing both sources
- **Resolve conflicts** — if two reviewers disagree, surface the disagreement explicitly; never silently pick one
- **Discard noise** — obvious false positives get tagged as "dismissed with reason"

For PR JSONL snapshots, run `scripts/cluster-feedback.py --input normalized.jsonl --output clusters.json` before manual verification. See `scripts/cluster-feedback.md` for inputs/outputs and `references/multi-agent-consolidation.md` for the clustering and conflict-resolution policy.

### Step 5 — Evaluate each item against the codebase

For every feedback item (or consolidated cluster), combine the subagent's verdict with parent verification. Each item ends with one verdict:

| Verdict | Meaning |
|---|---|
| **ACCEPT** | Feedback is correct and worth acting on |
| **PUSHBACK** | Feedback is wrong; respond with technical reasoning |
| **CLARIFY** | Feedback is unclear or evidence is missing; ask |
| **DEFER** | Correct but out of scope for this PR; log as follow-up |
| **DISMISS** | Noise, unambiguously wrong, or reviewer lacks context |

Verification lens (6 checks):

| Check | Question |
|---|---|
| Correctness | Would this break existing functionality? |
| Scope (YAGNI) | Is the suggested feature actually used? Grep first. |
| Stack fit | Is this correct for THIS codebase's stack? |
| Compat | Legacy/compatibility reasons for the current implementation? |
| Context | Does the reviewer have the full context? |
| Architectural | Does this conflict with a prior architectural decision? |

See `references/verification.md` for the full lens with worked examples.

### Step 6 — Produce the action plan

Output format depends on mode:

- **PR mode** — when PR replies are authorized, post thread replies via `gh api repos/{o}/{r}/pulls/{pr}/comments/{id}/replies` for ACCEPT/PUSHBACK/CLARIFY items. Top-level only for the summary. Never reply with pure gratitude. Mechanics in `references/gh-review-workflow.md`.
- **Session-audit mode** — markdown action plan as conversation output, grouped by verdict.
- **Markdown-doc mode** — markdown action plan written next to the source doc (e.g. `review.md` → `review-action-plan.md`).

Every action plan includes a decision register. Each item carries: stable item ID, source(s), source type(s), location and `commit_id` when available, verbatim reviewer text, verdict, evidence, planned action, and implementation status when implementation was requested.

See `references/action-plan-output.md` for the exact format per mode.

### Step 7 — Implement the accepted items (only if authorized)

- If the user asked only to evaluate, stop after Step 6 and hand over the action plan.
- If the user asked to evaluate and implement, produce the action plan first, then proceed under that original authorization.
- Destructive or externally visible actions (PR pushes, comment posts, deploys, deletes) require explicit authorization every time.
- **Order:** blocking (breaks, security) → simple (typos, imports) → complex (refactoring, logic).
- **Discipline:** one item at a time, test each before the next.
- **Reply:** after implementing an item, reply in the PR thread (PR mode) or update the action plan (markdown mode) with `Fixed. <what changed>.` — no gratitude.

After implementation, report: accepted item IDs fixed, files changed, commit SHA(s) when committed, validation command and exact result, remaining CLARIFY/DEFER/PUSHBACK/DISMISS items, and PR reply status by thread in PR mode.

## Voice discipline

**No performative agreement.** Actions speak; the diff is the acknowledgment. Phrase-level rules live in `references/voice.md` (forbidden phrases, "Fixed." alternatives, pushback templates). Pressure-scenario excuses and counters live in `references/rationalizations.md`.

Short version: avoid gratitude, praise, apology, and agreement-before-verification. Accept correct feedback by stating the fix. Push back with evidence. Ask for clarification only when evidence is genuinely insufficient.

## Multi-bot PR shortcuts (`gh`)

When the source is a PR with multiple AI reviewers, pull all comments before evaluation. Full recipes in `references/gh-review-workflow.md`. Headline commands:

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
5. Decision register (after Step 5) — item ID, sources, source types, location, commit_id, verbatim text, verdict, evidence, planned action, implementation status
6. Action plan output (after Step 6) — mode-specific
7. Implementation report (after Step 7) — fixed IDs, files changed, commit SHA(s), validation result, remaining items, PR reply status

## Do this, not that

| Do this | Not that |
|---|---|
| verify each suggestion against the actual code | implement on faith because "the reviewer is probably right" |
| dispatch an Explore subagent with a self-contained prompt | ask the subagent "remember what we were just working on?" |
| cluster multi-agent feedback by file+line range | treat each bot's comments as a separate todo list |
| reconstruct what changed from commits or tool outputs | trust the reviewer's description of "the changes" |
| push back with technical reasoning when feedback is wrong | accept everything to avoid conflict |
| reply in the comment thread for inline comments | reply at top-level PR comment (wrong channel) |
| state exactly what was verified | claim a check that did not run |
| ask for clarification when an item is ambiguous | implement a partial understanding |
| one item at a time, test each | batch-fix, batch-test, miss regressions |

## Guardrails and recovery

Do not:
- write gratitude, praise, apology, or agreement-before-verification — delete mid-sentence if it appears
- implement before verifying — the pre-implement check is not optional
- dispatch subagent prompts that reference "earlier in this conversation"
- silently pick a side when two reviewers conflict — surface the conflict
- dismiss bot feedback without stating the reason
- capitulate on push-back to save time

Recovery moves:

- **Can't verify a suggestion** → state the limitation: "Can't verify without running X; should I investigate / ask / proceed?"
- **Reviewer and prior architectural decision conflict** → stop, raise with the human; do not silently re-decide
- **Pushed back, then realized you were wrong** → correction template: "You were right — I checked <X> and it does <Y>. Implementing." No long apology.
- **Ambiguous input with no PR / no messages / no markdown** → report the gap explicitly; ask the user which source to evaluate

## Reference routing

| File | Read when |
|---|---|
| `references/voice.md` | Writing any response — forbidden phrases, "Fixed." alternatives, pushback templates |
| `references/rationalizations.md` | RED-baseline excuses that bypass verify-before-implement; counters |
| `references/understand-changes.md` | Reconstructing what was reviewed — commits → tool-trail → bash fallback chain |
| `references/subagent-dispatch.md` | Writing the Explore subagent prompt — self-contained template |
| `references/verification.md` | Evaluating a specific feedback item against the codebase; the 6-check verification lens |
| `references/multi-agent-consolidation.md` | Combining feedback from 2+ reviewers; line-range clustering; conflict resolution |
| `references/gh-review-workflow.md` | Pulling PR comments via `gh`; thread replies; PR-discussion vs. review-comment channels |
| `references/action-plan-output.md` | Formatting the action plan — per mode (PR / session / markdown-doc) |
| `scripts/parse-pr-comments.md` | Capturing PR reviews, inline comments, and discussion comments into raw snapshots plus normalized JSONL |
| `scripts/cluster-feedback.md` | Preparing normalized JSONL into stable clustered items before verification |

## Final checks

Before declaring done, confirm:

- [ ] input mode declared and matches the user's ask
- [ ] ground truth reconstructed with a named source (commits / tool-trail / bash / uncertain)
- [ ] Explore subagent dispatched with a self-contained prompt (no session references)
- [ ] if multi-source: line-range clustering applied, conflicts surfaced
- [ ] every feedback item has a verdict (ACCEPT / PUSHBACK / CLARIFY / DEFER / DISMISS) with reasoning
- [ ] output matches the action-plan format for the mode
- [ ] zero forbidden phrases in the response (grep-checked against `references/voice.md`)
- [ ] if PR mode: inline replies went in the correct thread, not at top level
- [ ] if implementation ran: order was blocking → simple → complex, one at a time

Quick orphan check:

```bash
for f in $(find references -name '*.md' -type f); do grep -q "$(basename $f)" SKILL.md || echo "ORPHAN: $f"; done
```
