#!/usr/bin/env python3
"""Propose a foundation→leaf merge order for N branches.

Heuristic: a branch that modifies files also modified by other branches is
more foundational (those other branches will want to rebase on it). Ties are
broken by commit count — smaller branches go later so a reviewer warms up
with the large one.

The script SUGGESTS; the agent DECIDES. Read `references/multi-worktree-merge-order.md`
for the semantics of the decision.

Usage:
    python3 suggest-merge-order.py --base main
    python3 suggest-merge-order.py --base main --branches feat/a feat/b docs/c
    python3 suggest-merge-order.py --base main --json

Exit codes:
    0  suggestion printed
    1  fewer than 2 branches (no ordering needed)
    2  not in a git repo / git error
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


def sh(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"


def repo_root() -> Path | None:
    rc, out, _ = sh(["git", "rev-parse", "--show-toplevel"])
    return Path(out) if rc == 0 else None


def all_non_default_branches(base: str, root: Path) -> list[str]:
    """All local branches except base itself, main, master."""
    rc, out, _ = sh(["git", "branch", "--format=%(refname:short)"], cwd=root)
    if rc != 0:
        return []
    excluded = {base, "main", "master", "HEAD"}
    return [b.strip() for b in out.splitlines() if b.strip() and b.strip() not in excluded]


def commit_count(base: str, branch: str, root: Path) -> int:
    rc, out, _ = sh(["git", "rev-list", "--count", f"{base}..{branch}"], cwd=root)
    if rc != 0:
        return 0
    try:
        return int(out.strip())
    except ValueError:
        return 0


def files_modified(base: str, branch: str, root: Path) -> set[str]:
    rc, out, _ = sh(["git", "diff", "--name-only", f"{base}...{branch}"], cwd=root)
    if rc != 0:
        return set()
    return {line.strip() for line in out.splitlines() if line.strip()}


def compute_order(base: str, branches: list[str], root: Path) -> list[dict]:
    """Return [{branch, commits, files, overlap_score, reason}, ...] in suggested order."""
    per_branch: dict[str, dict] = {}
    all_files = Counter()
    for b in branches:
        files = files_modified(base, b, root)
        commits = commit_count(base, b, root)
        per_branch[b] = {
            "branch": b,
            "commits": commits,
            "files": files,
            "n_files": len(files),
        }
        all_files.update(files)

    # overlap score: for each file the branch touches, how many OTHER branches touch it?
    for b, data in per_branch.items():
        overlap = 0
        for f in data["files"]:
            # all_files[f] is total branches touching this file (counting b itself)
            overlap += max(0, all_files[f] - 1)
        data["overlap_score"] = overlap

    # Order: higher overlap first (foundation); ties broken by FEWER commits last
    ordered = sorted(
        per_branch.values(),
        key=lambda d: (-d["overlap_score"], d["commits"], d["branch"]),
    )

    # Attach human-readable reasoning
    for i, d in enumerate(ordered, 1):
        if d["overlap_score"] > 0:
            d["reason"] = (
                f"position {i}: touches {d['overlap_score']} file-overlaps "
                f"with siblings; {d['commits']} commits."
            )
        elif d["overlap_score"] == 0 and i < len(ordered):
            d["reason"] = (
                f"position {i}: independent (no file overlap with other branches); "
                f"{d['commits']} commits."
            )
        else:
            d["reason"] = (
                f"position {i}: leaf/independent with fewest cross-branch conflicts."
            )

    # drop the raw files set in the output (too noisy); keep file counts
    for d in ordered:
        d.pop("files", None)

    return ordered


def render(ordered: list[dict]) -> str:
    if len(ordered) < 2:
        return "fewer than 2 branches — no ordering needed"
    lines = [f"suggested merge order ({len(ordered)} branches):", ""]
    for i, d in enumerate(ordered, 1):
        lines.append(f"  {i}. {d['branch']}")
        lines.append(f"     {d['reason']}")
        lines.append(
            f"     files modified: {d['n_files']} · "
            f"overlap score: {d['overlap_score']}"
        )
        lines.append("")
    lines.append("NOTE: this is a heuristic (foundation = more file overlap with other branches).")
    lines.append("The agent decides the final order. Override when the heuristic misses semantic")
    lines.append("ordering (e.g. 'tests for X must merge after X').")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="main", help="base branch to diff against (default: main)")
    ap.add_argument("--branches", nargs="*", default=None, help="explicit branch names (default: all non-base)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    root = repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    branches = args.branches if args.branches else all_non_default_branches(args.base, root)
    if len(branches) < 2:
        msg = f"only {len(branches)} branch(es) found — need at least 2 for ordering"
        print(msg, file=sys.stderr)
        return 1

    ordered = compute_order(args.base, branches, root)
    if args.json:
        print(json.dumps(ordered, indent=2))
    else:
        print(render(ordered))
    return 0


if __name__ == "__main__":
    sys.exit(main())
