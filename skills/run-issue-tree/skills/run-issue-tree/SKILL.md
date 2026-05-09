---
name: run-issue-tree
description: Use skill if you are planning or executing GitHub-only issue trees with sub-issues, wave/status labels, gh CLI orchestration, and runtime-native subagent dispatch.
---

# Run Issue Tree

Plan and execute wave-based GitHub Issue trees with sub-issue nesting, label-driven state, agent-ready issue bodies, and runtime-native worker dispatch.

## Trigger Boundary

Use this skill for GitHub Issues only:

- planning a GitHub Issue tree with sub-issues, waves, labels, and issue-body prompts
- executing an existing GitHub Issue tree wave by wave
- preparing ready issue prompts for the current runtime's native subagent/task tool

Do not use this skill for:

- Linear work; use `use-linear-cli`, even when creating many issues from a spec
- direct parallel Codex-agent fleets that do not need a GitHub issue tree; use `orchestrate-codex`
- generic planning without GitHub issue creation
- PR review; use `do-review`

`gh` manages GitHub issue state. Worker dispatch happens through the current runtime's native subagent/task tool, not through `gh`.

## Mode Routing

| Condition | Mode |
|---|---|
| No issue tree exists yet | Plan Mode |
| Issue tree exists with open waves | Execute Mode |
| User says "plan" explicitly | Plan Mode |
| User says "run" or "execute" explicitly | Execute Mode |

If Execute Mode cannot find a tree and the user did not provide a root issue number, switch to Plan Mode.

## Prerequisites

```bash
gh auth status
command -v jq >/dev/null
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
SKILL_DIR="/absolute/path/to/run-issue-tree"  # directory containing this SKILL.md
test -d "$SKILL_DIR/scripts"
```

`SKILL_DIR` is the directory containing this `SKILL.md`; installed skills do not assume the target repo contains helper scripts. Always pass `--repo "$REPO"` to direct `gh issue` commands.

For Execute Mode, verify the tree exists:

```bash
bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_NUMBER
```

## Available Scripts

Scripts resolve relative to `SKILL_DIR`.

| Script | Mutates | Purpose |
|---|---:|---|
| `scripts/read-tree.sh` | no | Recursively prints the tree and verifies parent links. See `scripts/read-tree.sh.md`. |
| `scripts/link-sub-issue.sh` | yes | REST-first sub-issue linking. See `scripts/link-sub-issue.sh.md`. |
| `scripts/setup-labels.sh` | yes | Creates wave/type/priority/status labels. See `scripts/setup-labels.sh.md`. |
| `scripts/issue-tree-status.sh` | no | Canonical status report for execution. See `scripts/issue-tree-status.sh.md`. |
| `scripts/dispatch-wave.sh` | optional | Writes dispatch manifest and prompt files; mutates only with `--mark-in-progress`. See `scripts/dispatch-wave.sh.md`. |
| `scripts/validate-issue-body.sh` | no | Validates issue body size, protocol sections, DoD quality, and references. See `scripts/validate-issue-body.sh.md`. |

## Plan Mode

### P1: Discover Context

1. Detect repo with `gh repo view`.
2. Scan open issues for conflicts or existing trees.
3. Briefly inspect README, package metadata, and entry points.

### P2: Ask Planning Questions

Ask Q1-Q5 from `references/question-bank.md`. Add at most two optional follow-ups when the task type requires them.

If the user answers in prose, map the prose back to Q1-Q5 before planning. If the user does not answer, stop before designing or mutating anything. If the user says to proceed with assumptions, create a draft-only tree with explicit assumptions and still require approval before label or issue mutation.

### P3: Design The Tree

1. Map waves; `wave:0-foundation` is always first, followed by the approved dynamic wave count.
2. Decompose maximally: epics, features, tasks, subtasks.
3. Map dependencies into `Blocked by`, `Blocks`, parent, and child relationships.
4. Assign one wave label, one type label, and one priority label per issue. Read `references/label-schema.md`.

Present the indented tree and wait for explicit approval before creating labels or issues.

### P4: Create Issues

Create issues bottom-up so children exist before parents. If labels are missing, get explicit approval, then run `scripts/setup-labels.sh`; use `MAX_WAVE` for wave 6 or higher.

Before every `gh issue create`, write the body to a file and run:

```bash
bash "$SKILL_DIR/scripts/validate-issue-body.sh" /path/to/body.md --repo "$REPO"
```

Read `references/issue-body-template.md` and `references/body-size-validation.md`. Every body keeps the mandated ownership and completion protocol lines exactly.

### P5: Wire Relationships

Use `scripts/link-sub-issue.sh` for parent/child hierarchy. It uses the current REST endpoint, sends `X-GitHub-Api-Version: 2026-03-10`, fetches the child REST id first, and only sets `replace_parent` when explicitly requested.

Use `references/cross-linking-patterns.md` for bidirectional `Blocked by` and `Blocks` edits and verification.

### P6: Verify Created Tree

Run:

```bash
bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_ISSUE_NUMBER
bash "$SKILL_DIR/scripts/issue-tree-status.sh" "$REPO" ROOT_ISSUE_NUMBER
```

