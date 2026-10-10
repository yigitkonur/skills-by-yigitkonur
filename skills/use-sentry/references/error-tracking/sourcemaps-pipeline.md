# Stack Traces & Sourcemap Build Pipeline

How to map minified production bundle errors back to original TypeScript/JavaScript source lines using modern **Debug IDs** and Sentry bundler plugins.

## The Modern Solution: Debug IDs

Historically, Sentry relied strictly on matching release names (`release` + `dist`) between source code and uploaded sourcemaps.
Modern Sentry uses **Debug IDs**:
1. During build time, Sentry injects a unique deterministic UUID snippet into each compiled `.js` file and its corresponding `.map` file.
2. When an error occurs in production, the runtime stack trace includes the embedded Debug ID.
3. Sentry matches the error to the exact uploaded sourcemap instantly, regardless of release tagging mismatches or multi-bundle architectures.

---

## Approach A: Official Bundler Plugins (Recommended)

The simplest and most reliable way to inject Debug IDs and upload sourcemaps is using Sentry's bundler plugins during your build.

### 1. Vite (`vite.config.ts`)

```bash
npm install --save-dev @sentry/vite-plugin
```

```typescript
import { defineConfig } from 'vite';
import { sentryVitePlugin } from '@sentry/vite-plugin';

export default defineConfig({
  build: {
    sourcemap: true, // or 'hidden' so source maps are not publicly exposed
  },
  plugins: [
    sentryVitePlugin({
      org: process.env.SENTRY_ORG,
      project: process.env.SENTRY_PROJECT,
      authToken: process.env.SENTRY_AUTH_TOKEN,
      telemetry: false,
    }),
  ],
});
```

### 2. Webpack (`webpack.config.js`)

```bash
npm install --save-dev @sentry/webpack-plugin
```

```javascript
const { sentryWebpackPlugin } = require('@sentry/webpack-plugin');

module.exports = {
  devtool: 'source-map',
  plugins: [
    sentryWebpackPlugin({
      org: process.env.SENTRY_ORG,
      project: process.env.SENTRY_PROJECT,
      authToken: process.env.SENTRY_AUTH_TOKEN,
    }),
  ],
};
```

---

## Approach B: Sentry CLI with Debug IDs (`inject` + `upload`)

If using custom build scripts, esbuild, or CI/CD pipelines without bundler plugins:

```bash
# 1. Build your application with sourcemaps enabled
npm run build

# 2. Inject Debug IDs into generated minified JS and sourcemaps
sentry-cli sourcemaps inject ./dist

# 3. Upload sourcemaps to Sentry
sentry-cli sourcemaps upload ./dist

# 4. Optional: Delete local .map files before deploying to public CDN
rm ./dist/*.map
```

---

## Approach C: Classic Release-Based Pipeline (Legacy Fallback)

If using older SDK versions (< 7.45.0) that do not support Debug IDs:

```bash
export SENTRY_RELEASE=$(git rev-parse --short HEAD)

sentry-cli releases new "$SENTRY_RELEASE"
sentry-cli releases set-commits "$SENTRY_RELEASE" --auto
sentry-cli sourcemaps upload --release "$SENTRY_RELEASE" ./dist
sentry-cli releases finalize "$SENTRY_RELEASE"
```
