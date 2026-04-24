# Cloud Lifecycle — `deploy`, `servers`, `deployments`

The three commands that drive the cloud. Model:

- A **server** is a Git-backed deploy target (repo + root-dir + config). Owned by one org. Holds env vars.
- A **deployment** is one build+runtime instance tied to a server. Multiple deployments per server (one current, older ones restartable/deletable).
- `mcp-use deploy` from a local project creates/reuses a server, triggers a new deployment, and writes `.mcp-use/project.json` linking this working copy to that deployment.

---

## `mcp-use deploy`

### Verbatim `--help`

```
Usage: mcp-use deploy [options]

Deploy MCP server from GitHub to Manufact cloud

Options:
  --open                 Open deployment in browser after successful deploy
  --name <name>          Custom deployment name
  --port <port>          Server port (default: "3000")
  --runtime <runtime>    Runtime (node or python)
  --new                  Force creation of new deployment instead of reusing linked deployment
  --env <key=value...>   Environment variables (can be used multiple times)
  --env-file <path>      Path to .env file with environment variables
  --root-dir <path>      Root directory within repo to deploy from (for monorepos)
  --org <slug-or-id>     Deploy to a specific organization (by slug or ID)
  -y, --yes              Skip confirmation prompts
  --region <region>      Deploy region: US, EU, or APAC (default: US)
  --build-command <cmd>  Custom build command (overrides auto-detection)
  --start-command <cmd>  Custom start command (overrides auto-detection)
  -h, --help             display help for command
```

### Every flag explained

| Flag | Effect |
|---|---|
| `--open` | After success, open the deployment URL in the default browser. |
| `--name <name>` | Override auto-named deployment. Must be unique within the org. |
| `--port <port>` | Port the container should expose. Default `3000`. Match your server's `listen()`. |
| `--runtime <runtime>` | Force `node` or `python`. Auto-detected from package.json / pyproject otherwise. |
| `--new` | Ignore `.mcp-use/project.json`; always create a fresh deployment. |
| `--env <key=value...>` | Repeatable. Values are baked at deploy time into the deployment's env. |
| `--env-file <path>` | Load a `.env` file (e.g. `.env.production`). Merged with `--env` (later wins). |
| `--root-dir <path>` | For monorepos — the path inside the repo to treat as the app root. |
| `--org <slug-or-id>` | Target an org different from the currently active one. |
| `-y, --yes` | Skip all confirmation prompts. Required for non-interactive CI. |
| `--region <region>` | `US` \| `EU` \| `APAC`. Default `US`. Can only be set on the first deploy to a server. |
| `--build-command <cmd>` | Override auto-detected build command (e.g. `pnpm build`). |
| `--start-command <cmd>` | Override auto-detected start command (e.g. `node dist/server.js`). |

---

## Mandatory use cases

### 1. Deploy a brand-new server (first-ever deploy from this repo)

```bash
mcp-use deploy --yes
```

- No `.mcp-use/project.json` yet → the CLI creates a new server + a new deployment.
- On success, writes `.mcp-use/project.json` and appends `.mcp-use` to `.gitignore`.
- Subsequent `mcp-use deploy` reuses this link.

### 2. Redeploy to the same server

```bash
mcp-use deploy --yes
```

- `.mcp-use/project.json` present → CLI calls the deployments endpoint with the linked `deploymentId`, producing a new deployment on the same server.
- This is the common "I pushed code, ship it" path.

### 3. Deploy to a different org than the currently-linked one

```bash
mcp-use deploy --org side-project --new --yes
```

- `--org` targets the org explicitly.
- `--new` is required because the existing `project.json` link points at a deployment in the previous org — reusing it would 404.

### 4. Monorepo deploy with `--root-dir`

```bash
mcp-use deploy --root-dir apps/mcp-server --yes
```

- CLI treats `apps/mcp-server/` inside the repo as the app root for detection of `package.json`, lockfile, runtime.
- `.mcp-use/project.json` lives at the **current working directory**, not at `--root-dir`. Run `deploy` from the repo root so subsequent deploys reuse the link.

### 5. Deploy with env vars from `.env.production`

