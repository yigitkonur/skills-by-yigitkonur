---
name: orchestrate-codex
description: Use skill if you are routing codex CLI work across five modes (exec fleet, batch template, single mission, branch review loop, rescue resume) under one manifest and one Monitor.
---

# Orchestrate Codex

Run multiple codex CLI workers under one manifest, one Monitor, one policy. The skill detects mode → seeds a manifest → spawns a detached runner → emits a Monitor hint → exits. Codex workers run in the background; the agent stays in the conversation; the manifest is the source of truth.

This skill is for codex-only orchestration. PRs go to `ask-review`. Bot-comment triage goes to `evaluate-code-review`. Cross-LLM batch fanout is out of scope.

## Trigger Boundary

Use this skill when the task matches one of:

- *parallel codex agents on ≥2 discrete coding tasks across separate worktrees, run as one fleet under one manifest*
- *one prompt template fanned out across N inputs (URLs, IDs, file paths) with one answer file per input*
- *one substantial codex mission the user wants to watch live via streamed JSONL events into Monitor*
- *a list of branches that need iterative `codex exec review` rounds with classifier-driven converged/blocked decisions*
- *a prior orchestrate-codex run that did not finish — resuming failed entries, never-started entries, or all non-done from the existing manifest*
- *any codex fleet that requires shared sandbox/model/effort policy, bounded concurrency, atomic manifest writes, and one Monitor surface*

Do NOT use this skill when:

- the work is one trivial codex invocation (≤5 minutes, no fleet, no monitor, no manifest needed). Run `codex exec` directly.
- a user references the deprecated install paths `run-codex-exec`, `run-codex-review`, or `run-batch-codex-research`. Those are shims that point here — load this skill and pick the matching mode (exec / review / batch). Do not restore their old bodies.
- the work is opening pull requests after a branch is ready. That is `ask-review`'s job; this skill never opens PRs.
- the work is consolidating third-party / human / bot review comments already posted on a PR. That is `evaluate-code-review`. This skill drives codex-only review.
- the work is generic batched LLM-CLI fanout against a non-codex backend, or multi-bot review evaluation across third-party reviewers. This skill is codex-only.

## Quickref — common operator phrasings → mode → invocation

Speed-read table. The dispatcher path is `<skill-root>/scripts/orchestrate-codex.mjs` — substitute the absolute install path. For the full decision tree, see Step 1 below.

| Operator says (intent) | Q-rule | Mode | Minimal invocation |
|---|---|---|---|
| *"resume / rescue / pick up where it left off / continue prior run"* | Q1 | rescue | `node <skill-root>/scripts/orchestrate-codex.mjs rescue --manifest <path>` |
| *"review these branches / ship-ready check / merge-ready for code-freeze"* | Q2 | review | `node <skill-root>/scripts/orchestrate-codex.mjs review --branches <list> [--base main]` |
| *"run this template across these inputs / fanout / research these vendors"* | Q3 | batch | `node <skill-root>/scripts/orchestrate-codex.mjs batch --inputs <file> --template <tmpl> [--answers-dir <dir>]` (`--template` is **required**, no default) |
| *"one big mission / watch live / watch the events / stream events / stream the output / monitor it"* | Q4 | single | `node <skill-root>/scripts/orchestrate-codex.mjs single --prompt-file <file>` (or `--prompt "..."`) |
| *"these N tasks in parallel" / "refactor X and rename Y"* (≥2 enumerated) | Q5 | exec | `node <skill-root>/scripts/orchestrate-codex.mjs exec --tasks <tasks.json>` |
| *"clean up the codebase / a bunch of stuff / help me with this"* (vague) | Q8 | ask | AskUserQuestion with one user-facing sentence per mode (compose from Trigger Boundary) |

Common decision flags:

| Need | Flag / env |
|---|---|
| Sibling manifest (parallel runs same workspace) | `--force-new-run --run-id <YYYYMMDDTHHMMZ>-<suffix>` (the `--run-id` is mandatory; `--force-new-run` alone is rejected) |
| Custom answers location (batch) | `--answers-dir <dir>` — round-trips through manifest; rescue redispatch honors it |
| Custom review base branch | `--base <branch>` (review mode; defaults to `main`). Override when the repo's default is `develop`/`trunk`/etc — silent wrong-base-diff is the failure mode otherwise. |
| Single-mode rescue with thread context | `--apply failed-only` on the rescue manifest; if `entry.codex_thread_id` is present, the runner is invoked with `codex exec resume <id>` automatically |
| Concurrency above mode default | `--concurrency N --i-have-measured "<TPM evidence>"`; refused without justification |
| Preview, don't run | `--dry-run` (works on every mode + rescue) |
| Skip codex auth gate (proxy / managed-companion / ephemeral CI) | `ORCHESTRATE_SKIP_CODEX_AUTH=1` (downgrades the bootstrap.sh login check to WARN) |
| Skip pre-flight entirely (dev/test) | `ORCHESTRATE_SKIP_CODEX_PREFLIGHT=1` (bypasses bootstrap.sh; only for harnesses) |
| Foreground / synchronous (test harness only) | `ORCHESTRATE_RUNNER_FOREGROUND=1` — runner runs synchronously; check `result.foreground_completed === true` to skip Monitor arming |

After the dispatcher returns, **the very next tool call is the Monitor invocation** — pass `envelope.monitor.tool_hint` through verbatim. Do not synthesize the Monitor block by hand.

## The five modes at a glance

| Mode | Spawn unit | Workspace | Loop shape | Success gate |
|---|---|---|---|---|
| exec | `codex exec` per task | `../<repo>-wt-exec-<slug>` per task | one-shot, auto-commit, exit | every entry done (commit + non-empty answer; post-verify is advisory, recorded as `mode_state.verify_status`, NOT a status gate — see `references/modes/exec.md`) or failed (surfaced) |
| batch | `codex exec` per input row | `<workdir>/answers/<id>.md` (no worktree) | bounded-concurrency runner, idempotent skip-existing | every input has non-empty answer + audit pass |
| single | one `codex exec --json` | selected cwd; `--reuse-worktree` records current-worktree reuse | one-shot streaming via filter | `-o` file non-empty + manifest entry `done` (`turn.completed` is a Monitor signal, not a gate) |
| review | one `codex exec review` per branch per round | `../<repo>-wt-review-<slug>` per branch | classifier-driven rounds, cap 10 | every branch in {converged, blocked, failed, cap_reached} |
| rescue | re-attach to an existing manifest | inherits prior mode's workspace | classify, then `--apply failed-only\|never-started-only\|all-non-done\|ids:...` (`--redo` is back-compat alias) | original mode's gate |

