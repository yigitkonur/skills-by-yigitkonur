# Package Scripts

The required `package.json` scripts and the build-order rule that breaks half of TinaCMS deployments when ignored.

## Required scripts

```json
{
  "scripts": {
    "dev": "tinacms dev -c \"next dev\"",
    "build": "tinacms build && next build",
    "start": "tinacms build && next start"
  }
}
```

## Build order is non-negotiable

```
✅  tinacms build && next build
❌  next build && tinacms build
```

The `tinacms build` step generates `tina/__generated__/` (TypeScript types and the GraphQL client). The Next.js build needs those types to compile. Reverse the order and you get:

```
ERROR: Cannot find module '../tina/__generated__/client'
ERROR: Property 'queries' does not exist on type '{}'
```

Same rule applies to `start` (production preview) — generated types must exist before Next.js boots.

## Why `tinacms dev -c "next dev"` instead of just `next dev`

`tinacms dev` does three things:

1. Starts the local GraphQL server on port `4001`
2. Compiles `tina/config.ts` and watches it for changes
3. Runs the `-c` child command (`next dev`) alongside it

If you run `next dev` alone, the GraphQL server is missing — queries return errors and `useTina()` won't subscribe to live edits.

If you have a custom Next.js dev command (e.g. with custom port):

```json
{
  "scripts": {
    "dev": "tinacms dev -c \"next dev --port 4000\""
  }
}
```

## Using a non-default Tina port

```json
{
  "scripts": {
    "dev": "tinacms dev --port 4002 -c \"next dev\""
  }
}
```

The Tina GraphQL port is unrelated to the Next.js port. `--port` controls the Tina server (default `4001`). The local datalayer server runs on `--datalayer-port` (default `9000`).

## Self-hosted scripts

For self-hosted projects you also expose a `TINA_PUBLIC_IS_LOCAL` flag so local dev skips your auth provider:

```json
{
  "scripts": {
    "dev": "TINA_PUBLIC_IS_LOCAL=true tinacms dev -c \"next dev\"",
    "dev:prod": "tinacms dev -c \"next dev\"",
    "build": "tinacms build && next build",
    "start": "tinacms build && next start"
  }
}
```

`dev:prod` runs against your production auth provider — useful for testing OAuth flows before deploy.

## CI scripts

In CI (GitHub Actions, GitLab CI, etc.) run the steps explicitly:

```yaml
- run: pnpm install --frozen-lockfile
- run: pnpm tinacms build
- run: pnpm next build
  env:
    NEXT_PUBLIC_TINA_CLIENT_ID: ${{ secrets.TINA_CLIENT_ID }}
    TINA_TOKEN: ${{ secrets.TINA_TOKEN }}
```

Don't rely on `pnpm build` alone in CI — being explicit makes failures easier to diagnose.

## Vercel configuration

For Vercel deploys, leave the build command at the default (`pnpm build`) since `package.json` already has the right order. If you override it in **Project Settings → Build & Development Settings → Build Command**, set:

```
pnpm tinacms build && pnpm next build
```

## Common script mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| `"build": "next build"` (missing tinacms build) | `Cannot find module '../tina/__generated__/client'` | Add `tinacms build &&` prefix |
| `"build": "next build && tinacms build"` (wrong order) | Same error | Swap order |
| `"dev": "next dev"` (missing tinacms wrapper) | useTina doesn't subscribe; queries return errors | Use `tinacms dev -c "next dev"` |
| `"start": "next start"` (no tinacms build) | Production start works first time then breaks if `__generated__/` is gitignored on a fresh checkout | Use `tinacms build && next start` |
| Missing CI step | Deployed admin loads localhost:4001 | Add `tinacms build` before `next build` in CI |

## Optional helper scripts

```json
{
  "scripts": {
    "tina:audit": "tinacms audit",
    "tina:reindex": "tinacms admin reindex",
    "types": "tinacms build --noWatch"
  }
}
```

- `audit` — checks schema/content consistency
- `reindex` — for self-hosted, forces DB reindex from git
- `types` — regenerates `__generated__/` without watching

## Verifying scripts

```bash
pnpm dev       # should print "tinacms dev" + "next dev" output side by side
pnpm build     # should print "tinacms build" succeeded, then "next build" output
pnpm start     # should serve at localhost:3000 with admin loadable
```

If any of these fails, fix the scripts before any deploy.
