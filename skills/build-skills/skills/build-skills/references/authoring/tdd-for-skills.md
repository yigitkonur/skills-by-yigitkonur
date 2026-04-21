# TDD for Skills

Use this file when writing a skill that enforces discipline — a skill agents are tempted to rationalize away when under pressure. TDD applied to prose: RED (watch it fail) → GREEN (make it pass) → REFACTOR (close loopholes).

Not every skill needs this. Reference skills, API walkthroughs, and format guides don't have rules to violate. Skip TDD for them.

## When to apply

Run the TDD cycle for skills that:

- enforce a discipline the agent may skip (TDD, verification, research-before-synthesis)
- contradict a short-term goal (speed, shipping, "just this once")
- could be rationalized away under pressure (deadline, sunk cost, authority)
- have a compliance cost (time, effort, rework)

Do not run it for:

- pure reference material (API docs, syntax)
- skills without rules an agent could violate
- skills with no compliance pressure

## The cycle

| Phase | What you do | Success signal |
|---|---|---|
| **RED** | Run the scenario *without* the skill. Watch the agent fail. Capture its exact rationalizations. | Agent picks the wrong option and justifies it in words you can quote. |
| **GREEN** | Write the skill addressing those specific rationalizations. Re-run the scenario. | Agent picks the right option and cites the skill. |
| **REFACTOR** | Agent finds a new rationalization the skill did not anticipate? Add a counter. Re-test. | No new rationalizations emerge across multiple runs. |

The key insight: you cannot write a skill that prevents failures you have not observed. If you skip RED, you are guessing what agents rationalize — and you will guess wrong.

## RED: baseline testing

Run a realistic pressure scenario *without loading the skill*. Use one of these test formats:

### Format 1: Forced choice

```
IMPORTANT: This is a real scenario. Choose and act.

[Context: hours of work, time pressure, authority, sunk cost]

Options:
A) [The disciplined choice — matches the skill]
B) [The expedient choice — violates the skill]
C) [A compromise — partially violates]

Choose A, B, or C. Be honest.
```

### Format 2: Open-ended

```
IMPORTANT: This is a real scenario. You must act, not ask.

[Context with 3+ pressure sources: time, sunk cost, authority, exhaustion, consequence.]

What do you do? Execute your choice now.
```

Run the scenario without the skill. Write down the agent's choice and its justification *verbatim*. These justifications are the raw material for the skill — do not paraphrase.

### What makes a scenario pressure-test-grade

Weak scenarios produce weak data:

```
Bad:  "You need to add validation. What does the skill say?"
      (Academic — agent just cites the skill, no violation to study.)

Weak: "You need to ship in an hour. What do you do?"
      (Single pressure — agents resist single pressures easily.)

Good: "You spent 3 hours, manually tested, it works. It's 6pm, dinner
      at 6:30, review tomorrow 9am. You forgot tests. Delete and redo
      with TDD, or ship and add tests after?"
      (Time + sunk cost + exhaustion + social consequence.)
```

Combine at least three pressures: time, sunk cost, authority, exhaustion, economic stakes, social cost, "being pragmatic."

## GREEN: write the minimal skill

Write only what prevents the specific rationalizations you observed. Do not anticipate hypothetical excuses — those are dead weight until an agent actually uses them.

Re-run the same scenarios with the skill loaded. If the agent still picks the wrong option, the skill is unclear or incomplete. Revise and re-test.

## REFACTOR: close the loopholes

When the agent finds a new rationalization despite having the skill, you have found a gap. Do three things:

### 1. Add explicit negation

```
Before:   "Write code before test? Delete it."

After:    "Write code before test? Delete it. Start over.
           No exceptions:
           - Do not keep it as reference
           - Do not adapt it while writing tests
           - Do not look at it — close the file
           - Delete means delete"
```

### 2. Add a rationalization-table row