## Step 1 — Detect the mode

Run this decision tree against the user's prompt and the cwd state. The first match wins; no fall-through.

```
Q1. Does <manifest-path> exist AND does the prompt contain
    {"resume","continue","pick up","rescue","prior run"}?
        → mode = rescue, HIGH

Q2. Did the user name ≥1 branch (1 branch counts; routes to the same per-branch
    converge-or-cap loop) — single name, branches.txt, comma list, or git refs —
    AND does the prompt express ship-readiness intent? Tokens like
    {"review","ship","merge","close out"} are illustrative, not literal —
    match intent (e.g. "across the line before code-freeze" = ship,
    "make sure these are merge-ready" = merge-prep). Per-branch flow lives
    in `references/modes/review.md`.
        → mode = review, HIGH

Q3. Did the user supply (or name) an inputs file (inputs.txt / urls.txt / *.csv)
    AND a template file?
        → mode = batch, HIGH

Q4. Does the prompt contain {"single task","one big mission","watch live",
    "stream events","monitor it"} AND describe only one task?
        → mode = single, HIGH

Q5. Does the prompt list ≥2 discrete tasks AND is cwd a git repo?
    (discrete = enumerated/named tasks the user listed — bullets, numbered,
    or comma-separated. Vague plurals like "a bunch of stuff" or "clean up
    everything" do NOT count as discrete; they fall through to Q8.)
        → mode = exec, HIGH

Q6. Does the prompt name ≥2 branches/features/plan files
    (and Q2 didn't already fire on it)?
        → mode = exec, MEDIUM

Q7. Is the prompt one substantial coding task in a git repo, no list?
        → mode = single, MEDIUM

Q8. None of the above → ask once. Compose option descriptions from the
    Trigger Boundary bullets above — one user-facing sentence per mode
    (e.g. "exec — parallel codex agents on ≥2 discrete coding tasks across
    separate worktrees"). A 5-bare-word picker is unusable; the user needs
    to see what each mode does.
```

### Multi-mode prompts: when Q1-Q7 fire on disjoint clauses

> **Trigger.** The user's prompt encodes more than one mode at once on disjoint clauses. The first-match-wins rule above mis-routes here by silently dropping the unmatched clauses. One orchestrate-codex run is one mode — never pick one clause and ignore the rest.

**Example.** *"3 branches need review, 2 small refactors in parallel, 1 big refactor I want to watch live"* matches Q2 (review) + Q5 (exec) + Q4 (single) simultaneously.

**Action.**

1. Surface the breakdown to the user explicitly — one line per clause mapping it to a mode (e.g. `clause 1 (3 branches, ship-ready) → review`, `clause 2 (2 refactors, parallel) → exec`, `clause 3 (1 big refactor, watch live) → single`). Confirm before dispatching.
2. Dispatch order is `review` → `exec` → `single` → `batch`. Review first because its findings may shrink scope before code lands.
3. Concurrent invocations against the same workspace require `--force-new-run --run-id <custom>` per dispatch — the dispatcher refuses overlapping runs otherwise.
4. Sequential same-workspace runs without `--run-id` overwrite the prior manifest. Use distinct run-ids if any audit trail matters across the wave.

Rescue is its own track and only fires on Q1; it never participates in the multi-mode dispatch order. See `references/universal/manifest-contract.md` for run-id semantics.

### Confidence policy

After running Q1-Q8, the matched rule emits a confidence:

| Confidence | Action |
|---|---|
| HIGH | Dispatch the matched mode immediately. State the match in the mode-declaration step (see Output contract). |
| MEDIUM | If the surrounding prompt is unambiguous in your read, dispatch and state the MEDIUM stamp in the mode declaration ("matched Q5 (MEDIUM): treating these as discrete tasks because user enumerated them"). If ambiguous, ask once with the same option-composition rule as Q8. |
| LOW (no rule fired, Q8 path) | Ask once. Compose option descriptions from the Trigger Boundary bullets — one user-facing sentence per mode. The 5-bare-word picker is unusable. |

Examples of MEDIUM ambiguity:
- "I have 3 features I'm working on" — could be Q5 (3 discrete tasks → exec) or Q4 (one big mission → single). Ask if the user wants parallel-fleet or one-mission shape.
- "Check these branches" — could be Q2 (review-mode if shipping intent) or just a `git diff` ask. Ask for shipping/merge intent.

`<manifest-path>` resolution: `resolveStateDir(cwd)/orchestrate-codex/manifest.json`, where `resolveStateDir` is the vendored codex-cc algorithm: `$CLAUDE_PLUGIN_DATA/state/<slug>-<hash>` when set, otherwise `${TMPDIR:-/tmp}/codex-companion/<slug>-<hash>`. See `references/universal/manifest-contract.md` and `references/universal/plugin-data.md`.

If detection lands on MEDIUM confidence and the surrounding prompt is genuinely ambiguous, ask. Cheap to confirm; expensive to misroute.

## Step 2 — Universal pre-flight

Run before every mode. Stops the agent from improvising into a broken state.

