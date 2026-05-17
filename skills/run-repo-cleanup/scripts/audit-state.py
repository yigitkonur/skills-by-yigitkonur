#!/usr/bin/env python3
"""Read-only state dump for Phase 1 of the run-repo-cleanup flow.

Prints a concise, scannable summary of:
  - Current branch + its upstream + ahead/behind counts
  - Remote configuration (origin vs upstream) with fork-safety verdict
  - Modified / staged / untracked files, grouped by top-level directory
  - Any in-progress rebase / merge / cherry-pick / bisect
  - Unpushed commits on the current branch
  - Open PRs on the fork (best-effort, requires gh CLI)

No git state is mutated. No network writes. Safe to run anywhere.

Usage:
    python3 audit-state.py           # human-readable report
    python3 audit-state.py --json    # machine-readable JSON

Exit codes:
    0  clean (nothing actionable)
    1  actionable state (dirty files, unpushed commits, mid-operation, etc.)
    2  could not determine state (not in a git repo, fatal shell error)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
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


def collect_remotes(root: Path) -> dict[str, dict[str, str]]:
    rc, out, _ = sh(["git", "remote", "-v"], cwd=root)
    remotes: dict[str, dict[str, str]] = {}
    if rc != 0:
        return remotes
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        name, url, kind = parts[0], parts[1], parts[2].strip("()")
        remotes.setdefault(name, {})[kind] = url
    return remotes


def current_branch(root: Path) -> str | None:
    rc, out, _ = sh(["git", "symbolic-ref", "--short", "HEAD"], cwd=root)
    return out if rc == 0 else None


def branch_upstream(root: Path, branch: str) -> str | None:
    rc, out, _ = sh(
        ["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"],
        cwd=root,
    )
    return out if rc == 0 else None


def ahead_behind(root: Path, branch: str, upstream: str) -> tuple[int, int]:
    rc, out, _ = sh(
        ["git", "rev-list", "--left-right", "--count", f"{upstream}...{branch}"],
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


_PORCELAIN_LINE = __import__("re").compile(r"^(.{2})\s(.*)$")


def dirty_files(root: Path) -> dict[str, list[tuple[str, str]]]:
    """Return {group: [(status, path), ...]} where group is the top-level dir.

    Parses `git status --porcelain=1` robustly: the XY status is always the
    first two characters, then a single separator space, then the path (which
    may be quoted if it contains special characters).
    """
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


def open_prs_on_fork(fork_owner_repo: str | None) -> list[dict] | None:
    """Query gh for open PRs; returns None if gh missing or query failed."""
    if not fork_owner_repo:
        return None
    rc, out, _ = sh(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            fork_owner_repo,
            "--state",
            "open",
            "--json",
            "number,title,baseRefName,headRefName,url",
        ]
    )
    if rc != 0:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def open_prs_on_upstream(upstream_owner_repo: str | None) -> list[dict] | None:
    if not upstream_owner_repo:
        return None
    rc, out, _ = sh(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            upstream_owner_repo,
            "--state",
            "open",
            "--author",
            "@me",
            "--json",
            "number,title,url",
        ]
    )
    if rc != 0:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def extract_owner_repo(remote_url: str | None) -> str | None:
    """Extract 'owner/repo' from a github.com git URL, or return None."""
    if not remote_url:
        return None
    url = remote_url.rstrip("/").removesuffix(".git")
    if url.startswith("git@github.com:"):
        return url.split(":", 1)[1]
    for prefix in ("https://github.com/", "http://github.com/"):
        if url.startswith(prefix):
            return url[len(prefix):]
    return None


def list_worktrees(root: Path) -> list[dict]:
    """Return list of worktree dicts parsed from `git worktree list --porcelain`."""
    rc, out, _ = sh(["git", "worktree", "list", "--porcelain"], cwd=root)
    if rc != 0:
        return []
    worktrees: list[dict] = []
    current: dict = {}
    for line in out.splitlines():
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue
        if line.startswith("worktree "):
            current["path"] = line[len("worktree "):]
        elif line.startswith("HEAD "):
            current["head"] = line[len("HEAD "):]
        elif line.startswith("branch "):
            current["branch"] = line[len("branch "):]
        elif line == "bare":
            current["bare"] = True
        elif line == "detached":
            current["detached"] = True
        elif line.startswith("locked"):
            current["locked"] = True
        elif line.startswith("prunable"):
            current["prunable"] = True
    if current:
        worktrees.append(current)
    return worktrees


def list_branches(root: Path) -> dict[str, list[str]]:
    """Return {'local': [...], 'remote': [...]} branch names."""
    result: dict[str, list[str]] = {"local": [], "remote": []}
    rc, out, _ = sh(["git", "branch", "--list"], cwd=root)
    if rc == 0:
        result["local"] = [
            b.removeprefix("* ").removeprefix("+ ").strip()
            for b in out.splitlines() if b.strip()
        ]
    rc, out, _ = sh(["git", "branch", "-r", "--list"], cwd=root)
    if rc == 0:
        result["remote"] = [
            b.strip().split(" -> ")[0]
            for b in out.splitlines() if b.strip() and " -> " not in b
        ]
    return result


def build_report(root: Path) -> dict:
    branch = current_branch(root)
    upstream = branch_upstream(root, branch) if branch else None
    ahead = behind = 0
    if branch and upstream:
        ahead, behind = ahead_behind(root, branch, upstream)

    remotes = collect_remotes(root)
    origin_url = (remotes.get("origin") or {}).get("push")
    upstream_url = (remotes.get("upstream") or {}).get("push")

    fork_owner_repo = extract_owner_repo(origin_url)
    upstream_owner_repo = extract_owner_repo(upstream_url)

    return {
        "repo_root": str(root),
        "branch": branch,
        "branch_upstream": upstream,
        "ahead_commits": ahead,
        "behind_commits": behind,
        "remotes": remotes,
        "origin_owner_repo": fork_owner_repo,
        "upstream_owner_repo": upstream_owner_repo,
        "origin_is_upstream_owner_warning": bool(
            fork_owner_repo and upstream_owner_repo and
            fork_owner_repo.split("/", 1)[0] == upstream_owner_repo.split("/", 1)[0]
        ),
        "dirty_groups": {k: v for k, v in dirty_files(root).items()},
        "mid_operation": mid_operation(root),
        "worktrees": list_worktrees(root),
        "branches": list_branches(root),
        "open_prs_on_fork": open_prs_on_fork(fork_owner_repo),
        "open_prs_on_upstream_by_me": open_prs_on_upstream(upstream_owner_repo),
    }


def actionable(report: dict) -> bool:
    if report["mid_operation"]:
        return True
    if report["dirty_groups"]:
        return True
    if report["ahead_commits"]:
        return True
    return False


def render(report: dict) -> str:
    lines = []
    lines.append(f"repo:    {report['repo_root']}")
    lines.append(f"branch:  {report['branch']}")
    if report["branch_upstream"]:
        lines.append(
            f"upstream: {report['branch_upstream']}  "
            f"(ahead {report['ahead_commits']}, behind {report['behind_commits']})"
        )
    else:
        lines.append("upstream: (none — this branch has no tracking ref)")

    mid = report["mid_operation"]
    if mid:
        lines.append(f"⚠  mid-operation: {mid}")

    lines.append("")
    lines.append("remotes:")
    for name, urls in (report["remotes"] or {}).items():
        push = urls.get("push") or urls.get("fetch") or "?"
        lines.append(f"  {name:<10} {push}")
    if report["origin_is_upstream_owner_warning"]:
        lines.append(
            "⚠  origin and upstream have the same owner — verify that origin is "
            "genuinely the private fork, not the same upstream repo twice."
        )

    lines.append("")
    groups = report["dirty_groups"]
    if not groups:
        lines.append("dirty files: (none — working tree is clean)")
    else:
        lines.append(f"dirty files, grouped by top-level dir ({sum(len(v) for v in groups.values())} total):")
        for group in sorted(groups):
            items = groups[group]
            lines.append(f"  {group}/  ({len(items)})")
            for status, path in items[:8]:
                lines.append(f"    [{status:<2}] {path}")
            if len(items) > 8:
                lines.append(f"    … and {len(items) - 8} more")

    worktrees = report["worktrees"]
    lines.append("")
    if len(worktrees) <= 1:
        lines.append("worktrees: 1 (main only)")
    else:
        lines.append(f"worktrees: {len(worktrees)} — multi-worktree scenario")
        for wt in worktrees:
            branch_or_detached = (
                wt.get("branch", "").removeprefix("refs/heads/") or
                ("(detached)" if wt.get("detached") else "(bare)" if wt.get("bare") else "?")
            )
            path = wt.get("path", "?")
            head = (wt.get("head", "") or "")[:8]
            flags = " ".join(k for k in ("locked", "prunable") if wt.get(k))
            line = f"  {path}  @  {branch_or_detached}  ({head})"
            if flags:
                line += f"  [{flags}]"
            lines.append(line)

    branches = report["branches"]
    n_local = len(branches.get("local", []))
    n_remote = len(branches.get("remote", []))
    lines.append("")
    lines.append(f"branches: {n_local} local, {n_remote} remote")

    fork_prs = report["open_prs_on_fork"]
    if fork_prs is not None:
        lines.append("")
        if fork_prs:
            lines.append(f"open PRs on fork ({report['origin_owner_repo']}):")
            for pr in fork_prs:
                lines.append(
                    f"  #{pr['number']}  {pr['title'][:60]}  "
                    f"({pr['baseRefName']} ← {pr['headRefName']})"
                )
        else:
            lines.append(f"open PRs on fork ({report['origin_owner_repo']}): (none)")

    upstream_prs = report["open_prs_on_upstream_by_me"]
    if upstream_prs:
        lines.append("")
        lines.append(
            f"⚠  open PRs on UPSTREAM ({report['upstream_owner_repo']}) authored by you:"
        )
        for pr in upstream_prs:
            lines.append(f"  #{pr['number']}  {pr['title'][:60]}  {pr['url']}")
        lines.append(
            "    These are posted on the public upstream repo. If unintended, "
            "close them immediately (see references/fork-safety.md)."
        )

    lines.append("")
    if actionable(report):
        lines.append("→ state is ACTIONABLE (dirty tree, unpushed commits, or mid-op).")
    else:
        lines.append("→ state is CLEAN.")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Dump git + gh state for the run-repo-cleanup flow.")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of human report")
    args = ap.parse_args()

    root = find_repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    report = build_report(root)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render(report))

    return 1 if actionable(report) else 0


if __name__ == "__main__":
    sys.exit(main())
