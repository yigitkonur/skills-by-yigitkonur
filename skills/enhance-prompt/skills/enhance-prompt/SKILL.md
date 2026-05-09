---
name: enhance-prompt
description: Use skill if you are improving a task prompt for another LLM or coding agent — adding steering, halt conditions, verification, and pre-empting the failure modes that would derail execution.
---

# Enhance Prompt

Rewrite a user's raw task prompt so another LLM or coding agent executes it well. The job is not style — it is **steering how the agent thinks, predicting where it trips, and injecting a halt condition** so it knows when to stop.

## When to use

*Trigger on any of these tells:*

- *"make this prompt better" / "rewrite this prompt" / "tighten this for Codex"*
- *"the prompt isn't getting the result I want" / "the agent keeps going off-track"*
- *user pastes a prompt destined for a sibling LLM, coding agent, or background subagent*
- *user wants a prompt to do a specific coding task and asks for steering, scope, or a done signal*
- *user asks to add halt / verification / failure-mode coverage to an existing prompt*
- *user says "turn this into a brief for an agent" / "package this as instructions"*
- *prompt is for an agent the user does not control directly (Codex, a queued job, a remote runtime)*

**Do NOT use when:**

- the user wants the *task itself* executed, not the prompt rewritten — just do the task
- the task is to improve a **skill's** instructions by watching a subagent use it → `enhance-skill-by-derailment`
- the task is to **create** or substantially redesign a skill → `skill-creator`
- the user is reasoning under ambiguity for themselves and is not preparing a prompt for another agent → `do-think`

If another workflow needs to prepare a prompt for a subagent or external model, use `enhance-prompt` for that prompt artifact only, then return to the parent workflow.

## Core philosophy — three jobs, in order

1. **Steer HOW the agent thinks** — not just what to think about. Frame the problem; sequence the approach; name the wrong framing to avoid.
2. **Predict WHERE the agent will trip** — and pre-block the 2–3 most likely failure modes. See `references/failure-modes.md` for the catalogue.
3. **Inject a halt condition** — a verification step, an observable done signal, and an "if X, stop and ask" boundary. Most prompts forget this and the agent spins.

Everything else is decoration. If a layer does not fix a specific failure mode, drop it.

## Non-negotiable rules

1. **Every enhanced prompt ends with a verification + done signal + halt condition.** Non-optional. See Layer 5 below.
2. **Preserve the user's voice and intent.** Rewrite the content, not the tone.
3. **Smallest prompt that blocks the likely failure modes.** Target ≤1,200 words or ≤2× the original, whichever is smaller, unless the user explicitly asks for a full brief.
4. **Never mention tools the target agent may not have.** If the target agent is unknown, use generic task language.
5. **Never spawn agents.** This skill enhances a user message — it does not execute the prompt.
6. **Never add filler techniques for completeness.** Every addition must fix a named failure mode.
7. **No more than 2 ask-user rounds, ever.** Round 1: 1–4 questions. Round 2 (conditional): 1–3 questions. Total budget ≤7.

## Workflow

### Step 1 — Read and diagnose (silent)

Read the prompt. Form an internal opinion on these questions — do not show this to the user:

| Question | Why it matters |
|---|---|
| What is the narrative arc? | Every good prompt tells a story: where we are → the problem → what done looks like. |
| What will the agent do FIRST? | The opening move determines everything. If unclear, the agent stalls or goes sideways. |
| Where will it get stuck? | Ambiguity, missing context, scope creep, no exit condition — predict the failure mode. |
| Is this code-related? | If yes, the agent can see the filesystem, run commands, read files. Don't repeat what it can discover. |
| What is the done signal? | How does the agent know to stop? Most prompts forget this and the agent spins. |

### Step 2 — Ask only when an answer changes the prompt

Ask a planning question only when the answer would materially change the enhanced prompt.

**Skip the planning round when:**
- The user asked for a direct rewrite.
- The missing detail can be handled as an explicit assumption.
- The prompt is already specific enough to enhance safely.
- The prompt is a one-line surgical edit with unambiguous intent.

If asking, dispatch **one** structured user-question call with **1–4 questions**; do not pad. Use the current runtime's structured user-question tool if available; otherwise use the prose fallback. See `references/ask-user-tools.md` for the runtime → tool lookup. See `references/planning-questions.md` for the canonical axis bank, "(Recommended)" selection rules, swap rules, and worked Round 1 / Round 2 examples.

Per question:
- **2–4 options**, mutually exclusive unless `multiSelect: true` is genuinely right (e.g., "which failure modes to block").
- **First option marked `(Recommended)`** based on the Step 1 diagnosis — not a static default.
- **Short labels** (1–5 words), one-line descriptions.
- **Do not manually add "Other"** — the runtime auto-adds it; see `references/ask-user-tools.md` if running on a runtime that differs.

### Step 2a — Round 2 (conditional, narrower)

After Round 1 answers come back, fire Round 2 **only if** an answer steered the enhancement into an axis Round 1 could not have anticipated, or the user chose "Other" with text introducing a new axis. Skip Round 2 when Round 1 cleared the picture or when tempted to "double-check" — just proceed.

Round 2 is **one** call with **1–3 focused questions**. Total question budget across both rounds: **≤7**. If the budget is blown, make a reasoned default and proceed with a note.

### Step 2b — Target-agent specificity

