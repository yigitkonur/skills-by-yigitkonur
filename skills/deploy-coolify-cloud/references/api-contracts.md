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

## Read & control

```
GET    /services            # list
GET    /services/{uuid}     # detail (add -s / can_read_sensitive for compose)
POST   /services/{uuid}/start | /stop | /restart
DELETE /services/{uuid}
GET    /resources           # everything with status (coolify resource list)
GET    /applications/{uuid}/logs?lines=200
```

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
