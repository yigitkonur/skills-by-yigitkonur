# Makefile template — copy and customize

This is the canonical zeo-radar Makefile, sanitized to placeholders. Targets at GNU Make 3.81 (macOS system default — no `.ONESHELL`, no fancy 4.x features). Works on Linux too.

## Placeholders to replace

| Placeholder | Default | Notes |
|---|---|---|
| `PROJECT_NAME` | from `package.json` `"name"` | Sans npm scope. Becomes `<NAME>.localhost`. |
| `PORT` | `3456` | For `make local-lan`. Pick far from 3000 (OrbStack squat zone). |
| `TUNNEL_PORT` | `3001` | For `make tunnel`. Different from `PORT` so both can run. |
| `DEV_CMD` | `npm run dev` | `pnpm dev` / `bun dev` if applicable. |
| `URL_PROD` (optional) | — | Production URL for `make verify`. |

## Full template

```makefile
SHELL := /bin/bash

# ── Local dev defaults ─────────────────────────────────────────
PORT        ?= 3456
HOST        ?= 0.0.0.0
TUNNEL_PORT ?= 3001

# ── ANSI palette (no-op on dumb terminals) ────────────────────
B := \033[1m
D := \033[2m
G := \033[32m
Y := \033[33m
R := \033[31m
C := \033[36m
Z := \033[0m

.DEFAULT_GOAL := help

.PHONY: help local local-lan tunnel tunnel-stop stop clean \
        _ensure-portless _ensure-services _free-port \
        _print-portless-banner _print-local-lan-banner

# ── help ──────────────────────────────────────────────────────
help:
	@printf "$(B)PROJECT_NAME$(Z)  $(D)— make targets$(Z)\n\n"
	@printf "  $(B)$(G)make local$(Z)         portless → $(B)https://PROJECT_NAME.localhost$(Z) $(D)(daily driver)$(Z)\n"
	@printf "  $(C)make local-lan$(Z)     direct $(HOST):$(PORT) for phone-on-Wi-Fi\n"
	@printf "  $(C)make tunnel$(Z)        Tailscale Serve → http://<node>.ts.net (cross-device)\n"
	@printf "  $(C)make tunnel-stop$(Z)   reset Tailscale serve/funnel + stop dev on :$(TUNNEL_PORT)\n"
	@printf "  $(C)make stop$(Z)          kill dev server on :$(PORT)\n"
	@printf "  $(C)make clean$(Z)         stop + wipe Turbopack cache\n"
	@printf "\n$(D)Override port:  make local-lan PORT=4000$(Z)\n"

# ── make local — portless, primary ────────────────────────────
local: _ensure-portless _ensure-services _print-portless-banner
	@npx portless

# ── make local-lan — direct binding, fallback ─────────────────
local-lan: _free-port _ensure-services _print-local-lan-banner
	@HOSTNAME=$(HOST) PORT=$(PORT) DEV_CMD -- --hostname $(HOST) --port $(PORT)

# ── make tunnel — Tailscale Serve ─────────────────────────────
# Default HTTP — see references/hsts-preload-trap.md for why HTTPS often makes things WORSE.
tunnel: _ensure-services
	@command -v tailscale >/dev/null 2>&1 || { \
	  printf "$(R)tailscale CLI not found — brew install --cask tailscale$(Z)\n"; exit 1; }
	@tailscale status >/dev/null 2>&1 || { \
	  printf "$(R)Tailscale not signed in — open the menu-bar icon and log in$(Z)\n"; exit 1; }
	@pid=$$(lsof -ti :$(TUNNEL_PORT) 2>/dev/null || true); \
	if [ -n "$$pid" ]; then \
	  cmd=$$(ps -p $$pid -o comm= 2>/dev/null | tr -d ' \t'); \
	  case "$$cmd" in \
	    *node|*node\ *|*next*|*turbopack*|next-server) \
	      printf "$(Y)→ port $(TUNNEL_PORT) busy with stale dev (pid $$pid, $$cmd) — reclaiming$(Z)\n"; \
	      kill -9 $$pid 2>/dev/null || true; sleep 0.4 ;; \
	    *) \
	      printf "$(R)port $(TUNNEL_PORT) held by $$cmd (pid $$pid). Won't clobber.$(Z)\n"; \
	      printf "$(D)  override:  make tunnel TUNNEL_PORT=3002$(Z)\n"; exit 1 ;; \
	  esac; \
	fi
	@printf "$(D)→ resetting Tailscale serve/funnel (security: turning off any prior public exposure)$(Z)\n"
	@tailscale funnel reset >/dev/null 2>&1 || true
	@tailscale serve  reset >/dev/null 2>&1 || true
	@if [ "$(TUNNEL_TLS)" = "1" ]; then \
	  tailscale serve --bg --https=443 $(TUNNEL_PORT) >/dev/null; \
	  scheme=https; \
	else \
	  tailscale serve --bg --http=80 $(TUNNEL_PORT) >/dev/null; \
	  scheme=http; \
	fi; \
	node=$$(tailscale status --json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['Self']['DNSName'].rstrip('.'))" 2>/dev/null); \
	short=$${node%%.*}; \
	printf "\n$(B)$(G)PROJECT_NAME dev$(Z)  $(D)Tailscale Serve · tailnet only$(Z)\n"; \
	printf "  $(C)→$(Z) $(B)$$scheme://$$node$(Z)\n"; \
	printf "  $(C)→$(Z) $$scheme://$$short  $(D)(short MagicDNS)$(Z)\n"; \
	printf "  $(C)→$(Z) http://localhost:$(TUNNEL_PORT)\n"
	@printf "  $(D)stop:  make tunnel-stop      Funnel is OFF      try TUNNEL_TLS=1 for HTTPS$(Z)\n\n"
	@PORT=$(TUNNEL_PORT) HOSTNAME=127.0.0.1 DEV_CMD -- --port $(TUNNEL_PORT) --hostname 127.0.0.1

tunnel-stop:
	@tailscale serve  reset >/dev/null 2>&1 || true
	@tailscale funnel reset >/dev/null 2>&1 || true
	@pid=$$(lsof -ti :$(TUNNEL_PORT) 2>/dev/null || true); \
	if [ -n "$$pid" ]; then kill -9 $$pid 2>/dev/null || true; fi
	@printf "$(D)tailscale serve + funnel reset; dev on :$(TUNNEL_PORT) stopped$(Z)\n"

# ── housekeeping ──────────────────────────────────────────────
stop:
	@pid=$$(lsof -ti :$(PORT) 2>/dev/null || true); \
	if [ -n "$$pid" ]; then \
	  kill -9 $$pid 2>/dev/null || true; \
	  printf "$(Y)killed pid $$pid on :$(PORT)$(Z)\n"; \
	else \
	  printf "$(D)nothing on :$(PORT)$(Z)\n"; \
	fi

clean: stop
	@rm -rf .next/cache && printf "$(G)wiped .next/cache$(Z)\n"

# ── private helpers ───────────────────────────────────────────
_ensure-portless:
	@if [ ! -x node_modules/.bin/portless ]; then \
	  if [ -d node_modules ]; then npm install --silent; \
	  else printf "$(R)node_modules not present — npm install first$(Z)\n"; exit 1; \
	  fi; \
	fi

# Best-effort docker-compose start. Non-fatal — UI-only work doesn't need DB.
_ensure-services:
	@if docker info >/dev/null 2>&1; then \
	  if [ -f docker-compose.yml ] || [ -f compose.yml ]; then \
	    if ! docker compose ps --services --filter status=running 2>/dev/null | grep -q .; then \
	      printf "$(D)→ starting compose services...$(Z)\n"; \
	      docker compose up -d >/dev/null 2>&1 || true; \
	    fi; \
	  fi; \
	else \
	  printf "$(Y)Docker not running — DB-backed pages may error.$(Z)\n"; \
	fi

# Free port: only kill OUR processes (node/next/turbopack), refuse strangers.
_free-port:
	@pid=$$(lsof -ti :$(PORT) 2>/dev/null || true); \
	if [ -z "$$pid" ]; then exit 0; fi; \
	cmd=$$(ps -p $$pid -o comm= 2>/dev/null | tr -d ' \t'); \
	case "$$cmd" in \
	  *node|*node\ *|*next*|*turbopack*|next-server) \
	    printf "$(Y)→ port $(PORT) busy with stale dev (pid $$pid, $$cmd) — reclaiming$(Z)\n"; \
	    kill -9 $$pid 2>/dev/null || true; \
	    sleep 0.4 ;; \
	  *) \
	    next=$$(( $(PORT) + 10 )); \
	    printf "$(R)port $(PORT) held by $$cmd (pid $$pid). Won't clobber.$(Z)\n"; \
	    printf "$(D)  • If you know it's safe:  kill -9 $$pid$(Z)\n"; \
	    printf "$(D)  • Or pick another port:    make local-lan PORT=$$next$(Z)\n"; \
	    exit 1 ;; \
	esac

_print-portless-banner:
	@printf "\n$(B)$(G)PROJECT_NAME dev$(Z)  $(D)portless · HTTPS$(Z)\n"
	@printf "  $(C)→$(Z) $(B)https://PROJECT_NAME.localhost$(Z)\n"
	@if [ ! -d $$HOME/.portless ] && [ ! -d "$$HOME/Library/Application Support/portless" ]; then \
	  printf "  $(Y)first run on this machine — sudo prompts incoming for cert + :443$(Z)\n"; \
	fi
	@printf "  $(D)stop:  Ctrl+C$(Z)\n\n"

_print-local-lan-banner:
	@printf "\n$(B)$(G)PROJECT_NAME dev$(Z)  $(D)direct $(HOST):$(PORT) (LAN)$(Z)\n"
	@printf "  $(C)→$(Z) http://localhost:$(PORT)\n"
	@ifconfig 2>/dev/null | awk '/inet / && $$2 != "127.0.0.1" {print $$2}' | head -4 \
	  | while read ip; do printf "  $(C)→$(Z) http://$$ip:$(PORT)  $(D)(LAN)$(Z)\n"; done
	@printf "  $(D)stop:  make stop      cache panic:  make clean$(Z)\n\n"
```

## Companion `portless.json`

```json
{ "name": "PROJECT_NAME" }
```

That's it. Don't pass `--name` flags everywhere; the config is single-source-of-truth.

## Companion `package.json` change

```json
{
  "devDependencies": {
    "portless": "^0.12.0"
  }
}
```

Pin via lockfile so contributors get the same proxy version.

## Notes on adapting

- For `pnpm`/`bun`: replace `DEV_CMD` and the `npm install` calls.
- For non-Next frameworks: drop the `--hostname` and `--port` flag passing — most frameworks read `HOST`/`PORT` env vars (which are already set).
- For monorepos: define `PROJECT_NAME`/`PORT`/`TUNNEL_PORT` once per app and namespace the targets (`make local-web`, `make local-admin`).
