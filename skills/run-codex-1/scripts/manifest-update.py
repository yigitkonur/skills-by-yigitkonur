#!/usr/bin/env python3
"""Atomic field-update helper for run-codex-1 manifest.json.

Mutates manifest entries (or top-level fields) under fcntl.flock(LOCK_EX) on
<manifest>.lock and a tempfile-then-os.replace cycle so concurrent writers
serialize cleanly. 50 simultaneous invocations against the same manifest
produce a manifest that parses and reflects every update.

Two modes (positional first arg):

    manifest-update.py entry --manifest <path> --entry <id> --set k=v ...
    manifest-update.py top   --manifest <path> --set k=v ...

Special values for k=v pairs:
    now    → current UTC ISO timestamp (e.g. status=running started_at=now)
    null   → JSON null (e.g. exit_code=null)
    +1     → numeric increment of an integer counter (key += 1, default 0)
    +N     → numeric increment by N (e.g. attempts=+1)
    @file:<path> → read raw text from <path> (rare; for long error strings)

Numeric-coercible keys (exit_code, attempts, schema_version, concurrency_cap,
round) parse into JSON numbers automatically when value matches an integer
or float literal; everything else stays a JSON string.

When `status=<v>` appears in an entry update, the script also appends a
{ts, entry_id, from, to} row to the manifest's history[].

Default mode is **dry-run** — the script prints the resulting manifest to
stdout and does NOT touch disk. Pass --execute to write it.

Exit codes (canonical table — bash sibling agrees):
    0  OK (executed) or DRY-RUN preview rendered cleanly
    1  Dry-run with mutations to apply (caller may want to run --execute)
       [python only — bash has no dry-run]
    2  Usage error / bad input / manifest missing or malformed / entry not found
    3  Environmental error (lock acquisition timeout, permission denied, write fail)
    4  Hard failure (resulting manifest would be invalid JSON)
    5  Missing required dependency (bash sibling only — jq)
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import fcntl
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NUMERIC_KEYS = {
    "exit_code", "attempts", "schema_version", "concurrency_cap", "round",
    # codex-side numeric fields
    "codex_pid", "post_verify_exit", "answer_size_bytes",
    "major_count", "minor_count",
}
LOCK_TIMEOUT_SECONDS = 30


def split_dotted_key(key: str) -> list[str]:
    """Split a dotted key path into segments.

    Treats `.` as the path separator. Empty segments (e.g. `..` or trailing
    `.`) are rejected by the caller. Backslash escaping is not supported —
    manifest keys do not contain literal `.` characters.
    """
    return key.split(".")


def assign_nested(target: dict, dotted_key: str, value: Any) -> None:
    """Assign `value` at the nested path `dotted_key` inside `target`.

    Creates intermediate dicts as needed. Refuses to overwrite a non-dict
    value with a dict (would silently nuke prior data).

    Examples:
        assign_nested({}, "mode_state.codex_pid", 12345)
            # {"mode_state": {"codex_pid": 12345}}
        assign_nested({"a": {"b": 1}}, "a.c", 2)
            # {"a": {"b": 1, "c": 2}}
    """
    parts = split_dotted_key(dotted_key)
    if not parts or any(p == "" for p in parts):
        raise SystemExit(f"manifest-update: bad dotted key (empty segment): {dotted_key!r}")
    cur = target
    for seg in parts[:-1]:
        nxt = cur.get(seg)
        if not isinstance(nxt, dict):
            if nxt is None:
                cur[seg] = {}
                cur = cur[seg]
            else:
                raise SystemExit(
                    f"manifest-update: cannot nest under non-dict at {seg!r} "
                    f"(in path {dotted_key!r}); existing value type "
                    f"{type(nxt).__name__}"
                )
        else:
            cur = nxt
    cur[parts[-1]] = value


def read_nested(target: dict, dotted_key: str, default: Any = None) -> Any:
    """Read a nested value or return default. Used for increment baseline."""
    parts = split_dotted_key(dotted_key)
    cur: Any = target
    for seg in parts:
        if not isinstance(cur, dict) or seg not in cur:
            return default
        cur = cur[seg]
    return cur


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def coerce_value(key: str, raw: str) -> tuple[str, Any]:
    """Map raw value string to (kind, parsed). kind is 'literal' (use directly),
    'increment' (k += N), or 'file' (raw_text). Numeric coercion follows the
    NUMERIC_KEYS allowlist."""
    if raw == "now":
        return "literal", utc_now_iso()
    if raw == "null":
        return "literal", None
    if raw.startswith("+"):
        try:
            return "increment", int(raw[1:])
        except ValueError:
            # Fall through and treat as a literal string starting with '+'
            pass
    if raw.startswith("@file:"):
        path = raw[len("@file:"):]
        try:
            return "literal", Path(path).read_text()
        except OSError as exc:
            raise SystemExit(f"manifest-update: cannot read @file: {path}: {exc}")

    # For dotted paths the leaf segment determines numeric coercion (e.g.
    # `mode_state.exit_code` should coerce because the leaf key is exit_code).
    leaf = key.rsplit(".", 1)[-1]
    if leaf in NUMERIC_KEYS:
        try:
            if re.fullmatch(r"-?\d+", raw):
                return "literal", int(raw)
            if re.fullmatch(r"-?\d+\.\d+", raw):
                return "literal", float(raw)
        except ValueError:
            pass
    # Booleans for fields like `bypass`
    if raw == "true":
        return "literal", True
    if raw == "false":
        return "literal", False
    return "literal", raw


def parse_set_pairs(pairs: list[str]) -> list[tuple[str, str, Any]]:
    out = []
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"manifest-update: bad --set pair (no '='): {pair!r}")
        key, raw = pair.split("=", 1)
        if not key:
            raise SystemExit(f"manifest-update: empty key in --set pair: {pair!r}")
        kind, value = coerce_value(key, raw)
        out.append((key, kind, value))
    return out


def apply_assignments_to_dict(target: dict, assignments: list[tuple[str, str, Any]]) -> None:
    """Mutate `target` in-place by assigning each (key, kind, value).

    kind in {'literal', 'increment'}. Keys are dotted paths (e.g.
    'mode_state.codex_pid'); intermediate dicts are auto-created. Increment
    requires the existing value (default 0) be numeric-coercible.
    """
    for key, kind, value in assignments:
        if kind == "increment":
            cur = read_nested(target, key, 0)
            try:
                cur_num = int(cur) if cur is not None else 0
            except (TypeError, ValueError):
                cur_num = 0
            assign_nested(target, key, cur_num + value)
        else:
            assign_nested(target, key, value)


def find_status_change(assignments: list[tuple[str, str, Any]]) -> Any:
    """Return the new top-level `status` value from assignments, if present.

    Only top-level `status=` (not nested like `mode_state.status=`) triggers
    a history-row append.
    """
    for key, _kind, value in assignments:
        if key == "status":
            return value
    return None


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"manifest-update: manifest not found: {path}")
    try:
        with path.open() as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"manifest-update: malformed JSON in {path}: {exc}")
    except OSError as exc:
        raise SystemExit(f"manifest-update: cannot read {path}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"manifest-update: manifest root must be an object in {path}")
    return data


def atomic_write_json(path: Path, data: dict) -> None:
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(parent), prefix=".manifest.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=False)
            f.write("\n")
        os.replace(tmp, str(path))
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


class LockTimeout(RuntimeError):
    """Raised when manifest lock cannot be acquired within the configured timeout.

    KB-001 fix: previously raised SystemExit, which produced exit code 1.
    Now raised as a typed exception and mapped to exit code 3 (environmental)
    in main(), matching the bash sibling's behavior and the documented contract.
    """


@contextlib.contextmanager
def manifest_lock(manifest_path: Path, timeout_seconds: int = LOCK_TIMEOUT_SECONDS):
    """Hold fcntl.LOCK_EX on <manifest>.lock for the duration of the block.

    Polls with non-blocking attempts at 0.05s intervals up to `timeout_seconds`,
    so concurrent writers serialize without indefinitely blocking.
    """
    lock_path = manifest_path.with_name(manifest_path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fp = open(lock_path, "w")
    try:
        deadline = _monotonic_deadline(timeout_seconds)
        delay = 0.05
        while True:
            try:
                fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if exc.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                    raise
                if _monotonic_now() >= deadline:
                    raise LockTimeout(
                        f"manifest-update: failed to acquire lock {lock_path} within {timeout_seconds}s"
                    )
                _sleep(delay)
                if delay < 0.5:
                    delay = min(delay * 1.5, 0.5)
        yield
    finally:
        try:
            fcntl.flock(fp, fcntl.LOCK_UN)
        finally:
            fp.close()


def _monotonic_now() -> float:
    import time
    return time.monotonic()


def _monotonic_deadline(seconds: int) -> float:
    return _monotonic_now() + seconds


def _sleep(seconds: float) -> None:
    import time
    time.sleep(seconds)


def update_entry(
    manifest: dict,
    entry_id: str,
    assignments: list[tuple[str, str, Any]],
) -> tuple[bool, Any, Any]:
    """Mutate the matching entry. Returns (changed, old_status, new_status).
    Raises SystemExit if the entry id is not found.
    """
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise SystemExit(
            f"manifest-update: manifest has no 'entries' array (got {type(entries).__name__})"
        )
    target = None
    for entry in entries:
        if isinstance(entry, dict) and entry.get("id") == entry_id:
            target = entry
            break
    if target is None:
        raise SystemExit(f"manifest-update: entry id not found: {entry_id!r}")

    old_status = target.get("status")
    apply_assignments_to_dict(target, assignments)
    new_status = target.get("status")
    return True, old_status, new_status


def append_history_row(
    manifest: dict,
    entry_id: str,
    old_status: Any,
    new_status: Any,
    actor: str | None = None,
    reason: str | None = None,
) -> None:
    """Append one row to manifest.history.

    `actor` defaults to the script basename (`manifest-update.py`).
    `reason` is `None` unless the caller supplies `--reason`.
    Both fields are documented in `references/universal/manifest-contract.md:184-191`.
    """
    if "history" not in manifest or not isinstance(manifest["history"], list):
        manifest["history"] = []
    if actor is None:
        actor = os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else "manifest-update.py"
    manifest["history"].append({
        "ts": utc_now_iso(),
        "entry_id": entry_id,
        "from": old_status,
        "to": new_status,
        "actor": actor,
        "reason": reason,
    })


def update_top(manifest: dict, assignments: list[tuple[str, str, Any]]) -> None:
    apply_assignments_to_dict(manifest, assignments)


def render_summary(
    mode: str,
    entry_id: str | None,
    assignments: list[tuple[str, str, Any]],
    old_status: Any,
    new_status: Any,
) -> str:
    lines = []
    lines.append(f"mode: {mode}")
    if entry_id is not None:
        lines.append(f"entry_id: {entry_id}")
        if old_status != new_status:
            lines.append(f"status: {old_status} → {new_status}")
    for key, kind, value in assignments:
        if kind == "increment":
            lines.append(f"  {key} += {value}")
        else:
            display = json.dumps(value, default=str)
            if len(display) > 80:
                display = display[:77] + "..."
            lines.append(f"  {key} = {display}")
    return "\n".join(lines)


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "mode",
        choices=("entry", "top"),
        help="entry: update a single entries[?id==<id>]; top: update top-level fields",
    )
    parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    parser.add_argument("--entry", help="Entry id (required for mode=entry)")
    parser.add_argument(
        "--set",
        action="append",
        dest="set_pairs",
        default=[],
        metavar="KEY=VALUE",
        help="key=value assignment (repeatable). Special: now, null, +N, @file:<path>",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually write the manifest. Default: dry-run (prints preview).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON status block on stdout instead of human summary.",
    )
    parser.add_argument(
        "--lock-timeout",
        type=int,
        default=LOCK_TIMEOUT_SECONDS,
        help=f"Max seconds to wait for the manifest lock. Default {LOCK_TIMEOUT_SECONDS}.",
    )
    parser.add_argument(
        "--actor",
        default=None,
        help="Override the actor recorded on history rows. Default: script basename.",
    )
    parser.add_argument(
        "--reason",
        default=None,
        help="Optional free-form reason recorded on history rows for this update.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argparser()
    args = parser.parse_args(argv)

    if args.mode == "entry" and not args.entry:
        parser.error("mode=entry requires --entry <id>")
    if not args.set_pairs:
        parser.error("at least one --set KEY=VALUE pair required")

    manifest_path = Path(args.manifest).resolve()
    try:
        assignments = parse_set_pairs(args.set_pairs)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 2

    # Pre-validate: read the manifest once before locking, to catch
    # malformed manifests early (and to fail fast in dry-run).
    if not manifest_path.is_file():
        print(f"manifest-update: manifest not found: {manifest_path}", file=sys.stderr)
        return 2
    try:
        manifest = load_manifest(manifest_path)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not args.execute:
        # Dry-run: simulate the update against the snapshot we just read.
        try:
            if args.mode == "entry":
                _changed, old_status, new_status = update_entry(
                    manifest, args.entry, assignments
                )
                if old_status != new_status:
                    append_history_row(
                        manifest, args.entry, old_status, new_status,
                        actor=args.actor, reason=args.reason,
                    )
            else:
                update_top(manifest, assignments)
                old_status = new_status = None
        except SystemExit as exc:
            print(str(exc), file=sys.stderr)
            return 2

        if args.json:
            print(json.dumps({
                "ok": True,
                "dry_run": True,
                "mode": args.mode,
                "entry_id": args.entry,
                "preview_manifest": manifest,
                "would_write": str(manifest_path),
            }, indent=2, default=str))
        else:
            print(render_summary(args.mode, args.entry, assignments, old_status, new_status))
            print()
            print("DRY-RUN: pass --execute to write.")
        return 1

    # --execute: lock, re-read, mutate, atomic write
    try:
        with manifest_lock(manifest_path, args.lock_timeout):
            try:
                manifest = load_manifest(manifest_path)
            except SystemExit as exc:
                print(str(exc), file=sys.stderr)
                return 2
            try:
                if args.mode == "entry":
                    _changed, old_status, new_status = update_entry(
                        manifest, args.entry, assignments
                    )
                    if old_status != new_status:
                        append_history_row(
                            manifest, args.entry, old_status, new_status,
                            actor=args.actor, reason=args.reason,
                        )
                else:
                    update_top(manifest, assignments)
                    old_status = new_status = None
            except SystemExit as exc:
                print(str(exc), file=sys.stderr)
                return 2

            # Sanity-check JSON serialization before commit.
            try:
                json.dumps(manifest)
            except (TypeError, ValueError) as exc:
                print(f"manifest-update: resulting manifest would be invalid JSON: {exc}",
                      file=sys.stderr)
                return 4

            try:
                atomic_write_json(manifest_path, manifest)
            except OSError as exc:
                print(f"manifest-update: failed to write {manifest_path}: {exc}",
                      file=sys.stderr)
                return 3
    except LockTimeout as exc:
        # KB-001 fix: lock-timeout now exits 3 with error.code="lock_timeout"
        # (was: uncaught SystemExit → exit 1). Matches bash sibling and the
        # documented contract.
        if args.json:
            print(json.dumps({
                "ok": False,
                "executed": False,
                "mode": args.mode,
                "entry_id": args.entry,
                "error": {"code": "lock_timeout", "message": str(exc)},
            }, indent=2, default=str))
        else:
            print(str(exc), file=sys.stderr)
        return 3
    except PermissionError as exc:
        print(f"manifest-update: permission denied: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps({
            "ok": True,
            "executed": True,
            "mode": args.mode,
            "entry_id": args.entry,
            "manifest_path": str(manifest_path),
        }, indent=2, default=str))
    else:
        print(render_summary(args.mode, args.entry, assignments, old_status, new_status))
        print()
        print(f"OK: manifest updated → {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
