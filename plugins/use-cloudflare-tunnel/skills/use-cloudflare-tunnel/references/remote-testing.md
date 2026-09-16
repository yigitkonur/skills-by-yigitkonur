# Remote Testing, Client Delivery & Webhooks via Tunnel

Cloudflare Tunnel bridges isolated execution environments (containers, remote cloud VMs, WSL) with real user browsers, automated mobile emulators, and external third-party webhooks.

---

## 1. The Target Client Verification Gate (Zero False Positives)

When an agent develops inside a Linux container and delivers a preview to a user's machine (e.g. MacBook via SSH) or automated browser, **probing from inside the container is not proof of external reachability**.

### The False-Positive Trap:
* `curl -Is <URL>` inside the container can connect to Cloudflare edge IPs while the remote user's operating system still has DNS unresolved or cached as NXDOMAIN.
* Triggering `ssh macbook "open '<URL>'"` prematurely causes the user to see `DNS_PROBE_FINISHED_NXDOMAIN` or connection failures.

### The Mandatory Target-Perspective Probe:
Before triggering any browser `open` command on the remote machine:

```bash
# 1. Flush remote DNS cache
ssh macbook "dscacheutil -flushcache 2>/dev/null || true"

# 2. Probe HTTP status directly from the remote client's OS network stack
PROBE_OK=false
for attempt in {1..20}; do
  STATUS=$(ssh macbook "curl -s -o /dev/null -w '%{http_code}' -m 5 '$TUNNEL_URL'" 2>/dev/null || echo "000")
  if [[ "$STATUS" == "200" ]]; then
    PROBE_OK=true
    break
  fi
  if (( attempt % 3 == 0 )); then
    ssh macbook "dscacheutil -flushcache 2>/dev/null || true"
  fi
  sleep 1.5
done

if [[ "$PROBE_OK" != "true" ]]; then
  echo "Error: Target machine could not reach tunnel (HTTP status: $STATUS)" >&2
  exit 1
fi

# 3. ONLY after remote 200 OK, trigger browser
ssh macbook "open '$TUNNEL_URL'"
```

---

## 2. Remote Browser Automation with ego-browser

In modern agentic setups, coding agents frequently run inside Linux Docker containers while human users (and ego-browser Chromium sessions) run on the host machine (e.g. macOS).

### Why SSH Port Forwarding Fails
SSH reverse forwarding (`-R 8099:localhost:8099`) frequently fails due to:
* Already allocated listen ports on host.
* Non-forwarded subdomains or dynamic web worker sockets.
* Hardcoded container loopback bindings (`127.0.0.1` vs `0.0.0.0`).

### The Cloudflare Tunnel Solution
Using a quick tunnel, the container exposes its port to an official public HTTPS URL (`https://xyz.trycloudflare.com`). The remote browser connects directly through Cloudflare edge.

---

## 3. Setting Mobile Viewports (iPhone / Android) via CDP

When testing responsive web and Expo Web apps, drive the browser via Chrome DevTools Protocol (`cdp`):

```javascript
ego-browser nodejs <<'SCRIPT'
const task = await useOrCreateTaskSpace('mobile-verification');

// Emulate iPhone (390 x 844, 3x retina, mobile touch events)
await cdp('Emulation.setDeviceMetricsOverride', {
  width: 390,
  height: 844,
  deviceScaleFactor: 3,
  mobile: true
});

// Navigate to tunnel URL
await openOrReuseTab('https://xyz.trycloudflare.com/onboarding', { wait: true, timeout: 20 });
await wait(2);

cliLog('Current page state: ' + await snapshotText());
SCRIPT
```

---

## 4. Bi-Directional Screenshot & Artifact Exfiltration

When ego-browser runs on the host OS, standard `captureScreenshot()` saves images to the host temporary directory (e.g. `/var/folders/.../ego-shot.png`), which is not directly readable from inside the container.

### The Exfiltration Endpoint Pattern
Add a small `/api/save-screenshot` endpoint to your local server or unified proxy:

```javascript
// On the server/proxy inside the container:
if (pathname === '/api/save-screenshot' && req.method === 'POST') {
  const buffer = Buffer.from(body.data, 'base64');
  fs.writeFileSync(`/path/to/artifacts/${body.name}`, buffer);
  return sendJson(res, 200, { ok: true, size: buffer.length });
}
```

### In the ego-browser script:
```javascript
// Capture raw base64 data directly from CDP
const shot = await cdp('Page.captureScreenshot', { format: 'png' });

// Upload to container via the active Cloudflare Tunnel
await serverFetch('https://xyz.trycloudflare.com/api/save-screenshot', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'step_1_verification.png', data: shot.data })
});
```

---

## 5. Testing External Webhooks (Stripe, GitHub, Supabase)

Quick tunnels are ideal for testing third-party webhooks locally without setting up dedicated DNS records:

```bash
# 1. Start webhook consumer locally on port 4000
python3 server.py &

# 2. Expose via tunnel with isolated daemon
setsid nohup cloudflared tunnel --url http://127.0.0.1:4000 --logfile /tmp/webhook-cf.log </dev/null >/dev/null 2>&1 &
sleep 3
WEBHOOK_URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' /tmp/webhook-cf.log | tail -n 1)

echo "Register this Webhook URL in dashboard: ${WEBHOOK_URL}/webhooks/stripe"
```
