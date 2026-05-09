---
name: orchestrate-codex
description: Use skill if you are orchestrating codex CLI for parallel worktree fleets, batched template runs, single-mission monitoring, per-branch review loops, or resuming a partial prior run.
---

# Orchestrate Codex

The skill orchestrates. Codex executes. One entry point, five modes. Detect mode → run pre-flight → spawn → emit Monitor hint → exit. The agent that loaded this skill stays in the conversation; the codex workers run in the background; the manifest is the source of truth for state.

## When to reach for this skill

Reach for it when the user wants to drive the codex CLI in any of these shapes:

- **Multiple discrete coding tasks** that touch disjoint files and are worth running in parallel worktrees.
- **One prompt template applied to N inputs** (URLs, IDs, file paths) where every output lands as a separate file.
- **One large mission** that benefits from a live event stream so the user can watch progress without hand-holding.
- **A branch list to converge** through codex's review surface, with classifier + main-agent decisioning.
- **A prior orchestrate-codex run that didn't finish** and needs failures redone or never-started entries dispatched.

Do not reach for this skill when:

- The work is one trivial codex invocation (≤ 5 minutes, no monitor needed). Type `codex exec` directly.
- The work is opening pull requests. That is `ask-review`'s job.
- The work is multi-bot review evaluation across third-party reviewers. This skill drives codex review only.
- The work is generic batched LLM-CLI fanout against a non-codex backend. This skill is codex-only.

## The five modes at a glance

| Mode | Spawn unit | Workspace | Loop shape | Success gate |
|---|---|---|---|---|
| exec | `codex exec` per task | `../<repo>-wt-exec-<slug>` per task | one-shot, auto-commit, exit | every entry done (commit + non-empty answer + post-verify pass) or failed (surfaced) |
| batch | `codex exec` per input row | `<workdir>/answers/<id>.md` (no worktree) | bounded-concurrency runner, idempotent skip-existing | every input has non-empty answer + audit pass |
| single | one `codex exec --json` | selected cwd; `--reuse-worktree` records current-worktree reuse | one-shot streaming via filter | `turn.completed` event seen + `-o` file non-empty |
| review | one `codex exec review` per branch per round | `../<repo>-wt-review-<slug>` per branch | classifier-driven rounds, cap 10 | every branch in {converged, blocked, failed, cap_reached} |
| rescue | re-attach to an existing manifest | inherits prior mode's workspace | classify, then `--redo failed|never-started|all-non-done` | original mode's gate |

## Step 1 — Detect the mode

Run this decision tree against the user's prompt and the cwd state. The first match wins; no fall-through.

```
Q1. Does <manifest-path> exist AND does the prompt contain
    {"resume","continue","pick up","rescue","prior run"}?
        → mode = rescue, HIGH

Q2. Did the user supply a branch list (named, branches.txt, or ≥2 git refs)
    AND does the prompt contain {"review","ship","merge","close out"}?
        → mode = review, HIGH

Q3. Did the user supply (or name) an inputs file (inputs.txt / urls.txt / *.csv)
    AND a template file?
        → mode = batch, HIGH

Q4. Does the prompt contain {"single task","one big mission","watch live",
    "stream events","monitor it"} AND describe only one task?
        → mode = single, HIGH

Q5. Does the prompt list ≥2 discrete tasks AND is cwd a git repo?
        → mode = exec, HIGH

Q6. Does the prompt name ≥2 branches/features/plan files
    (and Q2 didn't already fire on it)?
        → mode = exec, MEDIUM

Q7. Is the prompt one substantial coding task in a git repo, no list?
        → mode = single, MEDIUM

Q8. None of the above → ask once using request_user_input("Pick orchestration mode",
    options: exec / batch / single / review / rescue).
```

`<manifest-path>` resolution: `resolveStateDir(cwd)/orchestrate-codex/manifest.json`, where `resolveStateDir` is the vendored codex-cc algorithm: `$CLAUDE_PLUGIN_DATA/state/<slug>-<hash>` when set, otherwise `${TMPDIR:-/tmp}/codex-companion/<slug>-<hash>`. See `references/universal/manifest-contract.md`.

If detection lands on MEDIUM confidence and the surrounding prompt is genuinely ambiguous, ask. Cheap to confirm; expensive to misroute.

## Step 2 — Universal pre-flight

Run before every mode. Stops the agent from improvising into a broken state.

