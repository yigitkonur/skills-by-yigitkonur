# Technical Strategy and Architecture Decisions

## Read this if
- You are choosing architecture for a new system or major feature.
- You are considering structural changes in an existing system.
- You are unsure whether complexity is justified.

## Planning vision for this stage
Think in capability, constraints, and operating reality. Prefer fit over trend.

## Junior rule
If unsure, start with the simplest architecture that satisfies current constraints and preserves upgrade paths.

## Explore-before-decide protocol

1. Map current components and boundaries.
2. Trace one real workflow end-to-end.
3. Identify bottlenecks, coupling, and failure points.
4. Separate hard constraints from preferences.
5. Record what must stay stable during change.

## Method steering

### First principles
- Use when architecture debates rely on buzzwords.
- Thinking posture: “What capabilities are truly required?”

### Issue trees
- Use when architecture concerns are tangled.
- Thinking posture: “Separate domain, data, integration, and operations branches.”

### Decision matrix
- Use when comparing architecture candidates.
- Thinking posture: “Score against weighted non-functional requirements.”

### Cynefin framework
- Use when domain behavior is uncertain.
- Thinking posture: “Experiment in complex contexts; standardize in clear contexts.”

### Second-order thinking
- Use when long-term maintenance cost matters.
- Thinking posture: “Include onboarding, migration, and operations burden.”

### Confidence determines speed vs. quality
- Use when planning architecture rollout cadence.
- Thinking posture: “Low confidence -> phased validation; high confidence -> tighten quality.”

## “Do I need event-driven architecture?” quick guide

Use event-driven when most are true:
- several independent consumers need same business signal
- asynchronous behavior is acceptable
- loose coupling and scalability are priority
- operational capability exists for reliability and observability

Prefer simpler synchronous/modular flow when:
- immediate consistency is required
- team operating maturity is limited
- coordination cost of distributed flows outweighs benefits

---

## Architecture Decision Records (ADRs)

Record every significant architecture decision. Small decisions compound; undocumented ones create invisible constraints.

### ADR template

```
# ADR-NNNN: [Short Title]

## Status
Proposed | Accepted | Deprecated | Superseded by ADR-XXXX

## Context
What forces are at play? What constraints exist?
Include business drivers, technical constraints, team capabilities, and timeline pressure.

## Decision
What is the change we are making?
State the decision in active voice: "We will use X for Y."

## Alternatives Considered
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Option A | ... | ... | ... |
| Option B | ... | ... | ... |

## Consequences
What becomes easier? What becomes harder?
List both positive and negative consequences explicitly.

## Review Date
When should this decision be revisited? (e.g., 6 months, after v2 launch)
```

### Worked example

```
# ADR-0012: Use PostgreSQL over DynamoDB for order service

## Status
Accepted

## Context
The order service requires complex queries across order items, customer history,
and inventory joins. The team has deep SQL expertise. Read-to-write ratio is 3:1.
Peak load is 500 requests/second. Data fits comfortably in a single region.

## Decision
We will use PostgreSQL (via RDS) as the primary datastore for the order service.

## Alternatives Considered
| Option       | Pros                              | Cons                                    | Why Rejected                          |
|--------------|-----------------------------------|-----------------------------------------|---------------------------------------|
| DynamoDB     | Managed, auto-scaling, low-ops   | Complex queries need denormalization     | Query patterns require joins          |
| MongoDB      | Flexible schema, JSON native     | Weaker ACID, team unfamiliar            | Consistency requirements too strict   |
| CockroachDB  | Distributed SQL, horizontal scale | Higher cost, operational complexity     | Current scale doesn't justify cost    |

## Consequences
- Easier: complex reporting queries, familiar tooling, strong consistency
- Harder: horizontal scaling beyond single-node limits, multi-region replication
- Action required: set up read replicas before exceeding 2,000 req/s

## Review Date
Revisit if throughput exceeds 2,000 req/s sustained or multi-region is required.
```

### ADR hygiene rules

| Rule | Rationale |
|------|-----------|
| Number sequentially, never reuse numbers | Provides stable references across docs and conversations |
| Keep ADRs immutable once accepted | Supersede with a new ADR rather than editing; preserves decision history |
| Store ADRs in the repo alongside code | Decisions travel with the codebase; discoverable via search |
| Link ADRs to implementation PRs | Creates traceability from decision to execution |
| Set a review date on every ADR | Prevents stale decisions from silently constraining future work |

