# Interaction Patterns — How to Bring the User Along

The skill's whole premise is "user in the loop." This file is the how-to: when to pause, how to phrase questions, when to push back on a user who wants to shortcut a fork, and the "one question at a time" discipline.

## The five forks (recap)

Every interactive session pauses five times, one per step:

| Fork | After | User answers |
|---|---|---|
| Fork 1 | Step 1 (Classify) | Cynefin domain correct? Route right? |
| Fork 2 | Step 2 (Decompose) | Decomposition captures the problem? Branches missing? |
| Fork 3 | Step 3 (Explore) | Options resonate? Add / drop / expand? |
| Fork 4 | Step 4 (Evaluate) | Factors + weights right? Anything over- or under-weighted? |
| Fork 5 | Step 5 (Stress-test) | Blind spots change the pick? Loop back? |

No more, no fewer. Combining forks reduces user control; splitting them into more produces friction.

## One question at a time

When asking **open-ended** questions in a session, bundle only when the questions are truly parallel (choices along different dimensions). If a topic needs more exploration, split into multiple questions across messages.

**Good** (one per message):

```
Before I propose options, I want to make sure I have the right problem.
You mentioned "users aren't adopting the feature." Is the measure:
  (a) zero-use since release, OR
  (b) initial use but no return?
```

**Bad** (multi-topic in one message):

```
Before I propose options, I want to understand: what's the user
segment? What's your success metric? What's the timeline? What
competitors have tried? What's the budget?
```

The user picks one to answer and ignores the rest. Four of five questions go unanswered; session loses depth.

## Multiple-choice via the ask-user tool

When the question has **discrete choices**, use the runtime's ask-user tool (see `cross-runtime.md`). Rules:

- **Up to 4 questions per call** — AskUserQuestion's cap; keep portable
- **2-4 options per question** — structured; more is noise
- **First option marked `(Recommended)`** based on your analysis (not always the same option)
- **"Other" auto-provided** — don't add manually

Multiple-choice is faster for the user to answer and more accurate to capture — they pick rather than type. Use it for:

- Cynefin classification questions (Step 1)
- Decomposition-tool selection ("This looks like a root-cause problem — Issue Tree or Ishikawa?")
- Option-prioritization questions ("Which of these three resonates?")
- Evaluation-factor weighting ("Is latency or operational-simplicity more important?")

Don't use multiple-choice for questions where the answer is prose:

- "Tell me about the current architecture" — open-ended
- "What's the history of this problem?" — open-ended
- "What would failure look like to you?" — open-ended

Rule of thumb: if options A/B/C/D cover the answer space, use the tool. If the user needs to explain something, use a direct prompt.

## Phrasing questions

**Good** question framing:

- Names the decision explicitly: "Before I move to Step 3, I need to confirm the decomposition."
- Names what would make the answer useful: "The option labels below are drafts — I want to know which resonate so I can expand those."
- Names the consequence of the answer: "If we pick Option A, we lock into Postgres; if Option C, we're exploring a switch."

**Bad** question framing:

