# Function size limits

Vercel serverless functions have a hard limit: **50MB compressed** (unzipped per region). Exceed it → deploy fails with `Function exceeds 50MB`.

## Common offenders

| Dependency | Compressed | Why |
|---|---|---|
| Sharp (image processing) | ~30MB | Native binaries per platform |
| ffmpeg-static | ~50MB | Encodes to MP4/WebM |
| @sentry/profiling-node | ~5MB | Native profiler |
| canvas | ~30MB | Native renderer |
| puppeteer (full) | ~170MB | Bundles Chromium |
| playwright | ~250MB | Bundles browser drivers |

A vanilla Next.js function with Prisma + Clerk is ~10-20MB. Add one heavy native dep and you're over.

## Detecting

Vercel's deploy log shows the function size:

```
λ /api/upload  10.5 MB
λ /api/process 60.2 MB  ← FAIL
```

Or analyze locally:

```bash
# Build, then inspect
npm run build
du -sh .next/server/app/api/process/route.js .next/server/chunks/ | sort -h
```

`@vercel/analytics`'s "Function bundle size" check in CI also catches this.

## Fixes (ordered by preference)

### 1. Move the work to an external service

The cleanest fix. Image processing, video encoding, large-model inference — these don't belong in serverless functions.

- **Image processing:** Cloudinary, imgix, Vercel's built-in `next/image` (handles most cases)
- **Video:** Mux, Cloudflare Stream
- **Heavy compute:** offload to a Railway worker, AWS Lambda with bigger limits, or a dedicated service

### 2. Use Edge runtime instead

Edge functions have a different (smaller) bundle limit but no native code. If your function doesn't need native deps:

```ts
// app/api/process/route.ts
export const runtime = 'edge';
```

Edge functions are smaller, faster cold-start, but limited (no Node APIs, no Prisma standard adapter).

### 3. Externalize unused deps

`serverExternalPackages` in `next.config.ts` keeps server-only deps out of the function bundle (they're loaded at runtime via `require()`):

```ts
serverExternalPackages: ['@prisma/client', 'sharp', 'pino']
```

This is the same fix as in the make-local skill's optimization references — applies to Vercel too.

### 4. Tree-shake aggressively

Some packages bundle their entire surface even when you import one symbol. Audit with `@next/bundle-analyzer`:

```bash
ANALYZE=true npm run build
# opens a treemap of bundle contents
```

Look for large entries that don't match what you actually use → switch to subpath imports or smaller alternatives.

### 5. Split the function

If `/api/big-thing` does multiple things, split into multiple smaller functions:

```
/api/upload          (small — just receives the file)
/api/process-video   (different function, different bundle)
```

Each has its own 50MB budget.

## Edge runtime limits (different)

| Constraint | Edge | Serverless (Node) |
|---|---|---|
| Bundle size | 1-4 MB | 50 MB |
| Cold start | ~10ms | ~1s |
| Available APIs | Web standard (fetch, crypto.subtle) | Full Node.js |
| Native modules | ❌ | ✓ |
| DB drivers | HTTP/REST only (e.g., Neon serverless driver) | Full Postgres/MySQL drivers |

For high-volume read-heavy functions, Edge is great. For anything with Prisma + standard Postgres, use serverless.

## Vercel Pro / Enterprise

Pro doesn't lift the 50MB compressed limit — it's an architectural constraint of AWS Lambda (which Vercel uses under the hood).

Enterprise can negotiate custom limits but it's rare to need it.

## Alternative: deploy the heavy bit to Railway

If you need ffmpeg/sharp/puppeteer-class workloads, move them to Railway:

```ts
// On Vercel:
fetch('https://my-worker.railway.app/api/process', { method: 'POST', body: ... })
```

Vercel handles the request; Railway worker does the work. See `references/vercel-vs-railway.md`.

## Pre-deploy guard

Before `make deploy`, run a size check:

```bash
npm run build
SIZE_MB=$(du -sk .next/server | awk '{print int($1/1024)}')
if [ $SIZE_MB -gt 40 ]; then
  echo "WARN: build is ${SIZE_MB}MB, approaching 50MB function limit"
fi
```

40MB threshold = early warning; deploy proceeds. 50MB = hard fail at deploy time.
