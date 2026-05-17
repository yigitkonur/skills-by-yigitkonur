#!/usr/bin/env python3
"""Enumerate git worktrees with branch, HEAD, dirty status, unpushed count.

Human-readable or JSON output. Read-only. Phase 0 / Phase 2 helper.

Usage:
    python3 list-worktrees.py           # text
    python3 list-worktrees.py --json    # machine-readable

Exit codes:
    0  enumerated (even if 1 worktree)
    2  not in a git repository
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def sh(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"


def find_repo_root() -> Path | None:
    rc, out, _ = sh(["git", "rev-parse", "--show-toplevel"])
    return Path(out) if rc == 0 else None


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


def enrich(wt: dict) -> dict:
    path = wt.get("path")
    if not path or not Path(path).is_dir():
        return wt
    p = Path(path)

    # dirty count
    rc, out, _ = sh(["git", "status", "--porcelain=1"], cwd=p)
    wt["dirty_count"] = len([l for l in out.splitlines() if l.strip()]) if rc == 0 else None

    # unpushed count vs upstream
    branch = wt.get("branch")
    if branch and not wt.get("detached"):
        rc, upstream, _ = sh(
            ["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"], cwd=p
        )
        if rc == 0 and upstream:
            wt["upstream"] = upstream
            rc2, out2, _ = sh(
                ["git", "rev-list", "--count", f"{upstream}..{branch}"], cwd=p
            )
            if rc2 == 0:
                try:
                    wt["unpushed"] = int(out2.strip())
                except ValueError:
                    pass

    # commit count ahead of origin/main (useful for multi-worktree ordering)
    rc, out, _ = sh(["git", "rev-list", "--count", "origin/main..HEAD"], cwd=p)
    if rc == 0:
        try:
            wt["commits_ahead_of_origin_main"] = int(out.strip())
        except ValueError:
            pass

    return wt


def render(trees: list[dict]) -> str:
    if not trees:
        return "no worktrees (are you inside a git repo?)"
    lines = [f"{len(trees)} worktree(s):"]
    lines.append("")
    for wt in trees:
        branch = wt.get("branch", "(detached)" if wt.get("detached") else "(bare)" if wt.get("bare") else "?")
        path = wt.get("path", "?")
        head = (wt.get("head", "") or "")[:8]
        dirty = wt.get("dirty_count")
        unpushed = wt.get("unpushed")
        ahead = wt.get("commits_ahead_of_origin_main")
        upstream = wt.get("upstream")

        lines.append(f"  • {path}")
        lines.append(f"    branch: {branch}  (HEAD {head})")
        if upstream:
            lines.append(f"    tracks: {upstream}")
        extras = []
        if dirty is not None:
            extras.append(f"{dirty} dirty")
        if unpushed is not None:
            extras.append(f"{unpushed} unpushed")
        if ahead is not None:
            extras.append(f"{ahead} ahead of origin/main")
        flags = [k for k in ("locked", "prunable", "bare", "detached") if wt.get(k)]
        if flags:
            extras.append(",".join(flags))
        if extras:
            lines.append(f"    state:  {' · '.join(extras)}")
        lines.append("")
    if len(trees) > 1:
        lines.append("→ multi-worktree scenario. Use suggest-merge-order.py for ordering.")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = find_repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    trees = [enrich(wt) for wt in parse_worktrees(root)]
    if args.json:
        print(json.dumps(trees, indent=2))
    else:
        print(render(trees))
    return 0


if __name__ == "__main__":
    sys.exit(main())
