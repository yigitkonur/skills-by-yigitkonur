# PRD Anti-Patterns

Common mistakes that produce PRDs agents cannot execute on. Each pattern includes the symptom, consequence, and fix.

## 1. The Solution-First PRD

**Symptom:** PRD starts with "We need to build X using Y framework" without explaining the problem.
**Consequence:** Team builds the wrong thing confidently. No way to validate whether the solution addresses the actual pain.
**Fix:** Rewrite Problem Statement first. The solution should be derived from the problem, not the other way around. Ask: "If we built nothing, what specific harm would users experience?"

## 2. The Vague Requirements Doc

**Symptom:** Requirements use "fast", "intuitive", "user-friendly", "modern", "scalable" without numbers.
**Consequence:** AI agent interprets vague terms differently each time. No way to verify the requirement is met. Team argues about whether "fast enough" was achieved.
**Fix:** Attach a numeric threshold to every quality claim. "Fast" becomes "< 200ms at 95th percentile." "Scalable" becomes "supports 10K concurrent users with < 5% degradation."

Use this calibration:

```diff
# Vague (cannot verify)
- The search should be fast and return relevant results.
- The UI must look modern and be easy to use.
- The system should handle errors gracefully.

# Concrete (verifiable)
+ Search returns results within 200ms for datasets up to 10K records.
+ Search achieves >= 85% Precision@10 on the benchmark eval set.
+ UI follows the design system; scores 100% on Lighthouse Accessibility.
+ All API errors return JSON: { code, message, retryable, suggestedAction }.
```

## 3. The Monolithic Novel

**Symptom:** PRD is 40+ pages of prose. Sections blend into each other. No bullet lists or tables.
**Consequence:** Nobody reads it. AI agent exhausts context window. Key requirements are buried in paragraphs.
**Fix:** Keep under 200 discrete requirements. Use bullet lists and tables, not prose. Phase into execution blocks of 5-15 minutes each. If the PRD cannot be summarized in a 1-paragraph executive summary, the scope is too large.

## 4. The Architecture Prescription

**Symptom:** PRD dictates implementation details: specific functions, file structure, class hierarchy, database table designs.
**Consequence:** Constrains the engineering team (or AI agent) from finding better solutions. File paths become outdated within days. Creates false sense of completeness.
**Fix:** PRDs define WHAT and WHY. Technical design docs define HOW. In the PRD, describe modules by responsibility and interface, not by file path. "A module that handles user authentication and returns session tokens" is better than "Create `src/auth/SessionManager.ts` with a `createSession()` method."

## 5. The No-Evidence PRD

**Symptom:** Problem statement has no data, no customer quotes, no metrics. Just assertions: "Users struggle with X."
**Consequence:** No way to validate the problem exists. No baseline for success metrics. Stakeholders question priority.
**Fix:** Include at least one of: customer quote, support ticket count, analytics data point, competitive evidence. Format: "42% of support tickets in Q4 relate to search failures (source: Zendesk dashboard)."

## 6. The Missing Guardrails

**Symptom:** PRD defines success metrics but not guardrail metrics. Optimizes one dimension without protecting others.
**Consequence:** Feature succeeds on paper but breaks adjacent functionality. Conversion improves but page load time doubles. User satisfaction rises but error rate spikes.
**Fix:** For every primary success metric, identify 1-2 things that must NOT get worse. These become guardrail metrics: "Page load time must stay below 2s" alongside "Search conversion rate increases from 15% to 25%."

## 7. The PRD Written in Isolation

**Symptom:** Product manager writes the entire PRD without talking to engineers, designers, or users.
**Consequence:** Requirements conflict with system architecture. Effort estimates are wildly off. Users do not want what was specified.
**Fix:** PRD is a collaborative artifact. Phase 1 (Discovery) requires interviewing stakeholders. Phase 4 (Validation) requires engineering review. At minimum: 3 clarifying questions before drafting, 1 review cycle after.

## 8. The Immortal PRD

**Symptom:** PRD written once and never updated as understanding evolves.
**Consequence:** Implementation diverges from spec. Open questions never get resolved. TBDs remain forever.
**Fix:** Version-control the PRD alongside the code. Update it when decisions are made. Close Open Questions as they are resolved. The PRD is a living document — but "living" requires active maintenance, not just saying "it is living."

## 9. The Scope Creep Invitation

**Symptom:** No "Out of Scope" section. Or the Out of Scope section has no rationale.
**Consequence:** Every stakeholder adds their pet feature. Scope grows until the project is unshippable. AI agent builds features that were never intended.
**Fix:** Always include Out of Scope with explicit rationale for each exclusion. "Push notifications — deferred to v2 because the notification infrastructure is not yet available" is better than just "Push notifications — out of scope."

## 10. The Kitchen Sink PRD

**Symptom:** PRD tries to specify everything: UI copy, pixel dimensions, animation timing, database indices, caching strategy, deployment runbook.
**Consequence:** PRD becomes 100+ pages. Most content is better handled by specialized documents (design specs, tech design docs, runbooks). AI agent drowns in irrelevant detail.
**Fix:** The PRD defines the WHAT and WHY. Specialized documents handle: visual design (Figma/design spec), technical design (architecture doc), operations (runbook), content (copy doc). Reference these documents from the PRD; do not duplicate their content.
