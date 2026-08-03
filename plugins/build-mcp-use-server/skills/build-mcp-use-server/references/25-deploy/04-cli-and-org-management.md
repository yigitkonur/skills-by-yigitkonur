# CLI and Org Management

*Read this when deploying to Manufact Cloud with multiple organizations or in CI.*

## Login

```bash
# Interactive device flow (default)
mcp-use login

# CI: use environment variable token
mcp-use login --api-key "$MCP_USE_API_KEY"

# Specify org upfront
mcp-use login --org acme-corp
```

Credentials persist in `~/.mcp-use/config.json`. If the account has one resolvable/default organization, login can select it automatically. If multiple organizations remain ambiguous, a non-interactive login without `--org` fails fast instead of hanging for a selection.

## Organization Commands

```bash
# Show current user & active org
mcp-use whoami

# List all visible orgs
mcp-use org list

# Show the active org
mcp-use org current

# Switch active org for subsequent commands
mcp-use org use <org-slug>
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
| `[path]` | Project directory; defaults to the current directory |
| `--org <id-or-slug>` | Target organization (default: active organization) |
| `--name <name>` | Server name in dashboard (default: project name) |
| `--branch <name>` | Source branch (default depends on source mode: current branch, or `main`) |
| `--root-dir <path>` | Monorepo: path to server package inside the repo/upload |
| `--region <region>` | Cloud region identifier |
| `--env KEY=value` | Inline env var (repeatable) |
| `--env-file <path>` | Load env vars from a file |
| `--build-command <cmd>` | Override the detected build command |
| `--start-command <cmd>` | Override the detected start command |
| `--dockerfile <path>` | Dockerfile path relative to the selected source root |
| `--watch-paths <glob>` | GitHub auto-deploy path filter (repeatable, GitHub-only) |
| `--wait-for-ci` | Wait for other GitHub checks before auto-deploy (GitHub-only) |
| `--no-github` | Upload local source to managed storage (no GitHub App) |
| `--new` | Create a new server instead of reusing the local link |
| `--open` | Open the dashboard after a successful deployment |
| `--yes` / `-y` | Authorize confirmations and Git/repository mutations (CI mode) |
| `--json` | Emit exactly one JSON result or error; never prompt |

`--json` alone does not authorize mutations — pass `--json --yes` for headless GitHub deploys, or `--json --no-github` for a managed source upload. `--open` cannot combine with `--json` (JSON mode never opens a browser). `--new` requires `--yes` in non-interactive/JSON environments. `--watch-paths` and `--wait-for-ci` only apply to GitHub-backed deployments.

`--name`, `--region`, `--env`, `--env-file`, and other creation settings apply when a server is created. For an existing linked server, use `mcp-use servers update <server>` for supported mutable metadata/build settings and `mcp-use servers env set|unset <server> ...` for environment variables.

## CI Pattern

CI runners have no cached credentials:

```bash
# CI workflow
mcp-use login --api-key "$MCP_USE_API_KEY"
mcp-use deploy --org "$MCP_USE_ORG" --yes
```

Store `MCP_USE_API_KEY` in CI secrets. `MCP_USE_ORG` in this example is your own CI variable passed to `--org`; it is not a CLI-reserved environment variable. Track `.mcp-use/cloud/link.json` in git so redeploys reuse the same server rather than creating a separate cloud server.

## Project Linking

After first deploy, `.mcp-use/cloud/link.json` links to the cloud server. Commit it so future deploys update the same server, not create new ones.

```bash
git add -f .mcp-use/cloud/link.json
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
