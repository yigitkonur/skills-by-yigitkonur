# PRD Quality Checklist

Run this checklist during Phase 4 (Validation) before presenting the PRD to the user. Every item is binary (yes/no).

## Completeness

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

## Requirements quality

- [ ] No vague adjectives without numeric thresholds ("fast" -> "< 200ms")
- [ ] No subjective terms without operational definitions ("easy to use" -> "task completion in < 3 clicks")
- [ ] Every performance requirement has a number, percentile, and load context
- [ ] Every security requirement names a specific control (not "should be secure")
- [ ] Every accessibility requirement references a standard and level (e.g., WCAG 2.1 AA)
- [ ] Acceptance criteria are atomic (one assertion per criterion)
- [ ] Acceptance criteria are binary (pass/fail, no interpretation needed)
- [ ] Acceptance criteria start with a verb ("Validate that...", "Display...", "Return...")
- [ ] No acceptance criteria use "should" (use "must" for requirements)

## Structure and format

- [ ] Written in structured Markdown with consistent heading hierarchy
- [ ] Uses bullet lists and tables, not prose paragraphs, for requirements
- [ ] No file paths or code snippets (use module/component names instead)
- [ ] No implementation prescriptions in requirements sections (what, not how)
- [ ] Total requirement count is under 200 discrete items
- [ ] Each section is self-contained (can be read independently)
- [ ] All unknowns are labeled `TBD` (not assumed or invented)

## AI-agent readiness

- [ ] Requirements can be decomposed into 5-15 minute execution blocks
- [ ] Each requirement is independently testable
- [ ] Technical constraints specify exact versions, not ranges
- [ ] Data models are described with field names, types, and constraints
- [ ] Integration points name specific APIs, endpoints, or services
- [ ] Non-functional requirements have concrete thresholds an agent can verify
- [ ] Testing strategy references existing patterns in the codebase

## Stakeholder alignment

- [ ] Problem statement would be recognized by users experiencing the pain
- [ ] Success metrics are things the team can actually measure with existing tools
- [ ] Out of scope items have been validated (not just assumed out)
- [ ] Implementation decisions record the rationale, not just the choice
- [ ] Open questions have owners who can actually answer them

## Common misses

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
