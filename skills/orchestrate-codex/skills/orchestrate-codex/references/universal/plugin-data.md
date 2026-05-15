# `${CLAUDE_PLUGIN_DATA}` resolution and the state directory

Every orchestrate-codex run writes its manifest under the same state directory algorithm used by vendored codex-cc. Codex-companion uses the same workspace-slug+hash function, so our manifest sits next to its `state.json` and `jobs/` records — rescue can correlate by codex thread id.

## Contents

- Resolution chain
- Workspace slug + hash
- Why outside the repo
- Layout under state-root
- Pruning
- One active manifest per state-root
- Recovery from a corrupt state-root
- Anti-patterns
- Forensics

## Resolution chain

orchestrate-codex's resolver:

```
1. `${CLAUDE_PLUGIN_DATA}/state/<workspace-slug>-<hash>`
2. `${TMPDIR:-/tmp}/codex-companion/<workspace-slug>-<hash>`
```

Whichever resolves first AND is writable wins. The dispatcher computes:

```
state-root = "<resolved-state-dir>/orchestrate-codex"
manifest   = "<state-root>/manifest.json"
```

If `${CLAUDE_PLUGIN_DATA}` is not set OR not writable, the dispatcher logs a warning to stderr (in JSON envelope's `meta.warnings`) and proceeds with the fallback. If even the fallback isn't writable, the dispatcher emits `error.code="plugin_data_unwritable"` and exits 5.

### Symmetric fallback — orchestrate-codex and codex-companion agree

Both writers — orchestrate-codex (dispatcher + `bootstrap.sh`) and the vendored codex-companion (`scripts/codex-cc/lib/state.mjs`) — share the same resolver chain. There is no asymmetry between the two.

```
1. ${CLAUDE_PLUGIN_DATA}/state/<slug>-<hash>
2. ${TMPDIR:-/tmp}/codex-companion/<slug>-<hash>     (canonical fallback; same for both writers)
```

Verify at `scripts/codex-cc/lib/state.mjs:10` (`FALLBACK_STATE_ROOT_DIR = path.join(os.tmpdir(), "codex-companion")`) and `scripts/codex-cc/lib/state.mjs:41-43` (resolver returns `pluginDataDir ? path.join(pluginDataDir, "state") : FALLBACK_STATE_ROOT_DIR`). The dispatcher's bootstrap matches at `scripts/bootstrap.sh:114-120` (`STATE_ROOT="$CLAUDE_PLUGIN_DATA/state"` or `STATE_ROOT="${TMPDIR:-/tmp}/codex-companion"`). Neither consults `XDG_DATA_HOME` and neither falls back to `~/.local/share/claude-code`.

**Consequence:** rescue's correlation between manifest entries (orchestrate-codex's `manifest.json`) and codex-companion job records (`state.json`, `jobs/<id>.json`) holds whenever both writers ran in the same process tree, because they computed the same `<slug>-<hash>` against the same `${CLAUDE_PLUGIN_DATA}` (set or unset). The cross-link breaks only when `${CLAUDE_PLUGIN_DATA}` flips partway through the session — e.g. set on dispatch but unset for a later helper invocation, so the two writers land in different roots.

**Operators should export `${CLAUDE_PLUGIN_DATA}` once for the session OR always invoke `node orchestrate-codex.mjs <mode>` (which goes through `bootstrap.sh`) rather than the helper scripts directly.** Switching the env var mid-session is the only way the two roots can diverge.

## Workspace slug + hash

`<workspace-slug>-<hash>` is computed from `cwd` (or `--workspace-root` if explicit):

```python
import hashlib, os, re

def resolve_state_dir_name(cwd: str) -> str:
    workspace_root = os.path.realpath(cwd)  # codex-companion uses fs.realpath
    raw_basename = os.path.basename(workspace_root) or "workspace"
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw_basename).strip("-") or "workspace"
    digest = hashlib.sha256(workspace_root.encode("utf-8")).hexdigest()[:16]
    return f"{slug}-{digest}"
```

This is a verbatim port of codex-companion's `lib/state.mjs:resolveStateDir(cwd)`. Verified across 5 cwd inputs to produce byte-identical paths.

Notes:
- `realpath` resolves symlinks. macOS `/tmp` → `/private/tmp` matters; `cwd=/tmp/test` produces a different hash than the same script run from `/private/tmp/test`.
- The slug preserves case and allows dot/underscore/dash, matching `state.mjs`.
- The hash is 16 hex chars (64 bits) — ample collision resistance for any one user's workspaces.

## Why outside the repo

The state directory lives outside the source repo because:
- The orchestrator owns the state, not the project. Multiple repos share the same skill but have separate state.
- Matches codex-companion's model. Rescue can correlate cleanly.
- Multiple Claude Code sessions can run the skill on the same repo without leaving orphan files in the working tree.
- The repo's `.gitignore` doesn't have to know about the manifest.

