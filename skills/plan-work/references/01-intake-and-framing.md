# Intake and Framing

## Read this if

- The request is vague, broad, or conflicting.
- People are proposing solutions before defining the problem.
- Planning quality is low because goals are unclear.
- You inherited a project mid-stream and need to re-anchor.
- Multiple stakeholders have different definitions of "done."
- The ask sounds like a solution disguised as a problem.

## Planning vision for this stage

Think like an investigator first, not a builder.
Your job is to convert ambiguity into a decision-ready problem frame.

A well-framed problem is half-solved. Spend 20% of total effort here—it pays back 5x downstream. If you skip framing, you will build the wrong thing faster.

## 5W2H Technique

Use this as a rapid first-pass to surface gaps in understanding. Walk through each question and mark any you cannot answer confidently.

| Dimension    | Question                                      | Your Answer |
|--------------|-----------------------------------------------|-------------|
| **What**     | What is the problem or opportunity?            |             |
| **Why**      | Why does this matter now? What triggered it?   |             |
| **Who**      | Who is affected? Who owns the decision?        |             |
| **Where**    | Where does this occur (system, team, market)?  |             |
| **When**     | When must this be resolved? Any deadlines?     |             |
| **How**      | How will we approach this? Any constraints?     |             |
| **How much** | What resources/budget are available?            |             |

**Rule of thumb:** If you cannot answer 3+ of these, you are not ready to plan. Go back to discovery.

## Practical Intake Questionnaire

Use this questionnaire when receiving a new request. Copy the template and fill it in with the requester.

### Goals

1. What is the single most important outcome you need?
2. Why does this matter now—what triggered the request?
3. What does "done" look like in concrete, observable terms?

### Constraints

4. What is the hard deadline, if any? What drives that date?
5. What budget, team, or technology constraints exist?
6. What must NOT change (protected systems, contracts, processes)?

### Stakeholders

7. Who is the final decision-maker?
8. Who else needs to approve, review, or be informed?
9. Are there stakeholders who might resist or block this work?

### Success Criteria

10. How will we measure success? Name 1-3 metrics.
11. What is the minimum viable outcome vs. the ideal outcome?
12. What does failure look like—how will we know we failed?

### Timeline & Dependencies

13. Are there upstream dependencies (other teams, data, decisions)?
14. Are there downstream consumers who will be affected?
15. What is the sequence: must-have-first → nice-to-have-later?

> **Tip:** If the requester cannot answer questions 1, 7, and 10, the request is not ready for planning. Push back with: *"I want to help. Let's nail down the goal, the decision-maker, and how we'll measure success before we commit resources."*

## Problem Statement Template

A good problem statement eliminates ambiguity. Use this formula:

```
[Who] cannot [do what] because [blocker], causing [impact measured in X].
```

**Examples:**

| Component   | Weak Version                       | Strong Version                                                        |
|-------------|------------------------------------|-----------------------------------------------------------------------|
| Who         | "Users"                            | "Enterprise customers on the Pro plan"                                |
| Cannot      | "have issues with"                 | "cannot complete checkout"                                            |
| Because     | "it's broken"                      | "the payment API times out after 30s under >500 concurrent requests"  |
| Impact      | "it's bad"                         | "causing $12K/day in lost revenue and a 15% increase in churn"        |

**Full strong example:**
> Enterprise customers on the Pro plan cannot complete checkout because the payment API times out after 30s under >500 concurrent requests, causing $12K/day in lost revenue and a 15% increase in monthly churn.

## SMART Goals Framework

Convert vague goals into actionable targets using SMART criteria.

| Letter | Criterion     | Question to Ask                          | Red Flag if Missing                  |
|--------|---------------|------------------------------------------|--------------------------------------|
| **S**  | Specific       | What exactly will change?                | "Improve performance"                |
| **M**  | Measurable     | How will we know it changed?             | No metric defined                    |
| **A**  | Achievable     | Can we do this with current resources?   | No capacity check                    |
| **R**  | Relevant       | Does this connect to a business goal?    | Activity without purpose             |
| **T**  | Time-bound     | By when?                                 | Open-ended timeline                  |

### Conversion example

