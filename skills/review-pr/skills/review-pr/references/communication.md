# Writing Actionable Review Comments

How to write review comments that get addressed, not ignored. Good comments are specific, evidence-based, and constructive. Bad comments are vague, directive, and demoralizing.

---

## The Anatomy of an Actionable Comment

Every review comment should include these elements:

```
1. WHAT    — What is the issue? (specific, not vague)
2. WHERE   — Exact file:line reference
3. WHY     — Why does it matter? (impact, not theory)
4. HOW     — Suggested fix or question (code preferred)
5. LEVEL   — How serious is this? (severity tag)
```

### Good vs Bad Examples

| Element | Bad | Good |
|---------|-----|------|
| What | "This doesn't look right" | "The null check on line 42 doesn't cover the case where `user.role` is an empty string" |
| Where | "In the auth code" | "`src/auth/middleware.ts:42`" |
| Why | "This could cause issues" | "An empty string passes the null check but fails the role lookup on line 48, causing a 500 error" |
| How | "Fix this" | "Consider: `if (!user.role) return res.status(403).json({ error: 'No role assigned' });`" |
| Level | (none) | "🟡 Important — affects all users without explicitly assigned roles" |

### Complete actionable comment example

```markdown
🟡 **Missing empty-string guard on role check** — `src/auth/middleware.ts:42`

The current check `if (user.role !== null)` passes when `user.role` is `""` (empty string).
Users imported from the legacy system have `role = ""` instead of `null`.

When role is empty, line 48 calls `lookupPermissions("")` which returns `undefined`,
and line 52 crashes with `TypeError: Cannot read properties of undefined`.

Suggested fix:
```js
if (!user.role) {  // Catches null, undefined, and empty string
  return res.status(403).json({ error: 'No role assigned' });
}
```
```

---

## Language and Tone

### Phrases to Use

| Context | Good Phrasing |
|---------|---------------|
| Raising an issue | "This could cause..." / "I notice that..." / "It looks like..." |
| Suggesting a fix | "Consider..." / "One approach would be..." / "What about..." |
| Asking for context | "Could you help me understand why..." / "Is it intentional that..." |
| Agreeing with choice | "Nice approach here" / "Good use of..." / "This handles the edge case well" |
| Uncertain finding | "I might be wrong, but..." / "Can this be null here?" / "Unless I'm missing context..." |

### Phrases to Avoid

| Bad Phrase | Why | Better Alternative |
|-----------|-----|-------------------|
| "You should..." | Directive; creates defensiveness | "Consider..." / "It might help to..." |
| "Why didn't you..." | Implies negligence | "Was there a reason for..." |
| "Obviously..." | Condescending | (just state the fact) |
| "This is wrong" | Absolute statement without evidence | "This may not handle the case where..." |
| "Just do X" | Minimizes the work involved | "One option would be X" |
| "Nit: " on 10+ comments | Signals you're bikeshedding | Batch nits into one comment or skip |
| "LGTM" (without reading) | Irresponsible approval | Specify what you reviewed |

### The "I" vs "You" Rule

Frame comments from your perspective, not as directives to the author:

```
❌ "You forgot to handle the error case"
✅ "I don't see error handling for the case where the API returns 500"

❌ "You need to add validation here"
✅ "This endpoint would benefit from input validation — see the pattern in user-routes.ts:30"

❌ "Why did you use var instead of const?"
✅ "This could use const since it's never reassigned"
```

---

## Severity Tags and When to Use Them

Use consistent severity tags so the author can triage your feedback efficiently.

| Tag | When to Use | Author Action |
|-----|-------------|---------------|
| 🔴 Blocker | Security vuln, data loss, crash on common path | Must fix before merge |
| 🟡 Important | Bug, performance issue, missing error handling | Should fix; discuss if unclear |
| 🟢 Suggestion | Better approach, cleaner code, minor improvement | Optional; author decides |
| 💡 Question | Unclear intent, possible issue, need context | Respond with explanation |
| 🎯 Praise | Good pattern, clean approach, thorough testing | No action needed |

### Severity Calibration

Before assigning severity, ask:

```
Would a production user hit this? → Higher severity
Is the fix trivial (<5 minutes)? → Still flag it, lower severity is fine
Am I > 70% confident this is a real issue? → If not, use 💡 Question
Does the codebase already have this pattern elsewhere? → Don't flag conventions
Would I flag this in my own code? → Good calibration check
```

---

## Batching and Grouping

### When to batch

If you find the same issue in multiple files (e.g., missing error handling in 4 endpoints), do NOT leave 4 separate comments. Instead:

