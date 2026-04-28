#!/usr/bin/env python3
"""Layer review-loop checks on top of run-repo-cleanup's audit-state.py.

Detects:
  - Orphan worktrees matching <repo>-wt-* that aren't in the manifest.
  - Stale or missing manifest at the repo-local default path.
  - Round logs whose mtime is older than --stale-minutes.
  - In-flight Codex jobs from prior runs (best-effort via manifest entries).

Manifest defaults to the repo-local path `<repo-root>/.codex-review-manifest.json`
(matches the wrappers). Override with `--manifest <path>` if you've placed the
manifest elsewhere.

Usage:
    python3 audit-review-state.py                                 # repo-local defaults
    python3 audit-review-state.py --json
    python3 audit-review-state.py --manifest /custom/path.json
    python3 audit-review-state.py --rounds-dir /custom/rounds-dir/
    python3 audit-review-state.py --stale-minutes 60

Exit codes:
    0  CLEAN (base audit exit 0 AND no review-loop debris)
    1  ACTIONABLE (base audit exit 1 OR review-loop debris present)
    2  not in a git repo / fatal
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Defaults are computed lazily from the repo root when args are parsed —
# see _resolve_default_paths() below. The /tmp legacy paths are checked
# only as a fallback for older skill versions' state files.
LEGACY_TMP_MANIFEST = "/tmp/codex-review-manifest.json"
LEGACY_TMP_ROUNDS_DIR = "/tmp/codex-review-rounds/"
DEFAULT_STALE_MINUTES = 60
TERMINAL_STATES = {"DONE", "CAP-REACHED", "BLOCKED", "FAILED"}


def sh(cmd, cwd=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"


def find_repo_root() -> Path | None:
    rc, out, _ = sh(["git", "rev-parse", "--show-toplevel"])
    return Path(out) if rc == 0 else None


def find_run_repo_cleanup_audit() -> Path | None:
    """Locate run-repo-cleanup/scripts/audit-state.py via best-effort search."""
    here = Path(__file__).resolve()
    # sibling skill: skills/run-codex-review/scripts/audit-review-state.py
    skills_dir = here.parent.parent.parent
    candidate = skills_dir / "run-repo-cleanup" / "scripts" / "audit-state.py"
    if candidate.is_file():
        return candidate
    # fallback well-known install paths
    for path in [
        Path.home() / ".agents" / "skills" / "run-repo-cleanup" / "scripts" / "audit-state.py",
        Path.home() / "dev-test" / "dotfiles" / "agents" / ".agents" / "skills"
        / "run-repo-cleanup" / "scripts" / "audit-state.py",
    ]:
        if path.is_file():
            return path
    return None


def list_worktrees(root: Path) -> list[dict]:
    rc, out, _ = sh(["git", "worktree", "list", "--porcelain"], cwd=root)
    if rc != 0:
        return []
    trees, cur = [], {}
    for line in out.splitlines():
        if not line:
            if cur:
                trees.append(cur); cur = {}
            continue
        if line.startswith("worktree "):
            cur["path"] = line[len("worktree "):]
        elif line.startswith("HEAD "):
            cur["head"] = line[len("HEAD "):]
        elif line.startswith("branch "):
            cur["branch"] = line[len("branch "):].removeprefix("refs/heads/")
    if cur:
        trees.append(cur)
    return trees


def detect_review_worktrees(root: Path, repo_name: str) -> list[dict]:
    """Worktrees whose path basename matches the <repo>-wt-* pattern."""
    pattern = re.compile(rf"{re.escape(repo_name)}-wt-")
    return [
        wt for wt in list_worktrees(root)
        if pattern.search(Path(wt.get("path", "")).name)
    ]


def load_manifest(path: str) -> tuple[dict | None, str | None]:
    if not os.path.isfile(path):
        return None, None
    try:
        with open(path) as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"malformed JSON: {e}"
    except OSError as e:
        return None, f"unreadable: {e}"


def stale_round_logs(rounds_dir: str, stale_minutes: int) -> list[dict]:
    if not os.path.isdir(rounds_dir):
        return []
    now = time.time()
    cutoff = stale_minutes * 60
    stale = []
    for entry in sorted(os.listdir(rounds_dir)):
        if not entry.endswith(".json"):
            continue
        full = os.path.join(rounds_dir, entry)
        try:
            age = now - os.path.getmtime(full)
            if age > cutoff:
                stale.append({
                    "file": entry,
                    "age_minutes": int(age / 60),
                })
        except OSError:
            pass
    return stale


def in_flight_codex_jobs(manifest: dict | None) -> list[dict]:
    """Manifest entries with last_review_id but a non-terminal status."""
    if not manifest or "branches" not in manifest:
        return []
    in_flight = []
    for entry in manifest.get("branches", []):
        status = entry.get("status", "")
        last_review = entry.get("last_review_id")
        if last_review and status not in TERMINAL_STATES:
            in_flight.append({
                "branch": entry.get("branch"),
                "review_id": last_review,
                "rounds": entry.get("rounds"),
                "status": status,
                "last_review_at": entry.get("last_review_at"),
            })
    return in_flight


def build_report(root: Path, args) -> dict:
    repo_name = root.name
    review_wts = detect_review_worktrees(root, repo_name)
    manifest, manifest_err = load_manifest(args.manifest)
    stale_logs = stale_round_logs(args.rounds_dir, args.stale_minutes)
    in_flight = in_flight_codex_jobs(manifest)

    manifest_paths = set()
    if manifest and "branches" in manifest:
        manifest_paths = {e.get("worktree_path") for e in manifest["branches"]}
    orphan_wts = [
        wt for wt in review_wts
        if wt.get("path") and wt["path"] not in manifest_paths
    ]

    return {
        "repo_root": str(root),
        "repo_name": repo_name,
        "review_worktrees_total": len(review_wts),
        "review_worktrees": review_wts,
        "orphan_worktrees": orphan_wts,
        "manifest_path": args.manifest,
        "manifest_present": manifest is not None,
        "manifest_error": manifest_err,
        "manifest_branch_count": len(manifest.get("branches", [])) if manifest else 0,
        "rounds_dir": args.rounds_dir,
        "stale_round_logs": stale_logs,
        "in_flight_codex_jobs": in_flight,
    }


def actionable(report: dict, base_audit_actionable: bool) -> bool:
    if base_audit_actionable:
        return True
    if report["manifest_error"]:
        return True
    if report["orphan_worktrees"]:
        return True
    if report["stale_round_logs"]:
        return True
    if report["in_flight_codex_jobs"]:
        return True
    return False


def render(report: dict, audit_output: str, audit_rc: int) -> str:
    lines = []
    lines.append("─" * 64)
    lines.append("BASE AUDIT (run-repo-cleanup/scripts/audit-state.py)")
    lines.append("─" * 64)
    if audit_output:
        lines.append(audit_output)
    else:
        lines.append("(audit-state.py not found — review-loop checks only)")
    lines.append("")
    lines.append("─" * 64)
    lines.append("REVIEW-LOOP CHECKS")
    lines.append("─" * 64)

    lines.append(f"manifest:         {report['manifest_path']}")
    if report["manifest_error"]:
        lines.append(f"  ⚠  {report['manifest_error']}")
    elif report["manifest_present"]:
        lines.append(f"  present, {report['manifest_branch_count']} branch entries")
    else:
        lines.append("  absent (clean — no prior session debris)")

    lines.append(f"review worktrees: {report['review_worktrees_total']}")
    for wt in report["review_worktrees"]:
        lines.append(f"  • {wt.get('path')}  @ {wt.get('branch', '?')}")

    if report["orphan_worktrees"]:
        lines.append("")
        lines.append(f"⚠  ORPHAN worktrees (in fs, not in manifest): {len(report['orphan_worktrees'])}")
        for wt in report["orphan_worktrees"]:
            lines.append(f"  • {wt.get('path')}  @ {wt.get('branch', '?')}")
        lines.append("    Recommend: cleanup-worktrees.py --execute (use --force-abandon if unmerged)")

    if report["stale_round_logs"]:
        lines.append("")
        lines.append(f"⚠  STALE round logs (older than threshold): {len(report['stale_round_logs'])}")
        for log in report["stale_round_logs"]:
            lines.append(f"  • {log['file']}  ({log['age_minutes']}m old)")

    if report["in_flight_codex_jobs"]:
        lines.append("")
        lines.append(f"⚠  IN-FLIGHT Codex jobs (non-terminal status w/ review id): {len(report['in_flight_codex_jobs'])}")
        for job in report["in_flight_codex_jobs"]:
            lines.append(
                f"  • {job['branch']}  review={job['review_id']}  "
                f"status={job['status']}  rounds={job['rounds']}"
            )
        lines.append("    Recommend: query each with `codex review --status <id>`")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default=None,
                    help="Path to manifest. Default: <repo-root>/.codex-review-manifest.json (repo-local).")
    ap.add_argument("--rounds-dir", default=None,
                    help="Path to round-logs dir. Default: <repo-root>/.codex-review-rounds/")
    ap.add_argument("--stale-minutes", type=int, default=DEFAULT_STALE_MINUTES)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = find_repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    # Repo-local defaults (matches the wrappers); fall back to legacy /tmp paths
    # only if a stale manifest exists there.
    if args.manifest is None:
        repo_local = str(root / ".codex-review-manifest.json")
        if Path(repo_local).is_file() or not Path(LEGACY_TMP_MANIFEST).is_file():
            args.manifest = repo_local
        else:
            args.manifest = LEGACY_TMP_MANIFEST  # legacy, surface as actionable
    if args.rounds_dir is None:
        repo_local_rounds = str(root / ".codex-review-rounds")
        if Path(repo_local_rounds).is_dir() or not Path(LEGACY_TMP_ROUNDS_DIR).is_dir():
            args.rounds_dir = repo_local_rounds
        else:
            args.rounds_dir = LEGACY_TMP_ROUNDS_DIR

    audit_path = find_run_repo_cleanup_audit()
    audit_output, audit_rc = "", 0
    if audit_path:
        rc, out, _ = sh(["python3", str(audit_path)], cwd=root)
        audit_output, audit_rc = out, rc
    base_actionable = audit_rc == 1

    report = build_report(root, args)
    is_actionable = actionable(report, base_actionable)

    if args.json:
        report["base_audit_exit"] = audit_rc
        report["base_audit_output"] = audit_output
        report["actionable"] = is_actionable
        print(json.dumps(report, indent=2, default=str))
    else:
        print(render(report, audit_output, audit_rc))
        if is_actionable:
            print("→ ACTIONABLE")
        else:
            print("→ CLEAN")

    return 1 if is_actionable else 0


if __name__ == "__main__":
    sys.exit(main())
