# Spotlight: Zero-Overhead Local Developer Overlay

Spotlight is Sentry's local-first developer tool. It brings Sentry's full trace waterfall, exception capture, and log exploration directly into your local development environment without sending a single byte of telemetry to Sentry SaaS servers.

## 1. Starting the Spotlight Sidecar

Run the Spotlight desktop sidecar daemon in a separate terminal:

```bash
npx @spotlightjs/spotlight
```

This starts a local streaming collector listening on `http://localhost:8969` and opens the local dashboard in your browser.

## 2. Enabling Spotlight in Your Application

### Next.js / TypeScript / Browser
In `sentry.client.config.ts` or `sentry.server.config.ts`:

```typescript
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  // CRITICAL: Enable only during local development; never in production
  spotlight: process.env.NODE_ENV === 'development',
  tracesSampleRate: 1.0,
});
```

### Python / FastAPI / Django
In Python `sentry_sdk.init()`:

```python
import os
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    # Forward traces locally to http://localhost:8969
    spotlight=os.getenv("ENVIRONMENT") == "development",
    traces_sample_rate=1.0,
)
```

## 3. Spotlight Interactive Browser Overlay

In frontend applications, Spotlight injects a subtle bottom-right corner indicator.
- Clicking the badge slides out an interactive drawer showing the exact spans, queries, and errors triggered by your current page interaction.
- Click any span to see duration, SQL queries, HTTP requests, and contextual breadcrumbs in real time.

## 4. Key Developer Benefits

1. **Zero Quota Consumption:** Spans and errors stream directly to localhost. No quota or event limits are used.
2. **Instant Latency Profiling:** Catch N+1 database queries, slow API calls, and layout shifts during local development before pushing code.
3. **Works Fully Offline:** Operates on airplanes, trains, or networks without internet access.
