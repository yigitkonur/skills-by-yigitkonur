# Cloud providers for agent-browser

Use when tier 1 (local) and tier 2 (Steel/CDP) failed, or the user named a cloud browser. Official docs:

- https://agent-browser.dev/providers/browser-use
- https://agent-browser.dev/providers/browserbase
- https://agent-browser.dev/providers/browserless
- https://agent-browser.dev/providers/kernel

`-p <name>` always wins over `AGENT_BROWSER_PROVIDER`. **Never combine `-p` with `--cdp`.**

## Credential hygiene

- Keys live only in `~/.config/*.env` files, `chmod 600`, sourced from `~/.zshrc` with a guarded line.
- Never print key values. Confirm with "present" / character length only.
- Prefer process-local `source` + `-p` over exporting a sticky global provider for the whole shell (globals break Steel/CDP later on this host).

## Default preference order

| Order | Provider | CLI | Required env | Stealth default | Local env file on this host |
|---|---|---|---|---|---|
| 1 | Browser Use | `-p browseruse` | `BROWSER_USE_API_KEY` | n/a (cloud) | `~/.config/agent-browser-browseruse.env` |
| 2 | Kernel | `-p kernel` | `KERNEL_API_KEY` | `KERNEL_STEALTH=false` → **set true** | `~/.config/agent-browser-kernel.env` |
| 3 | Browserless | `-p browserless` | `BROWSERLESS_API_KEY` | `BROWSERLESS_STEALTH=true` (default) | `~/.config/browserless.env` |
| 4 | Browserbase | `-p browserbase` | `BROWSERBASE_API_KEY` | n/a | *(not configured here)* |

If the user names a provider, use that name regardless of order.

## Browser Use

Docs: https://agent-browser.dev/providers/browser-use  
Dashboard: Browser Use Cloud Dashboard (API key + free credits).

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
| `401` / unauthorized from provider | Key missing/wrong — re-ask user, rewrite env file |
| Provider timeout | Raise Kernel/Browserless TTL; retry once; else next provider |
| Local Chrome missing | Tier 2 Steel, else tier 3 |
| All providers fail | Tier 4 — ask for CDP URL or deploy approval |
