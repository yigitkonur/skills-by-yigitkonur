#!/usr/bin/env python3
"""Remove orchestrate-codex worktrees; refuse unmerged/dirty unless --force-abandon.

Reads the orchestrate-codex manifest, walks each entry, decides per entry
whether to remove its worktree. An entry is safe to remove only if its branch
(if any) is fully merged into <base> AND the worktree is clean. Otherwise
the script refuses unless explicitly told to abandon that entry via
--force-abandon <entry-id>.

Default is dry-run.

Usage:
    cleanup-worktrees.py --manifest <path>
    cleanup-worktrees.py --manifest <path> --base main --execute
    cleanup-worktrees.py --manifest <path> --execute --force-abandon 01-foo 02-bar

Exit codes:
    0  all worktrees handled (removed or already-cleaned)
    1  dry-run with actionable removals
    2  some refused — caller must add --force-abandon for them, or bad input
    3  worktree-remove failed (e.g. dirty tree refused removal)
    4  resulting manifest write failed
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def sh(cmd: list[str], cwd: Path | None = None, timeout: int | None = 30) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           check=False, timeout=timeout)
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "command timed out"


def repo_root(start: Path) -> Path | None:
    rc, out, _ = sh(["git", "rev-parse", "--show-toplevel"], cwd=start)
    return Path(out) if rc == 0 else None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def branch_is_merged(base: str, branch: str, root: Path) -> bool:
    rc, out, _ = sh(
        ["git", "branch", "--merged", base, "--format=%(refname:short)"], cwd=root
    )
    if rc != 0:
        return False
    merged = {b.strip() for b in out.splitlines() if b.strip()}
    return branch in merged


def worktree_present(path: str) -> bool:
    return bool(path) and os.path.isdir(path)


def worktree_dirty(path: str) -> bool:
    rc, out, _ = sh(["git", "status", "--porcelain=1"], cwd=Path(path))
    return rc != 0 or bool(out.strip())


def detect_worktree_branch(path: str) -> str | None:
    """Return the branch a worktree is checked out on, or None."""
    rc, out, _ = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=Path(path))
    if rc == 0 and out.strip() and out.strip() != "HEAD":
        return out.strip()
    return None


def atomic_write(path: Path, content: str) -> None:
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(parent), prefix=".manifest.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp, str(path))
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


@contextlib.contextmanager
def manifest_lock(manifest_path: Path, timeout: int = 30):
    lock_path = manifest_path.with_name(manifest_path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fp = open(lock_path, "w")
    try:
        deadline = time.monotonic() + timeout
        delay = 0.05
        while True:
            try:
                fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if exc.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                    raise
                if time.monotonic() >= deadline:
                    raise SystemExit(
                        f"cleanup-worktrees: failed to acquire lock {lock_path} within {timeout}s"
                    )
                time.sleep(delay)
                if delay < 0.5:
                    delay = min(delay * 1.5, 0.5)
        yield
    finally:
        try:
            fcntl.flock(fp, fcntl.LOCK_UN)
        finally:
            fp.close()


def load_manifest(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        with path.open() as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True, help="Path to orchestrate-codex manifest.json")
    ap.add_argument("--base", default="main",
                    help="Base branch to check merged-status against. Default: main.")
    ap.add_argument("--execute", action="store_true",
                    help="Actually remove worktrees. Default: dry-run.")
    ap.add_argument("--force-abandon", nargs="*", default=[],
                    metavar="ENTRY_ID",
                    help="Entry ids whose worktrees should be removed even if not merged or dirty.")
    ap.add_argument("--workspace-root", default=None,
                    help="Workspace root for git operations. Default: cwd.")
    ap.add_argument("--json", action="store_true",
                    help="Emit JSON action plan/result instead of human text.")
    args = ap.parse_args()

    workspace_root = Path(args.workspace_root).resolve() if args.workspace_root else Path.cwd().resolve()
    root = repo_root(workspace_root)
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    if manifest is None:
        msg = f"manifest absent or unreadable: {manifest_path}"
        if args.json:
            print(json.dumps({
                "ok": True,
                "manifest_present": False,
                "actions": [],
                "summary": "no manifest; nothing to clean",
            }, indent=2))
        else:
            print(msg)
            print("(nothing to clean — exit 0)")
        return 0

    entries = manifest.get("entries")
    if not isinstance(entries, list):
        if args.json:
            print(json.dumps({
                "ok": False,
                "error": "manifest has no entries[] array",
            }, indent=2))
        else:
            print(f"manifest at {manifest_path} has no 'entries' array; nothing to do")
        return 2

    if not entries:
        if args.json:
            print(json.dumps({
                "ok": True,
                "actions": [],
                "summary": "manifest has 0 entries",
            }, indent=2))
        else:
            print("manifest has no entries; nothing to do")
        return 0

    if not args.json:
        print(f"manifest:        {manifest_path}")
        print(f"base branch:     {args.base}")
        print(f"force-abandon:   {args.force_abandon if args.force_abandon else '(none)'}")
        print(f"mode:            {'EXECUTE' if args.execute else 'DRY-RUN'}")
        print()

    actions: list[dict] = []
    refused = 0
    failed = 0

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id") or entry.get("slug") or "<unknown>"
        wt = entry.get("worktree_path") or ""
        force = entry_id in args.force_abandon
        # Allow force by slug as a convenience
        if not force:
            force = entry.get("slug") in args.force_abandon

        # Already cleaned up
        if entry.get("cleaned_up"):
            actions.append({
                "entry_id": entry_id, "action": "noop",
                "message": "already cleaned up; skipping",
            })
            continue

        # No worktree path or path missing on disk
        if not worktree_present(wt):
            actions.append({
                "entry_id": entry_id, "action": "noop",
                "message": f"worktree not present at {wt!r}; marking cleaned",
                "worktree_path": wt,
            })
            entry["cleaned_up"] = True
            entry["updated_at"] = utc_now_iso()
            continue

        branch = detect_worktree_branch(wt)
        merged = branch_is_merged(args.base, branch, root) if branch else False
        dirty = worktree_dirty(wt) if wt else False

        # Refuse if branch not merged into base, unless force or no branch (detached)
        if branch and not merged and not force:
            refused += 1
            actions.append({
                "entry_id": entry_id, "action": "refuse",
                "message": (
                    f"branch {branch!r} not merged into {args.base}; "
                    f"pass --force-abandon {entry_id} to remove anyway"
                ),
                "worktree_path": wt, "branch": branch,
            })
            continue

        if dirty and not force:
            refused += 1
            actions.append({
                "entry_id": entry_id, "action": "refuse",
                "message": f"worktree {wt!r} is dirty; pass --force-abandon {entry_id} to discard",
                "worktree_path": wt,
            })
            continue

        if not args.execute:
            kind = "force-remove" if force else "remove"
            actions.append({
                "entry_id": entry_id, "action": "plan",
                "message": f"would {kind} worktree at {wt}",
                "worktree_path": wt,
            })
            continue

        # Execute
        cmd = ["git", "worktree", "remove"]
        if force or dirty:
            cmd.append("--force")
        cmd.append(wt)
        rc, _, err = sh(cmd, cwd=root)
        if rc != 0:
            failed += 1
            actions.append({
                "entry_id": entry_id, "action": "failed",
                "message": f"git worktree remove failed: {err}",
                "worktree_path": wt,
            })
            continue

        entry["cleaned_up"] = True
        entry["updated_at"] = utc_now_iso()
        actions.append({
            "entry_id": entry_id, "action": "removed",
            "message": f"worktree removed at {wt}" + (" (forced)" if force else ""),
            "worktree_path": wt,
        })

    # Persist manifest changes (only on actual mutations)
    write_failed = False
    if args.execute and any(a["action"] in ("removed", "noop") for a in actions):
        try:
            with manifest_lock(manifest_path):
                # Re-read under lock and merge our cleaned_up flags onto fresh data
                fresh = load_manifest(manifest_path)
                if fresh is not None and isinstance(fresh.get("entries"), list):
                    cleaned_ids = {
                        a["entry_id"] for a in actions
                        if a["action"] in ("removed", "noop")
                    }
                    for fe in fresh["entries"]:
                        if isinstance(fe, dict) and fe.get("id") in cleaned_ids:
                            fe["cleaned_up"] = True
                            fe["updated_at"] = utc_now_iso()
                    atomic_write(manifest_path, json.dumps(fresh, indent=2) + "\n")
                else:
                    atomic_write(manifest_path, json.dumps(manifest, indent=2) + "\n")
        except (OSError, SystemExit) as exc:
            print(f"cleanup-worktrees: manifest write failed: {exc}", file=sys.stderr)
            write_failed = True

    # Output
    if args.json:
        out = {
            "ok": failed == 0 and not write_failed,
            "executed": args.execute,
            "manifest_path": str(manifest_path),
            "actions": actions,
            "summary": {
                "total": len(actions),
                "removed": sum(1 for a in actions if a["action"] == "removed"),
                "planned": sum(1 for a in actions if a["action"] == "plan"),
                "refused": refused,
                "failed": failed,
                "noop": sum(1 for a in actions if a["action"] == "noop"),
            },
        }
        print(json.dumps(out, indent=2, default=str))
    else:
        for a in actions:
            marker = {
                "removed":  "[DO]",
                "plan":     "[DRY]",
                "refuse":   "[REFUSE]",
                "failed":   "[FAIL]",
                "noop":     "[NOOP]",
            }.get(a["action"], "[?]")
            print(f"  {marker} {a['entry_id']}: {a['message']}")
        print()
        if args.execute and any(a["action"] in ("removed", "noop") for a in actions):
            if write_failed:
                print("✗ manifest write failed; some changes may be unpersisted")
            else:
                print(f"✓ manifest updated: {manifest_path}")
        print()

    if write_failed:
        return 4
    if refused > 0:
        if not args.json:
            print(f"✗ {refused} entry/entries refused — re-run with --force-abandon for those")
        return 2
    if failed > 0:
        if not args.json:
            print(f"✗ {failed} removal(s) failed — see stderr above")
        return 3
    if not args.execute and any(a["action"] == "plan" for a in actions):
        if not args.json:
            print("DRY-RUN complete. Re-run with --execute to apply.")
        return 1
    if not args.json:
        print("✓ cleanup complete. Tidy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
