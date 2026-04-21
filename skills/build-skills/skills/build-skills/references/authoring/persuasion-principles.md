# Persuasion Principles for Skill Design

Use this file when writing a discipline-enforcing skill and the draft feels too soft — agents skim it, "adapt the concept," or ship without following it. The fix is not louder language; it is the right persuasion principle at the right point.

Research basis: Meincke et al. (2025) tested seven Cialdini persuasion principles across N=28,000 LLM conversations. Persuasion techniques more than doubled compliance (33% → 72%, p < .001). LLMs respond to the same principles humans do — they were trained on human text that encodes the pattern.

## The seven principles — which to use, which to avoid

| Principle | Use it | Avoid it |
|---|---|---|
| **Authority** | Discipline skills. Safety. Established best practices. | Guidance or taste-driven skills. |
| **Commitment** | Ensuring the skill is actually followed end-to-end. | Simple one-shot tasks. |
| **Scarcity** | Immediate verification. Time-bound steps. | Long-horizon planning. |
| **Social proof** | Universal patterns. Warning about common failures. | Controversial or niche practices. |
| **Unity** | Collaborative skills. Team culture. Code review. | Strict discipline (dilutes authority). |
| **Reciprocity** | Almost never — feels manipulative. | Default to avoid. |
| **Liking** | Never for compliance. | Always — creates sycophancy. |

## 1. Authority — for non-negotiable rules

The principle: deference to expertise, credentials, or official sources. In prose, this is imperative language with no hedging.

Use for: safety-critical steps, established best practices, discipline skills.

```
Strong:   "Write code before test? Delete it. Start over. No exceptions."
Weak:     "Consider writing tests first when feasible."
```

Why it works: "YOU MUST" removes decision fatigue. Absolute phrasing eliminates the "is this an exception?" question. Training data contains millions of examples of authoritative imperatives followed by compliance.

Where to place it: non-negotiable rules section, guardrails, do/not tables.

## 2. Commitment — for multi-step compliance

The principle: once an agent publicly declares intent, consistency pressure keeps it aligned with that declaration.

Use for: multi-step workflows, accountability checkpoints, ensuring the skill is actually followed.

```
Strong:   "When you find a relevant skill, announce: 'I am using [Skill Name]'
           before executing any of its steps."
Weak:     "Consider mentioning which skill you are using."
```

Why it works: once the agent has announced it is using the skill, violating the skill contradicts its own prior statement. The agent notices the contradiction and self-corrects.

Where to place it: at the top of workflows, after step classification, before commitment-cost steps (deletion, rewrite, rollback).

## 3. Scarcity — for time-bound requirements

The principle: urgency from time limits or limited availability triggers action.

Use for: immediate verification steps, sequential dependencies ("before X"), preventing "I will do it later."

```
Strong:   "Immediately after the code compiles, run the failing test you wrote.
           Do not proceed until it fails for the expected reason."
Weak:     "You can run the test when convenient."
```

Why it works: "immediately" and "before proceeding" block procrastination. The agent cannot defer the step to a future that never arrives.

Where to place it: verification checkpoints, phase gates, any step where delay creates compounding errors.

## 4. Social proof — for universal patterns and warnings

The principle: conformity to what others do or what is considered normal.

Use for: documenting universal practices, warning about common failures, establishing norms.

```
Strong:   "Checklists without TodoWrite tracking → steps get skipped. Every time."
Weak:     "Some people find TodoWrite helpful for checklists."
```

Why it works: "every time" and "without X = failure" establish the behavior as the norm, not one option among many. Universality creates the expectation that breaking the pattern will produce the described failure.

Where to place it: anti-patterns sections, "do this, not that" tables, rationalization tables.

## 5. Unity — for collaboration, not compliance

The principle: shared identity. "We" language invites the reader in.

Use for: collaborative workflows, code review, team culture — situations where the skill and the agent are on the same side.

```
Strong:   "We are colleagues. I need your honest technical judgment — not
           agreement."
Weak:     "You should probably tell me if I am wrong."
```

Warning: do not combine unity with discipline. Unity makes rules feel optional ("we are friends, the rule bends for us"). Use authority for rules, unity for collaboration.

Where to place it: review skills, collaborative workflows, tone-setting intros.

## 6. Reciprocity — avoid

Obligation to return benefits received. In skill prose this feels transactional and manipulative. The other principles are more effective. Default to skipping this one.

## 7. Liking — never use for compliance

Preference for cooperating with those we like. Using warmth to win compliance produces sycophancy: the agent tells the user what they want to hear instead of what is true.

```
Never:    "Please, if you have time, maybe consider..."
Never:    "I hope this is helpful! Feel free to ignore if not applicable."
```

Liking language undermines honest feedback culture, which is the opposite of what a discipline skill needs.

## Combining principles by skill type

| Skill type | Use | Avoid |
|---|---|---|
| Discipline-enforcing (TDD, verification, research-before-synthesis) | Authority + Commitment + Social proof | Liking, Reciprocity, Unity |
| Technique / guidance | Moderate Authority + Unity | Heavy authority, Liking |
| Collaborative (review, pair programming) | Unity + Commitment | Heavy Authority, Liking |
| Reference / format (API docs, syntax) | Clarity only | All persuasion |

Do not try to stack all seven. Two or three principles working together beat seven watered-down ones.

## Application to the build-skills output

When drafting a discipline skill in Step 7 (synthesis):

1. Identify which principle(s) the skill needs — usually authority + commitment.
2. Pick non-negotiable rules and rewrite them in imperative voice with "no exceptions" framing.
3. Add an announcement step ("declare you are using this skill before step 1") if compliance is the main risk.
4. Add a "without X = failure" pattern in anti-patterns for behaviors that commonly get skipped.
5. Reserve unity language for skills where the agent is collaborating, not being disciplined.

## The ethical test

Persuasion in skill prose is legitimate when it serves the user's real interests:

- Ensuring critical practices are followed
- Preventing predictable failures
- Making documentation that actually changes behavior

It is illegitimate when it:

- Creates false urgency to force agreement
- Manipulates for the author's gain at the user's expense
- Uses guilt-based compliance

The test: would the user endorse the technique if they fully understood it was being used? For "YOU MUST run the test before merging," yes. For "thousands of developers agree this framework is the best," no — that is authority manufactured from nothing.

## Quick reference

Before writing the skill, answer:

1. **What type is it?** Discipline, guidance, collaborative, or reference?
2. **What behavior am I trying to change?** Be specific.
3. **Which one or two principles apply?** Usually authority + commitment for discipline.
4. **Am I stacking too many?** More than three principles dilutes each.
5. **Is this ethical?** Does the persuasion serve the user's real interests?

## Sources

- Cialdini, R. B. (2021). *Influence: The Psychology of Persuasion (New and Expanded).* Harper Business.
- Meincke, L., Shapiro, D., Duckworth, A. L., Mollick, E., Mollick, L., & Cialdini, R. (2025). *Call Me A Jerk: Persuading AI to Comply with Objectionable Requests.* University of Pennsylvania. (N=28,000 conversations. Authority, commitment, and scarcity most effective.)
