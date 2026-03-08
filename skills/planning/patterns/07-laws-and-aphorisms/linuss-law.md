# Linus's Law

## Origin

Eric S. Raymond, 1999, *The Cathedral and the Bazaar*: "Given enough eyeballs, all bugs are shallow." Named after Linus Torvalds, who demonstrated it with the Linux kernel development model.

More precisely: "Given a large enough beta-tester and co-developer base, almost every problem will be characterized quickly and the fix obvious to someone."

## Explanation

When many people review code, the probability that at least one person will spot a bug increases dramatically. Different reviewers bring different expertise, different mental models, and different assumptions. A bug that is invisible to the author — because they are trapped in their own perspective — may be immediately obvious to a fresh pair of eyes.

This is the theoretical foundation for open-source development, code review practices, and "many eyes" security auditing.

However, the law has limits. "Enough eyeballs" must be qualified: they must be knowledgeable, motivated, and actually reading the code carefully.

## TypeScript Code Examples

### Bad: Code Reviewed by Nobody

```typescript
// Lone developer, no review process. Subtle bug ships to production.

export function calculateTax(
  amount: number,
  rate: number,
  exemptions: string[]
): number {
  if (exemptions.includes("nonprofit")) return 0;
  if (exemptions.includes("educational")) return amount * rate * 0.5;

  // Bug: rate is expected as decimal (0.08) but some callers pass percentage (8)
  // A second pair of eyes would ask: "What format is `rate` in?"
  return amount * rate;
}

// Called with calculateTax(100, 8, []) → returns 800 instead of 8
// No reviewer, no type safety on the rate format, ships to production.
```

### Good: Multiple Reviewers Catch Different Issues

```typescript
// Strong typing prevents the rate format ambiguity
// Code review catches semantic issues types cannot

/** Tax rate as a decimal between 0 and 1 (e.g., 0.08 for 8%) */
type TaxRate = number & { readonly __brand: "TaxRate" };

export function createTaxRate(percentage: number): TaxRate {
  if (percentage < 0 || percentage > 100) {
    throw new RangeError(`Tax rate must be 0-100%, got ${percentage}%`);
  }
  return (percentage / 100) as TaxRate;
}

export function calculateTax(
  amount: number,
  rate: TaxRate,
  exemptions: ReadonlyArray<string>
): number {
  // Reviewer A noticed: exemptions should be an enum, not raw strings
  // Reviewer B noticed: what about partial exemptions?
  // Reviewer C noticed: floating point — use integer cents
  if (exemptions.includes("nonprofit")) return 0;
  if (exemptions.includes("educational")) return Math.round(amount * rate * 50) / 100;
  return Math.round(amount * rate * 100) / 100;
}
```

### Code Review as "Many Eyeballs"

```typescript
// review-checklist.ts — systematic review increases eyeball effectiveness

interface ReviewChecklist {
  readonly security: {
    inputValidation: boolean;
    sqlInjection: boolean;
    xss: boolean;
    authorizationChecks: boolean;
  };
  readonly correctness: {
    edgeCases: boolean;
    errorHandling: boolean;
    concurrency: boolean;
    offByOne: boolean;
  };
  readonly maintainability: {
    naming: boolean;
    complexity: boolean;
    testCoverage: boolean;
    documentation: boolean;
  };
}

// Different reviewers focus on different sections.
// Security engineer checks security. Domain expert checks correctness.
// Senior dev checks maintainability. Many eyeballs, structured focus.
```

## When the Law Holds

- **Active open-source projects:** Linux, Chromium, and PostgreSQL benefit from thousands of contributors reviewing code.
- **Structured code review processes:** Google's "readability" reviews, where code must be approved by a certified reviewer.
- **Security audits with diverse teams:** Multiple security researchers with different specializations reviewing the same codebase.
- **Pair programming:** The most immediate form of "two eyeballs."

## When the Law Fails

The law has important failure modes:

1. **Bystander effect:** If everyone assumes someone else will review carefully, nobody does.
2. **Complexity barrier:** If code is too complex, eyeballs glaze over. (See: OpenSSL before Heartbleed — technically open source, but few people read it.)
3. **Rubber-stamp reviews:** "LGTM" without actual reading provides zero additional eyeballs.
4. **Homogeneous reviewers:** If all reviewers have the same background, they share the same blind spots.
5. **Volume overload:** Too many changes too fast means reviews are cursory.

## Alternatives and Related Concepts

- **Formal verification:** Mathematical proof that code is correct — does not depend on human eyeballs.
- **Static analysis:** Automated "eyeballs" that never get tired.
- **Fuzzing:** Automated testing that explores edge cases humans miss.
- **Pair programming:** Two eyeballs in real time, maximum knowledge transfer.
- **Mob programming:** N eyeballs in real time, maximum shared understanding.

## When NOT to Apply

- **Speed-critical prototypes:** Review overhead slows exploration. Review before merge to main, not before every experiment.
- **Solo projects with no future readers:** Personal scripts do not benefit from review.
- **When eyeballs are not qualified:** Random reviewers without domain knowledge add noise, not insight.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Mandatory 2+ reviewer approval | High defect detection | Slower merge velocity |
| Open-source "many eyes" model | Diverse perspectives, community trust | Most eyes skim; few read deeply |
| Pair programming | Real-time review, knowledge sharing | 2x developer cost per line |
| Automated analysis + review | Best of both worlds | Tool setup overhead, false positives |

## Real-World Consequences

- **Linux kernel:** Thousands of contributors, rigorous review. Relatively few critical bugs for its complexity.
- **OpenSSL / Heartbleed (2014):** Nominally open source with "many eyes," but the code was maintained by two part-time volunteers. The "eyes" were theoretical, not actual.
- **Google's code review culture:** Every change reviewed by at least one other engineer. Studies show this catches 15-30% of defects before they ship.
- **Log4Shell (2021):** The Log4j vulnerability existed for years in widely-used open-source code. Many eyeballs were using the library but not reading its source.

## The Uncomfortable Nuance

The law should be restated: "Given enough *qualified, motivated* eyeballs, most bugs are shallow." The qualification matters enormously. Open source does not automatically mean reviewed. Used widely does not mean read carefully.

## Further Reading

- Raymond, E.S. (1999). *The Cathedral and the Bazaar*
- Bacchelli, A. & Bird, C. (2013). "Expectations, Outcomes, and Challenges of Modern Code Review"
- Rigby, P. & Bird, C. (2013). "Convergent Contemporary Software Peer Review Practices"
- Wheeler, D. (2015). "How to Evaluate Open Source Software / Free Software"
