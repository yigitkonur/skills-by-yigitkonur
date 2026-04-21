# Planning Questions — Round 1 Axis Bank

Round 1 of `enhance-prompt` dispatches a single `AskUserQuestion` call with up to **4 questions** (tool cap) covering the axes most likely to change the final enhancement. This file is the canonical bank; swap axes when the prompt warrants.

## The four canonical axes

For a typical non-trivial prompt, Round 1 picks 3-4 of these. If an axis is irrelevant, drop it — do not pad to hit 4.

### Axis 1 — Outcome type

> What's the primary outcome you need from this prompt?

| Option | Description |
|---|---|
| Working code | Agent produces runnable code that solves the task |
| Plan or strategy | Agent produces a plan to be executed later |
| Understanding / explanation | Agent explains a concept, walks through a system, maps the landscape |
| Research summary | Agent gathers external info and synthesizes |

Mark "(Recommended)" based on Step 1 diagnosis:
- Step 1 said "this is a coding task with a clear done state" → Recommended = Working code
- Step 1 said "the user is exploring" → Recommended = Understanding
- Step 1 said "multi-step with unclear sequencing" → Recommended = Plan or strategy

### Axis 2 — Enhancement depth

> How aggressive should the enhancement be?

| Option | Description |
|---|---|
| Light touch | Add halt condition + verification only; prompt is already clear |
| Moderate | Add narrative arc + failure pre-emption + halt |
| Full restructure | Apply all 5 layers; show the transformation |

Mark "(Recommended)":
- Prompt is 1-3 sentences and already specific → Recommended = Light touch
- Prompt has intent but lacks structure → Recommended = Moderate
- Raw / stream-of-consciousness / vague → Recommended = Full restructure

### Axis 3 — Verification style

> How should the agent confirm the work is done?

| Option | Description |
|---|---|
| Run tests | Agent runs the test suite and confirms green |
| Smoke-test manually | Agent demonstrates the happy path end-to-end |
| Self-describe the fix | Agent explains why the change is correct with file:line evidence |
| Visual / screenshot | Agent produces a screenshot or demo |

Mark "(Recommended)":
- Code task, test suite exists in the repo → Recommended = Run tests
- Code task, no tests → Recommended = Smoke-test manually
- Diagnostic / debugging → Recommended = Self-describe the fix
- UI / frontend → Recommended = Visual / screenshot

### Axis 4 — Failure modes to block (multi-select)

> Which failure modes should the enhanced prompt block most aggressively? Pick all that apply.

| Option | Description |
|---|---|
| Scope creep | Agent refactors surrounding code, adds abstractions not asked for |
| Assumption cascade | Agent builds on a wrong initial assumption |
| Silent degradation | Agent gives up on the hard part and produces partial work |
| Over-engineering | Agent adds flexibility, config, or abstractions not requested |

Set `multiSelect: true` — failure modes co-occur.

Mark "(Recommended)" on the highest-likelihood modes per prompt type:
- Refactor / fix task → Recommended = Scope creep, Over-engineering
- "Add feature X" prompt → Recommended = Over-engineering
- Hard / ambiguous task → Recommended = Silent degradation, Assumption cascade
- Multi-step exploration → Recommended = Assumption cascade

## When to swap an axis

The four canonical axes cover most prompts. Swap one for a prompt-specific axis when the canonical set misses the decision that would change the enhancement.

Common swap candidates:

| Candidate axis | Use when | Sample question |
|---|---|---|
| Target agent | Prompt might go to Claude Code, Codex, an API call, Gemini, etc. | "Which agent will consume this prompt?" |
| Context scope | Prompt mentions files but is vague on which | "Which files should the agent focus on?" |
| Boundary | Change could be file / module / system level | "What's the scope boundary for this work?" |
| Blast radius | Prompt could affect shared systems (prod, shared infra) | "Should the agent act directly, or produce a plan for your approval?" |
| Existing-code sensitivity | Codebase has strong conventions the prompt doesn't surface | "Should the agent strictly match existing patterns or propose improvements?" |

Never swap just to vary the question set — swap only when the canonical axis is genuinely orthogonal to this prompt's decision space.

## Picking the "(Recommended)" option per question

The "(Recommended)" marker reflects your Step 1 diagnosis, not a static default. If you don't know which option to recommend, your Step 1 diagnosis was thin — read the prompt again before asking.

Concrete rules:

- Always mark exactly **one** option per question as Recommended (unless multiSelect, where you can mark up to 2)
- The Recommended option goes **first** in the list
- Append `(Recommended)` to the label — e.g., `Working code (Recommended)`
- If genuinely uncertain between two, prefer the less aggressive / lower-blast-radius option

## Round 1 example — code task

User prompt: *"Make the login page faster, it's slow."*

**Step 1 diagnosis**: vague (what's "slow"? what metric?), code-related (frontend), no verification criterion stated, no scope boundary.

**Round 1 AskUserQuestion call** (4 bundled questions):

```
Questions:

1. Outcome type:
   - Plan of attack (Recommended) — measure first, then decide what to change
   - Working code — jump straight to a fix
   - Research summary — gather benchmark data only

2. Enhancement depth:
   - Moderate (Recommended) — add narrative, failure pre-emption, halt
   - Full restructure — all 5 layers
   - Light touch — only halt + verification

3. Verification style:
   - Before/after timing with Lighthouse (Recommended)
   - Run existing tests
   - Smoke test in browser
   - Visual comparison screenshot

4. Failure modes to block (multi-select):
   - Scope creep (Recommended)
   - Over-engineering (Recommended)
   - Silent degradation
   - Assumption cascade
```

After the user answers, Step 3 applies the enhancement with the picked axes.

## Round 2 example — conditional follow-up

Round 1 answers came back:
- Outcome: **Plan of attack** (not code directly)
- Depth: Moderate
- Verification: Before/after Lighthouse
- Failure modes: Scope creep, Over-engineering

**New axis emerged**: user picked "Plan of attack" → now the enhancement must produce *a plan*, not *working code*. Plan-shaping is an axis Round 1 didn't cover.

**Round 2 AskUserQuestion call** (1 question, targeted):

```
Question:

1. Plan shape:
   - Step-by-step execution sequence (Recommended)
   - Tradeoff analysis of 2-3 approaches
   - Prioritized backlog of improvements
```

Total budget used across rounds: 5 questions. Under the ≤ 7 cap. Proceed to Step 3.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Ask 4 questions on every prompt | For 1-2 sentence surgical prompts, skip Round 1 entirely |
| Ask questions whose answers don't change the enhancement | Only ask if Step 3 would branch on the answer |
| Always mark Option 1 as Recommended regardless of diagnosis | Recommended reflects the Step 1 diagnosis; if you can't pick, your diagnosis is thin |
| Pad out to 4 questions when 2 would do | 2 focused questions > 4 diluted ones |
| Generic "Option A / Option B / Option C" labels | Labels must be meaningful; the user is comparing them at a glance |
| Include a manual "Just go with your best judgment" option | The tool auto-adds "Other" — the user can type there |
| Fire Round 2 to validate Round 1 answers | Round 2 fires only for newly-emerged axes, not double-checks |
| Round 2 with 4 questions (same size as Round 1) | Round 2 caps at 3 focused questions; if you need 4, it's really a Round 1 you should have run |
| Forget to set `multiSelect: true` on the failure-modes question | Failure modes co-occur; single-select there is wrong |