Verify links, labels, parent reports, DoD sections, and unresolved assumptions before returning the plan result.

## Execute Mode

### E1: Read Status

Run:

```bash
FULL=1 bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_NUMBER
bash "$SKILL_DIR/scripts/issue-tree-status.sh" "$REPO" ROOT_NUMBER
```

Treat `issue-tree-status.sh` as the canonical E2 status report and final issue-tree status source.

### E2: Select Work

Use the state machine below. Re-reading GitHub state must be enough to reconstruct execution.

| From | To | Condition |
|---|---|---|
| `open/no-status` | `status:ready` | Dependencies and children are clear |
| `status:ready` | `status:in-progress` | Dispatch starts |
| `status:in-progress` | `status:needs-review` | Human review is required |
| `status:in-progress` | `closed` | Every DoD criterion is verified |
| `status:in-progress` | `status:failed` | Criteria remain unmet |
| `status:failed` | `status:ready` | User selects recovery |
| parent with closed children | closure queue | Verify parent DoD; do not dispatch as leaf work |

Ready leaf issues are open `type:task` or `type:subtask` issues with no open children, no open blockers, and no active status label. Dynamic waves come from actual `wave:*` labels, not hard-coded wave 0-5 loops.

### E3: Prepare And Dispatch

Run:

```bash
bash "$SKILL_DIR/scripts/dispatch-wave.sh" "$REPO" ROOT_NUMBER --limit CONCURRENCY
```

Use Q5 to choose the concurrency cap. The script writes `status.md`, `manifest.json`, and one prompt file per selected ready issue. Add `--mark-in-progress` only when dispatch is actually starting.

Dispatch the generated prompt files through the current runtime's native subagent/task tool. Read `references/subagent-dispatch.md` and `references/generic-prompt-patterns.md`.

### E4: Verify Completion

For each worker result:

1. Check every BSV criterion from the issue Definition of Done.
2. If all criteria are met, remove active status labels and close with evidence.
3. If any criterion is unmet, label `status:failed`, comment with unmet criteria, and wait for user-selected recovery.

Use `references/subagent-dispatch.md` and `references/wave-execution.md` for exact closure and failure patterns.

### E5: Transition Waves

When a wave closes, run `issue-tree-status.sh` again. Return the wave summary, closure evidence, next-wave readiness, parent closure queue, and trailing failures. If partial failures remain, read `references/partial-wave-handling.md` and do not advance past a failed wave without user confirmation.

## Output Contract

Plan Mode returns:

- approved tree preview
- created root issue
- issue count by type and wave
- label setup result
- sub-issue wiring verification
- unresolved assumptions

Execute Mode returns:

- root issue
- current wave
- per-wave counts
- ready leaf queue
- parent closure queue
- blocked list with blockers
- failed list with recovery status
- dispatched issue numbers
- next required decision

Wave completion returns:

- wave summary
- evidence of closed DoD
- next wave readiness
- trailing failures, if any

## Decision Rules

### Planning

- If a task description exceeds three sentences, decompose it.
- If two tasks have no dependency, put them in the same wave.
- If a subtask would take more than one focused session, split it.
- Use `priority:critical` only for true blockers.

### Execution

- Dispatch only ready leaf issues; parent issues enter closure verification.
- Never dispatch through `gh`; use the runtime-native task/subagent tool.
- Never modify issue bodies during execution; add comments instead.
- Never close an issue unless every DoD criterion is verified with evidence.
- Never retry failed issues without user-selected recovery.
- Prefer parallel dispatch only within the current wave and concurrency cap.

## Reference Routing

| File | When to read |
|---|---|
| `references/question-bank.md` | Plan Mode P2, before asking planning questions |
| `references/issue-body-template.md` | Plan Mode P4, before writing issue bodies |
| `references/label-schema.md` | Plan Mode P3/P4, when applying labels |
| `references/body-size-validation.md` | Plan Mode P4, before validating or splitting bodies |
| `references/cross-linking-patterns.md` | Plan Mode P5, bidirectional dependency wiring |
| `references/wave-execution.md` | Execute Mode E2/E4/E5, state transitions and wave gates |
| `references/subagent-dispatch.md` | Execute Mode E3/E4, prompt manifests and completion handling |
| `references/generic-prompt-patterns.md` | Execute Mode E3, tool-agnostic prompt writing |
| `references/partial-wave-handling.md` | Execute Mode E5, recovery from partial failures |

## Guardrails

### Planning

- Do not create issues or labels without approval of the plan tree.
- Do not skip Q1-Q5.
- Do not create empty, vague, or oversized issue bodies.
- Do not leave sub-issue wiring unverified.
- Every issue body must have BSV Definition of Done criteria.
- Always create issues bottom-up.

### Execution

- Do not skip wave order.
- Do not treat `status:ready` as authoritative when blockers or children reopened; recompute with `issue-tree-status.sh`.
- Do not advance to the next wave while unresolved failures block it.
- Do not hand-write status loops when the status script can report the tree.
- Always read full issue body, sub-issues, and recent comments before dispatching.
