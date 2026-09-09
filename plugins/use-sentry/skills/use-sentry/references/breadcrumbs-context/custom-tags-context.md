# Custom Tags & Environment Context

How to attach searchable key-value tags and isolate issues by customer tenant, user tier, deployment region, or operational driver.

## What Makes Tags Powerful

In Sentry, **tags are indexed**, which allows:
- Instant filtering in Sentry search (`tenant_id:acme_corp`).
- Grouping in Sentry Discover (`SELECT count() GROUP BY user_tier`).
- Calculating regression impact across customer cohorts.

## 1. Setting Global vs Scoped Tags

### Global Tags (Across Entire Lifecycle)
```typescript
import * as Sentry from '@sentry/node';

Sentry.setTag('environment', process.env.NODE_ENV || 'production');
Sentry.setTag('region', process.env.AWS_REGION || 'eu-west-1');
Sentry.setTag('service_version', process.env.APP_VERSION || '1.0.0');
```

### Request-Scoped Tags (Using Scope)
```typescript
Sentry.withScope((scope) => {
  scope.setTag('tenant_id', req.tenantId);
  scope.setTag('user_tier', req.user.plan); // 'enterprise' | 'free'
  scope.setTag('request_id', req.headers['x-request-id']);
  scope.setTag('driver', 'kernel-cloud');

  // Set authenticated user context
  scope.setUser({
    id: req.user.id,
    email: req.user.email, // Automatically masked if configured
    ip_address: req.ip,
  });

  Sentry.captureException(err);
});
```

## Recommended Tag Taxonomy

| Tag Key | Example Values | Purpose |
|---|---|---|
| `tenant_id` | `org_998`, `zeo_agency` | Pinpoint which customer is affected |
| `user_tier` | `free`, `pro`, `enterprise` | Prioritize enterprise customer escalations |
| `region` | `us-east-1`, `eu-central-1` | Detect regional cloud provider outages |
| `driver` | `kernel`, `playwright`, `undici` | Identify failing subsystem |
| `site` | `semrush`, `ahrefs` | Isolate upstream integration failures |
| `request_id` | `uuid-v4` | Correlate with API gateway logs |
