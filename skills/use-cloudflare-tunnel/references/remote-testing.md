# Remote Testing, Ego-Browser & Webhooks via Tunnel

Cloudflare Tunnel bridges isolated execution environments (containers, remote cloud VMs, WSL) with real user browsers, automated mobile emulators, and external third-party webhooks.

---

## 1. Remote Browser Automation with ego-browser

In modern agentic setups, coding agents frequently run inside Linux Docker containers while human users (and ego-browser Chromium sessions) run on the host machine (e.g. macOS).

### Why SSH Port Forwarding Fails
SSH reverse forwarding (`-R 8099:localhost:8099`) frequently fails due to:
* Already allocated listen ports on host.
* Non-forwarded subdomains or dynamic web worker sockets.
* Hardcoded container loopback bindings (`127.0.0.1` vs `0.0.0.0`).

### The Cloudflare Tunnel Solution
Using a quick tunnel, the container exposes its port to an official public HTTPS URL (`https://xyz.trycloudflare.com`). The remote browser connects directly through Cloudflare edge.

---

## 2. Setting Mobile Viewports (iPhone / Android) via CDP

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

## 3. Bi-Directional Screenshot & Artifact Exfiltration

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

## 4. Testing External Webhooks (Stripe, GitHub, Supabase)

Quick tunnels are ideal for testing third-party webhooks locally without setting up dedicated DNS records:

```bash
# 1. Start webhook consumer locally on port 4000
python3 server.py &

# 2. Expose via tunnel
cloudflared tunnel --url http://127.0.0.1:4000 --logfile /tmp/webhook-cf.log &
sleep 4
WEBHOOK_URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' /tmp/webhook-cf.log | head -n 1)

echo "Register this Webhook URL in dashboard: ${WEBHOOK_URL}/webhooks/stripe"
```

### Supported Webhook Services:
* **Stripe:** Set Endpoint URL to `https://xyz.trycloudflare.com/stripe/webhook`
* **GitHub Apps:** Webhook URL for `push`, `pull_request`, and `issues` events
* **Supabase:** Database webhooks (`POST /functions/v1/...`)
* **Shopify / Slack / Twilio:** Inbound SMS & interactivity callbacks

---

## 5. Preserving Browser Sessions for the User

When an automated verification task finishes in ego-browser, agents should follow the ownership rules:

```javascript
// If the user wants to continue inspecting the page interactively:
await completeTaskSpace(taskId, { keep: true });

// If automated test is finished and no further user inspection needed:
await completeTaskSpace(taskId, { keep: false });
```
