# Option Design and Decision Quality

## Read this if
- Multiple options exist.
- Trade-offs are unclear.
- Discussion is driven by preference rather than criteria.

## Planning vision for this stage
Think like a decision architect: create fair comparisons, not just arguments.

## Decision sequence

1. Classify decision (reversible or hard-to-reverse).
2. Generate 2-4 viable options (including minimal option).
3. Define criteria and weights.
4. Evaluate options transparently.
5. Choose and document trade-offs.

## Method steering

### Decision matrix
Best for structured comparison.
- Thinking posture: "Make criteria explicit and weighted."

### Hard choice model
Best when values conflict and no option clearly wins.
- Thinking posture: "Choose your values, not fake certainty."

### Second-order thinking
Best when long-term consequences matter.
- Thinking posture: "What chain reaction follows this decision?"

### Six Thinking Hats
Best for broadening perspectives in group decisions.
- Thinking posture: "Separate data, risk, emotion, creativity, optimism, and process."

### Cynefin framework
Best for selecting decision mode by context complexity.
- Thinking posture: "Analyze in complicated contexts, experiment in complex contexts, stabilize in chaotic contexts."

### Zwicky box (option expansion)
Best when options feel too narrow.
- Thinking posture: "Generate combinations before eliminating candidates."

---

## Weighted decision matrix template

Use when comparing 3+ options across measurable criteria. The formula:

> **Score = Σ(Criterion Score × Weight)**

Each criterion is scored 1–5 (1 = poor, 5 = excellent). Weights must sum to 100%.

### Blank template

| Criterion | Weight | Option A | Weighted | Option B | Weighted | Option C | Weighted |
|-----------|--------|----------|----------|----------|----------|----------|----------|
| _name_    | __%    | _/5      | __       | _/5      | __       | _/5      | __       |
| _name_    | __%    | _/5      | __       | _/5      | __       | _/5      | __       |
| _name_    | __%    | _/5      | __       | _/5      | __       | _/5      | __       |
| **Total** | 100%   |          | **__**   |          | **__**   |          | **__**   |

### Worked example: Choosing a primary database

**Context:** E-commerce platform expecting 10M users in 2 years. Team of 8 backend engineers, most experienced with SQL.

| Criterion          | Weight | PostgreSQL | Weighted | MongoDB | Weighted | DynamoDB | Weighted |
|--------------------|--------|------------|----------|---------|----------|----------|----------|
| Query flexibility  | 30%    | 5          | 1.50     | 4       | 1.20     | 2        | 0.60     |
| Scalability        | 25%    | 3          | 0.75     | 4       | 1.00     | 5        | 1.25     |
| Team expertise     | 20%    | 5          | 1.00     | 2       | 0.40     | 1        | 0.20     |
| Cost               | 15%    | 4          | 0.60     | 3       | 0.45     | 3        | 0.45     |
| Ecosystem/tooling  | 10%    | 5          | 0.50     | 4       | 0.40     | 3        | 0.30     |
| **Total**          | 100%   |            | **4.35** |         | **3.45** |          | **2.80** |

**Reading the result:** PostgreSQL wins at 4.35. The gap is significant (0.90 over MongoDB), giving high confidence. If the gap were < 0.3, treat options as effectively tied and use a tiebreaker (e.g., reversibility, team morale).

**Sensitivity check:** Ask "What weight change would flip the winner?" Here, Scalability would need to be ~55% for DynamoDB to win — unlikely given the requirements. This confirms the decision is robust.

---

## Architecture Decision Record (ADR) template

ADRs create a durable log of *why* decisions were made, not just *what* was decided. Store them in `docs/adr/` or `decisions/` in the repo.

### Template