| Step     | Before                          | After                                                                 |
|----------|---------------------------------|-----------------------------------------------------------------------|
| Vague    | "We need to improve performance" | —                                                                    |
| Specific | —                               | Reduce p95 API latency for the /search endpoint                      |
| Measurable | —                             | From 1200ms to under 300ms                                           |
| Achievable | —                             | Team of 2 backend engineers, no infrastructure changes needed        |
| Relevant | —                               | Search latency is the #1 driver of user drop-off in onboarding       |
| Time-bound | —                             | Completed and deployed by end of Q3                                  |

**SMART result:** *Reduce p95 API latency for /search from 1200ms to under 300ms by end of Q3, using 2 backend engineers, to address the #1 driver of onboarding drop-off.*

## Stakeholder Mapping Template

Use the Power/Interest grid to decide how to engage each stakeholder.

|                | Low Interest     | High Interest    |
|----------------|------------------|------------------|
| **High Power** | Keep Satisfied   | Manage Closely   |
| **Low Power**  | Monitor          | Keep Informed    |

### Stakeholder register (copy and fill)

| Name / Role | Power (H/M/L) | Interest (H/M/L) | Quadrant         | Engagement Action              |
|-------------|----------------|-------------------|------------------|--------------------------------|
|             |                |                   |                  |                                |

**Engagement actions by quadrant:**

- **Manage Closely** → Regular 1:1 updates, involve in decisions.
- **Keep Satisfied** → Periodic summaries, no surprises.
- **Keep Informed** → Group updates, demo invitations.
- **Monitor** → Inform only on major milestones.

## Scope Definition Template

Define boundaries explicitly. If it is not in "In" or "Out," it belongs in "Unknown"—and unknowns require research before planning.

| Category    | Item                                    | Notes                                  |
|-------------|-----------------------------------------|----------------------------------------|
| **In**      |                                         |                                        |
| **In**      |                                         |                                        |
| **Out**     |                                         |                                        |
| **Out**     |                                         |                                        |
| **Unknown** |                                         | Owner + resolve-by date required       |

> **Rule:** Never plan around unknowns. Convert every "Unknown" to "In" or "Out" before committing to a plan. Each unknown should have an owner and a resolve-by date.

## Framing Flow

1. **State mission in one sentence.** Use the problem statement template above.
2. **Separate facts from assumptions.** Facts have evidence. Assumptions need validation.
3. **Define success and failure signals.** Use SMART criteria for success; define explicit failure modes.
4. **Set boundaries (in, out, unknown).** Use the scope definition template above.

### Facts vs. Assumptions worksheet

| # | Statement | Fact or Assumption? | Evidence / Validation Needed |
|---|-----------|---------------------|------------------------------|
| 1 |           |                     |                              |
| 2 |           |                     |                              |

## Method Steering

### First principles
Use when assumptions dominate.
- Thinking posture: "What must be true regardless of opinion?"
- Technique: Strip away conventions. Ask "Why?" five times until you reach bedrock truth.

### Abstraction laddering
Use when discussion is at the wrong altitude.
- Thinking posture: "Why does this matter?" then "How does it become action?"
- Go up: "Why?" → reveals purpose. Go down: "How?" → reveals tasks.

### Issue trees
Use when scope is messy.
- Thinking posture: "Break the whole into clear branches before solving."
- Each branch must be mutually exclusive and collectively exhaustive (MECE).

### Concept map
Use when entities and relationships are unclear.
- Thinking posture: "Understand connections before sequencing actions."

### Ladder of inference (bias guard)
Use to verify jumps from data to conclusion.
- Thinking posture: "What did we observe vs what did we infer?"
- Walk down the ladder: Conclusion → Belief → Interpretation → Selected data → Observable data.

## Use-Case Bundles

| Situation                                | Recommended Methods                              |
|------------------------------------------|--------------------------------------------------|
| New initiative, fuzzy objective           | First principles + Issue trees                   |
| Strategy discussion too abstract          | Abstraction laddering + Concept map              |
| Team disagreement on "what the problem is"| Ladder of inference + mission statement reset     |
| Inherited project, unclear scope          | 5W2H + Intake questionnaire + Scope definition   |
| Executive request, no detail              | SMART conversion + Stakeholder mapping            |
| Many stakeholders, conflicting priorities | Stakeholder mapping + Problem statement template  |

## Output Template

Every framing session should produce this artifact. Copy and fill.

