# CDP mode and Steel Browser on this host

Read this when attaching `agent-browser` to an existing Chrome/Chromium instance, using Steel Browser, choosing `connect` versus `--cdp`, diagnosing endpoint errors, or attaching from the tailnet.

## Current local configuration

`~/.config/steel-browser-cdp.env` is sourced by `~/.zshrc` and exports:

| Variable | Purpose |
|---|---|
| `STEEL_AGENT_BROWSER_CDP` / `STEEL_CDP_WS` | Steel session/CDP connect endpoint for `agent-browser`, Puppeteer, and Playwright: `ws://127.0.0.1:21301` |
| `STEEL_API_URL` | Steel REST API: `http://127.0.0.1:21301` |
| `STEEL_HEALTH_URL` | API health: `/v1/health` |
| `STEEL_CDP_HTTP` | Chrome CDP discovery/debugger proxy: `http://127.0.0.1:21303` |
| `STEEL_CDP_VERSION_URL` | Chrome `/json/version` endpoint |
| `STEEL_UI_URL` | Steel UI: `http://127.0.0.1:21305` |
| `*_TAILNET` | Same services at Tailscale IP `100.109.134.50` |

The env file intentionally does **not** set a generic `AGENT_BROWSER_CDP` variable because this machine also has provider runtimes and a separate Patchright scrape API. CDP must be selected explicitly per command/session.

For non-interactive shells:

```bash
source "$HOME/.config/steel-browser-cdp.env"
```

## Endpoint architecture

Steel exposes two distinct WebSocket layers:

1. `ws://127.0.0.1:21301` — Steel's browser/session connection endpoint. Use this with `agent-browser`, Puppeteer `browserWSEndpoint`, and Playwright `connectOverCDP`.
2. `http://127.0.0.1:21303` — nginx proxies this to Chrome's internal `9222`. It serves `/json/version`, `/json/list`, `/devtools/browser/<uuid>`, and `/devtools/page/<id>`.

A `/devtools/page/<id>` socket is a page target, not the browser endpoint expected by `agent-browser connect`. If the Steel root endpoint is rejected by a client, obtain the browser-level URL:

```bash
curl -fsS "$STEEL_CDP_VERSION_URL" | jq -r .webSocketDebuggerUrl
```

Pass that value directly to `connect`. Never log it when it contains credentials (the local Steel URL does not, but remote providers commonly embed tokens).

### Why Steel's reported browser URL may omit host port

The current `/json/version` value can look like:

```text
ws://127.0.0.1/devtools/browser/<uuid>
```

The discovery response reflects Chrome/nginx host headers and is not the main Steel session endpoint. Prefer `STEEL_AGENT_BROWSER_CDP`; use `/json/version` only as a fallback or identity probe.

## `--cdp` versus `connect`

### Repeat endpoint on every command

```bash
env -u AGENT_BROWSER_PROVIDER agent-browser \
  --session steel-task \
  --cdp "$STEEL_AGENT_BROWSER_CDP" \
  open https://example.com
```

This is explicit and easiest to audit. Keep the same session and endpoint for the entire flow.

### Register once, reuse later

```bash
env -u AGENT_BROWSER_PROVIDER agent-browser \
  --session steel-task connect "$STEEL_AGENT_BROWSER_CDP"

env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-task open https://example.com
env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-task snapshot -i
env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-task close
```

`connect <port|url>` accepts:

- numeric local CDP port (`9222` -> `http://localhost:9222`),
- `http://` or `https://` discovery endpoint,
- complete browser-level `ws://` or `wss://` URL.

Use a named session because the retained association lives in agent-browser session state. Do not assume it is global, process-local, or safe to share with another agent.

### Auto-connect

```bash
env -u AGENT_BROWSER_PROVIDER agent-browser --session attached --auto-connect open example.com
```

Auto-connect searches Chrome's `DevToolsActivePort`, then common ports 9222/9229, then direct WebSocket fallback. Use it for a user-launched local Chrome when you intentionally want that profile. Do not use it when Steel is required: auto-discovery can attach to the wrong browser.

## Provider conflict on this machine

No rc file auto-sources `AGENT_BROWSER_PROVIDER=browseruse` into a fresh interactive zsh (verified 2026-08-03: `~/.zshrc` does not source `agent-browser-browseruse.env` or `agent-browser-kernel.env`). `~/.bashrc` does auto-source `agent-browser-kernel.env`, which leaves:

```text
AGENT_BROWSER_PROVIDER=kernel
```

The same variable also gets exported into the current shell when you manually `source` a provider env file that defines it (the Browser Use and Kernel files currently do; Browserless exports only its key). Either path collides with CDP:

```text
Cannot use --cdp and -p/--provider together
```

For explicit CDP commands, unset only that variable for the process:

```bash
env -u AGENT_BROWSER_PROVIDER agent-browser --cdp "$STEEL_AGENT_BROWSER_CDP" snapshot -i
```

Do not delete or globally overwrite provider config merely to use Steel. Conversely, do not unset it when the user explicitly chose Browser Use or another provider.

## Sessions and concurrency

Steel OSS has **single-session semantics**: exactly one live/idle Steel session exists at any time.

