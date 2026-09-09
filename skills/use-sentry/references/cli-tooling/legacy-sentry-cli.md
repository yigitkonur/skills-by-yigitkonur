# Legacy Sentry CLI (`sentry-cli` binary) Reference

Complete manual for the classic `sentry-cli` tool (`/usr/local/bin/sentry-cli`), used for release management, sourcemap uploads, and issue queries.

## Binary Verification

```bash
which sentry-cli
sentry-cli --version
```

Verify authentication:
```bash
sentry-cli info
```

## Issue Management Commands

### List Issues
```bash
sentry-cli issues list
sentry-cli issues list --status unresolved
```

### Resolve an Issue
```bash
sentry-cli issues resolve <ISSUE_ID>
```

## Releases & Source Maps

### Create Release & Associate Commits
```bash
sentry-cli releases new "$VERSION"
sentry-cli releases set-commits "$VERSION" --auto
```

### Upload Source Maps
```bash
sentry-cli sourcemaps upload --release "$VERSION" ./dist
```

### Finalize Release
```bash
sentry-cli releases finalize "$VERSION"
```

## Binary Comparison

| Feature | `sentry-cli` (Classic) | `sentry` (Modern) |
|---|---|---|
| Binary name | `sentry-cli` | `sentry` |
| Primary focus | Build pipelines, sourcemaps, releases | Production debugging, triage, logs, spans |
| Issue listing output | ASCII table | JSON with `--json` or formatted tables |
| Event details | Basic | Full embedded `.event` with stack & breadcrumbs |
| Streaming logs | Not supported | Supported (`sentry log list -f`) |
