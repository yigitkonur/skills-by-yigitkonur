# bootstrap.sh

One-shot pre-flight runs before any mode dispatches. Verifies tooling, pins baseline state, resolves the manifest path.

## Inputs

```bash
bash bootstrap.sh [MONITOR_ROOT]
```

| Arg/env | Default | Effect |
|---|---|---|
| `MONITOR_ROOT` (positional) | derived from `${CLAUDE_PLUGIN_DATA}/state/<slug>-<hash>/` | where logs and per-entry artifacts go |
| `PROJECT_DIR` (env) | `$PWD` | the workspace root |
| `CLAUDE_PLUGIN_DATA` (env) | resolved per `references/universal/plugin-data.md` | state root for the manifest |

## Outputs

stdout (KEY=VALUE block; the dispatcher parses it):

```
PROJECT_DIR=/abs/path/to/repo
WORKSPACE_SLUG=myrepo-abc1234567890def
MONITOR_ROOT=/abs/path/.../state/myrepo-abc.../orchestrate-codex
MANIFEST_PATH=/abs/path/.../state/myrepo-abc.../orchestrate-codex/manifest.json
BASELINE_SHA=abc1234567890def
CODEX_VERSION=codex-cli 0.129.0
JQ_AVAILABLE=1
GH_AVAILABLE=1
NODE_VERSION=v22.x.x
PYTHON_VERSION=3.11.x
```

Side effects:
- Creates `MONITOR_ROOT` directory tree if missing.
- Pins `BASELINE_SHA` (current `git rev-parse HEAD`) to the manifest dir for forensics.
- Writes a stderr warning (non-fatal) when codex auth probe (`codex login status`) returns non-zero — auth probes are flaky on dev boxes; the actual spawns may still work.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Pre-flight clean; safe to dispatch |
| 1 | Not in a git repo (and the chosen mode requires one) |
| 2 | `codex` not on `PATH` or unauthenticated |

## Behavior

- Detects monorepo layout (multiple `package.json`s with workspace fields) and surfaces it in stdout for downstream tools.
- Verifies `.gitignore` covers `<repo-name>-wt-*`; appends pattern to `.gitignore` if missing AND user passed `--gitignore-fix` (default off).
- Soft-warns when `${CLAUDE_PLUGIN_DATA}` is unset and falls back to the XDG path.

## Notes

The dispatcher invokes `bootstrap.sh` once at the start of a run. Re-running is idempotent — every check is read-only or repeat-safe.

If `bootstrap.sh` exits non-zero, the dispatcher emits the failure as a JSON envelope `error.code` and stops. The user fixes the underlying issue (codex auth, git repo, etc.) and reruns the dispatcher.