The cost: rescue is local-machine-only. A run on machine A cannot resume on machine B; the state is on A's disk.

## Layout under state-root

What orchestrate-codex itself writes:

```
<state-root>/
├── manifest.json                    # the orchestrate-codex manifest
└── manifest.json.lock               # advisory lock file (flock)
```

That's it. The skill writes no other state files at this level — no jobs/, no broker.json, no per-run logs (logs land under `<monitor-root>/logs/<run-id>/`, configurable via `MONITOR_ROOT` env, default `/tmp/orchestrate-codex-monitor/`).

When `${CLAUDE_PLUGIN_DATA}` is set consistently AND codex-companion is also using it, codex-companion's siblings appear one level up:

```
<workspace-slug>-<hash>/
├── orchestrate-codex/manifest.json       # this skill's manifest
├── orchestrate-codex/manifest.json.lock
├── state.json                            # codex-companion's job index
├── jobs/<id>.json                        # codex-companion's per-job records
└── broker.json                           # codex-companion's broker endpoint
```

Note the slight nesting offset: orchestrate-codex's manifest is in `<state-root>/manifest.json` where `<state-root>` ends in `/orchestrate-codex/`. Codex-companion's `state.json` is one directory up, in `<workspace-slug>-<hash>/state.json`. Both writers anchor on the same `<workspace-slug>-<hash>` regardless of whether `${CLAUDE_PLUGIN_DATA}` is set, because they share the same resolver chain (see "Symmetric fallback" above). Rescue's correlation breaks only if `${CLAUDE_PLUGIN_DATA}` flips between writes — see also `references/universal/manifest-contract.md` §Path.

## Pruning

The skill does NOT auto-prune state directories. Multiple historical runs accumulate; cleanup is the user's call.

Codex-companion's `state.json` does prune: `MAX_JOBS=50` keeps the 50 most-recent job records. Past that, older `jobs/<id>.json` are deleted. Rescue handles this gracefully — when a manifest references a thread ID whose codex-companion record was pruned, rescue-detect classifies it as `unknown` and surfaces the "limited rescue context" warning.

To manually prune all orchestrate-codex state for a workspace:

```bash
rm -rf <state-root>
```

Or to prune just stale runs (keeping the most-recent):

```bash
ls -t <workspace-slug>-<hash>/orchestrate-codex/manifest.*.json 2>/dev/null | tail -n +2 | xargs rm -f
```

The skill's tidy command (`node orchestrate-codex.mjs tidy`) does NOT remove the state directory; it only removes worktrees and clears the active manifest.

## One active manifest per state-root

The dispatcher writes one active `manifest.json` per workspace state-root. If it contains non-terminal entries, the next dispatch refuses and routes to rescue. Use a different cwd/state root for truly independent concurrent orchestration.

## Recovery from a corrupt state-root

If the state directory is corrupt (e.g. `manifest.json` is partial JSON):

1. `python3 audit-fleet-state.py --manifest <state-root>/manifest.json --json --repair-dry-run` — reads with a tolerant parser, lists what's salvageable.
2. If salvageable, apply with `--repair-execute`.
3. If unsalvageable, rename the broken file (`mv manifest.json manifest.json.broken-<ts>`) and start fresh. Surface the broken file path so the user can inspect.

Never `rm` a corrupt manifest silently. The history may be the only record of what was attempted.

## Anti-patterns

- Hard-coding `${HOME}/.local/share/claude-code` in any script. Use `codex-cc/lib/state.mjs`.
- Inventing a custom manifest path. Dispatcher, bootstrap, and rescue must resolve the same state-root.
- Assuming `${CLAUDE_PLUGIN_DATA}` is set. The codex-cc fallback is valid and shared by dispatcher/bootstrap/rescue.
- Manually editing files under `<state-root>` other than the manifest. The lock file is advisory; broker.json is codex-companion's; meddling breaks both.
- Running the skill in a directory that resolves to a different `realpath` between runs (e.g. mounting/unmounting filesystems). The slug+hash will differ; rescue won't find prior state.

## Forensics

If rescue can't find a manifest the user expects:

```bash
# What's the resolved state-root for this cwd?
node -e 'import("/path/to/scripts/codex-cc/lib/state.mjs").then(m => console.log(m.resolveStateDir(process.cwd())))'

# What state-roots exist?
node -e 'import("/path/to/scripts/codex-cc/lib/state.mjs").then(m => console.log(m.resolveStateDir(process.cwd())))'

# Which one matches the workspace's expected slug?
ls -la "$(dirname "$(node -e 'import("/path/to/scripts/codex-cc/lib/state.mjs").then(m => console.log(m.resolveStateDir(process.cwd())))')")"

# Is the manifest in the expected place?
ls -la "${CLAUDE_PLUGIN_DATA:-...}/state/<slug>-<hash>/orchestrate-codex/"
```

The most common cause of "rescue can't find manifest": the user moved or renamed the workspace directory between runs, so `realpath` produces a different hash now than at original-run time.
