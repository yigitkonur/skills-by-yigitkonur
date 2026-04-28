# Solo Deep-Think Mode

The default operating mode. The agent reasons alone — no user fork pauses — and produces a single artifact at the end (Minto-shaped output per `foundations/output-contract.md`).

Use Solo when:
- The user asked for an answer, not a discussion
- The user is not present or available to fork on
- The decision is not so high-stakes that it requires user co-authorship
- The agent has enough grounding to credibly classify, calibrate, and commit alone

Solo is the default. Switch to Interactive only when the triggers in SKILL.md fire.

## How Solo runs the core loop

The 4-phase loop in `foundations/core-loop.md` runs end-to-end without pause.

1. Emit the opening contract (`Mode: Solo  Cynefin: <domain>  Tier: <tier>`) on the first response line.
2. Phase A → B → C → D, internally. Each phase exit criterion must be satisfied before the next.
3. Emit the Solo output (Minto Pyramid — `foundations/output-contract.md`).

The user sees the *output*, not the full Phase A → D trace. Trace is internal.

## Discipline rules

1. **No silent skipping.** If you skip Phase A1 (Cynefin), the opening contract reveals it (no domain emitted = process broken). Same for Tier (Phase B1).
2. **No mid-loop user prompts.** If you find yourself wanting to ask the user a question, you have hit the escalation gate — switch to Interactive.
3. **Phase C2 trio is mandatory at Tier Medium/High.** Outputs are written, not implied. See `foundations/stress-test-trio.md`.
4. **Verification before action.** Phase D2 verification check is written before Phase D1 action is executed.
5. **Anti-stall.** If a phase is hard, do the smallest local move that changes certainty. See `references/workflows/continuous-execution.md`.

## Anti-stall — when Solo gets stuck

Solo is autonomous, but autonomy ≠ recklessness. Three legitimate stop conditions:

| Stop condition | Action |
|---|---|
| **Real external blocker** (missing credentials, unavailable system, requires destructive action with no rollback) | Stop, surface the blocker, ask the user the minimum question that unblocks |
| **All three options die in C2 stress-test** | Switch Mode to Interactive — the option space needs the user to expand it |
| **Tier was wrong — calibration matrix mis-fired** | Re-enter Phase B1, re-emit the opening contract |

Anything else: keep moving. See `workflows/continuous-execution.md` for the anti-stall discipline.

## Escalation triggers — when Solo should become Interactive

Mid-session, switch to Interactive if any of:

- Phase C2 stress-test kills all three options (escalation gate)
- The user's framing required Abstraction Laddering and the up-rung is meaningfully different — surface and confirm
- Tier escalates from Medium to High mid-session AND the new Tier requires a decision the user owns (e.g., "this is now a one-shot deploy")
- The decision requires expert knowledge the agent does not have access to

When switching, re-emit the opening contract with `Mode: Interactive`, then route to `modes/interactive-brainstorm.md`.

## What Solo output looks like

Per `foundations/output-contract.md` Minto Pyramid:

- First sentence = chosen path
- Body = 3-5 evidence-backed key arguments
- Last sentence = verification check

The opening contract line precedes the output. No fork pauses. No 10-section document.

## Solo for sub-types of work

| Task shape | Workflow file |
|---|---|
| Bug or regression | `workflows/bug-tracing.md` |
| Refactor or redesign | `workflows/refactor-thinking.md` |
| Recurring issue ("we already fixed this") | `workflows/recurring-issue.md` |
| Planning a complex task | `workflows/task-planning.md` |
| Staying autonomous through blockers | `workflows/continuous-execution.md` |

The workflow files are Solo-mode recipes. They specialize the 4-phase loop for common shapes.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Skipping the opening contract because "Solo is the default, why repeat it?" | The contract is the proof Phase A1 ran. Without it, the user has no evidence the classifier didn't get silently skipped. Always emit. |
| Defaulting to Solo on a question the user clearly wanted to discuss | Read the trigger phrases ("help me think", "walk through", "brainstorm"). If they fire, Solo is the wrong mode. |
| Producing a 10-section document in Solo mode | That's Interactive. Solo = Minto Pyramid. |
| Asking the user a clarifying question mid-Solo | If you need to ask, you've hit an escalation trigger — switch to Interactive. Don't blend modes. |
| Stopping at the first obstacle | Anti-stall discipline. See `workflows/continuous-execution.md`. |
