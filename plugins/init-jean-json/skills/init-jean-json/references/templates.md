# Templates — jean.json, .worktreeinclude, AGENTS.md section

Starting points, not answers — every line must survive Phase 1 evidence and Phase 3 testing. Delete what the repo doesn't need.

## Node / pnpm (most common)

```json
{
  "scripts": {
    "setup": "cp \"$JEAN_ROOT_PATH/.env\" . 2>/dev/null || echo '[setup] no .env at root'; cp \"$JEAN_ROOT_PATH/.env.local\" . 2>/dev/null || true; mkdir -p .claude && cp \"$JEAN_ROOT_PATH/.claude/settings.local.json\" .claude/ 2>/dev/null || true; pnpm install --prefer-offline",
    "teardown": null,
    "run": "pnpm dev"
  },
  "ports": [{ "port": 3000, "label": "Dev server" }]
}
```

```gitignore
# .worktreeinclude
.env
.env.local
.claude/settings.local.json
```

## Node / npm or yarn-classic with slow install (APFS clonefile)

```json
{
  "scripts": {
    "setup": "cp \"$JEAN_ROOT_PATH/.env\" . 2>/dev/null || true; if cp -Rc \"$JEAN_ROOT_PATH/node_modules\" ./node_modules 2>/dev/null; then echo '[setup] node_modules cloned (CoW)'; npm install --prefer-offline; else npm install; fi",
    "teardown": null,
    "run": "npm run dev"
  },
  "ports": [{ "port": 3000, "label": "Dev server" }]
}
```

`.worktreeinclude` adds `node_modules/` only in this variant.

## Multiple processes (run array)

```json
"run": ["pnpm --filter api dev", "pnpm --filter web dev", "pnpm --filter worker dev"]
```

Each array entry becomes a separate selectable Run command in Jean's toolbar. Declare each process's port in `ports[]` with a distinguishing label.

## Python / uv

```json
{
  "scripts": {
    "setup": "cp \"$JEAN_ROOT_PATH/.env\" . 2>/dev/null || true; uv sync",
    "teardown": null,
    "run": "uv run uvicorn app.main:app --reload --port 8000"
  },
  "ports": [{ "port": 8000, "label": "API" }]
}
```

(uv's global CAS cache makes `uv sync` in a fresh worktree near-instant; no venv copying needed.)

## Rust

```json
{
  "scripts": {
    "setup": "cargo fetch",
    "run": "cargo run"
  }
}
```

Optionally share build artifacts across worktrees via a per-project shared target dir (immutable-ish, cargo locks it): `"setup": "export CARGO_TARGET_DIR=\"$JEAN_ROOT_PATH/target-shared\" && cargo fetch"` — note cargo serializes concurrent builds on the lock; drop this if agents build in parallel constantly.

## Docker-compose stack

```json
{
  "scripts": {
    "setup": "cp \"$JEAN_ROOT_PATH/.env\" . 2>/dev/null || true; docker compose -p \"app-$JEAN_BRANCH\" pull --quiet 2>/dev/null || true",
    "teardown": "docker compose -p \"app-$JEAN_BRANCH\" down --remove-orphans || true",
    "run": "docker compose -p \"app-$JEAN_BRANCH\" up"
  },
  "ports": [{ "port": 8000, "label": "App" }]
}
```

For port-collision handling and shared-DB alternatives read `worktree-optimization.md` §2–3.

## Monorepo

One root `jean.json`. Scope to the actively developed surface; agents working elsewhere still get env + install:

```json
{
  "scripts": {
    "setup": "cp \"$JEAN_ROOT_PATH/.env\" . 2>/dev/null || true; pnpm install --prefer-offline",
    "run": ["pnpm --filter @acme/web dev", "pnpm --filter @acme/api dev", "pnpm turbo run dev"]
  },
  "ports": [
    { "port": 3000, "label": "web" },
    { "port": 4000, "label": "api" }
  ]
}
```

## AGENTS.md section {#agents-md-section}

Append (or merge into an existing dev-env section). Purpose: a non-Jean agent (or human) can replicate the exact bootstrap by hand.

```markdown
## Worktrees & jean.json

This repo is set up for worktree-per-task development. `jean.json` (repo root) is the
automation manifest — the Jean desktop app runs it automatically; every other agent
should replicate it manually as below.

**Creating a worktree by hand:**

    git worktree add -b <branch> ../wt-<branch>
    cd ../wt-<branch>
    # replicate jean.json setup (Jean sets these env vars automatically):
    JEAN_ROOT_PATH=<abs path to main checkout> JEAN_BRANCH=<branch> \
      sh -c '<contents of scripts.setup>'

**What travels into a worktree:** the gitignored files listed in `.worktreeinclude`
(gitignore syntax; only files that are BOTH gitignored AND listed are copied — the
setup script performs these copies from `$JEAN_ROOT_PATH`).

**Run:** `<scripts.run>` — serves on port(s): <ports table>.

**Before deleting a worktree:** run `<scripts.teardown>` (idempotent), then
`git worktree remove <path> && git branch -d <branch>`.
```

Fill every `<...>` with the repo's actual values — never ship the placeholders.
