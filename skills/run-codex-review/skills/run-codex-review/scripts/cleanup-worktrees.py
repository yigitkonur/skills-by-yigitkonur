#!/usr/bin/env python3
"""Remove review worktrees; refuse unmerged unless --force-abandon.

Reads the manifest, walks each branch entry, decides per branch whether to
remove its worktree. A branch is safe to remove only if it's fully merged
into <base>. Otherwise the script refuses unless explicitly told to abandon
that branch via --force-abandon.

Default is dry-run.

Usage:
    python3 cleanup-worktrees.py
    python3 cleanup-worktrees.py --base main --execute
    python3 cleanup-worktrees.py --base main --execute --force-abandon feat/x feat/y

Exit codes:
    0  all worktrees handled (removed or noted as already-cleaned)
    1  dry-run with actionable removals
    2  some refused — caller must add --force-abandon for them
    3  worktree-remove failed (e.g. dirty tree refused removal)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_MANIFEST = "/tmp/codex-review-manifest.json"


def sh(cmd, cwd=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"


def repo_root() -> Path | None:
    rc, out, _ = sh(["git", "rev-parse", "--show-toplevel"])
    return Path(out) if rc == 0 else None


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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic_write(path: str, content: str):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".manifest.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_manifest(path: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--base", default="main", help="base branch to check merged-status against")
    ap.add_argument("--execute", action="store_true", help="actually remove worktrees")
    ap.add_argument("--force-abandon", nargs="*", default=[],
                    help="branches whose worktrees should be removed even if not merged")
    args = ap.parse_args()

    root = repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    manifest = load_manifest(args.manifest)
    if manifest is None:
        print(f"manifest absent or unreadable: {args.manifest}")
        print("(nothing to clean — exit 0)")
        return 0

    branches = manifest.get("branches", [])
    if not branches:
        print("manifest has no branches; nothing to do")
        return 0

    print(f"manifest:       {args.manifest}")
    print(f"base branch:    {args.base}")
    print(f"force-abandon:  {args.force_abandon if args.force_abandon else '(none)'}")
    print(f"mode:           {'EXECUTE' if args.execute else 'DRY-RUN'}")
    print("")

    actions = []  # list of (branch, action, message)
    refused = 0
    failed = 0

    for entry in branches:
        branch = entry.get("branch", "?")
        wt = entry.get("worktree_path") or ""
        force = branch in args.force_abandon

        if entry.get("cleaned_up"):
            actions.append((branch, "noop", "already cleaned up; skipping"))
            continue

        if not worktree_present(wt):
            actions.append((branch, "noop", f"worktree not present at {wt}; skipping"))
            entry["cleaned_up"] = True
            entry["updated_at"] = utc_now_iso()
            continue

        merged = branch_is_merged(args.base, branch, root)
        dirty = worktree_dirty(wt) if wt else False

        if not merged and not force:
            refused += 1
            actions.append((branch, "refuse",
                f"branch not merged into {args.base}; pass --force-abandon {branch} to remove anyway"))
            continue

        if dirty and not force:
            refused += 1
            actions.append((branch, "refuse",
                f"worktree {wt} is dirty; pass --force-abandon {branch} to discard"))
            continue

        if not args.execute:
            kind = "force-remove" if force else "remove"
            actions.append((branch, "plan", f"would {kind} worktree at {wt}"))
            continue

        # Execute
        cmd = ["git", "worktree", "remove"]
        if force or dirty:
            cmd.append("--force")
        cmd.append(wt)
        rc, _, err = sh(cmd, cwd=root)
        if rc != 0:
            failed += 1
            actions.append((branch, "failed", f"git worktree remove failed: {err}"))
            continue

        entry["cleaned_up"] = True
        entry["updated_at"] = utc_now_iso()
        actions.append((branch, "removed",
            f"worktree removed at {wt}" + (" (forced)" if force else "")))

    # Print
    for branch, action, msg in actions:
        marker = {
            "removed":      "[DO]",
            "plan":         "[DRY]",
            "refuse":       "[REFUSE]",
            "failed":       "[FAIL]",
            "noop":         "[NOOP]",
        }.get(action, "[?]")
        print(f"  {marker} {branch}: {msg}")

    # Persist manifest changes (only if we mutated anything)
    if args.execute and any(a[1] in ("removed", "noop") for a in actions):
        atomic_write(args.manifest, json.dumps(manifest, indent=2))
        print("")
        print(f"✓ manifest updated: {args.manifest}")

    print("")
    if refused > 0:
        print(f"✗ {refused} branch(es) refused — re-run with --force-abandon for those")
        return 2
    if failed > 0:
        print(f"✗ {failed} removal(s) failed — see stderr above")
        return 3
    if not args.execute and any(a[1] == "plan" for a in actions):
        print("DRY-RUN complete. Re-run with --execute to apply.")
        return 1
    print("✓ cleanup complete. Tidy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
