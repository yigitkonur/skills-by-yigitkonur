# `${CLAUDE_PLUGIN_DATA}` resolution and the state directory

Every orchestrate-codex run writes its manifest under a state directory keyed off the workspace. The directory's path is derived from `${CLAUDE_PLUGIN_DATA}` with a documented fallback chain. Codex-companion uses the same workspace-slug+hash function, so our manifest sits next to its `state.json` and `jobs/` records — rescue can correlate by codex thread id.

## Resolution chain

```
1. ${CLAUDE_PLUGIN_DATA}
2. ${XDG_DATA_HOME}/claude-code
3. ${HOME}/.local/share/claude-code
```

Whichever resolves first AND is writable wins. The dispatcher computes:

```
state-root = "<resolved-base>/state/<workspace-slug>-<hash>/orchestrate-codex"
manifest   = "<state-root>/manifest.json"
```

If `${CLAUDE_PLUGIN_DATA}` is not set OR not writable, the dispatcher logs a warning to stderr (in JSON envelope's `meta.warnings`) and proceeds with the fallback. If even the fallback isn't writable, the dispatcher emits `error.code="plugin_data_unwritable"` and exits 5.

**Important:** codex-companion's own state directory uses a different fallback (`os.tmpdir()/codex-companion/...`). When `${CLAUDE_PLUGIN_DATA}` is unset, our manifest and codex-companion's state may end up in different roots. Rescue mode handles this by computing codex-companion's path independently using the upstream `state.mjs:resolveStateDir` algorithm.

`bootstrap.sh` ensures `${CLAUDE_PLUGIN_DATA}` is set before any spawn, keeping the two co-located.

## Workspace slug + hash

`<workspace-slug>-<hash>` is computed from `cwd` (or `--workspace-root` if explicit):

```python
import hashlib, os, re

def resolve_state_dir_name(cwd: str) -> str:
    workspace_root = os.path.realpath(cwd)  # codex-companion uses fs.realpath
    raw_basename = os.path.basename(workspace_root) or "workspace"
    slug = re.sub(r"[^a-z0-9-]+", "-", raw_basename.lower()).strip("-") or "workspace"
    digest = hashlib.sha256(workspace_root.encode("utf-8")).hexdigest()[:16]
    return f"{slug}-{digest}"
```

This is a verbatim port of codex-companion's `lib/state.mjs:resolveStateDir(cwd)`. Verified across 5 cwd inputs to produce byte-identical paths.

Notes:
- `realpath` resolves symlinks. macOS `/tmp` → `/private/tmp` matters; `cwd=/tmp/test` produces a different hash than the same script run from `/private/tmp/test`.
- The slug is lowercase + dash-only; uppercase basenames are folded.
- The hash is 16 hex chars (64 bits) — ample collision resistance for any one user's workspaces.

## Why outside the repo

The state directory lives outside the source repo because:
- The orchestrator owns the state, not the project. Multiple repos share the same skill but have separate state.
- Matches codex-companion's model. Rescue can correlate cleanly.
- Multiple Claude Code sessions can run the skill on the same repo without leaving orphan files in the working tree.
- The repo's `.gitignore` doesn't have to know about the manifest.

The cost: rescue is local-machine-only. A run on machine A cannot resume on machine B; the state is on A's disk.

## Layout under state-root

```
<state-root>/
├── manifest.json                    # the orchestrate-codex manifest
├── manifest.json.lock               # advisory lock file (flock)
└── (siblings via codex-companion when CLAUDE_PLUGIN_DATA is shared:)
    ├── ../state.json                # codex-companion's job index (one level up)
    ├── ../jobs/<id>.json            # codex-companion's per-job records
    └── ../broker.json               # codex-companion's broker endpoint
```

Note the slight asymmetry: orchestrate-codex's manifest is in `<state-root>/manifest.json` where `<state-root>` ends in `/orchestrate-codex/`. Codex-companion's `state.json` is one directory up, in `<workspace-slug>-<hash>/state.json`. Both are under the same `<workspace-slug>-<hash>` so rescue's correlation works.

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

## Multiple manifests in one state-root

When `--force-new-run --run-id <custom>` is used, the manifest is written to:

```
<state-root>/manifest.<custom-id>.json
```

This lets parallel runs on the same workspace coexist (rare but valid for e.g. one fleet + one single-mission research task).

The Monitor command must use the explicit path (not just `manifest.json`). The dispatcher's emitted hint includes the path.

## Recovery from a corrupt state-root

If the state directory is corrupt (e.g. `manifest.json` is partial JSON):

1. `python3 audit-fleet-state.py --manifest <state-root>/manifest.json --json --repair-dry-run` — reads with a tolerant parser, lists what's salvageable.
2. If salvageable, apply with `--repair-execute`.
3. If unsalvageable, rename the broken file (`mv manifest.json manifest.json.broken-<ts>`) and start fresh with `--force-new-run`. Surface the broken file path so the user can inspect.

Never `rm` a corrupt manifest silently. The history may be the only record of what was attempted.

## Anti-patterns

- Hard-coding `${HOME}/.local/share/claude-code` in any script. Use the resolution chain.
- Writing the manifest to `/tmp/...`. Cross-session collisions silently overwrite.
- Relying on `${CLAUDE_PLUGIN_DATA}` being set without bootstrap. The skill's `bootstrap.sh` is the single setter.
- Manually editing files under `<state-root>` other than the manifest. The lock file is advisory; broker.json is codex-companion's; meddling breaks both.
- Running the skill in a directory that resolves to a different `realpath` between runs (e.g. mounting/unmounting filesystems). The slug+hash will differ; rescue won't find prior state.

## Forensics

If rescue can't find a manifest the user expects:

```bash
# What's the resolved state-root for this cwd?
node -e 'import("/path/to/scripts/codex-cc/lib/state.mjs").then(m => console.log(m.resolveStateDir(process.cwd())))'

# What state-roots exist?
ls -la "${CLAUDE_PLUGIN_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-code}/state/"

# Which one matches the workspace's expected slug?
ls -la "${CLAUDE_PLUGIN_DATA:-...}/state/" | grep "$(basename "$PWD")"

# Is the manifest in the expected place?
ls -la "${CLAUDE_PLUGIN_DATA:-...}/state/<slug>-<hash>/orchestrate-codex/"
```

The most common cause of "rescue can't find manifest": the user moved or renamed the workspace directory between runs, so `realpath` produces a different hash now than at original-run time.
