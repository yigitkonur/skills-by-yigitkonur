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
- Hard-fails with exit 3 when `codex login status` returns non-zero, unless `ORCHESTRATE_SKIP_CODEX_AUTH=1` is set (typical use: ephemeral CI runners that do not carry codex-cli auth state).

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

- Detects monorepo layout (multiple `package.json`s with workspace fields) and surfaces it in stdout for downstream tools.
- Probes `.gitignore` for the in-repo worktree pattern only; see "Worktree advisory" below for the conditional.
- Falls back to `${TMPDIR:-/tmp}/codex-companion` when `${CLAUDE_PLUGIN_DATA}` is unset (matches the codex-companion resolver — see `references/universal/plugin-data.md`).
- **`codex login status` is a hard gate** (`scripts/bootstrap.sh:74-82`): a non-zero exit fails bootstrap with exit 3 and the dispatcher surfaces the failure in its JSON envelope. The escape hatch is `ORCHESTRATE_SKIP_CODEX_AUTH=1`, which downgrades the gate to a stderr warning and proceeds. Use the escape hatch on ephemeral CI runners that do not carry codex-cli auth state; in any environment where spawns will exercise codex auth, leave the gate hard and run `codex login` if it fails.

### Worktree advisory

`scripts/bootstrap.sh:148-155` advises adding the worktree dir to `.gitignore` **only when** the resolved `WORKTREE_DIR_NAME` (default `.worktrees`) is treated as in-repo. The default convention (per `references/universal/worktree-contract.md`) places worktrees OUT-of-repo at `<repo-parent>/<repo>-wt-<mode>-<slug>`, in which case `.gitignore` does not need to cover them. The advisory fires only when `WORKTREE_DIR_NAME` points inside the repo — typically when the user has overridden the default to a relative path like `.worktrees/`.

## Notes

The dispatcher invokes `bootstrap.sh` once at the start of a run. Re-running is idempotent — every check is read-only or repeat-safe.

If `bootstrap.sh` exits non-zero, the dispatcher emits the failure as a JSON envelope `error.code` and stops. The user fixes the underlying issue (codex auth, git repo, etc.) and reruns the dispatcher.
