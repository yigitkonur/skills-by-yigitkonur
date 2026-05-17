# `tinacms dev`

Local dev. Starts:

1. The TinaCMS GraphQL server (default port 4001)
2. The local datalayer (default port 9000)
3. The wrapped child command (e.g. `next dev`)

## Standard usage

```bash
tinacms dev -c "next dev"
```

Or in `package.json`:

```json
{
  "scripts": {
    "dev": "tinacms dev -c \"next dev\""
  }
}
```

## Why `-c` is required

Plain `tinacms dev` only starts Tina's servers. Your Next.js app needs to run alongside, so wrap with `-c`:

```bash
tinacms dev -c "next dev"
tinacms dev -c "next dev --port 4000"
tinacms dev -c "vite"
tinacms dev -c "astro dev"
```

The wrapped command runs with stdout/stderr passed through.

## Custom Tina port

```bash
tinacms dev --port 4002 -c "next dev"
```

Default is 4001. Useful if 4001 conflicts with another service.

## Custom datalayer port

```bash
tinacms dev --datalayer-port 9001 -c "next dev"
```

Default is 9000. Less commonly needed.

## Hostname binding (Docker)

If running in Docker, bind to all interfaces:

```bash
tinacms dev -c "next dev --hostname 0.0.0.0"
```

Or in `docker-compose.yml`:

```yaml
services:
  app:
    command: pnpm dev  # which runs `tinacms dev -c "next dev --hostname 0.0.0.0"`
```

## Watching for changes

By default, `tinacms dev` watches `tina/config.ts` and content files for changes:

- Schema changes → regenerate `tina/__generated__/`
- Content file changes → reindex in DB
- Restart Tina server if config changes are major

To disable:

```bash
tinacms dev --noWatch -c "next dev"
```

## Verbose output

```bash
tinacms dev -v -c "next dev"
```

Useful for debugging — shows GraphQL queries, indexer activity, etc.

## What runs locally

Local mode (when `clientId` is empty or `TINA_PUBLIC_IS_LOCAL=true`):

- Local GraphQL server reads/writes content files directly
- No TinaCloud connection
- No auth
- Live reload as you edit content

For testing TinaCloud features (Editorial Workflow, fuzzy search), you can't use local mode — deploy to a Vercel preview instead.

## Env behavior

`tinacms dev` picks up env vars from `.env` (NOT `.env.local`). For local-only mode:

```env
# .env
TINA_PUBLIC_IS_LOCAL=true
```

## Verifying

After `pnpm dev`:

```bash
# Tina GraphQL up?
curl http://localhost:4001/health
# Should return 200

# Datalayer up?
curl http://localhost:9000/health
# Should return 200

# Next.js app up?
curl http://localhost:3000
# Your home page

# Admin loadable?
open http://localhost:3000/admin/index.html
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Plain `next dev` (no `tinacms dev`) | Tina server missing, useTina doesn't subscribe | Use `tinacms dev -c "next dev"` |
| Port 4001 in use | Tina fails to start | Use `--port` to override |
| Docker without `--hostname 0.0.0.0` | Admin not reachable | Add hostname flag |
| Forgot to install `@tinacms/cli` | Command not found | `pnpm add -D @tinacms/cli` |
| Watching disabled in dev | Schema changes don't apply | Don't use `--noWatch` in dev |
