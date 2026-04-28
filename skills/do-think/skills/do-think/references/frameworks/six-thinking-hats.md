# Six Thinking Hats

Library entry. Routed from the SKILL.md master table or `modes/interactive-brainstorm.md` Step 3.

## Essence

Rotate through six "hats" — each a distinct mental stance — to force structured perspective-taking. Catches blind spots a single-perspective analysis (the LLM default) glides over.

## When to use

- Phase C1 of the core loop is generating one strong option + two strawmen — perspective rotation surfaces alternatives
- Decisions with stakeholders, tradeoffs, or emotional stakes
- The agent's analysis feels coherent but unbalanced (too optimistic, too pessimistic, too data-bound)
- Interactive Step 3 when the user wants structured exploration

## Procedure

Rotate through six hats. Per hat, generate ideas/observations from that stance only — no blending.

| Hat | Stance | Ask |
|---|---|---|
| **Blue** | Process | What's our goal here? Are we on track? (Start + end with Blue.) |
| **White** | Data | What do we *actually know*? What data is missing? |
| **Yellow** | Positivity | What are the benefits? Best-case scenarios? |
| **Black** | Downside | What could go wrong? Worst-case scenarios? |
| **Green** | Creativity | What wild ideas haven't been considered? Let it run. |
| **Red** | Emotions | Gut reaction? What do you feel without justification? |

## Order: Blue → White → Yellow → Black → Green → Red → Blue

- Start + end with Blue (orchestration).
- Generate (Green) AFTER risks (Black) so creativity isn't pre-filtered by negativity.
- Red last so emotion doesn't anchor analysis.
- Each hat: 1-3 minutes for compact session, longer for deep.

## Output

```
## Six Hats pass

Blue: Goal is X. Constraint is Y.
White: Data: A, B, C. Missing: D.
Yellow: If it works → <benefits>.
Black: Risks → <fail modes>.
Green: Wild options → <unfiltered>.
Red: Gut → <honest reaction>.
Blue: Close. Options that survive: <list>.
```

## What it reveals

Blind spots. Yellow catches "this option has upside we underweighted"; Black catches "this option has a risk we glossed over." Green generates options the analytic process suppressed.

## Interactions

- Pair Green with Zwicky Box (`zwicky-box.md`) when Green stalls.
- Black hat is mid-generation; Inversion in `foundations/stress-test-trio.md` is post-decision — they catch different fail modes.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Blending hats ("here's a balanced view") | Sequential isolation is the whole point. One hat at a time. |
| Skipping Red because "emotions aren't analytical" | Red surfaces unstated stake-holder concerns. Skip it and you miss them. |
| Green that's just "moderate" ideas | Green is *unfiltered*. If your Green ideas are all reasonable, you ran Green wrong — re-do it as "what would be insane to try?" |
| Running Six Hats on a Clear-domain question | Decline. Six Hats has cost; Clear-domain decisions don't earn it. |
