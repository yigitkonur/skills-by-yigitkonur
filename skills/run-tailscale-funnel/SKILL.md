---
name: run-tailscale-funnel
description: Use skill if you are exposing a local HTTP server at a public `.ts.net` URL via Tailscale Funnel for agent-browser navigation, mobile testing, webhooks, or shared dev demos.
---

# run-tailscale-funnel

Get a local HTTP server reachable at a stable `https://<node>.<tailnet>.ts.net` URL, with a real Let's Encrypt cert, no port number in the URL, no ngrok account, no separate paid plan. The end state is a single public URL that any client on the public internet can hit — including sandboxed browser-automation agents that cannot reach the host's loopback.

This skill is the canonical operator for `tailscale funnel`. It owns the preflight, the port-slot decision, the bind-interface decision, the verification chain, and the teardown. It assumes Tailscale is already installed and the node is logged in to a tailnet.

## Use this skill when

- *the user wants an `https://...ts.net` URL for a local dev server, a static `dist/` folder, an MCP server, a webhook receiver, or a tracing dashboard*
- *a browser-automation tool (agent-browser, Playwright in a microVM, Vercel Sandbox, AgentCore cloud browsers) fails to reach `127.0.0.1`, `192.168.x.x`, or `100.x.x.x` and you need a public URL with a real cert*
- *the user asks to "make this reachable from my phone," "share this with a friend," "expose to the public internet," or "give me a tunnel"*
- *the user pastes a `tailscale serve`/`tailscale funnel` error or asks why `tailscale funnel up` shows "Funnel on" but the public URL is NXDOMAIN*
- *the user is wiring `make local` (or `make tunnel`, `make share`, `make demo`) into a project's Makefile*

## Do NOT use this skill when

- the user only needs **same-LAN access** (phone on same wifi, dev partner across the room) — direct LAN bind to `0.0.0.0:<port>` is simpler, no tunnel needed
- the user needs **tailnet-only access** between their own devices and explicitly does not want public exposure — use `tailscale serve` instead of `tailscale funnel`, and tell them so
- the user wants **production traffic** (large request bodies, file uploads, sustained high RPS) — Funnel is throttled to ~1 MB/s practical; recommend Cloudflare Tunnel or a real reverse proxy
- the user is on **Windows or Linux** — most of this still applies, but macOS DNS quirks (the single largest source of "Tailscale URL works on my phone but not on this Mac") do not. Skim the macOS sections; treat them as Mac-specific
- the request is for **ngrok, Cloudflare Tunnel, localtunnel, or LocalCan** specifically — those are different tools with different trade-offs. Funnel's pitch is no-signup, no-extra-account, one-CLI, free
- the answer is a **clear "no" to public exposure** — Funnel is opt-in. Never enable it as a side effect of a different request

## The mental model — read this before running any command

Most failures with Funnel come from one of five wrong assumptions. These are the wrong assumptions. Each is followed by what's actually true and why it matters.

### Wrong: "Tailscale Funnel is one thing"

It's four things, and any one can be in a different state than the others:

1. **The local app** — your dev server, static site, MCP server. Listens on a TCP port (usually `127.0.0.1:<port>`).
2. **The Tailscale daemon on this machine** — knows about Funnel mappings device-side, can be configured via `tailscale serve`/`tailscale funnel` without sudo.
3. **The tailnet coordination server** (Tailscale's hosted service) — owns the ACL that decides whether your node is allowed to expose Funnel, and publishes public DNS records for your `.ts.net` FQDN.
4. **The public DNS** — A and AAAA records for `<node>.<tailnet>.ts.net` published by Tailscale only when the ACL gate is open.

`tailscale funnel up` configures (2). It succeeds device-locally even when (3) hasn't granted the `funnel` attribute, and even when (4) therefore returns NXDOMAIN. The CLI happily prints "Funnel on" while the URL is unreachable from the public internet. You verify each layer independently. See `references/architecture.md` for the diagram.

### Wrong: "Binding `0.0.0.0` makes the app Funnel-compatible"

The bind interface and the HTTP Host header are two separate things at two separate OSI layers.

- **Bind interface** (`127.0.0.1` vs `0.0.0.0`) — TCP layer. Controls which network interfaces the app accepts connections from. Funnel forwards to whatever port you tell it to, on the loopback interface. `127.0.0.1` is the secure default — only the Funnel proxy can reach the backend.
- **Host header allowlist** — HTTP layer. Many dev servers (Astro preview, Vite, Next.js dev) check the incoming `Host:` header against an allowlist. Funnel forwards requests with `Host: <node>.<tailnet>.ts.net`. If that hostname isn't in the framework's allowlist, you get a 403 even though TCP routing is fine.

Flags like `astro preview --host`, `vite --host`, `next dev -H` control the **bind interface**, not the Host allowlist. They do not fix 403-from-Funnel. Two real fixes exist for the Host-header layer; see `references/backend-host-validation.md` for both.

### Wrong: "There's lots of room for new Funnel mappings"

Funnel publishes on **only three ports**: `443`, `8443`, `10000`. That's the entire slot inventory per node. Each port can host exactly one mapping. Assigning a new mapping silently replaces the old one — no warning, no confirmation. `tailscale funnel reset` wipes **every** Serve and Funnel mapping on the node, including unrelated projects.

The preflight is mandatory:

```bash
tailscale serve status
tailscale funnel status
```

These show the current map. Pick a free slot. If all three are taken, ask the user which one to take over (and snapshot the existing mapping first so you can restore). See `references/port-slot-management.md` for the decision tree.

### Wrong: "Sandboxed browser agents can reach localhost, they're on the same machine"

They often cannot. Many browser-automation runners isolate the Chrome process into its own network namespace (Docker, Vercel Sandbox, AWS Bedrock AgentCore browsers, agent-browser's headless Chrome) and:

- `127.0.0.1` from that namespace resolves to the *container's* loopback, not the host's
- `192.168.x.x` and `10.x.x.x` are often deliberately blocked by an SSRF guard (agent-browser shows "restricted target; contact support team" — a feature, not a bug)
- `100.x.x.x` (Tailscale CGNAT) is in the same private range and gets the same block

If a browser-automation agent needs to navigate your local server, **the only clean fix is a real public URL with a real cert**, which is exactly what Funnel produces. Don't try to switch from loopback to LAN IP to dodge it — most tools block both ranges, and even when LAN works it leaks the dev server to your whole wifi. Use Funnel.

### Wrong: "`host fqdn` and `curl fqdn` see the same DNS on macOS"

They do not, and this is the single largest source of debugging confusion.

| Tool | Resolver path | Reads `/etc/resolver/`? |
|---|---|---|
| `host`, bare `dig` (no `@server`) | libresolv → `/etc/resolv.conf` | **no** |
| `curl`, browsers, `getaddrinfo()` | mDNSResponder | **yes** |
| `dig @100.100.100.100` (explicit) | direct to Tailscale's DNS daemon | n/a |

So `host mini.tail2fcc55.ts.net` can return `NXDOMAIN` *while* `curl https://mini.tail2fcc55.ts.net/` returns `HTTP/2 200` on the same Mac. Both are correct — they're hitting different resolvers. Trust `curl`, `dscacheutil -q host -a name <fqdn>`, and `dig @<explicit-resolver>`. Distrust bare `host`/`dig`. See `references/macos-dns-fixup.md` for the `/etc/resolver/<tailnet>.ts.net` install that makes this consistent.

## The five drift points an agent slips into

Each is a "I'd think X, but actually Y" pairing. Internalize these before running any command.

| Drift | What you'd think | What's actually true | The fix |
|---|---|---|---|
| 1 | "Astro returns 403 because it's bound to `127.0.0.1`. Switch to `--host 0.0.0.0`." | Bind is TCP layer; 403 is HTTP-layer Host validation. Switching binds does not change the Host allowlist. | Either set framework `allowedHosts` to include `.ts.net`, or — for a static site — serve the built `dist/` via `python3 -m http.server`/`caddy file-server`/`npx serve`, which do not validate Host headers. See `references/backend-host-validation.md`. |
| 2 | "`tailscale funnel reset` is a safe way to start clean." | `reset` wipes every Serve and Funnel mapping on the node — including other projects' mappings, including unrelated production tunnels. There is no undo. | Use `tailscale funnel --https=<port> off` to clear a single port. Never `reset` without explicit user consent and a snapshot of `tailscale serve status` first. |
| 3 | "`tailscale funnel up` succeeded → the public URL works." | Device-side state and tailnet ACL state are independent. The CLI manages device-side only. Public DNS is only published when the ACL gate is open. | After `funnel up`, verify with `dig @ns1.dnsimple.com <fqdn> A +short`. Empty answer = gate is closed; tell the user to grant the `funnel` nodeAttr and enable HTTPS Certificates in the tailnet admin console. See `references/troubleshooting.md` § ACL gate. |
| 4 | "`host fqdn` returns NXDOMAIN, so the URL is broken." | `host` reads `/etc/resolv.conf` and ignores `/etc/resolver/`. `curl` reads `/etc/resolver/` and gets the right answer. Both are correct; they query different resolvers. | Verify user-facing behavior with `curl --noproxy '*'` or `dscacheutil -q host -a name <fqdn>`. Never debug user-facing DNS with bare `host`. See `references/macos-dns-fixup.md`. |
| 5 | "agent-browser can't reach `127.0.0.1`; let me try the Mac's LAN IP." | Browser-automation runners commonly block private IP ranges (RFC1918 + CGNAT) as an SSRF defense. agent-browser specifically refuses with "restricted target." The LAN IP is not the fix. | Stand up Funnel and use the public `.ts.net` URL. That's what these tools are designed to accept. |

## The canonical workflow

Seven steps, each with a verification gate. Do not skip the verifications — they catch the layered failures the mental-model section warned about.

### Step 1 — Preflight (the part agents skip)

```bash
# 1a. Identity — needed for the URL you'll print at the end
tailscale status --json | python3 -c "
import json,sys
d=json.load(sys.stdin); s=d.get('Self',{})
print('hostname:', s.get('HostName',''))
print('fqdn:', s.get('DNSName','').rstrip('.'))
print('magicdns:', d.get('CurrentTailnet',{}).get('MagicDNSEnabled'))
"

# 1b. Existing mappings — never clobber another project
tailscale serve status
tailscale funnel status

# 1c. Local port — what's listening, who owns it
lsof -nP -iTCP:<local-port> -sTCP:LISTEN
```

Capture all three before doing anything. If `magicdns: True` is missing, stop and tell the user — MagicDNS must be enabled in the tailnet admin console first.

### Step 2 — Bind the local app to `127.0.0.1`

Funnel terminates HTTPS externally and proxies to the loopback interface on this machine. Bind your app to `127.0.0.1`, not `0.0.0.0`, so the only path in is via Funnel.

- Static dir built ahead of time: `cd dist && python3 -m http.server <port> --bind 127.0.0.1` (no Host-header check, simplest path)
- Astro preview: `astro preview --port <port> --host 127.0.0.1` — but **note Step 3** about the Host-header trap
- Vite preview: same shape, same Host-header trap
- Next.js: `next start -p <port> -H 127.0.0.1` — Next does not Host-validate by default
- Docker Compose: `ports: ["127.0.0.1:<host-port>:<container-port>"]`

Confirm the bind:

```bash
lsof -nP -iTCP:<port> -sTCP:LISTEN
curl -sI http://127.0.0.1:<port>/ | head -1
```

### Step 3 — Decide: dev server vs static dir

This is the decision the recipe doc doesn't make for you. Two paths:

- **Static `dist/` available** (production build of a static site, pre-rendered docs, a built SPA): serve it via `python3 -m http.server`, `caddy file-server`, `npx serve`, or any other dumb static server. None of these validate Host headers. **This is the simplest, lowest-friction path. Prefer it.**
- **Live dev server needed** (you want hot-reload, server-side rendering, API routes, a backend in a framework): you'll hit Host-header validation. Two sub-fixes:
  - **Astro v5**: add `vite.preview.allowedHosts: ['.ts.net']` to `astro.config.mjs`, or simpler: `vite.server.allowedHosts: true` for dev.
  - **Vite ≥5.4**: `server.allowedHosts: true` or specific hostname list.
  - **Next.js dev**: no validation by default — just bind `-H 127.0.0.1`.
  - **Other frameworks**: search "<framework> allowedHosts" or "<framework> host header validation". The snippet collection in `assets/allowed-hosts-snippets.md` covers the common ones.

If 403 appears via Funnel but 200 via direct loopback, this is the cause. See `references/backend-host-validation.md` for the per-framework recipe.

### Step 4 — Pick a free Funnel slot

Public ports allowed by Tailscale Funnel: **`443`, `8443`, `10000`**. That's the entire inventory.

- If `443` is free → use `443` for a clean URL `https://<node>.<tailnet>.ts.net/`
- If `443` is taken → try `8443` for `https://<node>.<tailnet>.ts.net:8443/`
- If both taken → try `10000`
- If all three taken → stop. Read `references/port-slot-management.md` and either (a) tell the user which one to free and how, or (b) snapshot one mapping, take it over for the task, restore after

The check is `tailscale serve status` + `tailscale funnel status` (already done in Step 1).

### Step 5 — Map the slot to your loopback port

```bash
tailscale funnel --bg --https=<funnel-port> http://127.0.0.1:<local-port>
```

`--bg` makes the mapping persistent across shell exit and Tailscale daemon restarts. Without `--bg` the mapping vanishes when the shell closes.

Confirm device-side state:

```bash
tailscale funnel status
# expected output includes:
# https://<node>.<tailnet>.ts.net[:<port>] (Funnel on)
# |-- / proxy http://127.0.0.1:<local-port>
```

### Step 6 — Verify the three rungs

Local "it works on my machine" does not prove "the world can reach this." Verify each layer.

**Rung 1: ACL gate (authoritative DNS).** Proves the tailnet ACL has granted `funnel` to your node.

```bash
dig @ns1.dnsimple.com <node>.<tailnet>.ts.net A +short
# expected: 208.111.34.11 and/or 208.111.35.209
# empty = gate closed; see references/troubleshooting.md § ACL gate
```

**Rung 2: Public path through Funnel ingress.** Proves the proxy is live and the cert is valid.

```bash
for ip in 208.111.34.11 208.111.35.209; do
  curl --max-time 12 -sS -o /dev/null \
    -w "ingress=$ip HTTP=%{http_code} cert=%{ssl_verify_result} time=%{time_total}s\n" \
    --resolve <node>.<tailnet>.ts.net:<funnel-port>:$ip \
    https://<node>.<tailnet>.ts.net:<funnel-port>/
done
# expected: HTTP=200 cert=0 from both ingresses
# HTTP=403 → backend Host-header validation (Step 3 fix not applied)
# HTTP=502 → backend isn't running on the loopback port the mapping points at
```

**Rung 3: External client.** Phone on cellular, friend's laptop, or `curl` from a non-tailnet box. This is the only test that proves real-world clients can reach it. **Don't claim "Funnel works" until Rung 3.**

### Step 7 — Tear down or keep persistent

```bash
# Remove a specific port (the safe form):
tailscale funnel --https=<funnel-port> off

# What NEVER to use:
# tailscale funnel reset   ← wipes EVERY Serve+Funnel mapping on this node
# tailscale serve reset    ← same, also wipes
```

If the user wants the URL to stay live across reboots, `--bg` already handles it. Tell them how to take it down explicitly.

## `make local` integration

The common-case integration is a Makefile target that wraps Step 2 through Step 6 into one command. Patterns and a copy-pasteable Makefile live in `assets/Makefile.snippet` and `references/make-local-template.md`. The short version:

```makefile
LOCAL_PORT  ?= 4321
FUNNEL_PORT ?= 10000

# Bring up Funnel for this project's local server.
.PHONY: local
local:
	@bash $(SKILL_ROOT)/scripts/funnel-up.sh $(LOCAL_PORT) $(FUNNEL_PORT)

# Tear down only this project's Funnel port (never reset).
.PHONY: local-down
local-down:
	@bash $(SKILL_ROOT)/scripts/funnel-down.sh $(FUNNEL_PORT)
```

`scripts/funnel-up.sh` runs Steps 1, 4, 5, 6.1, 6.2 in order and exits non-zero on any failure, printing the public URL on success. `scripts/funnel-down.sh` is one line — `tailscale funnel --https=<port> off` — but it refuses to run if `<port>` doesn't match what the script previously brought up, so it can't accidentally tear down someone else's mapping.

Set `SKILL_ROOT` to wherever the skill is installed (typically `~/.claude/skills/run-tailscale-funnel`). Or copy the two scripts into the project repo so `make local` doesn't depend on the skill being installed.

## When something goes wrong

Quick decision table — read top to bottom and pick the first matching symptom.

| Symptom | First-line diagnosis | Where to read |
|---|---|---|
| `tailscale funnel --bg --https=<port>` returns "port already in use" | Another Serve/Funnel mapping owns that slot. Check with `tailscale serve status` and `tailscale funnel status`. | `references/port-slot-management.md` |
| `tailscale funnel status` says "Funnel on" but public DNS is NXDOMAIN | ACL gate is closed. Tailnet admin console must grant `funnel` nodeAttr and enable HTTPS Certificates. | `references/troubleshooting.md` § ACL gate |
| Public URL returns 502 | Backend not running on the loopback port the mapping points at. Confirm with `curl -sI http://127.0.0.1:<port>/`. | `references/troubleshooting.md` § 502 |
| Public URL returns 403 (HTML body says "Forbidden") | Backend Host-header validation rejecting `<node>.<tailnet>.ts.net`. | `references/backend-host-validation.md` |
| Local curl works, public curl fails | Either Funnel is misconfigured (re-check Step 5) or the cert is still issuing — wait 60s and retry. | `references/troubleshooting.md` § cert-still-issuing |
| `host fqdn` says NXDOMAIN, but `curl` works | macOS resolver split. `host` ignores `/etc/resolver/`. Trust `curl`/`dscacheutil`. | `references/macos-dns-fixup.md` |
| `dig @100.100.100.100 fqdn` works, but `curl` says "Could not resolve" | `/etc/resolver/<tailnet>.ts.net` is missing. Install it. | `references/macos-dns-fixup.md` § installing the resolver file |
| Worked from cellular phone, fails from this Mac | Same as above — `/etc/resolver/` issue. | `references/macos-dns-fixup.md` |
| 1.1.1.1 returns NXDOMAIN but 8.8.8.8/9.9.9.9 return records | Cloudflare DNS holds a stale negative cache up to 5 minutes after the ACL gate opens. Wait and retry. | `references/troubleshooting.md` § stale-DNS-cache |
| agent-browser shows "restricted target; contact support team" | You pointed it at a private IP. Switch to the `.ts.net` Funnel URL. | `references/architecture.md` § sandboxed-browser-context |

## Reference routing

Read these only when a step or symptom routes you here.

| File | Read when |
|---|---|
| `references/architecture.md` | You need the four-component mental model (app, daemon, coordination server, public DNS) to debug a layered failure — most importantly when one rung in Step 6 passes and another doesn't. Also covers why sandboxed-browser agents need Funnel specifically. |
| `references/port-slot-management.md` | Step 4 says all three Funnel slots are taken, or `tailscale funnel --bg` says "port already in use," or you need the decision tree for picking between 443 / 8443 / 10000 and handling takeovers without `reset`. |
| `references/backend-host-validation.md` | Step 3 — choosing between static-server and dev-server paths — and any time the public URL returns 403 while local loopback returns 200. Per-framework recipes for Astro, Vite, Next.js, Express, plus the recommended "build then serve `dist/`" fallback. |
| `references/macos-dns-fixup.md` | Anything DNS on macOS: `host` says NXDOMAIN but `curl` works, `dig @100.100.100.100` works but `curl` doesn't, or a tailnet-member Mac can't reach a URL that a cellular phone can. Installs `/etc/resolver/<tailnet>.ts.net`. |
| `references/troubleshooting.md` | Any of the symptoms in the table above whose row points here — ACL gate diagnosis, 502 vs 403 disambiguation, stale-DNS-cache wait. |
| `references/make-local-template.md` | The user asks to wire `make local` (or `make tunnel`, `make share`) into a project Makefile, or wants the full script set instead of inlining. Walks through `scripts/funnel-up.sh` and `scripts/funnel-down.sh`. |

## Output contract

When the workflow completes successfully, surface to the user:

1. The public URL (one line, copyable)
2. Which Funnel slot was used and which loopback port it forwards to
3. The teardown command they can run later (`tailscale funnel --https=<port> off`)
4. Any preexisting mappings the preflight surfaced — they will want to know nothing else got disturbed

When it fails, surface:

1. Which rung in Step 6 failed (rung 1, 2, or 3) — this tells the user where to look
2. The exact command that failed and its output
3. The next action the user needs to take (the troubleshooting table maps every common failure to a concrete action)

## Guardrails

- Never `tailscale funnel reset` or `tailscale serve reset` without an explicit user request and a snapshot of `tailscale serve status` first
- Never enable Funnel as a side effect of an unrelated request. Funnel exposes the app to the public internet — the user must explicitly ask for that scope. "Make this work on my phone" is *not* a request for Funnel; that's "install Tailscale on the phone."
- Never claim "Funnel works" until Rung 3 (external client) succeeds. Rungs 1 and 2 prove the path exists; only Rung 3 proves real-world clients can use it.
- Never use bare `host` or bare `dig` (no `@server`) to verify user-facing DNS on macOS. Use `curl --noproxy '*'` or `dscacheutil`.
- Default to `127.0.0.1` bind for backends behind Funnel. `0.0.0.0` is a security regression for this use case — every interface gets the dev server. Funnel does not require it.