```bash
mcp-use deploy --env-file .env.production --yes
```

- Variables become part of the deployment's environment.
- For post-deploy edits (rotate a secret etc.), use `servers env` — see below.

### 6. Add a sensitive env var to a deployed server

```bash
mcp-use servers env add "DATABASE_URL=postgres://..." \
  --server <server-uuid> \
  --sensitive \
  --env production
```

- `--sensitive` masks the value in UI and hides it from `servers env list` by default.
- Omit `--env` to apply to all three (production, preview, development).
- Requires a redeploy to take effect: `mcp-use deployments restart <deployment-id>`.

### 7. Update an existing env var value

```bash
mcp-use servers env update <var-id> \
  --server <server-uuid> \
  --value "postgres://new-host/db"
```

- `--value` is the new value; `--env` and `--sensitive`/`--no-sensitive` are independent toggles.
- Find `<var-id>` via `mcp-use servers env list --server <id>`.

### 8. Remove an env var

```bash
mcp-use servers env remove <var-id> --server <server-uuid>
```

- No confirmation prompt on this subcommand.

### 9. List all envs with values shown

```bash
mcp-use servers env list --server <server-uuid> --show-values
```

- `--show-values` only reveals non-sensitive values. Sensitive ones stay masked even with the flag.

### 10. Restart a deployment

```bash
mcp-use deployments restart <deployment-id>
```

- Triggers a fresh deployment on the same server (not a hot reload).
- `-f, --follow` streams build logs until the deployment reaches a terminal state.

```bash
mcp-use deployments restart <deployment-id> --follow
```

### 11. Stop and start a deployment to save budget

```bash
mcp-use deployments stop <deployment-id>
# later:
mcp-use deployments start <deployment-id>
```

- `stop` halts the running instance without deleting it.
- `start` boots the previously-built artefact — no rebuild.

### 12. Follow build logs in real-time

```bash
mcp-use deployments logs <deployment-id> --build --follow
```

- `--build` switches from runtime logs to build logs.
- Drop `--build` to tail runtime stdout/stderr.
- Drop `--follow` for a one-shot dump.

### 13. Delete a bad deployment

```bash
mcp-use deployments delete <deployment-id> --yes
```

- `-y, --yes` skips the irreversibility prompt.
- Does **not** delete the server; other deployments on the same server remain.

### 14. Delete a server and all its deployments

```bash
mcp-use servers delete <server-id> --yes
```

- Irreversible: all deployments, env vars, and the server record are destroyed.
- Accepts a slug in place of the UUID where the API allows it.
- After deleting the linked server, the local `.mcp-use/project.json` becomes stale — delete it or pass `--new` on the next deploy.

---

## `mcp-use servers` — full subcommand reference

### `servers list` / `servers ls`

```
Usage: mcp-use servers list|ls [options]

Options:
  --org <slug-or-id>       Target organization (slug, id, or name)
  --limit <n>              Page size (1–100, default 50)
  --skip <n>               Offset for pagination
  --sort <field:asc|desc>  Sort (e.g. updatedAt:desc)
```

Paginate through servers. Use `--sort createdAt:desc` to find the newest; `--sort updatedAt:desc` to find recently active.

### `servers get <id-or-slug>`

```
Usage: mcp-use servers get [options] <id-or-slug>

Arguments:
  id-or-slug          Server UUID or slug

Options:
  --org <slug-or-id>  Resolve org context before fetch
```

Shows server details + the recent deployments under it. Use to find the current deployment-id to restart/logs.

### `servers delete` / `servers rm`

```
Usage: mcp-use servers delete|rm [options] <server-id>

Arguments:
  server-id           Server UUID (or slug if API accepts it)

Options:
  -y, --yes           Skip confirmation prompt
  --org <slug-or-id>  Target organization
```

Irreversible. Requires `-y` to bypass the prompt.

### `servers env` family

```
Usage: mcp-use servers env [options] [command]

Commands:
  list|ls [options]             List environment variables for a server
  add [options] <KEY=VALUE>     Add an environment variable to a server
  update [options] <var-id>     Update an existing environment variable
  remove|rm [options] <var-id>  Remove an environment variable from a server
```

