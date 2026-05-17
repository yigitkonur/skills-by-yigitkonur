---
name: run-codex-exec
description: Use skill if you are landed on the deprecated run-codex-exec install path and need parallel codex exec agents in git worktrees with auto-commit and live monitor.
---

# run-codex-exec

This is a deprecated compatibility shim. **Do not restore the old implementation here.** The active runtime is `run-codex-2` exec mode. This skill exists so that users who installed the old path or who reach for the old verb still get routed to the right place.

## When to use this skill

Trigger when the user is asking for the exec-mode workload, regardless of whether they name the skill:

- *"run codex exec across these tasks in parallel worktrees"*
- *"spawn N codex agents, one per task, each in its own git worktree, auto-commit when done"*
- *"parallel codex exec fleet with a live monitor and per-worktree commits"*
- *"give me run-codex-exec for tasks A, B, C"*
- *"use codex exec on tasks.json"*
- *"fan out codex agents across a tasks list, each agent in a worktree, watch progress live"*

## Do NOT use this skill when

- *The user wants one prompt template applied to N inputs (URLs, IDs, file paths) with one answer file per input* → use **`run-batch-codex-research`** (also a shim) → routes to `run-codex-2` **batch** mode. No worktrees, no auto-commit; idempotent skip-existing.
- *The user wants per-branch codex review convergence loops with classifier-driven rounds* → use **`run-codex-review`** (also a shim) → routes to `run-codex-2` **review** mode. Branch list, not task list; review surface, not coding tasks.
- *The user is already on the active orchestrator and wants the full mode-detect tree (exec / batch / single / review / rescue)* → load **`run-codex-2`** directly. This skill is the install-path stub for the exec mode only.

## What "exec mode" means

The shape this skill represents:

| Aspect | Value |
|---|---|
| Spawn unit | `codex exec` per task |
| Workspace | `../<repo>-wt-exec-<slug>` per task (one git worktree per agent) |
| Loop shape | one-shot per task; auto-commit on done; exit |
| Concurrency | bounded (`xargs -P 5` default; raisable with `--i-have-measured`) |
| Observability | one Monitor per fleet, armed BEFORE the runner spawns |
| Success gate | every entry in {done, failed-surfaced}; Monitor sees `--- all jobs finished ---` |
| State of record | manifest at `resolveStateDir(cwd)/run-codex-2/manifest.json` |

If the user's request matches that shape, route to `run-codex-2` exec mode below.

## How to route

1. Confirm the shape is exec mode (≥2 discrete coding tasks, git repo, parallel desired, auto-commit acceptable).
2. Load the active skill: `skills/run-codex-2/skills/run-codex-2/SKILL.md`.
3. Run the dispatcher with the exec subcommand:

```bash
node skills/run-codex-2/skills/run-codex-2/scripts/run-codex-2.mjs exec --tasks <tasks.json>
```

The dispatcher writes the seed manifest, spawns `bash scripts/run-fleet.sh --manifest <path>` detached, and emits the Monitor hint envelope. Surface the literal `Monitor({...})` hint to the user before exiting.

## Key contracts to read in `run-codex-2`

The active skill owns the contracts. Read them there, not here.

- **Mode recipe:** `skills/run-codex-2/skills/run-codex-2/references/modes/exec.md` — tasks.json schema, prompt template, auto-commit + post-verify, recovery
- **Worktree contract:** `skills/run-codex-2/skills/run-codex-2/references/universal/worktree-contract.md` — naming `<repo>-wt-exec-<slug>`, lifecycle, dirty-state gates, reuse rules
- **Monitor contract:** `skills/run-codex-2/skills/run-codex-2/references/universal/monitor-contract.md` — one Monitor per fleet, arm before runner, coverage rule, lifecycle
- **Manifest contract:** `skills/run-codex-2/skills/run-codex-2/references/universal/manifest-contract.md` — atomic writes, run_id, state dir resolution, rescue correlation
- **Codex flag set:** `skills/run-codex-2/skills/run-codex-2/references/universal/codex-flags.md` — every CLI flag every spawn passes; what is forbidden
- **Concurrency policy:** `skills/run-codex-2/skills/run-codex-2/references/universal/concurrency.md` — default cap 5 for exec; how to measure before raising
- **JSON streaming:** `skills/run-codex-2/skills/run-codex-2/references/universal/json-streaming.md` — JSONL events, MCP-active fallback to `-o`
- **Failure modes:** `skills/run-codex-2/skills/run-codex-2/references/universal/failure-modes.md` — per-row remediation; rate-limit, hung process, JSON drop, output truncation, dirty worktree
- **Prompt template:** `skills/run-codex-2/skills/run-codex-2/references/templates/exec.tmpl.md` — SUBAGENT-STOP prefix preserved
- **Idempotency:** `skills/run-codex-2/skills/run-codex-2/references/universal/idempotency.md` — skip-existing rules; how to requeue

## Anti-patterns specific to exec mode

These reappear most often when users land here from the old install path. Reject them on sight; the active skill enforces them.

- **Never** spawn `codex exec` directly in a loop without the manifest + Monitor wrapper. Lose state on first failure.
- **Never** create a single shared worktree for the fleet. Each task gets its own; concurrent commits otherwise corrupt history.
- **Never** auto-merge a worker's branch into `main` / `canary` / default. Merging is operator-driven; this skill stops at per-worktree commit.
- **Never** run unbounded concurrency (`xargs -P 0`, naked `&` fan-out). Cap is 5 by default.
- **Never** raise `JOBS` past 5 without `--i-have-measured "<justification>"` recorded in `manifest.policy.overrides.concurrency`.
- **Never** arm the Monitor after the runner spawns. Late arming misses first-wave events; failures look silent.
- **Never** delete a worktree with uncommitted changes without an explicit gate. Use `scripts/cleanup-worktrees.py --execute`.
- **Never** hand-edit the manifest. Inspect with `audit-fleet-state.py`; mutate via `manifest-update.{py,sh}`.

## Migration from the old `run-codex-exec`

Old standalone scripts and old install paths from this skill's previous body have been retired. The exec-mode workflow now lives entirely under `run-codex-2`. The install path `skills/run-codex-exec` is preserved so existing automation does not break, but every active piece of logic is in the orchestrator. Treat any reference to `run-codex-exec`'s old internals as a migration detail, not a public contract.

## Bottom line

This shim's job is to recognize the exec-mode request, refuse to grow back into a parallel implementation, and route the agent to `run-codex-2` exec mode with the correct dispatcher invocation. One redirect, no orphaned state.
