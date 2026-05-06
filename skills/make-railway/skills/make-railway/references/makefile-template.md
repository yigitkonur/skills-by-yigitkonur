# Makefile template — copy and customize

The canonical zeo-radar `make prod` block, sanitized to placeholders. GNU Make 3.81 compatible.

## Placeholders

| Placeholder | Default | Notes |
|---|---|---|
| `WEB_SERVICES` | `app` | Space-separated Railway service names. Multi-service: `web worker`. |
| `URL_PROD_PRIMARY` | `https://<svc>.up.railway.app` | First URL probed by `make verify`. |
| `URL_PROD_SECONDARY` | (omit if single service) | Second URL probed by `make verify`. |

## Full template

```makefile
SHELL := /bin/bash

# ── Railway service registry ───────────────────────────────────
WEB_SERVICES := app

# ── Public URLs (post-deploy reachability check) ──────────────
URL_PROD_PRIMARY := https://app-production.up.railway.app
# URL_PROD_SECONDARY := https://noauth.example.com

# ── ANSI palette ──────────────────────────────────────────────
B := \033[1m
D := \033[2m
G := \033[32m
Y := \033[33m
R := \033[31m
C := \033[36m
Z := \033[0m

.PHONY: prod verify status logs install-hooks _check-prod-prereqs

# ── make prod ─────────────────────────────────────────────────
# Parallel `railway up` for every web service. Each upload is fire-
# and-forget (--detach); we wait on all forks via `wait`, then poll
# for terminal status. Deploy message embeds git sha + branch +
# dirty marker so Railway's deploy log is forensically useful.
prod: _check-prod-prereqs
	@sha=$$(git rev-parse --short HEAD); \
	branch=$$(git rev-parse --abbrev-ref HEAD); \
	if [ -n "$$(git status --porcelain 2>/dev/null | head -1)" ]; then \
	  dirty="+dirty"; \
	  printf "$(Y)WARN$(Z) deploying with uncommitted changes\n"; \
	else \
	  dirty=""; \
	fi; \
	tag="$$branch@$$sha$$dirty"; \
	printf "$(B)→ Deploying $$tag to Railway$(Z)\n"; \
	for svc in $(WEB_SERVICES); do \
	  log=/tmp/railway-deploy-$$svc.log; \
	  rm -f $$log; \
	  printf "  $(D)$$svc — uploading...$(Z)\n"; \
	  ( railway up --detach --service $$svc -m "make prod $$tag" >$$log 2>&1; \
	    code=$$?; \
	    if [ $$code -ne 0 ]; then \
	      printf "  $(R)✗ $$svc upload failed (exit $$code) — see $$log$(Z)\n"; \
	    fi ) & \
	done; \
	wait; \
	for svc in $(WEB_SERVICES); do \
	  log=/tmp/railway-deploy-$$svc.log; \
	  url=$$(grep -oE 'https://railway\.com[^ ]*id=[a-f0-9-]+' $$log | head -1); \
	  if [ -n "$$url" ]; then \
	    printf "  $(G)✓$(Z) $$svc uploaded — build log: $$url\n"; \
	  fi; \
	done; \
	printf "\n$(D)→ Polling Railway until services reach a terminal status...$(Z)\n"; \
	tries=0; max=80; \
	while [ $$tries -lt $$max ]; do \
	  s=$$(railway service status --all 2>/dev/null); \
	  pending=$$(printf "%s\n" "$$s" | grep -E "$$(echo $(WEB_SERVICES) | tr ' ' '|')" \
	    | grep -iE 'BUILDING|DEPLOYING|INITIALIZING|QUEUED|REMOVING|WAITING' | wc -l | tr -d ' '); \
	  if [ "$$pending" = "0" ]; then break; fi; \
	  sleep 8; tries=$$((tries+1)); \
	done; \
	printf "\n$(B)Final status$(Z)\n"; \
	railway service status --all | grep -E "NAME|$$(echo $(WEB_SERVICES) | tr ' ' '|')" || true; \
	printf "\n$(B)Live URLs$(Z)\n"; \
	printf "  $(G)→$(Z) $(URL_PROD_PRIMARY)\n"; \
	if [ -n "$(URL_PROD_SECONDARY)" ]; then \
	  printf "  $(G)→$(Z) $(URL_PROD_SECONDARY)\n"; \
	fi; \
	printf "\n$(D)HTTP check:  make verify$(Z)\n"

# ── verification ──────────────────────────────────────────────
verify:
	@printf "$(D)→ HTTP probe$(Z)\n"
	@for u in $(URL_PROD_PRIMARY) $(URL_PROD_SECONDARY); do \
	  if [ -z "$$u" ]; then continue; fi; \
	  code=$$(curl -s -L -o /dev/null -w "%{http_code}" --max-time 12 $$u/ || echo "ERR"); \
	  case $$code in \
	    2*|3*) printf "  $(G)$$code$(Z) $$u\n" ;; \
	    *)     printf "  $(R)$$code$(Z) $$u\n" ;; \
	  esac; \
	done

# ── observability ─────────────────────────────────────────────
status:
	@railway service status --all

logs:
	@railway logs --service $(firstword $(WEB_SERVICES)) --tail 50

# ── git hooks installer ───────────────────────────────────────
install-hooks:
	@bash scripts/install-hooks.sh

# ── pre-flight ────────────────────────────────────────────────
_check-prod-prereqs:
	@command -v railway >/dev/null 2>&1 || { \
	  printf "$(R)railway CLI not found$(Z)  $(D)brew install railway$(Z)\n"; exit 1; }
	@railway whoami >/dev/null 2>&1 || { \
	  printf "$(R)not logged into Railway$(Z)  $(D)railway login$(Z)\n"; exit 1; }
	@railway status >/dev/null 2>&1 || { \
	  printf "$(R)no Railway project linked$(Z)  $(D)railway link$(Z)\n"; exit 1; }
```

## Notes on adapting

- **Single service:** drop `URL_PROD_SECONDARY` and the conditional probe.
- **Many services (3+):** the loop already handles arbitrary count; just add to `WEB_SERVICES`.
- **Custom domains:** set `URL_PROD_PRIMARY` to the custom domain. Railway's edge resolves both.
- **Deploy on push:** wire `prod` from `.git/hooks/post-receive` if the repo is a bare-mirror style; otherwise prefer `make prod` invoked manually from the contributor's machine.
- **Dry-run:** add a `--dry-run` flag detection at the top of `prod`; just print "would run: railway up --detach -s X" without executing.
