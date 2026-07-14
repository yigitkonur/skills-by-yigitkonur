#!/usr/bin/env python3
"""Read-only git inventory for the run-repo-cleanup flow.

Surveys every branch (local and remote-only), every worktree, the dirty
working tree, mid-operation state, and remotes — then emits a verdict on
whether the repo needs cleanup work. No git state is mutated; no network
writes. Safe to run anywhere.

This skill merges all live branches/worktrees into the base branch LOCALLY.
There is NO fork, NO upstream, NO PR concept here — just a single repo whose
non-base branches need to be merged and retired.

Usage:
    python3 audit-state.py                    # human-readable report
    python3 audit-state.py --base main        # compare against `main`
    python3 audit-state.py --stale-days 14    # age cutoff for "stale"
    python3 audit-state.py --json             # machine-readable JSON

Exit codes:
    0  clean (no branches to merge/retire, no dirty tree, no mid-op, one worktree)
    1  actionable (any non-base branch, dirty tree, mid-op, or extra worktree)
    2  not inside a git repository
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path


def sh(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a shell command, return (returncode, stdout, stderr). Never raise.

    Only trailing newline is stripped; leading whitespace is preserved so
    callers that parse column-aligned output (e.g. git status --porcelain)
    get faithful line content.
    """
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"


def find_repo_root() -> Path | None:
    rc, out, _ = sh(["git", "rev-parse", "--show-toplevel"])
    if rc != 0:
        return None
    return Path(out)


def collect_remotes(root: Path) -> dict[str, str]:
    """Parse `git remote -v` to {name: url}. Informational only."""
    rc, out, _ = sh(["git", "remote", "-v"], cwd=root)
    remotes: dict[str, str] = {}
    if rc != 0:
        return remotes
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        name, url = parts[0], parts[1]
        remotes.setdefault(name, url)
    return remotes


def current_branch(root: Path) -> str | None:
    rc, out, _ = sh(["git", "symbolic-ref", "--short", "HEAD"], cwd=root)
    return out if rc == 0 else None


def resolve_base(root: Path, requested: str) -> str:
    """Resolve the base branch: requested if it exists, else main, else master,
    else the branch HEAD points at on the primary worktree."""
    def ref_exists(ref: str) -> bool:
        rc, _, _ = sh(["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{ref}"], cwd=root)
        return rc == 0

    if ref_exists(requested):
        return requested
    if ref_exists("main"):
        return "main"
    if ref_exists("master"):
        return "master"
    cur = current_branch(root)
    if cur:
        return cur
    return requested


def mid_operation(root: Path) -> str | None:
    git_dir_rc, git_dir, _ = sh(["git", "rev-parse", "--git-dir"], cwd=root)
    if git_dir_rc != 0:
        return None
    gd = Path(root) / git_dir if not Path(git_dir).is_absolute() else Path(git_dir)
    markers = {
        "rebase-merge": "rebase in progress",
        "rebase-apply": "rebase (apply) in progress",
        "MERGE_HEAD": "merge in progress",
        "CHERRY_PICK_HEAD": "cherry-pick in progress",
        "REVERT_HEAD": "revert in progress",
        "BISECT_LOG": "bisect in progress",
    }
    for marker, label in markers.items():
        if (gd / marker).exists():
            return label
    return None


_PORCELAIN_LINE = re.compile(r"^(.{2})\s(.*)$")


def dirty_files(root: Path) -> dict[str, list[tuple[str, str]]]:
    """Return {group: [(status, path), ...]} where group is the top-level dir."""
    rc, out, _ = sh(["git", "status", "--porcelain=1"], cwd=root)
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    if rc != 0:
        return grouped
    for line in out.splitlines():
        m = _PORCELAIN_LINE.match(line)
        if not m:
            continue
        status = m.group(1).strip() or "?"
        path = m.group(2).strip().strip('"')
        if " -> " in path:  # rename: "old -> new"
            path = path.split(" -> ", 1)[1]
        top = path.split("/", 1)[0] if "/" in path else "(root)"
        grouped[top].append((status, path))
    return grouped


def local_branches(root: Path) -> list[str]:
    rc, out, _ = sh(["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/"], cwd=root)
    if rc != 0:
        return []
    return [b.strip() for b in out.splitlines() if b.strip()]


def remote_only_branches(root: Path, locals_: set[str]) -> list[str]:
    """origin/ refs with no local counterpart, excluding origin/HEAD."""
    rc, out, _ = sh(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/"],
        cwd=root,
    )
    if rc != 0:
        return []
    result = []
    for b in out.splitlines():
        b = b.strip()
        if not b or b == "origin/HEAD" or b.endswith("/HEAD"):
            continue
        short = b[len("origin/"):]
        if short in locals_:
            continue
        result.append(b)
    return result


