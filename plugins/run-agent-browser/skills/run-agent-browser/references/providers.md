# Cloud providers for agent-browser

Use when tier 1 (local) and tier 2 (Steel/CDP) failed, or the user named a cloud browser. Official docs:

- https://agent-browser.dev/providers/browser-use
- https://agent-browser.dev/providers/browserbase
- https://agent-browser.dev/providers/browserless
- https://agent-browser.dev/providers/kernel

`-p <name>` always wins over `AGENT_BROWSER_PROVIDER`. **Never combine `-p` with `--cdp`.**

## Credential hygiene

- Keys live only in `~/.config/*.env` files with `chmod 600`; source them process-locally unless the user explicitly chooses a guarded shell startup line.
- Never print key values. Confirm with "present" / character length only.
- Prefer process-local `source` + `-p` over exporting a sticky global provider for the whole shell (globals break Steel/CDP later on this host).

## Default preference order

| Order | Provider | CLI | Required env | Stealth default | Local env file on this host |
|---|---|---|---|---|---|
| 1 | Browser Use | `-p browseruse` | `BROWSER_USE_API_KEY` | n/a (cloud) | `~/.config/agent-browser-browseruse.env` — **known-broken here, see below** |
| 2 | Kernel | `-p kernel` | `KERNEL_API_KEY` | `KERNEL_STEALTH=false` → **set true** | `~/.config/agent-browser-kernel.env` — verified working |
| 3 | Browserless | `-p browserless` | `BROWSERLESS_API_KEY` | `BROWSERLESS_STEALTH=true` (default) | `~/.config/browserless.env` — verified working |
| 4 | Browserbase | `-p browserbase` | `BROWSERBASE_API_KEY` | n/a | *(not configured here)* |

If the user names a provider, use that name regardless of order.

**Browser Use known-broken (this host, agent-browser 0.33.2, checked 2026-08-03):** `-p browseruse` fails every attempt with `✗ CDP WebSocket connect failed: HTTP error: 400 Bad Request` — reproduced across fresh session names, with `-v`/`--debug`, and doc-verbatim syntax with no custom session. The key itself is valid: authenticated `GET/POST` probes to the sessions API return `200`, session creation succeeds, and the session's own `webSocketDebuggerUrl` accepts a raw WebSocket upgrade. The fault is in agent-browser's Browser Use connect path, not the account, key, or network. Do not retry `-p browseruse` after one `400` — go straight to Kernel. Re-test only if the user reports an agent-browser version bump past 0.33.2.

## Browser Use

Docs: https://agent-browser.dev/providers/browser-use  
Dashboard: Browser Use Cloud Dashboard (API key + free credits).

**Known-broken on this host as of 2026-08-03 — see the note in "Default preference order" above before spending a retry on it.**

```bash
# ~/.config/agent-browser-browseruse.env
export BROWSER_USE_API_KEY="…"   # value never committed or printed
```

```bash
source "$HOME/.config/agent-browser-browseruse.env"
env -u AGENT_BROWSER_PROVIDER agent-browser --session bu-task -p browseruse open https://example.com
env -u AGENT_BROWSER_PROVIDER agent-browser --session bu-task -p browseruse snapshot -i
env -u AGENT_BROWSER_PROVIDER agent-browser --session bu-task -p browseruse close
```

## Kernel

Docs: https://agent-browser.dev/providers/kernel  
Always enable stealth for this skill.

| Variable | Default | Skill policy |
|---|---|---|
| `KERNEL_API_KEY` | required | from env file |
| `KERNEL_HEADLESS` | `true` | leave true unless user wants headed |
| `KERNEL_STEALTH` | `false` | **export `KERNEL_STEALTH=true`** |
| `KERNEL_TIMEOUT_SECONDS` | `300` | raise if long jobs |
| `KERNEL_PROFILE_NAME` | none | set only when user wants persistent cookies/logins |

```bash
source "$HOME/.config/agent-browser-kernel.env"
export KERNEL_STEALTH=true
env -u AGENT_BROWSER_PROVIDER agent-browser --session kn-task -p kernel open https://example.com
```

## Browserless

Docs: https://agent-browser.dev/providers/browserless  
Stealth defaults **on**.

| Variable | Default |
|---|---|
| `BROWSERLESS_API_KEY` | required |
| `BROWSERLESS_API_URL` | `https://production-sfo.browserless.io` |
| `BROWSERLESS_BROWSER_TYPE` | `chromium` |
| `BROWSERLESS_TTL` | `300000` (ms) |
| `BROWSERLESS_STEALTH` | `true` |

```bash
source "$HOME/.config/browserless.env"
env -u AGENT_BROWSER_PROVIDER agent-browser --session bl-task -p browserless open https://example.com
```

## Browserbase

Docs: https://agent-browser.dev/providers/browserbase  
Not preconfigured on this host — ask for `BROWSERBASE_API_KEY` before use.

```bash
# create ~/.config/agent-browser-browserbase.env (chmod 600) after user provides key
export BROWSERBASE_API_KEY="…"
env -u AGENT_BROWSER_PROVIDER agent-browser --session bb-task -p browserbase open https://example.com
```

## Configuring a missing provider (tier 4 handoff)

When a key is missing:

1. Tell the user which provider and which env var is needed (name only).
2. Point them at the provider dashboard from the official docs above.
3. After they supply the key (chat paste, 1Password, etc.), write:

```bash
umask 077
cat > "$HOME/.config/agent-browser-<provider>.env" <<EOF
export <PROVIDER>_API_KEY='…'   # from user; never re-echo
EOF
chmod 600 "$HOME/.config/agent-browser-<provider>.env"
```

4. Append once to `~/.zshrc` if absent:

```bash
[[ -r "$HOME/.config/agent-browser-<provider>.env" ]] && source "$HOME/.config/agent-browser-<provider>.env"
```

5. `source` the file in the current shell and retry the failed step with `-p <provider>`.
6. Confirm success with title/URL/snapshot — not by printing the key.

## Install / deploy alternatives

| Gap | Offer |
|---|---|
| No `agent-browser` binary | `npm install -g agent-browser` then `agent-browser install` (Chrome) |
| No local Chrome and no cloud key | Deploy Steel (this fleet: `deploy/steel-browser` via Coolify) **or** pick a paid provider |
| MacBook / remote tailnet client | Use Steel tailnet endpoints (`references/cdp-and-steel.md`) or a cloud provider; local Chrome optional |

## Failure signals → next action

| Symptom | Action |
|---|---|
| `Cannot use --cdp and -p/--provider together` | Drop one of the two; re-run |
| `CDP WebSocket connect failed: HTTP error: 400 Bad Request` from `-p browseruse` | Known-broken on this host (see above) — do not retry, skip straight to Kernel |
| `401` / unauthorized from provider | Key missing/wrong — re-ask user, rewrite env file |
| Provider timeout | Raise Kernel/Browserless TTL; retry once; else next provider |
| Local Chrome missing | Tier 2 Steel, else tier 3 |
| All providers fail | Tier 4 — ask for CDP URL or deploy approval |
