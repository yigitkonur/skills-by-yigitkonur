"""Shared Python helpers for run-codex-1.

Single source of truth for:
  - Constants (loaded from constants.json)
  - Manifest read/write (atomic via tempfile + os.replace; flock-protected)
  - State directory resolution (matches codex-companion's slug+hash algorithm)
  - JSON envelope construction (uniform across dispatcher/audit/rescue/cleanup)
  - Run-ledger logging (replaces `2>/dev/null || true` resilience pattern)
  - Status enum constants

Consumers:
  - manifest-update.py (canonical manifest writer)
  - audit.py / rescue-detect.py / cleanup-worktrees.py / classify-review-feedback.py
  - run-codex-1.mjs (indirectly, via shelling out to these helpers)

Design notes:
  - No imports from project-local modules beyond stdlib (and `re`, `hashlib`,
    `tempfile`, `fcntl`, `json`, `time`, `os`, `sys`, `errno`, `pathlib`).
  - All atomic-write recipes assume same-filesystem rename (mktemp in
    manifest parent dir; os.replace).
  - Lock files are NEVER unlinked by writers; only by cleanup-worktrees.py
    during full manifest-delete.
"""

from __future__ import annotations

import dataclasses
import errno
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterator, List, Optional, Tuple, Union


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CONSTANTS_PATH = Path(__file__).resolve().parent / "constants.json"


class Constants:
    """Loaded once at module import; immutable thereafter.

    Access patterns:
      Constants.lock_timeout_seconds      # int
      Constants.concurrency_defaults      # dict {mode -> int}
      Constants.concurrency_soft_cap      # int
      Constants.concurrency_hard_cap      # int
      Constants.schema_version            # int
      Constants.exit("environmental")     # int from exit_codes map
      Constants.raw()                     # full dict (for debugging)
    """

    _data: Dict[str, Any]

    def __init__(self, path: Path = _CONSTANTS_PATH):
        try:
            self._data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as e:
            raise RuntimeError(
                f"constants.json missing at {path}; refusing to proceed"
            ) from e

    @property
    def schema_version(self) -> int:
        return int(self._data["schema_version"])

    @property
    def lock_timeout_seconds(self) -> int:
        return int(self._data["lock_timeout_seconds"])

    @property
    def monitor_hard_max_ms(self) -> int:
        return int(self._data["monitor_hard_max_ms"])

    @property
    def rescue_freshness_days(self) -> int:
        return int(self._data["rescue_freshness_days"])

    @property
    def concurrency_defaults(self) -> Dict[str, int]:
        return dict(self._data["concurrency"]["defaults"])

    @property
    def concurrency_soft_cap(self) -> int:
        return int(self._data["concurrency"]["soft_cap"])

    @property
    def concurrency_hard_cap(self) -> int:
        return int(self._data["concurrency"]["hard_cap"])

    @property
    def audit_min_bytes_default(self) -> int:
        return int(self._data["audit"]["min_bytes_default"])

    @property
    def audit_stale_minutes_default(self) -> int:
        return int(self._data["audit"]["stale_minutes_default"])

    @property
    def codex_model_default(self) -> str:
        return str(self._data["codex"]["model_default"])

    @property
    def codex_effort_default(self) -> str:
        return str(self._data["codex"]["effort_default"])

    @property
    def review_round_soft_cap(self) -> int:
        return int(self._data["review"]["round_soft_cap"])

    @property
    def review_wall_clock_sec_per_round(self) -> int:
        return int(self._data["review"]["wall_clock_sec_per_round"])

    def exit(self, name: str) -> int:
        return int(self._data["exit_codes"][name])

    def raw(self) -> Dict[str, Any]:
        return dict(self._data)


# Module-singleton
CONSTANTS = Constants()


# ---------------------------------------------------------------------------
# Status enum
# ---------------------------------------------------------------------------

STATUS_TERMINAL: FrozenSet[str] = frozenset(
    {"done", "failed", "skipped", "converged", "blocked", "cap_reached"}
)
STATUS_NON_TERMINAL: FrozenSet[str] = frozenset({"queued", "running"})
STATUS_VALID: FrozenSet[str] = STATUS_TERMINAL | STATUS_NON_TERMINAL


# ---------------------------------------------------------------------------
# Slug + state-dir resolution (cross-language; verified against
# __fixtures__/golden/slug-derivation.json and state-dir-resolution.json)
# ---------------------------------------------------------------------------

_SLUG_REPLACE_RE = re.compile(r"[^a-z0-9._-]+")
_SLUG_COLLAPSE_RE = re.compile(r"-{2,}")


