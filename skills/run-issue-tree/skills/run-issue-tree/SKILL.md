---
name: run-issue-tree
description: Use skill if you are planning or executing a GitHub Issue tree (epic, tracking issue, parent + sub-issues) with wave-based dispatch via gh CLI and runtime-native subagents.
---

# Run Issue Tree

Plan and execute wave-based GitHub Issue trees with parent + sub-issue nesting, label-driven state, agent-ready issue bodies, and runtime-native worker dispatch.

## When to use

Use this skill if you are:

- *planning a GitHub Issue tree from a spec, PRD, or epic — splitting it into parent + sub-issues with wave labels*
- *creating an "epic" or "tracking issue" with nested sub-issues and Blocked-by / Blocks dependencies*
- *executing an existing GitHub Issue tree wave-by-wave through `gh` and runtime-native subagent dispatch*
- *given a GitHub issue URL or number and asked to "run it", "execute the tree", or "work the next wave"*
- *decomposing work into `wave:0-foundation`, `wave:N`, `status:ready / in-progress / needs-review / failed` labels*
- *writing agent-ready issue bodies with BSV Definition of Done, ownership protocol, and explicit blockers*
- *transitioning closed leaf children up to a parent closure queue and verifying parent DoD*

Do **not** use this skill if you are:

- working in **Linear** rather than GitHub Issues — use `use-linear-cli` even when creating many issues from a spec
- running **direct parallel Codex agents** without a GitHub issue tree — use `use-codex`
- doing **generic planning** without GitHub issue creation, sub-issue linking, or wave labels
- doing **PR review** rather than issue execution — use `do-review`

`gh` manages GitHub issue state. Worker dispatch happens through the current runtime's native subagent/task tool, not through `gh`.

---

## Mode routing

| Condition | Mode |
|---|---|
| No issue tree exists yet | Plan Mode |
| Issue tree exists with open waves | Execute Mode |
| User says "plan", "decompose", or "design the tree" | Plan Mode |
| User says "run", "execute", "dispatch", or "work the next wave" | Execute Mode |
| User gives a GitHub issue URL or `#NUMBER` and asks to act on it | Execute Mode against that root |

If Execute Mode cannot find a tree and the user did not provide a root issue number, switch to Plan Mode.

---

## Hard rules (load-bearing)

These rules govern every Plan and Execute step. Violating any of them is a defect, not a tradeoff.

1. **Approval before mutation.** Never create labels, issues, or sub-issue links until the user approves the indented tree preview.
2. **Bottom-up creation.** Always create child issues before parents so sub-issue links can resolve at creation time.
3. **One wave + one type + one priority label per issue.** No exceptions. Read `references/label-schema.md`.
4. **Validate every issue body before creation.** Run `scripts/validate-issue-body.sh` against each body file before `gh issue create`.
5. **BSV Definition of Done is mandatory.** Every issue body must end with binary, scriptable, verifiable DoD criteria — no prose-only acceptance.
6. **Dispatch only ready leaves.** A ready leaf is open, has `type:task` or `type:subtask`, no open children, no open blockers, and no active status label. Parent issues enter the closure queue, never the dispatch queue.
7. **Never dispatch through `gh`.** Worker execution always goes through the current runtime's native subagent/task tool. `gh` only manipulates issue state.
8. **Never modify issue bodies during execution.** Add comments instead — bodies are the immutable contract.
9. **Never close an issue without verified DoD evidence.** If any criterion is unmet, label `status:failed`, comment unmet criteria, and wait for user-selected recovery.
10. **Never advance past a failed wave** without explicit user confirmation. Recompute state with `issue-tree-status.sh` between waves.
11. **Re-read state, do not cache.** Treat `issue-tree-status.sh` as the canonical source for ready / blocked / failed leaves before every dispatch decision.

---

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

---

## Available scripts

Scripts resolve relative to `SKILL_DIR`. Each `.sh.md` sibling is the human-readable contract for that script.

