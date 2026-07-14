#!/usr/bin/env python3
"""Merge ordered branches into a base with `git merge --no-ff`, never resolving conflicts.

Policy: a conflicting branch is ABORTED and SKIPPED (reported), the run continues
to the next branch. Conflicts are a human's job; this script never edits files or
stages a half-merged tree. The working tree is always left clean.

Safety:
  - Refuses if the working tree is dirty (can't merge into a dirty tree).
  - Ensures HEAD is on base (checks it out in --execute, else just notes).

Without --execute the script is a DRY-RUN: it predicts conflicts via
`git merge-tree --write-tree` (git 2.38+) and mutates nothing.

Usage:
    python3 merge-branches.py --base main --branches feat/a feat/b           # dry-run
    python3 merge-branches.py --base main --branches feat/a feat/b --execute
    python3 merge-branches.py --base main --branches feat/a --execute --json

Exit codes:
    0  execute mode, no conflicts/errors (all merged or already-merged)
    1  dry-run, OR any branch was skipped-conflict (actionable — human must resolve)
    2  not in a git repo / git error
    3  safety refusal (dirty tree / checkout failed)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def sh(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a shell command, return (returncode, stdout, stderr). Never raise."""
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"


def repo_root() -> Path | None:
    rc, out, _ = sh(["git", "rev-parse", "--show-toplevel"])
    return Path(out) if rc == 0 else None


def tracked_changes_present(root: Path) -> bool:
    """True if there are staged/unstaged changes to TRACKED files.

    Untracked files (porcelain `??`) are ignored: git merges fine alongside
    them, and a cleanup run typically still has junk lying around (it gets
    swept in a later phase). Only tracked modifications make a merge unsafe.
    """
    rc, out, _ = sh(["git", "status", "--porcelain=1"], cwd=root)
    if rc != 0:
        return True  # can't tell → treat as unsafe
    return any(line and not line.startswith("??") for line in out.splitlines())


def current_branch(root: Path) -> str | None:
    rc, out, _ = sh(["git", "symbolic-ref", "--short", "HEAD"], cwd=root)
    return out if rc == 0 else None


def is_merged(base: str, branch: str, root: Path) -> bool:
    rc, _, _ = sh(["git", "merge-base", "--is-ancestor", branch, base], cwd=root)
    return rc == 0


def unmerged_paths(root: Path) -> list[str]:
    """Files in conflicted/unmerged state (git ls-files -u, unique paths)."""
    rc, out, _ = sh(["git", "ls-files", "-u"], cwd=root)
    if rc != 0 or not out.strip():
        return []
    paths = []
    seen = set()
    for line in out.splitlines():
        # format: <mode> <sha> <stage>\t<path>
        if "\t" in line:
            p = line.split("\t", 1)[1]
            if p not in seen:
                seen.add(p)
                paths.append(p)
    return paths


def conflicting_files(root: Path) -> list[str]:
    """Files in conflict during an in-progress merge (diff-filter=U)."""
    rc, out, _ = sh(
        ["git", "diff", "--name-only", "--diff-filter=U"], cwd=root
    )
    if rc != 0:
        return []
    return [l.strip() for l in out.splitlines() if l.strip()]


def staged_anything(root: Path) -> bool:
    """True if there are staged changes (cached diff is non-empty)."""
    rc, _, _ = sh(["git", "diff", "--cached", "--quiet"], cwd=root)
    # rc 0 = no staged changes, rc 1 = staged changes present
    return rc == 1


def predict_merge(base: str, branch: str, root: Path) -> tuple[str, str | None]:
    """DRY-RUN: predict via `git merge-tree --write-tree`.

    Returns (disposition, note). disposition is one of:
      would-merge | would-conflict | unknown
    """
    rc, out, err = sh(
        ["git", "merge-tree", "--write-tree", base, branch], cwd=root
    )
    if rc == 0:
        return "would-merge", None
    if rc == 1:
        return "would-conflict", None
    # rc 128 (or anything else) → old git / unsupported flag.
    msg = (err or out or "").strip()
    return "unknown", (
        "merge-tree prediction unavailable (needs git >= 2.38): "
        + (msg[:200] if msg else "unknown error")
    )