1. `codex --version` succeeds. The skill assumes codex 0.130.0 or later for the verified `codex exec review` flags.
2. `codex login status` exits 0 (authed). If not, surface and stop.
3. cwd is resolved. If the chosen mode requires a git repo (exec, review), `git rev-parse --is-inside-work-tree` succeeds.
4. Workspace slug+hash computed (see manifest contract).
5. Manifest path resolved. If a manifest already exists with non-terminal entries, refuse cleanly with `error.code = "concurrent_run_in_progress"`. Use rescue, not a force-new run, to replay partial work.
6. `.gitignore` (if a git repo) covers the worktree path pattern (`../<repo>-wt-*`) and any in-repo state files.
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

One Monitor per fleet, not per worker. Arm Monitor BEFORE launching the runner — late-arming Monitors miss first-wave events.

```
Monitor({
  description: "<mode> fleet (run_id=<id>)",
  command: "ORCHESTRATE_MANIFEST=<path> bash <skill-root>/scripts/codex-monitor.sh",
  persistent: true,
  timeout_ms: 300000
})
```

Each runner emits one stdout line per state transition (`START <id>`, `DONE <id>`, `FAIL <id>`, `SKIP <id>`, terminal `--- all jobs finished ---`). Coverage rule: filter must match every terminal state including failure — silent monitor is indistinguishable from "still running." Pipes use `--line-buffered` in grep and `fflush()` in awk.

Stop the Monitor explicitly when the manifest reaches a terminal state. `tail -F` does not exit on its own. Read `references/universal/monitor-contract.md`.

## Universal: worktree contract

Naming: `<repo-parent>/<repo-basename>-wt-<mode>-<slug>`. The mode token in the path makes provenance obvious in `git worktree list`.

Created by `scripts/setup-worktree.sh`. Symlinks `node_modules` and `.env.local` from the source repo when present; runs `prisma generate` if a Prisma schema is found; runs whatever codegen the repo declares. Never created twice for the same task slug — re-running spawns a fresh worktree only if the manifest entry's `worktree_path` is gone.

If cwd is already inside a worktree and the chosen mode is `single`, do NOT create another — set `mode_state.reuse=true` and run codex inside the existing worktree. For exec / review, every entry gets its own worktree regardless of cwd.

Cleanup gate: `scripts/cleanup-worktrees.py --execute` removes worktrees whose entries are `done` AND whose branches are merged. Refuses dirty/unmerged worktrees unless `--force-abandon <id>`. Read `references/universal/worktree-contract.md`.

## Universal: manifest contract

Path: `resolveStateDir(cwd)/orchestrate-codex/manifest.json`, matching `scripts/codex-cc/lib/state.mjs`.

Workspace slug+hash matches codex-companion's `lib/state.mjs:resolveStateDir(cwd)` so this manifest sits next to codex-companion's `state.json` and `jobs/` records — rescue can correlate by codex thread ID.

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

Soft gate: `JOBS > 20` (any mode) requires `--i-have-measured <justification>` and records the justification in `manifest.policy.overrides.concurrency`. `JOBS > 100` is refused at dispatcher and runner boundaries. Read `references/universal/concurrency.md`.

## Universal: destructive-action gates

Every destructive action stops and asks. Bypass only when the orchestrator is invoked with `--non-interactive` AND a parent agent supplied that authorization.

- `git worktree remove --force <path>` → ask.
- `git branch -d` / `git push --delete` → ask.
- `kill -TERM/-KILL <pid>` against a tracked codex PID → ask. Confirm the PID belongs to this run via manifest before killing.
- Hand-edit of the manifest → ask. Route to `audit-fleet-state.py` first.

Skip-existing is never a destruction; the answer file already exists, the runner just doesn't overwrite. Idempotency is free.

## Mode router

Each block is the router contract: trigger → pre-checks → read first → run → success gate → failure routing. Six lines, identical shape across modes so the agent scans all five in one pass.

### exec mode — parallel codex agents in worktrees