```markdown
# ADR-NNNN: [Title]

## Status
Proposed | Accepted | Deprecated | Superseded by ADR-XXXX

## Date
YYYY-MM-DD

## Context
[What forces are at play? What constraints exist? What problem triggered this decision?]

## Decision
[What we decided to do. State it as a direct, active sentence.]

## Alternatives Considered

### Alternative 1: [Name]
- Description: [What this option involves]
- Rejected because: [Specific reason]

### Alternative 2: [Name]
- Description: [What this option involves]
- Rejected because: [Specific reason]

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Trade-off 1]
- [Trade-off 2]

### Risks
- [Risk and mitigation]

## Review Date
[When to revisit: e.g., after 6 months or when throughput exceeds X]
```

### Worked example

```markdown
# ADR-0012: Use Kafka over RabbitMQ for event streaming

## Status
Accepted

## Date
2024-09-15

## Context
Our order processing pipeline currently uses synchronous HTTP calls between
services. At 2,000 orders/minute we see cascading failures when the inventory
service is slow. We need an asynchronous event backbone that supports:
- At-least-once delivery with ordering guarantees per partition
- Event replay for new consumers (30-day retention)
- Throughput headroom to 50,000 events/second

## Decision
Adopt Apache Kafka (managed via Confluent Cloud) as the event streaming
platform for all inter-service domain events, starting with OrderPlaced,
InventoryReserved, and PaymentProcessed.

## Alternatives Considered

### Alternative 1: RabbitMQ
- Description: Lightweight message broker with AMQP protocol support.
- Rejected because: No native event replay. Adding replay requires
  plugin workarounds (Shovel + external store). Partition-level ordering
  is not a first-class concept.

### Alternative 2: AWS SNS + SQS
- Description: Fully managed pub/sub with queue consumers.
- Rejected because: No replay capability. Message ordering requires
  FIFO queues with 300 msg/s throughput limit per group — insufficient
  for our projected volume.

### Alternative 3: Pulsar
- Description: Cloud-native messaging with tiered storage.
- Rejected because: Team has zero operational experience. Community
  and tooling ecosystem is smaller. Hiring would be harder.

## Consequences

### Positive
- Event replay lets new services bootstrap from historical events
- Partition-based ordering simplifies inventory consistency logic
- Confluent Cloud reduces operational burden vs self-hosted

### Negative
- Higher infrastructure cost (~$2,400/month vs ~$800 for RabbitMQ)
- Kafka consumer model is more complex; team needs training (~2 weeks)
- Schema evolution requires investing in a schema registry

### Risks
- Vendor lock-in to Confluent. Mitigation: use standard Kafka protocol;
  migration to self-hosted or Redpanda is feasible.

## Review Date
2025-03-15 (after 6 months) or when event volume exceeds 30,000/second.
```

---

## Pros/Cons analysis framework

Use for fast qualitative comparison when a full decision matrix feels too heavy. Rate each item's impact to elevate the analysis beyond a flat list.

### Template

| Category | Item | Impact | Notes |
|----------|------|--------|-------|
| ✅ Pro   | _description_ | 🔴 High / 🟡 Medium / 🟢 Low | _context_ |
| ✅ Pro   | _description_ | 🔴 / 🟡 / 🟢 | _context_ |
| ❌ Con   | _description_ | 🔴 / 🟡 / 🟢 | _context_ |
| ❌ Con   | _description_ | 🔴 / 🟡 / 🟢 | _context_ |
| ⚠️ Risk  | _description_ | 🔴 / 🟡 / 🟢 | _mitigation_ |

**Reading the result:**
- Count high-impact items per side. A single 🔴 Con can outweigh three 🟢 Pros.
- If all items are 🟡, the decision is low-stakes — pick fast and move on.
- Flag any 🔴 Risk without a mitigation as a blocker.

### Worked example: Adopting a monorepo

