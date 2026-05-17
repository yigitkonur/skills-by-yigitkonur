# Vendored: openai/codex-plugin-cc

This directory is a vendored copy of the `plugins/codex/scripts/` tree from
[`openai/codex-plugin-cc`](https://github.com/openai/codex-plugin-cc).

`run-codex-2` is a **skill**, not a plugin — so we ship the scripts as
data the skill uses, not as a Claude Code plugin. The vendored tree mirrors
the upstream layout exactly so internal `import` paths still resolve.

## Pinned

| Field | Value |
|---|---|
| Source | `~/.claude/plugins/cache/openai-codex/codex/1.0.4/scripts/` |
| Version | `1.0.4` |
| Vendored | `2026-05-08` |
| Patches | `codex.mjs.patch` |
| Excluded | `session-lifecycle-hook.mjs`, `stop-review-gate-hook.mjs` (skill ships no Claude Code hooks) |

The two hook scripts are intentionally **not** vendored. `run-codex-2`
is a skill; hook installation is the prerogative of `codex-plugin-cc`. If
the user installs both, `codex-plugin-cc`'s hooks own session-end cleanup
and ours stays out of that surface.

## Patches applied

`codex.mjs.patch` flips three default sandbox values from `"read-only"` to
`"danger-full-access"` so the app-server RPC path agrees with every direct
`codex exec --dangerously-bypass-approvals-and-sandbox` spawn the skill
fans out. Without the patch, codex-companion's task / review subcommands
would default to a read-only sandbox even though the user has globally
opted into bypass.

The patch touches three sites in `lib/codex.mjs`:

1. `buildThreadParams()` — the `task` path's default sandbox.
2. `buildResumeParams()` — the resume path's default sandbox.
3. `runAppServerReview()` — the review thread's hard-coded sandbox literal.

Each site has a leading comment explaining the patch so a reviewer reading
the file in isolation understands why it differs from upstream.

## Update procedure

When upstream ships a new version of `codex-plugin-cc`:

```bash
SRC=~/.claude/plugins/cache/openai-codex/codex/<NEW_VERSION>/scripts
DST=skills/run-codex-2/skills/run-codex-2/scripts/codex-cc

# 1. Refresh the lib tree (deletes orphans).
rsync -av --delete \
  --exclude '*-hook.mjs' \
  "$SRC/codex-companion.mjs" "$SRC/app-server-broker.mjs" "$DST/"
rsync -av --delete "$SRC/lib/" "$DST/lib/"

# 2. Reapply the patch.
cd "$DST" && patch -p2 < codex.mjs.patch

# 3. If the patch rejects, hand-merge the three sandbox sites by reading
#    the rejected hunks (`*.rej`). Update codex.mjs.patch with the
#    refreshed offsets so the next sync is mechanical again:
diff -u <vanilla-codex.mjs> lib/codex.mjs > codex.mjs.patch

# 4. Bump the "Pinned" table in this file.
# 5. Commit: chore(codex-cc): bump to <new version>
```

## Why we vendor instead of resolving at runtime

Two reasons.

First, runtime resolution (`${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs`
→ fallback to the latest semver-sorted dir under
`~/.claude/plugins/cache/openai-codex/codex/`) couples the skill to the
user's plugin install state. A user who hasn't installed
`openai/codex-plugin-cc` cannot run the skill.

Second, vendoring lets us pin a known-good version and ship the sandbox
patch as a single auditable diff. Upstream churn doesn't silently change
the skill's behavior between sessions.

The cost is that upstream bugfixes don't auto-land. The mitigation is the
update procedure above.

## What this directory does NOT contain

- `prompts/`, `commands/`, `agents/`, `hooks/`, `schemas/`, `skills/`,
  `LICENSE`, `NOTICE`, `CHANGELOG.md`, `.claude-plugin/` — every
  plugin-shape artifact upstream ships. The skill doesn't need them.
- `session-lifecycle-hook.mjs` / `stop-review-gate-hook.mjs` — hooks.

If you find yourself reaching for any of these, the boundary's wrong;
re-evaluate before adding them here.
