---
name: deploy-coolify-cloud
description: Use skill if you are deploying or updating a docker-compose service on Coolify Cloud (app.coolify.io) via its API — setting domains, connecting services, env secrets, or verifying a deploy.
---

# deploy-coolify-cloud

Deploy and update docker-compose services on **Coolify Cloud** (`app.coolify.io`) from evidence, not memory. The `coolify` CLI can start/stop/inspect but **cannot create or edit** a service — that is raw REST API, with a few undocumented rules this skill pins down. Every contract here was verified against a live instance.

## Use this skill when

- deploying a **new docker-compose service** to a server managed by Coolify Cloud
- **changing a running service's compose** (image, ports, env, volumes, healthcheck)
- a deploy "**succeeded**" in the API but the container isn't up, and you need to know why
- wiring the prerequisites — **project / environment / server UUIDs** — before a service create
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
3. **The `coolify` CLI cannot create or edit services** — only list/get/start/stop/restart/delete. Create = `POST /services`, edit = `PATCH /services/{uuid}`.
4. **A locally-built image (`image: foo:local`, no registry) is a singleton with no backup** — Docker/Coolify auto-cleanup deletes it and the next deploy fails `pull access denied`. Push to a registry or keep the build reproducible → `references/compose-authoring.md`.
5. **Never inline the API token** in a compose file, script, or repo. Store it as an env file sourced from your shell → `references/api-contracts.md`.
6. **Connecting a server in the Cloud UI does NOT mint an API token** — separate credentials. A `401` after "the server is connected" means you still need a token from **Keys & Tokens**.
7. **Pin a custom domain with the `urls` API field, NOT the `SERVICE_FQDN_*` compose var** — the magic var is output-only and won't set your domain; `{"domains":...}`/`{"fqdn":...}` are rejected. DNS must resolve to the server *before* the deploy or the TLS cert silently fails → `references/domains-and-networking.md`.
8. **App secrets go in service env vars, not inlined in `docker_compose_raw`** — push them via the envs API so they live in Coolify's encrypted store and arrive through the injected `.env` → `references/api-contracts.md`.

## Setup

```bash
# CLI (optional, handy for read/verify): scripts/install-coolify-cli.sh
coolify context add cloud https://app.coolify.io "$COOLIFY_CLOUD_API_TOKEN"
coolify context verify        # ✓ Connection / ✓ Auth / ✓ version
```

Token storage (portable convention): put `export COOLIFY_CLOUD_API_TOKEN=...` in `~/.config/coolify-cloud.env` (`chmod 600`) and source it from your shell rc with a comment. Never inline it.

## Deploy workflow

Run it with `scripts/deploy-compose.sh` or by hand. Steps:

1. **Gather UUIDs.** `server_uuid` (`GET /servers` or `coolify server list -s`); `project_uuid` + `environment_uuid` (`GET /projects`, then `GET /projects/{uuid}` → `.environments[].uuid`). Create a project first if needed (`POST /projects`; a `production` env is auto-created). → `references/api-contracts.md`.
2. **Author the compose** for Coolify — healthcheck, loopback binding, persistent volumes, image strategy → `references/compose-authoring.md`.
3. **Create the service.** `POST /services` with `project_uuid`, `environment_uuid`, `server_uuid`, `name`, base64 `docker_compose_raw`, `instant_deploy: true`.
4. **Verify on the box** (rule #1): container `healthy` + a real request returns 2xx, THEN confirm `coolify resource list` shows `running:healthy` (poller lags ~30–60s). → `references/verify-and-troubleshoot.md`.
5. **Expose publicly / connect services.** Pin a custom domain with the `urls` PATCH (or `scripts/set-domain.sh`) and, for an app↔sidecar/DB, join a shared network — both, with the DNS/TLS preflight, in → `references/domains-and-networking.md`.
6. **Edit later** with `PATCH /services/{uuid}` (new base64 compose + `instant_deploy: true`) — back up the current compose first (`GET .docker_compose_raw`) — then re-verify.

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
| Exact API payloads: create/update service, projects, envs, control, response codes, token storage | `references/api-contracts.md` |
| Writing a Coolify-friendly compose: healthcheck, loopback vs proxy, volumes, the local-image trap | `references/compose-authoring.md` |
| Proving a deploy actually ran: `201`≠running, deploy queue, `401`, `exited`, `running:unknown`, TLS-cert failures, box-level checks | `references/verify-and-troubleshoot.md` |
| Custom domains + Let's Encrypt TLS, and connecting one service to another (sidecar/DB) over a shared network | `references/domains-and-networking.md` |
| The two-brains model (self-hosted vs Cloud), ownership diagnosis, safe teardown / migration | `references/self-hosted-vs-cloud.md` |

## Scripts

- `scripts/deploy-compose.sh` — base64-encode a compose and create (`POST`) or update (`PATCH`) a service with `instant_deploy`; reads `$COOLIFY_CLOUD_API_TOKEN`, `$COOLIFY_BASE_URL` (default `https://app.coolify.io`).
- `scripts/set-domain.sh` — pin a custom domain (+ TLS) on a compose sub-service via the `urls` API; warns if DNS doesn't resolve yet and prints the cert-verify command.
- `scripts/verify-deploy.sh` — poll a resource to `running:healthy` (with timeout) and optionally probe an endpoint for a 2xx.
- `scripts/install-coolify-cli.sh` — install the `coolify` CLI to `~/.local/bin`.

## Guardrails

- Never treat an API `201`/`200` as proof the container runs — verify on the box.
- Never send raw (non-base64) `docker_compose_raw` — it 422s.
- Never rely on a `:local` image with no registry surviving a prune — push it or keep it reproducible.
- Never publish an internal service on `0.0.0.0` — bind `127.0.0.1:` and route public traffic through Coolify's proxy (80/443) with an FQDN.
- Never delete `coolify-proxy` / `coolify-sentinel` on a Cloud-managed box — they are Cloud's agents.
- Never inline or commit the API token; never inline app secrets in `docker_compose_raw` — use the envs API.
- Don't try to create a service, set a domain, or change env vars with the `coolify` CLI — it can't; use the API.
- Don't expect `SERVICE_FQDN_*` in the compose to set a domain — it's output-only; use the `urls` PATCH.
- Don't blanket-use host bind-mounts for stateful non-root images (ClickHouse/MinIO/…) — they hit `Permission denied`; use named volumes.
- Don't treat a `running:unknown` on a multi-container service as broken, and don't trust an `https` domain until `openssl s_client` shows a real Let's Encrypt cert.
- Check whether you're already **on** the target box (`docker ps | grep coolify-proxy`) before reaching for SSH.
