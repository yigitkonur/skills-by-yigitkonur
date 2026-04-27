#!/usr/bin/env python3
"""Split mixed-concern commits on a branch into granular conventional commits.

Dry-run prints a per-commit split plan based on a domain heuristic. Execute
creates a safety backup ref then drives `git rebase -i <base>` programmatically
via GIT_SEQUENCE_EDITOR. On any conflict or failure, aborts the rebase and
restores from the backup ref.

Refuses --execute on commits already on origin/<branch> unless --allow-published.

Usage:
    python3 redistribute-commits.py --branch <b> --base main           # dry-run plan
    python3 redistribute-commits.py --branch <b> --base main --execute # do the split
    python3 redistribute-commits.py --branch <b> --base main --execute --allow-published

Exit codes:
    0  nothing to split / split succeeded
    1  plan printed (dry-run with actionable splits)
    2  refused (published without --allow-published) or fatal
    3  rebase conflict — aborted and restored from backup
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

EMOJI_FOR = {
    "feat":   "✨",
    "fix":    "🐛",
    "docs":   "📝",
    "refactor": "♻️",
    "test":   "✅",
    "chore":  "🔧",
    "build":  "📦",
    "ci":     "👷",
    "perf":   "⚡",
    "style":  "🎨",
}


def sh(cmd, cwd=None, env=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=False)
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"


def repo_root() -> Path | None:
    rc, out, _ = sh(["git", "rev-parse", "--show-toplevel"])
    return Path(out) if rc == 0 else None


def utc_filesystem_ts() -> str:
    """ISO-ish timestamp safe for ref names."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def slug(branch: str) -> str:
    return branch.replace("/", "-")


def domain_of(path: str) -> tuple[str, str]:
    """Return (domain, conv_commit_type) for a path."""
    p = path.lower()
    if p.endswith(("/agents.md", "/claude.md", "/readme.md", "/contributing.md")) or \
       p in ("agents.md", "claude.md", "readme.md", "contributing.md"):
        return ("docs", "docs")
    parts = path.split("/")
    if not parts:
        return ("root", "chore")
    head = parts[0]
    if head == "src":
        scope = "/".join(parts[:3]) if len(parts) >= 3 else "/".join(parts)
        return (scope or "src", "feat")
    if head == "packages" and len(parts) >= 2:
        return (f"packages/{parts[1]}", "feat")
    if head in ("scripts", "bin"):
        return ("scripts", "chore")
    if head in ("docs",) or path.endswith(".md"):
        return ("docs", "docs")
    if head in ("test", "tests", "__tests__", "spec") or "/test" in p or path.endswith(("_test.py", ".test.ts", ".spec.ts")):
        return ("tests", "test")
    if head in ("locales", "i18n"):
        return ("i18n", "chore")
    if head == ".github":
        return ("ci", "ci")
    if head in ("Makefile", "package.json", "pyproject.toml") or path.endswith((".lock", ".toml", ".yaml", ".yml")):
        return ("build", "build")
    return (head or "root", "chore")


def list_commits(base: str, branch: str, root: Path) -> list[dict]:
    """Return [{sha, subject, parent_count}, ...] for commits in base..branch (oldest first)."""
    rec_sep = "\x1e"; fld_sep = "\x1f"
    fmt = f"%H{fld_sep}%P{fld_sep}%s{rec_sep}"
    rc, raw, _ = sh(["git", "log", "--no-merges", f"--format={fmt}", f"{base}..{branch}"], cwd=root)
    if rc != 0:
        return []
    out = []
    for record in raw.split(rec_sep):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split(fld_sep)
        if len(parts) < 3:
            continue
        sha, parents, subject = parts[0], parts[1].split(), parts[2]
        out.append({"sha": sha, "parents": parents, "subject": subject})
    out.reverse()  # oldest first
    return out


