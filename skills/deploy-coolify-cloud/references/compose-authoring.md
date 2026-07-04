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

If the image has `wget`/`curl` and an unauthenticated route, an HTTP probe is fine too — but don't probe an auth-gated route (busybox `wget` exits non-zero on a 401 and the container reads as unhealthy).

## Bind private services to loopback; publish through the proxy

- **Internal / admin services:** `ports: ["127.0.0.1:8082:8082"]`. Loopback-only means the host firewall (typically 22/80/443 in) never exposes it. Reach it over an SSH tunnel.
- **Public services:** don't publish a host port at all. Give the service an FQDN in Coolify and let its **Traefik proxy** (on 80/443) route to it with automatic Let's Encrypt TLS. Publishing `0.0.0.0:PORT` *and* routing through the proxy is a common double-exposure mistake.

## Persist state with host bind-mounts

Anything holding credentials, auth tokens, or a database must live on a **host bind-mount**, not an anonymous volume:

```yaml
    volumes:
      - /srv/my-svc/config.yaml:/app/config.yaml
      - /srv/my-svc/state:/app/state        # auth tokens, db — survives delete/recreate
```

Bind-mounts live *outside* Coolify's own database, so they survive a service delete/recreate and even a **self-hosted → Cloud migration** — recreate the service pointing at the same host paths and no credentials are re-provisioned. (Pre-create a mounted config *file* before first deploy; if the path doesn't exist Docker makes it a **directory**, and the app fails with "is a directory".)

## The local-image trap (the #1 failed-deploy cause)

`image: my-app:local` + `pull_policy: missing` + no registry = a **singleton with no backup**:

- `pull_policy: missing` means "use local if present, else pull" — but there's nothing to pull, so once the tag is gone the deploy dies with `pull access denied, repository does not exist`.
- Stopping a container can trigger Docker/Coolify image GC that deletes the tag. Coolify additionally runs `force_docker_cleanup` at a disk threshold (default 80%) — it **will** delete local-only images unattended.

**Fix — pick one:**
1. **Push to a registry** (even a private one) and reference `registry/my-app:tag` with `pull_policy: always`. Most robust.
2. **Keep the build reproducible** — commit the `Dockerfile` + source and rebuild on demand: `docker build -t my-app:local .`. Accept that a prune means a rebuild.

Never assume a `:local` tag will still exist next week on a box with automated cleanup.

## What Coolify injects

When you submit `docker_compose_raw`, Coolify re-renders it: it adds `container_name`, a per-resource network, `coolify.*` labels, `COOLIFY_*` env vars, and an `env_file: .env`. Your `image`, `ports`, `volumes`, `environment`, `restart`, and `healthcheck` are preserved. The rendered result lands on the box at `/data/coolify/services/<uuid>/docker-compose.yml` — read it there to see exactly what ran.

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