```markdown
## Framing Output — [Project Name]
**Date:** YYYY-MM-DD  |  **Facilitator:**  |  **Attendees:**

### Mission Statement
[One sentence. Use the problem statement template.]

### Facts
1.  2.  3.

### Assumptions (to validate)
1. [Assumption] → Validation: [how] → Owner: [who] → By: [date]

### Scope Boundaries
| In | Out | Unknown (+ resolve-by date) |
|----|-----|-----------------------------|
|    |     |                             |

### Success Criteria (SMART)
1.  2.

### Failure Signals
1.  2.

### Stakeholder Map
| Name / Role | Power | Interest | Action |
|-------------|-------|----------|--------|
|             |       |          |        |

### Unknowns Requiring Research
| Unknown | Owner | Resolve-by | Method |
|---------|-------|------------|--------|
|         |       |            |        |

### Next Steps
1.  2.
```

## Worked Example

**Vague request:** *"We need to improve performance."*

### Step 1 — 5W2H pass

| Dimension    | Answer                                                       |
|--------------|--------------------------------------------------------------|
| What         | API response times are slow                                  |
| Why          | Users are complaining; drop-off increased 20% this quarter   |
| Who          | Affects all users; owned by backend team                     |
| Where        | /search and /dashboard endpoints                             |
| When         | Must improve before Q4 product launch (8 weeks)              |
| How          | Unknown—needs profiling                                      |
| How much     | 2 engineers available; no budget for new infrastructure      |

### Step 2 — Problem statement

> All users cannot load search results in under 2 seconds because the /search endpoint p95 latency is 1200ms, causing a 20% increase in onboarding drop-off this quarter.

### Step 3 — SMART goal

> Reduce /search p95 latency from 1200ms to 300ms by Oct 15, using 2 backend engineers, to reverse the 20% onboarding drop-off.

### Step 4 — Scope definition

| Category    | Item                                      | Notes                              |
|-------------|-------------------------------------------|------------------------------------|
| **In**      | /search endpoint optimization             | Primary target                     |
| **In**      | Database query profiling                  | Likely root cause                  |
| **In**      | Add caching layer for hot queries         |                                    |
| **Out**     | /dashboard endpoint                       | Defer to next quarter              |
| **Out**     | Frontend rendering performance            | Separate workstream                |
| **Unknown** | Is the bottleneck in the DB or app layer? | Profile by Aug 25; owner: Alice    |

### Step 5 — Stakeholder map

| Name / Role           | Power | Interest | Action                        |
|-----------------------|-------|----------|-------------------------------|
| VP Product            | H     | H        | Weekly update, decision-maker |
| Backend team lead     | M     | H        | Daily standup, executor       |
| Frontend team lead    | M     | L        | Inform at milestones          |
| Customer support lead | L     | H        | Share timeline for user comms |

### Step 6 — Framing output

Mission: Reduce /search p95 from 1200ms to 300ms by Oct 15 to reverse onboarding drop-off.
Facts: p95 is 1200ms today; drop-off up 20%; Q4 launch is Oct 30.
Assumptions: DB queries are the bottleneck (validate by Aug 25).
Next step: Alice profiles /search by Aug 25 → team reviews results → plan sprints.

## Anti-Patterns

| Anti-Pattern                         | What It Looks Like                                                  | How to Fix                                                         |
|--------------------------------------|---------------------------------------------------------------------|--------------------------------------------------------------------|
| **Solution-first thinking**          | "We need to migrate to microservices"                | Ask: "What problem does that solve?" Reframe as a problem.         |
| **Treating assumptions as facts**    | "Users hate the new UI" (no data)                    | Label it as an assumption. Define a validation step.               |
| **Mixing urgency with importance**   | Urgent-but-trivial items crowd out important work    | Separate urgency from impact. Use an Eisenhower matrix if needed.  |
| **Boiling the ocean**                | Scope keeps growing, no boundaries                   | Force an In/Out/Unknown table. Say "out" more often.               |
| **Invisible stakeholders**           | Key people learn about the project too late           | Run the stakeholder mapping exercise before planning.              |
| **Vague success criteria**           | "We'll know it when we see it"                       | Apply SMART. If you can't measure it, it's not a criterion.        |
| **Premature commitment**             | Building before unknowns are resolved                | Block planning on unknowns. Each unknown needs an owner and date.  |
| **Copy-paste goals**                 | Reusing last quarter's OKRs without re-evaluating    | Re-run the intake questionnaire. Context changes; goals must too.  |
| **Single-perspective framing**       | Only the requester's view is captured                | Interview at least 2 additional stakeholders before finalizing.    |
