# Authoring a docker-compose service for Coolify

What Coolify does to your compose, and the four things that bite first-time deploys.

## Always define a healthcheck

Without a container healthcheck, Coolify reports the service as `running:unknown` **forever** (it's running, but Coolify has no signal to call it healthy). Add one to every service. A dependency-free TCP probe (works in any image with bash):

```yaml
    healthcheck:
      test: ["CMD-SHELL", "bash -lc 'exec 3<>/dev/tcp/127.0.0.1/<port>'"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 20s
```

If the image has `wget`/`curl` and an unauthenticated route, an HTTP probe is fine too — but don't probe an auth-gated route (busybox `wget` exits non-zero on a 401 and the container reads as unhealthy). **Use `127.0.0.1`, not `localhost`, in an HTTP probe** — busybox `wget` resolves `localhost` to IPv6 `::1` first, and an app bound to IPv4 `0.0.0.0` refuses it, so the container reads unhealthy forever while serving fine.

## Bind private services to loopback; publish through the proxy

- **Internal / admin services:** `ports: ["127.0.0.1:8082:8082"]`. Loopback-only means the host firewall (typically 22/80/443 in) never exposes it. Reach it over an SSH tunnel.
- **Public services:** don't publish a host port at all — use `expose: ["4000"]` for the routed port and give the service an FQDN so its **Traefik proxy** (80/443) routes to it with automatic Let's Encrypt TLS (→ `domains-and-networking.md`). Publishing `0.0.0.0:PORT` *and* routing through the proxy is a common double-exposure mistake. A loopback publish (`127.0.0.1:4000:4000`) is fine as a *temporary* handle for local `curl` while verifying — switch it to `expose` once the FQDN is live.
- **Multi-network bind gotcha:** if the app respects a bind-host env var (Next.js/Node read `HOSTNAME`) and you attach it to a second network (e.g. a shared `edge`), it may bind **one** interface's IP instead of all — then the host port, peers, *and* the internal healthcheck all fail. Set `HOSTNAME: "0.0.0.0"` (or the app's equivalent) so it binds every interface.

## Persist state with host bind-mounts

Anything holding credentials, auth tokens, or a database must live on a **host bind-mount**, not an anonymous volume:

```yaml
    volumes:
      - /srv/my-svc/config.yaml:/app/config.yaml
      - /srv/my-svc/state:/app/state        # auth tokens, db — survives delete/recreate
```

Bind-mounts live *outside* Coolify's own database, so they survive a service delete/recreate and even a **self-hosted → Cloud migration** — recreate the service pointing at the same host paths and no credentials are re-provisioned. (Pre-create a mounted config *file* before first deploy; if the path doesn't exist Docker makes it a **directory**, and the app fails with "is a directory".)

**Caveat — non-root images crash-loop on bind-mounts.** A bind-mount to a root-owned host dir fails `Permission denied` for any image that runs as a **non-root** user (ClickHouse `uid 101`, MinIO, Grafana, Elasticsearch…) — it can't write the dir and restart-loops. Either `chown` the host dir to the container's UID first, or use a **named volume**, which Docker creates with the correct ownership. Rule of thumb: bind-mounts for credential/config **files** you pre-create and control; **named volumes** for a non-root service's data dir. (Postgres/Redis tolerate bind-mounts because they run as root / chown on init — don't generalize from them.)

## The local-image trap (the #1 failed-deploy cause)

`image: my-app:local` + `pull_policy: missing` + no registry = a **singleton with no backup**:

- `pull_policy: missing` means "use local if present, else pull" — but there's nothing to pull, so once the tag is gone the deploy dies with `pull access denied, repository does not exist`.
- Stopping a container can trigger Docker/Coolify image GC that deletes the tag. Coolify additionally runs `force_docker_cleanup` at a disk threshold (default 80%) — it **will** delete local-only images unattended.

**Fix — pick one:**
1. **Push to a registry** (even a private one) and reference `registry/my-app:tag` with `pull_policy: always`. Most robust.
2. **Keep the build reproducible** — commit the `Dockerfile` + source and rebuild on demand: `docker build -t my-app:local .`. Accept that a prune means a rebuild.

Never assume a `:local` tag will still exist next week on a box with automated cleanup.

## Coolify eats `${VAR}` in your compose at parse time

Coolify performs its **own** variable substitution on `docker_compose_raw` before the container runs — using Coolify's environment, not the container's. A `${REDIS_PASSWORD}` you expect Docker to pass through is resolved (to empty, if Coolify doesn't have it) at deploy time, silently blanking the value. This bites hardest in `command:` and `healthcheck.test:` (e.g. a Redis `--requirepass ${REDIS_PASSWORD}` becomes `--requirepass` with no argument → auth disabled, or a healthcheck logs in with an empty password).

**Fix:** escape the dollar sign so Docker/Coolify leaves it for the container runtime, or move the logic into an entrypoint script that reads the environment inside the container:

```yaml
environment:
  REDIS_PASSWORD: ${REDIS_PASSWORD:?set in Coolify envs}
command: ["sh", "-c", "redis-server --requirepass \"$$REDIS_PASSWORD\""]
healthcheck:
  test: ["CMD-SHELL", "redis-cli -a \"$$REDIS_PASSWORD\" ping"]
```

`$$VAR` is the important part: Compose-style interpolation collapses `$$` to a literal `$` for the container command. When in doubt, read the rendered file at `/data/coolify/services/<uuid>/docker-compose.yml` to see what the value actually became.

## What Coolify injects

When you submit `docker_compose_raw`, Coolify re-renders it: it adds `container_name`, a per-resource network, `coolify.*` labels, `COOLIFY_*` env vars, and an `env_file: .env`. Your `image`, `ports`, `volumes`, `environment`, `restart`, and `healthcheck` are preserved. The rendered result lands on the box at `/data/coolify/services/<uuid>/docker-compose.yml` — read it there to see exactly what ran.

Two injected vars are **output-only**: `SERVICE_FQDN_<name>` / `SERVICE_URL_<name>` are filled *from* the service's stored fqdn on every deploy — a value you write there is ignored (set domains via the API → `domains-and-networking.md`). Keep app **secrets** out of this compose too: push them as service env vars so they live in Coolify's encrypted store and arrive via the injected `.env` → `api-contracts.md`.

## Minimal example

```yaml
services:
  my-svc:
    image: registry.example.com/my-svc:1.4.0
    pull_policy: always
    environment:
      TZ: UTC
    ports:
      - "127.0.0.1:8082:8082"
    volumes:
      - /srv/my-svc/config.yaml:/app/config.yaml
      - /srv/my-svc/state:/app/state
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "bash -lc 'exec 3<>/dev/tcp/127.0.0.1/8082'"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 20s
```