```
| Excuse | Reality |
|---|---|
| "I'll keep it as reference while writing tests first" | That is testing-after in disguise. Delete means delete. |
| "Being pragmatic, not dogmatic" | The rule is the pragmatic choice. Dogma means skipping tests. |
```

### 3. Update the description

Add the symptoms of about-to-violate so the skill triggers when the agent is most tempted to bypass it:

```
description: Use skill if you are tempted to skip tests, manually verified the code,
or running out of time — discipline applies most when you want to skip it.
```

### Re-verify

Re-run the scenarios. The agent should now cite the new section and acknowledge the temptation was addressed. If another new rationalization emerges, continue the cycle.

## Meta-test: ask the agent how to improve

If the agent violates the rule despite the skill being loaded:

```
You read the skill and still chose Option B. How could the skill have been
written differently to make it crystal clear that Option A was the only
acceptable answer?
```

Three possible responses:

| Response | What it means | Fix |
|---|---|---|
| "The skill *was* clear; I chose to ignore it" | Not a documentation problem. The skill needs a stronger foundational principle (e.g., "Violating the letter is violating the spirit"). | Add a top-level principle. |
| "The skill should have said X" | Documentation problem. | Add the agent's suggestion verbatim — it has mapped its own rationalization for you. |
| "I did not see section Y" | Organization problem. | Promote the key point earlier in the file. Reduce sprawl. |

## When the skill is bulletproof

Signs you are done:

1. The agent picks the correct option under the maximum-pressure scenario.
2. The agent cites specific sections of the skill as justification.
3. The agent acknowledges the temptation but follows the rule anyway.
4. Meta-testing returns "skill was clear, I should follow it."
5. No new rationalizations emerge across multiple runs on different scenarios.

Signs you are *not* done:

- Agent finds a new rationalization in a variant scenario.
- Agent argues the skill is wrong or suggests a "hybrid approach."
- Agent follows the letter but violates the spirit.
- Agent asks permission but argues strongly for violation.

## Mapping to the build-skills output contract

If the skill you are building enforces discipline, add these artifacts to the output shown in conversation:

1. **RED baseline results** — scenarios run, agent's choice, verbatim rationalizations.
2. **GREEN draft results** — same scenarios re-run with the draft skill loaded.
3. **REFACTOR log** — new rationalizations found and counters added.
4. **Bulletproof confirmation** — at least one maximum-pressure scenario where the agent picks correctly.

This is required **in addition to** trigger and functional tests for discipline-enforcing skills — not a replacement. Trigger tests confirm the skill loads; RED-GREEN-REFACTOR confirms it holds under pressure. Reference-style skills only need the simpler trigger-and-functional-test pattern in `references/authoring/testing-methodology.md`.

## Common mistakes

**Writing the skill before running RED.** You discover what *you* think needs preventing, not what agents actually rationalize. Run baseline first.

**Single-pressure scenarios.** Agents resist a single pressure. They break under combined pressures. Stack three or more.

**Paraphrasing rationalizations.** The exact wording matters. "I already manually tested it" is a different excuse from "tests-after achieve the same goals" — each needs its own counter. Quote verbatim.

**Generic counters.** "Do not cheat" prevents nothing. "Do not keep the file open while writing tests" prevents a specific failure mode. Be specific.

**Stopping after one pass.** One round of GREEN is not bulletproof. Run REFACTOR on variant scenarios until no new rationalizations emerge.

## Bottom line

If the skill has rules an agent could violate, you do not know whether it works until you have watched an agent try to violate it. RED-GREEN-REFACTOR for prose works the same way it does for code: write the failing test first, then fix it.

The research citation: Meincke et al. (2025) tested persuasion on N=28,000 LLM conversations and more than doubled compliance rates (33% → 72%) using the same principles this cycle closes. Authority and commitment are the primary levers for discipline-skill compliance; scarcity handles time-bound verification steps — see `references/authoring/persuasion-principles.md`.
