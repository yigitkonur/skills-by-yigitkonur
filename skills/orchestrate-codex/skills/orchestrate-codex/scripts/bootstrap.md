# bootstrap.sh

One-shot pre-flight runs before any mode dispatches. Verifies tooling, pins baseline state, resolves the manifest path.

## Inputs

```bash
bash bootstrap.sh [MONITOR_ROOT]
```

| Arg/env | Default | Effect |
|---|---|---|
| `MONITOR_ROOT` (env) | derived from `resolveStateDir(cwd)/orchestrate-codex/logs` | where logs and per-entry artifacts go |
| `PROJECT_DIR` (env) | `$PWD` | the workspace root |
| `CLAUDE_PLUGIN_DATA` (env) | optional | when set, state root is `$CLAUDE_PLUGIN_DATA/state`; otherwise `${TMPDIR:-/tmp}/codex-companion` |
| `SKIP_GIT=1` | off | batch/single may skip git checks. |
| `ORCHESTRATE_SKIP_CODEX_AUTH=1` | off | test-only auth bypass. Production preflight hard-fails unauthenticated Codex. |

## Outputs

stdout (KEY=VALUE block; the dispatcher parses it):

```
STATE_DIR=/abs/path/.../state/myrepo-abc1234567890def/orchestrate-codex
MANIFEST_PATH=/abs/path/.../state/myrepo-abc1234567890def/orchestrate-codex/manifest.json
MONITOR_ROOT=/abs/path/.../state/myrepo-abc1234567890def/orchestrate-codex/logs
BASELINE_SHA=abc1234567890def
RUN_ID=20260509T033000Z-abcd
PLUGIN_DATA_ROOT=/abs/plugin-data
WORKSPACE_SLUG=myrepo-abc1234567890def
CODEX_MODEL=gpt-5.5
CODEX_EFFORT=xhigh
```

Side effects:
- Creates `MONITOR_ROOT` directory tree if missing.
- Pins `BASELINE_SHA` (current `git rev-parse HEAD`) when git checks are enabled.
- Exits non-zero when `codex login status` fails, unless `ORCHESTRATE_SKIP_CODEX_AUTH=1` is set for tests.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Pre-flight clean; safe to dispatch |
| 1 | Not in a git repo (and the chosen mode requires one) |
| 2 | `codex` not on `PATH` |
| 3 | `codex login status` failed |
| 4 | `jq`, `flock`, or `node` missing |
| 5 | state dir unwritable |

## Behavior

- Computes the same slug/hash path as `scripts/codex-cc/lib/state.mjs`.
- Creates `STATE_DIR` and `MONITOR_ROOT`.
- Emits an advisory when `.worktrees/` is not ignored and git checks are enabled.

## Notes

The dispatcher invokes `bootstrap.sh` once at the start of a run. Re-running is idempotent — every check is read-only or repeat-safe.

If `bootstrap.sh` exits non-zero, the dispatcher emits the failure as a JSON envelope `error.code` and stops. The user fixes the underlying issue (codex auth, git repo, etc.) and reruns the dispatcher.
