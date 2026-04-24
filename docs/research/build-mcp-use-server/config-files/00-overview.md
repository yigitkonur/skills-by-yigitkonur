# Config Files — Overview

Every file the mcp-use CLI creates or reads. Two roots:

- `.mcp-use/` — project-local, written into the `cwd` at the time of the triggering command
- `~/.mcp-use/` — user-global, under `os.homedir()`

---

## Full table

| Path | Created by | Read by | Schema source | Purpose |
|---|---|---|---|---|
| `.mcp-use/` (dir) | `mcp-use deploy` (on first success), `mcp-use generate-types`, `mcp-use dev`/`build` (session store + type gen) | All local commands that need project state | `libraries/typescript/packages/cli/src/utils/project-link.ts` (`MCP_USE_DIR = ".mcp-use"`) | Project-scoped state directory. |
| `.mcp-use/project.json` | `mcp-use deploy` on first successful deploy | Subsequent `mcp-use deploy` invocations (unless `--new`) | `project-link.ts` — `ProjectLink` interface | Links this working copy to a specific cloud deployment. See `10-project-json.md`. |
| `.mcp-use/sessions.json` | `FileSystemSessionStore` in `mcp-use` runtime + `mcp-use client` REPL | Same places, plus any server using `FileSystemSessionStore` | `libraries/typescript/packages/mcp-use/src/server/sessions/stores/filesystem.ts` — `FileSystemSessionStoreConfig` | Persistent map of `sessionId` → `SessionMetadata`. See `20-env-and-sessions.md`. |
| `.mcp-use/tool-registry.d.ts` | `mcp-use dev` (init + HMR + widget changes), `mcp-use build` (pre-typecheck, since v1.21.1), `mcp-use generate-types` | TypeScript via your project's `tsconfig.json` include | `generateToolRegistryTypes()` in `mcp-use/server` | Auto-generated tool type definitions. See `20-env-and-sessions.md`. |
| `.gitignore` (in project root) | `mcp-use deploy` appends `.mcp-use` with a `# mcp-use deployment` header comment if not already present | git | `saveProjectLink()` in `project-link.ts` | Auto-ignores the entire `.mcp-use/` directory on first deploy. |
| `~/.mcp-use/` (dir) | `mcp-use login` (first run) | `mcp-use login`, `logout`, `whoami`, `org *`, every cloud subcommand (for auth + active org) | `libraries/typescript/packages/cli/src/utils/config.ts` — `CONFIG_DIR = path.join(os.homedir(), ".mcp-use")` | User-global config directory. |
| `~/.mcp-use/config.json` | `mcp-use login` | `login` / `logout` / `whoami` / `org *` / all cloud subcommands (auth + org resolution) | `config.ts` — `McpConfig` interface | Stores `apiKey`, `apiUrl`, and active org. See `11-user-config-json.md`. |

---

## `.mcp-use/` auto-gitignore behaviour

Source: `saveProjectLink()` in `libraries/typescript/packages/cli/src/utils/project-link.ts`.

On first successful `mcp-use deploy`:

1. If `.mcp-use/` does not exist, create it.
2. Write `project.json`.
3. Open the project's `.gitignore` (create if missing).
4. If `.mcp-use` is **not** already ignored, append:
   ```
   
   # mcp-use deployment
   .mcp-use
   ```
5. Never re-appends on subsequent deploys (idempotent).

Implication: the entire `.mcp-use/` folder — including `sessions.json` and `tool-registry.d.ts` — is ignored by default. If a teammate wants tool-registry types committed, they must manually unignore `tool-registry.d.ts`.

---

## Why two roots?

- **Project-local (`.mcp-use/`)** — ties to a specific working copy. Switching projects changes which deployment you redeploy to, which session cache is active, which tool registry is in scope.
- **User-global (`~/.mcp-use/`)** — identity and active org. Shared across every project.

A single machine can simultaneously:

- Be logged in as one user (via `~/.mcp-use/config.json`)
- Have the active org set to Acme (also in `~/.mcp-use/config.json`)
- Be linked from `~/proj-a/.mcp-use/project.json` to deployment X in Acme
- Be linked from `~/proj-b/.mcp-use/project.json` to deployment Y in SideProject (requires `--org` on deploy, otherwise a redeploy will fail because active org ≠ linked deployment's org)

---

## Next.js drop-in interaction (v1.25.0)

When Next.js is detected (presence of `next.config.{js,mjs,ts}` or `next` in `package.json`):

- CLI defaults `--mcp-dir` to `src/mcp/` — reads MCP entry + resources from there.
- Auto-shims the Next.js surfaces (`server-only`, `client-only`, `next/cache`, `next/headers`, `next/navigation`, `next/server`) — widget builds fail fast if a widget transitively imports any of these.
- Next.js env cascade is loaded the same way `next dev` would (`.env.development.local` then `.env.local` then `.env.development` then `.env`), so `mcp-use dev` sees the same vars as the Next.js host.
- None of this changes the file layout of `.mcp-use/` — `tool-registry.d.ts` and `sessions.json` still live under `./.mcp-use/` relative to `cwd`.

Source: `libraries/typescript/packages/cli/src/utils/next-shims.ts`.
