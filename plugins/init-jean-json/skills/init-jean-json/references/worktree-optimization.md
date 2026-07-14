# Worktree creation optimization

Goal: a fresh worktree that is *usable in seconds*, not minutes, even with parallel worktrees running side by side. Apply the cheapest technique that removes the dominant cost — measure first (Phase 3 records setup wall-clock).

## 1. Dependency directories (usually the dominant cost)

Ranked strategies for `node_modules/`, `.venv/`, `vendor/`, `target/`:

| Strategy | Speed | When |
|---|---|---|
| **Store-backed install** — `pnpm install --prefer-offline`, `uv sync`, `bun install` (global cache), cargo with shared `CARGO_TARGET_DIR` | fast (secs) | Default. The package manager already dedupes globally via hardlinks/CAS; a fresh install in a new worktree is mostly linking. |
| **APFS clonefile copy** — `cp -Rc "$JEAN_ROOT_PATH/node_modules" .` | near-instant (~ms, measured 20MB in 3ms) and copy-on-write (no double disk) | macOS/APFS, npm/yarn-classic repos where install is slow, or huge `.venv`s. Files diverge safely on write. |
| **Plain `cp -R`** | slow | Last resort; only for small dirs. |
| **Symlink to root's dir** | instant but **forbidden** | Never: parallel worktrees would share mutable state (one agent's `npm install` corrupts another's run) and realpath-resolving bundlers/watchers escape the worktree. |

Detection: `cp -Rc` needs macOS + APFS. Guard in setup:

```bash
if cp -Rc "$JEAN_ROOT_PATH/node_modules" ./node_modules 2>/dev/null; then
  npm install --prefer-offline   # fast top-up for lockfile drift between branches
else
  npm install                    # non-APFS fallback
fi
```

Always top-up after cloning — the worktree's branch may have a different lockfile than the root.

### Shared immutable caches (safe to share, unlike node_modules)

Point per-worktree builds at machine-global caches via setup-exported env or committed config: pnpm store (automatic), `CARGO_HOME`/sccache, `GOMODCACHE` (automatic), `UV_CACHE_DIR` (automatic), Turborepo/Nx remote or local cache dir, Playwright browsers (`PLAYWRIGHT_BROWSERS_PATH=0` is per-project — prefer the default shared `~/Library/Caches/ms-playwright`). Rule: **share immutable content-addressed caches; never share mutable build output dirs.**

## 2. Port collisions across parallel worktrees

Jean's whole point is N worktrees at once; hardcoded ports collide. Options, in preference order:

1. **Port-per-worktree derivation** — derive a stable offset from the branch name in setup and write it into the copied `.env`:

```bash
OFFSET=$(( $(cksum <<<"$JEAN_BRANCH" | cut -d' ' -f1) % 1000 ))
PORT=$((3000 + OFFSET))
sed -i '' "s/^PORT=.*/PORT=$PORT/" .env 2>/dev/null || echo "PORT=$PORT" >> .env
echo "worktree port: $PORT"
```

   Caveat: `ports[]` in jean.json is static — declare the base port with a label noting the offset scheme, or declare the handful of common offsets. Jean also auto-detects listening ports from its terminals (`get_terminal_listening_ports`), which covers dynamic ports for ⌘+O.
2. **Framework auto-increment** — Vite/Next dev servers pick the next free port automatically; then just declare the base port and rely on Jean's listening-port detection.
3. **Single-active-stack convention** — for heavy docker-compose stacks (databases), don't parallelize the stack: teardown kills it, setup of the *next* worktree claims it (Coolify's own jean.json does `docker rm -f ...` in `run`). Document this in AGENTS.md so agents expect it.

## 3. Docker-compose per worktree

- Unique project name so stacks don't collide: `docker compose -p "app-$JEAN_BRANCH" up -d`.
- teardown: `docker compose -p "app-$JEAN_BRANCH" down --remove-orphans --volumes || true` (idempotent; `--volumes` only if data is disposable).
- DB-heavy stacks: prefer one shared dev DB + schema-per-worktree (`DB_SCHEMA=$JEAN_BRANCH` in the copied .env) over N postgres containers, when the app supports it.

## 4. Copy-set hygiene (what goes in .worktreeinclude / the setup copy-block)

Include: `.env*`, `.envrc`, `.claude/settings.local.json`, `.agents/**` local overrides, `config/secrets*`, local certs, `user.bazelrc`-style personal tool config.
Exclude: anything tracked (never copies — intersection rule), caches that regenerate (`.next/`, `dist/`, `.turbo/` — cheaper to rebuild than to copy stale), OS junk (`.DS_Store`), and other worktrees' state.
Judgment call: `node_modules/` — list it in `.worktreeinclude` only if the chosen strategy is clonefile-copy; leave it out for store-backed installs.

## 5. Monorepo gotchas found in real tests

- **Internal packages need building before apps run.** In turbo/nx monorepos, `pnpm install` alone leaves `packages/*/dist` empty and app dev commands crash with `ERR_MODULE_NOT_FOUND` on workspace deps. Add a scoped pre-build to setup — and route it through a shared cache so it's instant after the first build: `TURBO_CACHE_DIR="$JEAN_ROOT_PATH/.turbo/cache" pnpm exec turbo run build --filter='./packages/*'` (measured: 2m cold → ~4s FULL TURBO in a fresh worktree).
- **dotenv loads from the app's cwd, not the repo root.** Apps with `import "dotenv/config"` run via `pnpm --filter <app> dev` read `apps/<app>/.env`, not the root `.env`. The setup copy-block must also copy `.env` into each such app dir, or the run command fails on missing env vars. Verify where env is actually loaded (`grep -rn dotenv apps/*/src` / framework convention) — Next.js reads its own `.env.local` at the app dir, Vite at root, etc.

## 6. Setup script ordering

1. Copies/clones (ms — unblocks the agent that starts typing immediately).
2. Fast install top-up.
3. Codegen the repo needs to typecheck (`prisma generate`, `gql codegen`).
4. Slow warmups (browser downloads, docker pulls) **last** — setup runs in background, so late slow steps don't delay usefulness; or drop them and let `run` handle it lazily.

Echo a one-line marker after each stage (`echo "[setup] env copied"`) — the Setup card shows combined output, and markers make failed stages obvious.

## 7. Teardown checklist

Anything setup/run *started* that outlives the worktree directory: compose stacks (`-p` scoped), background daemons (pid files in the worktree), tunnels, watchers holding ports. Verify in Phase 3 with `lsof -i :<port>` after teardown. Idempotence rule: every line ends `|| true` or checks existence first — teardown may run against a half-set-up worktree.
