---
name: run-agent-browser
description: "Use if driving agent-browser for webpage interaction, screenshots, @ref snapshots, tabs, UI verification, CDP attach, Steel Browser, or cloud providers (Browser Use, Browserbase, Browserless, Kernel)."
allowed-tools: Bash(npx agent-browser:*), Bash(agent-browser:*), Bash(env:*agent-browser:*), Bash(curl:*)
---

# run-agent-browser

Drive `agent-browser` as a live terminal REPL: one command, read the result, then decide the next. Never chain ad hoc browser work in a script or `&&` unless the user asked for a reusable harness.

**Escalate; never dead-end.** If a tier fails, diagnose once, then move to the next tier. If every automated tier fails, ask the user for credentials / a CDP URL / a deploy decision — do not stop with "can't."

## Authority

```bash
agent-browser skills get core
agent-browser COMMAND --help
agent-browser --version
```

Installed CLI help wins on syntax. This skill owns **runtime selection and failure escalation** for this host.

## Priority ladder (always start at tier 1)

| Tier | When | How |
|---|---|---|
| **1. Plain local** | Default for every new task | Unset provider env; launch local Chrome with stealth args |
| **2. Steel CDP** | Tier 1 fails (no Chrome, display, sandbox, or user asked for managed CDP) | Source Steel env; attach via `--cdp`; details in `references/cdp-and-steel.md` |
| **3. Cloud provider** | Tier 2 fails or unavailable | Browser Use → Kernel → Browserless → Browserbase (or user-named); details in `references/providers.md` |
| **4. Ask user** | All tiers fail or no credentials | Request CDP URL, provider key, or approval to install/deploy — then configure and retry |

Special cases (skip the ladder only when clearly required):

| Need | Route |
|---|---|
| Public URL text only | `agent-browser read URL` (no browser) |
| Google AI Overview / AI Mode / Gemini capture | Patchright scrape API — `references/managed-cdp-pool.md` (not CDP) |
| User-launched Chrome with existing auth | `--auto-connect` or `connect <port\|url>` — `references/cdp-and-steel.md` |
| Electron / Slack / AgentCore sandbox | `agent-browser skills get <name>` specialized skill |

## Stealth is the default (every tier)

Always prefer anti-automation defaults. There is no official `agent-browser-plugin-stealth` npm package (404); use built-ins + provider stealth flags:

```bash
# Local / Steel launch args (tier 1; also apply when launching unmanaged Chrome)
STEALTH_ARGS='--disable-blink-features=AutomationControlled'

# Browserless: stealth ON by default (BROWSERLESS_STEALTH=true)
# Kernel: stealth OFF by default — always set KERNEL_STEALTH=true for this skill
# Proxy (optional, all tiers): --proxy "$AGENT_BROWSER_PROXY" when configured
```

Never put proxy passwords, API keys, or cookie values in command output, commits, or chat.

## Tier 1 — plain local (start here)

This host loads `AGENT_BROWSER_PROVIDER=browseruse` from `~/.config/agent-browser-browseruse.env`. **Always unset it for tier 1**, or you will silently hit a cloud provider instead of local Chrome.

```bash
SESSION="local-$(agent-browser session id --scope cwd --prefix task)"

env -u AGENT_BROWSER_PROVIDER \
  agent-browser --session "$SESSION" \
  --args "--disable-blink-features=AutomationControlled" \
  open https://example.com

env -u AGENT_BROWSER_PROVIDER agent-browser --session "$SESSION" snapshot -i
env -u AGENT_BROWSER_PROVIDER agent-browser --session "$SESSION" get title
env -u AGENT_BROWSER_PROVIDER agent-browser --session "$SESSION" close
```

**Treat as tier-1 failure and escalate** when you see: Chrome/Chromium not found, display/Xvfb errors, sandbox/`--no-sandbox` crashes, CDP bind failures, repeated blank pages with no DOM, or the user is on a machine without a local browser (CI, remote-only laptop).

If the error is specifically `Cannot use --cdp and -p/--provider together`, you mixed tiers — drop `-p`/`AGENT_BROWSER_PROVIDER` for CDP, or drop `--cdp` for a provider.

## Tier 2 — Steel CDP (self-hosted on this fleet)

Read **`references/cdp-and-steel.md`** before changing endpoints or diagnosing attach failures. Short path:

```bash
source "$HOME/.config/steel-browser-cdp.env"   # no-op if missing — then ask user / deploy
# If STEEL_AGENT_BROWSER_CDP is empty: ask user for a CDP websocket URL, or offer to deploy Steel
# (deploy path: Coolify compose in zeo-crawler-omniroute/deploy/steel-browser/ — use deploy-coolify-cloud skill)

SESSION="steel-$(agent-browser session id --scope cwd --prefix task)"

# Optional clean slate (Steel is single-session / shared page — see reference)
curl -fsS -X POST "$STEEL_API_URL/v1/sessions/release" >/dev/null 2>&1 || true

env -u AGENT_BROWSER_PROVIDER \
  agent-browser --session "$SESSION" --cdp "$STEEL_AGENT_BROWSER_CDP" \
  open https://example.com

env -u AGENT_BROWSER_PROVIDER agent-browser --session "$SESSION" --cdp "$STEEL_AGENT_BROWSER_CDP" snapshot -i
env -u AGENT_BROWSER_PROVIDER agent-browser --session "$SESSION" --cdp "$STEEL_AGENT_BROWSER_CDP" close
curl -fsS -X POST "$STEEL_API_URL/v1/sessions/release" >/dev/null 2>&1 || true   # full reset; close only detaches
```

