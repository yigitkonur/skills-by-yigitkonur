# Sturgeon's Law

## Origin

Theodore Sturgeon, science fiction author, 1957: "Ninety percent of everything is crud."

Originally a retort to critics who dismissed science fiction as low quality. Sturgeon's point: 90% of *everything* — literature, film, music, and yes, software — is crud. Science fiction is no worse than the baseline.

## Explanation

Most software, most libraries, most frameworks, most blog posts, most Stack Overflow answers, most npm packages, and most architectural advice is mediocre or worse. This is not cynicism — it is a statistical reality. The implication is practical: you must develop strong evaluation skills because the default quality of anything you encounter is likely poor.

This applies to your own code too. Most of what you write is not your best work. The skill is knowing which 10% matters and investing quality there.

## TypeScript Code Examples

### Bad: Blindly Adopting a Popular npm Package

```typescript
// "This package has 10,000 weekly downloads, it must be good!"
// Downloads !== quality. Sturgeon's Law applies to npm too.

import { superValidate } from "super-validator-pro-ultimate"; // 10k downloads

// Actual source of the package:
// export function superValidate(input: any): boolean {
//   return input !== null && input !== undefined; // That's it.
//   // No actual validation. 10k downloads from bots and tutorials.
// }

const isValid = superValidate(userInput);
// You now depend on a package that does essentially nothing.
```

### Good: Evaluating Libraries Before Adoption

```typescript
// library-evaluation.ts — systematic quality assessment

interface LibraryEvaluation {
  readonly name: string;
  readonly criteria: {
    // Activity signals
    lastCommitDate: Date;
    openIssueCount: number;
    issueResponseTimeAvg: string;
    maintainerCount: number;

    // Quality signals
    hasTypeScriptTypes: boolean;
    testCoverage: "none" | "minimal" | "moderate" | "comprehensive";
    ciPipeline: boolean;
    securityAudited: boolean;

    // Community signals
    githubStars: number;          // Vanity metric, but non-zero signal
    dependedOnByCount: number;    // Better signal: who uses this?
    stackOverflowQuestions: number;

    // Code quality signals
    bundleSize: string;
    dependencies: number;         // Fewer is better
    codeReadability: "low" | "medium" | "high"; // Read the source!
  };
  readonly verdict: "adopt" | "trial" | "assess" | "hold" | "reject";
  readonly reasoning: string;
}

// Example evaluation:
const zodEvaluation: LibraryEvaluation = {
  name: "zod",
  criteria: {
    lastCommitDate: new Date("2025-11-15"),
    openIssueCount: 180,
    issueResponseTimeAvg: "2 days",
    maintainerCount: 3,
    hasTypeScriptTypes: true,     // Written in TypeScript
    testCoverage: "comprehensive",
    ciPipeline: true,
    securityAudited: false,
    githubStars: 34000,
    dependedOnByCount: 15000,
    stackOverflowQuestions: 2500,
    bundleSize: "13kb gzipped",
    dependencies: 0,              // Zero dependencies — excellent
    codeReadability: "high",
  },
  verdict: "adopt",
  reasoning: "Zero deps, TS-native, active maintenance, huge ecosystem. In the top 10%.",
};
```

### Applying Sturgeon's Law to Code Review

```typescript
// Not all code in a PR deserves equal review attention.
// Focus on the 10% that matters: the core logic.

// These are probably fine (boilerplate):
export interface UserDTO {
  id: string;
  name: string;
  email: string;
}

// THIS is where bugs hide — review this intensely:
export function reconcilePayments(
  invoices: ReadonlyArray<Invoice>,
  payments: ReadonlyArray<Payment>
): ReconciliationResult {
  // Complex business logic with financial implications.
  // This is the 10% that must be excellent.
  // Spend 90% of review time here.
}
```

## Applying Sturgeon's Law

| Domain | The 90% Crud | The 10% That Matters |
|---|---|---|
| npm packages | Abandoned, unmaintained, trivial | Well-maintained, tested, documented |
| Blog posts | Outdated, copied, superficial | Original research, real experience |
| Stack Overflow | Incorrect, outdated, cargo-culted | Upvoted, explained, recently verified |
| Your codebase | Boilerplate, CRUD, config | Core domain logic, algorithms, security |
| Architecture advice | Buzzword-driven, context-free | Battle-tested, trade-off aware |
| Conference talks | Marketing, hype, recycled content | Deep technical insight, honest failure stories |

## Alternatives and Related Concepts

- **Pareto Principle (80/20 rule):** Similar distribution. 20% of code contains 80% of bugs.
- **Signal vs. Noise:** Sturgeon's Law is about the signal-to-noise ratio of everything.
- **ThoughtWorks Technology Radar:** A curated assessment specifically designed to filter Sturgeon's 90%.
- **Lindy Effect:** Things that have survived long are more likely to be in the top 10%.

## When NOT to Apply

- **Curated environments:** If you are working within a well-maintained monorepo with strict quality standards, the 90/10 ratio may be much better.
- **Expert-recommended tools:** A list curated by a trusted expert has already filtered the crud.
- **Standards and specifications:** RFCs, ISO standards, and language specifications have higher quality floors.
- **Your best work:** Do not use Sturgeon's Law as an excuse for low quality. Aim for the top 10%.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Evaluate everything rigorously | Adopt only quality tools/code | Slow, expensive, analysis paralysis |
| Trust popularity metrics | Fast decisions | Popular does not mean good |
| Build everything yourself | Full quality control | Reinventing wheels, NIH syndrome |
| Use curated lists/radars | Pre-filtered quality | May miss niche solutions |

## Real-World Consequences

- **npm security incidents:** Typosquatting, malicious packages, and abandoned dependencies are all manifestations of the 90% crud on npm.
- **Left-pad incident (2016):** The ecosystem depended on a trivial package because nobody evaluated whether it belonged in the 10%.
- **WordPress plugin ecosystem:** Thousands of plugins, most unmaintained or insecure. The few excellent ones carry the ecosystem.
- **App stores:** Millions of apps, vast majority are low-quality clones. Curation and review are essential.

## The Meta-Application

Sturgeon's Law applies to advice about Sturgeon's Law. Most "hot takes" about software quality are themselves in the 90%. Develop your own evaluation framework, test it against reality, and refine it over time.

## Further Reading

- Sturgeon, T. (1957). "On Hand" column in *Venture Science Fiction*
- Raymond, E.S. (2003). *The Art of Unix Programming* — on evaluating software quality
- Taleb, N.N. (2012). *Antifragile* — on the Lindy Effect and quality filters
- ThoughtWorks Technology Radar — quarterly curated technology assessment