```markdown
🟡 **Missing error handling on external API calls** — multiple files

The following endpoints call `externalApi.fetch()` without try/catch:
- `src/api/users.ts:34`
- `src/api/orders.ts:67`
- `src/api/products.ts:23`
- `src/api/reports.ts:89`

If the external API returns 500 or times out, these endpoints will crash
with an unhandled promise rejection.

Consider wrapping in try/catch with a fallback response, similar to
the pattern in `src/api/payments.ts:45`.
```

### When NOT to batch

If the issues are in the same file but fundamentally different problems, keep them separate. Batching unrelated issues makes it harder for the author to track and address them individually.

---

## Commenting on Different Finding Types

### For bugs

```
1. State what the code does (observed behavior)
2. State what it should do (expected behavior)
3. Show the input that triggers the bug
4. Suggest a fix (code block preferred)
```

### For security issues

```
1. Name the vulnerability class (e.g., SQL injection, IDOR)
2. Show the attack vector (how could it be exploited?)
3. Show the tainted data flow (input → sink)
4. Suggest the fix (parameterized query, auth check, etc.)
5. Note the severity explicitly — security findings should never be subtle
```

### For performance issues

```
1. Identify the problematic pattern (N+1, unbounded, etc.)
2. Explain the scaling concern (works now, breaks at N)
3. Quantify if possible (scans 100k rows, makes N API calls)
4. Suggest the optimization (JOIN, batch, index, cache)
```

### For questions

```
1. State what you observed
2. State why it seems unusual or unclear
3. Offer your best interpretation
4. Ask the author to confirm or clarify
```

Example:
```markdown
💡 `src/api/orders.ts:56` — The timeout is set to 30 seconds for this payment
gateway call, but the other payment endpoints use 10 seconds. Is the longer
timeout intentional because this gateway is slower, or should this match the
others?
```

---

## Positive Feedback Patterns

Always include at least one positive observation. This is not politeness theater — it serves two purposes:

1. **Calibration signal** — shows you actually read and understood the code
2. **Reinforcement** — encourages good patterns to continue

### Good praise examples

```markdown
🎯 Clean error handling in `src/api/payments.ts:30-45` — wrapping each
gateway call with specific error types makes debugging much easier.

🎯 The pagination implementation in `src/api/users.ts:60` correctly uses
cursor-based pagination instead of offset — this will scale well.

🎯 Good defensive programming: checking for both null and empty array
before processing, and logging the skip reason. This will save debugging
time when issues arise.
```

### Bad praise (avoid)

```markdown
❌ "Looks good overall" — too vague, no evidence you read anything
❌ "Nice code!" — not specific enough to be useful
❌ "Good job 👍" — feels perfunctory
```

---

## Anti-Pattern: The Review That Gets Ignored

Reviews get ignored when they exhibit these patterns:

| Pattern | Why It's Ignored | Fix |
|---------|-----------------|-----|
| 20+ findings | Overwhelms the author | Limit to top 10, prioritize ruthlessly |
| All nits, no substance | Author sees no real value | Focus on bugs, security, correctness |
| No severity tags | Author can't prioritize | Tag every finding |
| No positive feedback | Feels like an attack | Include at least one praise |
| Vague suggestions | "Clean this up" is not actionable | Provide specific code suggestions |
| Style preferences | "I prefer X" is subjective | Only flag if it violates project conventions |
| Out-of-scope architecture | "You should refactor the whole module" | Not in scope for this PR |

## Steering notes

> These notes capture real mistakes observed during derailment testing.

1. **"You should" is the most common tone mistake in AI-generated reviews.** Replace with "This could...", "Consider...", or "One approach would be...". The goal is collaborative exploration, not directive instruction.
2. **Praise must be specific to be credible.** "Nice work!" is noise. "The error boundary at `src/ErrorBoundary.tsx:23` cleanly separates render failures from data failures -- this prevents cascading crashes" is useful praise.
3. **Batching repeated issues is under-used.** If the same missing-null-check pattern appears in 4 files, write one finding with all 4 locations, not 4 separate findings. This reduces noise by 75% without losing information.
4. **When extending an existing thread, start with "Agree with @reviewer" or "Building on the above."** This signals collaboration, not competition. Never rephrase someone else's finding as your own.
5. **Questions beat assertions for low-confidence observations.** "Is it intentional that this endpoint has no rate limiting?" is more useful than "This endpoint needs rate limiting" when you are unsure about the architectural context.

> **Cross-reference:** See `references/anti-patterns.md` for the full list of tone and content anti-patterns to avoid.
