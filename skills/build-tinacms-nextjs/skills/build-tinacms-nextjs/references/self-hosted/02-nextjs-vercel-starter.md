# Next.js + Vercel Starter

The official self-hosted starter. Uses Vercel KV (Upstash Redis) + GitHub + Auth.js. Easiest path to a working self-hosted setup.

## Repo

https://github.com/tinacms/tina-self-hosted-demo (or via `create-tina-app`)

## Quick start

```bash
pnpm dlx create-tina-app@latest my-site --template tina-self-hosted-demo
cd my-site
```

This scaffolds:

- Full Next.js App Router setup
- `tina/config.ts` with sample collections
- `tina/database.ts` with Vercel KV + GitHub provider
- `app/api/tina/[...routes]/route.ts` with Auth.js
- Sample admin user collection

## Setup checklist

After scaffold:

1. **Vercel KV**
   - Vercel Project Settings → Storage → Create KV Database
   - Vercel auto-injects `KV_REST_API_URL` and `KV_REST_API_TOKEN`

2. **GitHub Personal Access Token**
   - GitHub Settings → Developer settings → Personal access tokens → Generate (classic or fine-grained)
   - Scopes: `repo` (full repo access)
   - Add to Vercel as `GITHUB_PERSONAL_ACCESS_TOKEN`

3. **NEXTAUTH_SECRET**
   - Generate: `openssl rand -base64 32`
   - Add to Vercel

4. **Other env vars**
   ```env
   GITHUB_OWNER=<your-username>
   GITHUB_REPO=<your-repo>
   GITHUB_BRANCH=main
   TINA_PUBLIC_IS_LOCAL=false       # for production
   ```

5. **Deploy**
   - Vercel auto-deploys on push

## Local dev

```env
# .env
TINA_PUBLIC_IS_LOCAL=true
```

In local dev, the `LocalAuthProvider` skips auth and `createLocalDatabase()` uses in-memory state. Run:

```bash
pnpm dev
```

Open `http://localhost:3000/admin/index.html` — should work without any GitHub or KV setup.

## Initial admin user

The starter includes a sample user collection. To add yourself:

1. Open `tina/config.ts` — there's a `user` collection defined
2. After deploy, edit through the admin: create a user document with your email + a hashed password
3. Or run a setup script (the starter includes one): `pnpm tina:setup`

Auth.js validates against this user collection.

## Project structure

```
my-site/
├── app/
│   ├── admin/[[...index]]/page.tsx          # admin route
│   ├── api/
│   │   ├── tina/[...routes]/route.ts        # backend handler
│   │   └── auth/[...nextauth]/route.ts      # Auth.js routes
│   ├── layout.tsx
│   └── page.tsx
├── tina/
│   ├── config.ts                            # schema + auth provider
│   ├── database.ts                          # DB + git provider
│   └── tina-lock.json                       # commit this
├── content/                                  # CMS content
└── package.json
```

## What's wired by default

| Concern | Implementation |
|---|---|
| Auth | Auth.js with email/password (user collection in TinaCMS) |
| DB | Vercel KV (Upstash Redis) |
| Git | GitHub via Personal Access Token |
| Admin route | `/admin` |
| Local dev | `TINA_PUBLIC_IS_LOCAL=true` to skip auth |

## Customizing

After scaffold, swap any module:

- Different DB → see `references/self-hosted/database-adapter/`
- Different auth → see `references/self-hosted/auth-provider/`
- Different git → see `references/self-hosted/git-provider/`

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot to enable Vercel KV | DB connection fails | Vercel Project Settings → Storage → Create KV |
| Used `--no-optional` for install | Module resolution breaks | Reinstall without flag |
| GitHub PAT scope too narrow | Save fails with auth error | Use full `repo` scope |
| Missing `NEXTAUTH_SECRET` | Auth.js setup fails | Generate and add |
| Initial admin user not created | Can't log in | Run setup script or create via admin form |