def files_in_commit(sha: str, root: Path) -> list[str]:
    rc, raw, _ = sh(["git", "show", "--name-only", "--format=", sha], cwd=root)
    if rc != 0:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def published_commits(branch: str, root: Path) -> set[str]:
    """SHAs in branch that also exist on origin/<branch>."""
    rc, _, _ = sh(["git", "rev-parse", "--verify", "--quiet", f"origin/{branch}"], cwd=root)
    if rc != 0:
        return set()
    rc, raw, _ = sh(
        ["git", "rev-list", f"origin/{branch}..{branch}", "--reverse"], cwd=root
    )
    if rc != 0:
        return set()
    # rev-list gives ahead-of-origin commits; their negation is "published"
    rc, all_branch, _ = sh(["git", "rev-list", branch, "--max-count=200"], cwd=root)
    if rc != 0:
        return set()
    ahead = {line.strip() for line in raw.splitlines() if line.strip()}
    return {line.strip() for line in all_branch.splitlines() if line.strip() and line.strip() not in ahead}


def plan_for_commit(commit: dict, root: Path) -> dict:
    files = files_in_commit(commit["sha"], root)
    grouped = OrderedDict()
    for f in files:
        domain, conv_type = domain_of(f)
        key = (domain, conv_type)
        grouped.setdefault(key, []).append(f)
    needs_split = len(grouped) >= 2
    groups = []
    for (domain, conv_type), group_files in grouped.items():
        emoji = EMOJI_FOR.get(conv_type, "🔧")
        # Subject is a placeholder; user refines after split
        suggested_subject = f"{emoji} {conv_type}({domain}): split from {commit['sha'][:8]}"
        groups.append({
            "domain": domain,
            "conv_type": conv_type,
            "files": group_files,
            "suggested_subject": suggested_subject,
        })
    return {
        "sha": commit["sha"],
        "subject": commit["subject"],
        "files_total": len(files),
        "domains": [g["domain"] for g in groups],
        "needs_split": needs_split,
        "groups": groups,
    }


def render_plan(branch: str, base: str, plans: list[dict], published: set[str]) -> str:
    lines = []
    lines.append(f"branch:    {branch}")
    lines.append(f"base:      {base}")
    lines.append(f"commits:   {len(plans)}")
    needs = [p for p in plans if p["needs_split"]]
    lines.append(f"needs split: {len(needs)} of {len(plans)}")
    lines.append("")
    for i, p in enumerate(plans, 1):
        flag = " ⚠ MIXED" if p["needs_split"] else ""
        pub = " (published)" if p["sha"] in published else ""
        lines.append(f"{i}. {p['sha'][:10]}  {p['subject']}{pub}{flag}")
        lines.append(f"   files: {p['files_total']}, domains: {p['domains']}")
        if p["needs_split"]:
            lines.append(f"   proposed split into {len(p['groups'])} commits:")
            for g in p["groups"]:
                lines.append(f"     - [{g['conv_type']}({g['domain']})] {len(g['files'])} files")
                lines.append(f"       subject: {g['suggested_subject']}")
                for f in g["files"][:3]:
                    lines.append(f"       • {f}")
                if len(g["files"]) > 3:
                    lines.append(f"       … and {len(g['files']) - 3} more")
        lines.append("")
    return "\n".join(lines)


# ─── Execute mode ────────────────────────────────────────────────────────────

def write_sequence_editor(target_shas: set[str]) -> str:
    """Produce a Python script that rewrites the rebase-todo to mark target SHAs as edit."""
    fd, path = tempfile.mkstemp(prefix="rebase-todo-editor-", suffix=".py")
    os.close(fd)
    targets_repr = repr(sorted(target_shas))
    script = f'''#!/usr/bin/env python3
import sys

target_short = set(t[:7] for t in {targets_repr})

def rewrite(path):
    with open(path) as f:
        lines = f.readlines()
    out = []
    for line in lines:
        s = line.rstrip("\\n")
        if not s or s.startswith("#"):
            out.append(line)
            continue
        parts = s.split(maxsplit=2)
        if len(parts) >= 2 and parts[0] == "pick":
            sha = parts[1]
            if sha[:7] in target_short:
                parts[0] = "edit"
                line = " ".join(parts) + "\\n"
        out.append(line)
    with open(path, "w") as f:
        f.writelines(out)

if __name__ == "__main__":
    rewrite(sys.argv[1])
'''
    with open(path, "w") as f:
        f.write(script)
    os.chmod(path, 0o755)
    return path


