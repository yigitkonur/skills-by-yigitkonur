# Fly.io

Long-running container deploy with persistent disks, regional pinning, and full Node APIs. Good fit when you need real sessions and stateful features.

---

## 1. Setup

```bash
brew install flyctl
fly auth login
```

Use the `Dockerfile` from `25-deploy/03-docker.md`. Fly builds the image and runs it.

---

## 2. `fly.toml`

```toml
app = "mcp-server-mytools"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "3000"
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = false   # keep alive for session state
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  size = "shared-cpu-1x"
  memory = "256mb"

[[services]]
  internal_port = 3000
  protocol = "tcp"

  [services.concurrency]
    type = "connections"
    hard_limit = 200
    soft_limit = 100

  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [[services.tcp_checks]]
    interval = "15s"
    timeout = "2s"
    grace_period = "5s"
```

Key fields:

- **`auto_stop_machines = false`** — Fly's default is to stop idle machines. For MCP, idle stops drop in-memory sessions. Either pin `auto_stop_machines = false` or use `RedisSessionStore`.
- **`min_machines_running = 1`** — keeps at least one warm.
- **`force_https = true`** — required by most MCP clients in production.

---

## 3. Secrets

Never commit secrets to `fly.toml`. Use `fly secrets`:

```bash
fly secrets set API_KEY=your-key
fly secrets set DATABASE_URL=postgres://...
fly secrets set REDIS_URL=redis://...
```

Secrets become env vars at runtime. Setting a secret triggers a rolling restart.

---

## 4. Deploy

```bash
fly launch          # first time — creates the app, generates fly.toml
fly deploy          # subsequent deploys
```

Watch the build:

```bash
fly logs
```

---

## 5. Multi-region

Fly can deploy across regions. Add to `fly.toml`:

```toml
primary_region = "iad"
```

Scale to multi-region:

```bash
fly regions add ord cdg
fly scale count 3 --region ord=1 --region cdg=1 --region iad=1
```

For multi-region MCP, **always** use a shared session store (`RedisSessionStore`). In-memory sessions are per-instance and per-region.

---

## 6. Persistent volumes (optional)

For session stores that write to disk (`FileSessionStore`):

```bash
fly volumes create mcp_data --size 1 --region iad
```

```toml
[[mounts]]
  source = "mcp_data"
  destination = "/data"
```

Volumes are region-pinned and per-machine. For multi-machine, use Redis instead.

---

## 7. Custom domain

```bash
fly certs add mcp.example.com
# Add the printed CNAME or A records to your DNS
```

After DNS propagates, `https://mcp.example.com/mcp` is live.

---

## 8. Verify

```bash
curl -s https://mcp-server-mytools.fly.dev/health | jq .
fly logs                          # tail
fly ssh console                   # shell into the running container
```

---

## 9. Sizing

- `shared-cpu-1x` / 256 MB is enough for most MCP servers without heavy compute.
- Bump memory to 512 MB+ if you cache or run any model inference.
- Watch for OOM kills with `fly logs` — Fly restarts on OOM but you'll see process churn.

---

## 10. When to pick Fly

- Need persistent in-process state.
- Want cheap multi-region deployment.
- Need full Node APIs and arbitrary native modules.
- Don't want the operational weight of GCP/AWS.

If you only need HTTP request/response with no state, Vercel/Workers are simpler.