---

## Architecture Fitness Functions

Fitness functions are automated checks that continuously verify architecture characteristics. They turn “ilities” from aspirations into measurable constraints.

### Fitness function template

| Characteristic | Metric | Target | Measurement Method | Frequency | Alert Threshold |
|----------------|--------|--------|--------------------|-----------|-----------------|
| Performance | p99 latency | < 200ms | APM / load test | Every deploy + daily | > 250ms |
| Performance | Throughput | > 1,000 req/s | Load test | Weekly | < 800 req/s |
| Coupling | Circular dependencies | 0 | Static analysis (e.g., madge, deptree) | Every CI build | > 0 |
| Coupling | Afferent coupling per module | < 10 | Static analysis | Weekly | > 15 |
| Security | Secrets in source | 0 | Secret scanner (e.g., gitleaks, trufflehog) | Every commit | > 0 |
| Security | Known vulnerabilities | 0 critical | Dependency scanner (e.g., Snyk, npm audit) | Daily | > 0 critical |
| Reliability | Error rate | < 0.1% | Monitoring / logs | Continuous | > 0.5% |
| Reliability | Mean time to recovery | < 15 min | Incident tracking | Per incident | > 30 min |
| Observability | Trace coverage | > 95% of endpoints | APM | Weekly | < 90% |
| Cost | Infra spend per 1K requests | < $0.05 | Cloud billing API | Monthly | > $0.08 |

### How to implement fitness functions

1. **Embed in CI**: coupling checks, secret scanning, and dependency audits run on every pull request.
2. **Embed in CD**: performance benchmarks gate deployment; fail the pipeline if p99 exceeds threshold.
3. **Embed in monitoring**: reliability and cost metrics trigger alerts; dashboards show trend over time.
4. **Review quarterly**: recalibrate targets as scale, architecture, or business context changes.

---

## Technical Debt Quadrant

Martin Fowler’s model classifies technical debt along two axes: **deliberate vs. inadvertent** and **reckless vs. prudent**. Use this to communicate debt decisions with stakeholders.

|            | Deliberate | Inadvertent |
|------------|-----------|-------------|
| **Reckless** | “We don’t have time for design” | “What’s layering?” |
| **Prudent** | “Ship now, refactor later” | “Now we know how we should have done it” |

### When each quadrant is acceptable

| Quadrant | Acceptable When | Action Required |
|----------|----------------|-----------------|
| Reckless + Deliberate | Almost never. Only justified in throwaway prototypes or time-boxed experiments with a hard kill date. | Tag with expiry date. Delete or rewrite by that date — no exceptions. |
| Reckless + Inadvertent | Never acceptable — this is a skill gap, not a trade-off. | Invest in training, code review, and pairing. Retrofit tests before extending. |
| Prudent + Deliberate | Common and valid. Shipping a known shortcut when trade-offs are understood and a payback plan exists. | Create a ticket immediately. Schedule repayment within 1–2 sprints. Track in debt register. |
| Prudent + Inadvertent | Inevitable — you learn better approaches as the system evolves. | Capture the insight in an ADR. Refactor incrementally when you next touch the affected area. |

### Technical debt register template

| ID | Description | Quadrant | Impact (H/M/L) | Effort to Fix (H/M/L) | Owner | Created | Target Fix Date | Status |
|----|-------------|----------|-----------------|------------------------|-------|---------|-----------------|--------|
| TD-001 | Monolithic auth module | Prudent-Deliberate | H | M | @alice | 2024-01-15 | 2024-Q2 | Open |
| TD-002 | Missing input validation on /api/upload | Reckless-Inadvertent | H | L | @bob | 2024-02-01 | ASAP | In Progress |

---

## Build vs. Buy vs. Open Source Decision Framework

Use this matrix when deciding whether to build a capability in-house, purchase a commercial solution, or adopt an open-source project.

### Decision criteria