1. `codex --version` succeeds. The skill assumes codex 0.130.0 or later for the verified `codex exec review` flags.
2. `codex login status` is a hard gate in `scripts/bootstrap.sh`: non-zero exit → bootstrap dies with exit 3 ("Run `codex login` before dispatching"). Escape hatch: `ORCHESTRATE_SKIP_CODEX_AUTH=1` downgrades the gate to a WARN — use this for ephemeral CI runners, bearer-token / managed-companion / proxy auth setups where `login status` reports "Not logged in" but spawns succeed anyway. If you bypass, verify auth another way before claiming pre-flight green. Note: only **review** runs `bootstrap.sh` at dispatch time (review spawns native `codex review` immediately, so deferring auth doesn't help); exec, batch, and single defer the auth check to the runner's own first codex spawn — same eventual error, but the failure surfaces from the runner's stderr, not the dispatcher's envelope. To force the dispatcher-level check on every mode, run `bash <skill-root>/scripts/bootstrap.sh` yourself before invoking the dispatcher.
3. cwd is resolved. If the chosen mode requires a git repo (exec, review), `git rev-parse --is-inside-work-tree` succeeds.
4. Workspace slug+hash computed (see manifest contract).
5. Manifest path resolved. If a manifest already exists with non-terminal entries, refuse cleanly with `error.code = "concurrent_run_in_progress"`. Two recovery paths: rescue mode (default — re-attach to the existing manifest), or `--force-new-run --run-id <custom>` (writes a parallel `manifest.<custom>.json` so the original run is left untouched). See `references/universal/idempotency.md`.
6. `.gitignore` (if you use in-repo worktrees via `WORKTREE_DIR_NAME=.worktrees`) covers the worktree path pattern. Default convention is OUT-of-repo worktrees (`<repo-parent>/<repo>-wt-*`), which need no `.gitignore` coverage.
7. Required scripts present: `<skill-root>/scripts/codex-flags.sh`, the per-mode runner, the helpers for the chosen mode.
8. `<skill-root>/scripts/codex-cc/` is present because the dispatcher imports its `lib/` helpers. Review mode does not require `gh`; it uses native `codex exec review`.

Per-mode preflight delta lives in `references/modes/<mode>.md`.

## Universal: sandbox + model + effort policy

Every codex spawn passes the same flag set. The flag set lives in `<skill-root>/scripts/codex-flags.sh` and is sourced — not duplicated — by every runner.

```
--dangerously-bypass-approvals-and-sandbox
--skip-git-repo-check
-m gpt-5.5
-c model_reasoning_effort=xhigh
```

Plus per-spawn additions: `--json` (JSONL events), `-o <file>` (final-message fallback when MCP active causes JSON dropout), `-C <dir>` (worktree as cwd).

Override per session via env vars `ORCHESTRATE_CODEX_MODEL`, `ORCHESTRATE_CODEX_EFFORT`. Overrides record in `manifest.policy.overrides` so rescue replays the same policy.

Forbidden: `--full-auto` (deprecated), `-a` other than `never`, `-s read-only`, `-s workspace-write`, `--ignore-rules`, `--ignore-user-config`. Read `references/universal/codex-flags.md` for the per-flag rationale.

## Universal: Monitor contract

**Always pass `envelope.monitor.tool_hint` through unchanged — do NOT compose the Monitor command by hand. The example below is illustrative; the dispatcher emits per-mode-correct commands (single uses `tail -F | codex-json-filter.sh`; batch uses `--tail-runner-log`; exec/review use `codex-monitor.sh`).**

One Monitor per fleet, not per worker. The dispatcher detaches the runner before returning the envelope, so the agent cannot literally pre-arm. Arm Monitor immediately on envelope receipt; first-wave loss is bounded by the runner-spawn-to-envelope-emit window (typically <100ms). Don't sleep, don't read other files, don't re-plan — the very next tool call after the dispatcher returns must be the Monitor invocation.

```
Monitor({
  description: "<mode> fleet (run_id=<id>)",
  command: "ORCHESTRATE_MANIFEST=<path> bash <skill-root>/scripts/codex-monitor.sh",
  persistent: true,
  timeout_ms: 300000
})
```

Single mode uses a different Monitor command — it tails the JSONL stream directly (`tail -F <jsonl> | bash <skill-root>/scripts/codex-json-filter.sh | awk '{print; fflush();}'`) instead of `codex-monitor.sh`. Do NOT compose the Monitor block by hand; the dispatcher emits the correct per-mode command verbatim in `envelope.monitor.tool_hint`. Pass it through unchanged. Per-mode commands documented in `references/universal/monitor-contract.md`.

Each runner emits one stdout line per state transition (`START <id>`, `DONE <id>`, `FAIL <id>`, `SKIP <id>`, terminal `--- all jobs finished ---`). Coverage rule: filter must match every terminal state including failure — silent monitor is indistinguishable from "still running." Pipes use `--line-buffered` in grep and `fflush()` in awk.

Stop the Monitor explicitly when the manifest reaches a terminal state. `tail -F` does not exit on its own. Read `references/universal/monitor-contract.md`.

## Universal: worktree contract

Naming: `<repo-parent>/<repo-basename>-wt-<mode>-<slug>`. The mode token in the path makes provenance obvious in `git worktree list`.

Created by `scripts/setup-worktree.sh`. Symlinks `node_modules` and `.env.local` from the source repo when present; runs `prisma generate` if a Prisma schema is found; runs whatever codegen the repo declares. Never created twice for the same task slug — re-running spawns a fresh worktree only if the manifest entry's `worktree_path` is gone.

If cwd is already inside a worktree and the chosen mode is `single`, do NOT create another — set `mode_state.reuse=true` and run codex inside the existing worktree. For exec / review, every entry gets its own worktree regardless of cwd.

Cleanup gate: `scripts/cleanup-worktrees.py --execute` removes worktrees whose entries are `done` AND whose branches are merged. Refuses dirty / unmerged / non-terminal-status (`running` or `queued`) worktrees unless `--force-abandon <id>`. Read `references/universal/worktree-contract.md`.

## Universal: manifest contract

Path: `resolveStateDir(cwd)/orchestrate-codex/manifest.json`, matching `scripts/codex-cc/lib/state.mjs`.

Workspace slug+hash matches codex-companion's `lib/state.mjs:resolveStateDir(cwd)` so this manifest sits next to codex-companion's `state.json` and `jobs/` records — rescue can correlate by codex thread ID. See `references/universal/codex-companion.md` for runtime correlation; `references/maintenance/codex-companion.md` and `references/maintenance/upstream-codex-cc.md` cover the vendored-subtree contract for maintainers.

Top-level fields: `schema_version, run_id, mode, started_at, base_commit, workspace_root, state_dir, policy, concurrency_cap, monitor_root, paths, preflight, entries[], history[]`. Entry status: `queued | running | done | failed | skipped | converged | blocked | cap_reached`. `run_id` = `<UTC ISO compact>-<4-hex-from-os.urandom>`.

Atomic write: `flock(<manifest>.lock)` + `tempfile.mkstemp(dir=parent)` + `os.replace(tmp, manifest)`. Concurrent writers serialize; readers do not block. The helper is `scripts/manifest-update.py`. Bash callers shell out; do not hand-roll.

Manifest is **deleted** on successful tidy. **Preserved** during rescue — history rows append. Hand-editing is forbidden; if the manifest is wrong, run `audit-fleet-state.py` (read-only diagnostic) and re-write via the helper. Read `references/universal/manifest-contract.md`.

## Universal: concurrency cap policy

| Mode | Default cap | Mechanism | Override |
|---|---|---|---|
| exec | 5 | `xargs -P 5` in `run-fleet.sh` | `JOBS=N` env or `--concurrency N` |
| batch | 10 | `xargs -P 10` in `run-batch.sh` | `--concurrency N` or `JOBS=N` env |
| single | 1 | n/a | n/a |
| review | 4 (per-branch parallel) | `xargs -P 4` in `run-review.sh` | `--concurrency N` or `JOBS=N` env |
| rescue | inherits original mode | manifest replay | `JOBS=N` env |

Soft gate: any `JOBS` above the mode default OR `JOBS > 20` (any mode) requires `--i-have-measured "<justification>"` and records the justification in `manifest.policy.overrides.concurrency` (the dispatcher's canonical write location). `JOBS > 100` is refused unconditionally at every layer. Read `references/universal/concurrency.md`.

**Both surfaces enforce identically.** The dispatcher refuses raised concurrency without `--i-have-measured "<reason>"`; the bash runners refuse the same with `ORCHESTRATE_CONCURRENCY_JUSTIFICATION` unset (or pass `--i-have-measured "<reason>"` when you invoke the runner directly). Either path exits 3 above 20 unless the justification is set; either path refuses unconditionally above 100. There is no "WARN-only" bypass; the previous wording was wrong. Always invoke through `node <skill-root>/scripts/orchestrate-codex.mjs <mode>` for the canonical envelope shape, but the safety rail is identical at both layers. Full mechanics in `references/universal/concurrency.md`.

## Universal: rehearsal and preview

`--dry-run` is the first-class preview path on every dispatcher mode (`exec`, `batch`, `single`, `review`, `rescue`). The dispatcher writes the manifest, spawns the runner with `--dry-run` propagated through, and the runner prints the planned `codex exec` invocation plus stub artifacts (`dry-run answer for <id>`, a stub JSONL turn) without invoking codex. Use it to inspect command shape, manifest layout, and Monitor output before committing to a real spawn.

Read-only / audit paths that never mutate or spawn anything: `audit-fleet-state.py`, `list-worktrees.py`, `cleanup-worktrees.py` (default; `--execute` to mutate), `audit-sizes.sh`, `manifest-update.py` (default; `--execute` to mutate), `rescue` mode without `--apply` (classify-only). Beyond these and `--dry-run`, the only other rehearsal surface is reading the mode references and the runner script source — there is no "preview just the prompt expansion" sub-command. Per-mode `--dry-run` semantics in `references/modes/exec.md`, `references/modes/batch.md`, `references/modes/single.md`, `references/modes/review.md`, `references/modes/rescue.md`.

## Universal: destructive-action gates

Every destructive action stops and asks. Bypass only when the orchestrator is invoked with `--non-interactive` AND a parent agent supplied that authorization.

- `git worktree remove --force <path>` → ask.
- `git branch -d` / `git push --delete` → ask.
- `kill -TERM/-KILL <pid>` against a tracked codex PID → ask. Confirm the PID belongs to this run via manifest before killing.
- Hand-edit of the manifest → ask. Route to `audit-fleet-state.py` first.

Skip-existing is never a destruction; the answer file already exists, the runner just doesn't overwrite. Idempotency is free — see `references/universal/idempotency.md`.

## Output contract

Surface these artifacts in order, each at the step that produces it — not batched at the end:

1. **Mode declaration** (after Step 1) — `exec` / `batch` / `single` / `review` / `rescue`, plus confidence (HIGH / MEDIUM) and one-line reasoning.
2. **Pre-flight summary** (after Step 2) — codex version, login status, manifest path resolved, slug+hash.
3. **Manifest seed report** (after dispatcher returns) — `result.manifest_path`, `result.run_id`, `result.entries_count`, `result.runner_pid`, `result.concurrency_cap`.
4. **Monitor invocation** (immediately on envelope receipt) — pass `envelope.monitor.tool_hint` through verbatim. Do not synthesize it.

> *`result.next_action` is shape-variant by phase:*
> - *Plain string (`"arm Monitor and wait"`) — phases `running` / `queued`. The very next tool call is the Monitor invocation.*
> - *Object (`{kind: "preview", reason, rerun_with}`) — phase `preview` (rescue dry-run). Surface the preview, then re-invoke without `--dry-run` if the operator approves.*
> - *Array of choice objects (`[{id, label, entry_ids}, ...]`) — phase `done` after rescue classification. Surface as `AskUserQuestion`, then dispatch with `--apply <chosen-id>`.*
> *Do not assume `.kind` exists on a string; do not assume an array is iterable as choices without checking the array form.*
> *Test/dev escape hatch: when `ORCHESTRATE_RUNNER_FOREGROUND=1` is set, the runner runs synchronously before the dispatcher returns. Check `result.foreground_completed === true` to short-circuit Monitor arming — the run is already terminal. Production agents always run detached; this field is harness-only.*

5. **Per-phase manifest reads during the run** — mode-appropriate (`audit-fleet-state.py` snapshots for fleet modes; live JSONL for single).
6. **Terminal status report** — every entry's terminal status; surface `failed` / `blocked` for human attention.
7. **Cleanup decision** (only after success gate fires) — `tidy --execute` only when every branch is merged.

## Mode router

**Dispatcher path:** Replace `<skill-root>` in every `node` invocation below with the absolute path to the installed skill (e.g. `~/.claude/skills/orchestrate-codex/skills/orchestrate-codex` or wherever `npx skills add` placed it). Confirm with `ls <skill-root>/scripts/orchestrate-codex.mjs`.

| Mode | Trigger (Q-rule) | Pre-checks | Read first | Dispatcher invocation | Success gate |
|---|---|---|---|---|---|
| exec | Q5 or Q6 (≥2 discrete coding tasks; git repo) | repo clean main; `.gitignore` covers `../<repo>-wt-*`; no in-progress merge/rebase/cherry-pick; baseline tests pass | `references/modes/exec.md`, `references/universal/worktree-contract.md`, `references/universal/monitor-contract.md`, `references/universal/json-streaming.md`, `references/templates/exec.tmpl.md` | `node <skill-root>/scripts/orchestrate-codex.mjs exec --tasks <tasks.json>` — seeds manifest, spawns `bash scripts/run-fleet.sh --manifest <path>` detached, emits envelope; surface literal `Monitor({...})` from `envelope.monitor.tool_hint` | every entry in {done, failed-surfaced}; Monitor sees `--- all jobs finished ---` |
| batch | Q3 (input list + template) | workdir confirmed; `inputs.txt` non-empty; `template.md` contains `XXXXXXXXXXXXX` placeholder; slug collisions resolved before render | `references/modes/batch.md`, `references/universal/idempotency.md`, `references/universal/monitor-contract.md`, `references/universal/output-size-signals.md`, `references/templates/batch.tmpl.md` | `node <skill-root>/scripts/orchestrate-codex.mjs batch --inputs <file> --template <tmpl>` — renders prompts, seeds manifest, spawns `bash scripts/run-batch.sh --manifest <path>` detached, emits envelope; audit runs after `--- all jobs finished ---` | every input has non-empty `answers/<slug>.md`; `audit-sizes.sh` shows nothing below floor (or every flagged item explicitly waived) |
| single | Q4 or Q7 (one substantial task) | choose cwd explicitly; if cwd is already inside a worktree, pass `--reuse-worktree` to record that choice | `references/modes/single.md`, `references/universal/json-streaming.md`, `references/universal/monitor-contract.md`, `references/templates/single.tmpl.md` | `node <skill-root>/scripts/orchestrate-codex.mjs single --prompt-file <file>` (or `--prompt "..."`) — one-entry manifest, spawns `bash scripts/run-single.sh` which pipes `codex exec --json` through `codex-json-filter.sh`; surface literal Monitor hint | `-o` file non-empty AND manifest entry `done` (`turn.completed` is a Monitor observability signal, not a runner gate) |
| review | Q2 (branch list + ship-intent) | git repo; branch list resolved from comma-list, file, or positionals; codex-cc `lib/` helpers resolvable | `references/modes/review.md`, `references/universal/manifest-contract.md`, `references/templates/review.tmpl.md` | `node <skill-root>/scripts/orchestrate-codex.mjs review --branches <list>` — seeds branch entries and dispatches **round 1 only** (`bash scripts/run-review.sh <manifest> 1`). After Monitor reports each round's `done`, the orchestrator (this agent) reads `<rounds-dir>/<slug>.r<N>.json`, runs `python3 classify-review-feedback.py`, decides converged/blocked/continue, and **manually re-invokes** `bash scripts/run-review.sh <manifest> 2` (then 3, …) until convergence or round-cap 10. **Multi-round automation: Planned — not yet wired** (see `references/modes/review.md:86`). | every branch in {converged, blocked, failed, cap_reached}; manifest entry has `last_findings_path` |
| rescue | Q1 (manifest exists + resume keyword) | manifest path resolved; freshness ≤ 7 days OR user confirms staleness; `manifest.mode` field present | `references/modes/rescue.md`, `references/universal/manifest-contract.md`, then the original mode's reference (whatever `manifest.mode` says) | `node <skill-root>/scripts/orchestrate-codex.mjs rescue [--manifest <path>]` classifies only; redispatch with `node <skill-root>/scripts/orchestrate-codex.mjs rescue --manifest <path> --apply failed-only\|never-started-only\|all-non-done\|ids:s1,s2,...` | every NOT-DONE entry transitions to a terminal status; manifest history append-only |

Failure routing for every mode: `references/universal/failure-modes.md` plus the per-mode reference's recovery section.

### Verifying success per mode

| Mode | Verify with |
|---|---|
| exec | `node <skill-root>/scripts/orchestrate-codex.mjs audit --manifest <path>` reports zero drift; every entry status terminal |
| batch | `audit` as above, plus `bash <skill-root>/scripts/audit-sizes.sh --manifest <path>` for below-floor outputs |
| single | `-o` answer file non-empty AND manifest entry `done`; no `audit` needed for single missions |
| review | `audit` as above; classifier output for each branch's `last_findings_json` shows zero majors OR cap reached |
| rescue | original mode's verify path applies after redispatch terminates |

### Mode-specific gotchas

- **exec — raw inputs.** If your prompts are raw description files (tickets, issue bodies, briefs) rather than pre-rendered templates, run `bash <skill-root>/scripts/render-task-prompts.sh <input-dir> <output-dir> --mode exec` first to wrap each file in the SUBAGENT-STOP prefix and 6-section skeleton. Otherwise codex may burn 20-80k tokens on meta-skill rumination before doing useful work. See `scripts/render-task-prompts.md`.
- **exec — audit-style.** Findings-only / audit-style tasks (no code changes expected) MUST instruct codex to `git add` and `git commit` the report file in the prompt's Success criteria — otherwise the success gate fails with `codex_exit_0_no_changes`. See `references/modes/exec.md` 'Audit-style' subsection.
- **exec — cleanup gate.** `tidy --execute` only fires after every entry is done AND every branch is merged. See the handoff lifecycle in `## Compatibility boundaries`.
- **single — raw inputs.** Same wrapping concern as exec; use `bash <skill-root>/scripts/render-task-prompts.sh <input-dir> <output-dir> --mode single` (the SUBAGENT-STOP prefix is auto-skipped for research / analysis / audit inputs).
- **single — terminal sentinel.** The live JSONL stream ends with `--- single done (<id>: <status>) ---` (an `orchestrate.done` event the runner appends after the terminal manifest write). TaskStop the Monitor on this line — no manual pgrep, no guessing at `[TURN<]`.
- **rescue — `--apply` semantics.** The dispatcher's envelope prints `--apply` in its `rerun_with` template; `--redo failed|never-started|all-non-done` is accepted as a back-compat alias and normalized into `--apply`. Pass `--accept-stale` only when replaying unknown/stale entries intentionally.

## Failure-mode taxonomy (universal)

Every mode triages failures through this 7-row table first. Per-mode extensions live in the mode reference. Full per-row remediation in `references/universal/failure-modes.md`.

| # | Failure | Trigger signal | First-line mitigation |
|---|---|---|---|
| 1 | rate-limit / 503 | `503 Service Unavailable` in JSONL or log | wait 15 min, redispatch failed only — never touch done entries |
| 2 | hung process | no progress event ≥ 25 min OR wrapper wall-clock cap hit | flip entry to `status=failed` with `last_error="hung_25min"` (the status enum has no hung-specific value), terminate codex PID after gate, surface for rescue |
| 3 | MCP-active JSON drop | events absent in `--json` while child alive | rely on `-o` file as truth; advisory `last_error="json_event_dropped"` |
| 4 | output truncation | answer file < `MIN` bytes after DONE event | flag in audit, do NOT auto-retry, surface for human inspect |
| 5 | worktree dirty unexpected | post-run `git status --short` non-empty in supposed-to-commit worktree | mark BLOCKED-DIRTY, do not auto-commit, surface |
| 6 | manifest collision | second writer cannot acquire `manifest.lock` within 30s | hard fail, do not corrupt; surface "another run is active" |
| 7 | state dir missing | `${CLAUDE_PLUGIN_DATA}` unset or state root unwritable | use codex-cc fallback under `${TMPDIR:-/tmp}/codex-companion`; if that fails, surface |

## Terminal output contract

| Mode | Required artifacts | Terminal manifest states |
|---|---|---|
| exec | per-entry prompt, log, answer, worktree path, auto-commit result | `done`, `failed`, `skipped` |
| batch | rendered prompts, answers, logs, runner log, `audit-sizes.txt` | `done`, `failed`, `skipped` |
| single | one prompt file, answer file, JSONL log | `done`, `failed` |
| review | per-round findings, JSONL, classifier output | `converged`, `blocked`, `failed`, `cap_reached` |
| rescue | classification JSON in envelope, append-only history rows, selected redispatch ids | inherits original mode |

## Compatibility boundaries

The deprecated codex trio (`run-codex-exec`, `run-codex-review`, `run-batch-codex-research`) are install-path shims pointing here. Preserve their install paths; do not restore their old bodies; route every match into this skill's matching mode.

Use `run-repo-cleanup` after exec/review fleets leave dirty branches, stale worktrees, unpushed commits, or foundation-to-leaf cleanup ordering. Use `ask-review` only for PR handoff. `orchestrate-codex` never opens PRs.

Slash-command boundary: vendored `/codex:review` and codex-companion review remain in `scripts/codex-cc/` but are not used by this skill. Review mode uses `codex exec review`; per-item local review uses `do-review`; external/human/bot feedback consolidation uses `evaluate-code-review`; PR creation uses `ask-review`. There is no `/codex:resc` contract in this skill.

The old third-party bot-wait timing constants from `run-codex-review` are retired. This skill does codex-only review. For third-party bot waits, route to `evaluate-code-review` or a future dedicated skill.

### Handoff to ask-review

`orchestrate-codex` produces branches; `ask-review` produces PRs. The lifecycle is documented but not automated — the orchestrator drives it explicitly:

1. **Finish first.** Wait for the manifest's success gate (every entry in a terminal state) before any handoff.
2. **Confirm done.** Run `node <skill-root>/scripts/orchestrate-codex.mjs audit --manifest <path>` and verify zero drift. A worktree-missing or dirty-worktree drift means the entry is not handoff-ready.
3. **Per-entry handoff loop.** For each `done` entry in the manifest, ask-review needs three fields lifted directly from the entry: `branch` (the commit target), `base_branch` (the merge target — usually `main`), `worktree_path` (where the work landed). The natural pattern is `cd <entry.worktree_path>` and invoke ask-review from inside the worktree so its git-aware probes operate on the correct ref. Loop one entry at a time; do not parallelize the handoff (`ask-review` interacts with GitHub auth that does not parallelize cleanly).
4. **Wait for merges out-of-band.** ask-review opens the PR and exits. Reviews, CI runs, and merges happen asynchronously. The orchestrate-codex side is idle during this window — do not call `tidy` yet.
5. **Tidy only after merges land.** `node <skill-root>/scripts/orchestrate-codex.mjs tidy --execute` (or the underlying `cleanup-worktrees.py --execute`) refuses to remove a worktree whose branch is not merged. Run tidy only after every entry's branch has merged and you have confirmed via `gh pr list --state merged` (or equivalent). Tidy with unmerged branches will exit with `unmerged_branches` errors — that is the safety rail, not a bug.

Key invariant: ask-review never touches the manifest. The manifest stays the source of truth for the orchestrate-codex side; ask-review's PR records live in GitHub. Tidy is the bridge that closes both sides — and it requires the GitHub side to have advanced to "merged" before it will collect the worktree.

## Anti-patterns

For worked examples of each, read `references/universal/anti-patterns.md`.

- Never replace `--dangerously-bypass-approvals-and-sandbox`. The skill assumes bypass; downgrades silently change semantics.
  **Cost:** `workspace-write` blocks on non-write ops (network, exec) → codex hangs → runner sees no progress → rescue redispatches into same hang. The skill is built on bypass; downgrades change semantics silently.
- Never raise `JOBS` past mode default without `--i-have-measured` AND a logged justification in `manifest.policy.overrides.concurrency`.
  **Cost:** rate-limit cascade, queue starvation across other Anthropic sessions on the same auth tier, and the dispatcher can't tell whether the operator measured or guessed.
- Never use `/tmp/...` as the manifest path of record. Cross-session collisions are silent. Never hand-edit the manifest. Use `audit-fleet-state.py` to inspect and `manifest-update.py` to mutate.
  **Cost:** breaks `flock` invariant; concurrent writers corrupt entries; rescue can't classify safely; audit reports false drift.
- Never invent a `codex review` invocation other than the native CLI. Review uses `codex exec review` with the documented flags.
  **Cost:** loses classifier input shape (markdown vs JSON sidecar), no manifest entry, no Monitor wiring; review-mode loop machinery doesn't apply; bypasses the round-cap soft gate.
- Never silently overwrite a `done` manifest entry. Skip-existing is the only acceptable behavior.
  **Cost:** flips a verified terminal entry back to `queued`, double-spends API budget, may overwrite the answer file before its consumer (audit, ask-review) reads it.
- Never run unbounded concurrency (`xargs -P 0`, naked `&` fan-out). Cap is mode-specific.
- Never auto-merge to `main` / `canary` / default branch. Merging is operator-driven.
- Never skip Monitor arming order. Tail readers miss first-wave events when armed late.
- Never delete a worktree with uncommitted changes without explicit user gate.
- Never overwrite an answer file in batch mode. Archive to `answers/.prev/`, then re-run.
- Never drop `CODEX_FLAGS` inside an `xargs bash -c` subshell. The subshell forgets the user's zsh function wrappers.
- Never bundle Claude Code hooks. This is a skill, not a plugin — separation by design.

Full cost-counter expansions for every anti-pattern: `references/universal/anti-patterns.md`.

## Prompt authoring discipline

When the dispatcher does not render the prompt for you (custom exec missions, custom single missions, hand-written review mission briefs), follow `references/universal/prompt-discipline.md` for the Intent / Discovery / Constraints / Success / Out-of-scope / Failure-protocol skeleton.

## References

Read on entry — universal contracts:

- `references/universal/manifest-contract.md` — full manifest schema, atomic-write recipe, recovery, migration.
- `references/universal/codex-flags.md` — every codex CLI flag the skill touches with rationale + per-flag edge cases.
- `references/universal/monitor-contract.md` — awk/grep recipes per mode, `fflush()` rule, coverage rule, arm-before-runner, lifecycle.
- `references/universal/worktree-contract.md` — naming, lifecycle, reuse rules, dirty-state gates, recovery from interrupted state.
- `references/universal/concurrency.md` — per-mode cap rationale, how to measure before raising, the `--i-have-measured` gate.
- `references/universal/idempotency.md` — skip-existing guards across modes, archive-before-retry, explicit requeue rules.
- `references/universal/failure-modes.md` — per-row remediation for every taxonomy entry plus per-mode extensions.
- `references/universal/errors.md` — every `error.code` the dispatcher emits, with exit code, first-line recovery, and deep-dive cross-link.
- `references/universal/json-streaming.md` — JSONL event types codex emits, filter recipes, MCP-active fallback to `-o`.
- `references/universal/output-size-signals.md` — bottom-decile rule, absolute floor, when small ≠ bad.
- `references/universal/plugin-data.md` — `${CLAUDE_PLUGIN_DATA}` resolution, the state directory pruning policy.
- `references/universal/prompt-discipline.md` — mission-brief skeleton and prompt smell tests.
- `references/universal/anti-patterns.md` — the catalog above expanded with worked examples.
- `references/universal/codex-companion.md` — runtime correlation surface for rescue: codex-companion job records, manifest-correlation, forensics calls.

Maintenance (rare; not runtime — read only when bumping the vendored codex-plugin-cc tree):

- `references/maintenance/codex-companion.md` — vendored subtree library tour, dispatcher imports, why we don't drive review/exec/batch through codex-companion.
- `references/maintenance/upstream-codex-cc.md` — how to bump the vendored codex-plugin-cc, reapply the patch, what to watch for.

Read on routing — per-mode recipes:

- `references/modes/exec.md` — parallel codex exec across worktrees: tasks.json schema, prompt template, auto-commit + post-verify, recovery.
- `references/modes/batch.md` — template × N batch: input formats, slug rules, archive-before-retry, audit thresholds.
- `references/modes/single.md` — one mission with live stream: cwd-vs-worktree decision, JSONL filter setup.
- `references/modes/review.md` — per-branch convergence: round mechanics, classifier policy, evaluator/apply flow, terminal states.
- `references/modes/rescue.md` — resume: manifest read, classification table, redo decision matrix, edge cases.

Templates (loaded by dispatcher; read when authoring custom prompts):

- `references/templates/exec.tmpl.md` — exec-mode prompt template (SUBAGENT-STOP prefix preserved).
- `references/templates/batch.tmpl.md` — batch-mode prompt template (placeholder + structure).
- `references/templates/single.tmpl.md` — single-mission prompt template.
- `references/templates/review.tmpl.md` — codex review invocation template.

Cross-reference index of every reference and which mode pulls it: `references/index.md`.

## Scripts

| Script | Mode | Purpose |
|---|---|---|
| `scripts/orchestrate-codex.mjs <subcommand>` | all | top-level dispatcher; emits JSON envelope. Subcommands: `exec`, `batch`, `single`, `review`, `rescue` (mode handlers); `audit` (read-only manifest+filesystem state dump); `tidy` (dry-run-default cleanup of completed worktrees and merged branches; pair with `--execute` to apply — wraps `cleanup-worktrees.py`). |
| `scripts/codex-flags.sh` | all | sourced helper exporting `CODEX_FLAGS` and `CODEX_REVIEW_FLAGS` |
| `scripts/bootstrap.sh` | all | one-shot pre-flight |
| `scripts/setup-worktree.sh` | exec, review | create worktree, link artifacts, codegen |
| `scripts/render-prompts.sh` | batch, exec | template substitution |
| `scripts/render-task-prompts.sh` | exec, single | wrap raw description files (Linear tickets, issue bodies, audit briefs) in SUBAGENT-STOP prefix + 6-section skeleton; see `scripts/render-task-prompts.md` |
| `scripts/run-fleet.sh` | exec | bounded-concurrency exec runner |
| `scripts/run-batch.sh` | batch | bounded-concurrency batch runner |
| `scripts/run-single.sh` | single | one-shot wrapper with JSONL filter pipe |
| `scripts/run-review.sh` | review | per-branch round driver via native `codex exec review` |
| `scripts/codex-monitor.sh` | all | rule-engine fleet ticker, manifest-aware |
| `scripts/codex-json-filter.sh` | exec, single | JSONL → Monitor lines |
| `scripts/audit-sizes.sh` | batch | output-size auditor (bottom-decile + below-floor) |
| `scripts/audit-fleet-state.py` | all | read-only manifest+filesystem state dump |
| `scripts/list-worktrees.py` | all | read-only worktree enumeration |
| `scripts/cleanup-worktrees.py` | all | safe worktree removal with manifest cross-check |
| `scripts/manifest-update.py` | all | atomic manifest field setter (Python; flock + os.replace) |
| `scripts/manifest-update.sh` | all | atomic manifest field setter (bash; flock + jq + mv) — bash runners use this; dispatcher uses Python |
| `scripts/classify-review-feedback.py` | review | major-vs-minor classifier |
| `scripts/apply-review-decisions.py` | review | read-only apply-queue printer (main agent applies via Edit) |
| `scripts/rescue-detect.py` | rescue | classify entries done/failed/never_started/in_flight/unknown |
| `scripts/codex-cc/` | all | vendored OpenAI codex-plugin-cc tree (see `references/maintenance/upstream-codex-cc.md`) |
| `scripts/test-runner-contracts.mjs` | test | dispatcher/runner dry-run contract fixtures for all modes |

## Known limitations

These are gaps the skill does not paper over. Hit the workaround; don't reinvent the dispatcher.

- **Review prompt-injection / intensity dial.** `handleReview` valueOptions accept neither `--prompt-file` nor `--focus`; `run-review.sh` invokes `codex exec review` with hardcoded flags + `--base` and no positional prompt; `mode_state.task.prompt` is unread; `round_focus` is informational only. So no custom spec doc, no "hostile / adversarial" intensity dial, no focus bias through the dispatcher. Why: codex's own `review` subcommand takes a narrow flag set and the skill does not shell out to `codex-companion adversarial-review`. Workaround: drop to single mode per branch (`single --prompt-file <hostile-brief.md>`) — see `references/modes/review.md` "Custom-prompt injection". Trades classifier+round-loop for full prompt control.
- **`setup-worktree.sh` symlinks are Node-only and link exactly one env file.** Only `node_modules` and one env file (`LINK_ENV_FILE`, default `.env.local`) are linked + optional `prisma generate`. To link a different env file, set `LINK_ENV_FILE=.env.development` (or whichever); to link more than one, fork the script — the loop only iterates a single path. No detection or affordance for Unity (`Library/`, `Assets/`), Xcode (`DerivedData/`), Gradle (`.gradle/`, `build/`), Rust (`target/`), or embedded toolchain configs. Why: ecosystem detection is open-ended; the skill stays narrow rather than ship half-detection. Workaround: pre-create the worktree manually and hand-symlink heavy artifacts before exec/review, OR fork `setup-worktree.sh` for your stack and override via `WORKTREE_SETUP_HOOK`.
- **Multi-Claude-session auth-tier sharing.** The skill assumes one Claude / orchestrate-codex session per Anthropic auth tier; persistent rate-limits often mean another session is consuming the budget. Why: tier-share state is invisible from inside any single CLI session. Workaround: pause the other sessions, OR coordinate dispatch order, OR halve concurrency on rescue redispatch (`--concurrency N --i-have-measured "post-503; tier shared"`). See `references/universal/failure-modes.md` rate-limit row.
- **Manifest sibling enumeration is operator-managed.** `audit` and `rescue` default to `manifest.json` only; with sibling `manifest.<run-id>.json` files (from `--force-new-run`), the operator must remember every custom run-id out-of-band — there is no `audit --all` or `audit --list-manifests`. Why: enumeration adds dispatcher complexity without a clean answer for which sibling is "current". Workaround: keep an external log of run-ids, OR `ls "$(<state-dir>)/manifest"*.json` to enumerate. See `references/universal/idempotency.md` sibling discoverability paragraph.
- **Exec success-gate requires ≥1 commit; audit-style tasks must commit their report.** Exec mode's gate is "≥1 new commit on the worktree's branch since baseline". Findings-only tasks (audit reports, code reviews) trip `codex_exit_0_no_changes` unless the prompt instructs codex to write the report file AND `git commit` it. Why: the gate detects code-mission failures (rumination loops, no-op exits) and cannot distinguish "produced no work" from "produced a report I forgot to commit". Workaround: prefer single mode for audit-style work (gate is non-empty `-o`, no commit). For exec-mode audit fleets, end the prompt with the canonical commit instruction at `references/modes/exec.md` "Audit-style / findings-only tasks".
- **`--apply ids:` bypasses status filters; batch mode is asymmetric.** `rescue --apply ids:s1,s2,s3` is operator-by-name and ignores status; for **exec/single/review**, a `done` entry named in `ids:` flips to `queued` and redispatches. For **batch**, the runner's filesystem-keyed skip-existing (the answer file is still on disk) demotes the entry to `skipped` instead of redispatching codex — flipping `status` is not enough. To actually re-run a `done` batch entry, use `--force-redo <slug>` (which atomically archives the answer to `answers/.prev/` AND flips status), not `--apply ids:<slug>`. Status-filter subsets (`failed-only` / `never-started-only` / `all-non-done`) apply only to the named variants regardless of mode. Why: exec's idempotency lives in git history, batch's lives on disk; the dispatcher's archive-then-flip is the correct move for batch. See `references/modes/rescue.md`.
- **`attempts` increments by +2 per `--force-redo` cycle.** Each force-redo bumps `attempts` twice (queued-flip, then runner START); operator may misread the counter for cycle count. Why: two-phase manifest write — the dispatcher queues, the runner starts, both write. Workaround: divide `attempts` by 2 for cycle count, OR consult `history[]` rows for an authoritative cycle log.

## Bottom line

Detect mode → run pre-flight → write manifest → spawn the runner detached → emit envelope with Monitor hint → exit. The skill never blocks. Every spawn carries the same flag set. Every failure routes through the taxonomy. Every destructive action is gated. Every rescue starts from a manifest, not a memory.
