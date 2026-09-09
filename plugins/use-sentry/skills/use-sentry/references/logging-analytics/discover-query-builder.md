# Discover Query Builder & Analytics

How to run complex analytical queries across errors, transactions, and spans to discover systemic health trends and user impact.

## What is Sentry Discover?

Discover allows querying the raw telemetry database across all projects in an organization using SQL-like aggregations.

## Available Aggregate Functions

| Function | Description | Example |
|---|---|---|
| `count()` | Total number of events | `count()` |
| `count_unique(field)` | Unique values count | `count_unique(user.id)`, `count_unique(ip)` |
| `p50(duration)` | 50th percentile (median) duration | `p50(transaction.duration)` |
| `p95(duration)` | 95th percentile latency | `p95(span.duration)` |
| `p99(duration)` | 99th percentile worst-case latency | `p99(transaction.duration)` |
| `failure_rate()` | Percentage of events resulting in error | `failure_rate()` |
| `apdex(score)` | Apdex user satisfaction score | `apdex(300)` |

## Querying Discover via CLI (`sentry explore`)

### 1. Slowest Endpoints by p95 Latency
```bash
sentry explore <org>/<project> -d spans -q 'is_transaction:true' \
  -F 'transaction' -F 'p95(span.duration)' -F 'count()' \
  -s '-p95(span.duration)' -t 7d -n 10
```

### 2. Error Volume by Customer Tenant
```bash
sentry explore <org>/<project> -d errors \
  -F 'tenant_id' -F 'count()' \
  -q 'is:unresolved' -t 14d -n 10
```

### 3. API Error Rate Across Releases
```bash
sentry explore <org>/<project> -d errors \
  -F 'release' -F 'count()' -F 'count_unique(user.id)' \
  -q 'is:unresolved' -t 7d
```

## Running Raw Discover Queries via Sentry REST API

`GET /api/0/organizations/{org_slug}/events/?field=transaction&field=p95(transaction.duration)&query=is_transaction:true&statsPeriod=7d`

```bash
curl -s -H "Authorization: Bearer ${SENTRY_AUTH_TOKEN}" \
  "https://sentry.io/api/0/organizations/${ORG_SLUG}/events/?field=transaction&field=count()&query=event.type:error&statsPeriod=24h" | jq '.data'
```
