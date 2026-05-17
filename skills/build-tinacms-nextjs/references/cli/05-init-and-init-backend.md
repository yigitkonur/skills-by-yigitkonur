# `init` and `init backend`

Bootstrap commands for new projects and self-hosted backends.

## `init`

```bash
pnpm dlx @tinacms/cli@latest init
```

Bootstraps TinaCMS in the current directory.

### Prompts

| Prompt | Typical answer |
|---|---|
| Public assets directory | `public` |
| Sample blog collection? | Yes (delete after if not wanted) |
| Confirm install | Y |

### What it creates

- `tina/config.ts` — starter schema
- `app/admin/[[...index]]/page.tsx` — admin route (App Router)
- `pages/admin/[[...index]].tsx` — admin route (Pages Router)
- `content/posts/` (sample) — example content directory
- Updates `package.json` scripts

### What it doesn't do

- Sign you up for TinaCloud
- Deploy anything
- Configure auth

For TinaCloud, register at https://app.tina.io and add credentials manually.

## `init backend`

```bash
pnpm dlx @tinacms/cli@latest init backend
```

Adds self-hosted backend scaffolding to an existing TinaCMS project. Run AFTER `init` (or after manually setting up tina).

### What it creates

- `tina/database.ts` — DB + git provider config
- `app/api/tina/[...routes]/route.ts` — backend handler
- Adds dependencies: `@tinacms/datalayer`, `tinacms-authjs`, `upstash-redis-level`, `@upstash/redis`, `tinacms-gitprovider-github`, `next-auth`

### Prompts

| Prompt | Typical answer |
|---|---|
| Auth provider? | Auth.js (default) |
| Database adapter? | Vercel KV (default) |
| Git provider? | GitHub (default) |

After init, update `tina/config.ts` to add `contentApiUrlOverride` and `authProvider`.

## Verifying after init

```bash
ls tina/
# Should show: config.ts (or .tsx)
# After build: tina-lock.json, __generated__/

ls app/admin/
# Should show: [[...index]]/page.tsx (App Router)
# Or pages/admin/ for Pages Router

cat package.json | grep '"dev"\|"build"'
# Should show:
#   "dev": "tinacms dev -c \"next dev\"",
#   "build": "tinacms build && next build",
```

## Re-running init

Don't re-run `init` on an existing TinaCMS project — it overwrites `tina/config.ts` and admin routes. If you need to reset, delete and start over.

## Migrating from older TinaCMS versions

If you have an old TinaCMS project (pre-3.x):

1. Review the migration guide in TinaCMS' changelog
2. Update `package.json` to current versions
3. Run `pnpm install`
4. Run `pnpm tinacms build`
5. Fix any schema errors that surface

The CLI doesn't have a "migrate from old version" command.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Re-ran `init` on existing project | Overwrites schema | Don't re-run; manually edit `tina/config.ts` |
| Skipped `init backend` for self-hosted | Missing backend scaffolding | Run it (or copy from a starter) |
| Wrong public assets dir during init | Admin doesn't load | Re-init or fix `tina/config.ts` `build.publicFolder` |
| Used `npm` instead of `pnpm` for init | Module resolution issues | Reinstall with pnpm |
