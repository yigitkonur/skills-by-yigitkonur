# Upstream codex-plugin-cc — vendoring and update procedure

The skill ships a vendored copy of `openai/codex-plugin-cc`'s `plugins/codex/scripts/` tree under `<skill-root>/scripts/codex-cc/`. The vendor is pinned to a specific upstream version; updates are mechanical (`rsync` + `git apply` of the patch).

This file documents:
- Why we vendor instead of resolving at runtime.
- The pinned version and the patch.
- The update procedure when upstream ships a new version.
- What to watch for during updates.

## Why vendor, not resolve at runtime

Two reasons.

**(1) Coupling avoidance.** Runtime resolution (`${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs` → fallback to the latest semver-sorted dir under `~/.claude/plugins/cache/openai-codex/codex/`) couples the skill to the user's plugin install state. A user who hasn't installed `openai/codex-plugin-cc` cannot run the skill. Vendoring removes that dependency.

**(2) Auditable patches.** The skill applies a patch to `lib/codex.mjs` (default sandbox flipped from `read-only` to `danger-full-access`). When vendoring, the patch lives as a single file at `scripts/codex-cc/codex.mjs.patch` — an auditable diff against upstream. Runtime resolution would force us to either fork the project or runtime-monkey-patch, both of which are worse.

The cost: upstream bugfixes don't auto-land. The mitigation is this file's update procedure.

## What's vendored

| Upstream path | Vendored path | Action |
|---|---|---|
| `plugins/codex/scripts/codex-companion.mjs` | `scripts/codex-cc/codex-companion.mjs` | Copy verbatim |
| `plugins/codex/scripts/app-server-broker.mjs` | `scripts/codex-cc/app-server-broker.mjs` | Copy verbatim |
| `plugins/codex/scripts/lib/*` | `scripts/codex-cc/lib/*` | Copy verbatim except `codex.mjs` |
| `plugins/codex/scripts/lib/codex.mjs` | `scripts/codex-cc/lib/codex.mjs` | Copy + apply `codex.mjs.patch` |
| `plugins/codex/scripts/session-lifecycle-hook.mjs` | — | **SKIP** (skill ships no Claude Code hooks) |
| `plugins/codex/scripts/stop-review-gate-hook.mjs` | — | **SKIP** (review-gate hook; skill drives review without a stop gate) |
| `plugins/codex/{prompts,commands,agents,hooks,schemas,skills,LICENSE,NOTICE,CHANGELOG.md,.claude-plugin/}` | — | **SKIP** (plugin-shape artifacts) |

Total vendored: 17 files (`codex-companion.mjs`, `app-server-broker.mjs`, 15 `lib/*` files including 1 TypeScript declaration).

## Pinned version

```
Source: ~/.claude/plugins/cache/openai-codex/codex/1.0.4/scripts/
Version: 1.0.4
Vendored: 2026-05-08
codex-cli verified against: 0.130.0 (last test wave; previous version 0.129.0 also exercised)
```

Captured in `scripts/codex-cc/UPSTREAM.md`. Bumped on every update. The `codex-cli verified against` line is a record of which CLI versions the vendored `codex-companion.mjs` was last smoke-tested against; bump it when you re-run the smoke tests under §"Behavioral drift" below.

## The patch

`scripts/codex-cc/codex.mjs.patch` is a unified diff against the upstream `lib/codex.mjs`. It changes three sandbox defaults:

```diff
@@ buildThreadParams (~lines 55-65) @@
   approvalPolicy: options.approvalPolicy ?? "never",
-  sandbox: options.sandbox ?? "read-only",
+  sandbox: options.sandbox ?? "danger-full-access",
   serviceName: SERVICE_NAME,

@@ buildResumeParams (~lines 70-78) @@
   approvalPolicy: options.approvalPolicy ?? "never",
-  sandbox: options.sandbox ?? "read-only"
+  sandbox: options.sandbox ?? "danger-full-access"

@@ runAppServerReview (~line 918) @@
     const thread = await startThread(client, cwd, {
       model: options.model,
-      sandbox: "read-only",
+      sandbox: "danger-full-access",
```

Each patch site has a leading comment in the patched file explaining the rationale. The patch is auditable; the diff is the only differ between us and upstream.

## Update procedure

When `openai/codex-plugin-cc` ships a new version:

