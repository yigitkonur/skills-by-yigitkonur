# Eventing and Tracking

Polling, webhooks, notifications, metrics, history and time tracking in 0.3.28. Check command-specific output and pagination before automating these surfaces.

## Watch

```bash
linear-cli watch issue LIN-123 --interval 30 --output ndjson
linear-cli watch project PROJECT_ID --interval 30 --output ndjson
linear-cli watch team ENG --interval 30 --output ndjson
```

The default interval is ten seconds. Issue events are `initial` and `updated`, with `issue` and `timestamp` fields. They are triggered by changes to `updatedAt`; there is no `stateChanged` event or `new` payload in this release. Project and team watchers use their own resource keys.

```bash
# Prints the current state on each observed issue update, not only state transitions.
linear-cli watch issue LIN-901 --interval 30 --output ndjson \
  | jq --unbuffered -r 'select(.event == "updated") | "\(.timestamp) → \(.issue.state.name)"'
```

Polling consumes API quota. Stop a watcher when its bounded observation task is complete.

## Webhook CRUD

```bash
linear-cli wh list --output json
linear-cli wh get WEBHOOK_ID --output json
linear-cli wh create https://example.com/webhook --events Issue
linear-cli wh update WEBHOOK_ID --url https://example.com/new-webhook
linear-cli wh rotate-secret WEBHOOK_ID
linear-cli wh delete WEBHOOK_ID --force
```

These include remote mutations and require the appropriate permissions. Resource types are sent to Linear; verify valid resource names for the target API. Upstream help uses examples such as `Issue,Comment`. Secrets are redacted by default on supported read/rotation paths; use `--show-secret` only when the actual secret is needed and keep it out of logs.

## `wh listen` creates a remote webhook

This command is not an unauthenticated local HTTP server. It creates a temporary webhook in the selected Linear workspace, then binds the local server, and attempts to delete the webhook on graceful shutdown. A crash or failed cleanup may leave a remote webhook behind; reconcile it using the recorded ID.

```bash
# After explicitly choosing the target workspace and authorizing temporary webhook creation:
linear-cli wh listen --port 8080 --url https://your-tunnel.example.com \
  --events Issue --json
```

Pass the tunnel's **base URL**: the CLI appends `/webhook`. Without `--url` it tries to register `http://localhost:PORT/webhook`, which Linear cannot reach remotely. Do not separately create another webhook merely to use the listener.

The default bind address is `127.0.0.1`; `--bind` can change it. The command uses a supplied `--secret` or the secret returned by creation, refuses to run without a secret, verifies HMAC-SHA256, and limits headers/body/concurrent connections.

Use `--json` (or a JSON output mode) for event payloads. Startup/shutdown messages still share stdout, so stdout as a whole is not pure JSON. When processing captured output, explicitly discard non-JSON lines and validate event fields, for example:

```bash
jq -Rrc 'fromjson? | select(type == "object" and has("action") and has("data"))' listener.log
```

Capture and inspect the listener's complete log separately so cleanup failures remain visible. Forwarding event data to another service requires its own authorization and handling policy.

## Notifications

```bash
linear-cli n list --output json              # unread within fetched pages
linear-cli n count --output json
linear-cli n read NOTIFICATION_ID
linear-cli n read-all
linear-cli n archive NOTIFICATION_ID
linear-cli n archive-all
```

`read-all` and `archive-all` are broad remote mutations. Check the intended scope and handler-specific failure output before using them. Several notification mutations print prose despite a global JSON flag.

## Metrics

```bash
linear-cli mt cycle CYCLE_ID --output json
linear-cli mt project PROJECT_ID --output json
linear-cli mt velocity ENG --cycles 10 --output json
linear-cli sp velocity -t ENG --count 10 --output json
```

`mt velocity` uses `--cycles`; `sp velocity` uses `--count`. They are separate handlers with different response shapes. See `planning/projects-and-cycles.md` and `json-shapes.md`.

## History

```bash
linear-cli hist issue LIN-123 --limit 50 --output json
linear-cli hist issue LIN-123 --all --output json
```

For a time window, inspect the returned timestamp field and filter with `jq`. A limit of 100 is a bounded sample, not proof that all events from today were fetched.

## Time tracking

```bash
linear-cli tm log LIN-123 2h
linear-cli tm log LIN-123 30m
linear-cli tm log LIN-123 1h30m
linear-cli tm list --issue LIN-123 --output json
linear-cli tm update ENTRY_ID --duration 45m
linear-cli tm delete ENTRY_ID --force
```

The parser accepts hours/minutes and plain minute counts. **`1d` is invalid**; use `8h` when eight hours is the intended duration. Time mutations print prose in this release. Their live API support depends on the target workspace/schema and was not verified by offline parser checks.

## See also

- `setup.md` — profile and authentication checks.
- `troubleshooting.md` — rate limits, errors, partial outcomes and listener cleanup.
- `planning/projects-and-cycles.md` — sprint operations.
- `output-and-scripting.md` — stdout/stderr and NDJSON limits.
