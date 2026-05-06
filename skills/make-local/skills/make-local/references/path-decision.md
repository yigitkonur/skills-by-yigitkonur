# Path decision — portless vs Tailscale Serve vs plain LAN bind

Three local-dev paths exist for a reason. Pick by the user's actual constraint, not by what sounds modern.

## Decision matrix

| User need | Path | URL | Cert | First-run cost |
|---|---|---|---|---|
| "I want a stable URL on my Mac, no setup" | **portless** | `https://<name>.localhost` | Local CA (auto-trusted) | sudo prompt × 1 |
| "I want my phone/MacBook to reach my dev server" | **Tailscale Serve** | `http://<node>.ts.net` | Let's Encrypt (real CA) | `tailscale serve --bg --http=80 PORT` |
| "I want LAN access without DNS, or CI" | **plain bind** | `http://0.0.0.0:PORT` | none | nothing |
| "I want a stakeholder demo over the public internet" | **Tailscale Funnel** | `https://<node>.ts.net` (public) | Let's Encrypt | `tailscale funnel --bg PORT` — explicit opt-in only |

## Short version

- **`make local`** → portless. Daily driver.
- **`make tunnel`** → Tailscale Serve. Cross-device (phone, MacBook, iPad).
- **`make local-lan`** → plain bind. Headless CI, phone-on-Wi-Fi when MagicDNS fails, wget/curl from another machine.

## Why three, not one

Each path has a hard failure mode:

| Path | Hard failure |
|---|---|
| portless | `*.localhost` resolves to 127.0.0.1 *on every machine in the world* per RFC 6761 — your phone hits its own loopback, not yours |
| Tailscale Serve | Requires Tailscale signed in. Phone-on-cellular-not-on-tailnet can't reach |
| plain bind | No HTTPS, no friendly URL, has to know the IP, port can collide |

The Makefile that ships all three lets the user pick the right one at the moment of need without re-deciding.

## When NOT to use each

- **Skip portless** when the project's auth/cookies break across `.localhost` siblings (rare, but happens with strict `SameSite` + cookie domain rules).
- **Skip Tailscale Serve** when the user isn't on a tailnet at all. Don't try to install Tailscale for them — that's outside this skill.
- **Skip plain bind** when the user explicitly wants HTTPS (some Next.js features and Web APIs require secure contexts: `navigator.clipboard`, `Notification`, service workers).

## Funnel is opt-in only

Tailscale Funnel exposes the dev server **to the public internet**. Reset it on every `make tunnel` run:

```sh
tailscale funnel reset >/dev/null 2>&1 || true
```

Never default `make tunnel` to Funnel. If a user explicitly asks for "share my dev with someone outside my tailnet" — that's the only context where `tailscale funnel --bg PORT` is appropriate, and it should require explicit confirmation.