- Vague: "Thoughts?"
- Leading: "Option A is clearly the best, right?" (pre-filters the user's judgment)
- Multi-layer: "I'm thinking X because Y given Z unless you think W, so what do you want to do?"

## Pausing vs. surfacing

Pause at forks. Surface the rest of the time.

**Surfacing** = you produce output continuously — the decomposition tree, the options list, the evaluation matrix. The user sees what you're doing without being asked.

**Pausing** = you stop and wait for the user at fork points. The fork message explicitly names the decision.

Do NOT surface silently (no output until final) — the user can't redirect.
Do NOT pause continuously (one question per minor choice) — the user gets fatigued.

## When the user wants to skip a fork

Common: the user says "just pick Option B, move on." Or: "skip the stress-test, I'm fine with it."

**The response** depends on which fork:

| Fork | Skip-request response |
|---|---|
| Fork 1 (Classify) | **Refuse skip**. The classification is load-bearing; picking frameworks without it is operating blind. Say: "Let me get 30 seconds of classification; it changes which tools we use." |
| Fork 2 (Decompose) | **Compress, don't skip**. Present decomposition as 3 bullets, ask for y/n to move on. |
| Fork 3 (Explore) | **Compress, don't skip**. Show options as 1-liner each; ask "any missing?" in one message. |
| Fork 4 (Evaluate) | **Compress, don't skip**. Show the matrix; ask "any weights wrong?" |
| Fork 5 (Stress-test) | **Refuse skip** if the decision has reversibility-cost > "fully reversible." Skipping stress-test on irreversible decisions is the skill failing. |

If the user pushes hard after a refuse-skip: comply, but explicitly flag in the output contract that the fork was skipped. "Note: Step 5 was skipped at user request; this recommendation has not been pre-mortemed."

## The compression discipline

Sometimes the user is time-pressed. Each fork has a compressed form:

**Compressed Fork 1** (Classify):
```
Reading this as <domain> because <short rationale>. OK to proceed? (y/n)
```

**Compressed Fork 2** (Decompose):
```
Decomp: <3-bullet summary>. Priority: <1-2 branches>. Anything missing? (yes/no)
```

**Compressed Fork 3** (Options):
```
Options: A <label>, B <label>, C <label>. Which to focus on? (A/B/C/expand X/widen search)
```

**Compressed Fork 4** (Evaluate):
```
Matrix winner: <Option X, score>. Confidence: <H/M/L>. Want to challenge a weight? (y/n)
```

**Compressed Fork 5** (Stress-test):
```
Inversion + Ladder + Second-Order: pick <unchanged / changed to X>. Concerns: <list>. Proceed? (y/n)
```

Use compressed forms when:
- The user explicitly asks for compression
- The session has been running long and pacing needs to pick up
- The decision is low-impact (No-brainer or Apples-&-Oranges in Hard Choice terms)

## YAGNI discipline — cut what doesn't serve

Borrowed from obra/brainstorming: **YAGNI ruthlessly**. Every option, every weight, every factor, every branch in the decomposition — if you can't defend its presence, drop it.

Signs of YAGNI violation:

- Option that's listed because "it could be considered" — no active proponent
- Factor in the Decision Matrix that doesn't discriminate (all options score the same) — drop it
- Branch in the Issue Tree that's there because MECE required it but has no priority — note it exists, don't recurse into it
- Second-order effect that's purely speculative — drop it; every listed effect needs a chain of "and then what"

YAGNI makes the output shorter. Shorter output is easier for the user to evaluate at each fork.

## Pushback patterns

When the user says something that's operationally wrong:

- Wrong framework for the problem → push back with the right framework's name + one-line rationale
- Wrong classification → re-run the 3-question classifier with the user's new information
- Picking an option the evaluation ruled out → ask what evidence they're weighting that the matrix missed; revisit the matrix
- Skipping a fork on an irreversible decision → refuse politely (see above)

Pushback is technical, not oppositional. Frame: "The evaluation has Option A at 70, Option B at 68 — a 2-point gap is inside the rounding error. We can ship Option B if you prefer; I want to flag the Decision Matrix didn't really discriminate."

## When the user is silent

If the user doesn't answer a fork (tool timeout, conversation paused for a long time, etc.):

- Do NOT silently pick an answer
- Do NOT loop asking the same question
- Resume by surfacing a **compressed, one-message** version of the fork: "Still waiting on the <fork N> decision. Compressed: <options>. <specific question in one sentence>."
- If no answer after that, state you'll hold the fork open and offer to resume when the user is back

Never fabricate an answer.

## Common mistakes

| Mistake | Fix |
|---|---|
| Asking 5 questions in one message | One question per message for open-ended; bundle only multiple-choice via the ask-user tool |
| Leading questions ("Option A is best, right?") | Neutral framing; let the user answer without anchor |
| Silently resolving a fork | Always pause at forks; compressed if pressed, never skipped if irreversible |
| Not using the ask-user tool for discrete choices | Tool is faster + more accurate for structured questions |
| Over-pausing (question per minor choice) | 5 forks total; micro-forks inside steps are unnecessary |
| Forbidden phrases ("you're absolutely right", "thanks for the great question") | Delete; actions speak. Technical correctness > social softening |
| Refusing to compress when the user is time-pressed | Compress the surfacing; keep the fork itself |
| Stopping at the final output without an explicit user question | Every session ends with a named question at a concrete fork |
