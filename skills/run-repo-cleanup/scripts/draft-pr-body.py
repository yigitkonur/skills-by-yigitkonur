#!/usr/bin/env python3
"""Generate a Phase-3 PR body skeleton from a commit range.

Inspects the commits between <base> and <head>, produces a Markdown
body that follows the run-repo-cleanup template:
  - Title (from the most recent non-merge commit subject)
  - Summary block (from commit subjects)
  - Context & motivation (empty, to fill)
  - Per-item sections (one per commit; filled with files-touched)
  - Files touched table (aggregate)
  - Verification section (checklist skeleton)
  - Risks & open items (empty, to fill)
  - Follow-ups (empty, to fill)

No network calls. Pure git inspection. Pipe output into /tmp/pr-body.md
and hand-edit the prose sections before `gh pr create --body-file`.

Usage:
    python3 draft-pr-body.py --base main --head HEAD
    python3 draft-pr-body.py --base origin/main --head feat/foo
    python3 draft-pr-body.py --base main --head HEAD --title "Custom PR title"
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def sh(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return p.stdout.rstrip()


def list_commits(base: str, head: str) -> list[tuple[str, str, str]]:
    """Return [(sha, subject, body), ...] for commits in base..head."""
    rec_sep = "\x1e"
    fld_sep = "\x1f"
    fmt = f"%H{fld_sep}%s{fld_sep}%b{rec_sep}"
    raw = sh(["git", "log", "--no-merges", f"--format={fmt}", f"{base}..{head}"])
    commits: list[tuple[str, str, str]] = []
    for record in raw.split(rec_sep):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split(fld_sep)
        if len(parts) < 3:
            continue
        sha, subject, body = parts[0], parts[1], parts[2].strip()
        commits.append((sha, subject, body))
    # oldest first — easier to read
    commits.reverse()
    return commits


def commit_files(sha: str) -> list[tuple[str, str]]:
    """Return [(status, path), ...] for a commit."""
    raw = sh(["git", "show", "--name-status", "--format=", sha])
    files: list[tuple[str, str]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        status, path = parts[0][0], parts[1]
        files.append((status, path))
    return files


def aggregate_files(commits: list[tuple[str, str, str]]) -> list[tuple[str, str]]:
    """Collapse per-commit file lists; last-seen status wins."""
    latest: dict[str, str] = {}
    for sha, _subj, _body in commits:
        for status, path in commit_files(sha):
            latest[path] = status
    return sorted(((status, path) for path, status in latest.items()), key=lambda x: x[1])


def stats_for(base: str, head: str) -> tuple[int, int, int]:
    """Return (files_changed, additions, deletions) via git diff --shortstat."""
    raw = sh(["git", "diff", "--shortstat", f"{base}...{head}"])
    files = insertions = deletions = 0
    for token in raw.split(","):
        token = token.strip()
        if "file" in token:
            files = int(token.split()[0])
        elif "insertion" in token:
            insertions = int(token.split()[0])
        elif "deletion" in token:
            deletions = int(token.split()[0])
    return files, insertions, deletions


def domain_of(path: str) -> str:
    """Map a path to a one-word domain for the files-touched table."""
    if path.endswith("AGENTS.md") or path.endswith("CLAUDE.md") or path.endswith("README.md"):
        return "Docs"
    parts = path.split("/")
    if parts[0] == "src":
        return "/".join(parts[:3]) if len(parts) >= 3 else "/".join(parts)
    if parts[0] == "packages" and len(parts) >= 2:
        return f"packages/{parts[1]}"
    if parts[0] == "scripts":
        return "Scripts"
    if parts[0] in {"locales", "i18n"}:
        return "Locales"
    if parts[0] == ".github":
        return "CI"
    return parts[0] or "Root"


def render(
    title: str,
    commits: list[tuple[str, str, str]],
    files: list[tuple[str, str]],
    stats: tuple[int, int, int],
    base: str,
    head: str,
) -> str:
    out: list[str] = []
    out.append(f"# {title}")
    out.append("")
    out.append("## Summary")
    out.append("")
    # One bullet per commit subject
    for _sha, subj, _body in commits:
        out.append(f"- {subj}")
    f, a, d = stats
    out.append("")
    out.append(f"**Net diff:** {f} files, +{a} / −{d}. Commits: {len(commits)}.")
    out.append("")
    out.append("## Context & motivation")
    out.append("")
    out.append("> TODO: explain why this PR exists — the problem it solves, what "
               "prompted it, what the intended outcome is. 3–5 sentences.")
    out.append("")
    out.append(f"## The {len(commits)} item{'s' if len(commits) != 1 else ''}")
    out.append("")
    for idx, (sha, subj, body) in enumerate(commits, 1):
        out.append(f"### {idx}. {subj}")
        out.append("")
        cf = commit_files(sha)
        if cf:
            listing = ", ".join(f"`{p}`" for _s, p in cf[:6])
            suffix = f" (+{len(cf) - 6} more)" if len(cf) > 6 else ""
            out.append(f"**File(s):** {listing}{suffix}")
            out.append("")
        if body:
            out.append(body)
            out.append("")
        else:
            out.append("> TODO: 2–4 sentences — what changed, why, any judgment calls.")
            out.append("")

    out.append("## Files touched")
    out.append("")
    out.append("| Domain | Path | Type |")
    out.append("|---|---|---|")
    for status, path in files:
        out.append(f"| {domain_of(path)} | `{path}` | {status} |")
    out.append("")

    out.append("## Verification")
    out.append("")
    out.append("### Automated")
    out.append("```bash")
    out.append("# TODO: replace with the exact commands you ran")
    out.append("# e.g.:")
    out.append("#   bun run type-check")
    out.append("#   bunx vitest run --silent='passed-only' <paths>")
    out.append("```")
    out.append("")
    out.append("### Manual")
    out.append("- [ ] TODO: concrete step — URL or click-path the reviewer can follow.")
    out.append("- [ ] TODO: edge case.")
    out.append("")

    out.append("## Risks & open items")
    out.append("")
    out.append("> TODO: list risks the reviewer would ask about anyway. Pre-answer them.")
    out.append("")

    out.append("## Follow-ups (not in scope)")
    out.append("")
    out.append("> TODO: things you considered but did NOT do in this PR, with reason.")
    out.append("")

    out.append("---")
    out.append("")
    out.append(f"Generated from `{base}..{head}` with run-repo-cleanup/scripts/draft-pr-body.py. "
               "Hand-edit the TODO sections before `gh pr create --body-file`.")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Draft a PR body from a commit range.")
    ap.add_argument("--base", required=True, help="base ref (e.g. main, origin/main)")
    ap.add_argument("--head", default="HEAD", help="head ref (default HEAD)")
    ap.add_argument("--title", default=None, help="PR title (default: most recent commit subject)")
    args = ap.parse_args()

    # Validate we're inside a git repo
    try:
        sh(["git", "rev-parse", "--show-toplevel"])
    except subprocess.CalledProcessError:
        print("not inside a git repository", file=sys.stderr)
        return 2

    try:
        commits = list_commits(args.base, args.head)
    except subprocess.CalledProcessError as e:
        print(f"git log failed: {e.stderr}", file=sys.stderr)
        return 2

    if not commits:
        print(f"no commits between {args.base} and {args.head}", file=sys.stderr)
        return 1

    title = args.title or commits[-1][1]
    files = aggregate_files(commits)
    stats = stats_for(args.base, args.head)
    print(render(title, commits, files, stats, args.base, args.head))
    return 0


if __name__ == "__main__":
    sys.exit(main())
