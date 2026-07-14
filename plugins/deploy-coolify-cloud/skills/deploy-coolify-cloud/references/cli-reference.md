# Coolify CLI reference and the CLI↔API boundary

Use this when deciding whether an operation goes through the `coolify` CLI or the raw REST API. The CLI (v1.x; check with `coolify version`) is excellent for discovery, deploys, and lifecycle control — but **compose-service creation and compose edits are API-only**, and two CLI behaviors will silently bite an agent (see Gotchas).

Always confirm a subcommand with `coolify <area> --help` before relying on it; the surface below is verified against CLI v1.0.3 and the public `coollabsio/coolify` OpenAPI spec.

## Global flags

`--context <name>` · `--token <token>` (one-shot override) · `--format table|json|pretty` (default `table`) · `-s/--show-sensitive` · `--debug`. The flag must precede the subcommand: `coolify --format json project list`.

## Two gotchas that cause silent failures

1. **`service list` and `service get` ignore `--format json`** — they always print the human table, regardless of flag or position. Do **not** try to parse service JSON from the CLI. For machine-readable service data (including `docker_compose_raw`), call the API: `GET /services` / `GET /services/{uuid}`.
2. **`-s` masking is table-format only.** `coolify --format json server list` returns the **real IP even without `-s`**; table mode masks it as `********` until you pass `-s`. So JSON output is *not* safe-by-default — never pipe `--format json` of servers/contexts into logs, chat, or a repo assuming secrets are hidden. Mask before sharing.

## Command tree (verified v1.0.3)

| Group (aliases) | Subcommands | Notes |
|---|---|---|
| `app` (`application(s)`) | `list`, `get`, `logs [-f] [-n]`, `start`(=`deploy`), `stop`, `restart`, `update`, `delete`, `env {list,get,create,update,delete,sync}` | Git/buildpack apps. Has `update` + full env CRUD (services do not). |
| `service` (`svc`) | `list`, `get`, `start`, `stop`, `restart`, `delete` | **No `create`, `update`, or `env`.** Read/control only. |
| `database` (`db`) | `list`, `get`, `create <type>`, `update`, `start`, `stop`, `restart`, `delete`, `backup {list,create,update,delete,trigger,executions,...}` | The one resource with near-full CLI CRUD (8 engines). |
| `deploy` | `list`, `get`, `cancel`, `uuid <uuid>`, `name <name>`, `batch <a,b,c>` | Full API parity — trigger/inspect/cancel deploys with no curl. |
| `project` (`projects`) | `list`, `get` | Read-only. Create/update/delete + environment CRUD are API-only. |
| `server` (`servers`) | `list`, `get [--resources]`, `domains`, `add`, `validate`, `remove` | Can add/validate/remove but **cannot edit** an existing server. |
| `resource` | `list` | Best unified UUID/name/type/status overview. |
| `context` | `list`, `get`, `add`, `update`, `set-token`, `set-default`, `use`, `delete`, `verify`, `version` | Local connection profiles (see below). |
| `private-key` (`key(s)`) | `list`, `add`, `remove` | No in-place update (that's API-only). |
| `github` (`gh`) | `list`, `get`, `create`, `update`, `delete`, `repos`, `branches` | Full parity. |
| `teams` | `list`, `get`, `current`, `members` | Read-only (teams have no create/update API). |
| `config` | (none) | Prints the config file path. |
| `completion` | `bash\|zsh\|fish\|powershell` | Shell completion. |
| `update`, `version`, `help` | — | `update` self-updates the CLI binary — not your service. |

## CLI vs API vs UI — decision table

| Operation | Path | Why |
|---|---|---|
| Discover servers/projects/resources/apps/databases | **CLI** (`--format json`) | Convenient; but `service list` is table-only (gotcha #1) and JSON leaks secrets (gotcha #2). |
| Read a service's `docker_compose_raw` | **API** `GET /services/{uuid}` | The CLI `service get` is a thin summary and never shows the compose. |
| Get project/environment UUIDs | **API** `GET /projects`, `GET /projects/{uuid}` | CLI `project` is list/get only; envs are nested. |
| Create a project / environment | **API** `POST /projects`, `POST /projects/{uuid}/environments` | No CLI create for projects/envs. |
| Create a docker-compose service | **API only** `POST /services` (base64 `docker_compose_raw`) | CLI `service` has no `create`. |
| Edit a compose service's source compose | **API only** `PATCH /services/{uuid}` | The CLI can't; editing the rendered on-box file is overwritten on redeploy. |
| Trigger a redeploy | **CLI** `coolify deploy uuid <uuid>` or **API** `GET /deploy?uuid=<uuid>` | Both work; CLI has full deploy parity. |
| Start / stop / restart a service | **CLI** `coolify service start\|stop\|restart <uuid>` | Full parity across app/service/database. |
| Set a compose sub-service domain/TLS | **API only** `PATCH /services/{uuid}` with `urls` | `domains`/`fqdn` fields are rejected; CLI has no service-URL setter. |
| Manage a service's env vars/secrets | **API only** `/services/{uuid}/envs` | Services have no CLI `env` (apps do). Keeps secrets in Coolify's encrypted store. |
| Manage a database (create/update/backup) | **CLI** `coolify database ...` | Near-full CLI CRUD, the exception to "create is API-only". |
| Edit an application's config | **CLI** `coolify app update <uuid> --...` | Apps have `update`; services don't. |
| Read compose-service logs | **on-box `docker logs`** | No `service logs` CLI; `/applications/{uuid}/logs` is git/buildpack apps only and 404s for a compose sub-service. |
| Manage API keys | **UI/API** | No `coolify api-key` subcommand exists. |
| Wildcard domain on a server | **UI only** | `PATCH /servers/{uuid}` rejects `wildcard_domain` — set it in Server → General. |
| Verify a deploy actually ran | **on-box Docker + real HTTP probe + `coolify resource list`** | Queue/API success is not runtime proof (`verify-and-troubleshoot.md`). |

## Context/config mechanics

`coolify config` prints the config path, typically `~/.config/coolify/config.json` (mode `600`). Format:

```json
{ "instances": [ { "default": true, "fqdn": "https://app.coolify.io", "name": "cloud", "token": "<token>" } ] }
```

- Add/point a context: `coolify context add cloud https://app.coolify.io "$COOLIFY_CLOUD_API_TOKEN"` (`-d` default, `-f` overwrite). Rotate with `coolify context set-token cloud <token>`. `context use`/`set-default` flip which instance is default.
- `coolify context verify` does a live auth check and prints the server version (e.g. `4.1.2`). Run it before any control/mutation.
- The token sits in that JSON in plaintext, and `context list` masks it in the table but `--format json`/reading the file exposes it — treat the file as a secret and never commit it. Keep the durable source in `~/.config/coolify-cloud.env` (`token-setup.md`).

## Common CLI derailments

- **Creating/editing a compose service with the CLI** — impossible; use REST `POST`/`PATCH /services`.
- **Parsing `coolify service list --format json`** — it's table-only; hit `GET /services` instead.
- **Assuming `--format json` hides secrets** — it doesn't; mask IPs/tokens before sharing.
- **`coolify app logs`/`/applications/*` for a compose sub-service** — that's the git/buildpack app model; read `docker logs` on the box.
- **Treating the CLI self-update nag as a deploy failure** — ignore, or `coolify update` the binary separately.
- **Wrong context** — pass `--context cloud` in scripts, or `coolify context verify` first.
