# CLI and Org Management

*Read this when deploying to Manufact Cloud with multiple organizations or in CI.*

## Login

```bash
# Interactive device flow (default)
mcp-use login

# CI: use environment variable token
mcp-use login --api-key $MCP_USE_API_KEY

# Specify org upfront
mcp-use login --org acme-corp
```

Credentials persist in `~/.mcp-use/config.json`. Without TTY and without `--org`, login fails fast (doesn't hang).

## Organization Commands

```bash
# Show current user & active org
mcp-use whoami

# List all visible orgs
mcp-use org list

# Switch active org for subsequent commands
mcp-use org switch <org-slug>
```

Org preference is persisted. Every authenticated command includes org context in headers.

## Deploy Flags

```bash
mcp-use deploy \
  --name <server-name> \
  --org <org-slug> \
  --env KEY=value \
  --env-file .env.production \
  --yes
```

| Flag | Meaning |
|------|---------|
| `--org <slug>` | Target organization |
| `--name <name>` | Server name in dashboard |
| `--env KEY=value` | Inline env var (repeatable) |
| `--env-file <path>` | Load from file |
| `--no-github` | Upload source directly (no GitHub App) |
| `--yes` / `-y` | Non-interactive (CI mode) |
| `--root-dir <path>` | Monorepo: path to server package |

## CI Pattern

CI runners have no cached credentials:

```bash
# CI workflow
mcp-use login --api-key "$MCP_USE_API_KEY"
mcp-use deploy --org "$MCP_USE_ORG" --yes
```

Store `MCP_USE_API_KEY` in CI secrets. Track `.mcp-use/cloud/link.json` in git so redeploys reuse the same server (avoids new subdomains on each CI run).

## Project Linking

After first deploy, `.mcp-use/cloud/link.json` links to the cloud server. Commit it so future deploys update the same server, not create new ones.

```bash
git add .mcp-use/cloud/link.json
git commit -m "link: mcp-use cloud server"
```

## After Deploy

```bash
# Verify live server
mcp-use deployments list

# View deployment logs
mcp-use deployments logs <deployment-id> --build --follow
```

See `platforms/01-mcp-use-cloud.md` for complete Manufact Cloud walkthrough.
