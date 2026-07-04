# Coolify API contracts (verified)

Coolify Cloud REST API. Base: `https://app.coolify.io/api/v1`. Header on every call:
`Authorization: Bearer $COOLIFY_CLOUD_API_TOKEN`. Self-hosted is identical at `https://<your-host>/api/v1`.

> The `coolify` CLI (v1.x) has **no service-create and no compose-edit** — only list/get/start/stop/restart/delete. Everything below that mutates a service is raw API. These payloads were confirmed against a live Coolify 4.x (`ServicesController.php`).

## Token storage & rotation

- Store the token in `~/.config/coolify-cloud.env` (`chmod 600`), one line: `export COOLIFY_CLOUD_API_TOKEN=...`. Source it from your shell rc with a comment. **Never inline it** in a compose file, script, or repo.
- Mint/rotate at `app.coolify.io` → **Keys & Tokens**. Grant read + write + deploy (root scope) — read-only can't create services.
- Rotate the CLI's stored token with `coolify context set-token <ctx> <token>` — don't hand-edit `~/.config/coolify/config.json`.
- **Connecting a server in the Cloud UI does not create or refresh an API token.** The SSH connection and the API token are separate credentials; a `401` right after "server connected" means you still need to mint the token.

## Prerequisites: project + environment + server

A service needs a `project_uuid`, an `environment_uuid` (or `environment_name`), and a `server_uuid`.

```bash
# server uuid
curl -s -H "Authorization: Bearer $TOKEN" https://app.coolify.io/api/v1/servers
# or: coolify server list -s

# create a project -> 201 {"uuid":"..."}
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"utils","description":"..."}' https://app.coolify.io/api/v1/projects

# a "production" environment is AUTO-CREATED with the project. Get its uuid:
curl -s -H "Authorization: Bearer $TOKEN" \
  https://app.coolify.io/api/v1/projects/<project-uuid> | jq '.environments[].uuid'
# POST /projects/{uuid}/environments {"name":"..."} adds more; a duplicate name -> 409
```

## Create a compose service

```
POST /api/v1/services
```

Required: `project_uuid`, `server_uuid`, one of (`environment_uuid` | `environment_name`), and **either** `type` (a one-click template name) **or** `docker_compose_raw` — never both (→ 422). `docker_compose_raw` must be **base64-encoded, valid UTF-8**, and pass command-injection validation.

```bash
B64=$(base64 -w0 compose.yml)          # macOS: base64 -i compose.yml | tr -d '\n'
python3 -c "import json;print(json.dumps({
  'project_uuid':'<proj>','environment_uuid':'<env>','server_uuid':'<server>',
  'name':'my-svc','description':'...',
  'docker_compose_raw':'''$B64''','instant_deploy':True}))" > body.json
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  --data @body.json https://app.coolify.io/api/v1/services
# -> 201 {"uuid":"<service-uuid>","domains":[]}
```

**Allowed fields** (anything else → `422 "This field is not allowed."`):
`type, name, description, project_uuid, environment_name, environment_uuid, server_uuid, destination_uuid, instant_deploy, docker_compose_raw, urls, force_domain_override, is_container_label_escape_enabled`.

## Update a service's compose

```
PATCH /api/v1/services/{uuid}
```

```bash
curl -s -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"docker_compose_raw\":\"$(base64 -w0 compose.yml)\",\"instant_deploy\":true}" \
  https://app.coolify.io/api/v1/services/<uuid>
# -> 200 {"uuid":"...","domains":[]}
```

`instant_deploy:true` is what triggers the redeploy job. Without it the DB updates but nothing redeploys.

## Set a custom domain (+ TLS)

Coolify auto-assigns a `*.sslip.io` domain on create. Pin your own via the **`urls`** field — the only one that works (`{"domains":...}` and `{"fqdn":...}` both → `422 "This field is not allowed."`):

```bash
curl -s -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"urls":[{"name":"<compose-service>","url":"https://app.example.com"}],
       "force_domain_override":true,"instant_deploy":true}' \
  https://app.coolify.io/api/v1/services/<uuid>
# -> 200 {"uuid":"...","domains":["https://app.example.com"]}
```

`name` = the compose service key (read it from `GET /services/{uuid}` → `.applications[].name`); `instant_deploy:true` regenerates the Traefik labels + Let's Encrypt request. `SERVICE_FQDN_*` env vars do **not** set the domain (they are output-only). Full workflow + DNS/TLS preflight → `domains-and-networking.md`.

## Service env vars (the secret path — don't inline them in `docker_compose_raw`)

App secrets (provider keys, master keys, DB passwords) belong here, not baked into the compose. Coolify stores them encrypted and injects them via the `env_file: .env` it adds to every service.

```
GET    /services/{uuid}/envs                # list; is_coolify:true marks Coolify's own vars
POST   /services/{uuid}/envs   -d '{"key":"OPENROUTER_API_KEY","value":"sk-...","is_preview":false}'
PATCH  /services/{uuid}/envs   -d '{"key":"...","value":"..."}'
DELETE /services/{uuid}/envs/{ENV_UUID}     # by the var's UUID, NOT its key (key -> 404)
```

## Connect to the shared network

```bash
# join the predefined `coolify` network -> reach peers by their <service>-<uuid> container name
curl -s -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"connect_to_docker_network":true,"instant_deploy":true}' \
  https://app.coolify.io/api/v1/services/<uuid>
```

Clean-hostname alternative (a shared external `edge` network) + the tradeoff → `domains-and-networking.md`.

## Watch a deploy (the queue)

Create/update responses carry only `{"uuid","domains"}` — **no deployment handle**. To tell whether the queued job (rule #1) is running or failed, poll the deployments list; there is no `/services/{uuid}/deployments`:

```
GET /deployments        # array of in-flight deploys (empty when idle)
```

## Read & control

```
GET    /services            # list
GET    /services/{uuid}     # detail (add -s / can_read_sensitive for compose)
POST   /services/{uuid}/start | /stop | /restart
DELETE /services/{uuid}
GET    /resources           # everything with status (coolify resource list)
GET    /applications/{uuid}/logs?lines=200   # git/buildpack apps only
```

> A **compose service's sub-service is NOT addressable at `/applications/{uuid}`** — that returns `404 "Application not found."` (`/applications/*` is for git/buildpack apps). For compose logs, read them on the box (`docker logs <container>`) or take state from `GET /services/{uuid}` → `.applications[]`.

## Response codes

| Code | Meaning |
|---|---|
| `200` | Success |
| `201` | Created — **job queued, NOT proof the container runs**; verify on the box |
| `401` | Unauthorized — token missing/expired/wrong scope (a UI server-connect does not refresh it) |
| `404` | Not found |
| `409` | Conflict (e.g. environment name already exists) |
| `422` | Validation error — bad field, non-base64 compose, or injection check tripped |
| `500` | Server error |

## Discovering more endpoints (self-hosted only)

The public API docs omit several fields above. On a **self-hosted** instance you can read the real routes and validation instead of guessing:

```bash
docker exec coolify php artisan route:list | grep -i services
docker exec coolify sh -c "sed -n '294,430p' /var/www/html/app/Http/Controllers/Api/ServicesController.php"
```

Cloud gives no such access — extract what you need from a throwaway self-hosted instance first, then apply it against Cloud.
