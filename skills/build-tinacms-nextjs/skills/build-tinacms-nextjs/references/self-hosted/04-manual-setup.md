# Manual Setup (from scratch)

The hands-on approach. Build self-hosted from a fresh Next.js project — useful for understanding each piece.

## Steps

1. Create Next.js project (`pnpm dlx create-next-app@latest`)
2. Install TinaCMS (`pnpm dlx @tinacms/cli@latest init`)
3. Install self-hosted dependencies (see below)
4. Add `tina/database.ts`
5. Add `app/api/tina/[...routes]/route.ts`
6. Update `tina/config.ts` with `contentApiUrlOverride` + `authProvider`
7. Set env vars
8. Test locally with `TINA_PUBLIC_IS_LOCAL=true`
9. Deploy

For the file contents, see `references/self-hosted/03-existing-site-add.md` — the steps are nearly identical.

## Dependencies

```bash
pnpm add \
  @tinacms/datalayer \
  tinacms-gitprovider-github \
  upstash-redis-level \
  @upstash/redis \
  tinacms-authjs \
  next-auth \
  bcryptjs

pnpm add -D @types/bcryptjs
```

## Why each package

| Package | Purpose |
|---|---|
| `@tinacms/datalayer` | The Tina backend toolkit (`TinaNodeBackend`, `createDatabase`) |
| `tinacms-gitprovider-github` | GitHub git provider |
| `upstash-redis-level` | LevelDB-compatible adapter for Upstash Redis (Vercel KV) |
| `@upstash/redis` | Upstash client |
| `tinacms-authjs` | Auth.js integration with TinaCMS |
| `next-auth` | The Auth.js library itself |
| `bcryptjs` | Password hashing for the user collection |

## Verify each piece works in isolation

After setup:

```bash
# 1. Schema builds:
pnpm tinacms build

# 2. Database connects (in Vercel KV-backed projects):
node -e "import('@upstash/redis').then(({ Redis }) => Redis.fromEnv().get('test'))"

# 3. GitHub PAT works:
curl -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" https://api.github.com/repos/$GITHUB_OWNER/$GITHUB_REPO

# 4. Backend route returns:
curl -X POST http://localhost:3000/api/tina/gql -d '{"query":"{ __typename }"}'
```

If any fails, fix that piece before integrating.

## Why prefer the starter over manual

The starter (`references/self-hosted/02-nextjs-vercel-starter.md`) wires everything correctly out of the box. Manual setup is for:

- Learning how each piece connects
- Adding TinaCMS to a long-existing project
- Customizing in ways the starter doesn't allow

For most projects, the starter saves hours.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot to install one of the packages | Module not found at runtime | Re-check installs |
| Used npm/yarn instead of pnpm | Module resolution issues | Use pnpm |
| Missed `bcryptjs` | Password hashing fails | Install |
| Used Auth.js without `tinacms-authjs` integration | Auth doesn't tie into Tina's user collection | Use `tinacms-authjs` |
