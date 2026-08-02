# Cleanup and Maintenance

`mcpc` (verified against 0.6.0) uses a `clean` command, not the old `--clean=...`
flag family (removed in v0.2.0, when the CLI moved to command-first syntax).

## Safe forms

```bash
mcpc clean
mcpc clean sessions
mcpc clean profiles
mcpc clean logs
mcpc clean sessions logs
mcpc clean all
```

## What each target does

- `clean` with no arguments removes stale data only (crashed bridges, expired sessions, orphaned bridge logs) — non-destructive
- `clean sessions` (named explicitly) removes **every** session record, not just stale ones, plus their per-session stored headers or proxy bearer tokens — the "stale/crashed" wording in `--help` describes the no-args path, not this targeted form
- `clean profiles` removes **all** saved authentication profiles
- `clean logs` removes **all** bridge log files, regardless of age or whether the owning session is still active
- `clean all` removes all of the above unconditionally

Multiple cleanup targets in one invocation are valid.
`mcpc clean sessions logs --json` is fine — real run: `✓ Removed 1 session(s)` /
`✓ Removed 21 log file(s)`.
`--json` shape: `{ crashedBridges, expiredSessions, orphanedBridgeLogs, sessions, profiles, logs }`
(no-args cleanup populates only the first three; targeted resources populate their own counters).

## Inspect before you clean logs

Use `mcpc @session logs` instead of reading the bridge log file raw — it spans
rotation (`.log.1`–`.log.5`), filters by time, and can stream:

```bash
mcpc @session logs                   # last 50 lines (default)
mcpc @session logs -n 200 --json     # last 200 lines, `[{time,level,context?,msg}]`
mcpc @session logs --follow          # stream new lines (ESC/Ctrl+C/q to stop)
mcpc @session logs --since 1h        # entries from the last hour
```

## Sequence cleanup, do not race it

```bash
mcpc close @research
mcpc clean sessions
```

Do not run `close` and `clean` for the same session in parallel.
If `close` already says `Session not found`, skip straight to targeted cleanup.
`clean sessions` here purges every session record in `sessions.json`, not only
`@research` — fine in disposable CI state (a temporary `MCPC_HOME_DIR`) but
destructive to other live sessions on a shared machine. `mcpc clean` with no
arguments is the safe, targeted-nothing alternative when other sessions must survive.

## What not to assume

- cleanup does not rely on a public `expiresAt` field; document status-based cleanup behavior instead
- header-based bearer tokens are not OAuth profiles, but session cleanup still removes them because they belong to the session record
- `clean all` is not a casual troubleshooting step on a machine with saved profiles

## Useful local paths

- `~/.mcpc/sessions.json`
- `~/.mcpc/profiles.json`
- `~/.mcpc/credentials.json` — fallback credential store when the OS keychain is unavailable
- `~/.mcpc/wallets.json`
- `~/.mcpc/logs/bridge-<@session>.log` (rotated to `.log.1`–`.log.5`) — read via `mcpc @session logs`, not raw

Note: the interactive `shell` command (and its `~/.mcpc/shell-history` path) was removed in v0.4.0; the path no longer exists.
