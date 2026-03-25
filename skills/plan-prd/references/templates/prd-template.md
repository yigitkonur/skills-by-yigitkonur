# PRD Template

Full 10-section PRD template plus lightweight variants and per-section guidance. Copy the block that matches your chosen format.

## Output format

Write the PRD in Markdown. Output to one of:
- GitHub Issue: `gh issue create --title "PRD: {feature-name}" --body "..."`
- File: follow an explicit user instruction if one exists; otherwise use the target repo's existing PRD/spec convention; otherwise use `docs/prd/{feature-name}.md`
- Fallback when repo/GitHub writes are unavailable: `prd.md` in the current working context, with the intended final destination noted at the top

The current working context is the root of the shipping repo selected during discovery. If no shipping repo exists yet, use the directory where you are storing task artifacts for this request.

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

If the user is unavailable and `TBD`s remain, keep the document factual and append an `Open Questions` section or appendix instead of inventing answers.

## Additional format templates

### Lightweight PRD Template

Use this when `references/discovery/format-decision.md` routes you to the lightweight path.

```markdown
# PRD: {Feature Name}

**Author:** {name}
**Date:** {date}
**Status:** Draft | In Review | Approved

## 1. Problem Statement
- Who is affected:
- What hurts today:
- Why this matters now:

## 2. User Stories & Acceptance Criteria
1. As a {persona}, I want to {action} so that {benefit}.
   - [ ] {atomic, measurable acceptance criterion}
   - [ ] {primary error/edge case criterion}

## 3. Technical Constraints
- Tech stack / integration constraints:
- Performance / security / accessibility thresholds:

## 4. Out of Scope
- Explicitly not included in this version:

## 5. Success Metric
- Primary metric: {baseline} -> {target} within {timeframe}
```

If discovery surfaces hidden complexity, upgrade this document to the full 10-section template instead of stretching the lightweight version beyond recognition.

If any `TBD`s remain in this non-full format, append `## 6. Open Questions` with owner or next step rather than guessing.

### Eval-first PRD Template

Use this when `references/discovery/format-decision.md` routes you to the eval-first path.

```markdown
# PRD: {Feature Name}

**Author:** {name}
**Date:** {date}
**Status:** Draft | In Review | Approved

## 1. Problem Statement
- Who is affected:
- What behavior or outcome needs to improve:
- Why this matters now:
- Evidence:

## 2. Evaluation Criteria
- Primary metric: {baseline} -> {target} within {timeframe}
- Guardrails: {what must not get worse}
- Pass/fail thresholds:
- Review cadence / evaluator:

## 3. Sample Input / Output Pairs
| Scenario | Input | Expected Output | Notes |
|---|---|---|---|
| {name} | {prompt / event} | {expected behavior} | {edge condition if any} |

## 4. Boundaries
- MUST:
- SHOULD:
- MUST NOT:

## 5. Human Escalation Rules
- Escalate when:
- Human approval required for:
- Logging / review expectations:
```

If dependencies, rollout constraints, or open questions matter, append short sections after Section 5 instead of forcing the full 10-section template.

If any `TBD`s remain in this non-full format, append `## 6. Open Questions` with owner or next step rather than guessing.

### User Stories Only Template

Use this when `references/discovery/format-decision.md` routes you to the stories-only path.

```markdown
# Feature Stories: {Feature Name}

**Context:** {1-2 sentences on the already-understood problem or goal}

## 1. User Stories & Acceptance Criteria
1. As a {persona}, I want to {action} so that {benefit}.
   - [ ] {atomic, measurable acceptance criterion}
   - [ ] {primary error or edge case criterion}

## 2. Out of Scope
- Explicitly not included in this version:
```

If any `TBD`s remain in this non-full format, append `## 3. Open Questions` with owner or next step rather than guessing.

## Full PRD section-by-section guidance

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
