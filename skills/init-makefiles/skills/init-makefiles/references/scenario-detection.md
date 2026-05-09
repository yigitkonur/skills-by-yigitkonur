# Scenario detection — classify before you scaffold

Pick exactly one scenario per project (or per app, in monorepos). Run the signal commands top-to-bottom, take the first match, and stop. Ambiguity is resolved with one targeted question — never a guess.

## How to read this file

For each scenario A–G:
- **Primary signals** — must be present. If any one of these matches, the scenario is in play.
- **Secondary signals** — nice-to-have evidence; raises confidence but isn't load-bearing.
- **Exclusion signals** — must NOT be present. If any of these match, it's a different scenario.
- **Typical deps** — exact `package.json` keys (or equivalent) you expect to see.
- **Typical config files** — what to check for on disk.

All commands assume the project root as `cwd`. Replace nothing — copy and paste.

## Scenario A — Frontend-only

| Field | Value |
|---|---|
| Primary signals | `next.config.{js,ts,mjs}` exists; OR `vite.config.{js,ts}`; OR `astro.config.*`; OR `nuxt.config.*`; OR `svelte.config.*`; OR `remix.config.*`; OR `app/` + `page.tsx`; OR `pages/` + `_app.{js,tsx}` |
| Secondary signals | `.vercel/` directory present; `vercel.json`; `public/` static dir; `next-env.d.ts` |
| Exclusion signals | `apps/api`, `apps/server`, `services/` with HTTP framework deps; `supabase/` dir; `*.xcodeproj`; `Cargo.toml` at root; `@modelcontextprotocol/sdk` in deps |
| Typical deps | `next`, `react`, `react-dom`; OR `vite`, `vue`/`svelte`; OR `astro` |
| Typical configs | `next.config.ts`, `tsconfig.json`, `tailwind.config.*`, `postcss.config.*`, `vercel.json` (optional) |

```bash
# Primary detection
ls next.config.* vite.config.* astro.config.* nuxt.config.* svelte.config.* remix.config.* 2>/dev/null
find . -maxdepth 2 -name 'app' -type d -exec ls {}/page.tsx {}/page.ts {}/page.jsx {}/page.js \; 2>/dev/null
find . -maxdepth 2 -name 'pages' -type d -exec ls {}/_app.* \; 2>/dev/null

# Exclusions — refuse Scenario A if any of these match
find . -maxdepth 3 -path ./node_modules -prune -o -name 'package.json' -print | \
  xargs -I {} jq -r 'select(.dependencies.express or .dependencies.hono or .dependencies.fastify or .dependencies.koa or .dependencies["@nestjs/core"]) | input_filename' {} 2>/dev/null
ls supabase/config.toml 2>/dev/null
ls *.xcodeproj *.xcworkspace 2>/dev/null
jq -r '.dependencies | keys[]?' package.json 2>/dev/null | grep -E 'modelcontextprotocol|^mcp-use$'
```

## Scenario B — MCP server (local-facing service)

| Field | Value |
|---|---|
| Primary signals | `@modelcontextprotocol/sdk` in `dependencies`; OR `mcp-use` in deps; OR `package.json` `bin` field points at an MCP entry; OR `Server` constructor from MCP SDK in source |
| Secondary signals | `bin` script in `package.json`; `src/index.ts` exports an MCP `Server`; entry script ends with `server.connect(transport)` |
| Exclusion signals | Public HTTP framework signals beyond MCP transport; `next.config.*`; `vite.config.*`; `apps/api`; `supabase/` dir; `.xcodeproj` |
| Typical deps | `@modelcontextprotocol/sdk`, `zod`, optionally `mcp-use` |
| Typical configs | `tsconfig.json`, `package.json` with a `bin` field, `mcp.json` (optional) |

```bash
# Primary
jq -r '.dependencies | keys[]?' package.json 2>/dev/null | grep -E 'modelcontextprotocol|^mcp-use$'
jq -r '.bin' package.json 2>/dev/null
grep -RIl --include='*.ts' --include='*.js' '@modelcontextprotocol/sdk' src/ 2>/dev/null | head -3

# Exclusions
ls next.config.* vite.config.* 2>/dev/null
find apps server services -maxdepth 2 -name 'package.json' 2>/dev/null
```

## Scenario C — Frontend + custom backend