| Criterion | Build | Buy (SaaS/Commercial) | Open Source |
|-----------|-------|------------------------|-------------|
| **Core differentiator?** | Yes — build what makes you unique | No — buy commodities | Maybe — if you can customize |
| **Time to value** | Slowest (weeks–months) | Fastest (days–weeks) | Medium (days–weeks + integration) |
| **Total cost of ownership** | Dev salaries + maintenance | License + integration + lock-in | Free license + maintenance + expertise |
| **Customizability** | Full control | Limited to vendor API/config | Full control (if you invest) |
| **Maintenance burden** | You own it all | Vendor handles infra | Community + you handle patches |
| **Vendor/community risk** | None | Vendor lock-in, price changes, sunset | Project abandonment, fork fragmentation |
| **Compliance/security** | Full auditability | Depends on vendor SOC2/ISO posture | You audit; depends on project maturity |
| **Team expertise required** | Deep domain knowledge | Integration skills | Domain + open-source contribution skills |

### Decision flow

1. **Is this a core differentiator?** If yes → lean toward Build.
2. **Does a mature commercial solution exist?** If yes and it’s not a differentiator → lean toward Buy.
3. **Does a healthy open-source project exist?** Evaluate community size, commit frequency, license, and bus factor.
4. **What is the switching cost?** If high → favor options that preserve portability (open standards, abstraction layers).
5. **What is the team’s capacity?** If stretched → avoid Build unless it’s truly core.

---

## Migration Strategy Patterns

Choose a migration pattern based on risk tolerance, system complexity, and team capacity.

| Pattern | How It Works | When to Use | When to Avoid | Risk Level |
|---------|-------------|-------------|---------------|------------|
| **Strangler Fig** | Incrementally replace old system components by routing traffic to new implementations one endpoint/feature at a time. Old system shrinks until it can be removed. | Legacy modernization; system is decomposable into independent routes or features; team needs to deliver value continuously during migration. | System is tightly coupled with no clear seams; migration must complete by a hard deadline shorter than incremental timeline. | Low |
| **Parallel Run** | Run old and new systems simultaneously on the same inputs. Compare outputs to verify correctness before switching. | Financial systems, data pipelines, or anywhere correctness must be proven before cutover; regulatory environments. | Systems with side effects (e.g., sending emails, charging cards) that cannot be safely duplicated. | Low–Medium |
| **Big Bang** | Replace the entire old system with the new system in a single cutover event. | Small systems with low complexity; hard external deadlines; system is well-understood and fully tested. | Large or complex systems; insufficient test coverage; team lacks experience with coordinated cutovers. | High |
| **Feature Flags** | Deploy new implementation behind a flag. Gradually roll out to increasing percentages of users. Instant rollback by disabling the flag. | User-facing changes where gradual rollout reduces blast radius; A/B testing; canary deployments. | Infrastructure-level changes that cannot be toggled per-request; changes requiring schema migrations that are not backward-compatible. | Low |
| **Branch by Abstraction** | Introduce an abstraction layer over the component being replaced. Swap the implementation behind the abstraction. Remove the abstraction once migration is complete. | Internal library or module replacement; database migration behind a repository pattern; need to keep trunk green during migration. | Abstraction layer would add unacceptable latency or complexity; component has no clear interface boundary. | Low–Medium |

### Migration checklist

- [ ] Rollback plan documented and tested
- [ ] Data migration strategy validated (backward-compatible schema changes preferred)
- [ ] Monitoring and alerting configured for both old and new paths
- [ ] Success criteria defined (latency, error rate, data consistency)
- [ ] Communication plan for stakeholders and downstream consumers
- [ ] Feature flags or traffic splitting infrastructure in place
- [ ] Runbook for incident response during migration window

---

## Architecture Review Checklist

Use this checklist before approving any significant architecture proposal. Score each category as **Met / Partially Met / Not Met / N/A**.

### Non-functional requirements

