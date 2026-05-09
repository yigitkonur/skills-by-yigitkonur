# orchestrate-codex.mjs

Top-level dispatcher. Parses argv strictly, validates inputs, runs `codex` pre-flight, seeds the manifest, spawns the bash runner detached (with stdout+stderr redirected to a discoverable log), and emits a JSON envelope on stdout with a Monitor tool hint the agent surfaces verbatim.

## Inputs

```bash
node orchestrate-codex.mjs <mode> [args]
```

Modes:

| Mode | Required args | Optional |
|---|---|---|
| `exec` | `--tasks <tasks.json>` | `--concurrency N`, `--i-have-measured "<justification>"`, `--monitor-root <dir>`, `--run-id <id>`, `--force-redo <slug[,slug2,...]>`, `--force-redo-all`, `--force-new-run` (with `--run-id`) |
| `batch` | `--inputs <file> --template <tmpl>` | `--answers-dir <dir>`, `--concurrency N`, `--i-have-measured "<j>"`, `--force-redo <slug>`, `--force-redo-all`, `--force-new-run --run-id <id>` |
| `single` | `--prompt-file <p>` OR `--prompt <text>` | `--cwd <dir>`, `--out <file>`, `--reuse-worktree`, `--output-schema <schema.json>`, `--resume-last`, `--resume-thread <id>`, `--force-new-run --run-id <id>` |
| `review` | `--branches <a,b,c>` OR `--branches <file>` | `--base <main>`, `--concurrency N`, `--i-have-measured "<j>"` |
| `rescue` | none (resolves manifest from cwd) | `--manifest <path>`, `--apply failed-only\|never-started-only\|all-non-done\|ids:s1,s2,…`, `--accept-stale` |
| `audit` | none | `--manifest <path>`, `--json` |
| `tidy` | none | `--manifest <path>`, `--base <main>`, `--execute`, `--force-abandon <id>` |
| `--help` / no mode | n/a | n/a |

Unknown long-options produce `error.code: "unknown_option"` (exit 2). The dispatcher does not silently swallow flags — every flag listed above is honored, and anything else is rejected.

## Output (always one JSON envelope on stdout)

Success:
```json
{
  "ok": true,
  "schema_version": 1,
  "command": "exec",
  "result": {
    "phase": "queued",
    "next_action": "arm Monitor and wait",
    "manifest_path": "/abs/.../manifest.json",
    "run_id": "20260508T182030Z-7q4f",
    "entries_count": 5,
    "runner_pid": 69249,
    "runner_log_path": "/abs/.../logs/20260508T182030Z-7q4f/_runner.log",
    "concurrency_cap": 5,
    "concurrency_source": "default"
  },
  "meta": { "pid": 69249, "started_at": "2026-05-08T18:20:30Z" },
  "monitor": {
    "tool_hint": "Monitor({\n  description: \"...\",\n  command: \"...\",\n  persistent: true,\n  timeout_ms: 3600000\n})"
  }
}
```

Failure:
```json
{"ok": false, "schema_version": 1, "command": "exec", "error": {"code": "missing_required_arg", "message": "exec mode requires --tasks <tasks.json>."}}
```

### Rescue envelope (no `--apply`)

The classify-only rescue envelope returns `next_action` as a structured `ask_user_question` object — the calling agent doesn't have to parse English to extract the question:

```json
{
  "ok": true,
  "command": "rescue",
  "result": {
    "phase": "done",
    "next_action": {
      "kind": "ask_user_question",
      "prompt": "Which subset to redo?",
      "choices": [
        { "id": "failed-only", "label": "Redo failures only (1 entries)", "entry_ids": ["02-bar"] },
        { "id": "never-started-only", "label": "Redo never-started only (0 entries)", "entry_ids": [] },
        { "id": "all-non-done", "label": "Redo all non-done (1 entries)", "entry_ids": ["02-bar"] }
      ],
      "rerun_with": "node orchestrate-codex.mjs rescue --manifest <path> --apply <subset>"
    }
  }
}
```

