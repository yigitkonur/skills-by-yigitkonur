# Cleanup and Maintenance

`mcpc 0.2.x` uses a `clean` command, not the old `--clean=...` flag family.

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

- `clean` with no arguments removes stale data only
- `clean sessions` removes stale or crashed session records and their per-session stored headers or proxy bearer tokens
- `clean profiles` removes saved authentication profiles
- `clean logs` removes bridge logs
- `clean all` removes all of the above

Multiple cleanup targets in one invocation are valid.
`mcpc clean sessions logs --json` is fine.

## Sequence cleanup, do not race it

```bash
mcpc close @research
mcpc clean sessions
```

Do not run `close` and `clean` for the same session in parallel.
If `close` already says `Session not found`, skip straight to targeted cleanup.
In disposable CI state such as a temporary `MCPC_HOME_DIR`, `clean all` is fine after `close`.

## What not to assume

- cleanup does not rely on a public `expiresAt` field; document status-based cleanup behavior instead
- header-based bearer tokens are not OAuth profiles, but session cleanup still removes them because they belong to the session record
- `clean all` is not a casual troubleshooting step on a machine with saved profiles

## Useful local paths

- `~/.mcpc/sessions.json`
- `~/.mcpc/profiles.json`
- `~/.mcpc/credentials.json`
- `~/.mcpc/wallets.json`
- `~/.mcpc/shell-history`
- `~/.mcpc/logs/bridge-@session.log`