#### `env list`
```
Usage: mcp-use servers env list|ls [options]

Options:
  --server <id>  Server UUID
  --show-values  Reveal non-sensitive values in output
```
Without `--show-values`, every value is masked. Sensitive vars stay masked regardless.

#### `env add`
```
Usage: mcp-use servers env add [options] <KEY=VALUE>

Arguments:
  KEY=VALUE             Variable assignment, e.g. API_KEY=abc123

Options:
  --server <id>         Server UUID
  --env <environments>  Comma-separated environments: production,preview,development (default: all)
  --sensitive           Mark the variable as sensitive (value masked in UI)
```
- Value is the literal string to the right of the first `=`. Quote shell-sensitive values: `env add "URL=https://a/b?x=1"`.
- `--env` scopes: any combination of `production`, `preview`, `development`. Default is all three.

#### `env update`
```
Usage: mcp-use servers env update [options] <var-id>

Arguments:
  var-id                Environment variable UUID

Options:
  --server <id>         Server UUID
  --value <value>       New value
  --env <environments>  New environments
  --sensitive           Mark as sensitive
  --no-sensitive        Unmark as sensitive
```
- Every option is independent — pass only what changes.
- `--sensitive` + `--no-sensitive` are mutually exclusive.

#### `env remove`
```
Usage: mcp-use servers env remove|rm [options] <var-id>

Arguments:
  var-id         Environment variable UUID

Options:
  --server <id>  Server UUID
```

---

## `mcp-use deployments` — full subcommand reference

```
Usage: mcp-use deployments [options] [command]

Commands:
  list|ls                              List all deployments
  get <deployment-id>                  Get deployment details
  restart [options] <deployment-id>    Restart a deployment (triggers a new deployment on the same server)
  delete|rm [options] <deployment-id>  Delete a deployment
  logs [options] <deployment-id>       View deployment logs
  stop <deployment-id>                 Stop a deployment
  start <deployment-id>                Start a stopped deployment
```

| Subcommand | Options | Notes |
|---|---|---|
| `list` / `ls` | none | All deployments for the active org. |
| `get` | none | Full deployment detail incl. status, URL, server. |
| `restart` | `-f, --follow` | Triggers a new deployment on the same server. Follow streams build logs. |
| `delete` / `rm` | `-y, --yes` | Irreversible. |
| `logs` | `-b, --build`, `-f, --follow` | Default is runtime logs; `--build` switches to build logs. |
| `stop` | none | Halts the instance, keeps record. |
| `start` | none | Re-launches without rebuild. |

---

## Source cross-reference

- `libraries/typescript/packages/cli/src/index.ts` — all three command wirings
- `libraries/typescript/packages/cli/src/utils/project-link.ts` — `.mcp-use/project.json` read/write
- `libraries/typescript/packages/cli/src/utils/config.ts` — org + API key resolution used by every cloud call

---

## Gotchas

- **Stale link ⇒ 404.** If you delete a server (via CLI or dashboard) and then `mcp-use deploy`, the stored `deploymentId` 404s. Fix: delete `.mcp-use/project.json` or pass `--new`.
- **`--region` is first-deploy only.** Changing region after the initial deploy requires creating a new server (`--new` + `--region EU`).
- **`--env-file` + `--env` ordering.** `--env-file` loads first; `--env` overrides. Later `--env` occurrences beat earlier ones.
- **`servers env add` runtime effect.** Editing envs does not roll running deployments. Call `mcp-use deployments restart <id>` to pick up changes.
- **`--show-values` with sensitive vars.** Sensitive vars never print values. Rotate via `env update` if you can't recall the value.
- **Monorepo working dir.** `.mcp-use/project.json` is written next to `cwd`. Run `deploy` from the same directory every time (e.g. the repo root with `--root-dir apps/x`) or you'll end up with multiple stale link files.
- **`--org` + linked project.** Passing `--org` that differs from the linked deployment's org causes the reuse path to fail. Pair with `--new`.
- **`deployments delete` vs `servers delete`.** Delete a deployment and the server keeps running (with its other deployments). Delete a server and everything under it goes.
