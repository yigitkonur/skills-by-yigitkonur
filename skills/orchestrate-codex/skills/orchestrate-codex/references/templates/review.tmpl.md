# Review mode prompt template

Review mode invokes `codex exec review` per branch per round. The review focus is more constrained than exec/batch: it names what to review and what to ignore. In codex-cli 0.130.0, `codex exec review` accepts the same policy flags as `codex exec`, plus review-specific flags such as `--base`.

This template is the per-round review focus passed via stdin or `--prompt`. It uses the canonical six section headers from `references/universal/prompt-discipline.md` so the audit grep at `prompt-discipline.md:155-158` passes against review prompts. Review-specific blocks (what to flag, what to skip, round context, output format) live under those headers.

The `<one-sentence summary of the branch's intent>` placeholder below would, in a future revision, be filled from the per-entry `round_focus` field documented in `references/modes/review.md`. **That field is not consumed by the runner today** — for now, the operator hand-fills the placeholder before invoking review on a custom prompt.

**Custom prompt injection is not wired into `handleReview` today.** The dispatcher spawns `codex exec review` with hardcoded flags plus `--base` and no positional prompt; there is no `--prompt-file` or `--focus`. To redirect review focus toward a spec doc, perf concern, or hostile intent, see `references/modes/review.md` §"Custom-prompt injection: not supported in dispatcher today" for the three documented workarounds (single-mode bridge, repo-conventions discovery, bare `codex exec review`).

---

## Template

```
# Intent

Review the diff between origin/<base> and HEAD on the branch <branch> (round <N>). The branch has a single coherent concern: <one-sentence summary of the branch's intent>. Surface major issues only; the round terminates clean when no new majors remain.

# Discovery — read first

- the diff itself (`git diff origin/<base>...HEAD`) — the only authoritative source for what changed
- prior-round findings file (`findings.<N-1>.json` if N>1) — to avoid re-flagging
- AGENTS.md / CLAUDE.md / CONTRIBUTING.md (if present at the repo root) — repo-local conventions
- the branch's stated concern above — to detect scope creep within the diff

# Constraints

Flag (major):
- correctness bugs in the changed code
- runtime stability regressions (race conditions, null derefs, silent error swallowing)
- data integrity hazards (lost writes, ordering bugs, partial state on failure)
- security regressions (auth checks, input validation, secret handling)
- regressions of existing behavior the diff doesn't acknowledge
- hygiene that hides bugs (broad try/catch with no logging, swallowed promise rejections)
- branch-structure issues that block reviewability (one commit mixing N concerns)

Round context (prior rounds applied these fixes):
- <round 1: short summary>
- <round 2: short summary>
- ...

Output format — per finding, emit:
- file:line
- severity: major | minor (you decide; default-when-ambiguous: major)
- one-paragraph explanation (what + why)
- suggested fix as code or precise prose; mark as "speculative" if not certain

# Success criteria

- Every finding has a `file:line` location and a severity tag.
- No finding duplicates one already addressed in a prior round (see Round context).
- If no major items remain, the output says so explicitly so the classifier can mark the round converged.

# Out-of-scope

- Do NOT propose fixes by editing files — codex review is read-only by design.
- Do NOT flag formatting, naming preferences, or style nits unless they affect correctness.
- Do NOT flag doc-only polish.
- Do NOT raise speculative performance suggestions without a measurement.
- Do NOT scope-creep ("while you're here, also fix X") — only review what the diff changed.
- Do NOT re-review unchanged code from the branch's history; this round is the diff only.

# Failure protocol

If the diff is empty or unreadable (bad base ref, detached HEAD, merge conflict markers): emit a single line `REVIEW_BLOCKED: <one-sentence reason>` and stop. The classifier reads this status and the orchestrator surfaces it; do not improvise findings against an unreadable diff.
```

Note: the Failure protocol shape above is review-mode specific (the `REVIEW_BLOCKED:` status is what `classify-review-feedback.py` keys on). This per-mode template is authoritative for that section; see `references/universal/prompt-discipline.md` §"Failure protocol — mode-specific shapes".

## Why this shape

Intent orients codex to *this round's* diff (without it codex re-reviews branch history and ships stale findings). Constraints carry the major-vs-minor policy and the per-finding output format so `classify-review-feedback.py` can partition. Out-of-scope blocks the two biggest drift modes: writing fixes (codex review is read-only) and scope creep beyond the diff. Sizing: 30–80 lines; round context grows linearly with rounds (bounded at 10).

## Round termination

The skill caps rounds at 10. If a branch hasn't converged by round 10:
- Mark `cap_reached` if another terminal state has not been reached.
- Mark `blocked` if items are persistently ambiguous or contradict each other.

Read `references/modes/review.md` §terminal-states for the full taxonomy.
