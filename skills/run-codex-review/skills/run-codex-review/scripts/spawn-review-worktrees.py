#!/usr/bin/env python3
"""Spawn one worktree per branch, push to fork, emit/update the manifest.

For each branch:
  1. Verify the branch exists locally (or create from origin/<branch>).
  2. Create ../<repo>-wt-<slug> if missing; verify clean if pre-existing.
  3. git push -u <remote> <branch>  (refuses if remote != origin).
  4. Append a SPAWNED entry to the manifest.

Default is dry-run. Use --execute to actually create + push.

Usage:
    python3 spawn-review-worktrees.py --branches feat/a feat/b --dry-run
    python3 spawn-review-worktrees.py --branches feat/a feat/b --execute
    python3 spawn-review-worktrees.py --branches feat/a --base main --execute

Exit codes:
    0  all spawned (or pre-existing & clean)
    1  dry-run with actions, OR some pre-existing skipped (warning only)
    2  failure (push failed, branch missing, remote != origin, etc.)
    3  refused due to safety check
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


def get_remote_url(remote: str, root: Path) -> str | None:
    rc, out, _ = sh(["git", "remote", "get-url", remote], cwd=root)
    return out if rc == 0 else None


def extract_owner_repo(url: str) -> str | None:
    if not url:
        return None
    url = url.rstrip("/").removesuffix(".git")
    if url.startswith("git@github.com:"):
        return url.split(":", 1)[1]
    for prefix in ("https://github.com/", "http://github.com/"):
        if url.startswith(prefix):
            return url[len(prefix):]
    return None


def slug(branch: str) -> str:
    return branch.replace("/", "-")


def worktree_path(repo_name: str, branch: str, prefix: str | None) -> str:
    if prefix:
        return f"{prefix}{slug(branch)}"
    return f"../{repo_name}-wt-{slug(branch)}"


def branch_exists_local(branch: str, root: Path) -> bool:
    rc, _, _ = sh(["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=root)
    return rc == 0


def branch_exists_remote(branch: str, remote: str, root: Path) -> bool:
    rc, out, _ = sh(["git", "ls-remote", "--heads", remote, branch], cwd=root)
    return rc == 0 and bool(out.strip())


def worktree_for_branch(branch: str, root: Path) -> str | None:
    rc, out, _ = sh(["git", "worktree", "list", "--porcelain"], cwd=root)
    if rc != 0:
        return None
    cur_path = None
    for line in out.splitlines():
        if line.startswith("worktree "):
            cur_path = line[len("worktree "):]
        elif line.startswith("branch ") and cur_path:
            b = line[len("branch "):].removeprefix("refs/heads/")
            if b == branch:
                return cur_path
    return None


def is_clean(wt_path: str) -> bool:
    rc, out, _ = sh(["git", "status", "--porcelain=1"], cwd=Path(wt_path))
    return rc == 0 and not out.strip()


def head_sha(wt_path: str) -> str:
    rc, out, _ = sh(["git", "rev-parse", "HEAD"], cwd=Path(wt_path))
    return out if rc == 0 else ""


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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_or_init_manifest(path: str, root: Path, base: str, fork_owner_repo: str | None,
                          upstream_owner_repo: str | None) -> dict:
    if os.path.isfile(path):
        try:
            with open(path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "schema_version": 1,
        "repo_root": str(root),
        "base_branch": base,
        "fork_owner_repo": fork_owner_repo,
        "upstream_owner_repo": upstream_owner_repo,
        "created_at": utc_now_iso(),
        "completed_at": None,
        "merge_order": None,
        "branches": [],
    }


def find_or_create_entry(manifest: dict, branch: str) -> dict:
    for entry in manifest["branches"]:
        if entry["branch"] == branch:
            return entry
    entry = {
        "branch": branch,
        "concern_one_liner": None,
        "worktree_path": None,
        "remote": None,
        "head_sha_at_spawn": None,
        "head_sha_current": None,
        "status": "SPAWNED",
        "rounds": 0,
        "last_review_id": None,
        "last_review_at": None,
        "last_classifier_summary": None,
        "subagent_started_at": None,
        "updated_at": utc_now_iso(),
        "terminal_reason": None,
        "backup_ref": None,
        "cleaned_up": False,
        "round_history": [],
    }
    manifest["branches"].append(entry)
    return entry


# ─── Dependency installation per worktree ─────────────────────────────────────

def detect_package_manager(wt: Path) -> tuple[str, list[str]] | None:
    """Detect which package manager the project uses based on lockfile / config.
    Returns (label, install command) or None when no install step is needed.

    Detection order matters when multiple lockfiles coexist (e.g. pnpm + npm) —
    prefer the more specific one. Cargo/Go are no-ops because their toolchains
    handle vendoring transparently.
    """
    if (wt / "pnpm-lock.yaml").is_file():
        return ("pnpm", ["pnpm", "install", "--frozen-lockfile"])
    if (wt / "bun.lockb").is_file() or (wt / "bun.lock").is_file():
        return ("bun", ["bun", "install", "--frozen-lockfile"])
    if (wt / "yarn.lock").is_file():
        return ("yarn", ["yarn", "install", "--frozen-lockfile"])
    if (wt / "package-lock.json").is_file():
        return ("npm", ["npm", "ci"])
    if (wt / "package.json").is_file():
        # No lockfile but a package.json — fall back to plain install
        return ("npm", ["npm", "install"])
    if (wt / "requirements.txt").is_file():
        return ("pip", ["pip", "install", "-r", "requirements.txt"])
    if (wt / "pyproject.toml").is_file() and (wt / "poetry.lock").is_file():
        return ("poetry", ["poetry", "install"])
    if (wt / "pyproject.toml").is_file() and (wt / "uv.lock").is_file():
        return ("uv", ["uv", "sync"])
    if (wt / "Gemfile.lock").is_file():
        return ("bundler", ["bundle", "install"])
    # Cargo, Go modules, etc. handle deps in-toolchain — no install step needed.
    return None


def install_deps(wt: Path) -> tuple[bool, str]:
    """Install dependencies in worktree if a recognized package manager is in
    use. Returns (success, message). success=True when the install ran cleanly
    OR when the project doesn't need an install step (Cargo, Go, etc.).
    """
    detected = detect_package_manager(wt)
    if detected is None:
        return True, "no install step (Cargo / Go / no recognized manifest)"
    label, cmd = detected
    rc, _, err = sh(cmd, cwd=wt)
    if rc == 0:
        return True, f"{label} install ok ({' '.join(cmd)})"
    if rc == 127:
        return False, f"{label} install failed — `{cmd[0]}` not on PATH"
    return False, f"{label} install failed (rc={rc}): {err[:200]}"


def process_branch(branch: str, root: Path, args, manifest: dict) -> tuple[str, str]:
    """Returns (action, message). action ∈ {'spawned', 'reused', 'skipped', 'failed', 'planned'}."""
    repo_name = root.name
    expected_path = worktree_path(repo_name, branch, args.worktree_prefix)
    abs_path = str((root.parent / Path(expected_path).name).resolve()) \
        if expected_path.startswith("../") else str(Path(expected_path).resolve())

    # Existence checks
    has_local = branch_exists_local(branch, root)
    has_remote = branch_exists_remote(branch, args.remote, root)
    if not has_local and not has_remote:
        return "failed", f"branch '{branch}' not found locally or on {args.remote}"

    # Worktree handling
    existing_wt = worktree_for_branch(branch, root)

    if args.dry_run:
        if existing_wt:
            return "planned", f"would reuse existing worktree {existing_wt}; would push -u {args.remote} {branch}"
        if has_local:
            return "planned", f"would create worktree at {abs_path}; push -u {args.remote} {branch}"
        return "planned", f"would create worktree at {abs_path} from {args.remote}/{branch}; push -u"

    # Execute
    if existing_wt:
        if not is_clean(existing_wt):
            return "failed", f"existing worktree {existing_wt} is dirty; refuse to proceed"
        wt = existing_wt
        action = "reused"
    else:
        if has_local:
            cmd = ["git", "worktree", "add", abs_path, branch]
        else:
            cmd = ["git", "worktree", "add", "-b", branch, abs_path, f"{args.remote}/{branch}"]
        rc, _, err = sh(cmd, cwd=root)
        if rc != 0:
            return "failed", f"git worktree add failed: {err}"
        wt = abs_path
        action = "spawned"

    # Push to fork (refuse if remote != origin)
    if args.remote != "origin":
        return "failed", f"refusing to push to remote '{args.remote}' (must be 'origin'); fork-safety"
    rc, _, err = sh(["git", "push", "-u", args.remote, branch], cwd=Path(wt))
    if rc != 0:
        return "failed", f"git push -u {args.remote} {branch} failed: {err}"

    # Optionally install dependencies (--prep-deps) so Phase 3 / Phase 8 don't
    # discover missing node_modules / .venv mid-flight.
    deps_msg = ""
    if args.prep_deps:
        ok, msg = install_deps(Path(wt))
        deps_msg = f"; deps: {msg}"
        if not ok:
            # Surface but do not fail spawn — the worktree itself is valid;
            # the user can install deps manually if the auto-install couldn't.
            return action, f"{action} worktree at {wt}; pushed -u {args.remote} {branch}{deps_msg}"

    # Update manifest
    entry = find_or_create_entry(manifest, branch)
    sha = head_sha(wt)
    entry.update({
        "worktree_path": wt,
        "remote": args.remote,
        "head_sha_at_spawn": sha,
        "head_sha_current": sha,
        "status": "SPAWNED",
        "updated_at": utc_now_iso(),
    })
    return action, f"{action} worktree at {wt}; pushed -u {args.remote} {branch}{deps_msg}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--branches", nargs="+", required=True, help="branches to spawn worktrees for")
    ap.add_argument("--remote", default="origin", help="remote name (must be 'origin'; fork-safety)")
    ap.add_argument("--base", default="main", help="default base branch (recorded in manifest)")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--worktree-prefix", default=None,
                    help="custom worktree path prefix (default: ../<repo>-wt-)")
    ap.add_argument("--prep-deps", action="store_true",
                    help="After creating each worktree, detect the package manager "
                         "(pnpm-lock.yaml, package-lock.json, bun.lockb, yarn.lock, "
                         "requirements.txt, pyproject.toml + poetry.lock/uv.lock, Gemfile.lock) "
                         "and run the corresponding install. Cargo and Go are no-ops. "
                         "Use for any project whose validate command (Phase 3 build, Phase 8 test) "
                         "needs node_modules / .venv / equivalent. If install fails, the worktree "
                         "itself is left intact and a warning is surfaced.")
    ap.add_argument("--dry-run", action="store_true", help="print plan without doing anything")
    ap.add_argument("--execute", action="store_true", help="actually create worktrees and push")
    args = ap.parse_args()

    if not args.dry_run and not args.execute:
        # default to dry-run
        args.dry_run = True

    root = repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    if args.remote != "origin":
        print(f"refusing to spawn against remote '{args.remote}' — fork-safety requires 'origin'", file=sys.stderr)
        return 3

    fork_owner_repo = extract_owner_repo(get_remote_url("origin", root))
    upstream_owner_repo = extract_owner_repo(get_remote_url("upstream", root))

    manifest = load_or_init_manifest(args.manifest, root, args.base, fork_owner_repo, upstream_owner_repo)

    print(f"repo:     {root}")
    print(f"remote:   {args.remote}  ({fork_owner_repo or '?'})")
    print(f"manifest: {args.manifest}  ({'EXECUTE' if args.execute else 'DRY-RUN'})")
    print("")

    actions = []
    failures = 0
    for branch in args.branches:
        action, msg = process_branch(branch, root, args, manifest)
        actions.append((branch, action, msg))
        marker = {
            "spawned": "[DO]",
            "reused":  "[DO]",
            "planned": "[DRY]",
            "failed":  "[FAIL]",
            "skipped": "[SKIP]",
        }.get(action, "[?]")
        print(f"  {marker} {branch}: {msg}")
        if action == "failed":
            failures += 1

    if args.execute and failures == 0:
        atomic_write(args.manifest, json.dumps(manifest, indent=2))
        print("")
        print(f"✓ manifest written: {args.manifest}")
        return 0
    if args.execute and failures > 0:
        # Persist whatever did succeed
        atomic_write(args.manifest, json.dumps(manifest, indent=2))
        print("")
        print(f"✗ {failures} branch(es) failed; manifest reflects partial state", file=sys.stderr)
        return 2
    if args.dry_run:
        print("")
        print("DRY-RUN complete. Re-run with --execute to apply.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
