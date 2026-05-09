---
name: enhance-prompt
description: Use skill if you are rewriting a task prompt for an LLM or coding agent to improve execution quality without changing skill instructions or doing the task.
---

# Enhance Prompt

Rewrite a user's raw task prompt with enough context, steering, verification, and halt conditions for another LLM or coding agent to execute it well. Keep the result focused.

## Trigger boundary

Use this skill when rewriting a task prompt before another LLM or coding agent consumes it.

| Need | Use |
|---|---|
| Rewrite a task prompt before another LLM or coding agent consumes it | `enhance-prompt` |
| Improve a skill's instructions by watching a subagent use it | `enhance-skill-by-derailment` |
| Create or substantially redesign a skill | `synthesize-skills` |
| Solve an ambiguous or high-stakes problem directly, not prompt another agent | `do-think` |

If another workflow needs to prepare a prompt for a subagent or external model, use `enhance-prompt` only for that prompt artifact, then return to the parent workflow.

## Core philosophy

You're not rewriting for style. You're doing three things:
1. **Steering HOW the agent thinks** — not just WHAT to think about
2. **Predicting WHERE the agent will trip** — and pre-blocking those failures
3. **Injecting a halt condition** — so the agent knows when it's done

## Workflow

### Step 1 — Read and diagnose (silent)

Read the prompt. Form an internal opinion on these questions — do NOT show this to the user:

| Question | Why it matters |
|---|---|
| What's the narrative arc? | Every good prompt tells a story: here's where we are → here's the problem → here's what done looks like |
| What will the agent do FIRST? | The opening move determines everything. If unclear, the agent will stall or go sideways. |
| Where will it get stuck? | Ambiguity, missing context, scope creep, no exit condition — predict the failure mode. |
| Is this code-related? | If yes, the agent can see the filesystem, run commands, read files. Don't repeat what it can discover. |
| What's the done signal? | How does the agent know to stop? Most prompts forget this and the agent spins. |

### Step 2 — Ask only when it changes the prompt

Ask a planning question only when the answer would materially change the enhanced prompt.

Skip the planning round when:
- The user asked for a direct rewrite.
- The missing detail can be handled as an explicit assumption.
- The prompt is already specific enough to enhance safely.
- The prompt is a one-line surgical edit with unambiguous intent.

If asking, dispatch **one** structured user-question call with **1-4 questions**; do not pad. Use the current runtime's structured user-question tool if available; otherwise use the prose fallback in `references/ask-user-tools.md`. See `references/planning-questions.md` for the axis bank and selection rules.

Per question:
- **2-4 options**, mutually exclusive unless `multiSelect: true` is clearly right (e.g., "which failure modes to block" — multiple is common)
- **First option marked "(Recommended)"** based on your Step 1 diagnosis — not a static default
- **Short labels** (1-5 words), one-line descriptions
- **Do not manually add "Other"** — use the runtime's built-in free-form path when available; see `references/ask-user-tools.md` for fallback wording

### Step 2a — Round 2 (conditional, narrower)

After Round 1 answers come back, assess: did the answers surface a new ambiguity Round 1 could not have anticipated?

**Fire Round 2 only if:**
- An answer steered the enhancement into an axis Round 1 did not cover (e.g., user picked "Plan of attack" on the outcome axis → now you need to ask what shape the plan should take)
- The user chose "Other" with text that introduces a new axis

**Skip Round 2 when:**
- Round 1 cleared the picture — go straight to Step 3
- You are tempted to use Round 2 to "double-check" Round 1 answers → no, just proceed

Round 2 is **one** call to the runtime's ask-user tool, **1-3 focused questions**. Total question budget across both rounds: **≤ 7**. If the budget is blown, make a reasoned default and proceed with a note.

### Step 2b — Target-agent specificity

If the target agent is unknown, write the enhanced prompt in generic task language.
If the user names Codex, Claude Code, Gemini, a local model, an API call, or another target, adapt only the necessary syntax and tool assumptions.
Never mention unavailable tools in the enhanced prompt.

### Step 3 — Enhance

Apply these layers to the prompt. Read `references/enhancement-layers.md` for the full guide.

