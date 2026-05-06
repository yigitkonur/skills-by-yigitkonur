# Vercel + Self-hosted

Deploy a self-hosted TinaCMS backend on Vercel Functions.

## Architecture

```
GitHub repo (content + code)
   ↓ push
Vercel (Next.js app + your /api/tina/[...routes] backend)
   ↕ ↑↓
   │  └──→ Auth.js / Clerk (auth)
   ↓
Vercel KV / MongoDB (DB index)
   ↑↓
GitHub API (PAT) — commits content
```

## Setup

1. Set up self-hosted code (see `references/self-hosted/`)
2. Push to GitHub
3. Vercel: New Project
4. Enable Vercel KV (or MongoDB if using):
   - Project Settings → Storage → Create KV
5. Add env vars:
   ```env
   TINA_PUBLIC_IS_LOCAL=false
   NEXTAUTH_SECRET=<32 random chars>
   GITHUB_OWNER=<owner>
   GITHUB_REPO=<repo>
   GITHUB_BRANCH=main
   GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx
   # KV creds auto-injected when you create Vercel KV
   ```
6. Deploy

## Build command

Same as TinaCloud version:

```json
{
  "scripts": {
    "build": "tinacms build && next build"
  }
}
```

## Vercel Function config for the backend route

```typescript
// app/api/tina/[...routes]/route.ts
export const maxDuration = 60   // up to 60s on Pro, default 10s on Hobby

const handler = TinaNodeBackend({/* ... */})
export { handler as GET, handler as POST }
```

For initial DB indexing (~5 min for 1k docs), 10s timeout might be tight. Increase via Pro plan or use a Background Function.

## Edge runtime — DO NOT use

```typescript
// ❌ DO NOT
export const runtime = 'edge'
```

The backend depends on Node.js APIs.

## Region

```typescript
export const preferredRegion = 'iad1'  // match your DB region
```

For Vercel KV: KV regions are auto-selected; pick your function region near it.

## Webhook for content changes

Without TinaCloud, you need to handle webhooks yourself. Add a route:

```typescript
// app/api/revalidate/route.ts
import { revalidatePath } from 'next/cache'
import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  // 1. Auth check FIRST — never process the body of an unauthenticated request.
  //    Shared bearer token (rotate periodically):
  const auth = req.headers.get('authorization')
  if (auth !== `Bearer ${process.env.WEBHOOK_SECRET}`) {
    return new Response('Unauthorized', { status: 401 })
  }
  // For GitHub-style HMAC, verify x-hub-signature-256 with crypto.timingSafeEqual.

  const body = await req.json()
  for (const path of body.paths ?? []) {
    revalidatePath(`/${path.replace('content/', '').replace(/\.(md|mdx)$/, '')}`)
  }
  return NextResponse.json({ ok: true })
}
```

For self-hosted, no webhook fires automatically on saves — your backend handles them in-process. For external git pushes, add a GitHub webhook to call your `/api/revalidate` endpoint.

## Initial admin user

After first deploy, you need at least one user in `content/users/<email>.json`:

```bash
node -e "
const bcrypt = require('bcryptjs');
const fs = require('fs');
const hash = bcrypt.hashSync('your-password', 10);
fs.writeFileSync('content/users/admin.json', JSON.stringify({
  username: 'Admin',
  email: 'admin@example.com',
  password: hash,
}, null, 2));
"
git add content/users/admin.json && git commit -m 'Add admin user' && git push
```

Then deploy. After deploy, log in with email + password.

## Audit log via git

Each editor's commits are authored by them (if you wire up `author` in the GitHub provider). For aggregate audit:

```bash
git log --pretty=format:'%an %h %s' content/
```

## Migration / rollback

If self-hosted has issues, fall back to TinaCloud:

1. Re-create TinaCloud project (or restore old one)
2. Add `clientId` and `token` env vars
3. Remove `contentApiUrlOverride` from `tina/config.ts`
4. Delete the backend route
5. Redeploy

Content stays in git. Migration is just config + auth swap.

## Cost ballpark

| Component | Cost |
|---|---|
| Vercel Hobby (or Pro $20/mo) | $0–$20 |
| Vercel KV (free tier) | $0 |
| Atlas M0 (alt to KV, free) | $0 |
| GitHub | Free for public repos |
| Auth.js | Free |

Total: $0–$20/month for typical projects. Cheaper than TinaCloud Team Plus.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot env vars | Backend fails | Add all in Vercel settings |
| Edge runtime on backend route | Build fails | Use Node runtime |
| Forgot to enable Vercel KV | DB connection fails | Enable in Project Settings → Storage |
| Initial admin user not in git | Can't log in | Add user file before first deploy |
| Cross-region function + DB | Slow (200ms+ added latency) | Match regions |
