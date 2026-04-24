# `~/.mcp-use/config.json`

User-global config: API key + active org + (optionally) overridden API endpoint. Written by `mcp-use login`, mutated by `mcp-use org switch`, consumed by every cloud subcommand.

Source: `libraries/typescript/packages/cli/src/utils/config.ts`.

---

## Schema

```ts
export interface McpConfig {
  apiKey?: string;
  apiUrl?: string;
  orgId?: string;
  orgName?: string;
  orgSlug?: string;
  // Legacy/deprecated (read for backcompat, never written by v3.1.0+):
  profileId?: string;
  profileName?: string;
  profileSlug?: string;
}
```

Constants exported from the same file:

| Constant | Value |
|---|---|
| `CONFIG_DIR` | `path.join(os.homedir(), ".mcp-use")` |
| `CONFIG_FILE` | `path.join(CONFIG_DIR, "config.json")` |
| `DEFAULT_API_URL` | `process.env.MCP_API_URL` (normalized — trailing slashes trimmed, `/api/v1` appended if missing) **or** `https://cloud.mcp-use.com/api/v1` |
| `DEFAULT_WEB_URL` | `process.env.MCP_WEB_URL` **or** `https://manufact.com` |

Example on-disk content after a fresh login:

```json
{
  "apiKey": "mu_live_xxxxxxxxxxxxxxxxxxxx",
  "apiUrl": "https://cloud.mcp-use.com/api/v1",
  "orgId": "org_01HZABCDEF...",
  "orgName": "Acme Inc",
  "orgSlug": "acme"
}
```

---

## Fields

| Field | Role | Populated by |
|---|---|---|
| `apiKey` | Bearer token for all cloud API calls | `mcp-use login` (device flow or `--api-key`) |
| `apiUrl` | Pinned API base URL for this config. If unset, falls through to `DEFAULT_API_URL`. | `mcp-use login` when `MCP_API_URL` is set at login time |
| `orgId` | UUID of the active org | `login` (first/only org auto-selected; multi-org prompts) or `org switch` |
| `orgName` | Display name of the active org | Same as `orgId` |
| `orgSlug` | URL-safe slug | Same as `orgId` |
| `profileId` / `profileName` / `profileSlug` | **Legacy.** Pre-rename equivalents of `orgId/orgName/orgSlug`. | Read only; migrated to `org*` on next write. Never written by v3.1.0+. |

---

## Lifecycle

### When it's created

- First successful `mcp-use login` (both device flow and `--api-key`).
- The CLI ensures `~/.mcp-use/` exists, then writes `config.json` with `apiKey` + org identity.

### When it's updated

| Trigger | Fields changed |
|---|---|
| `mcp-use login` | `apiKey`, `orgId`, `orgName`, `orgSlug`, sometimes `apiUrl` |
| `mcp-use logout` | `apiKey` (and org fields) cleared; file kept so any `apiUrl` override survives |
| `mcp-use org switch` | `orgId`, `orgName`, `orgSlug` only |
| Any other command reading a legacy `profile*` field | On-the-fly migration to `org*` on the next write-triggering command |

### When it's read

- Every cloud subcommand — to pick up auth + active org.
- Flags like `--org <slug-or-id>` on `deploy`/`servers`/`deployments` override `orgSlug`/`orgId` for that one invocation only (no write back).
- `MCP_USE_API_KEY` env var overrides `apiKey` at request time (no write back).

---

## Env var overrides

| Env var | Overrides | Effect |
|---|---|---|
| `MCP_USE_API_KEY` | `apiKey` | Used in the `Authorization` header for that process only. Does not touch `config.json`. Ideal for CI. |
| `MCP_API_URL` | `apiUrl` + default | Normalizes input: strips trailing slashes and appends `/api/v1` if missing. Useful against staging (`MCP_API_URL=https://staging.mcp-use.com`). |
| `MCP_WEB_URL` | web host default | Changes where `mcp-use login` device flow opens the browser. Default `https://manufact.com`. |

Precedence for the API key:

```
MCP_USE_API_KEY  >  config.json apiKey
```

Precedence for the API URL:

```
MCP_API_URL env (normalized)  >  config.json apiUrl  >  https://cloud.mcp-use.com/api/v1
```

Precedence for the active org:

```
--org <flag on the command>  >  config.json orgId/orgSlug
```

---

## Default endpoints

- Backend API: `https://cloud.mcp-use.com/api/v1` — the HTTP API the CLI talks to for login/deploy/servers/deployments.
- Web dashboard: `https://manufact.com` — the browser URL for device-flow approval and the human-facing dashboard.

Both are overridable via the env vars above; this is how point releases route traffic to staging.

---

## Hand-editing — OK?

Mostly yes, with care:

- Safe: rotate `apiKey` manually after revoking it server-side, flip `apiUrl`, change `orgSlug/orgId/orgName` all together.
- Dangerous: leaving `orgId` pointing at one org but `orgSlug` pointing at another — some code paths prefer id, others prefer slug. If you edit, change all three (or run `mcp-use org switch` instead).
- Legacy: if you see `profileId/profileName/profileSlug` keys only, the file is pre-rename. Run any CLI command to force a migration write (e.g. `mcp-use whoami`).

---

## Gotchas

- Plaintext secret storage. Same posture as `~/.gh/config`, `~/.npmrc`. On shared machines, prefer `MCP_USE_API_KEY` and don't run `login`.
- `logout` keeps the file (just clears credentials). Delete `~/.mcp-use/config.json` manually if you need a truly clean slate.
- `MCP_API_URL` with a path beyond the host (e.g. `https://x.example.com/custom`) still gets `/api/v1` appended unless the path already ends in `/api/v1`. Check `mcp-use whoami` to confirm the final resolved URL.
- Setting `MCP_API_URL` only in a subshell and then running `login` bakes the override into `apiUrl` on disk, surviving shells that don't export the env var. To undo, re-login without the env var set or edit `apiUrl` out of the file.