def last_commit_iso(root: Path, ref: str) -> str | None:
    rc, out, _ = sh(["git", "log", "-1", "--format=%cI", ref], cwd=root)
    return out if rc == 0 and out else None


def last_commit_epoch(root: Path, ref: str) -> int | None:
    rc, out, _ = sh(["git", "log", "-1", "--format=%ct", ref], cwd=root)
    if rc != 0 or not out.strip():
        return None
    try:
        return int(out.strip())
    except ValueError:
        return None


def ahead_behind(root: Path, base: str, ref: str) -> tuple[int, int]:
    """ahead/behind of ref relative to base via base...ref left-right count.
    Left = behind (commits in base not ref), right = ahead (commits in ref not base)."""
    rc, out, _ = sh(
        ["git", "rev-list", "--left-right", "--count", f"{base}...{ref}"],
        cwd=root,
    )
    if rc != 0:
        return 0, 0
    parts = out.split()
    if len(parts) != 2:
        return 0, 0
    try:
        behind, ahead = int(parts[0]), int(parts[1])
    except ValueError:
        return 0, 0
    return ahead, behind


def is_merged(root: Path, base: str, ref: str) -> bool:
    rc, _, _ = sh(["git", "merge-base", "--is-ancestor", ref, base], cwd=root)
    return rc == 0


def n_files_changed(root: Path, base: str, ref: str) -> int:
    rc, out, _ = sh(["git", "diff", "--name-only", f"{base}...{ref}"], cwd=root)
    if rc != 0:
        return 0
    return len([l for l in out.splitlines() if l.strip()])


def classify(merged: bool, age_days: int | None, stale_days: int) -> str:
    if merged:
        return "already-merged"
    if age_days is not None and age_days > stale_days:
        return "stale"
    return "active"


def survey_branches(root: Path, base: str, stale_days: int) -> list[dict]:
    now = int(time.time())
    locals_ = local_branches(root)
    locals_set = set(locals_)
    branches: list[dict] = []

    def add(name: str, ref: str, is_remote_only: bool) -> None:
        epoch = last_commit_epoch(root, ref)
        age_days = (now - epoch) // 86400 if epoch is not None else None
        ahead, behind = ahead_behind(root, base, ref)
        merged = is_merged(root, base, ref)
        branches.append({
            "name": name,
            "is_remote_only": is_remote_only,
            "last_commit_iso": last_commit_iso(root, ref),
            "age_days": age_days,
            "ahead": ahead,
            "behind": behind,
            "merged": merged,
            "n_files": n_files_changed(root, base, ref),
            "classification": classify(merged, age_days, stale_days),
        })

    for name in locals_:
        if name == base:
            continue
        add(name, name, False)

    for ref in remote_only_branches(root, locals_set):
        add(ref, ref, True)

    return branches


def parse_worktrees(root: Path) -> list[dict]:
    rc, out, _ = sh(["git", "worktree", "list", "--porcelain"], cwd=root)
    if rc != 0:
        return []
    trees: list[dict] = []
    cur: dict = {}
    for line in out.splitlines():
        if not line:
            if cur:
                trees.append(cur)
                cur = {}
            continue
        if line.startswith("worktree "):
            cur["path"] = line[len("worktree "):]
        elif line.startswith("HEAD "):
            cur["head"] = line[len("HEAD "):]
        elif line.startswith("branch "):
            cur["branch"] = line[len("branch "):].removeprefix("refs/heads/")
        elif line == "bare":
            cur["bare"] = True
        elif line == "detached":
            cur["detached"] = True
        elif line.startswith("locked"):
            cur["locked"] = True
        elif line.startswith("prunable"):
            cur["prunable"] = True
    if cur:
        trees.append(cur)
    return trees


def survey_worktrees(root: Path, base: str) -> list[dict]:
    trees = parse_worktrees(root)
    result: list[dict] = []
    for wt in trees:
        path = wt.get("path")
        entry = {
            "path": path,
            "branch": wt.get("branch") or ("(detached)" if wt.get("detached") else "(bare)" if wt.get("bare") else "?"),
            "dirty_count": None,
            "ahead_of_base": None,
        }
        p = Path(path) if path else None
        if p and p.is_dir():
            rc, out, _ = sh(["git", "status", "--porcelain=1"], cwd=p)
            entry["dirty_count"] = len([l for l in out.splitlines() if l.strip()]) if rc == 0 else None

            rc, out, _ = sh(["git", "rev-list", "--count", f"{base}..HEAD"], cwd=p)
            if rc != 0:
                rc, out, _ = sh(["git", "rev-list", "--count", f"origin/{base}..HEAD"], cwd=p)
            if rc == 0:
                try:
                    entry["ahead_of_base"] = int(out.strip())
                except ValueError:
                    pass
        result.append(entry)
    return result