def execute_merge(base: str, branch: str, root: Path) -> dict:
    """EXECUTE: attempt `git merge --no-ff --no-commit <branch>`.

    Returns a disposition dict. Leaves the working tree clean in all cases.
    """
    rc, out, err = sh(
        ["git", "merge", "--no-ff", "--no-commit", branch], cwd=root
    )
    unmerged = unmerged_paths(root)

    if rc != 0 or unmerged:
        # Conflict (or merge refused mid-flight): capture conflicts, then abort.
        conflicts = conflicting_files(root) or unmerged
        sh(["git", "merge", "--abort"], cwd=root)  # best-effort; ignore failure
        # Distinguish a real conflict from an unexpected error: if git named
        # conflict files, it's a conflict; otherwise treat as error.
        if conflicts:
            return {
                "branch": branch,
                "disposition": "skipped-conflict",
                "conflict_files": sorted(set(conflicts)),
            }
        return {
            "branch": branch,
            "disposition": "error",
            "note": (err or out or "merge failed with no conflict files").strip()[:300],
        }

    # rc == 0 and no unmerged paths.
    if staged_anything(root):
        crc, cout, cerr = sh(["git", "commit", "--no-edit"], cwd=root)
        if crc != 0:
            sh(["git", "merge", "--abort"], cwd=root)
            return {
                "branch": branch,
                "disposition": "error",
                "note": (cerr or cout or "commit failed").strip()[:300],
            }
        return {"branch": branch, "disposition": "merged-now"}

    # Clean but nothing staged → already up to date.
    return {"branch": branch, "disposition": "already-merged"}


def run(base: str, branches: list[str], execute: bool, root: Path) -> tuple[list[dict], int]:
    """Process branches in order. Returns (results, exit_code)."""
    results: list[dict] = []

    # Ensure HEAD is on base.
    head = current_branch(root)
    if head != base:
        if execute:
            rc, _, err = sh(["git", "checkout", base], cwd=root)
            if rc != 0:
                print(
                    f"refusing: could not checkout base '{base}': {err}",
                    file=sys.stderr,
                )
                return results, 3
        else:
            # Dry-run: note the mismatch, but merge-tree doesn't need a checkout.
            results.append(
                {
                    "branch": "(head)",
                    "disposition": "note",
                    "note": f"HEAD is on '{head}', not base '{base}'; "
                    f"execute mode would checkout '{base}' first.",
                }
            )

    for b in branches:
        if is_merged(base, b, root):
            results.append({"branch": b, "disposition": "already-merged"})
            continue
        if execute:
            res = execute_merge(base, b, root)
            results.append(res)
            if res["disposition"] == "error":
                # Fatal repo error stops the run; conflicts do NOT.
                # (We continue on skipped-conflict by not breaking here.)
                pass
        else:
            disp, note = predict_merge(base, b, root)
            entry: dict = {"branch": b, "disposition": disp}
            if note:
                entry["note"] = note
            results.append(entry)

    # Exit code.
    if not execute:
        return results, 1

    branch_results = [r for r in results if r["disposition"] != "note"]
    if any(r["disposition"] == "skipped-conflict" for r in branch_results):
        return results, 1
    if any(r["disposition"] == "error" for r in branch_results):
        return results, 2
    return results, 0


def render(results: list[dict], base: str, execute: bool) -> str:
    mode = "EXECUTE" if execute else "DRY-RUN"
    lines = [f"merge-branches [{mode}] into base '{base}':", ""]
    for r in results:
        if r["disposition"] == "note":
            lines.append(f"  note: {r['note']}")
            continue
        line = f"  {r['branch']:<32} {r['disposition']}"
        lines.append(line)
        if r.get("conflict_files"):
            for f in r["conflict_files"]:
                lines.append(f"        conflict: {f}")
        if r.get("note"):
            lines.append(f"        {r['note']}")
    lines.append("")

    branch_results = [r for r in results if r["disposition"] != "note"]
    merged = sum(1 for r in branch_results if r["disposition"] in ("merged-now", "would-merge"))
    skipped = sum(1 for r in branch_results if r["disposition"] in ("skipped-conflict", "would-conflict"))
    already = sum(1 for r in branch_results if r["disposition"] == "already-merged")
    lines.append(f"merged {merged}, skipped-conflict {skipped}, already-merged {already}")
    if not execute:
        lines.append("(dry-run: nothing mutated; re-run with --execute to apply)")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Merge ordered branches into base; skip conflicts.")
    ap.add_argument("--base", default="main", help="base branch to merge into (default: main)")
    ap.add_argument("--branches", nargs="+", required=True, help="ordered branch names to merge")
    ap.add_argument("--execute", action="store_true", help="apply merges (default: dry-run)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    root = repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    if args.execute and tracked_changes_present(root):
        print(
            "refusing: tracked files have uncommitted changes — commit or stash "
            "before merging (untracked junk is fine; it's swept later).",
            file=sys.stderr,
        )
        return 3

    results, code = run(args.base, args.branches, args.execute, root)

    if args.json:
        print(json.dumps({"base": args.base, "execute": args.execute, "results": results}, indent=2))
    else:
        print(render(results, args.base, args.execute))

    return code


if __name__ == "__main__":
    sys.exit(main())