def is_rebase_in_progress(root: Path) -> bool:
    rc, git_dir, _ = sh(["git", "rev-parse", "--git-dir"], cwd=root)
    if rc != 0:
        return False
    gd = root / git_dir if not Path(git_dir).is_absolute() else Path(git_dir)
    return (gd / "rebase-merge").is_dir() or (gd / "rebase-apply").is_dir()


def current_rebase_sha(root: Path) -> str | None:
    rc, git_dir, _ = sh(["git", "rev-parse", "--git-dir"], cwd=root)
    if rc != 0:
        return None
    gd = root / git_dir if not Path(git_dir).is_absolute() else Path(git_dir)
    sha_path = gd / "rebase-merge" / "stopped-sha"
    if sha_path.is_file():
        try:
            return sha_path.read_text().strip()
        except OSError:
            return None
    return None


def execute_split(branch: str, base: str, root: Path, plans: list[dict],
                  backup_ref: str) -> tuple[bool, str]:
    """Returns (ok, message)."""
    target_shas = {p["sha"] for p in plans if p["needs_split"]}
    if not target_shas:
        return True, "no commits need splitting"

    # Create backup ref
    rc, _, err = sh(["git", "branch", "--force", backup_ref, branch], cwd=root)
    if rc != 0:
        return False, f"failed to create backup ref: {err}"
    print(f"  ✓ backup ref created: {backup_ref}")

    # Switch to branch (rebase requires branch checkout)
    rc, _, err = sh(["git", "checkout", branch], cwd=root)
    if rc != 0:
        return False, f"git checkout {branch} failed: {err}"

    editor_script = write_sequence_editor(target_shas)
    env = os.environ.copy()
    env["GIT_SEQUENCE_EDITOR"] = f"python3 {editor_script}"
    env["GIT_EDITOR"] = "true"  # for any unintended editor invocation

    try:
        # Start the rebase
        rc, out, err = sh(["git", "rebase", "-i", base], cwd=root, env=env)
        if rc != 0 and not is_rebase_in_progress(root):
            return False, f"git rebase -i failed at start: {err}\n{out}"

        # Loop through stops
        max_iterations = len(target_shas) + 5  # safety bound
        iters = 0
        while is_rebase_in_progress(root):
            iters += 1
            if iters > max_iterations:
                sh(["git", "rebase", "--abort"], cwd=root)
                sh(["git", "reset", "--hard", backup_ref], cwd=root)
                return False, "rebase loop exceeded max iterations; aborted and restored"

            sha = current_rebase_sha(root)
            if not sha:
                # Maybe the rebase stopped at something we didn't expect
                sh(["git", "rebase", "--abort"], cwd=root)
                sh(["git", "reset", "--hard", backup_ref], cwd=root)
                return False, "rebase stopped at unknown point; aborted and restored"

            plan = next((p for p in plans if p["sha"] == sha), None)
            if not plan or not plan["needs_split"]:
                # Shouldn't happen — sequence editor only marks split targets
                rc, _, err = sh(["git", "rebase", "--continue"], cwd=root, env=env)
                if rc != 0:
                    sh(["git", "rebase", "--abort"], cwd=root)
                    sh(["git", "reset", "--hard", backup_ref], cwd=root)
                    return False, f"unexpected rebase stop at {sha[:8]}; aborted: {err}"
                continue

            # Reset the stopped commit to put its changes back into the index
            rc, _, err = sh(["git", "reset", "HEAD~"], cwd=root)
            if rc != 0:
                sh(["git", "rebase", "--abort"], cwd=root)
                sh(["git", "reset", "--hard", backup_ref], cwd=root)
                return False, f"git reset HEAD~ failed at {sha[:8]}: {err}"

            # Stage + commit each group
            for g in plan["groups"]:
                rc, _, err = sh(["git", "add", "--"] + g["files"], cwd=root)
                if rc != 0:
                    sh(["git", "rebase", "--abort"], cwd=root)
                    sh(["git", "reset", "--hard", backup_ref], cwd=root)
                    return False, f"git add failed at {sha[:8]} group {g['domain']}: {err}"
                # Skip if nothing to commit (file already staged elsewhere)
                rc, staged, _ = sh(["git", "diff", "--cached", "--name-only"], cwd=root)
                if rc != 0 or not staged.strip():
                    continue
                rc, _, err = sh(
                    ["git", "commit", "-m", g["suggested_subject"]], cwd=root
                )
                if rc != 0:
                    sh(["git", "rebase", "--abort"], cwd=root)
                    sh(["git", "reset", "--hard", backup_ref], cwd=root)
                    return False, f"git commit failed at {sha[:8]} group {g['domain']}: {err}"

            # Continue the rebase
            rc, _, err = sh(["git", "rebase", "--continue"], cwd=root, env=env)
            if rc != 0:
                sh(["git", "rebase", "--abort"], cwd=root)
                sh(["git", "reset", "--hard", backup_ref], cwd=root)
                return False, f"git rebase --continue failed after splitting {sha[:8]}: {err}"

        return True, f"split complete; backup at {backup_ref}"
    finally:
        try:
            os.unlink(editor_script)
        except OSError:
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--base", default="main")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--allow-published", action="store_true",
                    help="allow rewriting commits already on origin/<branch> (DANGEROUS)")
    ap.add_argument("--backup-prefix", default="backup/codex-review/",
                    help="prefix for the safety backup ref")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    # Verify branch exists locally
    rc, _, _ = sh(["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{args.branch}"], cwd=root)
    if rc != 0:
        print(f"branch '{args.branch}' not found locally", file=sys.stderr)
        return 2

    commits = list_commits(args.base, args.branch, root)
    if not commits:
        print(f"no commits between {args.base} and {args.branch}; nothing to split")
        return 0

    plans = [plan_for_commit(c, root) for c in commits]
    published = published_commits(args.branch, root)

    if args.json:
        out = {
            "branch": args.branch, "base": args.base,
            "commits": plans, "published": sorted(published),
        }
        print(json.dumps(out, indent=2))
    else:
        print(render_plan(args.branch, args.base, plans, published))

    needs_split = [p for p in plans if p["needs_split"]]
    if not needs_split:
        if not args.json:
            print("→ no commits need splitting")
        return 0

    # Refuse published without --allow-published
    published_to_split = [p for p in needs_split if p["sha"] in published]
    if published_to_split and args.execute and not args.allow_published:
        print("", file=sys.stderr)
        print(f"✗ refusing to --execute: {len(published_to_split)} target commit(s) are already on origin/{args.branch}.", file=sys.stderr)
        print("   Either: (a) add --allow-published (DANGEROUS, requires force-push to origin),", file=sys.stderr)
        print("   or (b) use the cherry-pick-into-new-branch pattern from references/commit-redistribution.md.", file=sys.stderr)
        return 2

    if not args.execute:
        if not args.json:
            print(f"→ {len(needs_split)} commit(s) flagged for split. Re-run with --execute to perform the split.")
        return 1

    # EXECUTE
    backup_ref = f"{args.backup_prefix}{slug(args.branch)}/{utc_filesystem_ts()}"
    print("")
    print("EXECUTING split...")
    ok, msg = execute_split(args.branch, args.base, root, plans, backup_ref)
    print("")
    if ok:
        print(f"✓ {msg}")
        print(f"  backup ref: {backup_ref}  (recover: git reset --hard {backup_ref})")
        return 0
    print(f"✗ {msg}", file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main())
