# Project & Repository Mapping Configuration

How to configure persistent local repository-to-project mappings using `.claude/sentry-cli.local.md` or discover slugs dynamically.

## Local Config File (`.claude/sentry-cli.local.md`)

Create `.claude/sentry-cli.local.md` in the repo or workspace root. Keep it out of git:

```markdown
---
org: zeo-agency
projects:
  site-to-api: project-noah
  skill-semrush: project-noah
  skill-ahrefs: project-noah
has_logs: ["project-noah"]
has_traces: ["project-noah"]
has_replays: []
profiling: false
---

# Notes
- `project-noah` receives both API errors and CLI telemetry.
- Logs are correlated via `trace:<traceId>`.
```

## Live Discovery (Zero Setup)

If no local mapping file exists, discover slugs dynamically:

```bash
# 1. Discover org slug
sentry org list

# 2. Discover project slugs in org
sentry project list <org>/ --json | jq -r '.data[] | "\(.slug)\t\(.platform)"'
```

### Observability Matrix
Check what telemetry types actually exist in each project before querying:

```bash
for s in $(sentry project list <org>/ --json | jq -r '.data[].slug'); do
  iss=$(sentry issue list <org>/$s -q is:unresolved -t 7d -n 100 --json | jq '.data | length')
  log=$(sentry log list <org>/$s -t 7d -n 100 --json | jq '.data | length')
  tr=$(sentry trace list <org>/$s -t 7d -n 100 --json | jq '.data | length')
  printf '%-24s errors=%s logs=%s traces=%s\n' "$s" "$iss" "$log" "$tr"
done
```