def sanitize_slug(basename: str) -> str:
    """Lowercase basename; replace any character not in [a-z0-9._-] with '-';
    collapse runs of '-'; trim leading/trailing '-'."""
    lowered = basename.lower()
    replaced = _SLUG_REPLACE_RE.sub("-", lowered)
    collapsed = _SLUG_COLLAPSE_RE.sub("-", replaced)
    return collapsed.strip("-")


def workspace_slug_hash(cwd: Union[str, Path]) -> Tuple[str, str]:
    """Compute (slug, 16-hex hash) for the given cwd, matching codex-companion's
    state.mjs algorithm. realpath is honored so symlinked paths normalize."""
    real = os.path.realpath(str(cwd))
    slug = sanitize_slug(os.path.basename(real.rstrip("/")) or "root")
    sha = hashlib.sha256(real.encode("utf-8")).hexdigest()[:16]
    return slug, sha


def resolve_state_dir(cwd: Union[str, Path]) -> Path:
    """Return the absolute state directory for a workspace cwd.

    Resolution:
      1. If CLAUDE_PLUGIN_DATA is set (non-empty), base = $CLAUDE_PLUGIN_DATA/state
      2. Else, base = ${TMPDIR:-/tmp}/codex-companion
      3. Append /<slug>-<hash>
    """
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA", "").strip()
    if plugin_data:
        base = Path(plugin_data) / "state"
    else:
        base = Path(os.environ.get("TMPDIR") or "/tmp") / "codex-companion"
    slug, h = workspace_slug_hash(cwd)
    return base / f"{slug}-{h}"


# ---------------------------------------------------------------------------
# JSON envelope (matches dispatcher's envelope shape)
# ---------------------------------------------------------------------------

def json_envelope(
    *,
    ok: bool,
    result: Optional[Any] = None,
    error: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
    **extra: Any,
) -> Dict[str, Any]:
    """Produce the standard envelope structure for helper output.

    Shape:
      {"ok": bool, "result": Any|null, "error": {code, message, ...}|null, "meta": {...}, ...}

    Helpers that emit JSON to stdout use this and json.dumps with sort_keys=False,
    indent=2 by convention.
    """
    env: Dict[str, Any] = {
        "ok": bool(ok),
        "result": result,
        "error": error,
        "meta": dict(meta) if meta else {"pid": os.getpid(), "ts": time.time()},
    }
    env.update(extra)
    return env


# ---------------------------------------------------------------------------
# Run ledger (structured replacement for `2>/dev/null || true`)
# ---------------------------------------------------------------------------

_LEDGER_PATH_ENV = "OC_RUN_LEDGER"


def _ledger_path() -> Optional[Path]:
    p = os.environ.get(_LEDGER_PATH_ENV, "").strip()
    return Path(p) if p else None


def log_ledger_line(level: str, msg: str, **fields: Any) -> None:
    """Write a structured event to the run ledger.

    Format: `<HH:MM:SSZ> [<LEVEL>] <source>: <msg> key=value ...`

    Levels: INFO, WARN, ERROR. Source is derived from sys.argv[0] basename.
    No-op if OC_RUN_LEDGER is unset (so helpers running outside a fleet are silent).
    """
    path = _ledger_path()
    if not path:
        return
    ts = time.strftime("%H:%M:%SZ", time.gmtime())
    source = os.path.basename(sys.argv[0]) if sys.argv else "(unknown)"
    kv_parts = []
    for k, v in fields.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            kv_parts.append(f"{k}={v}")
        else:
            kv_parts.append(f"{k}={json.dumps(v)}")
    kv = (" " + " ".join(kv_parts)) if kv_parts else ""
    line = f"{ts} [{level}] {source}: {msg}{kv}\n"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fp:
            fp.write(line)
    except OSError:
        # Ledger write failure is never fatal; we tried.
        pass


# ---------------------------------------------------------------------------
# Manifest read/write with flock + atomic replace
# ---------------------------------------------------------------------------


class LockTimeout(RuntimeError):
    """Raised when manifest lock cannot be acquired within the configured timeout."""