**Critical Steel facts (do not skip):** one shared Chromium with effectively one page; serialize Steel tasks; `--session` isolates daemon state only; `close` detaches, `POST …/v1/sessions/release` resets. Full semantics, ports, tailnet URLs, and troubleshooting: `references/cdp-and-steel.md`.

**Escalate to tier 3** when: env file missing and user has no CDP URL; health/`/json/version` fail; attach refused after one recovery attempt; or Steel serialization blocks a needed parallel task.

If the user only has a raw CDP link (any host), use tier-2 mechanics with that URL:

```bash
env -u AGENT_BROWSER_PROVIDER agent-browser --session cdp-user --cdp "$USER_SUPPLIED_CDP_WS" open https://example.com
```

## Tier 3 — cloud providers (ask, configure, retry)

Read **`references/providers.md`** for env files, stealth defaults, and install. Order when the user has not named a provider:

1. **Browser Use** (`-p browseruse`) — key often already on this host  
2. **Kernel** (`-p kernel`) — set `KERNEL_STEALTH=true`  
3. **Browserless** (`-p browserless`) — stealth on by default  
4. **Browserbase** (`-p browserbase`) — only if key present / user provides  

```bash
# Example: Browser Use (do NOT print the key)
source "$HOME/.config/agent-browser-browseruse.env"   # if present
# If BROWSER_USE_API_KEY empty → ask user for the key; write to that env file (chmod 600); source; retry

SESSION="prov-$(agent-browser session id --scope cwd --prefix task)"
env -u AGENT_BROWSER_PROVIDER \
  agent-browser --session "$SESSION" -p browseruse \
  open https://example.com
```

Always pass `-p <name>` explicitly in commands (do not rely on a sticky global `AGENT_BROWSER_PROVIDER` for the whole session — it breaks Steel/CDP later). Never combine `-p` with `--cdp`.

**If no provider key exists:** ask the user which provider they want and for the API key (or dashboard invite). Offer to:

- write `~/.config/agent-browser-<provider>.env` (`chmod 600`) and a guarded `~/.zshrc` source line;
- open the provider dashboard URL from `references/providers.md`;
- re-run the failed step after config.

Do not invent keys. Do not paste key values into chat, commits, or logs — confirm with "key present / length only."

## Tier 4 — still blocked

Ask for **one** of, then configure and retry from the matching tier:

1. A CDP websocket URL (`ws://` / `wss://`) or host:port for an existing Chrome  
2. A provider name + API key (Browser Use / Kernel / Browserless / Browserbase)  
3. Approval to **install** local Chrome / `agent-browser` (`npm i -g agent-browser`, `agent-browser install`)  
4. Approval to **deploy** self-hosted Steel (this fleet: Coolify compose under `deploy/steel-browser/`)  

## Core interaction loop (any tier)

Use the same runtime prefix on every command in the flow:

```bash
# PREFIX is tier-1 env -u … --session … --args …   OR tier-2 … --cdp …   OR tier-3 … -p <name>
$PREFIX open https://example.com
$PREFIX snapshot -i          # refs like @e3 — never @ref=e3
$PREFIX click @e3
$PREFIX wait --url "**/expected"
$PREFIX snapshot -i          # refs stale after navigation — always re-snapshot
$PREFIX get url
$PREFIX get title
$PREFIX errors
$PREFIX close
```

Verify outcomes separately from action success. Screenshots when visual proof matters.

## Helpers

| Path | Use |
|---|---|
| `scripts/check-agent-browser-version.sh` | Read-only CLI + Steel + pool health |
| `scripts/inspect-page.sh` | Steel page capture harness |
| `assets/templates/*.sh` | Reusable workflows (only when user asked for a harness) |
| `references/cdp-and-steel.md` | Steel endpoints, single-session semantics, release, tailnet, CDP attach |
| `references/providers.md` | Browser Use / Browserbase / Browserless / Kernel setup, stealth, credentials |
| `references/managed-cdp-pool.md` | Patchright Google AI/Gemini scrape API |
| `references/commands.md` | Everyday command routing |
| `references/sessions-and-refs.md` | Refs, tabs, restore, auth vault |
| `references/safety.md` | Recovery ladder, shared-runtime safety |
| `references/trust-boundaries.md` | Secrets, injection, outward actions |
| `references/advanced.md` | Proxy, recording, engines, React |

## Output contract

Report: final URL/title + user-visible outcome; **which tier** ran (and any escalation); session name; deterministic checks; cleanup performed (incl. Steel `sessions/release` if used); artifacts + sensitivity; credentials requested or files written (**names only**, never values); any install/deploy recommendation left for the user.
