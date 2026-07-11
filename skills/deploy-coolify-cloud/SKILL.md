---
name: deploy-coolify-cloud
description: Use skill if you are deploying or updating a docker-compose service on Coolify Cloud (app.coolify.io) via its API — setting domains, connecting services, env secrets, or verifying a deploy.
---

# deploy-coolify-cloud

Deploy and update docker-compose services on **Coolify Cloud** (`app.coolify.io`) from evidence, not memory. The `coolify` CLI can start/stop/inspect/deploy but **cannot create or edit compose services** — that is raw REST API, with a few undocumented rules this skill pins down. Every contract here was verified against live Coolify Cloud behavior and the CLI/OpenAPI surface.

## Use this skill when

- deploying a **new docker-compose service** to a server managed by Coolify Cloud
- **changing a running service's compose** (image, ports, env, volumes, healthcheck)
- setting up **automatic updates** — poll an upstream image, redeploy + restart on a new version
- a deploy "**succeeded**" in the API but the container isn't up, and you need to know why
- wiring the prerequisites — **project / environment / server UUIDs** — before a service create
- first-time **token/CLI setup** on this machine (get, store, persist the API token)
- **migrating** a service between a self-hosted Coolify and Coolify Cloud
- **verifying on the box** that a Coolify deploy actually started, not just got queued

## Do NOT use this skill when

- the job is **authoring the app itself** (writing the Dockerfile / app code) rather than deploying it
- you only need to **read** status or logs and the `coolify` CLI already answers it (`coolify resource list`, `coolify service get`) — no API call needed
- deploying via **git-push / Nixpacks buildpack** rather than a docker-compose service — that is a different Coolify path, not covered here
- the target is a **self-hosted** Coolify and the question is pure dashboard UI — the compose/API mechanics still apply, but the Cloud-specific token flow and remote-deploy latency notes do not

## Non-negotiable rules

1. **A create/deploy API response (`201`/`200`) means "job queued," NOT "container running."** On Cloud the deploy job runs remotely, then SSHes into the target box; it can report API success while the container never starts. **Always verify on the box** → `references/verify-and-troubleshoot.md`.
2. **`docker_compose_raw` must be base64-encoded** in every create/update call. Raw YAML → `422`. Payloads + field rules → `references/api-contracts.md`.
3. **The `coolify` CLI cannot create or edit compose services** — it can inspect/control/deploy, but compose create/edit/env/domain work is API-only. Create = `POST /services`, edit = `PATCH /services/{uuid}`. CLI boundary → `references/cli-reference.md`.
4. **Edit the stored source compose via the API, never the rendered file on the box.** `GET /services/{uuid}` → `.docker_compose_raw` is the clean source; `/data/coolify/services/<uuid>/docker-compose.yml` is rendered output (labels/networks/env injected) and will be overwritten → `references/verify-and-troubleshoot.md`.
5. **A locally-built image (`image: foo:local`, no registry) is a singleton with no backup** — Docker/Coolify auto-cleanup deletes it and the next deploy fails `pull access denied`. Push to a registry or keep the build reproducible → `references/compose-authoring.md`.
6. **Never inline the API token** in a compose file, script, or repo. Store it once in `~/.config/coolify-cloud.env` (`chmod 600`) and source it → `references/token-setup.md`.
7. **Connecting a server in the Cloud UI does NOT mint an API token** — separate credentials. A `401` after "the server is connected" means you still need a token from **Keys & Tokens** → `references/token-setup.md`.
8. **Pin a custom domain with the `urls` API field, NOT the `SERVICE_FQDN_*` compose var** — the magic var is output-only after first create; `{"domains":...}`/`{"fqdn":...}` are rejected. DNS must resolve to the server *before* the deploy or the TLS cert silently fails → `references/domains-and-networking.md`.
9. **App secrets go in service env vars, not inlined in `docker_compose_raw`** — push them via the envs API so they live in Coolify's encrypted store and arrive through the injected `.env` → `references/api-contracts.md`.
10. **If the skill's advice seems stale, update the installed plugin — do not patch the runtime cache.** Skill fixes belong in the source repo and a pushed release; local cache edits vanish and leave other agents on old guidance.

## Setup

```bash
# One-time token setup if the token is missing or 401s:
scripts/setup-token.sh

# CLI (optional, handy for read/verify): scripts/install-coolify-cli.sh
source ~/.config/coolify-cloud.env
coolify context add cloud https://app.coolify.io "$COOLIFY_CLOUD_API_TOKEN"
coolify context verify        # ✓ Connection / ✓ Auth / ✓ version
```

Token storage (portable convention): put `export COOLIFY_CLOUD_API_TOKEN=...` in `~/.config/coolify-cloud.env` (`chmod 600`) and source it from your shell rc with a comment. If no working token exists, ask the user to mint one at **Keys & Tokens** and save it with `scripts/setup-token.sh` → `references/token-setup.md`. Never inline it.

## Deploy workflow

Run it with `scripts/deploy-compose.sh` or by hand. Steps:

