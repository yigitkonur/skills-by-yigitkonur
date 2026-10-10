# Ingress Rules & Routing Reference

Ingress rules tell `cloudflared` how to map incoming public traffic from Cloudflare's edge to services running locally or on your private network.

---

## 1. Core Rule Structure & Evaluation Order

* **First Match Wins:** Ingress rules are evaluated from **top to bottom**. The first rule that matches both the `hostname` and the optional `path` processes the request.
* **Go Regular Expressions for `path`:** The `path` attribute is parsed using **Go regular expressions (`regexp`)**, NOT shell glob wildcards. For example, `^/v2/.*` matches any path beginning with `/v2/`, whereas `/v2/*` matches `/v2` followed by multiple slashes.
* **Path Forwarding Behavior:** `cloudflared` forwards the full URL path **as-is** to the target service; it **does NOT strip** the matched prefix. For example, a request to `https://api.example.com/v2/users` is forwarded as `GET /v2/users` to `http://localhost:8002/v2/users`. Ensure the local service expects this path.
* **Native Full-Stack Routing (No Unified Proxy Needed):** Unlike Quick Tunnels (which only forward a single port via `--url`), Named Tunnels natively route frontend SPAs and backend APIs under the same domain without any reverse proxy:
  ```yaml
  ingress:
    # 1. Route backend API and WebSocket endpoints
    - hostname: app.example.com
      path: ^/(api|auth|rest|functions)/.*
      service: http://localhost:8080

    # 2. Route frontend SPA
    - hostname: app.example.com
      service: http://localhost:3000

    # 3. Mandatory catch-all
    - service: http_status:404
  ```
* **Mandatory Catch-All:** Every `ingress` configuration **must** end with a catch-all rule that has no `hostname` or `path` filter, typically `- service: http_status:404`. Without this, `cloudflared` will refuse to start.

```yaml
ingress:
  # Specific path on a hostname (Go regex)
  - hostname: api.example.com
    path: ^/v2/.*
    service: http://localhost:8002

  # Entire hostname
  - hostname: api.example.com
    service: http://localhost:8001

  # Wildcard subdomain
  - hostname: "*.preview.example.com"
    service: http://localhost:3000

  # Mandatory catch-all
  - service: http_status:404
```

---

## 2. Supported Service Types

`cloudflared` supports multiple protocol targets:

| Protocol Prefix | Example Target | Description |
|---|---|---|
| `http://` | `http://127.0.0.1:3000` | Standard HTTP services. WebSockets and Server-Sent Events (SSE) are fully supported. |
| `https://` | `https://127.0.0.1:8443` | Proxies to local HTTPS origins. Use with `noTLSVerify: true` if self-signed. |
| `unix:` | `unix:/var/run/docker.sock` | Proxies HTTP over a local Unix domain socket. |
| `tcp://` | `tcp://localhost:5432` | Raw TCP proxying (e.g. PostgreSQL, Redis) via Cloudflare Access WARP. |
| `ssh://` | `ssh://localhost:22` | Direct browser-rendered or CLI SSH access. |
| `rdp://` | `rdp://localhost:3389` | Windows Remote Desktop via browser or WARP client. |
| `http_status:` | `http_status:404` | Returns a fixed HTTP status code without touching any local port. |

---

## 3. Origin Request Configuration (`originRequest`)

The `originRequest` block configures connection timeouts, TLS verification, and proxy behavior when `cloudflared` contacts your local origin service. It can be declared globally under root, or overridden per ingress rule.

```yaml
ingress:
  - hostname: secure-internal.example.com
    service: https://localhost:8443
    originRequest:
      connectTimeout: 10s
      tlsTimeout: 10s
      noTLSVerify: true
      originServerName: internal.corp.local
      matchSNItoHost: false
      http2Origin: true
      keepAliveTimeout: 1m30s
      keepAliveConnections: 100
      disableChunkedEncoding: false
      caPool: /etc/ssl/certs/internal-ca.pem
      access:
        required: true
        teamName: myteam
        aud:
          - 83f7a26f8d...
```

### Key Parameters:

| Parameter | Type | Default | Explanation |
|---|---|---|---|
| `connectTimeout` | duration | `30s` | Maximum time to establish the initial TCP connection to the local service. |
| `noTLSVerify` | boolean | `false` | When connecting to an `https://` origin, ignores self-signed or invalid TLS certificates. |
| `originServerName` | string | none | Overrides the SNI (Server Name Indication) sent in the TLS handshake with the origin. |
| `matchSNItoHost` | boolean | `false` | When true, automatically sets the SNI hostname to match the `Host` header. |
| `caPool` | path | system | Path to a custom Certificate Authority PEM file to verify origin TLS certificates. |
| `http2Origin` | boolean | `false` | Attempts to speak HTTP/2 directly to the origin service rather than HTTP/1.1. |
| `httpHostHeader` | string | hostname | Sets the `Host` header sent to the local server (useful for virtual hosts). |
| `keepAliveTimeout` | duration | `1m30s` | Maximum time an idle connection to origin remains open before closing. |
| `keepAliveConnections` | integer | `100` | Max idle connections to origin in the connection pool. |
| `access` | object | none | Validates Cloudflare Access JWT directly at connector level before routing to origin. |

---

## 4. Validating Ingress Configuration

Before restarting or applying changes to a live tunnel, validate that syntax, rules, and catch-all requirements are met:

```bash
# Validate default configuration (~/.cloudflared/config.yml):
cloudflared tunnel ingress validate

# Validate custom or temporary configuration (Note: --config precedes ingress):
cloudflared tunnel --config /path/to/config.yml ingress validate
```

* If valid: Exits with code 0: `Validating rules... OK`
* If invalid: Outputs exact line numbers, missing catch-alls, or overlapping path warnings.

### Rule Testing
To test how a specific URL maps against your ingress configuration without sending network traffic:

```bash
# Test URL routing rule match against default or custom config:
cloudflared tunnel ingress rule https://api.example.com/v2/users
cloudflared tunnel --config /path/to/config.yml ingress rule https://api.example.com/v2/users
# Output: Matched rule #1: service http://localhost:8002
```
