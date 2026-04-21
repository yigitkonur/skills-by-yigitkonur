# Voice — Forbidden Phrases and Technical-Correctness Alternatives

The voice discipline is the most bypassed rule in this skill. Performative agreement costs nothing in the moment and corrodes technical rigor over time. Review this file **every time** you are about to write a response to a reviewer.

## Forbidden phrases (absolute)

These phrases are banned in any response — PR thread, conversation, markdown doc, or commit message. No exceptions.

| Forbidden | Why it fails |
|---|---|
| "You're absolutely right!" | Signals agreement before verification. Often written before the author has even checked the claim. |
| "Great point!" / "Excellent feedback!" | Purely performative. Conveys zero technical content. |
| "Thanks for catching that!" | Gratitude is fine in human contexts, but here it substitutes for the fix. Actions speak; the commit is the thanks. |
| "Thanks for the review!" | Same reason. Delete it. |
| "Thanks for [anything]" | Any gratitude expression. |
| "Let me implement that now" (before verifying) | Commits to an action before the pre-implement check. Violates rule 1. |
| "Hope this helps!" | Hedge language. The work either helps or it doesn't; the body is evidence. |
| "Please feel free to..." | Filler. Drop it. |
| "I apologize for..." | Long apologies after pushback turn corrections into drama. State the correction factually. |
| "No worries, I'll fix it" | "No worries" is a social fillers; "I'll fix it" is future-tense. Either fix it now or state the block. |

If you catch yourself about to type any of the above, **delete mid-sentence** and replace with the appropriate pattern below.

## Pattern: accepting correct feedback

Just fix it. The code is the acknowledgment.

```
[Push a commit with the fix]
"Fixed. <one-line description of what changed.>"
```

or even shorter:

```
"Fixed in `src/foo.ts:42`."
```

If the fix is non-obvious, one sentence of context:

```
"Fixed. Changed the retry shape from linear to exponential backoff since the
 request graph hits thundering-herd under failures."
```

## Pattern: pushing back on wrong feedback

Technical reasoning, not defensiveness. Evidence over opinion.

```
"Pushed back — the current implementation handles <X> intentionally because
 <Y>. See `src/auth/legacy.ts:87-102` where this path is exercised by
 test `auth.legacy.test.ts:L42`. Removing the guard would break <specific
 scenario>."
```

Or more concisely:

```
"Disagree — grep shows `parseHeader` is called in three places outside
 tests (`foo.ts:L12`, `bar.ts:L88`, `baz.ts:L23`). The 'unused helper'
 claim doesn't match the codebase."
```

## Pattern: asking for clarification

Restate what you understand; name exactly what you don't.

```
"Understood items 1, 2, 3, 6. Need clarification on 4 and 5 before
 implementing — specifically: does item 4 mean <interpretation A> or
 <interpretation B>?"
```

Partial understanding is worse than delay. The cost of asking is one message; the cost of implementing the wrong interpretation is a re-do.

## Pattern: "can't verify without more information"

Explicit limitation, clear follow-up ask.

```
"Can't verify this without running the integration suite against a
 production-like database. Should I spin up the test harness, ask the
 reviewer for more context, or proceed with the current implementation?"
```

This is **not** a pushback. It's honest uncertainty. The reviewer can answer the question and unblock you.

## Pattern: acknowledging a push-back you lost

You pushed back, reviewer produced evidence, you were wrong. State the correction factually.

```
"You were right — I checked `session.ts:L42` and the lock *is* acquired
 before the read. My initial understanding was wrong because I misread
 the import path. Fixing now."
```

**Don't:** long apology, justify the pushback, over-explain the mistake. Factual, brief, move on.

## Pattern: YAGNI rebuttal

When a reviewer suggests "implement X properly" and the feature isn't used, grep first.

```
"Grepped for <endpoint-name> — zero callers outside tests. The reviewer's
 suggestion to add <full stack> assumes this endpoint is in use. It isn't.
 Proposing we remove the endpoint instead of build it out. If there's
 planned usage I'm missing, please link."
```

This is aligned with obra's rule: "You and reviewer both report to me. If we don't need this feature, don't add it."

## Pattern: conflict with prior architectural decisions

Stop and escalate. Do not silently re-decide.

```
"This conflicts with the architectural decision to keep the session
 store in-memory (documented in `docs/arch/session-store.md`). Before
 changing it, we should get the human's input — should I open a discussion?"
```

## Pattern: dismissing bot noise

Bots sometimes flag false positives (unknown dependencies, language-specific patterns they don't understand). State the dismissal reason.

```
"Dismissed — Copilot flagged `import foo from './foo'` as unused, but
 `foo` is re-exported from the barrel file (`index.ts:L12`). Static
 analyzer false positive."
```

## The "delete if you catch yourself" rule

You will catch yourself about to write a forbidden phrase. The rule:

1. See the words forming in the draft.
2. Delete them before they're sent.
3. Replace with the appropriate pattern above.

This is explicit in obra's source: "If you catch yourself about to write 'Thanks': DELETE IT. State the fix instead."

## Common mistakes

| Mistake | Fix |
|---|---|
| "You're absolutely right, let me check that" (softened but still performative) | Just check it. Skip the preamble. |
| "Thanks for the thorough review, I'll address each item" | "Addressing each item below." |
| "Good question! Let me think..." | "Checking — <the actual check>." |
| "I see your point but..." (passive pushback) | "Disagree — <technical reason>." |
| "Sorry for the delay, fixing now" | "Fixed." (assuming it's fixed) or nothing. |

## Why this matters

The author-reviewer relationship is adversarial by design — the reviewer is paid to find what you missed. Performative agreement collapses the adversarial pressure: once you say "you're absolutely right," reversing course later looks like you didn't mean it. Technical-correctness voice keeps every claim defensible, which is what the review process requires.