| Category | Item | Impact | Notes |
|----------|------|--------|-------|
| ✅ Pro   | Single CI pipeline, unified versioning | 🔴 High | Eliminates cross-repo version drift |
| ✅ Pro   | Atomic cross-package refactors | 🟡 Medium | Saves ~2h per breaking change |
| ✅ Pro   | Shared tooling config (lint, test, build) | 🟢 Low | Minor DX improvement |
| ❌ Con   | CI build times increase as repo grows | 🔴 High | Need task caching (Turborepo/Nx) |
| ❌ Con   | Git clone size grows over time | 🟡 Medium | Mitigate with shallow clones |
| ❌ Con   | Steeper onboarding for new hires | 🟢 Low | Add CONTRIBUTING.md walkthrough |
| ⚠️ Risk  | Permission boundaries blur across teams | 🟡 Medium | Use CODEOWNERS per package |

---

## Technology comparison template

Use this feature-matrix format when evaluating tools, libraries, or frameworks side by side.

### Template

| Feature / Attribute   | Tool A | Tool B | Tool C | Notes |
|-----------------------|--------|--------|--------|-------|
| License               |        |        |        |       |
| Language / Runtime    |        |        |        |       |
| Maturity (years)      |        |        |        |       |
| GitHub stars / activity |      |        |        |       |
| Last release          |        |        |        |       |
| Key feature 1         | ✅/❌/🟡 | ✅/❌/🟡 | ✅/❌/🟡 |   |
| Key feature 2         | ✅/❌/🟡 | ✅/❌/🟡 | ✅/❌/🟡 |   |
| Key feature 3         | ✅/❌/🟡 | ✅/❌/🟡 | ✅/❌/🟡 |   |
| Learning curve        | Low/Med/High | Low/Med/High | Low/Med/High | |
| Community support     | Low/Med/High | Low/Med/High | Low/Med/High | |
| Hosting / pricing     |        |        |        |       |
| Integration with stack |       |        |        |       |

Legend: ✅ = full support, 🟡 = partial / plugin, ❌ = not supported

### Worked example: Choosing a CSS framework

| Feature / Attribute    | Tailwind CSS | Bootstrap 5 | CSS Modules | Notes |
|------------------------|-------------|-------------|-------------|-------|
| License                | MIT         | MIT         | MIT         |       |
| Approach               | Utility-first | Component-based | Scoped CSS | Philosophical difference |
| Maturity               | 7 years     | 13 years    | 9 years     |       |
| Bundle size (gzip)     | ~10 KB (purged) | ~22 KB | 0 KB (no runtime) | Tailwind requires purge step |
| Design customization   | ✅           | 🟡           | ✅           | Bootstrap theming is limited |
| Component library      | 🟡 (Headless UI) | ✅      | ❌           | Bootstrap ships prebuilt components |
| Framework agnostic     | ✅           | 🟡           | ✅           | Bootstrap JS assumes jQuery or vanilla |
| TypeScript support     | ✅           | 🟡           | ✅           |       |
| Learning curve         | Medium      | Low         | Low         |       |
| Team familiarity       | 3/8 devs    | 6/8 devs    | 5/8 devs    | Local context matters most |

---

## Reversibility classification

Not all decisions carry equal weight. Classify early to calibrate effort.

### Type 1 decisions — Irreversible (one-way doors)

High stakes. Difficult or impossible to undo once executed.

| Characteristic | Detail |
|---------------|--------|
| Reversal cost | Extremely high (months of rework, data migration, contract penalties) |
| Examples      | Choosing a primary database, signing a 3-year vendor contract, public API schema, programming language for core platform |
| Process       | Full decision matrix, ADR, stakeholder review, explicit sign-off |
| Timeline      | Take the time needed. A week of analysis can save months of regret. |
| Ownership     | Senior leadership or architecture council |

### Type 2 decisions — Reversible (two-way doors)

Lower stakes. Can be reversed or iterated on with manageable cost.

| Characteristic | Detail |
|---------------|--------|
| Reversal cost | Low to moderate (a few days of refactoring, config change, feature flag) |
| Examples      | Choosing a logging library, UI component framework, internal API naming convention, test runner |
| Process       | Lightweight: pros/cons list, brief discussion, timebox to 30 minutes |
| Timeline      | Decide fast. Bias toward action. The cost of delay exceeds the cost of being wrong. |
| Ownership     | Individual contributor or team lead |

