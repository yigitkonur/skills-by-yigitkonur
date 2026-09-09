# Cloudflare Named Tunnels (Production & Persistent)

Named Tunnels provide stable, persistent connectivity to Cloudflare's global network using your own custom domains, authenticated credentials, and declarative configuration.

---

## 1. Authentication Models: Token vs Local Credentials

There are two primary ways to run Named Tunnels:

### Method A: Token-Based (Remotely Managed - Recommended for CI & Cloud)
Tunnels managed via the Cloudflare One Dashboard (`one.dash.cloudflare.com`) generate a base64 tunnel token. This token encapsulates account authorization and tunnel identity into a single argument with zero file management.

```bash
cloudflared tunnel run --token eyJhIjoiY...
```

* **Pros:** Zero local configuration files, secrets easily managed via environment variables (`TUNNEL_TOKEN`), rules updated remotely via dashboard without restarting the daemon.
* **Cons:** Requires active internet connection during setup; configuration is stored on Cloudflare servers.

### Method B: Locally Managed (File-Based)
Tunnels managed entirely through local YAML and JSON files on disk.

1. **Authenticate CLI with Cloudflare account:**
   ```bash
   cloudflared tunnel login
   # Downloads ~/.cloudflared/cert.pem
   ```
2. **Create the tunnel:**
   ```bash
   cloudflared tunnel create my-app-tunnel
   # Output: Tunnel credentials written to /root/.cloudflared/<UUID>.json
   ```
3. **Route DNS hostname to the tunnel:**
   ```bash
   cloudflared tunnel route dns my-app-tunnel api.mycompany.com
   # Creates CNAME api.mycompany.com -> <UUID>.cfargotunnel.com
   ```
4. **Run the tunnel with configuration file:**
   ```bash
   cloudflared tunnel --config /etc/cloudflared/config.yml run my-app-tunnel
   ```

---

## 2. Configuration File Structure (`config.yml`)

When managing locally, `config.yml` defines the tunnel ID, credential file location, global origin settings, and ingress routing rules.

```yaml
tunnel: 69e33490-24c2-4ec0-9d6f-27bc79b87cb2
credentials-file: /etc/cloudflared/69e33490-24c2-4ec0-9d6f-27bc79b87cb2.json

# Optional: Global origin settings
originRequest:
  connectTimeout: 30s
  noTLSVerify: false

ingress:
  # Public Web Application
  - hostname: app.example.com
    service: http://localhost:3000

  # API Endpoint with custom timeout
  - hostname: api.example.com
    service: http://localhost:8080
    originRequest:
      connectTimeout: 15s

  # Catch-all rule (REQUIRED: must be the last entry)
  - service: http_status:404
```

---

## 3. High Availability & Replicas

Named tunnels support multiple running instances (connectors) using the exact same tunnel ID or token simultaneously across different servers or containers.

* **Automatic Anycast Load Balancing:** Incoming requests are automatically distributed across healthy active connectors by Cloudflare edge.
* **Zero Downtime Deploys:** Spin up a new `cloudflared` replica on the new instance, verify healthy connection logs, then terminate the old replica.
* **Failure Handling:** If a host machine or container crashes, Cloudflare's edge ceases routing traffic to that connector within seconds and routes exclusively to surviving replicas.

---

## 4. Running as a System Service (Systemd)

For production Linux environments, install `cloudflared` as a persistent background daemon:

```bash
# Install systemd service with token
sudo cloudflared service install eyJhIjoiY...

# Or with configuration file:
sudo cloudflared --config /etc/cloudflared/config.yml service install

# Start and enable on boot
sudo systemctl daemon-reload
sudo systemctl enable --now cloudflared

# Check status and logs
systemctl status cloudflared
journalctl -u cloudflared -f
```

---

## 5. Useful Management Commands

| Command | Purpose |
|---|---|
| `cloudflared tunnel list` | Lists all existing named tunnels in your account. |
| `cloudflared tunnel info <NAME/UUID>` | Displays connector status, active connections, and locations. |
| `cloudflared tunnel delete <NAME/UUID>` | Deletes the tunnel identity (must stop active instances first). |
| `cloudflared tunnel cleanup <NAME/UUID>` | Cleans up orphaned or dead connection records in Cloudflare edge. |
| `cloudflared tunnel ingress validate` | Validates YAML syntax and service rules in `config.yml`. |