| Field | Value |
|---|---|
| Primary signals | A signals (any) AND a backend dir (`apps/api`, `apps/server`, `services/<name>`, `server/`) with HTTP framework deps in its `package.json` |
| Secondary signals | `turbo.json`; `pnpm-workspace.yaml` listing both `apps/web` and `apps/api`; root `package.json` has `workspaces` array; `railway.toml` in the backend dir |
| Exclusion signals | `supabase/` dir (would make it D unless backend is *also* present, in which case ask); only one app dir; backend has no HTTP deps |
| Typical deps | Frontend: `next` (or A-equivalent); backend: `express`, `hono`, `fastify`, `koa`, `@nestjs/core`, `tsx` |
| Typical configs | `turbo.json`, `pnpm-workspace.yaml`, `apps/web/`, `apps/api/`, `apps/api/railway.toml` |

```bash
# Primary
ls next.config.* vite.config.* 2>/dev/null  # frontend
find apps server services -maxdepth 2 -name 'package.json' 2>/dev/null | while read f; do
  jq -r 'select(.dependencies | (has("express") or has("hono") or has("fastify") or has("koa") or has("@nestjs/core"))) | input_filename' "$f"
done

# Secondary
ls turbo.json pnpm-workspace.yaml 2>/dev/null
jq -r '.workspaces' package.json 2>/dev/null
```

## Scenario D — Frontend + Supabase

| Field | Value |
|---|---|
| Primary signals | A signals AND `@supabase/supabase-js` (or `@supabase/ssr`) in deps AND `supabase/` dir (or `supabase/config.toml`) |
| Secondary signals | `supabase/migrations/` with at least one `.sql`; `supabase/functions/`; `src/db/types.ts`; `.env.local` with `NEXT_PUBLIC_SUPABASE_URL` |
| Exclusion signals | A custom backend dir with HTTP framework deps (would make it C+D — ask) |
| Typical deps | `@supabase/supabase-js`, `@supabase/ssr`, `next` |
| Typical configs | `supabase/config.toml`, `supabase/migrations/`, `supabase/functions/`, `next.config.*` |

```bash
# Primary
ls supabase/config.toml 2>/dev/null
jq -r '.dependencies | keys[]?' package.json 2>/dev/null | grep -E '^@supabase/'
ls next.config.* vite.config.* 2>/dev/null

# Secondary
ls supabase/migrations 2>/dev/null
ls supabase/functions 2>/dev/null
```

## Scenario E — Multi-service Railway backend

| Field | Value |
|---|---|
| Primary signals | No frontend deps at root (or frontend lives in a separate repo); AND multiple service dirs (`apps/api`, `apps/worker`, `apps/cron`); OR multiple `railway.toml` files; OR project declared as Railway monorepo |
| Secondary signals | `Dockerfile` per service; `prisma/`; `bullmq` / `bull` in worker deps; `node-cron` / cron-runner in cron service deps |
| Exclusion signals | `next.config.*` at root; only one service dir; `supabase/` dir (Supabase belongs to D); `*.xcodeproj` |
| Typical deps | Per-service: `express`/`hono`/`fastify`, `bullmq`, `pg`/`prisma`, `ioredis` |
| Typical configs | `apps/api/railway.toml`, `apps/worker/railway.toml`, `apps/cron/railway.toml`, optional root `turbo.json` |

```bash
# Primary
find . -maxdepth 4 -name 'railway.toml' -not -path './node_modules/*' 2>/dev/null
ls apps/api apps/worker apps/cron services/* 2>/dev/null
ls next.config.* 2>/dev/null  # absent expected

# Secondary
find apps services -maxdepth 2 -name 'Dockerfile' 2>/dev/null
find apps services -maxdepth 2 -name 'package.json' -exec \
  jq -r 'select(.dependencies | (has("bullmq") or has("bull") or has("node-cron"))) | input_filename' {} \; 2>/dev/null
```

## Scenario F — Build-artifact app (no remote)

