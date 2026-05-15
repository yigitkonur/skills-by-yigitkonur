#!/usr/bin/env python3
"""audit.py — read-only inspection of orchestrate-codex state.

Subcommands:
  state     manifest + filesystem drift detection (replaces audit-fleet-state.py)
  sizes     batch-mode answer-size audit (replaces audit-sizes.sh)
  worktrees git worktree enumeration with enrichment (replaces list-worktrees.py)

All subcommands are read-only and share the _lib.py infrastructure (Manifest
loading, state-dir resolution, JSON envelope, run-ledger logging).

Exit codes (uniform):
  0  ok, no drift / nothing flagged
  1  actionable (drift found / files below floor / etc.)
  3  environmental error (manifest missing/unreadable, repo not a git repo, etc.)

The legacy scripts (audit-fleet-state.py, audit-sizes.sh, list-worktrees.py)
remain as deprecation shims forwarding here for 1 release; removed in v3.0.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local import (sibling _lib.py)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (
    CONSTANTS,
    Manifest,
    json_envelope,
    log_ledger_line,
    resolve_state_dir,
    workspace_slug_hash,
    STATUS_TERMINAL,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _git(*args: str, cwd: Optional[Path] = None, timeout: float = 10.0) -> subprocess.CompletedProcess:
    """Run git with the given args; capture stdout/stderr. Never raises."""
    return subprocess.run(
        ["git"] + list(args),
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _eprint(*args: Any, **kwargs: Any) -> None:
    print(*args, file=sys.stderr, **kwargs)


# ---------------------------------------------------------------------------
# Subcommand: state (drift detection)
# ---------------------------------------------------------------------------

def cmd_state(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd or os.getcwd()).resolve()
    workspace_root = Path(args.workspace_root or cwd).resolve()
    manifest_path = (
        Path(args.manifest).resolve()
        if args.manifest
        else resolve_state_dir(workspace_root) / "orchestrate-codex" / "manifest.json"
    )

    report: Dict[str, Any] = {
        "manifest_path": str(manifest_path),
        "manifest_present": manifest_path.is_file(),
        "workspace_root": str(workspace_root),
        "workspace_root_source": "flag" if args.workspace_root else "cwd",
        "state_dir": str(resolve_state_dir(workspace_root)),
        "counts": {},
        "drift_total": 0,
        "drift_kinds": [],
        "drift_summary": [],
        "recommendations": [],
        "entries": [],
        "orphan_worktrees": [],
        "actionable": False,
    }

    if not manifest_path.is_file():
        report["actionable"] = True
        report["drift_summary"].append("manifest missing")
        report["recommendations"].append(
            "Run `orchestrate-codex audit --manifest <path>` with the expected manifest location, "
            "or seed a new run via `orchestrate-codex <mode>`."
        )
        # Per KB-002: manifest-missing exits 1 (actionable), not 2.
        return _emit_state(args, report, exit_code=1, error={"code": "manifest_missing", "message": str(manifest_path)})

    try:
        m = Manifest.load_readonly(manifest_path)
    except (ValueError, OSError) as exc:
        report["actionable"] = True
        return _emit_state(args, report, exit_code=3, error={"code": "manifest_unreadable", "message": str(exc)})

    entries = m.data.get("entries", [])
    if not isinstance(entries, list):
        report["actionable"] = True
        return _emit_state(args, report, exit_code=3, error={"code": "manifest_corrupt", "message": "entries[] not a list"})

    # Counts per status
    counts: Dict[str, int] = {}
    for e in entries:
        if not isinstance(e, dict):
            continue
        status = str(e.get("status", "other"))
        counts[status] = counts.get(status, 0) + 1
    report["counts"] = counts

    # Run-id, mode, etc.
    report["manifest_run_id"] = m.data.get("run_id")
    report["manifest_mode"] = m.data.get("mode")
    report["manifest_started_at"] = m.data.get("started_at")
    report["manifest_concurrency_cap"] = m.data.get("concurrency_cap")
    report["manifest_policy"] = m.data.get("policy")
    report["monitor_root"] = m.data.get("monitor_root")

    # Drift detection: per-entry
    stale_threshold = args.stale_minutes * 60
    drift_total = 0
    drift_kinds_set: List[str] = []
    rendered_entries: List[Dict[str, Any]] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        eid = e.get("id")
        status = e.get("status")
        wt_path = e.get("worktree_path")
        log_path = e.get("log_path")
        drift: List[str] = []
        # worktree presence (exec/review modes)
        if wt_path and not Path(wt_path).exists():
            drift.append("worktree_missing")
        # log presence for running/done
        if status == "running":
            if log_path:
                lp = Path(log_path)
                if not lp.exists() or lp.stat().st_size == 0:
                    drift.append("log_missing")
        elif status == "done":
            if log_path:
                lp = Path(log_path)
                if not lp.exists() or lp.stat().st_size == 0:
                    drift.append("log_missing")
        drift_total += len(drift)
        if drift:
            drift_kinds_set.extend(drift)
        rendered_entries.append({
            "id": eid,
            "status": status,
            "drift": drift,
            "drift_kinds": list(drift),
            "worktree_present": Path(wt_path).exists() if wt_path else None,
            "answer_path_source": "manifest" if e.get("answer_path") else None,
        })
    report["entries"] = rendered_entries
    report["drift_total"] = drift_total
    report["drift_kinds"] = sorted(set(drift_kinds_set))
    if drift_total > 0:
        report["drift_summary"].append(f"{drift_total} drift findings across entries")
    report["actionable"] = drift_total > 0

    exit_code = 1 if report["actionable"] else 0
    return _emit_state(args, report, exit_code=exit_code)


def _emit_state(
    args: argparse.Namespace,
    report: Dict[str, Any],
    *,
    exit_code: int,
    error: Optional[Dict[str, Any]] = None,
) -> int:
    if args.json:
        env = json_envelope(
            ok=(exit_code == 0),
            result=report,
            error=error,
        )
        print(json.dumps(env, indent=2, default=str))
    else:
        print(f"manifest: {report['manifest_path']}")
        print(f"manifest_present: {report['manifest_present']}")
        print(f"workspace_root: {report['workspace_root']} (from {report['workspace_root_source']})")
        if report.get("manifest_run_id"):
            print(f"run_id: {report['manifest_run_id']}  mode: {report['manifest_mode']}  started_at: {report['manifest_started_at']}")
        if report.get("counts"):
            cs = report["counts"]
            print("counts: " + "  ".join(f"{k}={v}" for k, v in sorted(cs.items())))
        if report.get("entries"):
            print("entries:")
            for e in report["entries"]:
                marker = "D" if e["status"] == "done" else "R" if e["status"] == "running" else "Q" if e["status"] == "queued" else "F" if e["status"] == "failed" else "?"
                drift_s = ("  [" + ",".join(e["drift_kinds"]) + "]") if e["drift_kinds"] else ""
                print(f"  [{marker}] {e['id']} status={e['status']}{drift_s}")
        if error:
            print(f"error: {error['code']}: {error.get('message','')}", file=sys.stderr)
        if report.get("recommendations"):
            print("recommendations:")
            for r in report["recommendations"]:
                print(f"  - {r}")
        print(f"actionable: {report.get('actionable', False)}")
    return exit_code


# ---------------------------------------------------------------------------
# Subcommand: sizes (batch-mode size audit)
# ---------------------------------------------------------------------------

def cmd_sizes(args: argparse.Namespace) -> int:
    # Resolve answers + runner log paths.
    answers_dir: Optional[Path] = None
    runner_log: Optional[Path] = None
    min_bytes = args.min_bytes if args.min_bytes is not None else CONSTANTS.audit_min_bytes_default

    if args.manifest:
        try:
            m = Manifest.load_readonly(args.manifest)
        except (FileNotFoundError, ValueError, OSError) as exc:
            _eprint(f"audit.py sizes: manifest unreadable: {exc}")
            return 3
        paths = m.data.get("paths", {})
        answers_dir = Path(paths.get("answers_dir") or m.data.get("answers_dir") or "answers")
        rl = paths.get("runner_log")
        if rl:
            runner_log = Path(rl)
        else:
            mr = m.data.get("monitor_root")
            run_id = m.data.get("run_id")
            if mr and run_id:
                runner_log = Path(mr) / "logs" / run_id / "_runner.log"
        if args.answers:
            answers_dir = Path(args.answers)
        if args.log:
            runner_log = Path(args.log)
    else:
        answers_dir = Path(args.answers or "answers")
        runner_log = Path(args.log) if args.log else Path("logs/_runner.log")

    if not answers_dir or not answers_dir.is_dir():
        _eprint(f"audit.py sizes: answers dir not found: {answers_dir}")
        return 3

    md_files = sorted([p for p in answers_dir.glob("*.md") if p.is_file()])
    if not md_files:
        report = {
            "answers_dir": str(answers_dir),
            "runner_log": str(runner_log) if runner_log else None,
            "min_bytes": min_bytes,
            "files": [],
            "stats": {"count": 0},
            "below_floor": [],
            "flagged": False,
        }
        if args.json:
            print(json.dumps(json_envelope(ok=True, result=report), indent=2))
        else:
            print(f"=== Answer file sizes ===")
            print("(no answers yet)")
        return 0

    sizes = [(p.stat().st_size, p.name) for p in md_files]
    sizes.sort()

    # Stats: count, mean, stdev
    byte_values = [s for s, _ in sizes]
    stats = {"count": len(byte_values), "mean": statistics.mean(byte_values) if byte_values else 0}
    if len(byte_values) > 1:
        stats["stdev"] = statistics.stdev(byte_values)

    # Bottom decile
    decile_n = max(1, len(sizes) // 10)
    bottom_decile = sizes[:decile_n]

    # Below floor
    below_floor = [(sz, name) for sz, name in sizes if sz < min_bytes]

    # Runner log counts
    runner_summary: Dict[str, int] = {}
    if runner_log and runner_log.is_file():
        try:
            text = runner_log.read_text(encoding="utf-8", errors="replace")
            for token in ("DONE", "FAIL", "SKIP"):
                runner_summary[token.lower()] = sum(
                    1 for line in text.splitlines() if line.startswith(token)
                )
        except OSError:
            pass

    report = {
        "answers_dir": str(answers_dir),
        "runner_log": str(runner_log) if runner_log else None,
        "min_bytes": min_bytes,
        "files": [{"size": s, "name": n} for s, n in sizes],
        "stats": stats,
        "bottom_decile": [{"size": s, "name": n} for s, n in bottom_decile],
        "below_floor": [{"size": s, "name": n} for s, n in below_floor],
        "runner_summary": runner_summary,
        "flagged": len(below_floor) > 0,
    }

    if args.json:
        print(json.dumps(json_envelope(ok=True, result=report), indent=2))
    else:
        if runner_summary:
            print("=== Runner log summary ===")
            for k, v in sorted(runner_summary.items()):
                print(f"  {k}: {v}")
        else:
            print(f"(no runner log at {runner_log})")
        print()
        print("=== Answer file sizes (bytes, ascending) ===")
        for s, n in sizes:
            print(f"  {s:8d}  {n}")
        print()
        print("=== Stats ===")
        print(f"  count: {stats['count']}")
        print(f"  mean: {stats.get('mean', 0):.1f}")
        if "stdev" in stats:
            print(f"  stdev: {stats['stdev']:.1f}")
        print()
        print(f"=== Bottom decile ({len(bottom_decile)} smallest) ===")
        for s, n in bottom_decile:
            print(f"  {s:8d}  {n}")
        print()
        print(f"=== Below absolute floor (MIN={min_bytes} bytes) ===")
        if below_floor:
            for s, n in below_floor:
                print(f"  {s:8d}  {n}")
            print()
            print("Recommendation:")
            print(f"  mkdir -p {answers_dir}/.prev")
            print(f"  mv {answers_dir}/<name>.md {answers_dir}/.prev/")
            print(f"  JOBS=10 run-batch.sh > {runner_log} 2>&1 &")
        else:
            print("  (none — all answers above floor)")
            print()
            print("All sizes look healthy. No retry needed.")

    return 1 if below_floor else 0


# ---------------------------------------------------------------------------
# Subcommand: worktrees (git worktree enumeration)
# ---------------------------------------------------------------------------

def cmd_worktrees(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd or os.getcwd()).resolve()
    # Locate repo root
    res = _git("rev-parse", "--show-toplevel", cwd=cwd)
    if res.returncode != 0:
        _eprint("audit.py worktrees: not inside a git repository")
        return 3
    repo_root = Path(res.stdout.strip())

    res = _git("worktree", "list", "--porcelain", cwd=repo_root)
    if res.returncode != 0:
        _eprint(f"audit.py worktrees: git worktree list failed: {res.stderr.strip()}")
        return 3

    # Parse porcelain output: blocks separated by blank lines, each with
    # `worktree <path>`, `HEAD <sha>`, optional `branch <ref>`, `bare`, `detached`,
    # `locked`, `prunable`.
    raw_blocks: List[Dict[str, Any]] = []
    block: Dict[str, Any] = {}
    for line in res.stdout.splitlines():
        if not line.strip():
            if block:
                raw_blocks.append(block)
                block = {}
            continue
        parts = line.split(" ", 1)
        key = parts[0]
        val = parts[1] if len(parts) > 1 else True
        block[key] = val
    if block:
        raw_blocks.append(block)

    enriched: List[Dict[str, Any]] = []
    for b in raw_blocks:
        wt_path = b.get("worktree")
        head = b.get("HEAD")
        branch_full = b.get("branch", "")
        branch = branch_full.split("refs/heads/")[-1] if isinstance(branch_full, str) else None
        entry: Dict[str, Any] = {"path": wt_path, "head": head, "branch": branch}
        for flag in ("bare", "detached", "locked", "prunable"):
            if flag in b:
                entry[flag] = True
        # Enrichment when not bare/detached
        if wt_path and not entry.get("bare") and not entry.get("detached"):
            wt = Path(wt_path)
            ws = _git("status", "--porcelain=1", cwd=wt)
            entry["dirty_count"] = (
                len([l for l in ws.stdout.splitlines() if l]) if ws.returncode == 0 else None
            )
            # upstream
            if branch:
                up = _git("rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}", cwd=wt)
                if up.returncode == 0:
                    upstream = up.stdout.strip()
                    entry["upstream"] = upstream
                    unp = _git("rev-list", "--count", f"{upstream}..{branch}", cwd=wt)
                    if unp.returncode == 0:
                        try:
                            entry["unpushed"] = int(unp.stdout.strip())
                        except ValueError:
                            pass
            # commits ahead of origin/main
            cnt = _git("rev-list", "--count", "origin/main..HEAD", cwd=wt)
            if cnt.returncode == 0:
                try:
                    entry["commits_ahead_of_origin_main"] = int(cnt.stdout.strip())
                except ValueError:
                    pass
        enriched.append(entry)

    if args.json:
        env = json_envelope(ok=True, result={"worktrees": enriched, "repo_root": str(repo_root)})
        print(json.dumps(env, indent=2, default=str))
    else:
        if not enriched:
            print("no worktrees (are you inside a git repo?)")
        else:
            print(f"{len(enriched)} worktree(s):")
            for e in enriched:
                head_short = e.get("head", "")[:8] if e.get("head") else ""
                br = e.get("branch") or "(detached)"
                print(f"  • {e['path']}")
                print(f"    branch: {br}  (HEAD {head_short})")
                extras = []
                if e.get("upstream"):
                    extras.append(f"tracks={e['upstream']}")
                if e.get("dirty_count") is not None:
                    extras.append(f"dirty={e['dirty_count']}")
                if e.get("unpushed") is not None:
                    extras.append(f"unpushed={e['unpushed']}")
                if e.get("commits_ahead_of_origin_main") is not None:
                    extras.append(f"ahead_of_main={e['commits_ahead_of_origin_main']}")
                if extras:
                    print(f"    state:  {' · '.join(extras)}")
    return 0


# ---------------------------------------------------------------------------
# argparse + dispatch
# ---------------------------------------------------------------------------

def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audit.py",
        description="Read-only inspection of orchestrate-codex state (state | sizes | worktrees).",
    )
    subs = parser.add_subparsers(dest="subcommand", required=True)

    sp_state = subs.add_parser("state", help="manifest + filesystem drift report")
    sp_state.add_argument("--manifest", help="path to manifest.json (default: state-dir auto-resolution)")
    sp_state.add_argument("--workspace-root", help="workspace root (default: cwd)")
    sp_state.add_argument("--cwd", help="working directory")
    sp_state.add_argument(
        "--stale-minutes",
        type=int,
        default=CONSTANTS.audit_stale_minutes_default,
        help=f"flag entries with no activity for N minutes (default {CONSTANTS.audit_stale_minutes_default})",
    )
    sp_state.add_argument("--json", action="store_true", help="emit machine-readable JSON envelope")
    sp_state.set_defaults(func=cmd_state)

    sp_sizes = subs.add_parser("sizes", help="batch-mode answer-file size audit")
    sp_sizes.add_argument("--manifest", help="path to manifest.json")
    sp_sizes.add_argument("--answers", help="path to answers directory")
    sp_sizes.add_argument("--log", help="path to runner log")
    sp_sizes.add_argument(
        "--min-bytes",
        type=int,
        default=None,
        help=f"floor below which files are flagged (default {CONSTANTS.audit_min_bytes_default})",
    )
    sp_sizes.add_argument("--json", action="store_true", help="emit machine-readable JSON envelope")
    sp_sizes.set_defaults(func=cmd_sizes)

    sp_wt = subs.add_parser("worktrees", help="git worktree enumeration with enrichment")
    sp_wt.add_argument("--cwd", help="working directory (default: $PWD)")
    sp_wt.add_argument("--json", action="store_true", help="emit machine-readable JSON envelope")
    sp_wt.set_defaults(func=cmd_worktrees)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_argparser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
