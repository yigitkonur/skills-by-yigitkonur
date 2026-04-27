#!/usr/bin/env python3
"""Retire local + remote branches that are merged to <base>.

Default is DRY-RUN. Requires explicit --execute to actually delete anything.
Refuses to delete: main, master, default, the current branch, or any branch
not fully merged into <base>.

Usage:
    python3 retire-merged-branches.py --base main             # dry-run
    python3 retire-merged-branches.py --base main --execute   # delete for real
    python3 retire-merged-branches.py --base main --remote-only --execute
    python3 retire-merged-branches.py --base main --local-only --execute

Exit codes:
    0  no branches to retire, OR delete succeeded
    1  actionable branches found in dry-run (stay in loop)
    2  not a git repo / git error
    3  refused due to safety check
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROTECTED = {"main", "master", "default", "HEAD"}


def sh(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"


def repo_root() -> Path | None:
    rc, out, _ = sh(["git", "rev-parse", "--show-toplevel"])
    return Path(out) if rc == 0 else None


def current_branch(root: Path) -> str | None:
    rc, out, _ = sh(["git", "symbolic-ref", "--short", "HEAD"], cwd=root)
    return out if rc == 0 else None


def merged_local_branches(base: str, root: Path, current: str | None) -> list[str]:
    rc, out, _ = sh(
        ["git", "branch", "--merged", base, "--format=%(refname:short)"], cwd=root
    )
    if rc != 0:
        return []
    result = []
    for raw in out.splitlines():
        name = raw.strip()
        if not name:
            continue
        if name in PROTECTED or name == base or name == current:
            continue
        result.append(name)
    return result


def merged_remote_branches(base: str, root: Path, remote: str = "origin") -> list[str]:
    rc, out, _ = sh(
        ["git", "branch", "-r", "--merged", f"{remote}/{base}", "--format=%(refname:short)"],
        cwd=root,
    )
    if rc != 0:
        return []
    result = []
    prefix = f"{remote}/"
    for raw in out.splitlines():
        name = raw.strip().split(" -> ")[0]
        if not name.startswith(prefix):
            continue
        short = name[len(prefix):]
        if short in PROTECTED or short == base or short == "HEAD":
            continue
        result.append(name)
    return result


def run_action(cmd: list[str], dry_run: bool, label: str, cwd: Path) -> bool:
    prefix = "[DRY]" if dry_run else "[DO] "
    print(f"  {prefix} {label}: {' '.join(cmd)}")
    if dry_run:
        return True
    rc, out, err = sh(cmd, cwd=cwd)
    if rc != 0:
        print(f"        ✗ failed: {err or out}", file=sys.stderr)
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="main", help="branch to check merged-status against (default: main)")
    ap.add_argument("--remote", default="origin", help="remote name (default: origin)")
    ap.add_argument("--execute", action="store_true", help="actually perform deletions")
    ap.add_argument("--local-only", action="store_true", help="only retire local branches")
    ap.add_argument("--remote-only", action="store_true", help="only retire remote branches")
    args = ap.parse_args()

    root = repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    current = current_branch(root)
    dry_run = not args.execute

    print(f"base branch:    {args.base}")
    print(f"remote:         {args.remote}")
    print(f"current branch: {current}")
    print(f"mode:           {'DRY-RUN (no changes)' if dry_run else 'EXECUTE (deleting)'}")
    print("")

    any_action = False
    errors = 0

    if not args.remote_only:
        local = merged_local_branches(args.base, root, current)
        if local:
            any_action = True
            print(f"{len(local)} local branch(es) merged to {args.base}:")
            for b in local:
                ok = run_action(
                    ["git", "branch", "-d", b],
                    dry_run=dry_run, label="delete local", cwd=root,
                )
                if not ok:
                    errors += 1
            print("")
        else:
            print(f"local branches merged to {args.base}: none")
            print("")

    if not args.local_only:
        remote = merged_remote_branches(args.base, root, args.remote)
        if remote:
            any_action = True
            print(f"{len(remote)} remote branch(es) merged to {args.remote}/{args.base}:")
            for full in remote:
                short = full.split("/", 1)[1] if "/" in full else full
                ok = run_action(
                    ["git", "push", args.remote, "--delete", short],
                    dry_run=dry_run, label="delete remote", cwd=root,
                )
                if not ok:
                    errors += 1
            print("")
        else:
            print(f"remote branches merged to {args.remote}/{args.base}: none")
            print("")

    if not any_action:
        print("✓ nothing to retire. Tidy.")
        return 0
    if dry_run:
        print("DRY-RUN complete. Re-run with --execute to actually retire.")
        return 1
    if errors:
        print(f"✗ {errors} deletion(s) failed. See stderr above.", file=sys.stderr)
        return 2
    print("✓ retire complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