### How approach differs

```
Type 1 (irreversible)          Type 2 (reversible)
─────────────────────          ─────────────────────
Slow, deliberate               Fast, bias to action
Full decision matrix + ADR     Pros/cons or gut + brief note
Seek dissent actively          Seek rough consensus
Document extensively           Document lightly
Review with stakeholders       Decide within the team
Plan rollback before commit    Iterate after shipping
```

**Rule of thumb:** If you can reverse the decision in less than a sprint with no customer impact, treat it as Type 2.

---

## Option generation techniques

Good decisions require good options. If your option set is "do X or don't do X," you haven't explored enough.

### Zwicky morphological box

Decompose the problem into independent dimensions, list values for each, then combine across rows to discover non-obvious options.

**Example:** Designing a notification system

| Dimension       | Value A       | Value B        | Value C        |
|-----------------|---------------|----------------|----------------|
| Delivery channel | Email        | Push notification | In-app toast  |
| Trigger timing  | Real-time     | Batched (hourly) | User-polled   |
| Personalization | None          | Segment-based  | ML per-user    |
| Storage         | Fire-and-forget | 30-day log   | Permanent audit |

Combine one value per row to generate candidate designs:
- **Option 1:** Push + Real-time + Segment + 30-day → fast, moderate complexity
- **Option 2:** Email + Batched + None + Fire-and-forget → simplest MVP
- **Option 3:** In-app + Real-time + ML + Permanent → richest UX, highest cost

This produces options you would never reach by brainstorming alone.

### Constraint relaxation

Ask "What would we do if constraint X didn't exist?" Then see which ideas survive partial relaxation.

| Constraint to relax | Question | Insight |
|---------------------|----------|---------|
| Budget              | "If money were unlimited, what would we build?" | Reveals the ideal architecture to approximate |
| Timeline            | "If we had 6 months instead of 6 weeks?" | Separates essential from nice-to-have scope |
| Team size           | "If we had 3 more senior engineers?" | Highlights skill bottlenecks, not just capacity |
| Tech debt           | "If the codebase were greenfield?" | Distinguishes accidental from essential complexity |
| Compatibility       | "If we didn't need backward compatibility?" | Reveals how much legacy constrains design |

### Analogy mining

Borrow solutions from adjacent domains:
- "How does Stripe handle this?" (payments → your billing logic)
- "How does Git solve this?" (version control → your config management)
- "How do games handle this?" (game loops → your real-time sync)

Process: (1) Identify the abstract problem. (2) Find a domain that solved it well. (3) Map their solution back to your constraints.

---

## Decision anti-patterns

Watch for these — they silently degrade decision quality.

