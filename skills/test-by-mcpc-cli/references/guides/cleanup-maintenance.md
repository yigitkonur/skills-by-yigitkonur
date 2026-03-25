# Cleanup and maintenance

## Overview

`mcpc --clean` manages the lifecycle of all persistent state that mcpc accumulates during normal use: session records, authentication profiles, and log files. Cleanup falls into two categories — safe (non-destructive, automatic) and destructive (explicit, irreversible). Understanding the distinction prevents accidental data loss and helps recover from broken states.

---

## Command syntax

```
mcpc --clean[=sessions|profiles|logs|all]
```

Running `mcpc --clean` with no value performs safe cleanup only. Use one clean mode per invocation:

```bash
mcpc --clean                      # safe cleanup: stale PIDs, crashed bridges, orphaned logs
mcpc --clean=sessions             # remove all sessions (stops bridges, deletes keychain data)
mcpc --clean=profiles             # remove all authentication profiles + keychain credentials
mcpc --clean=logs                 # delete all files in ~/.mcpc/logs/
mcpc --clean=all                  # sessions + profiles + logs + remaining empty directories
```

---

## What each category cleans

### `sessions`

Calls `cleanSessions()`, which iterates every entry in `~/.mcpc/sessions.json`:

1. Calls `stopBridge(name)` to gracefully shut down the bridge process (errors are silently swallowed — the bridge may already be stopped).
2. Calls `deleteSession(name)` to remove the entry from `sessions.json` and delete any associated keychain credential (the per-session bearer token stored at `mcpc:session:<name>:bearer-token`).

After this runs, all session entries are gone. Any running bridge process that was not successfully stopped will become an orphan — it will be detected and cleaned on the next consolidation pass.

### `profiles`

Calls `deleteAuthProfiles()`, which removes all entries from `~/.mcpc/profiles.json` and deletes the corresponding OAuth token bundles from the OS keychain (keys of the form `mcpc:auth:<serverUrl>:<profileName>:tokens`).

If any currently-registered session references a now-deleted profile, the CLI emits a warning:

```
Warning: 2 session(s) were using deleted profiles: apify, staging
These sessions may fail to authenticate. Recreate them or login again.
```

Those sessions will still exist in `sessions.json` but will fail on next use with an authentication error. Recreate them with `mcpc <server> connect @<name> --profile <profile>` after running `mcpc login` again.

### `logs`

Calls `cleanLogs()`, which reads `~/.mcpc/logs/` and deletes every file matching `*.log` or `*.log.<number>` (rotated log files). This is unconditional — all log files are deleted regardless of age or whether the associated session still exists.

Bridge logs follow the naming pattern `bridge-@<session>.log`. Rotated copies are named `bridge-@<session>.log.1`, `.log.2`, etc. (up to 5 rotation files, max 10 MB each).

### `all`

Runs `cleanSessions()`, `deleteAuthProfiles()`, `cleanLogs()`, a final `cleanStale()` pass, then attempts to remove the `~/.mcpc/bridges/` and `~/.mcpc/logs/` directories entirely with `rm -rf`. If `~/.mcpc/` is empty afterwards it is also removed. This is the most destructive operation — it resets mcpc to a clean-install state.

---

## Safe cleanup vs destructive cleanup

| Mode | What it removes | Reversible |
|---|---|---|
| `mcpc --clean` (no args) | Crashed bridge records, stale PIDs, orphaned log files older than 7 days | Yes — sessions and credentials untouched |
| `mcpc --clean=sessions` | All session records and per-session keychain tokens | No — must reconnect manually |
| `mcpc --clean=profiles` | All OAuth profiles and keychain credential bundles | No — must `mcpc login` again |
| `mcpc --clean=logs` | All log files in `~/.mcpc/logs/` | Yes — logs are regenerated on next bridge start |
| `mcpc --clean=all` | Everything above plus empty directories | No |

The default `mcpc --clean` invocation is always safe to run. It never removes sessions or profiles you created intentionally.

---

## How `consolidateSessions()` works at startup

`consolidateSessions()` runs automatically at startup whenever mcpc launches and a sessions file already exists. The `clean` command also calls it explicitly (with `force: true`) as part of safe cleanup.

The function:

1. Reads `~/.mcpc/sessions.json` under a file lock.
2. For each session, checks whether the recorded PID is still alive using `process.kill(pid, 0)` (a no-op signal that only tests existence).
3. If the PID is gone, marks the session status as `crashed` and clears the `pid` field.
4. Removes sessions that have passed their expiry timestamp (`expiresAt` field, if set).
5. Writes the updated sessions file atomically (write to temp file, then rename).
6. Returns a result object with counts: `{ sessions, crashedBridges, expiredSessions }`.

The `sessions` field in the return value is a `Record<string, SessionEntry>` of all surviving sessions, which is then passed to `cleanupOrphanedLogFiles()` so it knows which sessions are still active.

---

## Session consolidation: dead PID detection and crashed status marking

When a bridge process is killed unexpectedly (OOM killer, `kill -9`, machine sleep/resume, power loss), its PID entry in `sessions.json` becomes stale. On the next mcpc invocation:

1. `consolidateSessions()` finds the PID is not running.
2. The session status is set to `crashed`.
3. The CLI surface (`mcpc`) displays the session as crashed with a yellow indicator.
4. On the next command that targets this session (e.g., `mcpc @name tools-list`), the CLI auto-restarts the bridge and retries.

