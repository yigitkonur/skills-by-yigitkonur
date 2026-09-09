# Issue Merges & Splits Protocol

How to merge duplicate issue clusters or split accidentally merged errors via Sentry CLI and REST API.

## Merging Duplicate Issues

When two distinct issues share the same underlying bug (e.g. an unhandled promise rejection in two different wrapper functions), merge them into a single canonical issue:

### Via Modern Sentry CLI:
```bash
# Merges SOURCE_ISSUE into TARGET_ISSUE
sentry issue merge <TARGET_ISSUE_ID> <SOURCE_ISSUE_ID>
```

### Via Sentry REST API:
`PUT /api/0/projects/{org_slug}/{project_slug}/issues/`
```bash
curl -X PUT \
  -H "Authorization: Bearer ${SENTRY_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "merge": 1,
    "issues": ["7720412315", "7720412364"]
  }' \
  https://sentry.io/api/0/projects/${ORG_SLUG}/${PROJECT_SLUG}/issues/
```

> [!WARNING]
> Merging issues is a permanent operational action. Future events matching either fingerprint will accumulate under the target issue.

## Splitting Issues

If Sentry's default grouping mistakenly merged two unrelated bugs into one issue:
1. Identify the event IDs belonging to the distinct bug.
2. In the Sentry Web UI, open the event and click **Similar Issues -> Split into New Issue**.
3. Or update fingerprint rules in code to give that event class its own explicit fingerprint (`scope.setFingerprint(['unique-bug-identifier'])`).
