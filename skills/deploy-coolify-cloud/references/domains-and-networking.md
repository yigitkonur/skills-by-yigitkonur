# Custom domains & cross-service networking

Two things you almost always need after a service exists — **give it a public domain** and **let it talk to another service** — and neither is obvious from the API. Every payload here was verified against a live Coolify Cloud 4.x.

## Expose a service publicly (custom domain + TLS)

Coolify auto-assigns a throwaway `*.sslip.io` domain on create. To pin **your** domain, set the sub-service's `fqdn` via the `urls` field — it is the **only** field that works:

```bash
# name = the compose service key (e.g. "litellm", "langfuse-web"); url = full URL with scheme.
curl -s -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"urls":[{"name":"litellm","url":"https://llm.example.com"}],
       "force_domain_override":true,"instant_deploy":true}' \
  https://app.coolify.io/api/v1/services/<uuid>
# -> 200 {"uuid":"...","domains":["https://llm.example.com"]}
```

- `instant_deploy:true` is **required** — Traefik labels + the Let's Encrypt request are (re)generated only on deploy. Set the domain without a deploy and nothing routes.
- `force_domain_override:true` reclaims a domain already held by another record (e.g. the auto `sslip.io` one). Include it when *changing* an existing domain.
- Multiple sub-services in one call: `"urls":[{"name":"web",...},{"name":"console",...}]`.
- **Rejected fields:** `{"domains":...}` and `{"fqdn":...}` both → `422 "This field is not allowed."` `domains` is a *read* field on `GET /services/{uuid}` only. Read the current value from `GET /services/{uuid}` → `.applications[].fqdn` (and `.name`, `.ports`).

### `SERVICE_FQDN_<NAME>` does NOT set the domain — it is output-only

Putting `SERVICE_FQDN_LITELLM_4000: https://llm.example.com` in the compose looks like it should pin the domain. It doesn't. Per Coolify's source, `SERVICE_FQDN_<NAME>` / `SERVICE_URL_<NAME>` are **output** variables Coolify *populates from* the stored fqdn on every deploy — the value you write is ignored/overwritten. Its only real effect is signalling "this compose service needs a web frontend." Set the domain with the `urls` PATCH above; if you read these vars in-app, `SERVICE_URL_*` carries the scheme, `SERVICE_FQDN_*` is host-only.

### Preflight or the cert silently fails

Let's Encrypt uses an **HTTP-01 challenge on port 80** (certresolver `letsencrypt`). If DNS doesn't yet resolve to the server, or `:80` is blocked, issuance fails **silently** and Traefik serves its default self-signed cert.

```bash
getent hosts llm.example.com | awk '{print $1}'      # must equal the server's public IP FIRST
# after deploy, prove a real cert issued:
echo | openssl s_client -connect llm.example.com:443 -servername llm.example.com 2>/dev/null \
  | openssl x509 -noout -issuer -dates                # issuer should be Let's Encrypt
```

For the routed port, prefer `expose: ["4000"]` over a host-published port — see `compose-authoring.md`.

## Connect two services (app ↔ sidecar, app ↔ DB in another stack)

Each Coolify service lands on its **own per-UUID Docker network**, so by default two services can't resolve each other. Two ways to bridge them:

| Approach | Reach peer as | Needs box shell? |
|---|---|---|
| **A. Shared external network** (`edge`) with aliases | `http://cli-proxy-api:8082` (clean) | ✅ — no API creates a raw docker network |
| **B. Predefined `coolify` network** (`connect_to_docker_network`) | `http://<service>-<uuid>:8082` (ugly, stable) | ❌ — pure API |

**A — shared external network** (mirrors the cross-stack pattern; clean hostnames):

```bash
docker network create edge          # once, on the box; external nets can't be made via API
```
```yaml
services:
  my-app:
    # ...
    networks:
      edge:
        aliases: [my-app]            # peers resolve http://my-app:<port>
networks:
  edge:
    external: true
```
Add the same `edge` block (with its own alias) to the **other** service's compose too. To wire a *running* container with zero downtime before you persist it: `docker network connect edge <container> --alias <name>`.

**B — predefined network** (no box access; API-only):

```bash
curl -s -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"connect_to_docker_network":true,"instant_deploy":true}' \
  https://app.coolify.io/api/v1/services/<uuid>
```
This joins the service to the shared `coolify` network; peers are reachable by their `<service>-<uuid>` container name (find it in `GET /services/{uuid}` → `.applications[].name` + the service uuid, or `docker ps`).

You do **not** add a `coolify` network just for *inbound* Traefik routing — `coolify-proxy` is already attached to every service's per-UUID network, so an `fqdn` alone is enough for the proxy to reach the container.

## Manual Traefik labels (fallback / to understand what Coolify generates)

If you must hand-wire routing, this is the label set Coolify emits for `https://llm.example.com` → container port `4000` (HTTPS + auto HTTP→HTTPS redirect). `certresolver` is literally `letsencrypt`; entrypoints are `https` and `http`:

```yaml
    expose: ["4000"]
    labels:
      - traefik.enable=true
      - traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https
      - "traefik.http.routers.https-x.rule=Host(`llm.example.com`)"
      - traefik.http.routers.https-x.entryPoints=https
      - traefik.http.routers.https-x.tls=true
      - traefik.http.routers.https-x.tls.certresolver=letsencrypt
      - traefik.http.services.https-x.loadbalancer.server.port=4000
      - "traefik.http.routers.http-x.rule=Host(`llm.example.com`)"
      - traefik.http.routers.http-x.entryPoints=http
      - traefik.http.routers.http-x.middlewares=redirect-to-https
    networks: [coolify]
networks:
  coolify:
    external: true
```

Prefer the `urls` API — the manual labels are overwritten whenever Coolify redeploys from its stored fqdn.
