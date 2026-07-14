# port-slot-management — the 443/8443/10000 inventory

Tailscale Funnel exposes traffic on **exactly three ports** per node:

- **443** — produces the clean URL `https://<node>.<tailnet>.ts.net/`
- **8443** — produces `https://<node>.<tailnet>.ts.net:8443/`
- **10000** — produces `https://<node>.<tailnet>.ts.net:10000/`

Each port can host exactly one mapping. There is no fourth slot, and there is no concept of multiple mappings per port. When you run `tailscale funnel --bg --https=<port> <target>`, you are either creating the mapping (if the slot is free) or **silently replacing** the previous one (if it's taken). No warning, no confirmation.

`tailscale funnel reset` and `tailscale serve reset` wipe **all** Serve and Funnel mappings on the node — including unrelated projects, including production tunnels, including whatever the user's coworker set up last week. There is no undo. Never run these as cleanup, ever, without explicit user authorization and a snapshot first.

## The mandatory preflight

Before claiming any Funnel slot:

```bash
# Both commands. They show overlapping but not identical info.
tailscale serve status
tailscale funnel status
```

`tailscale serve status` shows the full set of Serve and Funnel mappings (Funnel is implemented on top of Serve). `tailscale funnel status` shows only the public-internet-facing subset. Read both to get a complete picture, especially because tailnet-only Serve mappings on Funnel-eligible ports prevent Funnel from claiming the port.

Example output worth recognizing:

```text
# Funnel on:
#     - https://macmini.tail2fcc55.ts.net:10000
#     - https://mini.tail2fcc55.ts.net

https://macmini.tail2fcc55.ts.net:10000 (Funnel on)
|-- / proxy http://127.0.0.1:3000

https://macmini.tail2fcc55.ts.net (tailnet only)
|-- / proxy http://127.0.0.1:3400

https://macmini.tail2fcc55.ts.net:8443 (tailnet only)
|-- / proxy http://127.0.0.1:3100
```

In this example: port 443 is taken (tailnet-only, pointing at :3400), port 8443 is taken (tailnet-only, pointing at :3100), port 10000 is taken by Funnel (pointing at :3000). All three slots are occupied.

## Decision tree for picking a slot

1. **Is `443` free in both `tailscale serve status` and `tailscale funnel status`?** Use `443`. You get the cleanest URL with no port number.
2. **Is `8443` free?** Use `8443`. URL will be `https://<fqdn>:8443/` — works fine, port number visible.
3. **Is `10000` free?** Use `10000`. Same deal.
4. **All three taken?** Stop. The next two sections cover takeover and recovery.

If multiple are free, prefer `443` for the cleanest UX.

## When all three slots are taken

Two recovery paths. **Always tell the user before doing either** — these touch other projects.

### Path A — Snapshot, take over, restore

Best for short-lived work (a one-time agent-browser test, a 10-minute demo). Pick the slot whose current mapping is least sensitive (`tailnet only` and pointing at a service the user doesn't currently need accessible from outside is the safest). Take a snapshot, take over, restore when done.

```bash
# 1. Snapshot what's there (paste into a scratch file or print to terminal)
tailscale serve status   > /tmp/tailscale-snapshot-$(date +%s).txt
tailscale funnel status >> /tmp/tailscale-snapshot-$(date +%s).txt

# 2. Note the exact target the slot currently points at, e.g. http://127.0.0.1:3000
#    (you'll need it for restoration)

# 3. Remove the existing mapping (only this port — never `reset`)
tailscale funnel --https=10000 off
# or for a tailnet-only Serve mapping on a Funnel-eligible port:
tailscale serve --https=8443 off

# 4. Claim the slot for your task
tailscale funnel --bg --https=10000 http://127.0.0.1:<your-port>

# 5. When you're done, restore the original mapping
tailscale funnel --bg --https=10000 http://127.0.0.1:3000
# or:
tailscale serve --bg --https=8443 http://127.0.0.1:<original-port>
```

This is the path the skill's `scripts/funnel-up.sh` uses when invoked with the `--takeover` flag, and `scripts/funnel-down.sh` is what handles restoration when the snapshot file is present.

### Path B — Ask the user which mapping to retire

Some Funnel mappings are no longer needed (forgotten from a previous demo, pointing at a port that's no longer running). The user is the only one who knows which. List the mappings clearly:

```text
All three Funnel slots are taken on this node. To proceed, one needs to be freed:

  443  → http://127.0.0.1:3400  (tailnet only)
  8443 → http://127.0.0.1:3100  (tailnet only)
  10000 → http://127.0.0.1:3000 (Funnel on — public)

Which one would you like to free? Or should I snapshot and take over the
least-sensitive one (10000 → :3000) for this session and restore it later?
```

Let the user choose. Never assume which mapping is OK to disturb.

## The "tailnet only" vs "Funnel on" distinction

Tailscale's `serve` and `funnel` commands manage the same port-slot inventory, but with different visibility:

- `tailscale serve --https=8443 http://127.0.0.1:<port>` → reachable from other devices on the tailnet (private)
- `tailscale funnel --https=8443 http://127.0.0.1:<port>` → reachable from the public internet (and from the tailnet)

A port can be in one of three states: free, tailnet-only (Serve), or public (Funnel). A tailnet-only Serve mapping on a Funnel-eligible port still blocks Funnel from claiming the slot. You must `tailscale serve --https=<port> off` before you can `tailscale funnel --bg --https=<port>` against that port.

This is why the preflight runs *both* `serve status` and `funnel status` — Serve mappings on Funnel ports are invisible to the Funnel command but block it.

## "What ports does my node actually have?"

`tailscale status --json` includes the daemon's view of the node. To check if your tailnet supports Funnel at all, the simplest test is `tailscale funnel --bg --https=<port> http://127.0.0.1:1` against any free slot and inspect the output. If you get "Funnel requires HTTPS Certificates", the tailnet ACL gate is closed (see `troubleshooting.md` § ACL gate). If you get a `Funnel on` line, you're good.

## Things that are not solutions

- **Funnel on other ports** (444, 8080, 9443, etc.) — does not exist. Tailscale only allows 443, 8443, 10000.
- **Running multiple mappings on the same port** — does not exist. One mapping per slot.
- **`tailscale funnel reset` to "start clean"** — wipes every Serve and Funnel mapping on the node, not just this session's. Never do it.
- **`pkill tailscaled`** — daemon restart does not clear mappings. They're persisted in the daemon's state.
