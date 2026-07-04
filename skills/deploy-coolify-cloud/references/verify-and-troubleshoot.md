# Verify a deploy actually ran — and troubleshoot when it didn't

## The core rule: API success ≠ running container

`POST /services` and `PATCH /services/{uuid}` return `201`/`200` the moment the deploy job is **enqueued**. On Cloud that job then runs on coollabs' infra and SSHes into your box — so the API can report success while the container never started (missing image, bad compose, port clash). **A status code is a claim, not proof.**

## Verification checklist (run all four)

1. **Container is up and healthy** on the box:
   ```bash
   docker ps --filter "name=<svc>" --format "table {{.Names}}\t{{.Status}}"   # want: Up … (healthy)
   ```
2. **A real request succeeds** — hit the actual endpoint, not just the port:
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $KEY" http://127.0.0.1:<port>/<route>
   ```
3. **Logs show expected startup** (not a crash loop):
   ```bash
   docker logs --tail 20 <container>
   ```
4. **Coolify's own view agrees** — its poller lags ~30–60s, so poll:
   ```bash
   until coolify resource list | grep <svc> | grep -q running:healthy; do sleep 4; done
   ```

## Status meanings

| Status | Means | Do |
|---|---|---|
| `running:healthy` | Up, healthcheck passing | ✅ done |
| `running:unhealthy` | Up, healthcheck **failing** | read logs; fix the app or the healthcheck route |
| `running:unknown` | Up, **no healthcheck defined** | add a healthcheck to the compose (see compose-authoring) |
| `exited` | Container crashed / deploy failed | `docker ps -a` + `docker logs`; usually image or compose error |

## Common failures → fixes

- **`exited` right after create, `docker ps -a` shows it gone, deploy "succeeded":** the image couldn't be resolved. On the box: `cd /data/coolify/services/<uuid> && docker compose up -d` reproduces the real error. If it's `pull access denied, repository does not exist` you hit the local-image trap — rebuild the image or push it to a registry (see compose-authoring), then redeploy.
- **`401 Unauthorized` from the API:** token missing/expired/wrong scope. Connecting the server in the UI does **not** mint a token — create one at Keys & Tokens, then `coolify context set-token cloud <token>` and update `~/.config/coolify-cloud.env`.
- **`422` on create/update:** `docker_compose_raw` wasn't base64, or you sent both `type` and `docker_compose_raw`, or an extra field. Re-check against `api-contracts.md`.
- **Stuck `running:unknown`:** the compose has no healthcheck — Coolify can't confirm health. Add one and `PATCH`.
- **Port already allocated:** another container (or a second Coolify "brain") already publishes that host port — see `self-hosted-vs-cloud.md`. Free it or change the port.
- **Coolify shows healthy but the app 500s:** the container is up (healthcheck may be a bare TCP probe) but the app is misconfigured — trust the real request (step 2) over the status.

## Proving a teardown (the negative case)

When you *remove* something, verify the absence behaviorally, not just by `docker ps`. Example: a self-hosted Coolify brain self-SSHes into its own host every ~60s from a private IP. After deleting it, confirm those logins **stopped** — a removed-but-lingering process would still be knocking:

```bash
journalctl _COMM=sshd-session --since "15 min ago" | grep -c "<that-private-ip>"   # want: 0
```
