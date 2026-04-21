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

### Step 2 — Plan via the runtime's ask-user tool (Round 1, default)

**Default: run Round 1.** For non-trivial prompts, a short upfront planning round catches misalignment cheaper than rewriting after enhancement.

Dispatch **one** user-question call with up to **4 bundled questions** covering the axes most likely to change the enhancement. The tool name depends on the runtime:

- **Claude Code / Anthropic SDK** → `AskUserQuestion`
- **OpenAI Codex** → `ask_user_question`
- **Factory Droid CLI** → `ask_user`
- **Gemini CLI** → `ask-user`
- **Other / unknown runtime** → prose fallback (same options, presented as markdown)

See `references/ask-user-tools.md` for the full runtime-to-tool table, invocation shape, and the prose fallback template. See `references/planning-questions.md` for the canonical axis bank + selection rules.

Per question:
- **2-4 options**, mutually exclusive unless `multiSelect: true` is clearly right (e.g., "which failure modes to block" — multiple is common)
- **First option marked "(Recommended)"** based on your Step 1 diagnosis — not a static default
- **Short labels** (1-5 words), one-line descriptions
- **Do not manually add "Other"** — the tool auto-provides it

**Skip Round 1 only when:**
- The prompt is a one-line surgical edit with unambiguous intent ("fix typo in README line 12")
- The user explicitly said "just enhance, don't ask"
- Step 1 diagnosis shows the prompt is already excellent → proceed with the light-touch path and a one-line note

### Step 2a — Round 2 (conditional, narrower)

After Round 1 answers come back, assess: did the answers surface a new ambiguity Round 1 could not have anticipated?

**Fire Round 2 only if:**
- An answer steered the enhancement into an axis Round 1 did not cover (e.g., user picked "Plan of attack" on the outcome axis → now you need to ask what shape the plan should take)
- The user chose "Other" with text that introduces a new axis

**Skip Round 2 when:**
- Round 1 cleared the picture — go straight to Step 3
- You are tempted to use Round 2 to "double-check" Round 1 answers → no, just proceed

Round 2 is **one** call to the runtime's ask-user tool, **1-3 focused questions**. Total question budget across both rounds: **≤ 7**. If the budget is blown, make a reasoned default and proceed with a note.

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
- No more than 2 ask-user rounds, ever — and no more than 4 questions per round (Claude Code cap; keep portable)
- No forcing Round 1 on surgical one-liners — skip it when Step 1 diagnosis is unambiguous
- No "Option A / B / C" filler labels — every option must be a meaningful choice the user can compare
- No manually-added "Other" option — the tool auto-provides it
- No rewriting the user's voice — enhance the content, preserve the tone
- No spawning agents — this skill enhances a user message, period

## Reference routing

| File | Read when |
|---|---|
| `references/ask-user-tools.md` | Dispatching the planning round — picks the right tool name for the current runtime (AskUserQuestion / ask_user_question / ask_user / ask-user / prose fallback) |
| `references/planning-questions.md` | Running Step 2 (Round 1) — canonical axis bank, picking the "(Recommended)" option, swap rules, worked examples |
| `references/enhancement-layers.md` | Applying the 5 enhancement layers — detailed guidance per layer |
| `references/code-prompt-patterns.md` | Prompt targets a coding agent — file paths, verification, tech-stack awareness |
| `references/failure-modes.md` | Predicting and pre-empting common agent failure modes |