| Field | Value |
|---|---|
| Primary signals | `Cargo.toml`; OR `go.mod`; OR `Package.swift` WITHOUT a macOS app target; OR `CMakeLists.txt`; OR `Makefile.am`. AND no HTTP framework. AND no deploy target in scope. |
| Secondary signals | `src/main.rs`; `cmd/<name>/main.go`; `Sources/<name>/main.swift`; release binary path matches a CLI convention (`bin/`, `target/release/`) |
| Exclusion signals | `package.json` with a web framework; `next.config.*`; `apps/api`; `supabase/`; `*.xcodeproj` with a real GUI app target |
| Typical deps (Rust) | `clap`, `anyhow`, `tokio` (CLI); for Go: `cobra`, `urfave/cli` |
| Typical configs | `Cargo.toml`, `go.mod`, `Package.swift`, `CMakeLists.txt` |

```bash
# Primary
ls Cargo.toml go.mod Package.swift CMakeLists.txt Makefile.am 2>/dev/null

# Distinguish F (CLI) vs G (Mac app) when Package.swift is present
grep -E 'platforms|macOS|\.executable|\.app' Package.swift 2>/dev/null | head

# Exclusions
ls next.config.* vite.config.* 2>/dev/null
find apps server services -maxdepth 2 -name 'package.json' 2>/dev/null
```

## Scenario G — MacBook artifact transfer

| Field | Value |
|---|---|
| Primary signals | `*.xcodeproj` / `*.xcworkspace` directory; OR `Package.swift` with macOS target; OR `package.json` with `electron-builder` / `electron-forge` and a `mac` builder block. AND user has indicated remote-Mac target (or `Host macbook` in `~/.ssh/config`) |
| Secondary signals | `Info.plist` with `CFBundleName`; `.app` build outputs in `build/Release/` or `out/<name>-darwin-*/`; entitlements file; signed/notarized release script |
| Exclusion signals | No `~/.ssh/config` entry for a Mac alias AND user hasn't named one (Scenario G requires a remote target — without it, fall back to F) |
| Typical deps (Electron) | `electron-builder`, `electron-forge`, `electron` |
| Typical configs | `*.xcodeproj/project.pbxproj`, `Package.swift` (macOS target), `forge.config.*`, `electron-builder.yml`, `Info.plist` |

```bash
# Primary
ls *.xcodeproj *.xcworkspace Package.swift 2>/dev/null
jq -r '.devDependencies | keys[]?' package.json 2>/dev/null | grep -E 'electron-builder|electron-forge|^electron$'
grep -E 'platforms|\.macOS|\.app' Package.swift 2>/dev/null | head

# SSH alias (skill assumes alias is already configured)
grep -iE '^Host macbook' ~/.ssh/config 2>/dev/null
ssh -G macbook 2>/dev/null | awk '/^hostname / {print $2}'   # not literally "macbook" → alias resolved
```

## Decision tree (single-app projects, first match wins)

```
1. *.xcodeproj OR Package.swift (macOS target) OR electron-builder?
   YES → Mac alias exists or user named one?
         YES → Scenario G
         NO  → Scenario F  (build local; no ship)
   NO → continue
2. Cargo.toml / go.mod / CMakeLists.txt / Makefile.am AND no web framework?
   YES → Scenario F
   NO → continue
3. @modelcontextprotocol/sdk OR mcp-use OR MCP Server constructor in src?
   YES → Scenario B
   NO → continue
4. Frontend signals AND supabase/ dir?
   YES → custom backend dir also present?
         YES → ask (C+D ambiguity, see below)
         NO  → Scenario D
   NO → continue
5. Frontend signals AND backend dir with HTTP framework?
   YES → Scenario C
   NO → continue
6. Frontend signals only (no backend dir, no Supabase)?
   YES → Scenario A
   NO → continue
7. Multiple service dirs / multiple railway.toml / no frontend?
   YES → Scenario E
   NO → ambiguous → ask the catch-all question (below)
```

## Monorepo branching rule

If the repo is a monorepo (`apps/` or `packages/` plus `pnpm-workspace.yaml` / `turbo.json` / `nx.json` at root):

1. Run the decision tree against EACH app directory independently. Each app gets its own scenario tag.
2. Pick the **dominant scenario** for the root Makefile (usually the highest-traffic public-facing app — frontend > backend > tooling).
3. Generate one root `Makefile` plus up to three app sub-Makefiles, each scoped to its app. The root delegates via `$(MAKE) -C apps/<name> <target>`. See `makefile-base.md` for the helper convention and the monorepo reference for delegation patterns.
4. If the monorepo has more than four apps total, ask the user to pick three for now. The "max 4 Makefiles" ceiling is hard.

