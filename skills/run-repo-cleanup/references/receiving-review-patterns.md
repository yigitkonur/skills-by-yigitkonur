# Receiving-Review Patterns (inlined)

These patterns were adapted from the superpowers `receiving-code-review` discipline and inlined here so this skill is self-contained. They govern both how you **write self-review PR bodies** (Phase 3 of the parent skill) and how you **respond when the reviewer actually replies**.

Core principle: **Technical correctness over social comfort. Verify before implementing. Ask before assuming.**

## The response pattern

When the reviewer leaves comments (or when you're drafting the PR body — same discipline applied to yourself):

```
1. READ    — complete feedback without reacting.
2. UNDERSTAND — restate the requirement in your own words (or ask if unclear).
3. VERIFY  — check against codebase reality. Does the suggestion match how things actually work?
4. EVALUATE — technically sound for THIS codebase / stack / version?
5. RESPOND — technical acknowledgment or reasoned pushback. No theatre.
6. IMPLEMENT — one item at a time. Test each. Push only after the item is actually done.
```

## Forbidden phrases

Never emit any of these, in a PR body, in a thread reply, or in a top-level comment:

- "You're absolutely right!"
- "Great point!" / "Excellent feedback!"
- "Let me implement that now" (before you've verified)
- "Thanks for catching that!" / "Thanks for <anything>"
- "Please feel free to …" / "Kindly …"
- "Hope this helps!"
- "Let me know if this works!"

If you catch yourself about to write "Thanks": **delete it**. State the fix instead. Actions speak. The code itself shows you read the feedback.

### Use instead

- "Fixed. <1-sentence description of what changed>."
- "Good catch — <specific issue>. Fixed in `<file>:<line>`."
- "Checked <X>. <fact>. Pushed back because <reason>."
- "Can't verify this without <Y>. Should I investigate, or is <Z> the intended contract?"
- Or: just fix it and show it in the code.

## Handling unclear feedback

```
IF any feedback item is unclear:
  STOP — do not implement anything yet.
  ASK for clarification on the unclear items.
```

**Why:** items may be related. Partial understanding leads to wrong implementation.

Example, wrong:
> Reviewer: "Fix items 1–6."
> (Agent understands 1, 2, 3, 6. Vague on 4, 5.)
> Agent: implements 1, 2, 3, 6 and opens a fix-up PR. Later asks about 4, 5.

Example, right:
> Agent: "Clear on 1, 2, 3, 6. Need clarification on 4 and 5 before proceeding — is <interpretation A> or <interpretation B> what you meant?"

## Source-specific handling

### From the project owner / trusted reviewer

- **Trusted, implement after understanding.**
- Still ask if scope is unclear.
- No performative agreement.
- Skip to action or to a short technical acknowledgment.

### From external reviewers / drive-by suggestions

```
BEFORE implementing:
  1. Is the suggestion technically correct for THIS codebase?
  2. Does it break existing functionality?
  3. Is there a documented reason for the current implementation?
  4. Does it work across all supported platforms / runtime versions?
  5. Does the reviewer understand the full context of this code?
```

If the suggestion looks wrong → push back with a technical reason.
If you can't easily verify → say so: "I can't verify this without <X>. Investigate, or fall back to <Y>?"
If it conflicts with prior owner decisions → stop and involve the owner before implementing.

## YAGNI gate

When a reviewer suggests "implementing this properly" / "adding proper X":

```
grep the codebase for actual callers / usage.

IF unused:      "This endpoint isn't called anywhere. Remove it instead (YAGNI)?"
IF used:        implement properly.
```

PRs should shrink by default, not expand. Don't let reviewer enthusiasm widen a one-line fix into a 400-line abstraction.

## When to push back

Push back when:
- The suggestion breaks existing functionality.
- The reviewer lacks context (e.g. didn't read the linked doc).
- It violates YAGNI — the feature is genuinely unused.
- It's technically wrong for this stack/version.
- Legacy / backward-compatibility constraints exist.
- It conflicts with the owner's architectural decisions.

**How to push back:**
- Use technical reasoning, not defensiveness.
- Cite evidence — tests, grep output, benchmarks, docs.
- Ask specific questions ("Which call site did you have in mind for <X>?").
- Escalate to the owner only when the disagreement is architectural, not tactical.

## Acknowledging correct feedback

When the feedback is correct:

```
✅ "Fixed. <what changed>."
✅ "Good catch — <issue>. Fixed in <file>:<line>."
✅ (Just fix it and let the code speak.)

❌ "You're absolutely right!"
❌ "Great point!"
❌ "Thanks for catching that!"
```

Actions > words. Show the fix, not the gratitude.

## Gracefully correcting your own pushback

If you pushed back and were wrong:

```
✅ "You were right — I checked <X> and it does <Y>. Implementing now."
✅ "Verified this and you're correct. My initial read missed <Z>. Fixing."

❌ (long apology)
❌ (defending why you pushed back)
❌ (over-explaining)
```

State the correction factually. Move on. No theatre.

## GitHub thread replies vs top-level comments

When replying to **inline review comments** (attached to specific lines), reply **in the thread**, not as a top-level PR comment.

```bash
# Reply inline (correct for line-attached comments)
gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies \
  -f body="Fixed in <commit-sha>."

# Top-level PR comment (for general discussion, not line-attached feedback)
gh pr comment {pr-number} --repo {owner}/{repo} \
  --body "All items addressed in <commit-sha>."
```

Thread replies keep context anchored to the code. Top-level replies lose that anchor and force reviewers to re-navigate.

## Common mistakes

| Mistake | Fix |
|---|---|
| Performative agreement | Restate the requirement or just act. |
| Blind implementation | Verify against the codebase first. |
| Batching without testing | One item at a time; test each. |
| Assuming reviewer is always right | Check if the suggestion breaks things. |
| Avoiding pushback to be polite | Technical correctness > comfort. |
| Partial implementation | Clarify all items first. |
| Proceeding when you can't verify | State the limitation; ask for direction. |
| Gratitude in every reply | Delete it. Fix it. Ship it. |

## Real examples

**Performative agreement (bad):**
> Reviewer: "Remove this legacy code."
> Agent: "You're absolutely right! Removing now…"

**Technical verification (good):**
> Reviewer: "Remove this legacy code."
> Agent: "Checking — our build target is macOS 10.15+; this API needs 13+. The legacy path exists for back-compat. The current implementation does have a wrong bundle ID though — fix the bundle ID, or drop pre-13 support and delete the path entirely?"

**YAGNI (good):**
> Reviewer: "Implement proper metrics tracking with database, date filters, CSV export."
> Agent: "Grepped — nothing calls `/metrics`. Remove it instead (YAGNI)? Or is there usage I'm missing?"

**Unclear item (good):**
> Owner: "Fix items 1–6."
> Agent: "Clear on 1, 2, 3, 6. Need clarification on 4 and 5 before implementing — specifically: is 4 about the retry policy or the timeout? And in 5, do you mean the SSR shell or the SPA route?"

## Applying to self-review (the PR body)

The same discipline maps to writing your own PR body:

- **Verify, then claim.** "Type-check passes" ≠ "tests pass" ≠ "production verified". Say exactly what you ran.
- **Answer the reviewer's questions in advance.** If you know they'll ask "why this approach?", put the reason in the body.
- **State risks you'd state to yourself.** Hiding risks to make the PR look smaller is the same failure as performative agreement with a reviewer.
- **Grep before abstracting.** If the body describes an abstraction, grep the callers. If there's only one, don't abstract.
- **No gratitude in the body.** "Thanks for reviewing" is theatre in reverse.

## Bottom line

External feedback = **suggestions to evaluate**, not orders to follow. Verify. Question. Then implement. No performative agreement. Technical rigor always — whether the reviewer is someone else or you talking to yourself inside the PR body.
