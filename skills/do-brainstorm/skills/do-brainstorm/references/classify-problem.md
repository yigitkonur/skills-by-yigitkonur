# Classify the Problem (Step 1 — Cynefin First)

Every session starts here. Before choosing frameworks, classify the problem's domain. The Cynefin framework (pronounced "ku-NEV-in") is the router: each domain calls for different action sequences and different downstream tools.

## The five domains

| Domain | Signature | Action sequence | Routes to |
|---|---|---|---|
| **Clear** (Obvious / Simple) | Familiar problem, clear cause-effect, stable conditions. "Known knowns." | Sense → categorize → respond | **Decline brainstorm**: recommend the established best practice |
| **Complicated** | Multiple plausible answers exist, but aren't immediately obvious. "Known unknowns." Clear questions needing investigation. | Sense → analyze → respond | Step 2 (decompose) using **Issue Trees** or **Ishikawa** |
| **Complex** | "Unknown unknowns." Situation can't be understood by analysis. Unclear what questions to ask first. | Probe → sense → respond | Step 2 lite + Step 3 (**Six Thinking Hats**, **Connection Circles**, **Zwicky Box**) |
| **Chaotic** | Out of control. No clear cause-effect. Immediate action required to stabilize. | Act → sense → respond | Step 2 lite + Step 4 (**Hard Choice Model** for triage) |
| **Disorder** | You can't tell which domain applies. | Identify the domain first | Run **Abstraction Laddering**, then re-classify |

**Key principle:** different kinds of situations require different kinds of responses. Treating a Complex problem with Complicated-domain tools (pure analysis) fails — because analysis assumes the answer is discoverable, which it isn't. Treating a Complicated problem as Complex (experiment-first) wastes time — because analysis would have resolved it.

## The 3-question classifier

Dispatch ONE ask-user-tool call with these 3 questions (see `cross-runtime.md` for tool names per runtime):

### Question 1: problem shape

> "What shape is this problem?"

| Option | Signal |
|---|---|
| Design decision (architecture, framework choice, API shape) | Usually **Complicated** or **Complex** |
| Root-cause hunt (recurring bug, unclear failure) | Usually **Complicated** (decompose) or **Complex** (probe) |
| Prioritization under constraint | Usually **Complicated** (evaluate known options) |
| Novel exploration (no clear precedent) | Usually **Complex** or **Chaotic** |
| Stabilizing a crisis (production down, data at risk) | **Chaotic** |
| I'm not sure what shape this is | **Disorder** → run Abstraction Laddering |

### Question 2: cause-effect clarity

> "How clear is cause-effect here?"

| Option | Signal |
|---|---|
| Fully understood | **Clear** — decline |
| Multiple plausible paths, analysis will resolve | **Complicated** |
| Unknown unknowns, not sure what to even measure | **Complex** |
| Genuinely chaotic, no stable pattern | **Chaotic** |

### Question 3: reversibility

> "How reversible is the outcome?"

| Option | Signal |
|---|---|
| Fully reversible, low-stakes | Favor quicker routes (Big Choice or No-brainer in Hard Choice Model) |
| Adjustable with effort | Normal routing |
| Costly to reverse | Extra weight on Step 5 (stress-test) |
| One-shot (migration, irreversible deploy) | Extra weight on Step 5; also surface this in the output contract's Risks section |

Reversibility doesn't change Cynefin domain but does change how much time to spend in Step 5 (stress-test) — irreversible calls get more Inversion + Second-Order Thinking.

## Combining the answers

Take the modal answer across the three questions:

| Combination | Domain |
|---|---|
| Q1=Design, Q2=Plausible paths, Q3=Adjustable | **Complicated** |
| Q1=Root-cause, Q2=Unknown unknowns, Q3=Any | **Complex** |
| Q1=Stabilizing, Q2=Chaotic, Q3=One-shot | **Chaotic** |
| Q1=Novel, Q2=Unknown unknowns, Q3=Any | **Complex** |
| Q1=Prioritization, Q2=Fully understood options, Q3=Any | **Complicated** |
| Any question answered "I'm not sure" | **Disorder** |

If answers straddle two domains (e.g. Complicated + Complex), **prefer the more exploratory one** (Complex). The cost of over-exploring is small; the cost of analyzing a problem that can't be analyzed is "lots of pretty diagrams that don't help."

## The Disorder path — Abstraction Laddering

If classified as **Disorder**, run Abstraction Laddering before anything else.

Steps:

1. Write the current problem statement as the user stated it.
2. Ask **"Why?"** to climb one rung up — produces a more abstract statement. (e.g., "Make the login page faster" → why → "Reduce friction in the first-touch user experience")
3. Ask **"How?"** from the original to climb one rung down — produces a more concrete statement or solution. (e.g., "Make the login page faster" → how → "Reduce the bundle size of the login route")
4. Offer the user 3 problem statements: original + one rung up + one rung down.
5. Ask: "Which of these is the actual problem you're trying to solve?"

Once the user picks, re-run the 3-question classifier on the chosen framing.

## What "Clear" looks like — when to decline

If classification returns **Clear**, do not run the brainstorm. Respond with:

> "This has a standard answer: <the best practice>. Recommending that directly. If you'd like to deviate from the standard, let me know why — we can brainstorm the custom path then."

Examples of Clear-domain asks:

- "How should I structure a PR title?" → follow Conventional Commits; no brainstorm needed
- "What file-naming convention should I use?" → check the repo's existing convention; no brainstorm needed
- "Should I write tests for this one-line typo fix?" → no; write the fix

Declining is respectful of the user's time. Running a 6-step brainstorm on a Clear-domain problem signals the skill can't distinguish shapes.

## Chaotic — the "act first, stabilize, then brainstorm" path

If classified as **Chaotic** (production down, data at risk, financial emergency), the brainstorm is not what the user needs first. Respond:

> "This reads as a Chaotic-domain problem — act first to stabilize, then we brainstorm once the immediate fire is out. Right now: <the most conservative stabilizing action>. Do you want me to help with that first, or is the immediate action already handled and we're here to think about what's next?"

Only run the full brainstorm if the user confirms the chaos is already under control. Otherwise the brainstorm is the wrong tool.

## Fork 1 output (what to surface)

After classification, show the user:

```
## Classification

Problem shape: <from Q1>
Cause-effect clarity: <from Q2>
Reversibility: <from Q3>

Cynefin domain: <domain>

Proposed route:
- Step 2 decomposition tool: <Issue Trees / Ishikawa / Iceberg / Abstraction Laddering>
- Step 3 generative tools: <Six Thinking Hats / First Principles / Zwicky Box / Connection Circles>
- Step 4 evaluation: <Decision Matrix / Impact-Effort / Hard Choice>
- Step 5 stress-test (always): Inversion + Ladder of Inference + Second-Order

Does this read right? Anything that changes the shape?
```

Wait for approval or redirect. Do not proceed to Step 2 until confirmed.

## Common mistakes

| Mistake | Fix |
|---|---|
| Skipping Cynefin because "it's obviously Complicated" | Run the 3-question classifier anyway; assumptions about domain are commonly wrong |
| Treating Complex as Complicated | The symptom: diagrams multiply, no action emerges. Switch to probe-based tools (Zwicky Box, Six Hats) |
| Treating Disorder as any specific domain | Run Abstraction Laddering first; disorder means you don't know what problem you're solving |
| Running the full 6-step brainstorm on a Clear-domain question | Decline. Recommend the best practice. |
| Missing the Chaotic signal | "Production down", "user data at risk", "paying customer blocked right now" are chaotic markers. Stabilize first. |
