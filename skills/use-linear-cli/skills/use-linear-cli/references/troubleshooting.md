# Troubleshooting

Failure-mode catalog for `linear-cli`. Diagnose by exit code first; route to the right recovery from there.

## Exit-code dispatch

| Exit | Symptom | First move |
|---|---|---|
| 0 | success | n/a |
| 1 | general error | parse JSON error envelope; check the `details.request_id` and surface it |
| 2 | not found | the ID/key/name doesn't exist in this workspace; verify with `i get`, `t list`, `l list` |
| 3 | auth error | `linear-cli auth status` → re-auth (see Auth recovery) |
| 4 | rate limited | sleep `retry_after`, retry once (see Rate-limit recovery) |

Always combine `--output json` with `2>&1` capture so you have the envelope:

```bash
out=$(linear-cli i get LIN-999 --output json 2>&1)
code=$?
if [ $code -ne 0 ]; then
  echo "$out" | jq -r '"\(.code) \(.message) (req \(.details.request_id))"'
fi
```

## Auth recovery (exit 3)

```bash
linear-cli auth status                      # show current auth + expiry
# If empty / expired:
linear-cli auth login                       # API key
#   or
linear-cli auth oauth                       # OAuth + PKCE
linear-cli u me                             # confirm
```

For agent runs, prefer the `LINEAR_API_KEY` env var (highest priority) over keyring or config-file storage:

```bash
export LINEAR_API_KEY=lin_api_xxx
linear-cli u me
```

If `auth status` reports OAuth tokens that won't refresh:

```bash
linear-cli auth revoke
linear-cli auth oauth
```

If you suspect the wrong workspace:

```bash
linear-cli config workspace-current
linear-cli config workspace-list
linear-cli config workspace-switch <profile>
```

See `setup.md` for the full auth model.

## Rate-limit recovery (exit 4)

The JSON error envelope contains `retry_after` (seconds). Sleep and retry once.

```bash
attempt() {
  out=$(linear-cli "$@" --output json 2>/dev/null) ; code=$?
  if [ "$code" = 4 ]; then
    sleep "$(echo "$out" | jq -r '.retry_after // 5')"
    out=$(linear-cli "$@" --output json) ; code=$?
  fi
  echo "$out"
  return $code
}
```

If you keep tripping rate limits, you're probably hammering `i get` in a loop. Use **batch fetch** instead — `linear-cli i get LIN-1 LIN-2 LIN-3 ...` is one API call.

## "Command in upstream docs but not in my binary"

Your installed CLI is older than the docs.

```bash
linear-cli update --check       # report current vs latest, no install
linear-cli update               # self-update via Cargo
# or
cargo install linear-cli --force
```

If `linear-cli update` fails (some release builds skip the asset upload step), use `cargo install linear-cli --force` directly. See the project's release-asset note in upstream `AGENTS.md`.

## macOS pager leaves the terminal raw

Symptom: after a successful table-output command on macOS, the shell acts raw-ish until you run `reset` or `stty sane`. `stty -a` after the command may show `pendin`.

Recovery:

```bash
reset       # or: stty sane
```

Workaround for agent runs (stable):

```bash
export LINEAR_CLI_NO_PAGER=1
# or per command
linear-cli i list --no-pager
```

This is a known regression involving an early `std::process::exit` skipping pager `Drop` cleanup. Stay on `--no-pager` until a fixed release lands.

## Stale cache

Symptom: list / get returns data older than expected.

```bash
linear-cli cache status
linear-cli cache clear
# or per command
linear-cli i list --no-cache
```

## Empty result, want to fail loudly

```bash
linear-cli i list --mine --state "In Progress" --fail-on-empty
# exits non-zero when array is empty
```

## "Linear MCP says X, CLI says Y"

Trust the CLI for any task this skill covers. Linear MCP and `linear-cli` query the same Linear API but the CLI is closer to the raw GraphQL surface and far cheaper in tokens. If the MCP path is mandated by the user, flag the cost difference and continue.

## Webhook listener won't start

```bash
# Confirm the port is free
lsof -nP -iTCP:8080 -sTCP:LISTEN

# Confirm the secret is set
linear-cli wh listen --port 8080 --secret "$WEBHOOK_SECRET"
```

The listener defaults to `127.0.0.1`, verifies HMAC-SHA256, and enforces header/body size limits. See `eventing-and-tracking.md`.

## Bulk operation hit a partial failure

`b update-state`, `b assign`, `b label`, etc. process IDs sequentially. On a partial failure:

1. Re-run with `--dry-run` to confirm which IDs would be touched again.
2. Inspect each via `linear-cli i get <ID> --output json` to see actual state.
3. Roll back by inverting the mutation (e.g. `b update-state -s "In Progress"` after a botched `Done` run).
4. Use `recipes/creating-many-issues.md` "atomicity" pattern next time.

## OAuth callback never returns

The OAuth flow binds `127.0.0.1:<random-port>` and waits for a redirect. If the browser never returns:

- check that `127.0.0.1` is reachable from the browser (corporate VPN sometimes blocks loopback)
- check firewall / `pf` rules
- fall back to API key auth

## "Permission denied on uploads.linear.app"

`linear-cli up fetch` only accepts URLs from `uploads.linear.app`. Other hosts are rejected for safety. Use plain `curl` if you need to fetch from elsewhere.

## Diagnostic checklist

When in doubt, run:

```bash
linear-cli --version
linear-cli auth status
linear-cli doctor
linear-cli u me
linear-cli config workspace-current
linear-cli cache status
```

…and surface all five results in the bug report.

## See also

- `setup.md` — full auth model, env vars, keyring caveats.
- `output-and-scripting.md` — exit-code contract, JSON envelope.
- `json-shapes.md` — exact error-envelope keys.
