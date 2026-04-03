# Analytics Providers

> Documents the analytics module entry point and its provider-based structure. Consult this when enabling analytics or switching between supported providers.

## Key file

- `apps/web/modules/analytics/index.tsx`

## What the module does

- exports the active analytics implementation
- organizes provider-specific code under `provider/*`
- keeps analytics bootstrapping separate from general app providers

## Supported providers in the codebase

The module tree includes adapters for custom analytics plus common hosted services such as Google Analytics, Mixpanel, Pirsch, Plausible, PostHog, Umami, and Vercel analytics.

## Practical rule

The app should import the analytics module through its shared entry point rather than reaching into provider internals.

---

**Related references:**
- `references/analytics/consent-flow.md` — Consent gate around analytics behavior
- `references/routing/providers-document.md` — Where analytics script wiring lives
- `references/setup/environment-setup.md` — Analytics env vars
- `references/cheatsheets/env-vars.md` — Environment variable reference
