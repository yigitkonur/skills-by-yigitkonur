# Redacting Sensitive URL Parameters & Bearer JWTs

How to sanitize URLs containing bearer tokens, API keys, and JWT session strings before they reach breadcrumbs, transaction names, or spans.

## The Threat

Cloud providers, CDPs, and webhook handlers embed credentials directly into URL query parameters:
- `wss://browser.host/session?jwt=eyJ...`
- `https://s3.amazonaws.com/bucket/key?AWSAccessKeyId=...&Signature=...`
- `https://api.example.com/v1/data?api_key=secret`

When Sentry records HTTP client requests, navigation events, or span descriptions, these parameters are captured unless explicitly stripped.

## URL Sanitizer Implementation

```typescript
const SENSITIVE_PARAM_NAMES = new Set([
  'token',
  'jwt',
  'api_key',
  'apikey',
  'key',
  'secret',
  'auth',
  'signature',
  'signature_id',
  'access_token',
  'refresh_token',
  'password',
  'pwd',
]);

export function sanitizeUrl(rawUrl: string): string {
  try {
    const parsed = new URL(rawUrl);
    let changed = false;

    for (const [param] of parsed.searchParams.entries()) {
      if (SENSITIVE_PARAM_NAMES.has(param.toLowerCase())) {
        parsed.searchParams.set(param, '[Filtered]');
        changed = true;
      }
    }

    if (parsed.password) {
      parsed.password = '[Filtered]';
      changed = true;
    }

    return changed ? parsed.toString() : rawUrl;
  } catch {
    return rawUrl.replace(/([?&](?:jwt|token|key|secret)=)[^&#\s]+/gi, '$1[Filtered]');
  }
}
```

## Integration with HTTP Breadcrumbs

```typescript
export function recordHttpBreadcrumb(method: string, url: string, statusCode?: number) {
  const cleanUrl = sanitizeUrl(url);

  Sentry.addBreadcrumb({
    category: 'http',
    type: 'http',
    data: {
      method,
      url: cleanUrl,
      status_code: statusCode,
    },
    level: statusCode && statusCode >= 400 ? 'warning' : 'info',
  });
}
```
