# Verify a deploy actually ran — and troubleshoot when it didn't

## The core rule: API success ≠ running container

`POST /services` and `PATCH /services/{uuid}` return `201`/`200` the moment the deploy job is **enqueued**. On Cloud that job then runs on coollabs' infra and SSHes into your box — so the API can report success while the container never started (missing image, bad compose, port clash). **A status code is a claim, not proof.**

**Tip — you may already be on the box.** On a Cloud-managed *self-hosted* server, the machine you're working from is often the target itself. Check before reaching for SSH:

```bash
hostname; docker ps --format '{{.Names}}' | grep -q coolify-proxy && echo "on the Coolify box"
```

If so, you have direct `docker logs` / `docker exec` / `docker network` for every check below.

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

## Watch the deploy job (before the container exists)

Create/update return **no deployment handle** (just `{"uuid","domains"}`), so poll the queue to see the job in flight (rule #1). There is no `/services/{uuid}/deployments`:

```bash
GET /deployments        # array of in-flight deploys; [] = nothing running
```

An errored job (bad compose, image-build failure) also **leaves** the queue — so a drained queue is *not* success, only "no longer running." Always confirm the container with the checklist above.

## Status meanings

| Status | Means | Do |
|---|---|---|
| `running:healthy` | Up, healthcheck passing | ✅ done |
| `running:unhealthy` | Up, healthcheck **failing** | read logs; fix the app or the healthcheck route |
| `running:unknown` | Up, but **≥1 container lacks a healthcheck** — common on multi-container compose (e.g. a worker) | **not necessarily broken.** Trust per-container `docker inspect --format '{{.State.Health.Status}}' <container>` + a real request; add a healthcheck to *every* container to make the aggregate read `healthy` |
| `exited` | Container crashed / deploy failed | `docker ps -a` + `docker logs`; usually image or compose error |

## Common failures → fixes

- **`exited` right after create, `docker ps -a` shows it gone, deploy "succeeded":** the image couldn't be resolved. On the box: `cd /data/coolify/services/<uuid> && docker compose up -d` reproduces the real error. If it's `pull access denied, repository does not exist` you hit the local-image trap — rebuild the image or push it to a registry (see compose-authoring), then redeploy.
- **`401 Unauthorized` from the API:** token missing/expired/wrong scope. Connecting the server in the UI does **not** mint a token — create one at Keys & Tokens, then `coolify context set-token cloud <token>` and update `~/.config/coolify-cloud.env`.
- **`422` on create/update:** `docker_compose_raw` wasn't base64, or you sent both `type` and `docker_compose_raw`, or an extra field. Re-check against `api-contracts.md`.
- **Stuck `running:unknown`:** a container has no healthcheck — Coolify can't confirm health. On a *single*-container service, add one and `PATCH`. On a *multi*-container compose it just means one container (often a worker) has none — verify the real one per-container (`docker inspect … .State.Health.Status`) and don't treat `unknown` as failure.
- **HTTPS serves a wrong/self-signed cert, or the domain 404s:** the Let's Encrypt HTTP-01 challenge failed — DNS must resolve to the server IP and `:80` must be reachable *before* the deploy that sets the domain. Fix DNS, re-set the domain with `instant_deploy:true` (→ `domains-and-networking.md`), then prove issuance: `echo | openssl s_client -connect <host>:443 -servername <host> 2>/dev/null | openssl x509 -noout -issuer -dates` (issuer should be Let's Encrypt).
- **Port already allocated:** another container (or a second Coolify "brain") already publishes that host port — see `self-hosted-vs-cloud.md`. Free it or change the port.
- **Coolify shows healthy but the app 500s:** the container is up (healthcheck may be a bare TCP probe) but the app is misconfigured — trust the real request (step 2) over the status.

## Before you PATCH a running service — back up its compose

`PATCH … instant_deploy:true` recreates the container **immediately** (brief downtime + risk of a bad edit taking it down). Save the current compose first so a revert is one call away:

```bash
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/services/<uuid>" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["docker_compose_raw"])' > compose.bak.yml
```

## Proving a teardown (the negative case)

When you *remove* something, verify the absence behaviorally, not just by `docker ps`. Example: a self-hosted Coolify brain self-SSHes into its own host every ~60s from a private IP. After deleting it, confirm those logins **stopped** — a removed-but-lingering process would still be knocking:

```bash
journalctl _COMM=sshd-session --since "15 min ago" | grep -c "<that-private-ip>"   # want: 0
```
