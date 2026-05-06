# Environment Variables

TinaCMS env vars work in **two contexts** with different rules: the site build (your Next.js app) and the admin build (the TinaCMS editor SPA at `/admin`). Confusing them is the most common deployment failure.

## The two contexts

| Context | Read by | Available at |
|---|---|---|
| **Site build** | Your Next.js app (server + client code) | Any `process.env.*` |
| **Admin build** | The TinaCMS admin SPA (statically built, served from `/admin`) | Only **explicitly admin-exposed** vars |

The admin SPA is a **static build** — env vars are embedded into its JavaScript at `tinacms build` time. They are not read at runtime. If you set a var **after** running `tinacms build`, it has no effect on the admin.

## Build-time embedding

```
tinacms build
   ↓ reads env vars at build time
   ↓ embeds them into admin/index.js
   ↓ outputs to public/admin/

# After build, the admin can never see new env vars
# until you rebuild
```

This means:

- Setting an env var on Vercel after deploy doesn't affect the deployed admin until you redeploy.
- Local `.env` changes need a rebuild to reflect in admin.
- Sensitive secrets must NOT be admin-exposed — they'd leak into the publicly served `index.js`.

## Required env vars (TinaCloud projects)

```env
NEXT_PUBLIC_TINA_CLIENT_ID=<from app.tina.io project settings>
TINA_TOKEN=<read-only token from app.tina.io>
NEXT_PUBLIC_TINA_BRANCH=main
```

| Var | Context | Purpose |
|---|---|---|
| `NEXT_PUBLIC_TINA_CLIENT_ID` | Site + Admin | Identifies the TinaCloud project |
| `TINA_TOKEN` | Site only | Read-only API token (server-side queries) |
| `NEXT_PUBLIC_TINA_BRANCH` | Site + Admin | Which branch the admin operates on |

The `NEXT_PUBLIC_*` prefix is a Next.js convention that makes the var available in client bundles. TinaCMS also picks up these specific names for the admin build.

## Required env vars (self-hosted)

```env
TINA_PUBLIC_IS_LOCAL=false      # set to true for local dev to skip auth
NEXTAUTH_SECRET=<32+ random chars>
GITHUB_OWNER=<your-org>
GITHUB_REPO=<your-repo>
GITHUB_BRANCH=main
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx

# DB-specific:
KV_REST_API_URL=https://xxx.kv.vercel-storage.com  # for Vercel KV
KV_REST_API_TOKEN=xxx                              # for Vercel KV
MONGODB_URI=mongodb+srv://...                      # for MongoDB

# Auth-specific (Clerk):
CLERK_SECRET=sk_test_xxx
TINA_PUBLIC_CLERK_PUBLIC_KEY=pk_test_xxx
TINA_PUBLIC_ALLOWED_EMAIL=editor@example.com
```

## `.env` only — `.env.local` is NOT read by Tina build

Tina's build process picks up variables from **`.env`** only. **`.env.local`, `.env.development`, `.env.production` are NOT loaded by the TinaCMS build.**

```
✅  .env           ← Tina reads this
❌  .env.local     ← Tina ignores this
❌  .env.development
❌  .env.production
```

This trips up developers who follow the standard Next.js convention of using `.env.local`. **For TinaCMS env vars, put them in `.env`**, or set them through a hosting provider's env config.

For Next.js-only env vars (not used by TinaCMS), `.env.local` continues to work.

## Local dev pattern

```bash
# .env (gitignored for TinaCloud local dev — Tina reads this)
NEXT_PUBLIC_TINA_CLIENT_ID=<from app.tina.io>
TINA_TOKEN=tcl_xxxxx_real_token
NEXT_PUBLIC_TINA_BRANCH=main

# .env.local (gitignored — Next.js-only values may go here)
# Do not put Tina vars only in .env.local; tinacms build ignores it

# But: if you only have local-only mode and no TinaCloud, leave them empty
# and run `pnpm dev` — the local GraphQL server reads/writes filesystem directly
```

For local dev that doesn't need TinaCloud at all:

```env
TINA_PUBLIC_IS_LOCAL=true
```

This tells TinaCMS to skip cloud auth entirely. Useful for offline development.

## Vercel configuration

In **Vercel → Project Settings → Environment Variables**:

1. Add each var with the appropriate **Environment** scope (Production, Preview, Development).
2. Use **Team Environment Variables** to share keys across multiple projects in the same Vercel team.
3. After changing env vars, redeploy — Vercel doesn't auto-rebuild.

## Admin-exposed vars (security note)

Only specific `NEXT_PUBLIC_*` and `TINA_PUBLIC_*` prefixed vars are embedded in the admin build. This is a security feature — if everything were embedded, your `TINA_TOKEN` (which has write access in some configs) could leak from the admin's bundle.

Rule of thumb:

- `NEXT_PUBLIC_*` — embedded in client bundles. Safe for IDs, public URLs.
- `TINA_PUBLIC_*` — TinaCMS-specific, embedded in admin bundle.
- Anything else — server-side only. Tokens, secrets, DB connection strings.

## Common env var bugs

| Symptom | Cause | Fix |
|---|---|---|
| Admin loads but shows "no project" | `NEXT_PUBLIC_TINA_CLIENT_ID` missing or wrong | Check value in `.env` (NOT `.env.local`); rebuild |
| Edits save to wrong branch | `NEXT_PUBLIC_TINA_BRANCH` mismatch | Set per-environment in Vercel |
| Build fails with "missing token" | `TINA_TOKEN` not in CI env | Add to GitHub Actions secrets |
| Local admin works, deployed admin doesn't | Vars in `.env.local` only | Move to `.env` or Vercel env config |
| Admin shows localhost:4001 in production | `tinacms dev` ran instead of `tinacms build` | Use `tinacms build` in CI |

## Validating env at build

Add a sanity check at the top of `tina/config.ts`:

```typescript
if (process.env.NODE_ENV === 'production') {
  if (!process.env.NEXT_PUBLIC_TINA_CLIENT_ID) {
    throw new Error('NEXT_PUBLIC_TINA_CLIENT_ID is required in production')
  }
  if (!process.env.TINA_TOKEN) {
    throw new Error('TINA_TOKEN is required in production')
  }
}
```

Better to fail the build than ship a broken admin.
