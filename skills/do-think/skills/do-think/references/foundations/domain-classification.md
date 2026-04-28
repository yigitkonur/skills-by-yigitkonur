# Domain Classification — Cynefin

Phase A1. The first move in the Frame phase. Different kinds of situations require different kinds of responses; treating one domain's problem with another domain's tools produces fluent-looking analysis that doesn't help.

Cynefin (pronounced "ku-NEV-in") classifies the situation, then prescribes the action sequence.

## The five domains

| Domain | Signature | Action sequence | Solo agent default |
|---|---|---|---|
| **Clear** (Obvious) | Familiar problem, clear cause-effect, stable conditions. "Known knowns." | Sense → Categorize → Respond | Apply the established best practice; no further thinking needed. Decline `do-think` if invoked on a Clear problem. |
| **Complicated** | Multiple plausible answers exist but aren't immediately obvious. "Known unknowns." Investigation will resolve. | Sense → Analyze → Respond | Decompose (`frameworks/decomposition-tools.md`); pick via `frameworks/decision-matrix.md`. |
| **Complex** | "Unknown unknowns." Cause-effect emerges only through probing. Unclear what to measure. | Probe → Sense → Respond | Cheap experiment FIRST, then assess. Use `frameworks/six-thinking-hats.md` / `frameworks/zwicky-box.md` / `frameworks/systems-tools.md` for option generation. |
| **Chaotic** | Out of control. No clear cause-effect. Immediate action required to stabilize. | Act → Sense → Respond | Take the most conservative stabilizing action. Defer deep thinking until stabilized. |
| **Disorder** | You cannot tell which domain. | Identify the domain first | Run Abstraction Laddering (`reframing.md`), then re-classify. |

## Sequence inversion is the key insight

Most analysts default to Sense → Analyze → Respond regardless of domain. That fails for Complex (analysis assumes the answer is discoverable; it isn't) and for Chaotic (analyzing while the building burns wastes time).

Cynefin's contribution is **inverting the sequence by domain**:
- Complex requires Probe BEFORE Sense — you generate signal by acting.
- Chaotic requires Act BEFORE Sense — you stabilize, then learn.

Recognize the domain, invert the sequence accordingly.

## How to classify quickly (3-question check)

Ask yourself:

### Q1. What shape is this problem?

| Answer | Likely domain |
|---|---|
| Design decision (architecture, framework, API shape) | Complicated or Complex |
| Root-cause hunt (recurring bug, unclear failure) | Complicated (decompose) or Complex (probe) |
| Prioritization under constraint | Complicated |
| Novel exploration (no clear precedent) | Complex |
| Stabilizing a crisis (production down, data at risk) | Chaotic |
| I don't know | Disorder |

### Q2. How clear is cause-effect?

| Answer | Domain |
|---|---|
| Fully understood | Clear |
| Multiple plausible paths, analysis will resolve | Complicated |
| Unknown unknowns, not sure what to measure | Complex |
| Genuinely chaotic, no stable pattern | Chaotic |

### Q3. How reversible is the outcome?

Reversibility doesn't change Cynefin domain but changes how heavy the stress-test trio runs in Phase C2:

| Answer | Trio strictness |
|---|---|
| Fully reversible | Light trio; one-pass thinking acceptable |
| Adjustable with effort | Standard trio |
| Costly to reverse | Strict trio + extra Inversion + named rollback |
| One-shot (migration, irreversible deploy) | Strictest trio + explicit rollback + High tier |

## Combining the answers

If two questions point to different domains, **prefer the more exploratory one**. The cost of over-exploring is small; the cost of analyzing an un-analyzable problem is "lots of pretty diagrams that don't help."

| Combination | Domain |
|---|---|
| Q1=Design, Q2=Plausible paths, Q3=Adjustable | Complicated |
| Q1=Root-cause, Q2=Unknown unknowns, Q3=Any | Complex |
| Q1=Stabilizing, Q2=Chaotic, Q3=One-shot | Chaotic |
| Q1=Novel, Q2=Unknown unknowns, Q3=Any | Complex |
| Q1=Prioritization, Q2=Fully understood, Q3=Any | Complicated |
| Any "I don't know" | Disorder |

## Boundary signals — when domain shifts mid-session

Domain changes happen. Watch for:
- "We've fixed it three times and it keeps coming back" → drift from Complicated toward Complex (try probing)
- "The probe revealed a clear mechanism" → drift from Complex toward Complicated (now decompose)
- "The system is unstable RIGHT NOW" → escalation to Chaotic (stabilize first)

When the domain shifts, re-enter Phase A1 and re-emit the opening contract; the action sequence has to follow.

## Solo mode application

In Solo mode, you classify silently using the three questions above, write the domain in the opening contract, and proceed. No question asked of the user.

Confidence comes from the three questions being answerable without speculation. If they aren't answerable, you're in Disorder — run Abstraction Laddering (`reframing.md`) to reset.

## Interactive mode application

Interactive mode (`modes/interactive-brainstorm.md`) wraps a 3-question dispatch around this classifier — see Step 1 / Fork 1 there. The questions become user-facing multiple-choice via the runtime's ask-user tool (see `cross-runtime.md`).

## When the answer is Clear — decline the skill

If classification returns Clear, do not run the full loop. The right move is to apply the established best practice and stop. Burning a deep-think pass on "How should I name this commit?" signals the skill cannot distinguish shapes.

In Solo mode: state the standard answer, cite the source if available, stop.

In Interactive mode: tell the user the answer is standard, name it, offer to brainstorm only if they want to deviate.

## When the answer is Chaotic — stabilize first

If Chaotic, the deep-think loop is the wrong tool *for now*. Take the most conservative stabilizing action; once stabilized, re-run Phase A1 and likely re-classify as Complicated (post-stabilization).

Do not run the full trio in the middle of an active outage. Stabilize, then think.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Skipping the classifier because "this is obviously Complicated" | Ask the three questions anyway. "Obvious" is the most reliable signal of getting domain wrong. |
| Treating Complex as Complicated | Symptom: analysis multiplies but no action emerges. Switch to probe-based action — cheap experiment, see what the system says. |
| Treating Chaotic as Complex | You're trying to learn from data that hasn't stabilized. Stabilize first, then probe. |
| Running the full deep-think loop on a Clear-domain question | Decline. Apply the standard. Save the deep think for problems that earn it. |
| Misclassifying as Disorder when one of three questions can be answered | Disorder is genuinely "I don't know any of the three." If you can answer two of three, classify by those. |
