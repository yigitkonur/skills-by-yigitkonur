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

## Output template
- Architecture options
- Criteria and weights
- Trade-off summary
- Operating readiness
- Migration path and rollback guardrails
