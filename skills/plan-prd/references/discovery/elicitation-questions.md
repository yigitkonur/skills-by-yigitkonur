# Elicitation Questions

Structured interview questions for PRD discovery, organized by category. Use these to guide Phase 1 conversations. You do not need to ask every question — pick the ones relevant to the feature.

## Problem space

- What specific problem are we solving? (Describe the pain in 2-3 sentences)
- Who experiences this problem? (Which user persona, role, or segment)
- How are they solving it today? (Current workaround or competitor)
- How often does this problem occur? (Daily? Weekly? On specific triggers?)
- What is the cost of NOT solving this? (Revenue, churn, support tickets, developer time)
- Do we have evidence? (Customer quotes, analytics data, support ticket counts, NPS scores)

## Strategic context

- Why does this matter NOW vs. 3 months from now?
- Which company OKR or team goal does this support?
- What is the competitive landscape? (Are competitors solving this already?)
- Is there a contractual, compliance, or regulatory deadline?
- What happens if we de-prioritize this?

## Success definition

- What is the ONE primary metric that defines success? (Not 5 metrics — one)
- What are 2-3 secondary metrics worth tracking?
- What are the guardrail metrics — things that must NOT get worse? (e.g., page load time, error rate, adjacent feature usage)
- What does "good enough for MVP" look like vs. "ideal state"?
- How will we measure these? (Instrumentation, analytics, surveys)
- What is the baseline today for each metric?
- What target do we need to hit, and by when?

## Users and personas

- Who is the primary user? (Role, experience level, goals)
- Who are secondary users? (Other roles who interact with the feature)
- Are there anti-users? (People who should NOT have access)
- What are their jobs-to-be-done (JTBD)?
- What is their current workflow? (Steps, tools, pain points)
- What are their mental models? (How do they think about this domain?)

## Scope and boundaries

- What is explicitly IN scope for this version?
- What is explicitly OUT of scope? Why?
- Are there features we considered but intentionally deferred?
- What is the MVP boundary? What can ship in v1 vs. later?
- Are there hard constraints? (Must use specific tech, must integrate with specific system, must comply with specific standard)

## Technical context

- What tech stack must this use? (Framework, language, infrastructure)
- What existing systems does this feature touch?
- Are there API contracts or data models already defined?
- Are there performance requirements? (Latency, throughput, concurrent users)
- Are there security requirements? (Auth, encryption, data handling)
- Are there accessibility requirements? (WCAG level, assistive technology support)

## Rollout and risk

- How will this roll out? (All users at once? Phased? Feature-flagged?)
- What are the biggest technical risks?
- What are the biggest product risks? (Users don't adopt, behavior changes cause confusion)
- What dependencies exist? (Other teams, external vendors, infrastructure changes)
- What is the rollback plan if things go wrong?
- Are there legal or compliance risks?

## AI-specific questions (when building AI features)

- What tools or APIs does the AI system need access to?
- What evaluation strategy will validate AI output quality?
- What is the acceptable error/hallucination rate?
- How will we handle cases where the AI is uncertain?
- What is the human-in-the-loop escalation path?
- What training data or context does the AI need?
- How will we monitor model performance over time?

## Interview technique

### Do this
- Ask one question at a time, wait for the full answer
- Follow up on vague responses: "Can you be more specific about what 'fast' means?"
- Walk down each branch of the design tree, resolving dependencies one by one
- Capture direct quotes when users describe pain points — they make the PRD compelling
- Label genuine unknowns as `TBD` with an owner and timeline

### Do not
- Ask all questions at once (overwhelming)
- Accept "it should be intuitive" without probing for specifics
- Invent constraints the user did not mention
- Skip the "Why Now?" question — it reveals whether this actually deserves priority
- Move to drafting before reaching shared understanding