Budget rule: preserve user intent and voice; target the smallest prompt that blocks the likely failure modes. For normal tasks, keep the enhanced prompt under ~1,200 words or roughly 2x the original, whichever is smaller, unless the user explicitly asks for a full brief.

**Layer 1: Narrative structure**
Give the prompt a beginning-middle-end. The agent needs to know: where are we, what's the problem, what does success look like.

**Layer 2: Thinking steering**
Don't just say what to do — say how to approach it:
- "Start by understanding X before touching Y"
- "Check if Z exists first — if not, the approach changes"
- "Think about this as a [framing] problem, not a [wrong framing] problem"

**Layer 3: Failure pre-emption**
Block the 2-3 most likely ways the agent will go wrong:
- "Do NOT refactor surrounding code — only touch what's asked"
- "If the test suite doesn't exist yet, say so instead of creating one"
- "Scope: just this file, not the whole module"

**Layer 4: Context injection (code-aware)**
If the prompt targets a coding agent, don't explain what the agent can see. Instead:
- Name specific files/paths if the user mentioned them
- Mention the likely tech stack if obvious from context
- Assume the agent can `tree`, `cat`, `grep`, `git log` — don't duplicate that capability

**Layer 5: Verification and halt**
Every enhanced prompt MUST end with:
- A verification step: "After implementing, run X to confirm it works"
- A done signal: "You're done when [specific observable condition]"
- A halt condition: "If you hit [blocker], stop and ask instead of guessing"

Read `references/code-prompt-patterns.md` for code-specific patterns.
Read `references/failure-modes.md` for common agent failure modes to pre-empt.

### Step 4 — Present the artifact

Show the enhanced prompt in a code block. Below it, one line explaining the key improvement.
Use `references/output-contract.md` for the exact response shape and prompt skeleton.
Offer deeper context, tighter scope, or research only when the user asks or the prompt's risk warrants it.

If the user says "run it" — execute the enhanced prompt directly. Reset framing completely.

## Effort calibration

| Input quality | Action |
|---|---|
| Already good (clear intent, specific, has constraints) | Light touch: add halt condition + verification only. Say "Added a done signal and verification step." |
| Decent intent, vague on details | Moderate: add narrative arc + failure pre-emption + halt |
| Raw idea or stream-of-consciousness | Full restructure: all 5 layers. Show the transformation. |

## Decision rules

- If the prompt is already excellent: say so, add only the halt condition, offer to run as-is
- If the prompt is for a coding agent: assume filesystem access, skip explaining tools it has
- If the prompt mentions a specific technology: don't research it unless accuracy is critical (e.g., API versions). The agent doing the work can look things up itself.
- If the prompt is a system/agent prompt (defines behavior, not requests a task): preserve "You are..." framing, add edge-case handling and escalation criteria
- Never add filler techniques for completeness — every addition must fix a specific failure mode

## What NOT to do

- No five-shot examples unless the user asks for them
- No "agent writes its own prompt" meta-prompting
- No 26-principle dumps or academic prompt engineering
- No more than 2 ask-user rounds, ever — and no more than 4 questions per round (Claude Code cap; keep portable)
- No forcing Round 1 on surgical one-liners — skip it when Step 1 diagnosis is unambiguous
- No "Option A / B / C" filler labels — every option must be a meaningful choice the user can compare
- No manually-added "Other" option — Claude Code auto-provides it and most runtimes mimic this; see `references/ask-user-tools.md` if running on a runtime that differs
- No rewriting the user's voice — enhance the content, preserve the tone
- No spawning agents — this skill enhances a user message only

## Reference routing

| File | Read when |
|---|---|
| `references/ask-user-tools.md` | Step 2 decides to ask — use the current runtime's structured question tool or the prose fallback |
| `references/planning-questions.md` | Step 2 decides to ask — conditional axis bank, "(Recommended)" selection rules, swap rules, worked examples |
| `references/output-contract.md` | Producing the final enhanced prompt — response shape, prompt skeleton, budget guardrails, verification examples, assumptions, and prompt lint checklist |
| `references/enhancement-layers.md` | Applying the 5 enhancement layers — detailed guidance per layer |
| `references/code-prompt-patterns.md` | Prompt targets a coding agent — file paths, verification, tech-stack awareness |
| `references/failure-modes.md` | Predicting and pre-empting common agent failure modes |
