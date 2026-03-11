# Communication and Alignment

## Read this if
- Decisions are made but not understood.
- Stakeholder buy-in is weak.
- Feedback triggers defensiveness.
- Meetings end without clear owners or next steps.
- Written proposals get ignored or misinterpreted.
- You need to deliver bad news or push back on scope.
- Async updates are creating more confusion than clarity.

## Planning vision for this stage
Think in clarity, shared meaning, and trust. Every communication artifact should answer three questions: What do I need from you? Why does it matter? By when?

## Communication flow

1. Start with recommendation — state the answer first.
2. Group supporting reasons — cluster evidence into 2-4 themes.
3. Show evidence and risks — concrete data, not opinions.
4. End with clear asks and ownership — who does what by when.

**Anti-patterns to avoid:**
- Burying the ask at the end of a long narrative.
- Presenting data without interpretation or recommendation.
- Leaving meetings without written decisions and owners.
- Using "we should" without naming a specific person.

---

## Method steering

### Minto Pyramid
Best for concise executive communication.
- Thinking posture: "Lead with answer, support with structure."
- Structure: Answer → Key supporting arguments (2-4) → Evidence for each argument.
- When to use: Status updates to leadership, email summaries, written proposals.
- Example opening: "We should delay launch by two weeks. Here are the three reasons..."

### Situation-Behavior-Impact (SBI)
Best for precise, non-judgmental feedback.
- Thinking posture: "Describe observation and effect, not personality."
- Structure: "In [situation], when you [specific behavior], the impact was [concrete effect]."
- When to use: 1:1 feedback, performance conversations, peer reviews.
- Example: "In yesterday's design review (situation), when you interrupted the presenter three times (behavior), the team stopped sharing their concerns (impact)."

### Six Thinking Hats
Best for multi-perspective discussion hygiene.
- Thinking posture: "Separate thought modes so teams stop talking past each other."
- White hat: Facts and data only. Blue hat: Process and agenda. Green hat: Creative ideas. Yellow hat: Benefits and value. Black hat: Risks and concerns. Red hat: Gut feelings and emotions.
- When to use: Cross-functional decisions, heated debates, brainstorming sessions.
- Facilitation tip: Assign one hat at a time to the entire group. Spend 5 minutes per hat. Prevents the loudest critic from dominating.

### Conflict Resolution Diagram
Best for resolving apparently incompatible goals.
- Thinking posture: "Find shared objective behind conflicting positions."
- Structure: State each side's position → Identify the underlying need behind each position → Find the shared objective → Generate options that satisfy both needs.
- When to use: Cross-team disagreements, resource conflicts, architectural disputes.

### Ladder of inference
Best for preventing conclusion jumps in meetings.
- Thinking posture: "Ask what data each conclusion is built on."
- The ladder (bottom to top): Observable data → Selected data → Interpreted meaning → Assumptions → Conclusions → Beliefs → Actions.
- Intervention questions: "What did you actually observe?" / "What are we assuming here?" / "Is there another interpretation?"
- When to use: Post-incident reviews, disagreements about root cause, interpersonal conflicts.

---

## RACI matrix

Use RACI to eliminate ambiguity about who does what. Without it, either nobody owns a task or everybody thinks someone else does.

- **R = Responsible** — Does the work. Can be multiple people.
- **A = Accountable** — Final decision-maker. Exactly one per task. The buck stops here.
- **C = Consulted** — Provides input before the work is done. Two-way communication.
- **I = Informed** — Notified after the work is done. One-way communication.

### RACI rules
1. Every task has exactly one A. No exceptions. Two A's means zero A's.
2. Minimize C and I assignments — each one adds communication overhead.
3. R without A means no one can make the final call.
4. A without R means the accountable person has delegated all execution.
5. If a column is mostly C, that person is a bottleneck. Redesign.

### Example RACI matrix

| Task | Product Manager | Tech Lead | Designer | Engineering |
|---|---|---|---|---|
| Define requirements | A | C | C | I |
| Architecture design | I | A, R | I | C |
| UI/UX mockups | C | I | A, R | I |
| Implementation | I | A | I | R |
| Release sign-off | A | R | C | R |

