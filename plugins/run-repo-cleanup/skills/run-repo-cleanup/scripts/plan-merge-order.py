#!/usr/bin/env python3
"""Plan a foundation→leaf merge order for live branches merging into a base.

Classifies branches into three buckets:
  - already_merged: fully contained in base — retire, don't merge.
  - stale: last commit older than --stale-days — skip unless confirmed.
  - active: everything else — ordered foundation→leaf for merging.

Ordering heuristic (active only): a branch that modifies files also modified
by OTHER active branches is more foundational (others will want it first), so
higher overlap_score merges earlier. Ties broken by age (newer first) then name.

The script PLANS; the agent DECIDES the final order. `merge-branches.py` then
consumes the ordered branch names.

Usage:
    python3 plan-merge-order.py --base main
    python3 plan-merge-order.py --base main --branches feat/a feat/b docs/c
    python3 plan-merge-order.py --base main --stale-days 14 --json

Exit codes:
    0  plan produced (>=1 active branch)
    1  fewer than 1 active branch (nothing to merge)
    2  not in a git repo / git error
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
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


def all_non_default_branches(base: str, root: Path) -> list[str]:
    """All local branches except base itself, main, master, HEAD."""
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


def age_days(branch: str, root: Path) -> float:
    """Days since the branch tip's commit. Large number if unknown."""
    rc, out, _ = sh(["git", "log", "-1", "--format=%ct", branch], cwd=root)
    if rc != 0:
        return float("inf")
    try:
        ts = int(out.strip())
    except ValueError:
        return float("inf")
    return max(0.0, (time.time() - ts) / 86400.0)


def is_merged(base: str, branch: str, root: Path) -> bool:
    """True if branch is fully an ancestor of base (nothing to merge)."""
    rc, _, _ = sh(["git", "merge-base", "--is-ancestor", branch, base], cwd=root)
    return rc == 0


def compute_order(active: list[dict]) -> list[dict]:
    """Order active branch dicts (with 'files' sets) foundation→leaf.

    overlap_score: for each file the branch touches, count how many OTHER
    active branches also touch it, summed. Higher = more foundational.
    """
    all_files: Counter = Counter()
    for d in active:
        all_files.update(d["files"])

    for d in active:
        overlap = 0
        for f in d["files"]:
            overlap += max(0, all_files[f] - 1)
        d["overlap_score"] = overlap

    ordered = sorted(
        active,
        key=lambda d: (-d["overlap_score"], d["age_days"], d["branch"]),
    )

    for i, d in enumerate(ordered, 1):
        if d["overlap_score"] > 0:
            d["reason"] = (
                f"position {i}: touches {d['overlap_score']} file-overlap(s) "
                f"with sibling branches (foundation); {d['commits']} commits."
            )
        else:
            d["reason"] = (
                f"position {i}: independent (no file overlap with other active "
                f"branches); {d['commits']} commits."
            )
    return ordered


def build_plan(base: str, branches: list[str], stale_days: float, root: Path) -> dict:
    already_merged: list[str] = []
    active_raw: list[dict] = []
    stale_raw: list[dict] = []

    for b in branches:
        if is_merged(base, b, root):
            already_merged.append(b)
            continue
        d = {
            "branch": b,
            "commits": commit_count(base, b, root),
            "files": files_modified(base, b, root),
            "age_days": round(age_days(b, root), 2),
        }
        d["n_files"] = len(d["files"])
        if d["age_days"] > stale_days:
            stale_raw.append(d)
        else:
            active_raw.append(d)

    ordered = compute_order(active_raw)

    # Strip the raw files sets from output (noisy); keep counts.
    for d in ordered:
        d.pop("files", None)
    stale_clean = []
    for d in sorted(stale_raw, key=lambda d: -d["age_days"]):
        d.pop("files", None)
        stale_clean.append(d)

    return {
        "base": base,
        "stale_days": stale_days,
        "active": ordered,
        "stale": stale_clean,
        "already_merged": sorted(already_merged),
    }


def render(plan: dict) -> str:
    active = plan["active"]
    stale = plan["stale"]
    merged = plan["already_merged"]
    sd = plan["stale_days"]
    lines: list[str] = []

    lines.append(f"Suggested merge order ({len(active)} active branch(es)):")
    lines.append("")
    if not active:
        lines.append("  (no active branches to merge)")
    for i, d in enumerate(active, 1):
        lines.append(f"  {i}. {d['branch']}")
        lines.append(f"     {d['reason']}")
        lines.append(
            f"     files modified: {d['n_files']} · "
            f"overlap score: {d['overlap_score']} · "
            f"age: {d['age_days']}d"
        )
        lines.append("")

    lines.append(f"Stale (>{sd:g}d) — skip unless confirmed:")
    if not stale:
        lines.append("  (none)")
    else:
        for d in stale:
            lines.append(
                f"  - {d['branch']}  (age {d['age_days']}d, "
                f"{d['commits']} commits, {d['n_files']} files)"
            )
    lines.append("")

    lines.append("Already merged — retire, don't merge:")
    if not merged:
        lines.append("  (none)")
    else:
        for b in merged:
            lines.append(f"  - {b}")
    lines.append("")

    lines.append(
        "NOTE: this is a heuristic; the agent decides the final order. Override when"
    )
    lines.append(
        "semantic ordering matters (e.g. 'tests for X must merge after X'). Feed the"
    )
    lines.append(
        "ordered active branch names to merge-branches.py to execute the merges."
    )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Plan a merge order for live branches.")
    ap.add_argument("--base", default="main", help="base branch to merge into (default: main)")
    ap.add_argument("--branches", nargs="*", default=None, help="explicit branch names (default: all non-base local)")
    ap.add_argument("--stale-days", type=float, default=7, help="branches older than this are stale (default: 7)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    root = repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    branches = args.branches if args.branches else all_non_default_branches(args.base, root)
    plan = build_plan(args.base, branches, args.stale_days, root)

    if args.json:
        print(json.dumps(plan, indent=2))
    else:
        print(render(plan))

    return 0 if plan["active"] else 1


if __name__ == "__main__":
    sys.exit(main())