def build_report(root: Path, requested_base: str, stale_days: int) -> dict:
    base = resolve_base(root, requested_base)
    branches = survey_branches(root, base, stale_days)
    worktrees = survey_worktrees(root, base)
    dirty = {k: v for k, v in dirty_files(root).items()}
    mid = mid_operation(root)

    has_dirty = bool(dirty)
    has_branches = bool(branches)
    has_extra_worktree = len(worktrees) > 1
    is_actionable = has_dirty or bool(mid) or has_branches or has_extra_worktree

    return {
        "repo_root": str(root),
        "base": base,
        "current_branch": current_branch(root),
        "mid_operation": mid,
        "stale_days": stale_days,
        "branches": branches,
        "worktrees": worktrees,
        "dirty_groups": dirty,
        "remotes": collect_remotes(root),
        "verdict": "actionable" if is_actionable else "clean",
    }


def _actionable_reason(report: dict) -> str:
    reasons = []
    if report["dirty_groups"]:
        n = sum(len(v) for v in report["dirty_groups"].values())
        reasons.append(f"{n} dirty file(s)")
    if report["mid_operation"]:
        reasons.append(report["mid_operation"])
    counts: dict[str, int] = defaultdict(int)
    for b in report["branches"]:
        counts[b["classification"]] += 1
    branch_bits = [f"{counts[c]} {c}" for c in ("active", "stale", "already-merged") if counts.get(c)]
    if branch_bits:
        reasons.append("branches: " + ", ".join(branch_bits))
    if len(report["worktrees"]) > 1:
        reasons.append(f"{len(report['worktrees'])} worktrees")
    return "; ".join(reasons) if reasons else "needs review"


def render(report: dict) -> str:
    lines: list[str] = []
    lines.append(f"repo:    {report['repo_root']}")
    lines.append(f"base:    {report['base']}")
    lines.append(f"current: {report['current_branch']}")
    if report["mid_operation"]:
        lines.append(f"!!  mid-operation: {report['mid_operation']}")

    lines.append("")
    branches = report["branches"]
    if not branches:
        lines.append(f"branches: (none other than base `{report['base']}`)")
    else:
        by_class: dict[str, list[dict]] = defaultdict(list)
        for b in branches:
            by_class[b["classification"]].append(b)
        for cls in ("active", "stale", "already-merged"):
            group = by_class.get(cls, [])
            lines.append(f"{cls} ({len(group)}):")
            for b in sorted(group, key=lambda x: x["name"]):
                age = f"{b['age_days']}d" if b["age_days"] is not None else "?"
                ro = " [remote-only]" if b["is_remote_only"] else ""
                lines.append(
                    f"  {b['name']}{ro}  {age}  +{b['ahead']}/-{b['behind']}  {b['n_files']} files"
                )

    worktrees = report["worktrees"]
    lines.append("")
    if len(worktrees) <= 1:
        lines.append("worktrees: 1 (main only)")
    else:
        lines.append(f"worktrees: {len(worktrees)} — multi-worktree scenario")
        for wt in worktrees:
            dirty = wt.get("dirty_count")
            ahead = wt.get("ahead_of_base")
            extras = []
            if dirty is not None:
                extras.append(f"{dirty} dirty")
            if ahead is not None:
                extras.append(f"{ahead} ahead of base")
            suffix = ("  (" + ", ".join(extras) + ")") if extras else ""
            lines.append(f"  {wt.get('path', '?')}  @  {wt.get('branch', '?')}{suffix}")

    lines.append("")
    groups = report["dirty_groups"]
    if not groups:
        lines.append("dirty files: (none — working tree is clean)")
    else:
        total = sum(len(v) for v in groups.values())
        lines.append(f"dirty files, grouped by top-level dir ({total} total):")
        for group in sorted(groups):
            items = groups[group]
            lines.append(f"  {group}/  ({len(items)})")
            for status, path in items[:8]:
                lines.append(f"    [{status:<2}] {path}")
            if len(items) > 8:
                lines.append(f"    ... and {len(items) - 8} more")

    lines.append("")
    if report["remotes"]:
        lines.append("remotes:")
        for name, url in report["remotes"].items():
            lines.append(f"  {name:<10} {url}")
        lines.append("")

    if report["verdict"] == "clean":
        lines.append("-> Repo is clean — nothing to do.")
    else:
        lines.append(f"-> ACTIONABLE: {_actionable_reason(report)}.")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-only git inventory for run-repo-cleanup.")
    ap.add_argument("--base", default="main", help="merge target branch to compare against (default: main)")
    ap.add_argument("--stale-days", type=int, default=7, help="age cutoff in days for `stale` classification (default: 7)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of human report")
    args = ap.parse_args()

    root = find_repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    report = build_report(root, args.base, args.stale_days)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render(report))

    return 1 if report["verdict"] == "actionable" else 0


if __name__ == "__main__":
    sys.exit(main())