### How to build a RACI
1. List all tasks/deliverables in the left column.
2. List all roles (not people) across the top.
3. Fill in R first — who does the work?
4. Fill in A next — who makes the final call? Exactly one per row.
5. Add C sparingly — only people whose input is truly needed before work proceeds.
6. Add I last — only people who need to know the outcome.
7. Review each column: if someone is C or I on everything, they may not need to be on the matrix at all.

---

## Stakeholder communication plan

Not all stakeholders need the same information at the same frequency. Over-communicating wastes time. Under-communicating breeds surprises.

### Stakeholder mapping

Classify stakeholders on two axes:
- **Interest**: How much do they care about the outcome?
- **Influence**: How much power do they have over the outcome?

| | High Influence | Low Influence |
|---|---|---|
| **High Interest** | Manage closely | Keep informed |
| **Low Interest** | Keep satisfied | Monitor only |

### Communication plan template

| Stakeholder | Role | Interest | Influence | Frequency | Format | Key Messages |
|---|---|---|---|---|---|---|
| VP Engineering | Sponsor | High | High | Weekly | 1:1 meeting | Timeline, risks, resource needs |
| Product Manager | Partner | High | Medium | 2x/week | Slack + weekly sync | Scope changes, trade-offs, blockers |
| Security Team | Reviewer | Medium | High | Biweekly | Written update | Compliance status, audit findings |
| Customer Support | Downstream | Medium | Low | Monthly | Email summary | Feature changes, timeline, training needs |

### Communication plan rules
1. High influence + high interest stakeholders get face time. Don't rely on email alone.
2. Tailor the message to what they care about — executives want outcomes, engineers want details.
3. Bad news travels up immediately. Never let a sponsor be surprised in a meeting they didn't expect.
4. Review and adjust the plan every 2-4 weeks as the project evolves.

---

## Decision log

Decisions made in meetings evaporate unless written down. A decision log is the institutional memory of a project.

### Decision log template

| Date | Decision | Context | Alternatives Considered | Rationale | Owner | Review Date |
|---|---|---|---|---|---|---|
| 2024-01-15 | Use PostgreSQL over MongoDB | Need complex joins for reporting; team has SQL expertise | MongoDB (flexible schema, but weak joins), DynamoDB (scalable but costly for our access patterns) | Relational model fits our domain; team ramp-up cost is zero; managed PostgreSQL available on our cloud provider | @tech-lead | 2024-04-15 |
| 2024-01-22 | Defer mobile app to Q3 | 60% of users are desktop-only; mobile usage growing but not urgent | Build now (high cost, diverts from core), React Native wrapper (fast but limited UX), PWA (compromise) | Desktop-first delivers most value per engineering hour; revisit when mobile reaches 40% of traffic | @product-mgr | 2024-03-22 |
| 2024-02-01 | Adopt trunk-based development | Long-lived branches causing painful merges; CI pipeline supports fast feedback | Git Flow (familiar but slow), GitHub Flow (simpler but still uses feature branches) | Trunk-based reduces merge pain, forces smaller changes, aligns with CI/CD goals; team agreed after trial sprint | @eng-mgr | 2024-05-01 |

### Decision log rules
1. Record the decision within 24 hours. Memory degrades fast.
2. Always capture alternatives considered — future you will wonder "why didn't we just do X?"
3. Set a review date. Decisions made under constraints should be revisited when constraints change.
4. The owner is not necessarily the decision-maker — they are the person responsible for revisiting the decision if circumstances change.

---

## Meeting structure templates

Most meetings fail because they lack structure. Pick the right template for the meeting type.

### Decision meeting
**Purpose:** Make a specific decision and leave with an owner.
**Duration:** 30-45 minutes. **Max attendees:** 5-7 (decision-makers only).

1. **Frame** (5 min) — State the decision to be made. Define decision criteria upfront.
2. **Present options** (10 min) — Share 2-3 options with pros/cons. Pre-read materials sent 24h before.
3. **Discuss criteria** (10 min) — Evaluate each option against the criteria. Use Six Thinking Hats if the discussion gets heated.
4. **Decide** (5 min) — The accountable person makes the call. Silence is not agreement — poll the room.
5. **Assign actions** (5 min) — Who does what by when. Write it down in the meeting notes before anyone leaves.