| Script | Mutates | Purpose |
|---|---:|---|
| `scripts/read-tree.sh` | no | Recursively prints the tree and verifies parent links. See `scripts/read-tree.sh.md`. |
| `scripts/link-sub-issue.sh` | yes | REST-first sub-issue linking (`X-GitHub-Api-Version: 2026-03-10`). See `scripts/link-sub-issue.sh.md`. |
| `scripts/setup-labels.sh` | yes | Creates wave / type / priority / status labels. See `scripts/setup-labels.sh.md`. |
| `scripts/issue-tree-status.sh` | no | Canonical status report for execution. See `scripts/issue-tree-status.sh.md`. |
| `scripts/dispatch-wave.sh` | optional | Writes dispatch manifest and prompt files; mutates only with `--mark-in-progress`. See `scripts/dispatch-wave.sh.md`. |
| `scripts/validate-issue-body.sh` | no | Validates body size, protocol sections, DoD quality, and references. See `scripts/validate-issue-body.sh.md`. |

---

## Plan Mode

### P1: Discover context

1. Detect the repo with `gh repo view`.
2. Scan open issues for conflicts or existing trees.
3. Briefly inspect README, package metadata, and entry points to scope the work.

### P2: Ask planning questions

Ask Q1–Q5 from `references/question-bank.md`. Add at most two optional follow-ups when the task type requires them.

If the user answers in prose, map the prose back to Q1–Q5 before planning. If the user does not answer, stop before designing or mutating anything. If the user says "proceed with assumptions", create a draft-only tree with explicit assumptions and still require approval before label or issue mutation.

### P3: Design the tree

1. Map waves; `wave:0-foundation` is always first, followed by the approved dynamic wave count.
2. Decompose maximally: epics → features → tasks → subtasks. If a description exceeds three sentences, split it. If a subtask would take more than one focused session, split it.
3. Map dependencies into `Blocked by`, `Blocks`, parent, and child relationships.
4. Assign exactly one wave label, one type label, and one priority label per issue. Read `references/label-schema.md`. Use `priority:critical` only for true blockers.
5. If two tasks have no dependency, put them in the same wave.

Present the indented tree and wait for explicit approval before creating labels or issues.

### P4: Create issues

Create issues bottom-up so children exist before parents. If labels are missing, get explicit approval and run `scripts/setup-labels.sh`; use `MAX_WAVE` for wave 6 or higher.

Before every `gh issue create`, write the body to a file and run:

```bash
bash "$SKILL_DIR/scripts/validate-issue-body.sh" /path/to/body.md --repo "$REPO"
```

Read `references/issue-body-template.md` and `references/body-size-validation.md`. Every body keeps the mandated ownership and completion protocol lines exactly as specified.

### P5: Wire relationships

Use `scripts/link-sub-issue.sh` for parent / child hierarchy. It uses the current REST endpoint, sends `X-GitHub-Api-Version: 2026-03-10`, fetches the child REST id first, and only sets `replace_parent` when explicitly requested.

Use `references/cross-linking-patterns.md` for bidirectional `Blocked by` / `Blocks` edits and verification.

### P6: Verify the created tree

```bash
bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_ISSUE_NUMBER
bash "$SKILL_DIR/scripts/issue-tree-status.sh" "$REPO" ROOT_ISSUE_NUMBER
```

Verify links, labels, parent reports, DoD sections, and unresolved assumptions before returning the plan result.

---

## Execute Mode

### E1: Read status

```bash
FULL=1 bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_NUMBER
bash "$SKILL_DIR/scripts/issue-tree-status.sh" "$REPO" ROOT_NUMBER
```

Treat `issue-tree-status.sh` as the canonical E2 status report and the final issue-tree status source.

### E2: Select work

Use this state machine. Re-reading GitHub state must be enough to reconstruct execution — never rely on cached intent.

