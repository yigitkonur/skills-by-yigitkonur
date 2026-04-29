# Eventing and Tracking

Watching for changes, webhooks (CRUD + local listener), notifications, metrics, history, and time tracking. Cold-path commands an agent rarely reaches for daily but needs to know exist.

## Watch — poll for live changes

```bash
linear-cli watch LIN-123                       # poll every 10 seconds (default)
linear-cli watch LIN-123 --interval 30         # every 30 seconds
linear-cli watch LIN-123 -i 60
linear-cli watch LIN-123 --output json         # stream changes as JSON
```

Use sparingly — polling consumes API quota. For real-time, use webhooks instead.

## Webhooks — CRUD

```bash
linear-cli wh list
linear-cli wh list --output json

linear-cli wh get WEBHOOK_ID
linear-cli wh create https://example.com/hook --events Issue
linear-cli wh update WEBHOOK_ID --url https://new-url.example.com
linear-cli wh delete WEBHOOK_ID --force

linear-cli wh rotate-secret WEBHOOK_ID         # rotate signing secret
```

Event types are documented in Linear's webhook docs. Common: `Issue`, `IssueComment`, `Project`, `Cycle`.

## Webhook local listener (HMAC-SHA256)

For local development and integration testing:

```bash
linear-cli wh listen --port 8080
linear-cli wh listen --port 8080 --secret "$WEBHOOK_SIGNING_SECRET"
```

The listener:

- binds `127.0.0.1` only (not all-interfaces)
- verifies HMAC-SHA256 on every event
- enforces header / body size limits

Combine with a tunnel (`ngrok`, `cloudflared`) to receive real Linear events on your laptop:

```bash
ngrok http 8080
linear-cli wh create "https://abc.ngrok.io/hook" --events Issue
linear-cli wh listen --port 8080 --secret "$SECRET"
```

Rotate the secret routinely with `linear-cli wh rotate-secret`.

## Notifications

Linear's per-user notification inbox.

```bash
linear-cli n list                              # unread
linear-cli n list --output json
linear-cli n count                             # unread count

linear-cli n read NOTIFICATION_ID
linear-cli n read-all

linear-cli n archive NOTIFICATION_ID
linear-cli n archive-all
```

## Metrics

Velocity, burndown, project progress.

```bash
linear-cli mt cycle CYCLE_ID                   # cycle metrics
linear-cli mt cycle CYCLE_ID --output json
linear-cli mt project PROJECT_ID
linear-cli mt velocity ENG                     # team velocity
linear-cli mt velocity ENG --cycles 10         # last 10 cycles
```

For the friendlier sprint-analytics surface, see `planning/projects-and-cycles.md` (`linear-cli sp velocity`).

## History

Per-issue activity timeline.

```bash
linear-cli hist issue LIN-123
linear-cli hist issue LIN-123 --output json
linear-cli hist issue LIN-123 --limit 50
linear-cli hist issue LIN-123 --all
```

Useful for "who changed this and when" and audit trails.

## Time tracking

```bash
linear-cli tm log LIN-123 2h                   # log 2 hours
linear-cli tm log LIN-123 30m                  # 30 minutes
linear-cli tm log LIN-123 1h30m                # 1.5 hours

linear-cli tm list --issue LIN-123
linear-cli tm list --output json
linear-cli tm delete ENTRY_ID
```

Duration format: `30m`, `1h`, `2h30m`, `1d` (= 8 hours).

## Recipe: watch for status changes on a critical issue

```bash
linear-cli watch LIN-901 --interval 30 --output json \
  | jq -r 'select(.event == "stateChanged") | "\(.timestamp) → \(.new.state.name)"'
```

## Recipe: post Linear events into Slack via webhook listener

```bash
linear-cli wh create "https://my-bridge.example.com/linear" --events Issue
linear-cli wh listen --port 8080 --secret "$SECRET" \
  | jq --unbuffered -r 'select(.action == "create") | .data.identifier' \
  | while read -r id; do
      curl -X POST -d "{\"text\":\"new issue: $id\"}" "$SLACK_WEBHOOK"
    done
```

## Recipe: "what changed today on this issue?"

```bash
linear-cli hist issue LIN-123 --since 1d --output json
```

## Common confusions

| Looks like | Is actually |
|---|---|
| `watch` | Poll one issue (or project / team). Quota-heavy. |
| `wh listen` | Local HMAC-verifying listener. Real-time. |
| `n` | User-inbox notifications, not webhook events. |
| `hist` | Issue activity timeline. |
| `mt` | Raw metric numbers. |
| `sp` | Pre-rendered sprint analytics (uses `mt` internally). |
| `tm` | Time tracking. |

## See also

- `setup.md` — webhook listener security defaults.
- `troubleshooting.md` — when the listener won't start or rate limits hit.
- `planning/projects-and-cycles.md` — `sp velocity` is friendlier than `mt velocity` for most users.
- `output-and-scripting.md` — `--output ndjson` for streaming.
