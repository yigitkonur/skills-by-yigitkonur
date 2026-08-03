# check-agent-browser-version.sh

Verifies the local environment for `run-agent-browser` execution.

## What it checks

1. `agent-browser` CLI executable (falls back to `npx --no-install agent-browser`).
2. Version satisfies minimum requirement (default `0.33.2`).
3. Installed version-matched `core` skill is available.
4. `~/.config/steel-browser-cdp.env` exists and exports all expected Steel variables (`STEEL_AGENT_BROWSER_CDP`, `STEEL_HEALTH_URL`, `STEEL_CDP_VERSION_URL`, `STEEL_UI_URL`).
5. Steel REST API health (`STEEL_HEALTH_URL`) returns 2xx.
6. Steel CDP discovery endpoint (`STEEL_CDP_VERSION_URL`) returns 2xx.
7. Presence of any global `AGENT_BROWSER_PROVIDER` environment variable (warns if CDP commands need `env -u AGENT_BROWSER_PROVIDER`).
8. Patchright scrape pool `/health` API on `https://browserpool.65.108.140.207.sslip.io/health`.

## Usage

```bash
bash scripts/check-agent-browser-version.sh
bash scripts/check-agent-browser-version.sh 0.33.2
```

## Exit codes

- `0` — All checks passed.
- `2` — Invalid minimum-version argument format.
- `3` — CLI version output parse failure.
- `4` — Minimum version not satisfied.
- `5` — Installed core skill unavailable.
- `6` — `steel-browser-cdp.env` unreadable.
- `7` — Required Steel environment variables missing.
- `8` — Steel API health failed.
- `9` — Steel CDP version endpoint failed.
- `10` — Patchright scrape pool health failed.

Read-only: never installs packages, launches Chrome, exposes credentials, or alters environment/provider settings.