@dataclasses.dataclass
class Manifest:
    """Manifest container with atomic write semantics.

    Typical usage:

        with Manifest.with_lock(path, timeout=30) as m:
            m.set("entries[0].status", "running")
            m.set("entries[0].attempts", "+1")
            m.append_history(actor="run-fleet.sh", reason="started",
                             from_status="queued", to_status="running")
        # __exit__ writes the manifest atomically and releases the lock
    """

    path: Path
    data: Dict[str, Any]
    _lock_fp: Any = None  # file pointer for the flock
    _dirty: bool = False

    # ------- loading -------

    @classmethod
    def load_readonly(cls, path: Union[str, Path]) -> "Manifest":
        """Load without acquiring a lock. Use for audit / rescue read paths."""
        p = Path(path)
        try:
            text = p.read_text(encoding="utf-8")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"manifest not found: {p}") from e
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"manifest corrupt: {p}: {e}") from e
        if not isinstance(data, dict):
            raise ValueError(f"manifest root must be an object: {p}")
        cls._check_schema_version(data, p)
        return cls(path=p, data=data)

    @classmethod
    def _check_schema_version(cls, data: Dict[str, Any], path: Path) -> None:
        sv = data.get("schema_version")
        if sv is None:
            return
        if int(sv) > CONSTANTS.schema_version:
            raise ValueError(
                f"schema_version {sv} > skill schema_version {CONSTANTS.schema_version}: {path}"
            )

    # ------- locked write context -------

    @classmethod
    @contextmanager
    def with_lock(
        cls,
        path: Union[str, Path],
        timeout: Optional[float] = None,
    ) -> Iterator["Manifest"]:
        """Acquire flock, load manifest, yield Manifest, write atomically on exit."""
        p = Path(path)
        timeout = float(timeout if timeout is not None else CONSTANTS.lock_timeout_seconds)
        lock_path = p.with_suffix(p.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fp = open(lock_path, "a+")
        deadline = time.time() + timeout
        delay = 0.01
        while True:
            try:
                fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (OSError, BlockingIOError):
                if time.time() >= deadline:
                    fp.close()
                    raise LockTimeout(f"could not acquire {lock_path} within {timeout}s")
                time.sleep(delay)
                delay = min(0.5, delay * 2)
        try:
            # Post-lock re-read
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                except json.JSONDecodeError as e:
                    raise ValueError(f"manifest corrupt: {p}: {e}") from e
                if not isinstance(data, dict):
                    raise ValueError(f"manifest root must be an object: {p}")
                cls._check_schema_version(data, p)
            else:
                data = {}
            m = cls(path=p, data=data, _lock_fp=fp)
            yield m
            if m._dirty:
                cls._atomic_write(p, m.data)
        finally:
            try:
                fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            fp.close()

    @staticmethod
    def _atomic_write(path: Path, data: Dict[str, Any]) -> None:
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(parent), prefix=".manifest.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # ------- mutation API -------

    def get(self, dotted_key: str, default: Any = None) -> Any:
        """Read a value by dotted key path (e.g. 'entries[0].mode_state.codex_pid')."""
        node: Any = self.data
        for segment in _parse_dotted(dotted_key):
            if isinstance(segment, int):
                if not isinstance(node, list) or segment >= len(node):
                    return default
                node = node[segment]
            else:
                if not isinstance(node, dict) or segment not in node:
                    return default
                node = node[segment]
        return node

    def set(self, dotted_key: str, value: Any) -> None:
        """Write a value at the given dotted key, creating intermediate dicts as needed.

        Special values:
          "+N" or "+1"  → integer increment (creates 0 if missing)
          "true"/"false" → bool only if leaf name is in the allowlist; else string
          numeric strings → number only if leaf name is in the numeric allowlist; else string
        """
        coerced = coerce_value(dotted_key.split(".")[-1].split("[")[0], value)
        if isinstance(value, str) and value.startswith("+") and value[1:].isdigit():
            increment = int(value[1:])
            current = self.get(dotted_key, 0)
            coerced = (int(current) if isinstance(current, (int, float)) else 0) + increment
        _set_dotted(self.data, dotted_key, coerced)
        self._dirty = True

    def append_history(
        self,
        *,
        actor: str,
        reason: Optional[str],
        from_status: Optional[str] = None,
        to_status: Optional[str] = None,
        dry_run: bool = False,
    ) -> None:
        """Append a history row. Convention: only invoked when an entry's top-level
        status changes (not on every mode_state mutation)."""
        history = self.data.setdefault("history", [])
        attempts = None
        # If a current entry is implied, capture its attempts count for the row.
        entries = self.data.get("entries", [])
        if isinstance(entries, list):
            for e in entries:
                if isinstance(e, dict) and e.get("status") == to_status:
                    attempts = e.get("attempts")
                    break
        history.append(
            {
                "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "actor": actor,
                "reason": reason,
                "from": from_status,
                "to": to_status,
                "attempts": attempts,
                "dry_run": bool(dry_run),
            }
        )
        self._dirty = True

    def mark_dirty(self) -> None:
        self._dirty = True


# ---------------------------------------------------------------------------
# Value coercion (numeric + boolean allowlists; matches bash semantics)
# ---------------------------------------------------------------------------

NUMERIC_LEAF_KEYS: FrozenSet[str] = frozenset(
    {
        "exit_code",
        "attempts",
        "schema_version",
        "concurrency_cap",
        "round",
        "codex_pid",
        "post_verify_exit",
        "answer_size_bytes",
        "major_count",
        "minor_count",
    }
)

BOOLEAN_LEAF_KEYS: FrozenSet[str] = frozenset(
    {"below_floor", "dry_run", "bypass", "cleaned_up", "reuse_worktree"}
)


def coerce_value(leaf: str, raw: Any) -> Any:
    """Coerce a raw string value to int/float/bool/str based on leaf-name allowlists.

    Matches the bash manifest-update.sh semantics so cross-language consumers don't diverge.
    """
    if not isinstance(raw, str):
        return raw
    if leaf in BOOLEAN_LEAF_KEYS:
        if raw == "true":
            return True
        if raw == "false":
            return False
    if leaf in NUMERIC_LEAF_KEYS:
        if re.fullmatch(r"-?\d+", raw):
            return int(raw)
        if re.fullmatch(r"-?\d+\.\d+", raw):
            return float(raw)
        if raw == "null":
            return None
    # off-allowlist: stay as string (matches bash semantics).
    return raw


# ---------------------------------------------------------------------------
# Dotted-key path utilities
# ---------------------------------------------------------------------------

_DOTTED_SEGMENT_RE = re.compile(r"(?P<key>[^.\[\]]+)(?:\[(?P<idx>\d+)\])?")


def _parse_dotted(dotted_key: str) -> List[Union[str, int]]:
    out: List[Union[str, int]] = []
    for match in _DOTTED_SEGMENT_RE.finditer(dotted_key):
        out.append(match.group("key"))
        if match.group("idx") is not None:
            out.append(int(match.group("idx")))
    return out


def _set_dotted(root: Dict[str, Any], dotted_key: str, value: Any) -> None:
    segments = _parse_dotted(dotted_key)
    node: Any = root
    for i, seg in enumerate(segments):
        last = i == len(segments) - 1
        next_seg = segments[i + 1] if not last else None
        if isinstance(seg, int):
            while not isinstance(node, list) or len(node) <= seg:
                if not isinstance(node, list):
                    raise TypeError(f"expected list at segment {seg!r} in {dotted_key!r}")
                node.append({} if isinstance(next_seg, str) or last else [])
            if last:
                node[seg] = value
                return
            if node[seg] is None:
                node[seg] = {} if isinstance(next_seg, str) else []
            node = node[seg]
        else:
            assert isinstance(node, dict), f"expected dict at {seg!r} in {dotted_key!r}"
            if last:
                node[seg] = value
                return
            if seg not in node or not isinstance(node[seg], (dict, list)):
                node[seg] = {} if isinstance(next_seg, str) else []
            node = node[seg]


# ---------------------------------------------------------------------------
# CLI for self-verification: `python3 _lib.py --verify-fixtures`
# ---------------------------------------------------------------------------

def _verify_fixtures() -> int:
    fixtures_dir = Path(__file__).resolve().parent / "__fixtures__" / "golden"
    fails = 0

    # 1. slug derivation
    slug_path = fixtures_dir / "slug-derivation.json"
    if slug_path.exists():
        data = json.loads(slug_path.read_text())
        for case in data.get("cases", []):
            got, _ = workspace_slug_hash(case["input_path"])
            want = case["expected_slug"]
            if got != want:
                print(
                    f"FAIL slug-derivation/{case['name']}: got {got!r} want {want!r}",
                    file=sys.stderr,
                )
                fails += 1

    # 2. coerce_value spot checks
    spot = [
        ("below_floor", "true", True),
        ("below_floor", "false", False),
        ("last_error", "true", "true"),  # off-allowlist → stays string
        ("attempts", "42", 42),
        ("codex_pid", "12345", 12345),
        ("last_error", "42", "42"),  # off-allowlist → stays string
    ]
    for leaf, raw, want in spot:
        got = coerce_value(leaf, raw)
        if got != want or type(got) is not type(want):
            print(
                f"FAIL coerce/{leaf}={raw}: got {got!r} ({type(got).__name__}) want {want!r}",
                file=sys.stderr,
            )
            fails += 1

    if fails == 0:
        print("_lib.py fixture verification: OK")
        return 0
    print(f"_lib.py fixture verification: {fails} failures", file=sys.stderr)
    return 1


def _print_slug(path: str) -> int:
    slug, h = workspace_slug_hash(path)
    print(f"{slug}-{h}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(
            "_lib.py — shared Python helpers for run-codex-1.\n"
            "Usage:\n"
            "  python3 _lib.py --verify-fixtures   self-test against golden/\n"
            "  python3 _lib.py --slug-for=<path>   print slug-hash for a path\n",
            file=sys.stderr,
        )
        sys.exit(0)
    arg = sys.argv[1]
    if arg == "--verify-fixtures":
        sys.exit(_verify_fixtures())
    if arg.startswith("--slug-for="):
        sys.exit(_print_slug(arg.split("=", 1)[1]))
    print(f"_lib.py: unknown flag {arg!r}", file=sys.stderr)
    sys.exit(2)