- `POST /v1/sessions` silently destroys and replaces the previous session — it vanishes from the list with no released record. Creating a session is destructive to any in-flight work.
- Every session's `websocketUrl` is the identical fixed endpoint `ws://127.0.0.1:21301/`; there is no per-session URL.
- All agent-browser sessions attached to Steel share one Chromium and effectively one page — verified live: client A opened example.com, client B opened iana.org, and A's tab listing then showed iana.org while `/json/list` held exactly one page (B had navigated A's page away).
- Concurrent browser tasks against Steel therefore clobber each other. **Serialize Steel work**: one task at a time, finish and clean up before the next. Parallel browser agents must not drive Steel simultaneously — route parallel needs to a provider runtime or separate local sessions.
- `--session <name>` isolates agent-browser **daemon** state only (refs, bookkeeping) — not browser state. Still generate one session name per task so daemon state never collides, but never treat it as browser isolation or a security boundary:

```bash
SESSION="steel-$(agent-browser session id --scope cwd --prefix verify)"
```

- `agent-browser close` only **detaches** that client; pages persist in the shared browser after close. A full reset requires the Steel API — `curl -fsS -X POST "$STEEL_API_URL/v1/sessions/release"` — after which Steel auto-creates a fresh idle session with a clean `about:blank` browser. Never use `close --all`.

### Steel session API

| Endpoint | Effect |
|---|---|
| `GET /v1/sessions` | List the current (single) session |
| `POST /v1/sessions` | Replaces the current session — destructive to any in-flight work |
| `POST /v1/sessions/release` | Release the current session; Steel auto-creates a fresh idle one |
| `POST /v1/sessions/{sessionId}/release` | Per-id release variant |

Both release endpoints are `POST`; there is no `DELETE`. The live spec is served at `$STEEL_API_URL/documentation/openapi.json` (Scalar UI at `/documentation`).

### Recommended task lifecycle

1. Health check: `curl -fsS "$STEEL_HEALTH_URL"`.
2. Optionally `POST /v1/sessions/release` first when a clean slate matters — page state from earlier tasks may linger.
3. Do the work in one named agent-browser session.
4. `close` to detach.
5. `POST /v1/sessions/release` to reset the browser if the task loaded sensitive or bulky state.
6. Re-check health.

## Tailnet access

From this host use loopback. From another tailnet device use:

- `STEEL_CDP_WS_TAILNET=ws://100.109.134.50:21301`
- `STEEL_API_URL_TAILNET=http://100.109.134.50:21301`
- `STEEL_CDP_HTTP_TAILNET=http://100.109.134.50:21303`
- `STEEL_UI_URL_TAILNET=http://100.109.134.50:21305`

The public server IP must refuse 21301/21303/21305. Steel has no API authentication and gives complete browser control, including cookies, JavaScript execution, and private-network requests. Never bind these ports to `0.0.0.0` or proxy them publicly without a separately designed authentication/authorization layer.

## Live verification sequence

Run one step at a time:

```bash
source "$HOME/.config/steel-browser-cdp.env"
curl -fsS "$STEEL_HEALTH_URL"
curl -fsS "$STEEL_CDP_VERSION_URL" | jq '{Browser, Protocol-Version, webSocketDebuggerUrl}'

env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-proof --cdp "$STEEL_AGENT_BROWSER_CDP" open https://example.com
env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-proof --cdp "$STEEL_AGENT_BROWSER_CDP" snapshot -i
env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-proof --cdp "$STEEL_AGENT_BROWSER_CDP" get url
env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-proof --cdp "$STEEL_AGENT_BROWSER_CDP" get title
env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-proof --cdp "$STEEL_AGENT_BROWSER_CDP" errors
curl -fsS "$STEEL_CDP_HTTP/json/list" | jq '[.[] | select(.type == "page") | {title,url}]'
env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-proof close
curl -fsS -X POST "$STEEL_API_URL/v1/sessions/release"
curl -fsS "$STEEL_HEALTH_URL"
```

`/json/list` retaining the opened page after `close` is expected — `close` only detaches the client, so the lingering page is not a leak bug; the `sessions/release` call cleans it and leaves a fresh `about:blank` session.

A complete proof shows:

- Steel API healthy before/after,
- Chrome `/json/version` available,
- agent-browser navigation and snapshot succeed,
- URL/title/DOM expected,
- Steel `/json/list` contains that page (runtime identity),
- no browser errors relevant to the task,
- cleanup (detach + release) does not stop the Steel service.

## Troubleshooting

| Symptom | Check / fix |
|---|---|
| Provider/CDP mutual-exclusion error | Use `env -u AGENT_BROWSER_PROVIDER` for the CDP process. |
| Steel env variable empty | Source `~/.config/steel-browser-cdp.env`; interactive `.zshrc` loading is not guaranteed in Bash/noninteractive agents. |
| 21301 refused | `curl "$STEEL_HEALTH_URL"`; check Coolify Steel containers and loopback bindings. Do not immediately mutate agent-browser state. |
| 21303 refused | Check Steel api container/nginx and `/json/version`; 21301 may still be healthy while raw discovery is not. |
| Root ws URL rejected | Fetch `/json/version`, pass its browser-level `webSocketDebuggerUrl` to `connect`. |
| Browser URL has no port | Prefer the Steel root endpoint; the discovery URL reflects upstream Host handling. |
| Wrong browser/page | Use a new named session; compare `get cdp-url`, `get url`, and Steel `/json/list`. |
| Stale refs after reconnect | Snapshot again; refs never survive reconnect/navigation reliably. |
| `--allowed-domains` rejected | Expected for pre-existing CDP; enforce egress outside the attached browser. |
| Cleanup might affect shared browser | Close task-owned tabs/session only; verify Steel health and avoid `close --all`. |