| From | To | Condition |
|---|---|---|
| `open / no-status` | `status:ready` | Dependencies and children are clear |
| `status:ready` | `status:in-progress` | Dispatch starts |
| `status:in-progress` | `status:needs-review` | Human review is required |
| `status:in-progress` | `closed` | Every DoD criterion is verified |
| `status:in-progress` | `status:failed` | Criteria remain unmet |
| `status:failed` | `status:ready` | User selects recovery |
| parent with closed children | closure queue | Verify parent DoD; never dispatch as leaf work |

Dynamic waves come from the actual `wave:*` labels on issues — not hard-coded `wave 0–5` loops.

### E3: Prepare and dispatch

```bash
bash "$SKILL_DIR/scripts/dispatch-wave.sh" "$REPO" ROOT_NUMBER --limit CONCURRENCY
```

Use Q5 (concurrency cap) from the planning answers. The script writes `status.md`, `manifest.json`, and one prompt file per selected ready issue. Add `--mark-in-progress` only when dispatch is actually starting.

Dispatch the generated prompt files through the current runtime's native subagent/task tool. Read `references/subagent-dispatch.md` and `references/generic-prompt-patterns.md` before constructing prompts.

### E4: Verify completion

For each worker result:

1. Check every BSV criterion from the issue Definition of Done.
2. If all criteria are met: remove active status labels and close the issue with evidence.
3. If any criterion is unmet: label `status:failed`, comment with unmet criteria, and wait for user-selected recovery.

Use `references/subagent-dispatch.md` and `references/wave-execution.md` for exact closure and failure patterns.

### E5: Transition waves

When a wave closes, run `issue-tree-status.sh` again. Return:

- wave summary
- closure evidence
- next-wave readiness
- parent closure queue
- trailing failures

If partial failures remain, read `references/partial-wave-handling.md` and do **not** advance past a failed wave without explicit user confirmation.

---

## Output contracts

**Plan Mode returns:**

- approved tree preview
- created root issue
- issue count by type and wave
- label setup result
- sub-issue wiring verification
- unresolved assumptions

**Execute Mode returns:**

- root issue
- current wave
- per-wave counts
- ready leaf queue
- parent closure queue
- blocked list with blockers
- failed list with recovery status
- dispatched issue numbers
- next required decision

**Wave completion returns:**

- wave summary
- evidence of closed DoD
- next wave readiness
- trailing failures, if any

---

## Reference routing

Read references on demand — do not preload them all.

| File | When to read |
|---|---|
| `references/question-bank.md` | Plan Mode P2, before asking planning questions |
| `references/issue-body-template.md` | Plan Mode P4, before writing issue bodies |
| `references/label-schema.md` | Plan Mode P3 / P4, when applying labels |
| `references/body-size-validation.md` | Plan Mode P4, before validating or splitting bodies |
| `references/cross-linking-patterns.md` | Plan Mode P5, bidirectional dependency wiring |
| `references/wave-execution.md` | Execute Mode E2 / E4 / E5, state transitions and wave gates |
| `references/subagent-dispatch.md` | Execute Mode E3 / E4, prompt manifests and completion handling |
| `references/generic-prompt-patterns.md` | Execute Mode E3, tool-agnostic prompt writing |
| `references/partial-wave-handling.md` | Execute Mode E5, recovery from partial failures |

---

## Guardrails

**Planning:**

- Do not create issues or labels without approval of the plan tree.
- Do not skip Q1–Q5.
- Do not ship empty, vague, or oversized issue bodies.
- Do not leave sub-issue wiring unverified.
- Every issue body must have BSV Definition of Done criteria.
- Always create issues bottom-up.

**Execution:**

- Do not skip wave order.
- Do not treat `status:ready` as authoritative when blockers or children reopened — recompute with `issue-tree-status.sh`.
- Do not advance to the next wave while unresolved failures block it.
- Do not hand-write status loops when the status script can report the tree.
- Always read the full issue body, sub-issues, and recent comments before dispatching.
