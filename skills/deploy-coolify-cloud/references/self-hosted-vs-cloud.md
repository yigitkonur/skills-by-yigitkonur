# Self-hosted vs Cloud — the model, ownership, and safe teardown

Both are the *same* open-source Coolify app. The only difference is **where the control-plane brain (the Laravel app + its Postgres DB) runs.** This matters most when a box is managed by one and you're migrating to the other.

## The two brains

| | Self-hosted | Cloud (`app.coolify.io`) |
|---|---|---|
| Brain (app + Postgres) | On your box: `coolify`, `coolify-db`, `coolify-redis`, `coolify-realtime` | On coollabs infra |
| Your box holds | Everything (brain + agents + workloads) | Only **agents** (`coolify-proxy`, `coolify-sentinel`) + your workload containers + rendered compose in `/data/coolify/services/<uuid>/` |
| Source of truth | The `coolify-db` **volume on your box** — lose it = lose everything | Cloud's DB — your box is disposable / re-renderable |
| SSH trust | Coolify **generates its own** keypair and self-authorizes into `~/.ssh/authorized_keys` | Cloud **injects its** pubkey; connects from a public IP |
| Continuous telemetry | App scheduler self-SSHes to localhost (~60s, from a private IP) | `coolify-sentinel` **pushes** to `PUSH_ENDPOINT=https://app.coolify.io` |
| API introspection | `docker exec coolify php artisan route:list` — read controller source | Black box — the app container isn't yours |

## Both push identically-named agents to the box

When either brain manages a server, it deploys `coolify-proxy` (Traefik on 80/443) and `coolify-sentinel` (metrics) — **same names, same `/data/coolify/*` paths**. On a box that was self-hosted and is now Cloud-managed you cannot tell ownership by name. Diagnose it:

```bash
docker inspect <name> --format '{{.Created}}'                    # newer agents = whichever brain connected later
docker inspect coolify-sentinel --format '{{range .Config.Env}}{{println .}}{{end}}' | grep PUSH_ENDPOINT
```

**Never run both brains against one box** — they collide on host ports (both render your workload to the same `127.0.0.1:PORT`) and on `/data/coolify/services/<uuid>/` dirs.

## Migrating a service self-hosted → Cloud

1. Connect the box to Cloud (Cloud UI → Servers → Add Server) and mint an API token (Keys & Tokens).
2. Recreate the service via `POST /services` pointing at the **same host bind-mount paths**. Because auth/state lives outside Coolify's DB (see compose-authoring), nothing is re-provisioned.
3. **Verify the Cloud-managed container is healthy and serving** (see verify-and-troubleshoot) — this is where the local-image trap usually strikes, because stopping the old container can GC the `:local` image out from under the new deploy.
4. Only then tear down the self-hosted brain.

## Safe teardown — two blast radii, not one

Deleting "self-hosted Coolify" on a now-Cloud-managed box is **not** `rm -rf /data/coolify` or a whole-stack `compose down`.

**Remove (self-hosted's own brain):**
- Containers: `coolify`, `coolify-db`, `coolify-redis`, `coolify-realtime`.
- Named volumes: `coolify-db`, `coolify-redis` (`docker volume rm` — check `docker inspect --format '{{json .Mounts}}'`).
- Data dirs: `/data/coolify/{source,applications,databases,backups,ssh}` + the self-hosted service's own `services/<uuid>` dir and its docker network.
- Its self-generated SSH key: the `... coolify` line in `~/.ssh/authorized_keys`.
- Unused images (`coolify:*`, `coolify-realtime:*`, `coolify-helper:*`, and `postgres`/`redis` if nothing else needs them), build cache (`docker builder prune`), dead credential files (e.g. `~/.secrets/*coolify*`), stale CLI contexts (`coolify context delete local`).

**KEEP (now Cloud's agents / shared):**
- Containers: `coolify-proxy`, `coolify-sentinel` (+ images `traefik:*`, `sentinel:*`).
- Dirs: `/data/coolify/{proxy,sentinel,ssl}` and any *other* live resource's `services/<uuid>`.
- The `coolify` docker network **if** the surviving proxy is still attached (`docker network inspect coolify`).
- Cloud's injected SSH key in `authorized_keys`.

**Easy-to-miss remnants:** orphaned images, build cache, `~/.secrets/*coolify*`, cron/systemd units (`systemctl list-units | grep coolify`), iptables NAT for the old admin port (`iptables -t nat -L DOCKER -n | grep 8000`). Leave `/etc/docker/daemon.json` — its log-rotation limits are beneficial regardless of origin. Prove the brain is truly dead with the behavioral check in `verify-and-troubleshoot.md` (the self-SSH heartbeat stops).
