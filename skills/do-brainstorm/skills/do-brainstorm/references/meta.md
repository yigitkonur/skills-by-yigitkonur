# Meta — When the Session Itself Needs Adjustment

Three frameworks for meta-level decisions about the brainstorm session itself — pacing (OODA), structuring ideation with execution plan (Productive Thinking Model), and deciding whether to prioritize speed or quality in the output (Confidence-determines-Speed-vs-Quality).

Most sessions won't touch this file. Reach for it when:

- The session is dragging and decisions aren't emerging fast enough (OODA)
- You need an end-to-end path from ideation to execution plan, not just a recommendation (Productive Thinking Model)
- You're brainstorming how to BUILD something and need to decide MVP-vs-v1 (Confidence framework)

## OODA Loop

**When**: the session is in a rapidly changing environment, or decisions need to happen faster than analysis can complete. Competitor just shipped; incident is unfolding; user feedback is coming in faster than you can parse.

**The four steps** (cycled continuously, not once):

1. **Observe** — gather available information. Situational context, external data, feedback from previous cycles. Speed matters because data can become obsolete.
2. **Orient** — analyze and synthesize. Consider options. Leverage experience. Challenge the status quo. Consider others' perspectives.
3. **Decide** — select a course of action. Treat it as a **hypothesis you'll test by acting**, not a final commitment.
4. **Act** — implement to test whether the observations and decision were accurate. Feedback feeds the next Observe.

**Key principle**: the advantage is the **tempo of the loop**, not any single decision. Running OODA faster than the environment changes gives you unpredictability — your next move is hard for adversaries / competitors / complexity to anticipate.

**Application to the brainstorm**:

- If the session keeps looping back to Step 2 because new info keeps arriving, use OODA: acknowledge it's a Complex-domain problem, commit to faster cycles, ship smaller decisions and learn
- If the session is exploring something where the "market" shifts weekly (e.g., LLM tooling), plan for OODA cycles explicitly in the recommended next step — "decide on first version, ship, observe for 2 weeks, re-brainstorm"

**Interactions**: OODA complements Cynefin — Cynefin classifies the domain, OODA is the cadence for Complex domain decisions. OODA is NOT a decision method (for that, see `evaluate.md`); it's the tempo structure around the method.

## Productive Thinking Model (Tim Hurson)

**When**: the brainstorm needs to produce a full **execution plan** with success criteria, catalytic questions, and resource allocation — not just a recommendation.

**The six steps**:

1. **What's going on?** Explore the problem's nature: impact, knowledge, parties involved, target future state.
2. **What's success?** Define success via the **DRIVE** framework:
   - **D** — what the solution must **D**o
   - **R** — **R**estrictions
   - **I** — **I**nvestable resources (time, money, people)
   - **V** — **V**alues that must be upheld
   - **E** — **E**ssential outcomes
3. **What's the question?** Generate "catalytic questions" phrased as **"How might we…?"** These frame the solution space.
4. **Generate answers.** Brainstorm potential solutions to the HMW questions. This is where Steps 3-4 of our skill's workflow (Explore + Evaluate) would normally fire.
5. **Forge the solution.** Evaluate candidates against the DRIVE criteria. Use Decision Matrix for scoring.
6. **Align resources.** Document necessary actions, resources, and responsibility assignments for execution.

**Application to the brainstorm**:

- Use Productive Thinking when the session's end-state is a plan, not just a decision
- DRIVE (Step 2 above) is a stronger success-criteria frame than generic "what does success look like?" — use it when stakes are high or stakeholders are multiple
- "How might we…?" questions from Step 3 above feed directly into Step 3 (Explore) of our workflow — use HMW phrasing when generating options

**Interactions**: Productive Thinking wraps around our workflow — its Step 1-2 precede our Step 1 (Cynefin); its Step 6 (align resources) extends our Step 6 (Communicate). If the user asks for "the full plan, not just the decision," adopt Productive Thinking's frame.

## Confidence-Determines-Speed-vs-Quality

**When**: brainstorming what to BUILD (product, feature, system) and the decision "ship the MVP or build the right thing first" needs to be explicit.

**The two axes**:

1. **Confidence in problem importance** — do you genuinely understand the problem's significance? How many users feel it? How much pain?
2. **Confidence in solution correctness** — does your proposed solution actually solve the problem? Is there a better one you haven't found?

**Decision matrix**:

| Problem confidence | Solution confidence | Posture |
|---|---|---|
| Low | Any | **Focus on speed.** Ship the cheapest possible experiment; learn fast. |
| High | Low | **Balance speed + quality.** Iterate, but with rigor. |
| High | High | **Focus on quality.** Invest in the build. The certainty earns the time. |

**Key note**: confidence is a scale, not binary. Outcomes are graded. "Moderately high problem, low solution" → lean toward speed.

**Application to the brainstorm**:

- When the recommendation involves building something, add a "posture" section: speed-first, balanced, or quality-first
- If posture is "speed-first," the recommended next step should be a cheap experiment (hours-to-days), not a full build
- If posture is "quality-first," name the evidence that justifies the certainty — future-you will want to verify the confidence was earned

**Interactions**: Plays with Hard Choice Model (`evaluate.md`) — Hard Choice's "High impact, hard compare, run a cheap experiment" aligns with Confidence's "Low solution confidence → speed-focused experiment." The frameworks converge on: when in doubt, experiment cheaply before investing.

## When to consult this file

Most sessions don't need this file. Signals to reach for it:

| Signal | Framework |
|---|---|
| Session pacing feels wrong — dragging or shallow | OODA — check if the cycle time is mismatched to the environment |
| User wants a full plan, not a decision | Productive Thinking Model — wrap our workflow with DRIVE + resource alignment |
| Deciding what to build at what depth | Confidence-Speed-Quality — surface the posture explicitly |
| Session covered a week-to-ship vs. month-to-ship argument | Confidence framework + Hard Choice Model — make the experiment vs. commit call |

## Common mistakes

| Mistake | Fix |
|---|---|
| Using OODA as a decision method | OODA is a cadence, not a method; use it around methods in `evaluate.md` |
| Productive Thinking's DRIVE not applied because "success is obvious" | Run it anyway; surfaces resource and value constraints that get missed |
| Skipping Confidence framework on build decisions | Build decisions always benefit from the posture call; surface it even if briefly |
| Treating Confidence as binary (shipped vs. not) | It's graded; name the confidence level (Low/Med/High) with evidence |
