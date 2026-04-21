# Action Plan Output Formats

The action plan is the deliverable of this skill. Format depends on input mode.

## PR mode

Output the action plan in two layers:

### Layer 1 — top-level PR summary comment

One top-level comment summarizes the overall response. No item details here — those go in thread replies.

```markdown
Addressed in commit `<sha>` (or "see per-thread replies"):

- <N> items accepted and fixed
- <M> items pushed back (details inline per-thread)
- <K> items need clarification (inline per-thread, tagged CLARIFY)
- <L> items dismissed with reason (inline per-thread)

Validation: `<what you ran>` passes.

<Optional one-paragraph framing if the PR context warrants — e.g., "The retry-strategy thread is the only unresolved item; reviewer and I are aligned that it needs architectural input.">
```

**Voice rules apply** (`references/voice.md`): no gratitude, no performative agreement. Drop filler.

### Layer 2 — per-item thread replies

One reply per inline comment thread. Reply target: `gh api .../pulls/<N>/comments/<comment-id>/replies`.

Format by verdict:

**ACCEPT:**
```
Fixed. <one-line description of what changed.>
```
or
```
Fixed in `<file:line>`.
```

**PUSHBACK:**
```
Disagree — <technical reason>. <evidence: file:line + citation>.
Willing to revisit if <specific condition>.
```

**CLARIFY:**
```
Need clarification before proceeding. <specific question>.
<Your current understanding, for context.>
```

**DEFER:**
```
Agree, but out of scope for this PR. Logged as follow-up: <issue link or planned PR>.
```

**DISMISS:**
```
Dismissed. <reason — usually "static analyzer false positive: X" or "not in this PR's diff: out-of-scope file">.
```

## Session-audit mode

No GitHub channel involved. Output the action plan as conversation output.

```markdown
## Action plan — evaluating the review

**Ground truth source:** <commits | tool-trail | bash-ops | uncertain>
**Feedback source(s):** <prev message author(s) or file name(s)>
**Explore subagent dispatched:** <subagent id or "yes" + one-line verdict summary>

### ACCEPT (N items)

1. **<short label>** (`<file:line>`)
   - Reviewer: <verbatim, trimmed>
   - Verdict: correct
   - Fix: <what to change, one or two sentences>

2. **<short label>** (`<file:line>`)
   - ...

### PUSHBACK (M items)

1. **<short label>** (`<file:line>`)
   - Reviewer: <verbatim, trimmed>
   - Verdict: incorrect — <technical reason>
   - Evidence: <file:line + reasoning>
   - Suggested response: <draft of the reply>

### CLARIFY (K items)

1. **<short label>** (`<file:line>`)
   - Reviewer: <verbatim>
   - Ambiguity: <what's unclear>
   - Question to ask: <specific question>

### DEFER (L items)

1. **<short label>** — <why out of scope for now; when it should ship>

### DISMISS (P items)

1. **<short label>** — <reason>

### Conflicts (if multi-source)

- <Item X>: <Reviewer A said X; Reviewer B said Y>. Resolution: <needs human / architectural decision / my take with evidence>.

### Next steps

- [ ] Implement <N items> in order: <blocking first, then simple, then complex>
- [ ] Reply to <M items> with pushback text
- [ ] Ask <K items> for clarification
- [ ] Defer <L items> to follow-up
```

## Markdown-doc mode

The user pointed at a file like `review.md` or `audit.md`. Write a sibling action plan to the same directory.

- Input: `review.md`
- Output: `review-action-plan.md`

Use the same structure as session-audit mode above. Additionally:

- At the top, include a "Source" block with the path + mtime of the input doc
- If the input doc had item numbers (1, 2, 3...), preserve them in the action plan
- Write to disk, don't just return inline unless the user asked for inline

## Implementation mode (optional Step 7)

If the user asked for both evaluation AND implementation (e.g., "evaluate and apply the fixes"), after the action plan is produced and approved:

- Process ACCEPT items in order: blocking → simple → complex
- One item at a time, test each
- After each item:
  - Commit with a message like `fix(scope): <what was done> — addresses review feedback on <item ref>`
  - (PR mode) Reply in the thread: `Fixed in <sha>.`
- Do NOT batch multiple items into one commit unless they are the same file + same concern

## Character budget (PR mode)

| Output | Recommended cap |
|---|---|
| Top-level summary comment | 1500 chars |
| Per-thread reply | 400 chars (GitHub keeps threads readable when replies are short) |
| Markdown-doc action plan | No hard cap; keep below 15000 chars for a typical PR |

If an explanation genuinely needs more characters, split — link from the summary to a discussion comment, or attach a file in a follow-up commit.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| One giant PR comment with everything inline | Layer 1 summary + Layer 2 thread replies |
| Thread reply with pure "Fixed." | If the fix is non-obvious, state the commit SHA or the one-line change |
| PUSHBACK reply without evidence | Cite `file:line`; specific scenarios that break |
| CLARIFY reply that's actually a pushback | If you have evidence, push back. CLARIFY is for genuine uncertainty. |
| Dismiss bot feedback without reason | "Dismissed — <reason>" always |
| Action plan that doesn't name the ground-truth source | Always state how you reconstructed what was reviewed |

## Worked example — PR mode

**Input:** PR #42 with 5 inline comments from human + Copilot + CodeRabbit + Devin + Greptile.

**Top-level summary:**

```markdown
Addressed in commit `abc1234`. Details inline per-thread.

- 3 items accepted and fixed (null check on auth, typo in README, missing await on the session refresh)
- 1 item pushed back (retry strategy — linear is correct here; see thread)
- 1 item needs clarification on scope (rate limiting depends on deployment context)

Validation: `pnpm test` passes (47 tests). `tsc --noEmit` clean.

The Copilot + Bito + Human cluster on auth.ts:L40-47 converged on the same null-check concern — fixed as one item.
```

**Per-thread replies** (abbreviated, one per inline comment):

- Thread on `auth.ts:L42`: `Fixed in abc1234. Added null guard + specific error.`
- Thread on `README.md:L14`: `Fixed. Typo corrected.`
- Thread on `session.ts:L87`: `Fixed in abc1234. Moved the mutex release out of the async call path.`
- Thread on `worker.ts:L104` (PUSHBACK): `Disagree — fixed-delay retry is correct for this use case because the downstream API rate-limits at 1 req/s and exponential backoff doubles wait under failure, which makes the 10s SLA unreachable. Happy to revisit if the API's rate limit changes.`
- Thread on `auth.ts:L42` (CLARIFY, rate-limit suggestion): `Need clarification before proceeding. Is this endpoint exposed externally, or internal-only? Rate-limiting scope depends. If external, I'd add a rate limiter; if internal, the existing session throttling should be enough.`
