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
   # Prompts browser to authorize domain; downloads ~/.cloudflared/cert.pem
   ```
2. **Create the tunnel:**
   ```bash
   cloudflared tunnel create my-app-tunnel
   # Output: Tunnel credentials written to ~/.cloudflared/<UUID>.json
   ```
   *(Note: Never run `rm -rf ~/.cloudflared/` during quick tunnel testing, as it destroys these permanent credentials and your `cert.pem` login).*
3. **Route DNS hostname to the tunnel:**
   ```bash
   # Use -f / --overwrite-dns to overwrite existing CNAME/A records without error
   cloudflared tunnel route dns -f my-app-tunnel api.mycompany.com
   # Creates CNAME api.mycompany.com -> <UUID>.cfargotunnel.com
   ```
4. **Run the tunnel with configuration file:**
   ```bash
   # When running as current user:
   cloudflared tunnel --config ~/.cloudflared/config.yml run my-app-tunnel
   
   # Or when running as system daemon (/etc/cloudflared/):
   sudo cp ~/.cloudflared/<UUID>.json /etc/cloudflared/
   sudo cloudflared tunnel --config /etc/cloudflared/config.yml run my-app-tunnel
   ```

---

## 2. Configuration File Structure (`config.yml`)

When managing locally, `config.yml` defines the tunnel ID, credential file location, global origin settings, and ingress routing rules. Ensure the `credentials-file` path accurately points to where `<UUID>.json` is stored (`~/.cloudflared/` for user runs or `/etc/cloudflared/` for system services).

```yaml
tunnel: 69e33490-24c2-4ec0-9d6f-27bc79b87cb2
# Match the credentials location:
credentials-file: /etc/cloudflared/69e33490-24c2-4ec0-9d6f-27bc79b87cb2.json
# (For user runs: credentials-file: /Users/username/.cloudflared/69e33490-24c2-4ec0-9d6f-27bc79b87cb2.json)

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

## 4. Running as a System Service (Systemd & macOS Launchd)

### Linux (Systemd)
For production Linux environments, install `cloudflared` as a persistent systemd service:

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

### macOS (Launchd)
On macOS workstations, `cloudflared service install` configures a LaunchAgent or LaunchDaemon (`com.cloudflare.cloudflared.plist`):

```bash
# Install launchd service with token
sudo cloudflared service install eyJhIjoiY...

# Start and stop using launchctl
sudo launchctl start com.cloudflare.cloudflared
sudo launchctl stop com.cloudflare.cloudflared

# View service logs on macOS
tail -f /Library/Logs/com.cloudflare.cloudflared.err.log
tail -f /Library/Logs/com.cloudflare.cloudflared.out.log
```

---

## 5. Autonomous Agent & Headless Programmatic Access (Service Tokens)

While Protected Quick Tunnels (`--allowed-mail`) require an interactive browser to submit an email OTP, **Named Tunnels protected by Cloudflare Access support non-interactive machine-to-machine authentication via Service Tokens**.

This is the standard pattern for autonomous coding agents, automated test suites, and remote CI/CD pipelines:

### 1. Generate Service Token in Cloudflare One Dashboard:
* Navigate to **Zero Trust > Access > Service Auth > Create Service Token**.
* Copy the generated `Client ID` and `Client Secret`.
* Create an Access Policy allowing requests with this Service Token.

### 2. Programmatic Client Access:
When an agent or script requests the tunnel endpoint, pass the credentials as headers:

```bash
curl -H "CF-Access-Client-Id: <CLIENT_ID>" \
     -H "CF-Access-Client-Secret: <CLIENT_SECRET>" \
     https://api.mycompany.com/v1/health
```

### 3. Agent Integration in Code:
```typescript
const response = await fetch('https://api.mycompany.com/v1/agent-task', {
  headers: {
    'CF-Access-Client-Id': process.env.CF_ACCESS_CLIENT_ID,
    'CF-Access-Client-Secret': process.env.CF_ACCESS_CLIENT_SECRET,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ task: 'execute' })
});
```

---

## 6. Useful Management Commands

| Command | Purpose |
|---|---|
| `cloudflared tunnel list` | Lists all existing named tunnels in your account. |
| `cloudflared tunnel info <NAME/UUID>` | Displays connector status, active connections, and locations. |
| `cloudflared tunnel route dns -f <NAME/UUID> <hostname>` | Binds DNS CNAME to the named tunnel (overwrites existing records). |
| `cloudflared tunnel route ip add <CIDR> <NAME/UUID>` | Routes private IP subnet traffic (WARP / Zero Trust Private Network). |
| `cloudflared tunnel ready` | Calls embedded `/ready` endpoint and returns proper process exit code (0 = ready, 1 = not ready). |
| `cloudflared tunnel delete <NAME/UUID>` | Deletes the tunnel identity (must stop active instances first). |
| `cloudflared tunnel cleanup <NAME/UUID>` | Cleans up orphaned or dead connection records in Cloudflare edge. |
| `cloudflared tunnel ingress validate` | Validates YAML syntax and service rules in `config.yml`. |
| `cloudflared tunnel ingress rule <URL>` | Evaluates which ingress rule matches a given test URL. |
