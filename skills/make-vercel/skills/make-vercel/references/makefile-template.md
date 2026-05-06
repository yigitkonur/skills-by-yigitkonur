# Makefile template — copy and customize

The Vercel-flavored equivalent of make-railway's deploy. GNU Make 3.81 compatible.

## Placeholders

| Placeholder | Default | Notes |
|---|---|---|
| `PROD_URL` | `https://<project>.vercel.app` | Custom domain or default vercel.app URL. |
| `PROJECT_NAME` | from `package.json` | Used in banners. |

## Full template

```makefile
SHELL := /bin/bash

# ── Public URLs (post-deploy reachability check) ──────────────
PROD_URL := https://app.example.com
# Vercel-issued fallback: https://my-project.vercel.app

# ── ANSI palette ──────────────────────────────────────────────
B := \033[1m
D := \033[2m
G := \033[32m
Y := \033[33m
R := \033[31m
C := \033[36m
Z := \033[0m

.PHONY: deploy preview verify env-pull env-add logs install-hooks _check-prereqs

# ── make deploy (production) ──────────────────────────────────
deploy: _check-prereqs
	@sha=$$(git rev-parse --short HEAD); \
	branch=$$(git rev-parse --abbrev-ref HEAD); \
	if [ -n "$$(git status --porcelain 2>/dev/null | head -1)" ]; then \
	  printf "$(Y)WARN$(Z) deploying with uncommitted changes\n"; \
	fi; \
	tag="$$branch@$$sha"; \
	printf "$(B)→ Vercel production deploy: $$tag$(Z)\n"; \
	url=$$(vercel --prod --yes 2>&1 | tee /tmp/vercel-deploy.log | grep -oE 'https://[^ ]+\.vercel\.app' | tail -1); \
	if [ -n "$$url" ]; then \
	  printf "  $(G)✓$(Z) deployed to $$url\n"; \
	else \
	  printf "  $(R)✗ deploy failed — see /tmp/vercel-deploy.log$(Z)\n"; \
	  exit 1; \
	fi; \
	printf "\n$(B)Live URL$(Z)\n"; \
	printf "  $(G)→$(Z) $(PROD_URL)\n"; \
	printf "\n$(D)HTTP check:  make verify$(Z)\n"

# ── make preview (per-commit preview deploy) ──────────────────
preview: _check-prereqs
	@printf "$(B)→ Vercel preview deploy$(Z)\n"
	@url=$$(vercel deploy --yes 2>&1 | tee /tmp/vercel-preview.log | grep -oE 'https://[^ ]+\.vercel\.app' | tail -1); \
	if [ -n "$$url" ]; then \
	  printf "  $(G)✓$(Z) preview at $$url\n"; \
	  printf "$(D)Aliasing requires:  vercel alias $$url <your-preview-domain>$(Z)\n"; \
	else \
	  printf "  $(R)✗ preview failed$(Z)\n"; exit 1; \
	fi

# ── verification ──────────────────────────────────────────────
verify:
	@printf "$(D)→ HTTP probe$(Z)\n"
	@code=$$(curl -s -L -o /dev/null -w "%{http_code}" --max-time 12 $(PROD_URL)/ || echo "ERR"); \
	case $$code in \
	  2*|3*) printf "  $(G)$$code$(Z) $(PROD_URL)\n" ;; \
	  *)     printf "  $(R)$$code$(Z) $(PROD_URL)\n" ;; \
	esac

# ── env management ────────────────────────────────────────────
env-pull:
	@printf "$(D)→ pulling Vercel env into .env.local$(Z)\n"
	@vercel env pull .env.local --environment=development
	@printf "$(G)✓ .env.local updated (development scope)$(Z)\n"

env-add:
	@printf "Add a key:  vercel env add KEY production\n"
	@printf "Remove:     vercel env rm KEY production\n"
	@printf "List:       vercel env ls\n"

# ── observability ─────────────────────────────────────────────
logs:
	@vercel logs $(PROD_URL) --follow

# ── git hooks installer (shared with make-railway) ────────────
install-hooks:
	@bash scripts/install-hooks.sh

# ── pre-flight ────────────────────────────────────────────────
_check-prereqs:
	@command -v vercel >/dev/null 2>&1 || { \
	  printf "$(R)vercel CLI not found$(Z)  $(D)npm install -g vercel$(Z)\n"; exit 1; }
	@vercel whoami >/dev/null 2>&1 || { \
	  printf "$(R)not logged into Vercel$(Z)  $(D)vercel login$(Z)\n"; exit 1; }
	@[ -d .vercel ] || { \
	  printf "$(R)project not linked$(Z)  $(D)vercel link$(Z)\n"; exit 1; }
```

## Notes on adapting

- **No custom domain yet:** `PROD_URL` can be the auto-generated `<project>.vercel.app`. Update later when you assign a domain.
- **Preview deploy URLs:** Vercel auto-assigns. The `make preview` target captures it from CLI output — if Vercel changes the format, update the regex.
- **Multi-environment Make targets:** add `make deploy-staging` if you have a staging environment configured.
- **`vercel deploy --target production`** vs `vercel --prod`: equivalent. The Makefile uses `--prod` because it's shorter.
- **`--yes` flag:** non-interactive; auto-confirms prompts. Good for scripts. Drop for first-time deploy if you want to inspect the prompts.

## Companion `vercel.json` (optional)

Most Next.js projects don't need this. Add only when:

```json
{
  "buildCommand": "cd apps/web && npm run build",
  "outputDirectory": "apps/web/.next",
  "framework": "nextjs",
  "git": {
    "deploymentEnabled": {
      "main": true,
      "develop": false
    }
  },
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" }
      ]
    }
  ]
}
```

See `references/vercel-config.md` for the full schema.
