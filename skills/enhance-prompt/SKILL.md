---
name: enhance-prompt
description: "Use skill if you are enhancing a prompt before sending it to an LLM or coding agent — adds narrative structure, thinking-steering, failure pre-emption, halt conditions, and verification layers."
---

# Enhance Prompt

Intercept a user's raw prompt, turbocharge it with context and steering, and return it ready to execute. Fast. No bloat. No agent-spawning — you're just crafting a better user message.

## Trigger boundary

**Use when:** enhancing a prompt before sending it to an LLM or coding agent
**Do NOT use when:** improving general writing (emails, essays), building skill files, or reviewing code

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

### Step 2 — Ask ONLY if scope is genuinely ambiguous

**Default: skip questions entirely.** Most prompts don't need clarification — they need enhancement.

Ask ONLY when the prompt could go in 2+ meaningfully different directions and you can't make a reasonable default assumption. If you must ask, use `AskUserQuestion` with:
- **Maximum 2 questions**, 2-3 options each
- Put the best default first with "(Recommended)"
- Always include an option that says "Just go with your best judgment"

**Skip questions when:**
- The intent is clear even if details are vague (you'll fill them in)
- You can make a sensible default and note it
- The prompt is code-related and the agent can discover context from the filesystem

### Step 3 — Enhance

Apply these layers to the prompt. Read `references/enhancement-layers.md` for the full guide.

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

### Step 4 — Present and offer depth

Show the enhanced prompt in a code block. Below it, one line explaining the key improvement.

Then always end with:

> Want me to dig deeper? I can add more context, tighten the scope, or research the topic first.

If the user says "run it" — execute the enhanced prompt directly. Reset framing completely.

## Effort calibration

| Input quality | Action |
|---|---|
| Already good (clear intent, specific, has constraints) | Light touch: add halt condition + verification only. Say "This is solid — I just added a done signal." |
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
- No excessive AskUserQuestion rounds — 0 or 1 question max
- No rewriting the user's voice — enhance the content, preserve the tone
- No spawning agents — this skill enhances a user message, period

## Reference routing

| File | Read when |
|---|---|
| `references/enhancement-layers.md` | Applying the 5 enhancement layers — detailed guidance per layer |
| `references/code-prompt-patterns.md` | Prompt targets a coding agent — file paths, verification, tech-stack awareness |
| `references/failure-modes.md` | Predicting and pre-empting common agent failure modes |
