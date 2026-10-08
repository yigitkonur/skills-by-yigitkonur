# Tunnel Networking Protocols: QUIC vs HTTP/2

Understanding and configuring transport protocols ensures reliable tunnel connectivity across various firewall and cloud network environments.

---

## 1. Protocol Comparison & The `auto` Default

Modern `cloudflared` defaults to `--protocol auto`, which automatically negotiates the best available transport protocol (testing QUIC over UDP port 7844, and gracefully falling back to HTTP/2 over TCP port 7844).

| Feature | QUIC (HTTP/3 over UDP) | HTTP/2 (over TCP) |
|---|---|---|
| **Underlying Transport** | **UDP (Destination port 7844)** | **TCP (Destination port 7844)** |
| **Multiplexing** | Stream-level (zero Head-of-Line blocking) | Connection-level (packet loss stalls streams) |
| **Connection Migration**| Supported (resilient to client IP changes) | Not supported (reconnects on IP change) |
| **Firewall Requirement**| Outbound UDP port 7844 allowed | Outbound TCP port 7844 allowed |
| **CPU / Performance** | Lower latency, higher throughput | Slightly higher latency on lossy links |

> [!IMPORTANT]
> **Port 7844 is required for BOTH protocols.** A common misconception is that HTTP/2 connects on standard port 443. Both QUIC and HTTP/2 data plane tunnels terminate at Cloudflare edge on destination **port 7844**. Port 443 is used strictly for control plane API calls (`api.cloudflare.com`).

---

## 2. When to Force HTTP/2

While `--protocol auto` handles fallback automatically, you can explicitly force HTTP/2 if UDP egress on port 7844 is blocked by strict enterprise firewall policies:

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

## 3. Pre-Checks, Diagnostics & Startup Latency

When `cloudflared` starts, it performs connectivity pre-checks against Cloudflare edge servers (`region1.v2.argotunnel.com` and `region2.v2.argotunnel.com`) testing DNS, UDP, TCP, and Cloudflare API reachability.

### Speeding Up Startup in Automated Environments
In CI/CD or ephemeral subagent runs, connectivity pre-checks can add 2–4 seconds to startup. You can bypass them with `--no-prechecks`:
```bash
cloudflared tunnel --no-prechecks --url http://127.0.0.1:8080
```

### Comprehensive Network Diagnostics (`cloudflared tunnel diag`)
To verify edge connectivity, port 7844 reachability, and generate a diagnostic bundle (run inside `/tmp` to avoid dropping a diagnostic zip file in your working tree):
```bash
(cd /tmp && cloudflared tunnel diag)
```

---

## 4. Post-Quantum Hybrid Key Exchange

Modern `cloudflared` supports and automatically negotiates post-quantum hybrid key exchange (`X25519MLKEM768`) to future-proof encrypted tunnel connections against "harvest now, decrypt later" attacks. You can explicitly opt into experimental post-quantum tunnels with:

```bash
cloudflared tunnel --post-quantum --url http://127.0.0.1:8080
```

---

## 5. ICMP Socket Warnings in Docker Containers

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

## 6. Firewall Egress Rules

If running in a locked-down network or VPC, ensure outbound rules allow:

| Port | Protocol | Destination | Purpose |
|---|---|---|---|
| **7844** | UDP | `*.v2.argotunnel.com` | QUIC tunnel data transport |
| **7844** | TCP | `*.v2.argotunnel.com` | HTTP/2 tunnel data transport |
| **443** | TCP | `api.cloudflare.com` | Tunnel management, registration, and auth |
