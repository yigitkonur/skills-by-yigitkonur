# Stack Traces & Sourcemap Build Pipeline

How to map minified production bundle errors back to original TypeScript/JavaScript source lines using Sentry CLI and release pipelines.

## The Minification Problem

Without sourcemaps, production error stack traces display:
```text
TypeError: Cannot read property 'map' of undefined
    at e.extract (https://cdn.example.com/app.min.js:1:14231)
    at t.process (https://cdn.example.com/app.min.js:1:982)
```
Engineers cannot identify the offending line or variable name.

With sourcemaps uploaded to Sentry:
```text
TypeError: Cannot read property 'map' of undefined
    at extractResults (src/core/extract.ts:42:18)
    at processPipeline (src/core/pipeline.ts:112:5)
```

## Step 1: Configure Build Tool to Emit Sourcemaps

### TypeScript (`tsconfig.json`)
```json
{
  "compilerOptions": {
    "sourceMap": true,
    "inlineSources": true
  }
}
```

### Vite / Rollup (`vite.config.ts`)
```typescript
export default defineConfig({
  build: {
    sourcemap: true, // or 'hidden' so maps are not published to public CDN
  },
});
```

## Step 2: Upload Sourcemaps via Sentry CLI

In your CI/CD pipeline (e.g. GitHub Actions):

```bash
# 1. Define release version (e.g. git commit sha or package version)
export SENTRY_RELEASE=$(git rev-parse --short HEAD)

# 2. Create release
sentry-cli releases new "$SENTRY_RELEASE"

# 3. Associate Git commits for repo line-linking
sentry-cli releases set-commits "$SENTRY_RELEASE" --auto

# 4. Upload sourcemaps from build directory
sentry-cli sourcemaps upload --release "$SENTRY_RELEASE" ./dist

# 5. Finalize release
sentry-cli releases finalize "$SENTRY_RELEASE"
```

## Step 3: Delete Sourcemaps from Public CDN (Optional)

If you do not want public users downloading `.map` files:
```bash
# Upload to Sentry first
sentry-cli sourcemaps upload --release "$SENTRY_RELEASE" ./dist

# Remove local .map files before uploading bundle to public S3 / Cloudflare Pages
rm ./dist/*.map
```

Sentry securely stores the sourcemaps and de-obfuscates stack traces automatically on ingest.
