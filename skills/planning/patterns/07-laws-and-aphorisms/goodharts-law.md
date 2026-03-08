# Goodhart's Law

## Origin

Charles Goodhart, 1975 (economist, Bank of England): "When a measure becomes a target, it ceases to be a good measure."

Later generalized by Marilyn Strathern: "When a measure becomes a target, it ceases to be a good measure." The formulation is often attributed to both.

## Explanation

Metrics are proxies for the outcomes you actually care about. The moment you incentivize the metric itself — by tying it to performance reviews, bonuses, or team goals — people optimize for the metric rather than the underlying outcome. The metric decouples from reality and becomes meaningless or actively harmful.

In software engineering, this manifests constantly: code coverage targets that produce worthless tests, velocity points that inflate sprint after sprint, lines of code that reward verbosity, and bug counts that discourage proper reporting.

## TypeScript Code Examples

### Bad: Code Coverage Gaming (Target: 80% Coverage)

```typescript
// Developer writes tests purely to hit coverage targets.
// Tests assert nothing meaningful.

// src/pricing.ts
export function calculateDiscount(
  price: number,
  tier: "bronze" | "silver" | "gold"
): number {
  if (tier === "gold") return price * 0.3;
  if (tier === "silver") return price * 0.2;
  return price * 0.1;
}

// __tests__/pricing.test.ts — gaming coverage
describe("calculateDiscount", () => {
  it("should work", () => {
    // "Covers" all branches but tests nothing meaningful
    calculateDiscount(100, "gold");
    calculateDiscount(100, "silver");
    calculateDiscount(100, "bronze");
    // No assertions! Coverage tool marks lines as "covered"
    // because they executed, but no behavior is verified.
  });
});
```

### Good: Meaningful Tests That Happen to Have Good Coverage

```typescript
// __tests__/pricing.test.ts — tests behavior, not lines
describe("calculateDiscount", () => {
  it("applies 30% discount for gold tier", () => {
    expect(calculateDiscount(100, "gold")).toBe(30);
  });

  it("applies 20% discount for silver tier", () => {
    expect(calculateDiscount(100, "silver")).toBe(20);
  });

  it("applies 10% discount for bronze tier (default)", () => {
    expect(calculateDiscount(100, "bronze")).toBe(10);
  });

  it("handles zero price without negative discounts", () => {
    expect(calculateDiscount(0, "gold")).toBe(0);
  });

  it("handles large prices without overflow", () => {
    const result = calculateDiscount(Number.MAX_SAFE_INTEGER, "gold");
    expect(result).toBeGreaterThan(0);
    expect(Number.isFinite(result)).toBe(true);
  });
});
```

### Bad: Velocity Inflation

```typescript
// Sprint 1: Team estimates tasks honestly
// "Add email validation" → 2 points
// "Build user dashboard" → 8 points
// Total: 30 velocity

// Sprint 5: Management uses velocity as a performance metric
// Same work, inflated estimates:
// "Add email validation" → 5 points
// "Build user dashboard" → 13 points
// Total: 65 velocity — "team is improving!"
// Reality: same throughput, inflated numbers.
```

## Common Goodhart Violations in Software

| Metric | Intended Outcome | Gaming Behavior |
|---|---|---|
| Code coverage % | Well-tested code | Tests without assertions, testing getters/setters |
| Velocity points | Predictable delivery | Point inflation, splitting stories artificially |
| Lines of code | Productivity | Verbose code, copy-paste, avoiding refactoring |
| Bug count (low = good) | Quality software | Not reporting bugs, reclassifying as "features" |
| PR merge speed | Fast delivery | Rubber-stamp reviews, skipping thoroughness |
| Deployment frequency | CI/CD maturity | No-op deployments, config changes counted as deploys |
| MTTR (mean time to recovery) | Operational excellence | Marking incidents resolved before actually fixed |

## Alternatives and Better Approaches

- **Use metrics as diagnostic tools, not targets.** Track coverage to find untested areas, not to gate PRs.
- **Combine multiple metrics.** No single number captures quality. Use a dashboard, not a scoreboard.
- **Measure outcomes, not outputs.** Customer satisfaction, incident frequency, and time-to-resolution are harder to game.
- **Rotate metrics.** Change what you measure periodically so teams cannot settle into gaming patterns.
- **Qualitative assessment.** Code reviews, architecture reviews, and retrospectives catch what metrics miss.

## When NOT to Apply

- **Minimum quality bars:** Some thresholds are genuinely useful. "Zero tests" is worse than "tests-with-coverage-target," even with gaming.
- **Regulatory compliance:** Certain metrics must be tracked and targeted regardless of gaming risk.
- **Early-stage teams:** New teams may need training wheels — explicit targets help build habits, even imperfect ones.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| No metric targets | Eliminates gaming | No accountability, no visibility |
| Strict metric targets | Clear expectations | Guaranteed gaming behavior |
| Metrics as diagnostics only | Honest measurement | Harder to set goals for managers |
| Outcome-based metrics | Aligned with business value | Harder to measure, lagging indicators |

## Real-World Consequences

- **Wells Fargo (2016):** Employees opened millions of fake accounts to hit account-opening targets. The metric (accounts opened) was a proxy for customer growth, but became a target that destroyed customer trust.
- **Soviet factories:** Nail factories measured by weight produced fewer, heavier nails. Measured by count, they produced tiny useless nails.
- **Stack Overflow reputation:** Gameable through strategic answering of easy questions, leading to a culture that sometimes optimizes for points over helpfulness.
- **Google's 20% time:** When "20% projects" became a factor in performance reviews, the original spirit of free exploration was compromised.

## Further Reading

- Goodhart, C. (1975). "Problems of Monetary Management: The UK Experience"
- Strathern, M. (1997). "'Improving Ratings': Audit in the British University System"
- Muller, J. (2018). *The Tyranny of Metrics*
- Austin, R. (1996). *Measuring and Managing Performance in Organizations*
- Forsgren, N., Humble, J., & Kim, G. (2018). *Accelerate* — on meaningful engineering metrics
