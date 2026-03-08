# Cunningham's Law

## Origin

Attributed to Ward Cunningham (inventor of the wiki), as stated by Steven McGeady: "The best way to get the right answer on the Internet is not to ask a question; it's to post the wrong answer."

Cunningham himself has noted he did not originate this phrasing, but the observation bears his name.

## Explanation

People are more motivated to correct errors than to answer questions. Post a question and you might get silence. Post a wrong answer and people will rush to correct you with detailed, accurate information. This is a social dynamic rooted in how humans process information: errors trigger a stronger response than gaps.

In software engineering, this principle extends beyond internet forums into code reviews, design proposals, and architecture discussions. A draft proposal with deliberate imperfections generates more useful feedback than a blank page asking for input.

## TypeScript Code Examples

### Bad: Asking for Input on a Blank Slate

```typescript
// Slack message: "Hey team, how should we design the caching layer?"
// Result: silence for two days, then a vague "maybe Redis?"

// Empty design document:
/**
 * Caching Strategy
 * ================
 *
 * TODO: Need input from the team on:
 * - What cache store to use?
 * - What TTL values?
 * - How to handle invalidation?
 *
 * Please comment below.
 */

// Nobody comments. The blank page is not motivating.
```

### Good: Post an Imperfect Proposal to Trigger Correction

```typescript
// Design doc with a concrete (intentionally imperfect) proposal:

/**
 * Caching Strategy — DRAFT v0.1
 * ==============================
 *
 * Proposal: Use in-memory Map for all caching.
 * TTL: 24 hours for everything.
 * Invalidation: None — let entries expire naturally.
 */

// Implementation:
const cache = new Map<string, { value: unknown; expiresAt: number }>();

export function cacheGet<T>(key: string): T | undefined {
  const entry = cache.get(key);
  if (!entry) return undefined;
  if (Date.now() > entry.expiresAt) {
    cache.delete(key);
    return undefined;
  }
  return entry.value as T;
}

export function cacheSet(key: string, value: unknown): void {
  cache.set(key, {
    value,
    expiresAt: Date.now() + 24 * 60 * 60 * 1000, // 24h for everything
  });
}

// Responses flood in within hours:
// "In-memory Map won't survive restarts!" → suggests Redis
// "24h TTL for user sessions is a security risk!" → suggests 15 minutes
// "No invalidation means stale prices for 24 hours!" → suggests event-driven invalidation
// "Map has no size limit — this will OOM!" → suggests LRU cache

// Result: detailed, specific feedback that a blank question never generates.
```

### Using Cunningham's Law in Code Reviews

```typescript
// Submit a PR with a known suboptimal approach to get
// reviewers to suggest the correct one.

// Your PR (draft):
export function findUser(users: User[], id: string): User | undefined {
  // Linear search — O(n)
  return users.find((u) => u.id === id);
}

// Reviewer immediately responds:
// "This is O(n) on every call. We should use a Map for O(1) lookup."
//
// You "improve" it based on feedback:
const userIndex = new Map<string, User>();

export function indexUsers(users: ReadonlyArray<User>): void {
  for (const user of users) {
    userIndex.set(user.id, user);
  }
}

export function findUser(id: string): User | undefined {
  return userIndex.get(id);
}

// The reviewer feels good about catching the issue.
// You get the correct approach with a detailed explanation.
// The codebase gets better code.
```

## Applications in Software Engineering

| Context | "Wrong Answer" Approach | Feedback Generated |
|---|---|---|
| Architecture design | Propose a simple, incomplete design | Team identifies missing requirements |
| API design | Share a draft with obvious gaps | Consumers identify their actual needs |
| Tech debt prioritization | Propose refactoring the wrong thing | Team identifies what actually hurts |
| Estimation | Propose an obviously too-short timeline | Team reveals hidden complexity |
| Documentation | Write docs with known errors | Readers correct and improve them (wiki model) |
| Retrospectives | State a provocative opinion | Team engages deeply with the real issues |

## Alternatives and Related Concepts

- **Straw Man Proposal:** Present a weak proposal to generate discussion — Cunningham's Law formalized.
- **RFC (Request for Comments):** The entire RFC process is Cunningham's Law at scale — propose something, let the community correct it.
- **Spike Solutions:** Build a quick, imperfect implementation to learn what the real solution should be.
- **Design Thinking Prototyping:** Build a rough prototype to get concrete feedback.
- **Amazon's Working Backwards:** Write the press release first (imperfect), then iterate.

## When NOT to Apply

- **Safety-critical decisions:** Do not propose a wrong medical dosage algorithm to "generate feedback." Some domains require getting it right the first time.
- **Trust erosion:** If overused, people will stop trusting your proposals. "Is this another straw man or do they actually believe this?"
- **When you are the expert:** If you genuinely know the answer, posting the wrong one wastes everyone's time and erodes your credibility.
- **Regulatory or legal context:** "I posted the wrong compliance approach to get feedback" does not play well with auditors.
- **Performance reviews:** Do not submit bad code to trigger corrections. Reviewers will think you lack competence.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Post wrong answer / draft proposal | Generates detailed, motivated feedback | May erode trust if overused |
| Ask open-ended question | Respects others' expertise | Often generates silence |
| Post perfect answer | Demonstrates competence | No feedback loop, may miss blind spots |
| Structured RFC process | Formal, documented feedback | Slower, more overhead |

## Real-World Consequences

- **Wikipedia:** The entire model is Cunningham's Law at scale. Anyone can edit (post a "wrong answer"), and the community corrects toward accuracy. It works remarkably well for most topics.
- **Linux kernel mailing list:** Linus Torvalds frequently posts strong (sometimes wrong) opinions to provoke detailed technical responses from maintainers.
- **Stack Overflow:** Wrong answers with high visibility get corrected faster than questions get answered. The correction often contains more detail than a direct answer would.
- **Open-source RFCs:** Rust, Python (PEPs), and Go use proposal processes where drafts generate detailed community feedback.

## The Meta-Lesson

Cunningham's Law is really about lowering the activation energy for participation. A blank page asks people to generate something from nothing (high energy). A flawed draft asks them to improve something that exists (low energy). Humans are better editors than creators.

## Further Reading

- Cunningham, W. — wiki.c2.com (the original wiki, full of this dynamic)
- McGeady, S. — attribution of the law
- Raymond, E.S. (1999). *The Cathedral and the Bazaar* — open-source feedback dynamics
- Surowiecki, J. (2004). *The Wisdom of Crowds*
