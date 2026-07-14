# CLI and Organization Management

Driving `mcp-use` and `@mcp-use/cli` for multi-org Manufact Cloud accounts.

---

## 1. Login

```bash
# Interactive device-flow login (CLI 3.x)
npx mcp-use login

# Non-interactive — pick org by slug, id, or name
npx mcp-use login --org acme-corp
```

`mcp-use login` validates the stored API key against the backend before short-circuiting. Expired or revoked keys drop into device-auth automatically (since v1.25.0).

Without a TTY and without `--org`, login fails fast instead of hanging on stdin. Use `--org` in CI.

---

## 2. Org commands

```bash
# List orgs visible to the current account
npx mcp-use org list

# Switch the active org for subsequent commands
npx mcp-use org switch <slug-or-id>

# Show the active org
npx mcp-use org current

# Show the logged-in identity and active org
npx mcp-use whoami
```

Org preference is persisted in `~/.mcp-use/config.json`. Every org-scoped API request includes the `x-profile-id` header derived from that file.

---

## 3. Deploy to a specific org

```bash
npx mcp-use deploy --org acme-corp
```

Behavior when `.mcp-use/project.json` already links to a different org (since v1.25.0):

- The CLI **warns** and creates a **new** server in the requested org instead of silently redeploying to the linked one.
- To reset the link, delete `.mcp-use/project.json` and redeploy.

---

## 4. Common deploy flags

| Flag                  | Meaning                                                   |
|-----------------------|-----------------------------------------------------------|
| `--name <name>`       | Label stored in `project.json` (does not set the URL).   |
| `--port <port>`       | Server port. Default: `3000`.                             |
| `--runtime <node\|python>` | Runtime. Default: `node`.                            |
| `--env <key=value>`   | Inline env var. Repeatable.                               |
| `--env-file <path>`   | Path to `.env`.                                           |
| `--root-dir <path>`   | Monorepo support — path to the server package.            |
| `--org <slug-or-id>`  | Target org.                                               |
| `--open`              | Open the deploy URL in the browser when done.             |
| `-y` / `--yes`        | Non-interactive. Skips confirmations. Errors if not logged in. |

Example multi-flag deploy:

```bash
npx mcp-use deploy \
  --name my-server \
  --org acme-corp \
  --env DATABASE_URL=postgres://... \
  --env-file .env.production \
  --open
```

---

## 5. Server env management

Manage env vars on already-deployed cloud servers without redeploying source (since v1.24.2):

```bash
npx mcp-use servers env list <server-id>
npx mcp-use servers env create <server-id> KEY=value
npx mcp-use servers env update <server-id> KEY=newvalue
npx mcp-use servers env delete <server-id> KEY
```

---

## 6. Listing deployments

```bash
npx mcp-use deployments list
```

Output includes an ORG column (since v1.25.0) so you can disambiguate when the same name exists in multiple orgs.

---

## 7. Auth failure handling

Authenticated commands (`whoami`, `org`, `servers`, `deployments`, `env`) funnel 401 responses through a shared handler that prints:

```
session expired — run `npx mcp-use login`
```

Re-running `mcp-use login` triggers device-auth. Don't try to manually edit `~/.mcp-use/config.json`.

---

## 8. CI patterns

Treat the CI runner as a fresh machine — it has no `~/.mcp-use/config.json`.

```bash
# CI step: login non-interactively with API key
echo "$MCP_USE_API_KEY" | npx mcp-use login --token-stdin
npx mcp-use deploy --org "$MCP_USE_ORG" --yes --env-file .env.production
```

Track `.mcp-use/project.json` in git so the CI runner reuses the existing deployment subdomain. Without it, every CI deploy creates a new subdomain (see `platforms/01-mcp-use-cloud.md`).

---

See `platforms/01-mcp-use-cloud.md` for full Manufact Cloud deploy walkthrough.
