# Severity Classification Guide

How to decide the severity level for each finding.

## Decision tree

```
Is it a security vulnerability, data loss risk, or crash?
  → YES → 🔴 Blocker

Does it cause incorrect behavior for users?
  → YES → Is it in a critical path (auth, payments, data writes)?
    → YES → 🔴 Blocker
    → NO → 🟡 Important

Is it a performance issue?
  → YES → Is it measurably impactful (N+1, unbounded, no pagination)?
    → YES → 🟡 Important
    → NO → 🟢 Suggestion

Is it an error handling gap?
  → YES → Could it cause silent failures or data corruption?
    → YES → 🟡 Important  
    → NO → 🟢 Suggestion

Is it a code quality issue?
  → YES → Would it confuse the next developer?
    → YES → 🟢 Suggestion
    → NO → Skip (not worth commenting)

Are the reviewer uncertain about the intent or behavior?
  → YES → 💡 Question

Did the author do something well?
  → YES → 🎯 Praise
```

## Severity definitions with examples

### 🔴 Blocker — Must fix before merge

**Definition:** The code has a defect that will cause immediate harm if deployed.

**Examples:**
- SQL injection: `query("SELECT * FROM users WHERE id = " + userId)`
- Auth bypass: endpoint missing authentication middleware
- Data loss: migration drops a column without backing up data
- Crash: null pointer access on a code path that WILL be hit
- Secret exposure: API key hardcoded in source code

**Calibration:** If the reviewer has >3 blockers in a PR, re-examine. Either the PR is seriously problematic (suggest closing/rewriting) or the review threshold is too low. True blockers are rare — most PRs have 0-1.

### 🟡 Important — Should fix, author decides if it blocks

**Definition:** The code has an issue that could cause problems but won't cause immediate harm.

**Examples:**
- Missing input validation on an API endpoint
- N+1 database query in a frequently called path
- Error caught but not handled (empty catch block)
- Race condition that's unlikely but possible
- Missing test for a new critical code path
- Inconsistent error response format

**Calibration:** 2-5 important findings per PR is normal. If >5, check if the review is being too strict.

### 🟢 Suggestion — Non-blocking improvement

**Definition:** The code works correctly but could be better.

**Examples:**
- A simpler way to express the same logic
- Dead code that could be removed
- A variable name that's slightly misleading
- A function that's growing too long (>50 lines)
- A missing TypeScript type that defaults to `any`

**Calibration:** 3-8 suggestions per PR is fine. If >10, the review is probably bikeshedding.

### 💡 Question — Needs author clarification

**Definition:** The intent or behavior is unclear and author input is needed.

**Use when:**
- Confidence is < 70% on a potential finding
- The code could be intentional but confidence is low
- The behavior seems odd but may have missing context
- A design decision needs context

**Examples:**
- "Is `user.role` guaranteed to be non-null here?"
- "Should this endpoint also handle the case where `items` is empty?"
- "Was the removal of the cache invalidation on line 45 intentional?"

### 🎯 Praise — Positive observation

**Definition:** Something done well that's worth calling out.

**Examples:**
- Clean error handling with good user-facing messages
- Thorough test coverage including edge cases
- Good use of TypeScript generics for type safety
- Clear variable names that make the code self-documenting
- Defensive programming (input validation, null checks)
- Well-structured commits with clear messages

**Rule:** Always include at least one. If the PR has blockers, praise is even more important to balance the feedback.

## Steering notes

> These notes capture real mistakes observed during derailment testing.

1. **Blocker inflation is the most common severity calibration error.** More than 3 blockers in a single review almost always means some are actually Important. Re-check each blocker against the definition: does it make the PR *unsafe to merge*? If the PR could merge and the issue could be fixed in a follow-up, it is Important, not Blocker.
2. **Suggestions should never be phrased imperatively.** If a finding uses "must", "should", or "need to", it is probably mis-classified as a suggestion. Suggestions are optional improvements -- phrase them as "consider", "one option would be", or "this could be simplified by".
3. **Questions are under-used.** When intent, context, or bug status is unclear, a question is the correct severity. "Is it intentional that `maxRetries` defaults to 0?" is more useful than "Bug: maxRetries defaults to 0" when the intended behavior is unknown.
4. **Praise must appear in every review.** If the reviewer cannot find something specific to praise, the reviewer has not read the PR carefully enough. Even a small PR has something worth acknowledging -- a well-named variable, a good error message, or a clean test structure.

> **Cross-reference:** See SKILL.md "Severity calibration" section for the calibration checks that catch over-counting.
