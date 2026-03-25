# PRD Quality Checklist

Run this checklist during Phase 4 (Validation) before presenting the PRD to the user. Every item is binary (yes/no).

Pick the section that matches the chosen format:
- **Full PRD**: run `Universal checks` and `Full PRD only`
- **Lightweight PRD**: run `Universal checks` and `Lightweight PRD only`
- **Eval-first PRD**: run `Universal checks` and `Eval-first PRD only`
- **User stories only**: run `Universal checks` and `User stories only`

Do not force lighter formats to include sections they intentionally omit. If the lighter format no longer fits the discovered scope, upgrade the document instead of fudging the checklist.

## Universal checks

- [ ] Problem or user goal is stated concretely enough that a reviewer can tell what is being built and why
- [ ] Scope boundaries or non-goals are explicit
- [ ] No vague adjectives without thresholds where thresholds are required
- [ ] Acceptance criteria are atomic (one assertion per criterion)
- [ ] Acceptance criteria are binary (pass/fail, no interpretation needed)
- [ ] Acceptance criteria start with a verb ("Display", "Return", "Reject", "Validate")
- [ ] Written in structured Markdown with consistent heading hierarchy
- [ ] No file paths or code snippets (use module/component names instead)
- [ ] All unknowns are labeled `TBD` (not assumed or invented)
- [ ] Every remaining `TBD` has an owner, next step, or clearly named decision-maker
- [ ] Output can be decomposed into independently testable work
- [ ] Testing approach references existing codebase patterns, or explicitly notes that no prior art exists yet

## Full PRD only

### Completeness

- [ ] Problem Statement has Who, What, Why, and Evidence
- [ ] "Why Now?" section has a specific strategic trigger, not just "it would be nice"
- [ ] At least ONE primary success metric with baseline and target
- [ ] At least ONE guardrail metric (what must NOT get worse)
- [ ] At least 2 user personas with goals and pain points
- [ ] User stories cover happy paths, error states, and edge cases
- [ ] Every user story has at least 2 acceptance criteria
- [ ] Out of Scope section exists with rationale for each exclusion
- [ ] Risks section has at least 2 identified risks with mitigations
- [ ] All `TBD` items appear in the Open Questions section with owner and timeline

### Requirements quality

- [ ] No vague adjectives without numeric thresholds ("fast" -> "< 200ms")
- [ ] No subjective terms without operational definitions ("easy to use" -> "task completion in < 3 clicks")
- [ ] Every performance requirement has a number, percentile, and load context
- [ ] Every security requirement names a specific control (not "should be secure")
- [ ] Every accessibility requirement references a standard and level (e.g., WCAG 2.1 AA)
- [ ] Acceptance criteria are atomic (one assertion per criterion)
- [ ] Acceptance criteria are binary (pass/fail, no interpretation needed)
- [ ] Acceptance criteria start with a verb ("Validate that...", "Display...", "Return...")
- [ ] No acceptance criteria use "should" (use "must" for requirements)

### Structure and format

- [ ] Written in structured Markdown with consistent heading hierarchy
- [ ] Uses bullet lists and tables, not prose paragraphs, for requirements
- [ ] No file paths or code snippets (use module/component names instead)
- [ ] No implementation prescriptions in requirements sections (what, not how)
- [ ] Total requirement count is under 200 discrete items
- [ ] Each section is self-contained (can be read independently)
- [ ] All unknowns are labeled `TBD` (not assumed or invented)

### AI-agent readiness

- [ ] Requirements can be decomposed into 5-15 minute execution blocks
- [ ] Each requirement is independently testable
- [ ] Technical constraints specify exact versions, not ranges
- [ ] Data models are described with field names, types, and constraints
- [ ] Integration points name specific APIs, endpoints, or services
- [ ] Non-functional requirements have concrete thresholds an agent can verify
- [ ] Testing strategy references existing patterns in the codebase

### Stakeholder alignment

- [ ] Problem statement would be recognized by users experiencing the pain
- [ ] Success metrics are things the team can actually measure with existing tools
- [ ] Out of scope items have been validated (not just assumed out)
- [ ] Implementation decisions record the rationale, not just the choice
- [ ] Open questions have owners who can actually answer them

### Common misses

These items are frequently forgotten. Double-check:

- [ ] Empty states (what does the feature look like with zero data?)
- [ ] Permission denied states (what happens when a user lacks access?)
- [ ] Loading states (what does the user see while data loads?)
- [ ] Error messages (what specific messages does the user see on failure?)
- [ ] Undo/rollback (can the user reverse their action?)
- [ ] Bulk operations (what if the user selects 100 items?)
- [ ] Concurrency (what if two users edit the same thing?)
- [ ] Data migration (what happens to existing data?)
- [ ] Notification triggers (when should the user be alerted?)
- [ ] Audit trail (do we need to log who did what and when?)

## Lightweight PRD only

- [ ] Problem Statement names who is affected, what hurts today, and why this matters now
- [ ] User stories cover the main user flow plus the primary error or edge condition
- [ ] Technical Constraints section names the relevant stack or integrations and any required numeric thresholds
- [ ] Out of Scope section makes the boundary explicit
- [ ] Success Metric section includes one primary metric with baseline and target
- [ ] Hidden complexity discovered during drafting triggered an upgrade to a fuller format instead of overloading the lightweight template

## Eval-first PRD only

- [ ] Problem Statement describes the user outcome and includes evidence or a concrete trigger
- [ ] Evaluation Criteria define the primary metric, pass/fail thresholds, and any guardrails
- [ ] Sample Input/Output section is concrete enough to judge correctness without guessing
- [ ] Boundaries clearly distinguish MUST, SHOULD, and MUST NOT behavior
- [ ] Human Escalation Rules state when the system must defer to a human
- [ ] Additional implementation notes were only added when they clarified scope rather than bloating the eval-first core

## User stories only

- [ ] Context line states the already-understood problem or goal in 1-2 sentences
- [ ] Stories are numbered and each story has attached acceptance criteria
- [ ] Out of Scope section exists with clear exclusions
- [ ] Open questions are carried explicitly if any remain
- [ ] The scope is still small and well-understood enough that a fuller PRD is unnecessary
