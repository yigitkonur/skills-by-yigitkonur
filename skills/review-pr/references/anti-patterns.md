# Anti-Patterns in PR Review

Things to NEVER do during a review, synthesized from 121 skill analyses.

## The Noise Generators

### 1. Style policing
**Don't:** Flag formatting, whitespace, bracket style, import ordering.
**Why:** Linters and formatters handle this. Your review should focus on what machines can't catch.
**Instead:** If the project doesn't have a linter, suggest adding one — as a general comment, not per-instance.

### 2. Architecture astronautics
**Don't:** Suggest major architectural changes in a PR review.
**Why:** A PR is not the venue for redesigning the system. The code under review is scoped to a specific change.
**Instead:** If you see a systemic issue, note it as a 💡 Question: "Have you considered [X]? This might be worth a separate discussion."

### 3. Hypothetical concerns
**Don't:** "This MIGHT cause issues IF someone WERE to..."
**Why:** Hypotheticals are infinite. Review the actual code for actual problems.
**Instead:** Only flag if you can describe a concrete, realistic scenario. "If a user submits an empty array here, this will throw on line 45" is concrete.

### 4. Pre-existing tech debt
**Don't:** Flag issues in code that wasn't changed in this PR.
**Why:** The author didn't write it, can't reasonably fix it, and it's not in scope.
**Instead:** If the pre-existing issue interacts with the new code dangerously, explain the interaction.

### 5. Duplicate findings
**Don't:** Raise an issue already flagged by another reviewer.
**Why:** It adds noise without value. The author has already seen it.
**Instead:** If you agree, add a brief note on the existing thread: "Agree with @reviewer — this is important."

### 6. Bikeshedding
**Don't:** Debate naming, variable order, whether to use `const` vs `let` when both work.
**Why:** These are low-value discussions that delay merge without improving quality.
**Instead:** Save naming feedback for cases where the name is genuinely misleading.

## The Credibility Killers

### 7. No evidence
**Don't:** "This doesn't look right" without explaining what's wrong.
**Why:** Vague feedback is not actionable.
**Instead:** Always include: file:line, what the code does, what it should do, and why.

### 8. "You should" language
**Don't:** "You should refactor this" / "You need to add tests."
**Why:** Directive language creates defensiveness and assumes you know the context better than the author.
**Instead:** "This could be simplified by..." / "A test for the empty-input case would catch the edge case on line 42."

### 9. Inconsistent standards
**Don't:** Flag an issue in one file but ignore the same pattern in another.
**Why:** Inconsistency suggests arbitrary review, which erodes trust.
**Instead:** If the pattern appears in multiple places, note it once as a cross-cutting concern.

### 10. Approving without reading
**Don't:** Approve a PR after skimming the title and description.
**Why:** Your approval is a signal to other reviewers and the author that the code is safe.
**Instead:** If you can't do a thorough review, say "I reviewed [X cluster] but didn't review [Y]."

## The Process Failures

### 11. Reviewing drafts uninvited
**Don't:** Review a draft PR unless the author explicitly asked for feedback.
**Why:** Draft PRs are work in progress. The author knows it's not ready.

### 12. Reviewing before CI
**Don't:** Do a full review when CI is failing.
**Why:** CI failures may indicate fundamental problems that would change your review.
**Instead:** Note which CI checks are failing and suggest the author fix those first.

### 13. Too many findings
**Don't:** List 20+ findings in a single review.
**Why:** It overwhelms the author and suggests the PR needs a different approach, not 20 fixes.
**Instead:** If you find >15 issues, step back. Either the PR is too large (suggest splitting) or you're being too noisy (re-apply the actionability filter).

### 14. Missing positive feedback
**Don't:** Write a review that's 100% criticism.
**Why:** Even PRs that need changes have things done well. Acknowledging them builds trust.
**Instead:** Always include at least one positive observation, no matter how small.

## The Confidence Trap

### 15. Low-confidence findings stated as facts
**Don't:** "This will crash on null input" when you're not sure the input can be null.
**Why:** If you're wrong, you lose credibility for future reviews.
**Instead:** If confidence < 70%, phrase as a question: "Can `user.role` be null here? If so, line 42 would throw."

## Steering notes

> These notes capture real mistakes observed during derailment testing.

1. **The most common anti-pattern in AI reviews is restating the diff.** Saying "this function now takes an extra parameter" is description, not review. Always ask: "so what?" -- what is the impact on callers, contracts, or safety?
2. **Anti-pattern #4 (pre-existing tech debt) is the hardest to resist.** When reviewing a file, surrounding code flaws are visible and tempting to flag. Only flag pre-existing issues if they create a new interaction hazard with the changed code.
3. **Anti-pattern #13 (too many findings) often signals scope creep.** If you hit 15+ findings, pause and re-apply the actionability gate from SKILL.md Phase 6 before continuing. Consider whether the PR itself is too large rather than continuing to enumerate problems.
4. **Style policing is context-dependent.** In a repo with no linter, a single "consider adding a linter" comment is appropriate. In a repo with ESLint/Prettier, zero style comments are appropriate -- the machines handle it.

> **Cross-reference:** Load `references/communication.md` for phrasing alternatives when you catch yourself writing anti-pattern language.
