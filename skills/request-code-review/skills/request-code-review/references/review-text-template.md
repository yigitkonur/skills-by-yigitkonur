# Review Text Template

How to structure the PR body (or markdown review doc) so a reviewer can finish reading and say "LGTM" instead of "tell me more". The author's job is to pre-empt every foreseeable question.

## Character budget

**Hard cap: 50,000 characters.** GitHub's PR body limit is 65,536; 50k leaves room for reviewer quotes, edits, and resolution markdown. If the draft is approaching the cap, the PR is too big — split it along the natural domain seam.

Typical well-structured bodies land at 2,000-12,000 characters. Past 20,000, reviewers start skimming. Past 30,000, start considering whether multiple PRs would be clearer.

## Required structure

```markdown
# <title — matches the commit-style subject line>

## Summary
<2-4 sentences. What changed, why, and what the reviewer should focus on.>

## Context / Why now
<The problem this solves. Link issue/ticket if any. Constraints that drove the design.>

## The N items
<One subsection per logical change cluster. For each:
- files touched in this item
- what it does
- why this approach (and what alternatives were considered and rejected)
- how it was verified>

### Item 1: <short label>
- Files: `path/a.ts`, `path/b.ts`
- What: <what it does>
- Why this shape: <why not the alternative>
- Verified by: <what was actually run>

### Item 2: ...

## Files touched
<Aggregate table of all modified files with net line counts and one-line purpose.>

| File | ± | Purpose |
|---|---|---|
| `src/auth/session.ts` | +42 / −8 | Rotate session tokens on privilege elevation |

## Verification
<What the author ran and the results. State exactly — "type-check passes" ≠ "tests pass" ≠ "production verified".>

- Automated: `pnpm test` (27 tests, all pass) / `cargo test` (clean) / `pytest -q` (12 passed)
- Manual: <steps that were walked through>
- Not verified: <what the author could NOT confirm, and why>

## Weaknesses and open questions
<At least TWO items. This is the author's own critique.>

1. <Weakness or uncertainty>. Would prefer reviewer attention on <specific question>.
2. <Second weakness or trade-off>. Reviewer: <specific ask>.

## Request to the reviewer
<At least ONE explicit "please explain in depth" prompt on something the author is genuinely uncertain about. Invite pushback.>

Example:
> The retry loop in `worker.ts:142` uses exponential backoff with jitter, but I'm not sure the jitter window is right for our thundering-herd shape. If you have seen this before, please explain in depth.

## Follow-ups (not in scope)
<Explicit "this PR does NOT include" list. Prevents scope-creep questions.>

- <Thing reviewers might ask about that is intentionally deferred>
- <Follow-up PR that will address X>
```

## The self-review voice

**Forbidden phrases anywhere in the body:**

- "Thanks for reviewing!" / "Hope this helps" / "Please feel free to"
- "You're absolutely right" / "Great point"
- "LGTM" (the author does not LGTM their own work — that's what the reviewer does)
- "Just" (as in "just a small change") — every change deserves a rationale

**Preferred voice:**

- "Fixed by doing X." (action, past tense)
- "Pushed back on doing X because Y." (technical reasoning)
- "Uncertain whether X holds for Y; please explain." (explicit uncertainty)
- "Did not verify Z because W; flagged as follow-up." (honest gap)

## Severity taxonomy (for weaknesses section)

When surfacing your own weaknesses, categorize:

| Level | Use for | Example |
|---|---|---|
| **Critical** | Might break production, security gap, data-loss risk | "Migration drops NOT NULL constraint — rollback window is ~30s if we hit an invalid row." |
| **Important** | Design trade-off the author picked and wants validation on | "Chose synchronous retry over queue because latency matters more than throughput here — open to reviewer disagreement." |
| **Minor** | Known-but-deferred polish | "Error message on L48 still says 'foo' — will rename in the follow-up PR." |

Critical items always get a review question. Important items usually do. Minor items are informational.

## The "explain every change" rule

Every changed file must appear under either **The N items** section or **Files touched** table. If a file changed and the reviewer cannot find its rationale in the body, the body is incomplete. No silent changes.

For mechanical changes (rename, import reorder, formatter pass), group them under one item labeled "Mechanical" with the rationale "automated fix" — but still list them.

## Do not include

- **Session history or agent narration.** The reviewer gets the work product, not the process. "I tried X first, then switched to Y after running Z" belongs in the PR's development story, not the review body. (Borrowed from obra's precise-context principle.)
- **Todo comments or placeholders.** If the body says `[TODO: describe]`, it is not ready.
- **Screenshots of terminal output without context.** Paste the relevant line, not the whole session.
- **Apology language.** "Sorry this is so long" reads as unserious. If it's long, justify the length or split the PR.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Summary says "various improvements" | Rewrite per-item with rationale |
| No weaknesses section | Find two. Every non-trivial PR has them. |
| No reviewer question | Add one. Uncertain nowhere = either lying or not actually done |
| Body > 50k chars | Split the PR along the natural seam |
| Same paragraph explains two unrelated changes | Split into two items |
| "This is obvious" tone | Nothing is obvious to a reviewer seeing it for the first time |
