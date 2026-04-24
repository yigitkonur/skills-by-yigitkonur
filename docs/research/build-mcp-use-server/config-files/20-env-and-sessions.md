# `.mcp-use/sessions.json` + `.mcp-use/tool-registry.d.ts` + Env Precedence

Two auto-managed project-local files, plus the full env-var precedence story that decides which API/auth/org the CLI uses at runtime.

---

## `.mcp-use/sessions.json`

Persistent map of `sessionId` → `SessionMetadata`, written by the `FileSystemSessionStore` in the mcp-use server runtime and by `mcp-use client`.

Source: `libraries/typescript/packages/mcp-use/src/server/sessions/stores/filesystem.ts`.

### Config

```ts
export interface FileSystemSessionStoreConfig {
  path?: string;          // default: <cwd>/.mcp-use/sessions.json
  debounceMs?: number;    // default: 100
  maxAgeMs?: number;      // default: 86_400_000 (24h)
}
```

| Field | Default | Purpose |
|---|---|---|
| `path` | `<cwd>/.mcp-use/sessions.json` | Override file location. **Single-writer only** — `FileSystemSessionStore` is unsafe for concurrent multi-replica writes (race on the JSON file can lose sessions). For multi-replica deployments use `RedisSessionStore` instead. |
| `debounceMs` | `100` | Coalesces rapid writes (each session touch) into one disk write. |
| `maxAgeMs` | `86_400_000` (24h) | Entries older than this are pruned on next load. |

### On-disk shape

A single JSON object keyed by `sessionId`:

```json
{
  "sess-xyz": {
    "clientCapabilities": {},
    "clientInfo": {},
    "protocolVersion": "2025-11-25",
    "logLevel": "info",
    "lastAccessedAt": 1700000000000
  }
}
```

### Lifecycle

- **Created:** first time the `FileSystemSessionStore` or `mcp-use client` writes a session. `.mcp-use/` is created if missing.
- **Updated:** every session touch, debounced by `debounceMs`.
- **Pruned:** entries older than `maxAgeMs` are dropped on the next load.
- **Ignored by git** thanks to the `.mcp-use` entry auto-appended to `.gitignore` on first deploy.

### Gotchas

- Shared between `mcp-use client` REPL sessions and any server using `FileSystemSessionStore`. If your server uses a different store (Redis, Upstash, in-memory), this file won't exist server-side.
- The file is plain JSON, not append-only. Concurrent writes from multiple server replicas can stomp each other — use a different store for multi-replica prod.
- Stale sessions older than 24h are silently dropped. If a session disappears unexpectedly, suspect the `maxAgeMs` default first.

---

## `.mcp-use/tool-registry.d.ts`

Auto-generated `.d.ts` containing typed definitions for every tool registered on the server. Let TypeScript infer tool argument/return shapes at call sites.

### Who writes it

| Trigger | When |
|---|---|
| `mcp-use dev` | On server init, on HMR, whenever a widget file changes |
| `mcp-use build` | Before `tsc --noEmit` (since v1.21.1) — guarantees types exist when typecheck runs |
| `mcp-use generate-types` | Manual CLI command (v3.1.0 present). `--server <file>` defaults to `"index.ts"` |
| Programmatic | `generateToolRegistryTypes()` exported from `mcp-use/server` |

### Who reads it

- The project's `tsconfig.json` (pick it up via `include` — the generator writes under `.mcp-use/`, so either include `".mcp-use/**/*"` explicitly or use `"include": ["**/*"]`).
- IDE tooling that respects your `tsconfig`.

### Skip condition

Skipped when `NODE_ENV=production` for `dev` and `build`. Rationale: production container images should have a pre-generated file baked in (or not need one). `mcp-use generate-types` itself ignores `NODE_ENV` and always writes.

### Path

`.mcp-use/tool-registry.d.ts` (relative to `cwd`). Override via `-p, --path <path>` on the CLI.

### Gotchas

- Gitignored only **after the first successful `mcp-use deploy`** from this `cwd` (where `saveProjectLink()` appends `.mcp-use` to the project's `.gitignore`). **Pre-deploy**, `tool-registry.d.ts` and `sessions.json` can leak into git — add `.mcp-use/` to `.gitignore` manually before running `mcp-use dev` for the first time. If a teammate's IDE can't find tool types, make sure they ran `mcp-use dev` or `mcp-use generate-types` at least once.
- If `tsconfig.json` has a restrictive `include` that excludes `.mcp-use/`, you'll get "cannot find name" errors for the generated types. Either unrestrict the include or reference the file via a triple-slash directive in a file that's included.
- `mcp-use generate-types --server` defaults to `index.ts`. Next.js drop-in projects need `--server src/mcp/index.ts`.
- Regeneration is content-addressed; no-op if the registry hasn't changed.

---

## Env-var precedence (the complete story)

Every CLI command that hits the cloud resolves these in order.

### API key (for `Authorization: Bearer` header)

```
MCP_USE_API_KEY (env)    — highest priority
  ↓
apiKey in ~/.mcp-use/config.json
  ↓
(unauthenticated — command errors with a login hint)
```

### API URL (base for all API calls)

```
MCP_API_URL (env, normalized)   — trailing slashes trimmed, /api/v1 appended if missing
  ↓
apiUrl in ~/.mcp-use/config.json
  ↓
https://cloud.mcp-use.com/api/v1    — DEFAULT_API_URL
```

### Web URL (for `mcp-use login` device-flow browser open)

```
MCP_WEB_URL (env)
  ↓
https://manufact.com    — DEFAULT_WEB_URL
```

### Active org (for deploy, servers, deployments, ...)

```
--org <slug|id|name>  flag on the command — highest priority, no write-back
  ↓
orgSlug / orgId / orgName in ~/.mcp-use/config.json
  ↓
(single-org user: auto-selected at login time)
```

### Project deployment link (for `mcp-use deploy` without `--new`)

```
.mcp-use/project.json in cwd — if present and valid
  ↓
(no link — deploy creates a new server + deployment)
```

`--new` on `deploy` bypasses the link read; the file is still overwritten on success.

### Full matrix for one command

Example: `mcp-use deploy --org acme-inc` with `MCP_USE_API_KEY=xxx` in env, `config.json` active org set to `side-project`, `.mcp-use/project.json` linked to a `side-project` deployment.

| Resolved input | Source |
|---|---|
| API key | `MCP_USE_API_KEY` env |
| API URL | `config.json` apiUrl (or default) |
| Web URL | (not used by `deploy`) |
| Active org | `--org acme-inc` flag |
| Deployment link | `.mcp-use/project.json` — but pointed at `side-project` org |

Result: this request will 404 at the deployment link step because the active org (acme-inc) doesn't own that deployment. Fix: add `--new` to the command so the link is ignored and a fresh server gets created in acme-inc.

---

## Quick reference — "where does each config live?"

| Concern | File |
|---|---|
| Who am I? | `~/.mcp-use/config.json` (`apiKey`, identity) |
| Which org? | `~/.mcp-use/config.json` (`orgId/orgName/orgSlug`), overridable per-command with `--org` |
| Which deployment for `deploy`? | `.mcp-use/project.json` in project `cwd` |
| Which persisted sessions? | `.mcp-use/sessions.json` in project `cwd` |
| Tool types for TS? | `.mcp-use/tool-registry.d.ts` in project `cwd` |
| Staging vs prod cloud? | `MCP_API_URL` env or `config.json` `apiUrl` |
