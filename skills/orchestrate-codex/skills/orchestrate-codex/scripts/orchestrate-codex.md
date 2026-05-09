# orchestrate-codex.mjs

Top-level dispatcher. Parses argv, validates inputs, seeds the manifest, spawns the bash runner detached, emits a JSON envelope on stdout with a Monitor tool hint the agent surfaces verbatim.

## Inputs

```bash
node orchestrate-codex.mjs <mode> [args]
```

Modes:

| Mode | Required args | Optional |
|---|---|---|
| `exec` | `--tasks <tasks.json>` | `--concurrency N`, `--monitor-root <dir>` |
| `batch` | `--inputs <file> --template <tmpl>` | `--answers-dir <dir>`, `--concurrency N` |
| `single` | `--prompt-file <p>` OR `--prompt <text>` | `--cwd <dir>`, `--out <file>`, `--reuse-worktree` |
| `review` | `--branches <a,b,c>` OR `--branches-file <file>` | `--base <main>`, `--max-rounds N`, `--concurrency N` |
| `rescue` | none (resolves manifest from cwd) | `--manifest <path>`, `--accept-stale` |
| `audit` | none | `--manifest <path>`, `--json` |
| `tidy` | none | `--manifest <path>`, `--base <main>`, `--execute`, `--force-abandon <id>...` |
| `--help` / no mode | n/a | n/a |

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
    "runner_pid": 69249
  },
  "meta": {
    "pid": 69249,
    "started_at": "2026-05-08T18:20:30Z"
  },
  "monitor": {
    "tool_hint": "Monitor({\n  description: \"orchestrate-codex exec fleet (run_id=20260508T182030Z-7q4f)\",\n  command: \"ORCHESTRATE_MANIFEST=/abs/.../manifest.json bash /abs/.../codex-monitor.sh\",\n  persistent: true,\n  timeout_ms: 14400000\n})"
  }
}
```

Failure:
```json
{"ok": false, "schema_version": 1, "command": "exec", "error": {"code": "missing_required_arg", "message": "exec mode requires --tasks <tasks.json>."}}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Dispatcher succeeded; runner detached |
| 2 | User-input error (missing args, bad mode name) |
| 3 | Manifest error (concurrent run in progress, manifest unwritable) |
| 4 | Spawn error (runner script not found, fork failed) |
| 5 | Codex unauthenticated (`codex login status` non-zero) |

## Behavior

- Sources the workspace state-dir from `codex-cc/lib/state.mjs:resolveStateDir(cwd)`. Slug+hash matches codex-companion exactly.
- Writes the seed manifest atomically (mktemp + rename in the same dir).
- Spawns the bash runner via `child_process.spawn(..., { detached: true, stdio: 'ignore' })` and `unref()`s it. The dispatcher returns instantly; the runner runs independently.
- Refuses concurrent runs: if a manifest exists with `queued|running` entries, exits 3 with `error.code="concurrent_run_in_progress"`.
- For `rescue|audit|tidy`: invokes the corresponding Python helper via `subprocess`, embeds the helper's JSON output under `result`.

## Monitor hint contract

Every successful envelope includes `monitor.tool_hint`. The string is a literal `Monitor({...})` invocation that the agent surfaces verbatim. Properties:
- `description` is mode-specific and includes the `run_id` for disambiguation.
- `command` always uses `--line-buffered` in any grep pipe and `fflush()` in any awk pipe.
- `persistent: true` for exec/batch/review (long-running); `persistent: false` with bounded `timeout_ms` for single.
- The `monitor.tool_hint` parses as a valid JS expression (verified by `test-monitor-integration.mjs`).

## Notes

The dispatcher does NOT invoke `codex` directly. It spawns the bash runner; the runner sources `codex-flags.sh` and invokes `codex exec`. Updating the codex policy (model, effort, sandbox) is a one-line change in `codex-flags.sh`; the dispatcher need not be touched.

Two test/dev hatches exist as env vars (`ORCHESTRATE_RUNNER_<MODE>` to point at a stub, `ORCHESTRATE_HELPER_<KIND>` to point at a stub). Production callers never set these; they exist for the integration test harness.
