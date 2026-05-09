# Review mode prompt template

Review mode invokes `codex exec review` per branch per round. The review focus is more constrained than exec/batch: it names what to review and what to ignore. In codex-cli 0.130.0, `codex exec review` accepts the same policy flags as `codex exec`, plus review-specific flags such as `--base`.

This template is the per-round review focus passed via stdin or `--prompt`. The main agent reads the resulting `findings.<round>.json` and decides per-item.

---

## Template

```
# Review focus (round <N> of <branch-slug>)

You are reviewing the diff between origin/<base> and HEAD on the branch <branch>. The branch has a single coherent concern: <one-sentence summary of the branch's intent>.

# What to flag (major)

- correctness bugs in the changed code
- runtime stability regressions (race conditions, null derefs, silent error swallowing)
- data integrity hazards (lost writes, ordering bugs, partial state on failure)
- security regressions (auth checks, input validation, secret handling)
- regressions of existing behavior the diff doesn't acknowledge
- hygiene that hides bugs (broad try/catch with no logging, swallowed promise rejections)
- branch-structure issues that block reviewability (one commit mixing N concerns)

# What to skip (minor)

- formatting, naming preferences, style nits unless they affect correctness
- doc-only polish
- speculative performance suggestions
- scope creep ("while you're here, also fix X")

# Round context

Prior rounds applied these fixes:
- <round 1: short summary>
- <round 2: short summary>
- ...

# Output format

Per finding, emit:
- file:line
- severity: major | minor (you decide; default-when-ambiguous: major)
- one-paragraph explanation (what + why)
- suggested fix as code or precise prose; mark as "speculative" if not certain

If you find no major items, say so explicitly. The classifier exits with status indicating "converged".
```

## Why each section

- **Review focus** — orients codex to this round's diff specifically; without it, codex re-reviews unchanged code from the branch's history and produces stale findings.
- **What to flag (major) / What to skip (minor)** — codifies the major-vs-minor policy. Without this list codex flags every style nit and the round never converges.
- **Round context** — prevents codex from re-flagging the issues prior rounds already fixed.
- **Output format** — every finding has a file:line + severity so `classify-review-feedback.py` can partition.

## What stays out

- "Be thorough" — codex defaults to thorough; pad-language drives output bloat.
- Apply guidance — codex review is read-only by design; do not ask it to write fixes inside this template.
- "Look for security issues" without scope — phrase it as the `# What to flag` bullet (existing in the template).

## Sizing

Review focus prompts run 30–60 lines. The template is the upper bound; round context grows linearly with rounds (bounded at 10).

## Round termination

The skill caps rounds at 10. If a branch hasn't converged by round 10:
- Mark `cap_reached` if another terminal state has not been reached.
- Mark `blocked` if items are persistently ambiguous or contradict each other.

Read `references/modes/review.md` §terminal-states for the full taxonomy.
