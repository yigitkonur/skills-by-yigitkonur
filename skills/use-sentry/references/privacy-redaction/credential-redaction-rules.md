# Defense-in-Depth Credential & PII Redaction

How to scrub authorization headers, Bearer JWTs, API keys, cookies, and PII from Sentry error events, breadcrumbs, tags, and stack frames.

## The Unified Redactor Implementation (`src/core/obs/redact.ts`)

```typescript
const SENSITIVE_KEY_PATTERNS = [
  /api[-_]?key/i,
  /auth(?:orization)?/i,
  /bearer/i,
  /cookie/i,
  /jwt/i,
  /password/i,
  /secret/i,
  /token/i,
  /session/i,
  /private[-_]?key/i,
];

const CREDENTIAL_VALUE_REGEXES = [
  /\beyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b/g, // JWT
  /\b(sntry[us]_[a-f0-9]{64})\b/g,                                        // Sentry tokens
  /\bBearer\s+[a-zA-Z0-9._~+/-]+=*/gi,                                    // Bearer tokens
  /\bBasic\s+[a-zA-Z0-9+/=]+/gi,                                          // Basic auth
  /:\/\/[^:]+:([^@]+)@/g,                                                 // Password in URI
];

export function redactString(input: string): string {
  let result = input;
  for (const regex of CREDENTIAL_VALUE_REGEXES) {
    result = result.replace(regex, '[Filtered]');
  }
  return result;
}

export function redactObject<T>(input: T): T {
  if (!input || typeof input !== 'object') {
    return typeof input === 'string' ? (redactString(input) as unknown as T) : input;
  }

  if (Array.isArray(input)) {
    return input.map((item) => redactObject(item)) as unknown as T;
  }

  const output: Record<string, any> = {};
  for (const [key, value] of Object.entries(input)) {
    const isSensitiveKey = SENSITIVE_KEY_PATTERNS.some((pattern) => pattern.test(key));
    if (isSensitiveKey) {
      output[key] = '[Filtered]';
    } else if (typeof value === 'object' && value !== null) {
      output[key] = redactObject(value);
    } else if (typeof value === 'string') {
      output[key] = redactString(value);
    } else {
      output[key] = value;
    }
  }

  return output as T;
}
```

## Hooking into Sentry `beforeSend` & `beforeBreadcrumb`

```typescript
import * as Sentry from '@sentry/node';
import { redactObject, redactString } from './redact.js';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  beforeSend(event) {
    if (event.exception?.values) {
      for (const val of event.exception.values) {
        if (val.value) val.value = redactString(val.value);
      }
    }
    if (event.request?.headers) {
      event.request.headers = redactObject(event.request.headers);
    }
    if (event.request?.url) {
      event.request.url = redactString(event.request.url);
    }
    if (event.tags) {
      event.tags = redactObject(event.tags);
    }
    if (event.extra) {
      event.extra = redactObject(event.extra);
    }
    return event;
  },

  beforeBreadcrumb(breadcrumb) {
    if (breadcrumb.message) {
      breadcrumb.message = redactString(breadcrumb.message);
    }
    if (breadcrumb.data) {
      breadcrumb.data = redactObject(breadcrumb.data);
    }
    return breadcrumb;
  },
});
```