### Status update
**Purpose:** Surface blockers and coordinate dependencies.
**Duration:** 15-25 minutes. **Max attendees:** 8-10.

1. **Progress** (5 min) — What shipped since last update? Metrics if available.
2. **Blockers** (5 min) — What is stuck and who can unblock it? Name specific people.
3. **Asks** (5 min) — What do you need from others in this room?
4. **Next steps** (5 min) — Key deliverables before the next update. Owners and dates.

**Anti-pattern:** Do not use status meetings for discussion or problem-solving. If a topic needs more than 2 minutes, take it offline with the relevant people.

### Brainstorming
**Purpose:** Generate and prioritize ideas for a specific problem.
**Duration:** 45-60 minutes. **Max attendees:** 5-8.

1. **Diverge** (15 min) — Silent individual brainstorming. Write ideas on sticky notes or a shared doc. No criticism, no discussion. Quantity over quality.
2. **Cluster** (10 min) — Group similar ideas together. Name each cluster.
3. **Converge** (15 min) — Discuss the top clusters. Clarify, combine, refine.
4. **Prioritize** (10 min) — Dot-vote or use impact/effort scoring. Select the top 2-3 ideas to pursue.

**Rule:** The facilitator does not contribute ideas. Their job is to manage time and ensure all voices are heard.

### Retrospective
**Purpose:** Improve team processes based on recent experience.
**Duration:** 45-60 minutes. **Max attendees:** the team (6-10).

1. **What went well** (10 min) — Celebrate wins. Be specific about behaviors, not just outcomes.
2. **What didn't go well** (10 min) — Identify pain points without blame. Focus on systems, not people.
3. **Action items** (15 min) — For each pain point, define one concrete improvement. Assign an owner and a review date.
4. **Follow-up on previous actions** (10 min) — Review action items from the last retro. Did they happen? Did they help?

**Rule:** Start by reviewing last retro's action items. If the team keeps identifying the same problems, the retro process itself needs fixing.

---

## Written communication templates

### RFC (Request for Comments)
Use when proposing a significant change that affects multiple teams or has long-term consequences.

```
# RFC: [Title]
**Author:** [Name] | **Date:** [Date] | **Status:** Draft / Open for Review / Accepted / Rejected
**Review deadline:** [Date — give at least 5 business days]

## Summary
[2-3 sentences. What are you proposing and why?]

## Motivation
[What problem does this solve? What happens if we do nothing?]

## Proposal
[Detailed description of the proposed change. Be specific enough that someone could implement it.]

## Alternatives considered
[What else did you evaluate? Why did you reject those options?]

## Trade-offs and risks
[What are you giving up? What could go wrong? How will you mitigate?]

## Migration / rollout plan
[How do you get from here to there? Phased rollout? Feature flags? Backward compatibility?]

## Open questions
[What haven't you figured out yet? Where do you need input?]

## Appendix
[Data, benchmarks, diagrams, references.]
```

### Technical proposal
Use for smaller, team-scoped decisions that need documentation but not a full RFC.

```
# [Title]
**Author:** [Name] | **Date:** [Date]

## Problem
[What is broken or missing? Include evidence — metrics, user complaints, incident reports.]

## Proposed solution
[What do you want to build/change? Include enough detail to estimate effort.]

## Alternatives considered
[At least 2 alternatives. For each: description, pros, cons, why rejected.]

## Implementation plan
[Phases, milestones, dependencies. Who does what by when.]

## Risks and mitigations
[Top 3 risks with concrete mitigation strategies.]
```

### Status report
Use for weekly or biweekly updates to leadership or stakeholders.

```
## TL;DR
[1-2 sentences. The single most important thing the reader needs to know.]

## Progress
[What shipped or was completed since last report. Use bullet points.]

## Upcoming
[What's planned for the next period. Key milestones and dates.]

## Risks and blockers
[What could derail the timeline. Be specific about impact and likelihood.]
- Risk: [description] | Impact: [High/Med/Low] | Mitigation: [action]

## Asks
[What do you need from the reader? Be explicit about the action and deadline.]
```