| Anti-pattern | Description | Signal | Remedy |
|-------------|-------------|--------|--------|
| **Analysis paralysis** | Over-researching to avoid committing. The 12th comparison spreadsheet gets created. | Decision has been "almost done" for 2+ weeks. No new information is changing scores. | Timebox the decision. Set a deadline. Use the "good enough" threshold — if top 2 options are within 10%, flip a coin. |
| **HiPPO** (Highest Paid Person's Opinion) | The most senior person's preference overrides structured evaluation. | Matrix scores point to Option A, but the team builds Option B because "the VP prefers it." | Require written criteria and weights *before* revealing preferences. Run blind scoring. |
| **Sunk cost fallacy** | Continuing with a failing option because of past investment. | "We've already spent 3 months on this approach" is used as justification to continue. | Ask: "If we were starting fresh today with zero investment, would we still choose this?" If no, switch. |
| **Anchoring bias** | The first option presented dominates the evaluation; subsequent options are judged relative to it. | Option 1 gets disproportionate discussion. Late-added options are dismissed quickly. | Randomize presentation order. Evaluate each option against criteria independently before comparing. |
| **Confirmation bias** | Seeking only evidence that supports a preferred option. | Research phase only covers articles praising the favored tool; failure cases are ignored. | Assign a "red team" member to argue against the leading option. Require at least 2 negative references per option. |
| **Groupthink** | Team converges on consensus too quickly to avoid conflict. | No dissent in the discussion. Everyone "agrees" in the meeting, then complains privately. | Use silent individual scoring before group discussion. Explicitly ask: "What could go wrong?" |
| **Recency bias** | Choosing what's newest or trending over proven solutions. | "Everyone on Twitter is using X" replaces evaluation. | Add maturity, production track record, and long-term maintenance as explicit criteria in the matrix. |

---

## Use-case bundles

- Vendor/tool selection → Decision matrix + Technology comparison + ADR
- Value conflict (speed vs robustness) → Hard choice model + Six Thinking Hats + Pros/Cons
- High uncertainty domain → Cynefin + safe-to-learn experiments
- Irreversible infrastructure choice → Type 1 process + Full decision matrix + ADR + Sensitivity check
- Quick library pick → Type 2 process + Pros/Cons + Timebox 30 min
- Expanding a narrow option set → Zwicky box + Constraint relaxation + Analogy mining

## Output template
- Decision statement (one sentence: "We will use X for Y because Z")
- Reversibility classification (Type 1 or Type 2)
- Options considered (minimum 3, including "do nothing" or "minimal" option)
- Criteria and weights (must sum to 100%)
- Trade-off matrix (scored and weighted)
- Selected option and rationale (link back to highest weighted score)
- Consequences: positive, negative, and risks
- Fallback option and trigger ("If X happens, we switch to Y")
- Review date (when to revisit the decision)
- ADR reference (link to the full ADR in the repo)


## Common traps

### Only one "real" option generated
**What happens:** Agent generates 3 options but two are obviously terrible (do nothing, rewrite everything). The decision matrix is theater.
**Why it happens:** Generating genuinely viable alternatives requires creative effort. Padding with strawmen is easier.
**Prevention:** Each option must be one that a reasonable person could defend. If you cannot write a 2-sentence argument for why someone might choose it, it is not a real option. Replace it.

### Decision matrix scores are invented
**What happens:** Agent fills the matrix with scores like 7/10, 8/10, 6/10 without explaining the basis. The scores feel precise but are arbitrary.
**Why it happens:** The template has cells that demand numbers. Without evidence, agents fill them with guesses.
**Prevention:** Every score must have a 1-line justification. "Performance: 8/10 because benchmark shows 200ms p99 vs. 500ms target" is valid. "Performance: 8/10" alone is not. If you cannot justify a score, use "?" and flag it as an unknown.

### Type 1 / Type 2 reversibility not checked
**What happens:** Agent treats a reversible technology choice like a permanent architecture commitment, producing 3 pages of analysis for a decision that could be reversed in a sprint.
**Why it happens:** The skill mentions reversibility but does not force a check early enough.
**Prevention:** Before building options, classify the decision: Type 1 (hard to reverse, high blast radius) or Type 2 (easy to reverse, low blast radius). Type 2 decisions get a bias-to-action treatment: recommend the simplest option and a 2-week review.

### Multiple methods stacked for perceived rigor
**What happens:** Agent uses a decision matrix, THEN a pros/cons list, THEN a SWOT analysis for the same decision. Each framework adds length but not clarity.
**Why it happens:** Agents equate "more frameworks = more thorough." The skill says "use one primary method" but does not penalize stacking.
**Prevention:** After completing the primary method, ask: "Did this answer the question?" If yes, stop. A companion method is justified ONLY when the primary method left a specific question unanswered. Name that question before adding the companion.

### Pros/cons list missing "Avoid" criteria
**What happens:** All options look good because the comparison only lists positive attributes. The recommendation is based on which option has more pros, ignoring dealbreakers.
**Why it happens:** Pros/cons framing is inherently optimistic. Agents list benefits first and risks as afterthoughts.
**Prevention:** Add an "Avoid" column to every comparison: "What would make us reject this option regardless of its benefits?" Screen options against the Avoid list before scoring.
