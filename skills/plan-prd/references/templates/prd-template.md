# PRD Template

Complete 10-section template with guidance for each section. Copy this structure when drafting a PRD.

## Output format

Write the PRD in Markdown. Output to one of:
- GitHub Issue: `gh issue create --title "PRD: {feature-name}" --body "..."`
- File: `docs/prd/{feature-name}.md` (or the project's existing convention)

## Template

```markdown
# PRD: {Feature Name}

**Author:** {name}
**Date:** {date}
**Status:** Draft | In Review | Approved
**Last Updated:** {date}

---

## 1. Problem Statement

**Who:** {Which users or personas experience this problem}
**What:** {The specific pain point or unmet need — 2-3 sentences}
**Why:** {Why this matters to the business — revenue, retention, efficiency, compliance}
**Evidence:**
- {Customer quote, interview insight, or support ticket data}
- {Analytics data point with specific numbers}
- {Competitive signal or market trend}

## 2. Why Now?

{1-2 paragraphs explaining why this must be built now, not later. Include:}
- Strategic trigger (OKR, competitive threat, regulatory deadline, customer escalation)
- Cost of delay (quantified if possible)
- What has changed to make this urgent or feasible

## 3. Success Metrics

**Primary metric (ONE):**
- {Metric name}: {current baseline} -> {target} within {timeframe}

**Secondary metrics:**
- {Metric}: {baseline} -> {target}
- {Metric}: {baseline} -> {target}

**Guardrail metrics (must NOT get worse):**
- {Metric}: must stay {above/below} {threshold}
- {Metric}: must stay {above/below} {threshold}

## 4. User Personas

### {Persona Name 1} (Primary)
- **Role:** {job title, experience level}
- **Goals:** {what they are trying to accomplish}
- **Pain points:** {current frustrations}
- **Behaviors:** {how they currently work, tools they use}
- **Jobs-to-be-done:** {the underlying job they hire this product for}

### {Persona Name 2} (Secondary)
- **Role:** ...
- **Goals:** ...
- **Pain points:** ...

## 5. User Stories & Acceptance Criteria

### Epic Hypothesis
We believe that {action} for {users} will {outcome} because {rationale}. We will measure success by {metric} within {timeframe}.

### Stories

1. As a {persona}, I want to {action} so that {benefit}.
   - [ ] {Atomic, measurable acceptance criterion — verb-first}
   - [ ] {Criterion covering the happy path}
   - [ ] {Criterion covering the primary error state}
   - [ ] {Criterion with numeric threshold if applicable}

2. As a {persona}, I want to {action} so that {benefit}.
   - [ ] ...

3. As a {persona}, I want to {action} so that {benefit}.
   - [ ] ...

{Continue numbering. Aim for 10-30 stories for a full feature. Cover:}
- Happy paths (primary user flows)
- Error states (what happens when things go wrong)
- Edge cases (boundary conditions, empty states, overflow)
- Permissions (who can and cannot do what)
- Notifications (what triggers alerts or messages)

## 6. Solution Overview & Implementation Decisions

### High-level approach
{1-2 paragraphs describing the solution at a conceptual level. Focus on the user experience and system behavior, NOT implementation details.}

### Key decisions made
| Decision | Choice | Rationale |
|---|---|---|
| {Decision area} | {What we chose} | {Why} |
| {Decision area} | {What we chose} | {Why} |

### Module sketch
{List the major modules that will be built or modified. Describe their responsibilities and interfaces. Do NOT include file paths or code snippets — they become outdated.}

- **{Module A}**: {responsibility} — interface: {inputs/outputs}
- **{Module B}**: {responsibility} — interface: {inputs/outputs}
- **{Module C}**: {responsibility} — interface: {inputs/outputs}

{Actively look for deep modules — ones that encapsulate significant functionality behind a simple, testable interface that rarely changes.}

## 7. Technical Constraints & Non-Functional Requirements

### Tech stack constraints
- {Framework/language/version requirements}
- {Infrastructure constraints}
- {Integration requirements}

### Performance
- {API response time: < Xms at Yth percentile under Z concurrent users}
- {Page load time: < Xs for Yth percentile}
- {Throughput: X requests/second}

### Security
- {Authentication/authorization requirements}
- {Data encryption requirements}
- {Compliance standards (GDPR, SOC2, HIPAA, etc.)}

### Accessibility
- {WCAG compliance level}
- {Specific accessibility targets}

### AI-specific requirements (if applicable)
- {Accuracy/precision threshold}
- {Hallucination rate limit}
- {Latency under load}
- {Evaluation strategy}

## 8. Testing Strategy

### What makes a good test for this feature
{Define testing philosophy — e.g., "Test external behavior, not implementation details. Focus on user-observable outcomes."}

### Modules to test
- {Module A}: {what to test, at what level (unit/integration/e2e)}
- {Module B}: {what to test}

### Prior art
{Reference existing test patterns in the codebase that should be followed for consistency.}

## 9. Out of Scope & Non-Goals

### Out of scope for this version
- {Feature/capability we are NOT building} — Reason: {why}
- {Feature/capability we are NOT building} — Reason: {why}

### Explicit non-goals
- {Behavior we are intentionally NOT optimizing for}
- {User segment we are intentionally NOT targeting}

### Deferred to future versions
- {Feature planned for v2}
- {Enhancement planned for later iteration}

## 10. Risks, Dependencies & Open Questions

### Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| {Risk description} | High/Medium/Low | High/Medium/Low | {Mitigation plan} |

### Dependencies
- {External team/service dependency} — Status: {confirmed/pending}
- {Infrastructure dependency} — Status: {confirmed/pending}

### Open questions (TBD)
- [ ] {Question} — Owner: {who} — Due: {when}
- [ ] {Question} — Owner: {who} — Due: {when}
```

## Section-by-section guidance

### Problem Statement
Lead with evidence, not opinions. Include at least one data point (customer quote, metric, support ticket count). The "Who" should reference a named persona from Section 4.

### Why Now?
This section is frequently skipped but critical. If you cannot articulate why now, the feature may not deserve priority. Valid reasons: competitive threat with timeline, regulatory deadline, customer escalation with churn risk, strategic OKR alignment with quarterly deadline.

### Success Metrics
The primary metric should be ONE number the team obsesses over. Guardrail metrics are what must NOT get worse — they prevent optimizing one metric at the expense of others (e.g., improving conversion rate but breaking page load time).

### User Stories
Write an EXTENSIVE list. Coverage matters more than brevity. Use the format: "As a {persona}, I want to {action} so that {benefit}." Each story gets its own acceptance criteria — atomic, measurable, binary (pass/fail), verb-first.

### Solution Overview
This is about WHAT the system does, not HOW it is built. Do not include file paths, code snippets, or implementation algorithms. Those belong in a technical design doc. Focus on modules, interfaces, and decisions.

### Testing Strategy
Reference prior art from the codebase. "Only test external behavior, not implementation details" is the default philosophy unless the team has a different standard.

### Out of Scope
Always include this section. It prevents scope creep and sets expectations. Give the reason for each exclusion — "out of scope" without rationale invites pushback.

### Open Questions
Every `TBD` in the PRD should appear here with an owner and timeline. A PRD with no open questions is either very mature or the author did not think hard enough.