### Rescue envelope (`--apply <subset>`)

When `--apply` is passed, rescue performs pre-rescue cleanup (kill stale pids, stash dirty worktrees, prune missing worktrees), flips selected entries back to `queued` via `manifest-update.py`, and re-spawns the original mode's runner. The envelope shape mirrors the original mode's success envelope, with extra `flipped_entries` + `cleanup` fields.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Dispatcher succeeded; runner detached |
| 2 | User-input error (`unknown_option`, `missing_required_arg`, `bad_argument`, `bad_*_file`, `not_a_repo`) |
| 3 | Manifest error (`concurrent_run_in_progress`, `manifest_corrupt`, `manifest_not_found`, `manifest_inflight_race`) |
| 4 | Spawn error (`spawn_failed`, `python_helper_failed`) |
| 5 | Codex unavailable / unauthenticated (`codex_unavailable`, `codex_unauthenticated`) |

## Behavior

- **Strict argv parsing.** The dispatcher wraps `parseArgs` so unknown long-options error out with `error.code: "unknown_option"` and the offending flag name. Unknown short-form flags are also rejected — the dispatcher uses long-form exclusively.
- **`codex` pre-flight.** Before seeding any manifest, the dispatcher runs `command -v codex`. If missing, exits with `error.code: "codex_unavailable"` (exit 5). Without this gate, a missing `codex` would let the runner exit immediately and strand every entry in `queued` forever, blocking every subsequent run with `concurrent_run_in_progress`. The check is skipped when `ORCHESTRATE_RUNNER_<MODE>` is set (integration test hatch) or when `ORCHESTRATE_SKIP_CODEX_PREFLIGHT=1` is set.
- **Sources the workspace state-dir** from `codex-cc/lib/state.mjs:resolveStateDir(cwd)`. Slug+hash matches codex-companion exactly.
- **Atomic manifest write.** `mktemp + rename` in the same directory.
- **Detached runner spawn.** `child_process.spawn(..., { detached: true, stdio: ['ignore', logFd, logFd] })` and `unref()`. The dispatcher returns instantly; the runner runs independently. **Stdout+stderr are redirected to `${monitor_root}/logs/<run_id>/_runner.log`** so `audit-sizes.sh` and `codex-monitor.sh` can grep the runner's `START/DONE/FAIL/SKIP` markers after the dispatcher exits. The log path is surfaced in the envelope as `result.runner_log_path`.
- **Concurrent-run gate.** If a manifest exists with `queued|running` entries, exits 3 with `error.code="concurrent_run_in_progress"` and `recovery_options: ["wait", "rescue", "--force-new-run --run-id <custom>"]`. The defense-in-depth race guard inside `seedManifest()` returns the same envelope shape (`error.code="manifest_inflight_race"`) instead of throwing.
- **Concurrency soft gate.** Any concurrency above the mode default OR above the hard cap (20) requires `--i-have-measured "<justification>"` (a value flag, not a boolean). The justification is persisted at `manifest.policy.overrides.concurrency = {value, justification, set_at}`. The absolute ceiling (100) is refused unconditionally. Precedence: `--concurrency` flag > `JOBS` env > mode default; the `result.concurrency_source` field reports which source won.
- **Per-task `post_verify_cmd`.** When a task in `tasks.json` carries `post_verify_cmd`, it's threaded into `entries[i].mode_state.post_verify_cmd` so `run-fleet.sh` can prefer it over auto-detect.
- **Force-redo (exec/batch).** `--force-redo <slug[,slug2,…]>` (or `--force-redo-all`) operates on an existing manifest: archives the current answer files into `<answers>/.prev/<slug>-<ts>.md`, flips chosen entries to `queued` via `manifest-update.py --execute`, and re-spawns the runner without re-seeding. Force-redo deliberately bypasses the concurrent-run gate (the operator's intent is to act on the existing manifest).
- **Force-new-run.** `--force-new-run --run-id <custom>` writes the manifest to `manifest.<run_id>.json` instead of `manifest.json`, allowing a parallel run on the same workspace without colliding. `--run-id` is required (otherwise the resulting manifest is undiscoverable).
- **Single-mode flags.** `--output-schema <file.json>` validates the schema is JSON-parseable, persists the path to `mode_state.single.output_schema`, and forwards `--output-schema <file>` to `run-single.sh`. `--reuse-worktree` is forwarded as a runner flag and recorded at `mode_state.single.reuse_worktree=true`. `--resume-last` and `--resume-thread <id>` are mutually exclusive; both are forwarded to `run-single.sh` and recorded in `mode_state.single.resume_*`.
- **Monitor timeout clamp.** Every `monitor.tool_hint` `timeout_ms` is clamped to `MONITOR_HARD_MAX_MS = 3,600,000` (1 hour). Larger values would be silently clamped by Monitor itself; clamping here keeps the envelope honest.
- **Rescue redispatch.** `rescue --apply <subset>` selects entries (`failed-only`, `never-started-only`, `all-non-done`, `ids:s1,s2,…`), runs cleanup (kill stale pids, stash dirty worktrees, prune missing worktrees), flips them to `queued` via `manifest-update.py --execute`, and re-spawns the original mode's runner. Refuses rescue-of-rescue.
- For `audit/tidy`: invokes the corresponding Python helper via `subprocess`, embeds the helper's JSON output under `result`.

## Monitor hint contract

Every successful envelope includes `monitor.tool_hint`. The string is a literal `Monitor({...})` invocation that the agent surfaces verbatim. Properties:
- `description` is mode-specific and includes the `run_id` for disambiguation.
- `command` for `exec/batch/review` invokes `codex-monitor.sh` (the rule-engine ticker that already line-buffers its output); for `single` it tails the JSONL through `awk '{ print; fflush(); }'` so events stream live, not block-buffered.
- `persistent: true` for fleet modes (long-running); `persistent: false` for single (bounded).
- `timeout_ms` is always clamped to ≤ 3,600,000 ms (Monitor's hard ceiling).
- The `monitor.tool_hint` parses as a valid JS expression (verified by `test-monitor-integration.mjs`).

## Notes

The dispatcher does NOT invoke `codex` directly. It spawns the bash runner; the runner sources `codex-flags.sh` and invokes `codex exec`. Updating the codex policy (model, effort, sandbox) is a one-line change in `codex-flags.sh`; the dispatcher need not be touched.

Test/dev hatches (env vars; production callers never set):
- `ORCHESTRATE_RUNNER_<MODE>` — point a mode at a stub runner.
- `ORCHESTRATE_HELPER_<KIND>` — point rescue/audit/tidy at a stub helper.
- `ORCHESTRATE_RUNNER_FOREGROUND=1` — run the selected runner synchronously via `spawnSync` so tests can inspect the resulting manifest without waiting on a detached process.
- `ORCHESTRATE_SKIP_CODEX_PREFLIGHT=1` — skip the `command -v codex` check.
- `ORCHESTRATE_SKIP_PREFLIGHT=1` — bypass `bootstrap.sh` invocation for dry-run fixtures.
- `ORCHESTRATE_SKIP_CODEX_AUTH=1` — bypass the bash `bootstrap.sh` `codex login status` hard-gate for bearer-token / managed-companion / proxy auth scenarios.

Documented references:
- `references/universal/concurrency.md` — soft gate, override format, hard ceiling.
- `references/universal/idempotency.md` — force-redo, force-new-run, archive layout.
- `references/modes/rescue.md` — pre-rescue cleanup procedure.
- `references/modes/single.md` — single-mode flag semantics.