1. **Gather UUIDs.** `server_uuid` (`GET /servers` or `coolify server list -s`); `project_uuid` + `environment_uuid` (`GET /projects`, then `GET /projects/{uuid}` → `.environments[].uuid`). Create a project first if needed (`POST /projects`; a `production` env is auto-created). → `references/api-contracts.md`.
2. **Author the compose** for Coolify — healthcheck, loopback binding, persistent volumes, image strategy → `references/compose-authoring.md`.
3. **Create the service.** `POST /services` with `project_uuid`, `environment_uuid`, `server_uuid`, `name`, base64 `docker_compose_raw`, `instant_deploy: true`.
4. **Verify on the box** (rule #1): container `healthy` + a real request returns 2xx, THEN confirm `coolify resource list` shows `running:healthy` (poller lags ~30–60s). → `references/verify-and-troubleshoot.md`.
5. **Expose publicly / connect services.** Pin a custom domain with the `urls` PATCH (or `scripts/set-domain.sh`) and, for an app↔sidecar/DB, join a shared network — both, with the DNS/TLS preflight, in → `references/domains-and-networking.md`.
6. **Edit later** with `PATCH /services/{uuid}` (new base64 compose + `instant_deploy: true`) — back up the current compose first (`GET .docker_compose_raw`) — then re-verify.
7. **Auto-update later** only when the service tracks a registry image: set `pull_policy: always`, poll the image digest, trigger a Coolify redeploy on change, and wait for healthy. Do **not** let Watchtower recreate Coolify-managed containers behind Coolify's back → `references/auto-update.md`.

```bash
# create
scripts/deploy-compose.sh --compose ./compose.yml --name my-svc \
  --server <server-uuid> --project <project-uuid> --env <env-uuid>
# update an existing service
scripts/deploy-compose.sh --compose ./compose.yml --service <service-uuid>
# verify it actually came up
scripts/verify-deploy.sh --uuid <service-uuid> --url http://127.0.0.1:PORT/health
```

## Decision splits — references

| Need | Read |
|---|---|
| First-time setup, missing/expired token, cross-platform env persistence, CLI context setup | `references/token-setup.md` |
| Exact API payloads: create/update service, projects, envs, control, response codes, token storage | `references/api-contracts.md` |
| What the `coolify` CLI can/cannot do, CLI quirks, `--format json`/sensitive-output gotchas | `references/cli-reference.md` |
| Writing a Coolify-friendly compose: healthcheck, loopback vs proxy, volumes, interpolation, the local-image trap | `references/compose-authoring.md` |
| Proving a deploy actually ran: `201`≠running, deploy queue, `401`, `exited`, `running:unknown`, TLS-cert failures, box-level checks | `references/verify-and-troubleshoot.md` |
| Custom domains + Let's Encrypt TLS, and connecting one service to another (sidecar/DB) over a shared network | `references/domains-and-networking.md` |
| Auto-updating a registry-backed service by polling image digests and redeploying through Coolify | `references/auto-update.md` |
| The two-brains model (self-hosted vs Cloud), ownership diagnosis, safe teardown / migration | `references/self-hosted-vs-cloud.md` |

## Scripts

- `scripts/setup-token.sh` — prompt for the Coolify API token (no shell-history leak), save it to `~/.config/coolify-cloud.env` (`chmod 600`), persist a source line in the shell rc, and verify it against the API. Works on Linux and macOS.
- `scripts/deploy-compose.sh` — base64-encode a compose and create (`POST`) or update (`PATCH`) a service with `instant_deploy`; auto-sources `~/.config/coolify-cloud.env`, reads `$COOLIFY_CLOUD_API_TOKEN`, `$COOLIFY_BASE_URL` (default `https://app.coolify.io`).
- `scripts/set-domain.sh` — pin a custom domain (+ TLS) on a compose sub-service via the `urls` API; warns if DNS doesn't resolve yet and prints the cert-verify command.
- `scripts/verify-deploy.sh` — poll a resource to `running:healthy` (with timeout) and optionally probe an endpoint for a 2xx.
- `scripts/auto-update-service.sh` — pull a registry image, compare to the running container, and on change trigger a Coolify redeploy and wait for healthy (pair with a systemd timer / launchd agent → `references/auto-update.md`).
- `scripts/install-coolify-cli.sh` — install the `coolify` CLI to `~/.local/bin`.

## Guardrails

- Never treat an API `201`/`200` as proof the container runs — verify on the box.
- Never send raw (non-base64) `docker_compose_raw` — it 422s.
- Never rely on a `:local` image with no registry surviving a prune — push it or keep it reproducible.
- Never publish an internal service on `0.0.0.0` — bind `127.0.0.1:` and route public traffic through Coolify's proxy (80/443) with an FQDN.
- Never delete `coolify-proxy` / `coolify-sentinel` on a Cloud-managed box — they are Cloud's agents.
- Never inline or commit the API token; never inline app secrets in `docker_compose_raw` — use the envs API.
- Don't try to create a service, set a domain, or change env vars with the `coolify` CLI — it can't; use the API → `references/cli-reference.md`.
- Don't parse `coolify service list --format json` — that command ignores `--format` and stays a table; and don't assume `--format json` hides secrets (it leaks IPs/tokens without `-s`) → `references/cli-reference.md`.
- Don't edit the rendered compose at `/data/coolify/services/<uuid>/` — edit the source via `PATCH /services/{uuid}`; the rendered file is regenerated on every deploy.
- Don't expect `SERVICE_FQDN_*` in the compose to set a domain — it's output-only after first create; use the `urls` PATCH.
- Don't reference `${VAR}` for a secret inside `command:`/`healthcheck:` — Coolify interpolates it at parse time (to empty); inline the literal → `references/compose-authoring.md`.
- Don't auto-update a Coolify service with Watchtower or a raw `docker` recreate — route updates through Coolify so labels/networks survive → `references/auto-update.md`.
- Don't restart host network daemons (`tailscaled`, `docker`) just to "prove" reboot-safety on a box serving live traffic — that check can cause the outage it was testing for.
- Don't blanket-use host bind-mounts for stateful non-root images (ClickHouse/MinIO/…) — they hit `Permission denied`; use named volumes.
- Don't treat a `running:unknown` on a multi-container service as broken, and don't trust an `https` domain until `openssl s_client` shows a real Let's Encrypt cert.
- Check whether you're already **on** the target box (`docker ps | grep coolify-proxy`) before reaching for SSH.
