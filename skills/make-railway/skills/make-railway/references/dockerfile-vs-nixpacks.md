# Dockerfile vs Nixpacks

Railway can build via:

1. **Dockerfile** — explicit, reproducible, you control everything
2. **Nixpacks** — auto-detection from package.json, framework hints, no Dockerfile needed

Pick by the project's complexity.

## Decision

| Project shape | Use |
|---|---|
| Vanilla Next.js, no Prisma/migrations, no native deps | Nixpacks |
| Next.js + Prisma + multi-step boot (migrations, seed, baseline) | Dockerfile |
| BullMQ worker + web split from same image | Dockerfile |
| Custom Node version, custom env, custom packages at OS level | Dockerfile |
| Bun, Deno, non-Node runtime | Dockerfile (Nixpacks supports limited set) |
| You want to test the same build locally (`docker build .`) | Dockerfile |

## When Nixpacks is fine

```bash
# Just deploy — Railway auto-detects Next.js
railway up --service web --detach
```

Railway will:
1. Detect framework from `package.json`
2. Run `npm ci` + `npm run build`
3. Start with `npm start`

No config needed. But:

- You can't add a custom boot script (e.g., `prisma migrate deploy` before `npm start`)
- You can't add native packages
- You can't share the same build with a worker service

## When you NEED a Dockerfile

Anything more than vanilla. Canonical Next.js + Prisma:

```Dockerfile
FROM node:24-alpine
WORKDIR /app

# Install deps (cached layer)
COPY package.json package-lock.json ./
RUN npm ci --omit=optional

# Copy source
COPY . .

# Generate Prisma client (output: src/generated/prisma)
RUN npx prisma generate

# Build Next.js
RUN npm run build

# Migrations + start
CMD ["sh", "-c", "./scripts/start.sh && npm start"]
```

`scripts/start.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Apply migrations (idempotent)
echo "→ applying Prisma migrations"
npx prisma migrate deploy

# Optional: baseline a legacy db push-provisioned DB
# npx prisma migrate resolve --applied <migration-name>

echo "→ migrations complete; handing off to npm start"
```

## CRITICAL: never `output: "standalone"` with `npm start`

Next.js standalone mode produces a minimal server in `.next/standalone/server.js`. It's incompatible with `next start` and silently breaks server actions, returning "Failed to find Server Action" on client invocations.

```ts
// next.config.ts
const nextConfig: NextConfig = {
  // output: "standalone",  ← DON'T (breaks server actions when using `npm start`)
  // ...
};
```

If you need standalone (e.g., to ship a smaller image), invoke it directly:

```Dockerfile
CMD ["node", ".next/standalone/server.js"]
```

But for the typical Next.js + Railway deploy, `output: "standalone"` is the wrong choice.

## Sharing one Dockerfile across services

Railway services from the same source repo all build the same Dockerfile. Differentiate at runtime via env or custom start command:

| Service | Custom Start Command (Railway UI) |
|---|---|
| `web` | (default — uses `CMD` from Dockerfile) |
| `worker` | `sh -c "./scripts/start.sh && ZEO_ROLE=worker npm run worker"` |

The Dockerfile builds once per service deploy; `CMD` runs per process start.

## Nixpacks gotchas

- Nixpacks uses `nixpacks.toml` (optional) for overrides. Quickly outgrows Dockerfile usefulness — at that point, switch.
- Build cache is opaque; you can't `docker history <image>` to inspect.
- Prisma `generate` runs (Nixpacks detects), but `migrate` doesn't — you'd need a `nixpacks.toml` `[start]` hook to run it before `npm start`. At that point, just write a Dockerfile.

## Local parity

The killer feature of Dockerfile: identical build locally + on Railway.

```bash
docker build -t myapp .
docker run --env-file .env.local -p 3000:3000 myapp
```

Whatever works in this `docker run` will work on Railway. Whatever breaks here breaks there too. This shortens the deploy-fail-debug cycle dramatically.
