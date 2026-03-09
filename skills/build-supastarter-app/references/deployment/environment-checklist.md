# Deployment Environment Checklist

> Condensed pre-flight list for any hosted deployment. Consult this before shipping a new environment.

## Core checks

- Database URL points to the correct environment
- Better Auth secret is set
- Site URL / docs URL are correct
- Mail provider configuration matches the environment
- Payment provider keys and price IDs match the correct workspace/account
- Storage bucket and endpoint credentials are configured
- Optional analytics and AI keys are present only if those features are enabled

## After deploy

- Verify auth pages load
- Verify the marketing homepage or SaaS redirect matches feature flags
- Verify a signed-in dashboard request succeeds
- Verify uploads and billing links if those features are used

---

**Related references:**
- `references/deployment/vercel.md` — Vercel-specific notes
- `references/cheatsheets/env-vars.md` — Short env-var cheat sheet
- `references/deployment/local-services.md` — Local service parity during development
