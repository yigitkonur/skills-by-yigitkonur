# `mcp-use deploy`

Deploys an MCP server to Manufact Cloud. Requires `mcp-use login` first — see `13-device-flow-login.md`.

## Usage

```bash
mcp-use deploy [options]
```

`mcp-use deploy` links a GitHub repository and creates a cloud deployment from that source. It does not upload local `dist/`; deploy works best when the project is already committed and pushed.

## Flags

| Flag | Description | Default |
|---|---|---|
| `--name <name>` | Custom deployment name | Auto-generated from project name |
| `--port <port>` | Server port | `3000` |
| `--runtime <runtime>` | `node` or `python` | `node` |
| `--open` | Open the deployment URL in a browser | `false` |
| `--new` | Force a new deployment instead of reusing a linked one | `false` |
| `--env <key=value>` | Add a single env var; repeatable | — |
| `--env-file <path>` | Load env vars from a `.env` file | — |
| `--root-dir <path>` | Root directory for monorepo deploys (v1.21.1+) | — |
| `--org <slug-or-id>` | Target org by slug or ID | active org |
| `-y, --yes` | Skip confirmation prompts | `false` |
| `--region <region>` | Deploy region: `US`, `EU`, or `APAC` | `US` |
| `--build-command <cmd>` | Override auto-detected build command | auto |
| `--start-command <cmd>` | Override auto-detected start command | auto |

For multi-org workflows, prefer `mcp-use org switch` over `--org` per command. See `08-mcp-use-org-list-and-switch.md`.

## Deploy flow

1. Detect git remote; ensure project is a GitHub repository.
2. Prompt to install the GitHub App if not already linked.
3. Create or link the cloud project (records `.mcp-use/project.json` for stable URLs across redeploys).
4. Build and deploy from the linked GitHub repo.
5. Print MCP endpoint and Inspector URLs.

`.mcp-use/project.json` is what keeps the deployment URL stable between local redeploys. The CLI writes `.mcp-use` to `.gitignore`, so treat this as local state and avoid deleting it unless you intend to relink.

## Examples

```bash
mcp-use deploy
mcp-use deploy --name my-server --open
mcp-use deploy --env DATABASE_URL=postgres://... --env API_KEY=secret
mcp-use deploy --env-file .env.production
mcp-use deploy --runtime python
mcp-use deploy --root-dir packages/my-server     # monorepo
mcp-use deploy --region EU --yes                 # non-interactive deploy
```

## Env var handling

Inline `--env` is fine for single non-secret values. For anything sensitive, use `--env-file` and keep the file out of git:

```bash
echo '.env.production' >> .gitignore
mcp-use deploy --env-file .env.production
```

Never put secrets into shell history via `--env API_KEY=sk-live-…`.

`.env` file format:

```text
MCP_SERVER_URL=https://mcp.example.com
API_KEY=sk-live-123
DATABASE_URL=postgres://...
```

## Auth gate

`mcp-use deploy` fails if you're not logged in. Run `mcp-use login` first; verify with `mcp-use whoami`. See `13-device-flow-login.md`.

## Returned URLs

After a successful deploy:

| URL | Purpose |
|---|---|
| MCP endpoint | The public `/mcp` URL clients connect to |
| Inspector | Web Inspector for the deployed instance |

Wire the MCP endpoint into client configs as `"url": "https://…/mcp"`.

## See also

- `13-device-flow-login.md` — auth before first deploy
- `08-mcp-use-org-list-and-switch.md` — multi-org workflow
- `../25-deploy/` — end-to-end deploy patterns and Docker fallback
- `../02-setup/09-env-vars.md` — env vars the running server reads
