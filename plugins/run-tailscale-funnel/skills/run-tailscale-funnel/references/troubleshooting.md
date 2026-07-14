# troubleshooting — symptom → cause → fix

Read top to bottom. The order matches "most common cause given the symptom." If the first cause doesn't match, fall through.

## "Funnel on" but public URL is NXDOMAIN

The CLI manages **device-side** state. The public DNS record is published by Tailscale's coordination server only when the tailnet ACL has granted the `funnel` node-attribute **and** HTTPS Certificates is enabled. Both can be off while `tailscale funnel status` happily reports "Funnel on."

**Diagnostic**:

```bash
dig @ns1.dnsimple.com <node>.<tailnet>.ts.net A +short
# - empty answer  = ACL gate is closed (most common)
# - 208.111.34.11 / 208.111.35.209 = gate is open, DNS resolver caches just stale
```

**Fix (gate closed)** — must be done by the tailnet admin:

1. Go to `https://login.tailscale.com/admin/dns` → enable **HTTPS Certificates**.
2. Go to `https://login.tailscale.com/admin/acls` → add or merge into `nodeAttrs`:

   ```json
   {
     "nodeAttrs": [
       { "target": ["autogroup:member"], "attr": ["funnel"] }
     ]
   }
   ```

   Save. Public DNS publishes within ~30–60 seconds.

**Fix (gate open, just stale cache)** — wait. Cloudflare `1.1.1.1` holds NXDOMAIN for the full 5-minute negative TTL. Other resolvers (`8.8.8.8`, `9.9.9.9`, `208.67.222.222`) usually clear within seconds. Probe from multiple resolvers:

```bash
for r in 1.1.1.1 8.8.8.8 9.9.9.9 208.67.222.222; do
  printf '%-16s A=%s\n' "$r" "$(dig @$r <fqdn> A +short)"
done
```

If 3 of 4 return records and 1 doesn't, that's stale cache; wait it out.

## Public URL returns 502 Bad Gateway

Funnel is forwarding but the backend isn't there.

**Diagnostic**:

```bash
tailscale funnel status                                    # confirm what target the mapping points at
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:<backend-port>/  # confirm backend is reachable
```

**Fixes** (in order of likelihood):

1. **Backend isn't running** — start it: `cd <project> && <start-command>`
2. **Backend is bound to wrong port** — `lsof -nP -iTCP:<backend-port> -sTCP:LISTEN` shows nothing
3. **Funnel mapping points at wrong port** — `tailscale funnel status` shows it forwarding to a different port than the backend is on. Re-map: `tailscale funnel --bg --https=<funnel-port> http://127.0.0.1:<actual-backend-port>`
4. **Backend bound to `0.0.0.0` only, daemon expects loopback** — unusual but possible; check `lsof` output for `*:<port>` vs `127.0.0.1:<port>`. Both should work for Funnel because tailscaled hits the loopback address; if you see it only on a specific external interface, that's the issue.

## Public URL returns 403 Forbidden

Backend Host-header validation. This is covered in detail in `backend-host-validation.md`. Short version:

- Most dev servers (Astro, Vite, Next dev) validate the incoming `Host:` header
- Funnel forwards with `Host: <node>.<tailnet>.ts.net`
- The framework's allowlist doesn't include that hostname → 403

**Fastest fix**: switch to serving a static `dist/` via `python3 -m http.server --bind 127.0.0.1`. No Host check.

**Framework fix**: set `allowedHosts: ['.ts.net']` in the framework config (Astro/Vite) and restart the dev server.

**Diagnostic to confirm**: `curl http://127.0.0.1:<port>/` returns 200 directly, but `curl https://<fqdn>:<funnel-port>/` returns 403.

## `dig @100.100.100.100` works, but `curl` says "Could not resolve host"

macOS resolver-chain split. `curl` reads `/etc/resolver/`; the daemon's resolver is at `100.100.100.100` but `/etc/resolver/ts.net` isn't installed.

**Diagnostic**:

```bash
scutil --dns | grep -A3 'domain *: ts.net'
# If no output: resolver file is missing
```

**Fix** — see `macos-dns-fixup.md`. Short version:

```bash
sudo mkdir -p /etc/resolver
sudo tee /etc/resolver/ts.net >/dev/null <<EOF
nameserver 100.100.100.100
EOF
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

## `host <fqdn>` returns NXDOMAIN

Almost always not a real problem on macOS — `host` ignores `/etc/resolver/`. Verify with `curl`/`dscacheutil` instead.

```bash
dscacheutil -q host -a name <fqdn>     # what mDNSResponder sees
curl -sI --noproxy '*' https://<fqdn>/ # what your apps see
```

If both of these work, `host` is the only thing wrong. That's fine; document but don't fix.

If `dscacheutil` is also empty, the daemon doesn't know the FQDN — check `tailscale status` and confirm the node is logged in.

## "Worked from cellular phone, fails from this Mac"

Same root cause as the previous two. The phone uses public DNS (which sees the Funnel records correctly). This Mac has a broken local resolver chain. Apply the `/etc/resolver/<tailnet>.ts.net` fix on this Mac.

## `tailscale funnel --bg --https=443` says "port already in use"

Another Serve or Funnel mapping owns the slot. See `port-slot-management.md`.

**Diagnostic**:

```bash
tailscale serve status
tailscale funnel status
```

**Fix**: free a single port — `tailscale funnel --https=443 off` or `tailscale serve --https=443 off`. Never `tailscale funnel reset` or `tailscale serve reset` — those wipe everything.

## Backend works from Funnel, but Cert validation fails

Almost always means the cert is still being issued by Let's Encrypt for the first time. Wait 60 seconds, retry:

```bash
curl --max-time 12 -sS -o /dev/null \
  -w "HTTP=%{http_code} cert=%{ssl_verify_result}\n" \
  https://<fqdn>:<funnel-port>/
# cert=0 means valid; cert=anything-else means TLS problem
```

If after 5 minutes the cert is still failing, check `tailscale dns status` — if HTTPS Certificates is disabled at the tailnet level, Tailscale won't even attempt issuance.

## `tailscale funnel up` says "Funnel requires HTTPS Certificates"

The tailnet-level setting is off. Tailnet admin must enable it at `https://login.tailscale.com/admin/dns` → enable HTTPS Certificates. This is one of the two checks at the ACL gate; the other is the `funnel` nodeAttr.

## Browser refuses to load `http://<fqdn>:<port>/`

`*.ts.net` is on Chrome's HSTS preload list. Browsers force HTTPS for this domain. Use the `https://...` URL. Plain HTTP is not optional.

For CLI work (`curl`, `mcpc`, `wget`), HSTS preload doesn't apply — plain HTTP works against tailnet-only Serve on a non-standard port, but not against Funnel (Funnel always terminates HTTPS).

## "agent-browser shows 'restricted target; contact support team'"

You pointed it at a private IP — `127.0.0.1`, `localhost`, `192.168.x.x`, `10.x.x.x`, or a Tailscale CGNAT address `100.x.x.x`. The tool deliberately blocks private IP ranges as an SSRF defense.

Use the public Funnel URL instead — `https://<node>.<tailnet>.ts.net[:port]/`. Funnel resolves to `208.111.34.11` / `208.111.35.209`, which are public Tailscale ingress IPs, and the cert is Let's Encrypt-signed. Browser-automation tools accept this.

If agent-browser still rejects with the same error after switching to the public URL, you likely typed the URL wrong or DNS hasn't propagated. Confirm with `curl --noproxy '*' -sI https://<fqdn>:<port>/` first.

## The mapping survived after Ctrl-C; was that supposed to happen?

Yes. `tailscale funnel --bg` is persistent. After Ctrl-C the mapping remains. It's harmless when the backend is down — clients get 502, no security risk — but tear it down explicitly when you're really done:

```bash
tailscale funnel --https=<port> off
```

## I tore down the wrong mapping

If you accidentally ran `tailscale funnel --https=<port> off` against the wrong port, the mapping is gone but easy to recreate if you know the target. Look at the snapshot file from your preflight (`/tmp/tailscale-snapshot-*.txt` if you used `port-slot-management.md`'s recipe) or in shell history for the previous `tailscale funnel --bg` command.

If you `tailscale funnel reset` or `tailscale serve reset` instead, you wiped everything. Apologize to whoever else uses this node and start re-creating mappings from history. Save a snapshot before any destructive command, every time.
