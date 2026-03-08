# The Peter Principle

## Origin

Laurence J. Peter and Raymond Hull, 1969, *The Peter Principle*: "In a hierarchy, every employee tends to rise to his level of incompetence."

Originally presented as satire, but subsequent research has confirmed it as an empirical phenomenon. A 2018 study by Benson, Li, and Shue analyzing 53,000 sales employees found strong evidence: the best salespeople became the worst managers.

## Explanation

People are promoted based on performance in their current role, not their suitability for the next one. An excellent developer is promoted to tech lead, then engineering manager, then director — each promotion moving them further from what they are good at. Eventually they reach a role where they are no longer competent, and there they stay.

In software engineering, this manifests most visibly in the **developer-to-manager transition**: a brilliant individual contributor is promoted to manage people, a fundamentally different skill set, and struggles.

## TypeScript Code Examples

### Bad: Promoting the Best Coder to Lead Without Support

```typescript
// Sarah: Best developer on the team. Writes elegant code.
// Promotion: "Sarah, you're now Tech Lead!"

// Before: Sarah's day
const sarahsDay = {
  "9:00": "Deep focus: implementing search algorithm",
  "10:00": "Deep focus: continued",
  "11:00": "Code review: one PR, thorough",
  "12:00": "Lunch, reading about new TypeScript features",
  "13:00": "Pair programming with junior dev",
  "14:00": "Deep focus: writing tests",
  "15:00": "Deep focus: refactoring module",
  "16:00": "Planning tomorrow's work",
};
// Output: high-quality code, happy developer.

// After: Sarah's day as Tech Lead
const sarahsNewDay = {
  "9:00": "Standup with team",
  "9:30": "1:1 with underperforming developer (unprepared for this)",
  "10:00": "Sprint planning meeting",
  "11:00": "Architecture review with other leads",
  "12:00": "Lunch at desk, answering Slack messages",
  "13:00": "Stakeholder sync: explain delays (hates this)",
  "14:00": "Hiring: resume screening",
  "15:00": "1:1 with PM about priorities",
  "15:30": "Incident response coordination",
  "16:00": "Finally opens IDE. Writes zero code. Frustrated.",
};
// Output: mediocre leadership, unhappy former-developer.
```

### Good: Dual Career Ladder

```typescript
// Define parallel tracks so promotion does not require role change

interface CareerLadder {
  readonly individualContributor: ReadonlyArray<{
    title: string;
    focus: string;
    codeContribution: string;
  }>;
  readonly management: ReadonlyArray<{
    title: string;
    focus: string;
    codeContribution: string;
  }>;
}

const engineeringLadder: CareerLadder = {
  individualContributor: [
    {
      title: "Software Engineer",
      focus: "Deliver well-tested features within a team",
      codeContribution: "Daily hands-on coding",
    },
    {
      title: "Senior Software Engineer",
      focus: "Technical leadership within a team, mentoring",
      codeContribution: "Daily coding, PR reviews, design docs",
    },
    {
      title: "Staff Engineer",
      focus: "Cross-team technical influence, architecture",
      codeContribution: "Strategic coding, prototypes, key systems",
    },
    {
      title: "Principal Engineer",
      focus: "Organization-wide technical direction",
      codeContribution: "Selective, high-impact contributions",
    },
    {
      title: "Distinguished Engineer",
      focus: "Industry-level technical leadership",
      codeContribution: "Research, standards, foundational systems",
    },
  ],
  management: [
    {
      title: "Tech Lead",
      focus: "Team delivery and technical quality",
      codeContribution: "50% coding, 50% coordination",
    },
    {
      title: "Engineering Manager",
      focus: "People management, team health, delivery",
      codeContribution: "Minimal — focus on people and process",
    },
    {
      title: "Senior Engineering Manager",
      focus: "Multiple teams, hiring, organizational design",
      codeContribution: "None expected",
    },
    {
      title: "Director of Engineering",
      focus: "Department strategy, cross-functional alignment",
      codeContribution: "None expected",
    },
  ],
};

// Sarah stays on the IC track as Staff Engineer.
// She gets the same pay and respect as an Engineering Manager.
// She keeps doing what she is excellent at.
```

## The Tech Lead Transition Trap

The most common Peter Principle violation in tech:

```
Great coder  →  Promoted to Tech Lead  →  Expected to:
  ✓ Still write code (less time)
  ✓ Review all PRs (bottleneck)
  ✓ Mentor juniors (never taught how)
  ✓ Run meetings (no training)
  ✓ Negotiate with PMs (new skill)
  ✓ Handle conflicts (never done before)
  ✓ Estimate timelines (for others' work)

Skills that made them great:        Skills they now need:
  - Deep technical focus              - Context switching
  - Individual problem-solving        - Delegation
  - Code elegance                     - Communication
  - Long uninterrupted sessions       - Constant interruptions
```

## Alternatives and Mitigations

- **Dual career ladder:** Separate IC and management tracks with equivalent compensation.
- **Trial periods:** Let people "try" management for 3-6 months with a safe return path.
- **Management training before promotion:** Teach the skills needed before the role change.
- **Promote based on demonstrated next-level skills:** Not just current-role performance.
- **Pendulum career paths:** Allow people to move between IC and management over their career.

## When NOT to Apply

- **People who genuinely want to manage:** Not everyone promoted to management is a Peter Principle victim. Some people thrive in leadership and seek it out.
- **Small startups:** Everyone wears multiple hats. Rigid career ladders are premature.
- **Temporary leadership roles:** Tech lead for a project, then back to IC — this is healthy rotation, not permanent promotion.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Promote top performers to management | Rewards excellence, seems fair | Loses a great IC, may gain a bad manager |
| Dual career ladder | People stay in their strength zone | Hard to maintain pay/prestige parity |
| Trial management periods | Low-risk exploration | Disrupts team, temporary leaders lack authority |
| External management hires | Professional managers from day one | Cultural mismatch, "they don't understand code" |

## Real-World Consequences

- **The CTO who cannot stop coding:** A developer promoted through management ranks who still tries to make technical decisions better handled by the team. Micromanagement disguised as "technical leadership."
- **The manager who cannot give feedback:** A developer promoted for code quality who has never had a difficult conversation. Performance problems fester because the manager avoids confrontation.
- **Apple's dual ladder:** Apple maintains parallel IC and management tracks. "Apple Fellow" is an IC role at the VP level, explicitly preventing the Peter Principle.
- **Valve's flat structure (attempt):** Valve tried to eliminate hierarchy entirely, but informal hierarchies emerged — and without formal career paths, the Peter Principle manifested in invisible ways.

## Further Reading

- Peter, L. & Hull, R. (1969). *The Peter Principle*
- Benson, A., Li, D., & Shue, K. (2018). "Promotions and the Peter Principle" — NBER Working Paper
- Larson, W. (2019). *An Elegant Puzzle: Systems of Engineering Management*
- Fournier, C. (2017). *The Manager's Path*
- Reilly, T. (2022). *The Staff Engineer's Path*