| Category | Question | Evidence Required |
|----------|----------|-------------------|
| **Scalability** | Can the system handle 10x current load without re-architecture? | Load test results or capacity model |
| **Scalability** | Are stateless components separated from stateful ones? | Architecture diagram |
| **Scalability** | Is there a horizontal scaling path for compute-heavy components? | Deployment configuration |
| **Reliability** | What is the target availability (e.g., 99.9%)? Is it achievable with the proposed design? | SLA document + failure mode analysis |
| **Reliability** | Are there single points of failure? If so, what is the mitigation? | Architecture diagram + runbook |
| **Reliability** | Is there a graceful degradation strategy? | Design doc describing fallback behavior |
| **Security** | Is authentication and authorization handled at every entry point? | Security review or threat model |
| **Security** | Is data encrypted at rest and in transit? | Infrastructure configuration |
| **Security** | Are secrets managed via a vault, not environment variables or code? | Secret management architecture |
| **Observability** | Are structured logs, metrics, and distributed traces in place? | Observability stack description |
| **Observability** | Can an on-call engineer diagnose a production issue within 15 minutes? | Runbook + dashboard screenshots |
| **Observability** | Are SLIs and SLOs defined for critical user journeys? | SLO document |
| **Maintainability** | Can a new team member make a meaningful contribution within 2 weeks? | Onboarding guide + code documentation |
| **Maintainability** | Is the dependency tree auditable and are upgrades automated? | Dependabot/Renovate configuration |
| **Maintainability** | Are module boundaries enforced (e.g., no circular imports)? | CI fitness function results |
| **Cost** | Is there a cost estimate for steady-state and peak load? | Cloud cost model or calculator output |
| **Cost** | Are there cost alerts and auto-scaling limits to prevent runaway spend? | Billing alert configuration |
| **Cost** | Has the team evaluated reserved/committed-use pricing? | Cost optimization review |

---

## Technology Radar

Use the technology radar to align the team on which technologies to invest in, experiment with, or phase out. Review and update quarterly.

### Radar categories

| Ring | Definition | Team Expectation |
|------|-----------|------------------|
| **Adopt** | Proven in production. Default choice for new projects. | Use without justification needed. |
| **Trial** | Worth pursuing. Use in non-critical projects to build experience. | Requires a short write-up of goals and evaluation criteria before adopting. |
| **Assess** | Worth exploring. Investigate with spikes or proof-of-concept work. | Time-boxed investigation only. Do not use in production. |
| **Hold** | Proceed with caution. Do not start new work with these. Migrate away when practical. | Existing usage is maintained but not extended. New usage requires ADR justification. |

### Example radar entries

| Category | Technology | Ring | Rationale |
|----------|-----------|------|-----------|
| Languages | TypeScript | Adopt | Team-wide expertise; strong type safety; broad ecosystem |
| Languages | Rust | Assess | Potential for performance-critical services; steep learning curve |
| Frameworks | Next.js (App Router) | Trial | Server components promising; stability still maturing |
| Frameworks | Express.js | Hold | Maintenance-only; prefer Fastify or Hono for new services |
| Datastores | PostgreSQL | Adopt | Battle-tested; covers 90% of our query patterns |
| Datastores | Redis | Adopt | Caching and session management standard |
| Datastores | CockroachDB | Assess | Evaluate for multi-region use cases |
| Infrastructure | Kubernetes | Adopt | Standard orchestration layer; team has deep ops experience |
| Infrastructure | Serverless (Lambda) | Trial | Good for event-driven workloads; cold start latency needs evaluation |
| Tools | Terraform | Adopt | Infrastructure-as-code standard |
| Tools | Pulumi | Assess | TypeScript IaC alternative; evaluate developer experience |
| Practices | Trunk-based development | Adopt | Reduces merge pain; pairs well with feature flags |
| Practices | Micro-frontends | Hold | Complexity outweighs benefits at current team size |

### Maintaining the radar

1. **Quarterly review**: the engineering team reviews all entries, proposes moves, and votes.
2. **New entry proposals**: any engineer can propose a new entry with a one-paragraph rationale.
3. **Ring changes require evidence**: moving from Assess → Trial requires a spike summary. Moving from Trial → Adopt requires production usage data.
4. **Hold entries require migration plan**: if a technology moves to Hold, document a timeline for phasing it out.

---

## Output template

When presenting architecture decisions, include these sections:

- Architecture options considered (with ADR reference if applicable)
- Criteria and weights (linked to fitness functions)
- Trade-off summary (what you gain and what you give up)
- Technical debt implications (quadrant classification)
- Build/Buy/Open Source rationale
- Operating readiness (monitoring, alerting, runbooks)
- Migration path and rollback guardrails
- Technology radar alignment
- Review date for revisiting the decision
