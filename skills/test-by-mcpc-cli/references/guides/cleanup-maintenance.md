# Cleanup and Maintenance

`mcpc clean [resources...]` (verified against 0.6.0) is the only cleanup
command — there is no separate flag-based interface.

## Two operations share one name

Bare `mcpc clean` is **safe**: it removes only stale/crashed data (dead
bridges, expired sessions, orphaned bridge logs) and never touches a live
session. Naming a resource explicitly — `sessions`, `profiles`, `logs`, or
`all` — is **unconditional**: it wipes every record of that kind, live or
dead, and kills the bridge process behind any live session it removes.
`mcpc clean sessions` reads like a narrower version of the default; it is
not — the `--help` text's "Remove stale/crashed session records" wording
describes only the no-args path.

```bash
mcpc clean                # safe: stale/crashed data only
mcpc clean sessions       # destructive: ALL sessions, live or not
mcpc clean profiles       # destructive: ALL auth profiles
mcpc clean logs           # destructive: ALL log files
mcpc clean sessions logs  # destructive: targets combine in one call
mcpc clean all            # destructive: sessions + profiles + logs
```

Test destructive forms only inside an isolated `MCPC_HOME_DIR` — running
`mcpc clean sessions`/`all` against the default home on a shared machine
kills every other session on that box, not just yours.

## What each target does

- `clean` (no args) — stale/crashed bridges, expired sessions, orphaned bridge logs. Non-destructive.
- `clean sessions` — removes **every** session record, live or not, plus per-session stored headers/proxy bearer tokens; kills each session's bridge process.
- `clean profiles` — removes **all** saved authentication profiles.
- `clean logs` — removes **all** bridge log files, regardless of age or whether the owning session is still active.
- `clean all` — sessions + profiles + logs, unconditionally.

`--json` shape: `{ crashedBridges, expiredSessions, orphanedBridgeLogs, sessions, profiles, logs }`
(no-args cleanup populates only the first three; targeted resources populate their own counters).
Real combined run: `mcpc clean sessions logs --json` → `✓ Removed 1 session(s)` / `✓ Removed 21 log file(s)`.

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
mcpc clean
```

Do not run `close` and `clean` for the same session in parallel. If `close`
already says `Session not found` (exit 1 — closing an already-closed session
is a hard error, not a no-op), bare `clean` safely clears stale records. Reach
for `clean sessions` only when you intend to purge every session in
`sessions.json`, not only `@research`.

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
