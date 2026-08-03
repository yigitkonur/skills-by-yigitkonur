# run-agent-browser

A Claude/Codex skill for reliable browser automation with the installed
`agent-browser` CLI, this host's private Steel Browser CDP service, and its
separate authenticated Patchright scrape pool.

Last reconciled against the installed CLI (`agent-browser --version`),
<https://agent-browser.dev/cdp-mode>, the live Steel Browser deployment
(`/root/dev/zeo-crawler-omniroute/deploy/steel-browser/README.md`), and the
live `patchright-browserpool` Coolify application. The current version pin
lives in `SKILL.md`.

The installed CLI remains the syntax authority:

```bash
agent-browser skills get core --full
agent-browser COMMAND --help
agent-browser --version
```

## Runtime map

| Runtime | Use it for | Entry point |
|---|---|---|
| Steel Browser | Normal interactive web/UI automation, refs, screenshots, deployment verification | `env -u AGENT_BROWSER_PROVIDER agent-browser --cdp "$STEEL_AGENT_BROWSER_CDP" ...` |
| Patchright pool | Structured Google AI Overview/Mode and Gemini captures through rotating proxies | Authenticated HTTP `POST /scrape` (not CDP) |
| Provider | Browser Use, Kernel, Browserless, AgentCore, etc. | `AGENT_BROWSER_PROVIDER` / `-p` |
| Auto-connect/raw CDP | Intentional attachment to an existing local Chrome/profile | `--auto-connect` or `connect <port|url>` |

## Key local facts

- Steel env file: `~/.config/steel-browser-cdp.env` (chmod 600, sourced by
  `.zshrc`); exact endpoint roles, ports, and tailnet equivalents are in
  `SKILL.md` and `references/cdp-and-steel.md`.
- Steel is one shared Chromium with single-session semantics — serialize Steel
  tasks; see `references/cdp-and-steel.md`.
- A global Browser Use provider is set on this machine. Explicit CDP commands
  must use `env -u AGENT_BROWSER_PROVIDER ...` or the CLI rejects the mixed
  runtime.
- Patchright pool: purpose-built authenticated scrape API, no CDP socket;
  capacity and limits are in `references/managed-cdp-pool.md`.

## Skill layout

- `SKILL.md` — runtime selection and operating loop.
- `references/cdp-and-steel.md` — Steel endpoints, `connect`, `--cdp`, sessions,
  provider conflict, tailnet security, live proof.
- `references/managed-cdp-pool.md` — Patchright pool API, credential handling,
  capacity, retries, response semantics.
- `references/commands.md` — current everyday CLI routing.
- `references/sessions-and-refs.md` — refs, tabs, sessions, restore/auth state.
- `references/trust-boundaries.md` — prompt injection, secrets and outward
  actions.
- `references/safety.md` — recovery and shared-runtime safety.
- `references/advanced.md` — providers, profiling, traces, engines and advanced
  features.
- `scripts/` and `assets/templates/` — reusable helpers; ad hoc browser tasks
  remain one-command-at-a-time.

## Minimal Steel smoke test

Run each command separately and read the output before the next:

```bash
source "$HOME/.config/steel-browser-cdp.env"
env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-smoke --cdp "$STEEL_AGENT_BROWSER_CDP" open https://example.com
env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-smoke --cdp "$STEEL_AGENT_BROWSER_CDP" snapshot -i
env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-smoke --cdp "$STEEL_AGENT_BROWSER_CDP" get title
env -u AGENT_BROWSER_PROVIDER agent-browser --session steel-smoke close
curl -fsS -X POST "$STEEL_API_URL/v1/sessions/release"   # full reset; close only detaches
```

See `references/cdp-and-steel.md` for the full runtime-identity proof and
troubleshooting ladder.
