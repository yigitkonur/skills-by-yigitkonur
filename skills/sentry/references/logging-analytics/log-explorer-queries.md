# Sentry Log Explorer Querying & Syntax Reference

How to use the Log Explorer syntax to query, filter, and correlate structured logs across distributed services.

## Syntax Operators Overview

Sentry's Log Explorer uses standard key-value search operators with implicit AND:

| Query Pattern | Description | Example |
|---|---|---|
| `level:<severity>` | Filter by log level | `level:error`, `level:warning` |
| `service:<name>` | Filter by microservice name | `service:auth-api` |
| `trace:<traceId>` | Filter all logs from a specific distributed trace | `trace:9ec60100773b4f648b265b1618c774f0` |
| `message:*pattern*` | Wildcard text match in log message | `message:*connection refused*` |
| `timestamp:[start TO end]` | Absolute time range query | `timestamp:[2026-09-08T00:00:00Z TO 2026-09-09T00:00:00Z]` |
| `tag:<key>` | Filter by presence of custom attribute | `driver:kernel`, `status_code:>499` |

## Top Investigation Recipes

### 1. Correlating Logs for a Given Sentry Error
When you have an issue's `traceId`:
```bash
sentry log list <org>/<project> -q "trace:9ec60100773b4f648b265b1618c774f0" --json \
  | jq -r '.data[] | "\(.timestamp) [\(.severity)] \(.message)"'
```

### 2. High-Severity Warning & Error Stream
```bash
sentry log list <org>/<project> -q "level:[error,fatal]" -t 2h -n 50 --json
```

### 3. Service-Specific Failure Inspection
```bash
sentry log list <org>/<project> -q "service:scraper level:error" -t 24h
```
