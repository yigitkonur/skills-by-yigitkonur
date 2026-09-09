# Architecture: Cloud Browsers & Playwright Automation

How to instrument cloud browser automation engines (Kernel, Playwright, Puppeteer, CDP) with Sentry, strictly redacting JWT tokens in `cdpWsUrl`.

## The Cloud Browser Credentials Trap

When connecting to remote browser infrastructure (Kernel, Browserless, Steel):
```typescript
const browser = await chromium.connectOverCDP(cdpWsUrl);
```
- `cdpWsUrl` embeds a bearer authentication JWT: `wss://.../devtools/browser/...?jwt=eyJhbGci...`
- **If `cdpWsUrl` is logged or sent as a Sentry tag, you leak full billing and VM control credentials into your telemetry.**
- **RULE:** Never log `cdpWsUrl`. Log `sessionId` or `leaseId`, which are opaque and safe.

## 1. Redactor for Cloud Browser URLs

```typescript
export function sanitizeCdpUrl(url: string): string {
  // Strip ?jwt=... from WebSocket endpoints
  return url.replace(/([?&]jwt=)[^&#\s]+/gi, '$1[Filtered]');
}
```

## 2. Instrumenting Browser Automation Workflows

```typescript
import * as Sentry from '@sentry/node';

export async function runScrapingLane(sessionId: string, cdpWsUrl: string, targetUrl: string) {
  // 1. Record session breadcrumb with opaque ID
  Sentry.addBreadcrumb({
    category: 'cloud_browser.session',
    message: `Connected to cloud session ${sessionId}`,
    level: 'info',
    data: {
      sessionId,
      targetUrl,
      cdpHost: new URL(cdpWsUrl).host, // Safe host without JWT
    },
  });

  return Sentry.startSpan(
    {
      name: `browser.scrape.${new URL(targetUrl).hostname}`,
      op: 'browser.scrape',
      attributes: {
        'browser.sessionId': sessionId,
        'browser.targetUrl': targetUrl,
      },
    },
    async (span) => {
      try {
        const result = await executeScrape(cdpWsUrl, targetUrl);
        span.setStatus({ code: 1 });
        return result;
      } catch (error: any) {
        span.setStatus({ code: 2, message: error.message });

        Sentry.withScope((scope) => {
          scope.setTag('sessionId', sessionId);
          scope.setTag('targetHost', new URL(targetUrl).hostname);
          Sentry.captureException(error);
        });

        throw error;
      }
    }
  );
}
```

## 3. Capturing Interstitials & Anti-Bot Challenges

When Cloudflare, PerimeterX, or Datadome blocks a scraping run:
```typescript
if (isCaptchaPresent || response.status === 403) {
  Sentry.addBreadcrumb({
    category: 'bot_detection',
    message: `Challenge detected on ${targetUrl}`,
    level: 'warning',
    data: { challengeType: 'cloudflare_turnstile', status: response.status },
  });
}
```