---

## Difficult conversations guide

### Delivering bad news
Bad news does not improve with age. Deliver it early, directly, and with a plan.

1. **Lead with the news.** Don't bury it in context. "We're going to miss the March deadline by two weeks."
2. **Explain the why briefly.** One or two sentences of context. Not a defense, just facts.
3. **Present your recovery plan.** What are you doing about it? What are the options?
4. **State what you need.** Be explicit about the ask — more time, more people, scope reduction.
5. **Own it.** Don't blame others. Even if external factors contributed, focus on what you control.

**Template:** "I need to share some difficult news. [State the bad news]. This happened because [brief context]. Here's what we're doing about it: [recovery plan]. What I need from you is [specific ask]."

### Pushing back on scope
Scope creep kills projects. Pushing back is not saying no — it's saying "yes, and here's what that costs."

1. **Acknowledge the request.** Show you understand the value. "I see why that feature matters to customers."
2. **Make the trade-off visible.** "If we add this, we need to cut X or push the deadline by Y."
3. **Present options.** Give 2-3 paths with trade-offs. Let the stakeholder choose.
4. **Get the decision in writing.** Verbal agreements evaporate. Follow up with an email summarizing the decision.

### Saying no to stakeholders
Sometimes the answer is no. The goal is to say it without burning the relationship.

1. **Say no clearly.** Don't hedge with "maybe" or "we'll try." Ambiguity creates false expectations.
2. **Explain the constraint.** "We can't do this because [resource/timeline/technical constraint]."
3. **Offer an alternative.** "What we can do instead is [alternative that partially addresses the need]."
4. **Redirect to priorities.** "Based on our current priorities from [decision-maker], this would need to displace [current work]. Would you like to discuss reprioritization with [decision-maker]?"

---

## Async communication best practices

### When to use async vs sync

| Use Async | Use Sync |
|---|---|
| Status updates and FYIs | Decisions requiring real-time debate |
| Code reviews and document feedback | Sensitive feedback or difficult conversations |
| Questions that can wait 4+ hours | Urgent blockers (someone is stuck now) |
| Sharing context, data, or proposals | Brainstorming that benefits from rapid iteration |
| Routine approvals | Conflict resolution or alignment conversations |

### Writing effective async updates

1. **Lead with the action needed.** Start with: "[FYI]", "[Action needed by DATE]", "[Decision needed]", or "[Blocking]".
2. **Front-load the summary.** First sentence = the entire point. Details follow for those who need them.
3. **Use structure over prose.** Bullet points, headers, and tables beat paragraphs. Scannable > readable.
4. **Set a response deadline.** "Please review by Thursday EOD" is better than "when you get a chance."
5. **Close the loop.** When a decision is made or an action is completed, update the original thread. Don't leave open threads dangling.

### Async anti-patterns
- **The infinite thread:** 30+ messages with no summary. Solution: Summarize and restart.
- **The drive-by question:** A vague "thoughts?" with no context. Solution: State what you tried, what you're stuck on, and what kind of input you need.
- **The silent disagreement:** Someone disagrees but doesn't say so in the thread, then raises it later in a meeting. Solution: Explicitly ask for objections with a deadline.
- **The notification storm:** Pinging @channel or @here for non-urgent updates. Solution: Use targeted mentions and respect notification boundaries.

---

## Use-case bundles

- Executive update → Minto Pyramid + Status report template
- Performance/coaching feedback → SBI + intent clarification
- Heated cross-team decision → Six Thinking Hats + Conflict Resolution Diagram + Decision meeting template
- Misinterpretation risk → Ladder of inference checkpoints
- New initiative proposal → RFC template + RACI matrix
- Project kickoff → Stakeholder communication plan + RACI matrix
- Scope change request → Pushing back on scope guide + Decision log entry
- Post-incident review → Retrospective template + Decision log
- Cross-timezone collaboration → Async best practices + Status report template

## Output template
- Decision summary
- Rationale and evidence (link to decision log entry)
- Stakeholder impact (reference communication plan)
- RACI for follow-up actions
- Risks and mitigations
- Open questions and next review point
