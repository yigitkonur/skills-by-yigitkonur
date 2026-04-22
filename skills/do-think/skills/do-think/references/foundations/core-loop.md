# Core Loop

The default `do-think` loop is:

1. **Frame the real question**
2. **Gather the minimum grounding set**
3. **Classify the task shape**
4. **Keep live options**
5. **Apply filters**
6. **Choose the next move**
7. **Verify or revise**

## 1. Frame the Real Question

State the question you are actually trying to answer.

Examples:
- `What is the real root cause of this failure?`
- `Which option is safest to ship?`
- `What is the smallest change that preserves behavior?`

If the question is fuzzy, the reasoning will sprawl.

## 2. Gather the Minimum Grounding Set

Collect only the evidence that can materially change the decision:
- current files, docs, commands, errors, or tests
- constraints from the user or repo docs
- observed behavior from the existing system

Do not read everything just to feel thorough.

## 3. Classify the Task Shape

Pick the dominant mode:
- build
- bug fix
- refactor
- architecture
- research
- review

The mode changes what evidence matters and what counts as success.

## 4. Keep Live Options

For medium or high complexity, keep 2-3 viable options or causes alive.

For each one, note:
- what must be true for it to win
- what currently supports it
- what would falsify it

## 5. Apply Filters

Before committing, run a short filter pass:
- reversibility
- simplicity
- coupling
- evidence quality
- verification

Use only the filters that change the decision.

## 6. Choose the Next Move

Choose one:
- implement
- probe for more evidence
- ask one clarifying question
- stop because the task is not ready

If more thinking would not change the next move, stop thinking.

## 7. Verify or Revise

Every chosen path needs:
- a verification check
- a revision trigger if the check fails

Thinking is done when the next move is clear and the check is defined.
