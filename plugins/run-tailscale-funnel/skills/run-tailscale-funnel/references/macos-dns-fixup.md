# macos-dns-fixup — the resolver split that makes Funnel "work on phone, fail on this Mac"

The single largest source of "Tailscale Funnel doesn't work" on macOS is the resolver-chain split. The Tailscale daemon knows the right answer for `<node>.<tailnet>.ts.net`, and `dig @100.100.100.100` confirms it. But `curl` says "Could not resolve host" on the same Mac. Same daemon, same FQDN, same shell. Both are correct — they're hitting different resolvers.

## Why this happens

macOS has multiple DNS paths. They behave differently:

| Tool | Resolver path | Reads `/etc/resolver/`? |
|---|---|---|
| `host`, `dig` (no `@server`) | libresolv → `/etc/resolv.conf` (BIND-style) | **no** |
| `dig @100.100.100.100` (explicit `@server`) | direct UDP to that resolver | n/a |
| `curl`, browsers, `getaddrinfo()`, app code | mDNSResponder + lookupd | **yes** |
| `dscacheutil -q host -a name <fqdn>` | mDNSResponder + lookupd | **yes** |

`/etc/resolver/<domain>` is macOS' canonical split-DNS mechanism. A file like `/etc/resolver/ts.net` containing `nameserver 100.100.100.100` tells mDNSResponder: "for any `*.ts.net` lookup, ask `100.100.100.100` directly." That resolver lives inside the Tailscale daemon. mDNSResponder's clients (curl, browsers, native macOS APIs, anything that calls `getaddrinfo()`) honor it. BIND-style tools (`dig` without `@server`, `host`) ignore it entirely.

This produces the most confusing diagnostic in the whole system:

```bash
$ host mini.tail2fcc55.ts.net
Host mini.tail2fcc55.ts.net not found: 3(NXDOMAIN)

$ curl -sI https://mini.tail2fcc55.ts.net/
HTTP/2 200
```

Both correct. `host` only ever queries `/etc/resolv.conf` (or whatever was set there at boot — typically the ISP's DNS). `curl` reads `/etc/resolver/ts.net` (if present) and asks the Tailscale daemon, which knows the answer.

**Rule**: Trust `curl --noproxy '*'` and `dscacheutil -q host -a name <fqdn>` when verifying user-facing behavior. Use `host` and bare `dig` only when you want to see *public* DNS state (which Funnel updates separately from MagicDNS).

## When you need to install `/etc/resolver/<tailnet>.ts.net`

You need this file when:

- `dig @100.100.100.100 <fqdn>` returns the right tailnet IP, but `curl <fqdn>` says "Could not resolve host"
- The URL works from another machine (phone on cellular, friend's laptop) but not from this Mac
- `tailscale dns status` says "Tailscale DNS: enabled" but actual lookups still fail

The Tailscale.app from the App Store usually installs this for you (it has the macOS DNS network-extension entitlement). The Homebrew `tailscale`/`tailscaled` formula does **not** — its daemon runs but doesn't have entitlement to install the network extension. Same fix in either case:

## Installing the resolver file

```bash
sudo mkdir -p /etc/resolver
sudo tee /etc/resolver/ts.net >/dev/null <<EOF
nameserver 100.100.100.100
EOF
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

The file is named after the **top-level tailnet domain** (`ts.net`), not your specific tailnet name. One file covers every tailnet you're a member of.

If you're on a tailnet with a custom domain (organization with their own tailnet domain), you'll need a resolver file for that too — the file name should match the suffix of your FQDN. For most users, `ts.net` is the right name.

## Verification

After installing, confirm the resolver is loaded:

```bash
scutil --dns | grep -A3 'domain *: ts.net'
# Expected:
# resolver #N
#   domain   : ts.net
#   nameserver[0] : 100.100.100.100
#   reach    : 0x00000002 (Reachable)
```

Then confirm a real lookup works:

```bash
dscacheutil -q host -a name <node>.<tailnet>.ts.net
# Expected: name + ip_address line(s), 100.x.y.z (your tailnet IP)

curl -sI https://<node>.<tailnet>.ts.net/
# Expected: HTTP/2 200 (or whatever your app returns)
```

If `scutil` shows the resolver but `dscacheutil` returns nothing, the daemon doesn't know the FQDN either — check `tailscale status --json | python3 -c "import json,sys; print(json.load(sys.stdin)['Self']['DNSName'])"` matches what you're querying.

## The AAAA-only trap

When Funnel is enabled, Tailscale publishes **both** A (IPv4) and AAAA (IPv6) records on public DNS. Some resolver chains on clients without IPv6 transit (most home wifi) return *only* the AAAA records. The client gets an IPv6 address it can't route to:

```bash
$ dscacheutil -q host -a name mini.tail2fcc55.ts.net
name: mini.tail2fcc55.ts.net
ipv6_address: 2607:f740:0:3f::2f0
ipv6_address: 2607:f740:0:3f::3cc
# no ipv4_address — curl will fail

$ curl -m 10 https://mini.tail2fcc55.ts.net/
curl: (6) Could not resolve host
```

The fix is the same `/etc/resolver/ts.net` install above. With the resolver file in place, the lookup routes through Tailscale's daemon, which returns the **tailnet IPv4** (`100.x.y.z`) directly — bypassing the public Funnel ingress entirely and skipping the IPv6 problem.

This is the failure mode where two Macs on the same tailnet disagree: the first Mac (Tailscale.app from App Store, `/etc/resolver/ts.net` installed automatically by the network extension) works. The second Mac (Homebrew Tailscale, no resolver file) returns AAAA-only and curl fails. Apply the same fix on both.

## What to trust when debugging

- **`dscacheutil -q host -a name <fqdn>`** — what curl and browsers will see
- **`curl --noproxy '*' -sS https://<fqdn>/`** — end-to-end, user-facing
- **`scutil --dns`** — what resolvers are loaded
- **`dig @100.100.100.100 <fqdn>`** — what Tailscale's daemon knows
- **`dig @ns1.dnsimple.com <fqdn>`** — what *public* DNS knows (this is what people outside your tailnet see)

What **not** to trust:

- **`host <fqdn>`** without `@server` — ignores `/etc/resolver/`, lies about resolution on macOS
- **`dig <fqdn>`** without `@server` — same as `host`
- **`nslookup <fqdn>`** — same

These three commands are not wrong for any other purpose; they're wrong for **verifying tailnet-DNS behavior on macOS**.

## The `/usr/local/bin/tailscale` stub trap

If you've used both the App Store Tailscale.app and the Homebrew formula (e.g., uninstalled one to install the other), you may have a stub at `/usr/local/bin/tailscale`:

```sh
#!/bin/sh
/Applications/Tailscale.app/Contents/MacOS/tailscale "$@"
```

This was installed by the App Store version. If you've since removed the app, every `tailscale` command tries to exec a non-existent binary. Either remove the stub or patch it to forward to your active binary:

```bash
sudo tee /usr/local/bin/tailscale >/dev/null <<'EOF'
#!/bin/sh
exec /opt/homebrew/bin/tailscale "$@"
EOF
sudo chmod +x /usr/local/bin/tailscale
```

Or remove the stub and put `/opt/homebrew/bin` (Apple Silicon) or `/usr/local/Cellar/tailscale/<version>/bin` (Intel) first in PATH.

If `tailscale --version` errors out, this is usually why.
