# Auth + Org — `login`, `logout`, `whoami`, `org`

Covers the authentication and multi-org selection surfaces added/expanded in v1.24.0 (device flow) and v1.25.0 (`--org` flag).

---

## `mcp-use login`

### Verbatim `--help`

```
Usage: mcp-use login [options]

Login to mcp-use cloud

Options:
  --api-key <key>       Login with an API key directly (non-interactive, for CI/CD)
  --org <slug|id|name>  Select an organization non-interactively
  -h, --help            display help for command
```

### Option table

| Flag | Purpose |
|---|---|
| `--api-key <key>` | Non-interactive login using a pre-issued key (CI/CD). Skips the device flow. |
| `--org <slug\|id\|name>` | Pick the active org without prompting. Resolved against the user's memberships. |

### Device flow behaviour (v1.24.0)

When called with **no arguments**, `mcp-use login`:

1. Opens the browser to a device-verification URL with a short user code.
2. The user approves inside `manufact.com` (web host; override via `MCP_WEB_URL`).
3. The CLI long-polls the backend (`cloud.mcp-use.com/api/v1`; override via `MCP_API_URL`) until approval.
4. On success the CLI writes the API key + org identity to `~/.mcp-use/config.json`.

On-disk result (schema from `libraries/typescript/packages/cli/src/utils/config.ts`):

```json
{
  "apiKey": "mu_live_...",
  "apiUrl": "https://cloud.mcp-use.com/api/v1",
  "orgId": "org_01H...",
  "orgName": "Acme Inc",
  "orgSlug": "acme"
}
```

### `--org <slug|id|name>` (v1.25.0)

Resolves to an org membership before writing. Accepts slug, UUID, or human-readable name. Without it and with more than one org, the CLI prompts interactively.

### `--api-key` for CI

```bash
MCP_USE_API_KEY= mcp-use login --api-key "$CI_MCP_API_KEY" --org acme
```

- Writes the same file shape as the device flow.
- Combine with `--org` to avoid interactive org selection on first run.
- In pure CI where no state should be persisted, prefer the env var `MCP_USE_API_KEY` (see below) and skip `login` entirely.

### `MCP_USE_API_KEY` env var

- Set on the shell, takes precedence over the `apiKey` stored in `~/.mcp-use/config.json`.
- Intended for ephemeral runners. The CLI still reads `orgId/orgSlug` from the config file, so for CI first-runs you usually want `--api-key` + `--org` to seed the config file once, or pass `--org` on every `deploy` call.

---

## `mcp-use logout`

```
Usage: mcp-use logout [options]

Logout from Manufact cloud

Options:
  -h, --help  display help for command
```

Clears the `apiKey` (and org fields) from `~/.mcp-use/config.json`. Keeps the file so `apiUrl` overrides and legacy fields survive. Does **not** touch `MCP_USE_API_KEY`.

---

## `mcp-use whoami`

```
Usage: mcp-use whoami [options]

Show current user information

Options:
  -h, --help  display help for command
```

Prints, at minimum:

- User's email/name (from the API)
- Active org: slug, name, id
- API endpoint in use (so you can confirm `MCP_API_URL` override is picked up)

If not authenticated, exits non-zero with a "run `mcp-use login`" hint.

---

## `mcp-use org`

```
Usage: mcp-use org [options] [command]

Manage organizations

Commands:
  list            List your organizations
  switch          Switch the active organization
  current         Show the currently active organization
```

None of the three subcommands accept options beyond `-h, --help`.

### `org list`

Prints every org the user belongs to (slug, name, id, role). Marks the currently active one.

### `org switch`

Interactive selector. Updates `orgId/orgName/orgSlug` in `~/.mcp-use/config.json`. Takes effect for the **next** CLI invocation.

### `org current`

One-line print: active org slug + name + id. Equivalent to the org portion of `whoami`.

---

## Multi-org workflow patterns

### A. Local dev, switch between orgs per project

```bash
mcp-use org switch       # pick Acme Inc
cd ~/projects/acme-mcp
mcp-use deploy           # goes to Acme

mcp-use org switch       # pick SideProject LLC
cd ~/projects/side-mcp
mcp-use deploy           # goes to SideProject
```

Note the active org is global (file in `~/`), not per-project. If two terminals deploy in parallel, the second deploy races against whichever `org switch` ran last.

### B. Per-command override (v1.25.0+)

Most cloud subcommands accept `--org <slug-or-id>` to override without mutating `config.json`:

```bash
mcp-use deploy --org acme
mcp-use servers list --org side-project
mcp-use servers env add "API_KEY=x" --server <id> --sensitive --org acme
```

This is the recommended pattern for CI: set `MCP_USE_API_KEY` + pass `--org` explicitly on every command.

### C. CI bootstrap (no interactive flow)

```bash
# In the runner, one-time per-job:
export MCP_USE_API_KEY="$SECRET_MCP_KEY"
mcp-use deploy --org acme --yes
```

Skips `login`; `MCP_USE_API_KEY` is used for the HTTP `Authorization` header. `--org` disambiguates without reading a persisted config.

---

## Source cross-reference

- `libraries/typescript/packages/cli/src/utils/config.ts` — `McpConfig`, `CONFIG_DIR`, `CONFIG_FILE`, `DEFAULT_API_URL`, `DEFAULT_WEB_URL`
- `libraries/typescript/packages/cli/src/index.ts` — `login`, `logout`, `whoami`, `org *` command wiring

## Gotchas

- `~/.mcp-use/config.json` stores the API key **in plaintext**. Match your existing posture for tools like `gh` or `npm` tokens.
- The legacy `profileId`/`profileName`/`profileSlug` fields are read for backwards compat only — the CLI migrates them into `orgId`/`orgName`/`orgSlug` on the next write. If you edit the file by hand, use the `org*` fields.
- `MCP_API_URL` normalization: the CLI trims trailing slashes and appends `/api/v1` if missing. Setting `MCP_API_URL=https://staging.mcp-use.com` and `MCP_API_URL=https://staging.mcp-use.com/api/v1/` both resolve identically.
- `--org` name matching is case-insensitive but whitespace-sensitive. Prefer slug or id in scripts.
