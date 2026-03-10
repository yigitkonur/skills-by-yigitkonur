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

Are you uncertain about the intent or behavior?
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

**Calibration:** If you have >3 blockers in a PR, re-examine. Either the PR is seriously problematic (suggest closing/rewriting) or your threshold is too low. True blockers are rare — most PRs have 0-1.

### 🟡 Important — Should fix, author decides if it blocks

**Definition:** The code has an issue that could cause problems but won't cause immediate harm.

**Examples:**
- Missing input validation on an API endpoint
- N+1 database query in a frequently called path
- Error caught but not handled (empty catch block)
- Race condition that's unlikely but possible
- Missing test for a new critical code path
- Inconsistent error response format

**Calibration:** 2-5 important findings per PR is normal. If >5, check if you're being too strict.

### 🟢 Suggestion — Non-blocking improvement

**Definition:** The code works correctly but could be better.

**Examples:**
- A simpler way to express the same logic
- Dead code that could be removed
- A variable name that's slightly misleading
- A function that's growing too long (>50 lines)
- A missing TypeScript type that defaults to `any`

**Calibration:** 3-8 suggestions per PR is fine. If >10, you're probably bikeshedding.

### 💡 Question — Needs author clarification

**Definition:** You're unsure about the intent or behavior and need the author's input.

**Use when:**
- Confidence is < 70% on a potential finding
- The code could be intentional but you're not sure
- The behavior seems odd but might have context you're missing
- You want to understand a design decision

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
