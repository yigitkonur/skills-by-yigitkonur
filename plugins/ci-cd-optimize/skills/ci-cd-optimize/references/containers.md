# Containers

Use this file for Docker/OCI build acceleration and image correctness.

## Dockerfile ordering

Order from least frequently changed to most frequently changed:

1. base image digest,
2. OS dependencies,
3. package manifests/lockfiles,
4. dependency install,
5. source,
6. compile/build,
7. runtime-only artifacts.

Use multi-stage builds so dev dependencies and compilers do not reach the runtime image.

## TypeScript Dockerfile shape

```dockerfile
# syntax=docker/dockerfile:1.7
ARG NODE_IMAGE=node:24-alpine@sha256:REPLACE_WITH_CURRENT_DIGEST

FROM ${NODE_IMAGE} AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    corepack pnpm install --frozen-lockfile

FROM --platform=$BUILDPLATFORM ${NODE_IMAGE} AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY package.json pnpm-lock.yaml tsconfig.json ./
COPY src ./src
RUN corepack pnpm run build && corepack pnpm prune --prod

FROM ${NODE_IMAGE} AS runtime
ENV NODE_ENV=production
WORKDIR /app
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./
USER node
CMD ["node", "dist/index.js"]
```

Use a `.dockerignore` for `.git`, `node_modules`, `dist`, `.env*`, logs, and local artifacts.

## Cache backends

Ephemeral CI runners need external layer cache:

```yaml
cache-from: type=registry,ref=ghcr.io/org/app:buildcache
cache-to: type=registry,ref=ghcr.io/org/app:buildcache,mode=max
```

- `mode=max`: includes intermediate stages; better hits, larger transfer.
- `mode=min`: smaller cache; usually only final image layers.
- Cache mounts (`RUN --mount=type=cache`) persist per builder, not automatically across ephemeral builders.
- Concurrent stages sharing a writable cache mount need distinct `id=`
  values or `sharing=locked`; parallel mutation corrupts the store.

### Measure the export, not just the hit rate

`mode=max` writes every intermediate layer on **every** build; the cost
hides in step timings, not the hit rate. Measured: a 166 s image job spent
49 s in `preparing build cache for export` plus 52 s writing layers — 101 s
of export against ~65 s of building. Read the BuildKit step lines
(`exporting cache`, `preparing build cache for export`, `writing layer`)
and compute `net benefit = uncached build − import − export − transfer`.

Choose the write policy by job purpose: a deploy-artifact job earns
`mode=max`; a validate-only job earns `mode=min` or exporting only from the
default branch; matrix cells restore while one canonical job writes.
Read-on-branch / write-on-default removes export from the common path
without losing hits.

### Layer-cost traps

- `RUN chown -R` over the app tree rewrites every inode into a new layer
  and can dominate the build (52 s in the measured case above). Use
  `COPY --chown=user:group` so ownership is set as the layer is written;
  chown only paths created afterwards.
- Any `RUN` touching many files (`chmod -R`, `find -exec`, recursive `cp`)
  creates a large layer that must be written, exported, and pulled. Do the
  work at `COPY` time or in the stage that owns the files.

## Multi-platform

Avoid QEMU for compile-heavy stages. TypeScript emits platform-neutral JavaScript, so compile on `$BUILDPLATFORM` and run only final packaging on target platforms. Native modules must be built for the target platform.

## Provenance and security

- Pin BuildKit/buildx and base images by digest.
- Provenance `mode=max` can expose build internals; use minimal provenance for closed-source images.
- Generate SBOM/provenance for release images and verify them before deployment.
- Never pass secrets through `ARG`, `ENV`, or `COPY`; use BuildKit secret mounts.
- Deleting a secret in a later layer does not remove it from earlier layers.
- Scope shared cache writes per trust boundary or branch.

## Sources

- Build cache backends: https://docs.docker.com/build/cache/backends/ (accessed 2026-07-28)
- Cache optimization: https://docs.docker.com/build/cache/optimize/ (accessed 2026-07-28)
- Multi-platform: https://docs.docker.com/build/building/multi-platform/ (accessed 2026-07-28)
- Multi-stage: https://docs.docker.com/build/building/multi-stage/ (accessed 2026-07-28)
- Provenance: https://docs.docker.com/build/metadata/attestations/slsa-provenance/ (accessed 2026-07-28)
- Docker security announcements: https://docs.docker.com/security/security-announcements/ (accessed 2026-07-28)