- **Trigger:** Q5 or Q6 (≥2 discrete coding tasks; git repo).
- **Pre-checks:** repo clean main; `.gitignore` covers `../<repo>-wt-exec-*`; no in-progress merge / rebase / cherry-pick; baseline tests pass.
- **Read first:** `references/modes/exec.md`, `references/universal/worktree-contract.md`, `references/universal/monitor-contract.md`, `references/universal/json-streaming.md`.
- **Run:** `node scripts/orchestrate-codex.mjs exec --tasks <tasks.json>`. The dispatcher writes the seed manifest, spawns `bash scripts/run-fleet.sh --manifest <path>` detached, emits the JSON envelope. Surface the literal `Monitor({...})` from `envelope.monitor.tool_hint`.
- **Success gate:** every entry in {done, failed-surfaced}; Monitor sees `--- all jobs finished ---`.
- **Failure routing:** `references/universal/failure-modes.md` + `references/modes/exec.md` §recovery.

### batch mode — template × N inputs, no worktrees

- **Trigger:** Q3 (input list + template).
- **Pre-checks:** workdir confirmed; `inputs.txt` non-empty; `template.md` contains the `XXXXXXXXXXXXX` placeholder; slug collisions resolved before render.
- **Read first:** `references/modes/batch.md`, `references/universal/idempotency.md`, `references/universal/monitor-contract.md`, `references/universal/output-size-signals.md`.
- **Run:** `node scripts/orchestrate-codex.mjs batch --inputs <file> --template <tmpl>`. The dispatcher renders prompts, writes the manifest, spawns `bash scripts/run-batch.sh --manifest <path>` detached, emits the envelope. Audit runs after `--- all jobs finished ---`.
- **Success gate:** every input has a non-empty `answers/<slug>.md`; `audit-sizes.sh` shows nothing below floor (or every flagged item explicitly waived).
- **Failure routing:** `references/universal/failure-modes.md` + `references/modes/batch.md` §retry.

### single mode — one big mission with live stream

- **Trigger:** Q4 or Q7 (one substantial task).
- **Pre-checks:** choose cwd explicitly; if cwd is already inside a worktree, pass `--reuse-worktree` to record that choice.
- **Read first:** `references/modes/single.md`, `references/universal/json-streaming.md`, `references/universal/monitor-contract.md`.
- **Run:** `node scripts/orchestrate-codex.mjs single --prompt-file <file>` (or `--prompt "..."`). The dispatcher writes a one-entry manifest, spawns `bash scripts/run-single.sh` which pipes `codex exec --json` through `codex-json-filter.sh`. Surface the literal Monitor hint.
- **Success gate:** `turn.completed` event observed AND `-o` file non-empty AND manifest entry `done`.
- **Failure routing:** `references/universal/failure-modes.md` + `references/modes/single.md` §recovery.

### review mode — per-branch convergence loop

- **Trigger:** Q2 (branch list + review keyword).
- **Pre-checks:** git repo; branch list resolved from comma-list, file, or positionals; codex-cc `lib/` helpers resolvable.
- **Read first:** `references/modes/review.md`, `references/universal/manifest-contract.md`, `references/templates/review.tmpl.md`.
- **Run:** `node scripts/orchestrate-codex.mjs review --branches <list>`. The dispatcher seeds branch entries, then `run-review.sh` iterates rounds: native `codex exec review --base <base> --json -o <findings.md>` per branch, then `classify-review-feedback.py`. If zero major: `converged`. If major or ambiguous: `blocked` with findings/classification paths for main-agent evaluation. Round cap 10.
- **Success gate:** every branch in {converged, blocked, failed, cap_reached}; manifest entry has `last_findings_path`.
- **Failure routing:** `references/universal/failure-modes.md` + `references/modes/review.md` §loops.

### rescue mode — resume an interrupted run

- **Trigger:** Q1 (manifest exists + resume keyword).
- **Pre-checks:** manifest path resolved; freshness ≤ 7 days OR user confirms staleness; `manifest.mode` field present.
- **Read first:** `references/modes/rescue.md`, `references/universal/manifest-contract.md`, then the original mode's reference (whatever `manifest.mode` says).
- **Run:** `node scripts/orchestrate-codex.mjs rescue [--manifest <path>]` classifies only. Redispatch with `node scripts/orchestrate-codex.mjs rescue --manifest <path> --redo failed|never-started|all-non-done`; pass `--accept-stale` only when replaying unknown/stale entries intentionally.
- **Success gate:** every NOT-DONE entry transitions to a terminal status; manifest history append-only.
- **Failure routing:** `references/universal/failure-modes.md` + `references/modes/rescue.md` §edge-cases.

## Failure-mode taxonomy (universal)

Every mode triages failures through this 7-row table first. Per-mode extensions live in the mode reference. Full per-row remediation in `references/universal/failure-modes.md`.