```bash
# Monorepo signal
ls pnpm-workspace.yaml turbo.json nx.json 2>/dev/null
jq -r '.workspaces' package.json 2>/dev/null
ls apps/ packages/ 2>/dev/null

# Per-app classification
for dir in apps/*/; do
  printf '\n=== %s ===\n' "$dir"
  ( cd "$dir" && ls package.json railway.toml supabase/config.toml 2>/dev/null )
done
```

## Common ambiguous cases

The agent **never guesses**. It asks one binary or short-list question, waits for the answer, then proceeds. Each prompt below follows the pattern: "I see X. Does Y? (y/n)" or "I see X. Is it (a) … or (b) …?".

### 1. Next.js + `apps/api` (Express) + Turborepo

> "I see Next.js plus `apps/api` with Express. Does `apps/api` deploy to Railway, or is it a worker invoked from Supabase only? (a) Railway / (b) Supabase-only / (c) something else"

Pick: (a) → Scenario C; (b) → not Scenario C — usually D with workers folded into Supabase Edge Functions; (c) → ask follow-up.

### 2. Next.js + `supabase/` + a backend dir

> "I see Next.js + Supabase + a custom backend at `apps/api`. Does the backend deploy to Railway in addition to Supabase, or is `apps/api` only a build-time script? (a) deploys to Railway / (b) build-time only"

Pick: (a) → C+D combined (rare; treat as C with Supabase added) — surface explicitly; (b) → Scenario D.

### 3. `Package.swift` with both CLI and macOS targets

> "I see `Package.swift` declares both a CLI target and a macOS app target. Which is the primary deliverable: (a) the CLI / (b) the macOS app?"

Pick: (a) → Scenario F; (b) → Scenario G if remote-Mac alias exists, else F with `make ship` deferred.

### 4. Mac project with web view embedded

> "I see a macOS app and `apps/web`. Does the app embed `apps/web` via WKWebView, or are they independent products? (a) embedded / (b) independent"

Pick: (a) → Scenario G primary; the web app is a build-time dependency, no Vercel deploy. (b) → both — pick primary scenario for the root, generate sub-Makefiles for each.

### 5. MCP server + a public HTTP route

> "I see `@modelcontextprotocol/sdk` and an HTTP server endpoint. Is this (a) local-only MCP / (b) hosted-MCP over HTTP+SSE?"

Pick: (a) → Scenario B; (b) → defer to `build-mcp-use-server` (hosted-MCP patterns) and refuse to generate generic deploy targets.

### 6. `railway.toml` at root + `next.config.ts` at root (single repo, no monorepo split)

> "I see `railway.toml` and `next.config.ts` at the same root. Is the Next.js app deployed to (a) Vercel / (b) Railway as a single service?"

Pick: (a) → Scenario A (Vercel) — `railway.toml` is leftover or for a related-but-deferred service; ask if it should be removed. (b) → Scenario C with the frontend self-hosted (rare; surface that `output: 'standalone'` plus `0.0.0.0:$PORT` are required).

### 7. No clear signals (catch-all)

> "I couldn't classify this project from on-disk signals. Is it primarily: (a) a web frontend / (b) a backend service / (c) a CLI tool / (d) a Mac app / (e) an MCP server / (f) something else (please describe)?"

Map: (a) → A; (b) → C or E depending on follow-up; (c) → F; (d) → G; (e) → B; (f) → ask follow-up to identify.

## Rules for asking

- **Ask once.** One question per ambiguity. Don't chain three questions before generating.
- **Binary or short-list.** y/n, or labelled options (a)/(b)/(c). Avoid open-ended prompts.
- **State what you saw.** "I see X" up front so the user can correct misperception in the same answer.
- **Never guess silently.** When ambiguous, refuse to start generation until the user answers. The cost of a guess is regenerating the wrong Makefile and burning the snapshot commit.

## Pre-generation checklist

After classifying:

- [ ] Scenario tag recorded (A–G)
- [ ] If monorepo: per-app tags recorded; dominant scenario picked for root; ≤3 sub-Makefile slots assigned
- [ ] Exclusion signals double-checked (no Supabase config in a C-tagged repo without Supabase deps; no `*.xcodeproj` in an F-tagged repo)
- [ ] Disambiguation answered if any ambiguous case applied
- [ ] User informed of the chosen scenario before any file is written
