# manifest-update.{sh,py}

Atomic manifest field setter. Used by the bash runners (`run-fleet.sh`, `run-batch.sh`, etc.) for status flips and per-entry mutations. The Python sibling (`manifest-update.py`) is the same surface for non-bash callers and adds a `--execute` gate (default dry-run).

## Inputs

```bash
# Bash (silent, default execute):
bash manifest-update.sh entry <manifest-path> <entry-id> <key>=<value> [<key2>=<value2> ...] \
        [--reason "<text>"] [--actor "<name>"]
bash manifest-update.sh top   <manifest-path> <key>=<value> [...]

# Python (default dry-run; --execute writes):
python3 manifest-update.py entry --manifest <path> --entry <id> --set <key>=<value> [...] \
        [--reason "<text>"] [--actor "<name>"] [--execute] [--json]
python3 manifest-update.py top   --manifest <path> --set <key>=<value> [...]
```

| Arg | Notes |
|---|---|
| `entry` / `top` mode | First positional. `entry` updates a single entry by id; `top` updates manifest top-level fields |
| `<manifest-path>` | Path to manifest.json |
| `<entry-id>` (entry mode only) | Matches `entries[i].id` |
| `<key>=<value>` (repeatable) | Dotted key path under the entry (or top); e.g. `status=running`, `mode_state.codex_pid=12345`. Intermediate dicts are auto-created via jq's `setpath`/python's nested-write helper |
| `--reason "<text>"` | Optional. Recorded on history rows for status changes |
| `--actor "<name>"` | Optional. Override the actor recorded on history rows. Default: script basename (`manifest-update.sh` or `manifest-update.py`) |

Special values:
- `now` — replaced with current UTC ISO-8601 (e.g. `started_at=now`)
- `null` — sets the field to JSON null
- `+1` / `+N` — increments the existing integer value (e.g. `attempts=+1`)
- `@file:<path>` (python only) — substitute file contents (rare; for long error strings)

Numeric coercion (allowlist applied to the leaf segment of dotted keys): `exit_code`, `attempts`, `schema_version`, `concurrency_cap`, `round`, `codex_pid`, `post_verify_exit`, `answer_size_bytes`, `major_count`, `minor_count`. Numeric-shaped values for these keys parse to JSON numbers; everything else stays a string.

Boolean coercion (allowlist applied to the leaf segment of dotted keys): `below_floor`, `dry_run`, `bypass`, `cleaned_up`, `reuse_worktree`. When the raw value is exactly `true` or `false`, it is written as a JSON boolean. The Python sibling coerces every literal `true`/`false`; the bash sibling restricts coercion to this allowlist so that user-supplied free-form strings stay strings. Both writers agree on the boolean output for the listed keys — downstream consumers can safely compare with `=== true` / `=== false`.

## Outputs

- Manifest file updated atomically (lock + atomic-rename).
- Per-entry **top-level** status changes auto-append a row to `manifest.history[]`:

```json
{
  "ts": "2026-05-08T18:30:11Z",
  "entry_id": "01-foo",
  "from": "queued",
  "to": "running",
  "actor": "manifest-update.sh",
  "reason": "rescue redispatch"
}
```

Bash variant: silent on success. Python variant: prints a human summary unless `--json` (then a machine-readable status block).

Note: only top-level `status=` triggers a history row; nested writes like `mode_state.status=` do not.

## Exit codes (canonical — bash and python agree)

| Code | Meaning |
|---|---|
| 0 | Update applied (or python dry-run preview rendered cleanly) |
| 1 | Python dry-run with mutations to apply (caller may want `--execute`). Bash never returns 1. |
| 2 | Usage error / bad input / manifest missing or malformed / entry id not found |
| 3 | Environmental error (lock acquire timeout, write failure, permission denied) |
| 4 | Hard failure (resulting manifest would be invalid JSON) |
| 5 | Missing required dependency (bash sibling only — `jq` not on PATH) |

## Behavior

- Acquires `flock(LOCK_EX)` on `<manifest>.lock` (advisory on POSIX).
- Reads manifest, applies all `key=value` updates (dotted keys land at nested paths).
- Writes to `<manifest>.json.tmp.<rand>` in the same directory; `mv -f` / `os.replace` to the canonical path (atomic on the same filesystem).
- Releases lock; lock file remains (intentional — saves an `unlink` race on next acquire). Tidy removes it.
- For top-level status changes only, appends a `{ts, entry_id, from, to, actor, reason}` row to `history[]`.

## Concurrency

50 concurrent invocations against the same manifest serialize cleanly. Cross-tested with mixed bash + python writers: every nested key lands at its correct nested path; no interleaved writes lose data.

## Notes

The bash variant defaults to `--execute` (silent atomic write). The Python variant defaults to dry-run (per the spec's "mutators must default to dry-run" rule for user-facing scripts). Bash callers are runner-internal; the silent write is correct.

`jq` is a hard dependency for the bash variant. Pre-flight (`bootstrap.sh`) detects jq and fails the run if missing.