| # | Failure | Trigger signal | First-line mitigation |
|---|---|---|---|
| 1 | rate-limit / 503 | `503 Service Unavailable` in JSONL or log | wait 15 min, redispatch failed only — never touch done entries |
| 2 | hung process | no progress event ≥ 25 min OR wrapper wall-clock cap hit | mark FAILED-HUNG, terminate codex PID after gate, surface for rescue |
| 3 | MCP-active JSON drop | events absent in `--json` while child alive | rely on `-o` file as truth; advisory `last_error="json_event_dropped"` |
| 4 | output truncation | answer file < `MIN` bytes after DONE event | flag in audit, do NOT auto-retry, surface for human inspect |
| 5 | worktree dirty unexpected | post-run `git status --short` non-empty in supposed-to-commit worktree | mark BLOCKED-DIRTY, do not auto-commit, surface |
| 6 | manifest collision | second writer cannot acquire `manifest.lock` within 30s | hard fail, do not corrupt; surface "another run is active" |
| 7 | state dir missing | `${CLAUDE_PLUGIN_DATA}` unset or state root unwritable | use codex-cc fallback under `${TMPDIR:-/tmp}/codex-companion`; if that fails, surface |

## Terminal Output Contract

| Mode | Required artifacts | Terminal manifest states |
|---|---|---|
| exec | per-entry prompt, log, answer, worktree path, auto-commit result | `done`, `failed`, `skipped` |
| batch | rendered prompts, answers, logs, runner log, `audit-sizes.txt` | `done`, `failed`, `skipped` |
| single | one prompt file, answer file, JSONL log | `done`, `failed` |
| review | per-round findings, JSONL, classifier output | `converged`, `blocked`, `failed`, `cap_reached` |
| rescue | classification JSON in envelope, append-only history rows, selected redispatch ids | inherits original mode |

## Compatibility Boundaries

The old codex trio (`run-codex-exec`, `run-codex-review`, `run-batch-codex-research`) are deprecated compatibility shims. Preserve their install paths, but do not restore their old bodies; route users here.

Use `run-repo-cleanup` after exec/review fleets leave dirty branches, stale worktrees, unpushed commits, or foundation-to-leaf cleanup ordering. Use `ask-review` only for PR handoff. `orchestrate-codex` never opens PRs.

Slash-command boundary: vendored `/codex:review` and codex-companion review remain in `scripts/codex-cc/` but are not used by this skill. Review mode uses `codex exec review`; per-item local review uses `do-review`; external/human/bot feedback consolidation uses `evaluate-code-review`; PR creation uses `ask-review`. There is no `/codex:resc` contract in this skill.

The old third-party bot-wait timing constants from `run-codex-review` are retired. This skill does codex-only review. For third-party bot waits, route to `evaluate-code-review` or a future dedicated skill.

## Anti-patterns

- Never silently overwrite a `done` manifest entry. Skip-existing is the only acceptable behavior.
- Never raise `JOBS` past mode default without `--i-have-measured` AND a logged justification in `manifest.policy.cap_override`.
- Never replace `--dangerously-bypass-approvals-and-sandbox`. The skill assumes bypass; downgrades silently change semantics.
- Never run unbounded concurrency (`xargs -P 0`, naked `&` fan-out). Cap is mode-specific.
- Never auto-merge to `main` / `canary` / default branch. Merging is operator-driven.
- Never use `/tmp/...` as the manifest path of record. Cross-session collisions are silent.
- Never invent a `codex review` invocation other than the native CLI. Review uses `codex exec review` with the documented flags.
- Never skip Monitor arming order. Tail readers miss first-wave events when armed late.
- Never delete a worktree with uncommitted changes without explicit user gate.
- Never overwrite an answer file in batch mode. Archive to `answers/.prev/`, then re-run.
- Never hand-edit the manifest. Use `audit-fleet-state.py` to inspect and `manifest-update.py` to mutate.
- Never drop `CODEX_FLAGS` inside an `xargs bash -c` subshell. The subshell forgets the user's zsh function wrappers.
- Never bundle Claude Code hooks. This is a skill, not a plugin — separation by design.

## References

| File | Role |
|---|---|
Read when routing:

- **Mode files:** `references/modes/exec.md`, `batch.md`, `single.md`, `review.md`, `rescue.md`.
- **Universal runtime contracts:** `manifest-contract.md`, `codex-flags.md`, `monitor-contract.md`, `worktree-contract.md`, `concurrency.md`, `idempotency.md`.
- **Template authoring:** `references/templates/*.tmpl.md` and `references/universal/prompt-discipline.md`.
- **Vendored codex-cc maintenance:** `references/universal/codex-companion.md`, `upstream-codex-cc.md`.
- **Failure forensics:** `references/universal/failure-modes.md`, `json-streaming.md`, `output-size-signals.md`.

| File | Role |
|---|---|
| `references/modes/exec.md` | Recipe for parallel codex exec across worktrees: tasks.json schema, prompt template, auto-commit + post-verify, recovery |
| `references/modes/batch.md` | Recipe for template × N batch: input formats, slug rules, archive-before-retry, audit thresholds |
| `references/modes/single.md` | Recipe for one mission with live stream: cwd-vs-worktree decision, JSONL filter setup |
| `references/modes/review.md` | Recipe for per-branch convergence: round mechanics, classifier policy, evaluator/apply flow, terminal states |
| `references/modes/rescue.md` | Recipe for resume: manifest read, classification table, redo decision matrix, edge cases |
| `references/universal/codex-flags.md` | Every codex CLI flag the skill touches with rationale + per-flag edge cases |
| `references/universal/codex-companion.md` | The vendored codex-cc subtree, dispatcher imports, and rescue state correlation |
| `references/universal/manifest-contract.md` | Full manifest schema with examples; atomic-write recipe; recovery; migration notes |
| `references/universal/monitor-contract.md` | Awk/grep recipes per mode; `fflush()` rule; coverage rule; arm-before-runner; lifecycle |
| `references/universal/worktree-contract.md` | Naming, lifecycle, reuse rules, dirty-state gates, recovery from interrupted state |
| `references/universal/failure-modes.md` | Per-row remediation for every taxonomy entry above plus per-mode extensions |
| `references/universal/concurrency.md` | Per-mode cap rationale; how to measure before raising; the `--i-have-measured` gate |
| `references/universal/json-streaming.md` | JSONL event types codex emits; filter recipes; MCP-active fallback to `-o` |
| `references/universal/idempotency.md` | Skip-existing guards across modes; archive-before-retry; explicit requeue rules |
| `references/universal/output-size-signals.md` | Bottom-decile rule; absolute floor; when small ≠ bad |
| `references/universal/prompt-discipline.md` | Mission-brief skeleton (Intent/Discovery/Constraints/Success/Out-of-scope/Failure protocol) |
| `references/universal/plugin-data.md` | `${CLAUDE_PLUGIN_DATA}` resolution; the state directory pruning policy |
| `references/universal/anti-patterns.md` | The catalog above expanded with worked examples |
| `references/universal/upstream-codex-cc.md` | How to bump the vendored codex-plugin-cc; reapply the patch; what to watch for |
| `references/templates/exec.tmpl.md` | Prompt template for exec mode tasks (SUBAGENT-STOP prefix preserved) |
| `references/templates/batch.tmpl.md` | Prompt template for batch mode (placeholder + structure) |
| `references/templates/single.tmpl.md` | Prompt template for single mission |
| `references/templates/review.tmpl.md` | Prompt template for codex review invocation |
| `references/index.md` | Cross-reference of every reference and which mode pulls it |

## Scripts

| Script | Mode | Purpose |
|---|---|---|
| `scripts/orchestrate-codex.mjs` | all | top-level dispatcher; emits JSON envelope |
| `scripts/codex-flags.sh` | all | sourced helper exporting `CODEX_FLAGS` and `CODEX_REVIEW_FLAGS` |
| `scripts/bootstrap.sh` | all | one-shot pre-flight |
| `scripts/setup-worktree.sh` | exec, review | create worktree, link artifacts, codegen |
| `scripts/render-prompts.sh` | batch, exec | template substitution |
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
| `scripts/codex-cc/` | all | vendored OpenAI codex-plugin-cc tree (see `references/universal/upstream-codex-cc.md`) |
| `scripts/test-runner-contracts.mjs` | test | dispatcher/runner dry-run contract fixtures for all modes |

## Bottom line

Detect mode → run pre-flight → write manifest → spawn the runner detached → emit envelope with Monitor hint → exit. The skill never blocks. Every spawn carries the same flag set. Every failure routes through the taxonomy. Every destructive action is gated. Every rescue starts from a manifest, not a memory.