If the target agent is unknown, write the enhanced prompt in generic task language. If the user names Codex, Claude Code, Gemini, a local model, an API call, or another target, adapt only the necessary syntax and tool assumptions. Never mention unavailable tools.

### Step 3 — Apply the five enhancement layers

Apply the layers below. Read `references/enhancement-layers.md` for detailed worked examples per layer.

| Layer | Purpose | Read |
|---|---|---|
| 1. Narrative structure | Beginning–middle–end: situation → problem → done state | `references/enhancement-layers.md` |
| 2. Thinking steering | How to approach, not just what to do; framing; sequencing; wrong-framing block | `references/enhancement-layers.md` |
| 3. Failure pre-emption | Block the 2–3 most likely failure modes — pick from the catalogue | `references/failure-modes.md` |
| 4. Context injection (code-aware) | File paths, stack hints, non-obvious constraints — never repeat capabilities the agent has | `references/code-prompt-patterns.md` |
| 5. Verification + halt | Verification step + observable done signal + "if X, stop and ask" boundary | `references/enhancement-layers.md` (Layer 5) and `references/output-contract.md` |

**Layer 5 is mandatory on every output.** No enhanced prompt ships without all three: verification step, done signal, halt condition.

### Step 4 — Present the artifact

Use the response shape and prompt skeleton in `references/output-contract.md`. The default shape is:

````markdown
```text
<enhanced prompt>
```
Key improvement: <one sentence naming the main execution risk you blocked>
````

Offer deeper context, tighter scope, or research only when the user asks or the prompt's risk warrants it.

If the user says "run it" — execute the enhanced prompt directly. Reset framing completely.

## Effort calibration

| Input quality | Action |
|---|---|
| Already good (clear intent, specific, has constraints) | Light touch: add halt condition + verification only. Say "Added a done signal and verification step." |
| Decent intent, vague on details | Moderate: add narrative arc + failure pre-emption + halt |
| Raw idea or stream-of-consciousness | Full restructure: all 5 layers. Show the transformation. |

## Decision rules

- If the prompt is already excellent: say so, add only the halt condition, offer to run as-is.
- If the prompt is for a coding agent: assume filesystem access, skip explaining tools it has.
- If the prompt mentions a specific technology: don't research it unless accuracy is critical (e.g., API versions). The agent doing the work can look things up itself.
- If the prompt is a system / agent prompt (defines behavior, not requests a task): preserve "You are…" framing, add edge-case handling and escalation criteria.
- If the prompt risks scope creep, over-engineering, or silent degradation: see `references/failure-modes.md` and inject the matching pre-emption.

## Output contract — what every enhanced prompt must contain

| Element | Source / detail |
|---|---|
| Task outcome (explicit) | Step 3 Layer 1 + 2 |
| Scope boundary | Step 3 Layer 3; common scope fences in `references/code-prompt-patterns.md` |
| Failure-mode pre-emptions | `references/failure-modes.md` — pick the 2–3 most likely |
| Verification method (observable) | Type-shaped — see verification table in `references/output-contract.md` |
| Done signal (specific, observable) | Layer 5 — "you're done when …" |
| Halt condition (named ambiguity / blocker) | Layer 5 — "if X, stop and ask, do not guess" |

Full skeleton, code/non-code variants, verification-by-type table, assumption format, and prompt lint checklist live in `references/output-contract.md`.

## Anti-patterns

- Five-shot examples unless the user asks for them.
- "Agent writes its own prompt" meta-prompting.
- 26-principle dumps or academic prompt-engineering frameworks.
- More than 2 ask-user rounds, or more than 4 questions in a single round.
- Forcing Round 1 on a surgical one-liner — skip when Step 1 diagnosis is unambiguous.
- "Option A / B / C" filler labels — every option must be a meaningful choice the user can compare.
- Manually-added "Other" option — the runtime auto-provides it; see `references/ask-user-tools.md` if not.
- Rewriting the user's voice — enhance the content, preserve the tone.
- Spawning agents — this skill enhances a user message only.
- Padding the prompt with examples or policy dumps to look thorough — every word must earn its place.
- Skipping Layer 5 — verification, done, halt are mandatory on every output.

## Reference routing

| File | Read when |
|---|---|
| `references/ask-user-tools.md` | Step 2 decides to ask — pick the runtime's structured tool or prose fallback |
| `references/planning-questions.md` | Step 2 decides to ask — canonical axis bank, "(Recommended)" rules, swap rules, Round 1 / Round 2 examples |
| `references/enhancement-layers.md` | Step 3 — applying the 5 layers, with worked examples per layer |
| `references/failure-modes.md` | Step 3 Layer 3 — the catalogue of common agent failure modes and their pre-emptions |
| `references/code-prompt-patterns.md` | Step 3 Layer 4 — file-path anchors, scope fences, verification ladders, anti-pattern blocks for coding agents |
| `references/output-contract.md` | Step 4 — response shape, prompt skeleton, code / non-code variants, verification-by-type table, prompt lint checklist |

## Final test

Before returning the enhanced prompt, confirm:

- Task outcome is explicit.
- Scope boundary exists.
- Likely failure modes are blocked (named, not generic).
- Verification method is observable.
- Done signal is specific.
- Halt condition names the ambiguity or blocker.
- Word count is under the 1,200 / 2× cap unless the user asked for a full brief.
- The user's voice and intent are preserved.

If any answer is "no" or "fuzzy", fix it before returning. The prompt is the artifact; everything else is commentary.
