# Troubleshooting

Diagnose the installed command's stdout, stderr, and exit code together. The notes below target 0.3.28.

## Errors and partial results

| Exit | Interpretation |
|---|---|
| 0 | Handler returned successfully; inspect its result. Auth status and import have important exceptions. |
| 1 | General failure; inspect stderr. |
| 2 | Not-found or CLI parser failure. Parser errors are plain text. |
| 3 | Authentication failure; verify credentials and effective identity. |
| 4 | Rate limit; honor a supplied retry delay with a bounded fallback. |

Runtime errors in JSON mode are written to stderr, not stdout. Some error codes are inferred from message text, and `details` or `retry_after` can be null. Preserve both channels:

```bash
if linear-cli i get LIN-999 --output json > result.json 2> error.log; then
  code=0
else
  code=$?
fi
if [ "$code" -ne 0 ]; then
  cat error.log >&2
fi
```

A nonzero multi-get may still contain successfully fetched issues in `result.json`. Reconcile requested IDs before retrying. Do not concatenate progress text, partial stdout, and the JSON error envelope and then assume the combination is valid JSON.

Parser regression probe (this intentionally fails):

```bash
if linear-cli i list --state > /tmp/linear-parser.out 2> /tmp/linear-parser.err; then
  echo "Expected a parser failure" >&2
  exit 1
else
  test "$?" -eq 2 || exit 1
fi
```

## Auth and profile

Use `u me` as the effective identity check. `auth status --validate` can exit 0 with `validated: false`, while `configured` excludes environment-only credentials. A usable OAuth profile is preferred over the API-key fallback; setting `LINEAR_API_KEY` alone does not always switch identities.

```bash
linear-cli auth status --validate --output json
linear-cli u me --output json
linear-cli config workspace-current
linear-cli config workspace-list
linear-cli config workspace-switch work
```

If credentials fail, use `auth login` for an API key or `auth oauth` for a browser OAuth flow. Refresh failure is one possible cause of an auth error; revocation, permissions, and the wrong profile also need consideration. Keep secrets out of shell history and reports. See `setup.md`.

## Rate limits

Retry a read at most once after a bounded delay. Keep JSON stderr separate from stdout:

```bash
if linear-cli i list --output json > result.json 2> error.log; then
  code=0
else
  code=$?
fi
if [ "$code" -eq 4 ]; then
  delay=$(jq -er '.retry_after // 5 | numbers | select(. >= 0 and . <= 60)' error.log 2>/dev/null) || delay=5
  sleep "$delay"
  if linear-cli i list --output json > result.json 2> error.log; then
    code=0
  else
    code=$?
  fi
fi
[ "$code" -eq 0 ] || { cat error.log >&2; exit "$code"; }
```

`i get LIN-1 LIN-2 LIN-3` bounds concurrency to ten per-ID requests; it does not combine them into one GraphQL request. Narrow list queries or use a purpose-built raw query when reducing request count matters. Do not automatically retry a mutation whose server outcome is unknown: check whether it already succeeded.

## Missing command or different flags

Check `linear-cli --version` and the exact subcommand's help. A missing command can indicate a different project with the same name, an older version, or an inaccurate example; it does not always justify updating automatically. Use `linear-cli update --check` when a version comparison is useful, then explicitly choose an update method from upstream documentation.

## Pager and stale data

Use `LINEAR_CLI_NO_PAGER=1` or `--no-pager` in agent runs. If a terminal is already left in a bad mode, restore it with `reset` or `stty sane`. The 0.3.28 source scopes pager cleanup before process exit; do not describe the older cleanup bug as necessarily present in every installed build.

```bash
linear-cli cache status
linear-cli i list --no-cache --output json
# Local cache mutation, only when needed:
linear-cli cache clear
```

If CLI and another client disagree, compare profile, permissions, filters, pagination, cache and timestamps against the owning Linear data. Neither client is inherently authoritative merely because it is a CLI or MCP tool.

## Bulk and import failures

Bulk handlers vary in concurrency and failure reporting. Preserve the target set and old values, inspect successful IDs and warnings, and re-read every affected resource. A generic inverse status change is not rollback: original states or assignees may differ.

Import is especially important: `--dry-run` previews rows without resolving status/user/label names; actual import can omit unresolved fields with warnings, and per-item create failures do not necessarily make the process fail. Inspect stderr and reconcile results. See `data/import-export.md`.

## Webhooks and downloads

`wh listen` authenticates and creates a temporary remote webhook before listening locally. It defaults to `127.0.0.1` but allows `--bind`; pass a public tunnel base URL with `--url`. It verifies signatures and attempts cleanup on graceful shutdown. Startup and shutdown prose still appears on stdout, even in event JSON mode. See `eventing-and-tracking.md` before scripting it.

`up fetch` accepts validated HTTPS upload URLs on `uploads.linear.app`. A host-validation error is different from an API permission or download failure. Extract actual URLs from Markdown rather than passing a complete description string.

## Diagnostic report

Collect only the information relevant to the failure: CLI version, exact command with secrets removed, stdout/stderr, exit code, selected profile, and whether the result was partial. Avoid attaching raw credential-bearing config files. Distinguish parser/source/offline checks from successful live API operations.
