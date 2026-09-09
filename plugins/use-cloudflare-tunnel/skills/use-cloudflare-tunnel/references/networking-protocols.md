# Tunnel Networking Protocols: QUIC vs HTTP/2

Understanding and configuring transport protocols ensures reliable tunnel connectivity across various firewall and cloud network environments.

---

## 1. Protocol Comparison: QUIC (UDP) vs HTTP/2 (TCP)

Cloudflared connects to Cloudflare edge data centers using either **QUIC (HTTP/3 over UDP)** or **HTTP/2 (over TCP)**.

| Feature | QUIC (Default) | HTTP/2 (Fallback) |
|---|---|---|
| **Underlying Transport** | UDP (Destination port 7844) | TCP (Destination port 443) |
| **Multiplexing** | Stream-level (zero Head-of-Line blocking) | Connection-level (packet loss stalls all streams) |
| **Connection Migration**| Supported (resilient to client IP changes) | Not supported (disconnects on IP change) |
| **Firewall Friendliness**| Often blocked by strict corporate firewalls | Universally allowed on standard HTTPS port 443 |
| **CPU / Performance** | Lower latency, higher throughput | Slightly higher latency on packet loss |

---

## 2. When to Force HTTP/2

By default, `cloudflared` attempts to connect over QUIC. If UDP traffic is dropped or blocked by firewalls, security groups, or ISP filters, the tunnel connection will fail or hang during the handshake.

### Symptoms of QUIC Blocking:
* Tunnel logs show: `UDP Connectivity: FAIL` or `failed to dial to edge with quic`.
* Frequent connection retry loops every few seconds.
* High latency or packet drop on local VPN connections.

### Solution: Force HTTP/2 Protocol
Pass `--protocol http2` explicitly in the command line or configuration file:

```bash
cloudflared tunnel --protocol http2 --url http://127.0.0.1:8080
```

In `config.yml`:
```yaml
tunnel: <UUID>
credentials-file: /etc/cloudflared/<UUID>.json
protocol: http2

ingress:
  - hostname: app.example.com
    service: http://localhost:8080
  - service: http_status:404
```

---

## 3. Pre-Checks and Startup Latency

When `cloudflared` starts, it performs connectivity pre-checks against Cloudflare edge servers (`region1.v2.argotunnel.com` and `region2.v2.argotunnel.com`) testing DNS, UDP, TCP, and Cloudflare API reachability.

### Speeding Up Startup in Automated Environments
In CI/CD, unit tests, or ephemeral subagent runs, connectivity pre-checks can add 3–5 seconds to startup. You can safely bypass them with `--no-prechecks`:

```bash
cloudflared tunnel --no-prechecks --url http://127.0.0.1:8080
```

---

## 4. ICMP Socket Warnings in Docker Containers

When running `cloudflared` as the root user inside Docker containers, you may see this warning in logs:
```
WRN The user running cloudflared process has a GID that is not within ping_group_range.
WRN ICMP proxy feature is disabled error="cannot create ICMPv4 proxy: Group ID 0 is not between ping group"
```

### Impact:
* **Completely harmless for HTTP/HTTPS/WebSocket tunnels.**
* This only disables ICMP ping proxying through Cloudflare WARP private virtual networks.
* Standard web traffic, APIs, and quick tunnels function 100% normally.

---

## 5. Firewall Egress Rules

If running in a locked-down network or VPC, ensure outbound rules allow:

| Port | Protocol | Destination | Purpose |
|---|---|---|---|
| **7844** | UDP | `*.v2.argotunnel.com` | QUIC tunnel transport (preferred) |
| **443** | TCP | `*.v2.argotunnel.com` | HTTP/2 tunnel transport (fallback) |
| **443** | TCP | `api.cloudflare.com` | Tunnel registration and authentication |
