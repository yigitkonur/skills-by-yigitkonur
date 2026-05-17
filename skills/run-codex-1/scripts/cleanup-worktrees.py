#!/usr/bin/env python3
"""Remove run-codex-1 worktrees; refuse unmerged/dirty unless --force-abandon.

Reads the run-codex-1 manifest, walks each entry, decides per entry
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


def worktree_dirty(path: str) -> tuple[bool, str | None]:
    """Returns (is_dirty, git_error_message_or_None).

    Distinguishes:
      - clean tree            → (False, None)
      - dirty (status output) → (True, None)
      - git command failed    → (False, "<stderr>")  — caller surfaces error,
                                  does NOT silently treat as dirty.
    """
    rc, out, err = sh(["git", "status", "--porcelain=1"], cwd=Path(path))
    if rc != 0:
        return False, (err.strip() or f"git status exit {rc}")
    return bool(out.strip()), None


TERMINAL_STATUSES = {"done", "failed", "skipped", "rescued"}


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
    ap.add_argument("--manifest", required=True, help="Path to run-codex-1 manifest.json")
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
    cleaned_ids: set[str] = set()

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
            cleaned_ids.add(entry_id)
            continue

        # Non-terminal manifest status — refuse. `running` means the worktree
        # is in active use; `queued` means a runner may (re-)claim it. Cleaning
        # either is unsafe regardless of branch-merged / tree-clean signals.
        # Operator escape hatch is the existing --force-abandon flag.
        status = entry.get("status")
        if status in ("running", "queued") and not force:
            refused += 1
            actions.append({
                "entry_id": entry_id, "action": "refuse",
                "message": (
                    f"manifest status={status!r} is non-terminal; "
                    f"worktree may be in active use. "
                    f"Pass --force-abandon {entry_id} to remove anyway."
                ),
                "reasons": [f"manifest status={status!r} (non-terminal)"],
                "worktree_path": wt,
                "manifest_status": status,
            })
            continue

        # No worktree path or path missing on disk
        if not worktree_present(wt):
            actions.append({
                "entry_id": entry_id, "action": "noop",
                "message": f"worktree not present at {wt!r}; marking cleaned",
                "worktree_path": wt,
            })
            cleaned_ids.add(entry_id)
            continue

        branch = detect_worktree_branch(wt)
        merged = branch_is_merged(args.base, branch, root) if branch else False
        dirty, dirty_err = worktree_dirty(wt)

        # Surface a git failure as a hard error (NOT silently as dirty).
        if dirty_err is not None:
            failed += 1
            actions.append({
                "entry_id": entry_id, "action": "failed",
                "message": f"git status failed at {wt!r}: {dirty_err}",
                "worktree_path": wt,
            })
            continue

        # Build refusal reasons. When BOTH dirty AND unmerged are true, surface
        # both — operator needs to know they're committing to abandoning both
        # uncommitted work AND unmerged work when they pass --force-abandon.
        refusal_reasons: list[str] = []
        if branch and not merged:
            refusal_reasons.append(
                f"branch {branch!r} not merged into {args.base}"
            )
        if dirty:
            refusal_reasons.append(f"worktree {wt!r} is dirty (uncommitted changes)")

        if refusal_reasons and not force:
            refused += 1
            actions.append({
                "entry_id": entry_id, "action": "refuse",
                "message": (
                    "; ".join(refusal_reasons)
                    + f"; pass --force-abandon {entry_id} to remove anyway"
                ),
                "reasons": refusal_reasons,
                "worktree_path": wt, "branch": branch,
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

        cleaned_ids.add(entry_id)
        actions.append({
            "entry_id": entry_id, "action": "removed",
            "message": f"worktree removed at {wt}" + (" (forced)" if force else ""),
            "worktree_path": wt,
        })

    # Persist manifest changes (only on actual mutations).
    # Single write path: re-read under lock, mark every cleaned id, write
    # back. If after the write every entry is in a terminal status AND every
    # applicable entry is cleaned_up, delete the manifest + lock (lifecycle
    # rule documented in references/universal/manifest-contract.md:248).
    write_failed = False
    manifest_deleted = False
    if args.execute and cleaned_ids:
        try:
            with manifest_lock(manifest_path):
                fresh = load_manifest(manifest_path)
                if fresh is None or not isinstance(fresh.get("entries"), list):
                    fresh = manifest  # fall back to in-memory copy

                ts = utc_now_iso()
                for fe in fresh["entries"]:
                    if isinstance(fe, dict) and fe.get("id") in cleaned_ids:
                        fe["cleaned_up"] = True
                        fe["updated_at"] = ts

                # Decide whether to delete the manifest.
                all_terminal_and_cleaned = all(
                    isinstance(fe, dict)
                    and fe.get("status") in TERMINAL_STATUSES
                    and (
                        # entries with no worktree don't need cleaned_up
                        not fe.get("worktree_path")
                        or fe.get("cleaned_up") is True
                    )
                    for fe in fresh["entries"]
                )

                atomic_write(manifest_path, json.dumps(fresh, indent=2) + "\n")

                if all_terminal_and_cleaned and fresh["entries"]:
                    # Delete the manifest and its lock file (the cleanup
                    # contract: every entry terminal and tidy → state is
                    # gone). The lock file stays open until the with-block
                    # exits, so unlink the manifest here and let the lock
                    # cleanup run after.
                    try:
                        os.unlink(str(manifest_path))
                        manifest_deleted = True
                    except OSError as exc:
                        print(
                            f"cleanup-worktrees: manifest delete failed: {exc}",
                            file=sys.stderr,
                        )
            # After the lock context closes, remove the lock file too.
            if manifest_deleted:
                lock_path = manifest_path.with_name(manifest_path.name + ".lock")
                with contextlib.suppress(OSError):
                    os.unlink(str(lock_path))
        except (OSError, SystemExit) as exc:
            print(f"cleanup-worktrees: manifest write failed: {exc}", file=sys.stderr)
            write_failed = True

    # Output
    if args.json:
        out = {
            "ok": failed == 0 and not write_failed,
            "executed": args.execute,
            "manifest_path": str(manifest_path),
            "manifest_deleted": manifest_deleted,
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
                "removed":  "[OK]",
                "plan":     "[DRY]",
                "refuse":   "[REFUSE]",
                "failed":   "[FAIL]",
                "noop":     "[NOOP]",
            }.get(a["action"], "[?]")
            print(f"  {marker} {a['entry_id']}: {a['message']}")
        print()
        if args.execute and cleaned_ids:
            if write_failed:
                print("✗ manifest write failed; some changes may be unpersisted")
            elif manifest_deleted:
                print(f"✓ manifest deleted (all entries terminal+cleaned): {manifest_path}")
            else:
                print(f"✓ manifest updated: {manifest_path}")
        print()

    if write_failed:
        return 4
    if failed > 0:
        if not args.json:
            print(f"✗ {failed} removal(s) failed — see stderr above")
        return 3
    # P1-5: refused entries in dry-run are informational ("preview surfaced
    # entries you have a decision to make on") — they are NOT a failure of
    # the preview itself. Keep exit 2 for refused-during-execute (operator
    # told us to remove and we couldn't, that's actionable). The dispatcher's
    # tidy handler accepts exit 0 and 1 as success, mirroring audit's
    # contract (audit-fleet-state.py: 0 clean, 1 actionable, ≥2 helper-fail).
    if refused > 0:
        if not args.json:
            print(f"⚠ {refused} entry/entries refused — re-run with --force-abandon for those")
        return 2 if args.execute else 1
    if not args.execute and any(a["action"] == "plan" for a in actions):
        if not args.json:
            print("DRY-RUN complete. Re-run with --execute to apply.")
        return 1
    if not args.json:
        print("✓ cleanup complete. Tidy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
