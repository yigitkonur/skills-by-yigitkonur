# Vercel Deployment

> Notes for deploying the Supastarter Next.js app to Vercel. Consult this when setting environment variables or understanding how base URLs resolve in production.

## Environment variables

At minimum, production needs:

- `NEXT_PUBLIC_SITE_URL`
- `DATABASE_URL`
- `BETTER_AUTH_SECRET`
- chosen mail/provider keys
- payment keys + price IDs if billing is enabled
- storage credentials if uploads are enabled

## Base URL behavior

`packages/utils/lib/base-url.ts` reads Vercel-specific environment variables when present, which is why preview/production deployments should have their site URL configured cleanly.

## Practical checklist

1. Set all required env vars in Vercel project settings
2. Ensure the database is reachable from Vercel
3. Configure auth callback/site URLs consistently
4. Add public asset/image hosts in `next.config.ts` when needed

---

**Related references:**
- `references/setup/environment-setup.md` — Full environment variable catalog
- `references/utils.md` — Base URL helper behavior
- `references/setup/next-config.md` — Image and plugin configuration that affects deploys
- `references/deployment/environment-checklist.md` — Pre-deployment checklist