```bash
SRC=~/.claude/plugins/cache/openai-codex/codex/<NEW_VERSION>/scripts
DST=<skill-root>/scripts/codex-cc

# 1. Refresh the vendored tree (deletes orphans).
rsync -av --delete \
  --exclude '*-hook.mjs' \
  "$SRC/codex-companion.mjs" "$SRC/app-server-broker.mjs" "$DST/"
rsync -av --delete "$SRC/lib/" "$DST/lib/"

# 2. Reapply the patch.
cd "$DST" && patch -p2 < codex.mjs.patch

# 3. If the patch rejects, hand-merge the three sandbox sites.
# Read the rejected hunks (*.rej), fix manually, then refresh the patch:
diff -u <SRC>/lib/codex.mjs lib/codex.mjs > codex.mjs.patch

# 4. Bump the "Pinned" table in UPSTREAM.md.

# 5. Smoke-test the dispatcher's invocations.
node <skill-root>/scripts/orchestrate-codex.mjs --help
node -e 'import("$DST/lib/state.mjs").then(m=>console.log(m.resolveStateDir(process.cwd())))'

# 6. Run validate-skills.py.
python3 <repo-root>/scripts/validate-skills.py

# 7. Commit:
git add scripts/codex-cc UPSTREAM.md
git commit -m "chore(codex-cc): bump to <new version>"
```

## What to watch for during updates

### Breaking changes upstream that affect us

The skill imports from three paths:
- `codex-cc/lib/state.mjs:resolveStateDir(cwd)` — workspace slug+hash function. If upstream changes the algorithm, our manifest path computation drifts and rescue can't find prior runs.
- `codex-cc/lib/workspace.mjs:resolveWorkspaceRoot(cwd)` — root-finding logic.
- `codex-cc/lib/args.mjs:parseArgs(...)` — the dispatcher's argv parser.

The dispatcher `orchestrate-codex.mjs` imports these explicitly. After an update:
1. Re-run `node --check <skill-root>/scripts/orchestrate-codex.mjs` — catches stale imports.
2. Re-run `bash <skill-root>/scripts/test-monitor-integration.mjs` — catches regressions in slug computation.

### Patch rejection

If `patch -p2` rejects a hunk, three causes:
- The function was renamed. Find the new name; update the patch's `@@ ... @@` header.
- The default values changed upstream (e.g. they also flipped to a different sandbox). Confirm the new default is still wrong for our purposes; if right, the patch is no-op and can be removed.
- The function was deleted entirely. Confirm the new code path; if no override is needed, drop the patch site.

### New scripts upstream

If upstream adds new files under `plugins/codex/scripts/`:
- If they're new hooks → skip (we don't ship hooks).
- If they're new lib/ helpers → vendor (rsync includes them).
- If they're new top-level dispatchers → evaluate per file. The skill currently uses `codex-companion.mjs` as the only entry; new dispatchers may not be needed.

### Removed scripts upstream

If upstream removes a `lib/*` file the dispatcher imports:
- The `node --check` will fail with a missing-import error.
- Identify the replacement; update the import in `orchestrate-codex.mjs`.
- If no replacement exists, the upstream change is incompatible and the skill needs a deeper refactor.

### Behavioral drift

Upstream may change behavior without changing the API. Smoke test after every update:
- `node <skill-root>/scripts/codex-cc/codex-companion.mjs --help` — confirm the dispatch surface looks the same.
- Trigger one rescue against a fixture manifest — confirm `task-resume-candidate` works as expected.
- Run one `single` mode task — confirm the manifest writes match the expected schema.

If any smoke test fails, surface in the upstream-bump commit message; do not ship the bump.

## Rolling back an update

If the new version misbehaves:

```bash
# Restore from git.
cd <skill-root>/scripts/codex-cc
git checkout HEAD~1 -- .

# Or, restore from the prior cached version.
SRC_OLD=~/.claude/plugins/cache/openai-codex/codex/<OLD_VERSION>/scripts
rsync -av --delete \
  --exclude '*-hook.mjs' \
  "$SRC_OLD/codex-companion.mjs" "$SRC_OLD/app-server-broker.mjs" "<skill-root>/scripts/codex-cc/"
rsync -av --delete "$SRC_OLD/lib/" "<skill-root>/scripts/codex-cc/lib/"
patch -p2 < codex.mjs.patch
```

Document the rollback in `UPSTREAM.md` so the next maintainer knows why we skipped a version.

## Anti-patterns

- Modifying vendored files outside the patch. Drift from upstream becomes invisible. Every modification belongs in the patch.
- Vendoring partially (e.g. just `codex.mjs` without the rest of `lib/`). Imports break.
- Skipping the smoke test on update. Behavioral drift is the most common cause of post-update failures.
- Not bumping `UPSTREAM.md` on update. Future audits don't know which version is in tree.
- Vendoring the hooks (`session-lifecycle-hook.mjs`, `stop-review-gate-hook.mjs`). The skill is not a plugin; hook installation is the wrong layer.