The `crashedBridges` counter returned by `consolidateSessions()` reflects how many sessions were transitioned to crashed state in this pass. During `mcpc --clean`, this count is surfaced in the output:

```
Cleaned 1 crashed bridge(s), 0 expired session(s), 3 orphaned log(s)
```

---

## Orphaned log file cleanup

`cleanupOrphanedLogFiles()` in `src/lib/cleanup.ts` handles log files for sessions that no longer exist. It is called by both `cleanStale()` (triggered by `mcpc --clean` with no args) and the bridge process at startup.

Rules:

- Only files matching `bridge-(@.+?)\.log(?:\.\d+)?` are considered.
- The session name is extracted from the filename and looked up in the active sessions map.
- If the session does not exist in the map, the file is a candidate for deletion.
- The file is only deleted if its `mtime` is older than `maxAgeDays` (default: **7 days**).
- Files younger than 7 days are left intact even if the session is gone — this preserves recent crash diagnostics.
- The `skipSession` option allows the current bridge to exclude its own log file from deletion.

This means running `mcpc --clean` immediately after a crash will not delete the crash log if it was written within the last week. To force-delete all logs regardless of age, use `mcpc --clean=logs`.

---

## When to use each clean mode

### After crashes

```bash
mcpc --clean          # removes stale PIDs and marks crashed sessions; safe to run anytime
```

If sessions are stuck in `crashed` state and auto-restart is not working:

```bash
mcpc --clean=sessions # tears down all sessions; start fresh with mcpc connect
```

### During testing

```bash
mcpc --clean=all      # full reset between test runs; equivalent to a fresh install
```

For CI pipelines, run `mcpc --clean=all` in a teardown step to avoid leaked sessions and credentials between jobs.

### Before CI

```bash
mcpc --clean=sessions # ensures no stale sessions interfere with test targets
mcpc --clean=logs     # keeps log directory size bounded
```

### Routine disk space management

```bash
mcpc --clean=logs     # removes all rotated and active log files
mcpc --clean          # removes orphaned logs older than 7 days without touching sessions
```

Bridge logs rotate at 10 MB with up to 5 files retained, so maximum per-session log usage is ~50 MB. With many sessions over time, `mcpc --clean=logs` can reclaim significant space.

---

## Recovering from cleanup mistakes

### Accidentally cleaned sessions

Sessions themselves are cheap to recreate. Run:

```bash
mcpc <server> connect @<name>
```

If the session used OAuth authentication, the profile may still exist (unless you also ran `mcpc --clean=profiles`). Re-link it:

```bash
mcpc <server> connect @<name> --profile <profile-name>
```

### Accidentally cleaned profiles

Profiles store OAuth tokens. After `mcpc --clean=profiles`, you must re-authenticate:

```bash
mcpc login <server>                          # recreates the default profile
mcpc login <server> --profile <name>         # recreates a named profile
mcpc <server> connect @<name> --profile <name>
```

### Accidentally cleaned all

`mcpc --clean=all` is equivalent to removing `~/.mcpc/` entirely. Recovery steps:

1. Run `mcpc login <server>` for each server you use with OAuth.
2. Run `mcpc <server> connect @<name>` for each session you need.
3. Logs will regenerate automatically when bridges start.

Bearer tokens passed via `--header` are not affected — they were never stored as profiles.

---

## Storage management

### Directory layout

```
~/.mcpc/
├── sessions.json          # session records (file-locked)
├── profiles.json          # OAuth profile metadata
├── history                # shell command history (last 1000 lines)
├── bridges/
│   └── @<name>.sock       # Unix domain socket per active bridge
└── logs/
    ├── bridge-@<name>.log
    ├── bridge-@<name>.log.1
    └── ...
```

### Orphaned log file cleanup (`cleanupOrphanedLogFiles`)

When `mcpc --clean` or `mcpc --clean=logs` runs, the `cleanupOrphanedLogFiles()` function handles age-based cleanup:

1. Scans `~/.mcpc/logs/` for files matching `bridge-@<session>.log` (and rotated variants `.log.1`, `.log.2`, etc.)
2. For each log file, checks if the session still exists in `sessions.json`
3. If the session is gone (orphaned log), checks file age against `maxAgeDays` (default: **7 days**)
4. Only deletes files older than 7 days — recent debug logs are preserved even if the session is gone
5. Skips logs for the `skipSession` (the current bridge session, if called from within a bridge)

This means after a session crash, you have 7 days to inspect the logs before they're cleaned up.

### Log rotation

Bridge logs are capped at **10 MB per file** with **5 rotated copies** retained (`.log` → `.log.1` → `.log.2` → `.log.3` → `.log.4` → `.log.5`). Rotation is asynchronous and handled automatically — no manual intervention needed during normal operation.

To check current log disk usage:

```bash
du -sh ~/.mcpc/logs/
```

### Disk space recommendations

- Run `mcpc --clean=logs` periodically on long-lived machines or CI systems.
- Run `mcpc --clean` (safe mode) in CI teardown to remove orphaned logs from failed runs.
- The `~/.mcpc/bridges/` directory contains only socket files — these are tiny and cleaned automatically when bridges stop.

### JSON output for scripting

All clean operations support `--json` for scripting:

```bash
mcpc --json --clean=all
```

Output fields: `crashedBridges`, `expiredSessions`, `orphanedBridgeLogs`, `sessions`, `profiles`, `logs`, `affectedSessions`.
