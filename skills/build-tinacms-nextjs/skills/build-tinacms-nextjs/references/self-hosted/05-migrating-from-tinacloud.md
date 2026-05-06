# Migrating from TinaCloud to Self-hosted

Move an existing TinaCloud project to self-hosted. Content stays the same — only the backend changes.

## Why migrate

- Outgrew paid tiers
- Need custom auth not supported by TinaCloud
- Compliance requires on-prem
- Want to avoid SaaS dependency

## What stays the same

- `tina/config.ts` schema (mostly)
- All content files in git
- `tina-lock.json`
- Editor workflows (with caveats — see below)
- Visual editing patterns

## What changes

- `tina/config.ts` adds `contentApiUrlOverride` + `authProvider`
- Add `tina/database.ts`
- Add `app/api/tina/[...routes]/route.ts`
- Replace TinaCloud env vars with self-hosted env vars
- Set up DB (Vercel KV or MongoDB)
- Set up auth (Auth.js, Clerk, or custom)

## Migration steps

### 1. Inventory current setup

What you have:

- TinaCloud project URL
- `NEXT_PUBLIC_TINA_CLIENT_ID` and `TINA_TOKEN` env vars
- Editorial Workflow enabled? (Note: not available in self-hosted — you'll lose this)

### 2. Pick self-hosted modules

| Concern | Pick |
|---|---|
| Auth | Auth.js (default), Clerk, or custom |
| DB | Vercel KV (default) or MongoDB |
| Git | GitHub (default) |

For most migrations, default to Auth.js + Vercel KV + GitHub.

### 3. Set up the new infrastructure

- Vercel KV: enable in Vercel project settings
- Auth.js: install `next-auth` + `tinacms-authjs`, set up `app/api/auth/[...nextauth]/route.ts`
- GitHub PAT: generate (full `repo` scope)

### 4. Add the backend code

Follow `references/self-hosted/03-existing-site-add.md`:

- `tina/database.ts`
- `app/api/tina/[...routes]/route.ts`
- Update `tina/config.ts`

### 5. Add user collection

Self-hosted Auth.js uses a user collection in your CMS:

```typescript
{
  name: 'user',
  path: 'content/users',
  format: 'json',
  fields: [
    { name: 'username', type: 'string', isTitle: true },
    { name: 'email', type: 'string' },
    { name: 'password', type: 'string', ui: { component: 'hidden' } },
  ],
}
```

Migrate your TinaCloud user list:

- Get list from TinaCloud Project → Users
- For each, create a `content/users/<email>.json` file with hashed password
- Editors will need to set new passwords (TinaCloud passwords don't transfer)

### 6. Update env vars

Remove TinaCloud-specific:

```env
# REMOVE (or set to empty)
NEXT_PUBLIC_TINA_CLIENT_ID=
TINA_TOKEN=
```

Add self-hosted:

```env
TINA_PUBLIC_IS_LOCAL=false
NEXTAUTH_SECRET=<32 random chars>
GITHUB_OWNER=<owner>
GITHUB_REPO=<repo>
GITHUB_BRANCH=main
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx
KV_REST_API_URL=https://xxx.kv.vercel-storage.com
KV_REST_API_TOKEN=xxx
```

### 7. Deploy

Deploy to Vercel. Initial deploy:

- Backend route boots up
- DB indexes content from git
- Editors hit `/admin`, log in via Auth.js

### 8. Decommission TinaCloud

Once self-hosted is stable:

- Project Settings → Delete Project on TinaCloud (or downgrade to free)
- Remove TinaCloud webhooks from your repo

## What you lose

| Feature | TinaCloud | Self-hosted |
|---|---|---|
| Editorial Workflow | ✓ | ✗ — DIY via PR-based workflow |
| Built-in fuzzy search | ✓ | ✗ — use Algolia/Meilisearch |
| Git co-authoring (per-editor identity) | ✓ | Via Auth.js if user data is correct |
| Audit log UI | ✓ (Business+) | DIY via git log |
| Content API versioning | Auto | Manual via package versions |

If Editorial Workflow is critical, **stay on TinaCloud Team Plus**.

## What you gain

- No SaaS dependency
- Custom auth (Clerk, your own JWT)
- Cheaper at scale (Vercel KV is free up to 100MB; Mongo Atlas free tier)
- Full control over backend

## Rollback

If self-hosted has issues:

1. Re-enable TinaCloud project
2. Restore original env vars
3. Remove `contentApiUrlOverride`
4. Redeploy

Content files in git are unaffected — rollback is just env-var swap.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot to migrate users | Editors can't log in | Create user docs first |
| Kept old `clientId`/`token` | Conflicts with self-hosted auth | Set to empty |
| Skipped DB setup | Backend route 500s | Enable Vercel KV or MongoDB |
| Lost Editorial Workflow without realizing | Multi-editor team breaks | Stay on TinaCloud or build PR-based workflow |
| Didn't test locally first | Production breaks | Test with `TINA_PUBLIC_IS_LOCAL=true` first |
