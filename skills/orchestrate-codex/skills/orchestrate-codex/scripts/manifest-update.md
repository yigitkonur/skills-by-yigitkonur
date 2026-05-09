# manifest-update.sh

Atomic manifest field setter (bash). Used by the bash runners (`run-fleet.sh`, `run-batch.sh`, etc.) for status flips and per-entry mutations. Sibling Python helper `manifest-update.py` is the same surface for non-bash callers.

## Inputs

```bash
bash manifest-update.sh entry <manifest-path> <entry-id> <key>=<value> [<key2>=<value2> ...]
bash manifest-update.sh top   <manifest-path> <key>=<value> [...]
```

| Arg | Notes |
|---|---|
| `entry` / `top` mode | First positional. `entry` updates a single entry by id; `top` updates manifest top-level fields |
| `<manifest-path>` | Path to manifest.json |
| `<entry-id>` (entry mode only) | Matches `entries[i].id` |
| `<key>=<value>` (repeatable) | Dotted key path under the entry (or top); e.g. `status=running`, `mode_state.post_verify_exit=0` |

Special values:
- `now` — replaced with current UTC ISO-8601 (e.g. `started_at=now`)
- `null` — sets the field to JSON null
- `+1` — increments the existing integer value (e.g. `attempts=+1`)

## Outputs

- Manifest file updated atomically.
- Per-entry status changes auto-append a row to `manifest.history[]`:

```json
{
  "ts": "2026-05-08T18:30:11Z",
  "entry_id": "01-foo",
  "from": "queued",
  "to": "running",
  "actor": "manifest-update.sh",
  "reason": null
}
```

stdout: empty on success (silent). Use `--verbose` to print the resolved JSON-pointer-style path of every set.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Update applied |
| 1 | Manifest missing or unreadable |
| 2 | Bad CLI args |
| 3 | `flock` timeout (couldn't acquire `<manifest>.lock` within 30 s) |
| 4 | `jq` not installed (required dependency) |

## Behavior

- Acquires `flock(LOCK_EX)` on `<manifest>.lock` (advisory on POSIX).
- Reads manifest via `jq`.
- Applies all `key=value` updates.
- Writes to `<manifest>.json.tmp.<pid>` in the same directory; `mv -f` to canonical path.
- Releases lock; lock file remains (intentional — saves an `unlink` race on next acquire).

## Concurrency

50 concurrent invocations against the same manifest serialize cleanly. Cross-tested with sibling `manifest-update.py` (mixed bash + python writers); both honor the same lock contract.

## Notes

The bash variant defaults to `--execute` (silent atomic write). The Python variant defaults to dry-run (per the spec's "mutators must default to dry-run" rule for user-facing scripts). Bash callers are runner-internal; the silent write is correct.

`jq` is a hard dependency. Pre-flight (`bootstrap.sh`) detects jq and fails the run if missing.
