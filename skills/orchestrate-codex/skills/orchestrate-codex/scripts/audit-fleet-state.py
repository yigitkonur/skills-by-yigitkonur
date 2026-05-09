#!/usr/bin/env python3
"""Read-only state dump for an orchestrate-codex run.

Surfaces drift between manifest.status and filesystem reality:
  - per-entry: worktree exists?, log file exists & growing?, answer file size,
    codex-companion job correlation (jobId, status, pid alive, stale).
  - top-level: orphan worktrees on disk that the manifest doesn't list,
    stale round logs (review mode), in-flight pid liveness summary.

Read-only. Never modifies state. The companion script for mutations is
manifest-update.py (entry/top updates).

Usage:
    audit-fleet-state.py --manifest <path>
    audit-fleet-state.py --manifest <path> --json
    audit-fleet-state.py --manifest <path> --stale-minutes 30
    audit-fleet-state.py --manifest <path> --workspace-root /repo

Exit codes:
    0  CLEAN   — manifest matches reality, no drift
    1  ACTIONABLE — drift detected (orphans, stale logs, dead pids w/ running)
    2  Manifest missing or unreadable
    3  Environmental error (permission denied, etc)
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

DEFAULT_STALE_MINUTES = 30


def sh(cmd: list[str], cwd: Path | None = None, timeout: int | None = 10) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.rstrip("\n"), proc.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "command timed out"


def find_repo_root(start: Path) -> Path | None:
    rc, out, _ = sh(["git", "rev-parse", "--show-toplevel"], cwd=start)
    return Path(out) if rc == 0 else None


def workspace_slug_hash(workspace_root: Path) -> tuple[str, str]:
    """Replicate codex-companion state.mjs:resolveStateDir() slug+hash.

    Mirrors Node's `fs.realpathSync.native(workspaceRoot)` semantics: if the
    path resolves (exists), use the canonical form; otherwise fall back to the
    raw input. Node's API throws on missing paths and the JS code catches.

    slug = sanitize(basename(workspace_root)) — replace non [A-Za-z0-9._-]
            runs with '-', strip leading/trailing '-', empty → 'workspace'.
    hash = first 16 hex chars of sha256(canonical_or_raw).
    """
    raw = str(workspace_root)
    try:
        canonical = os.path.realpath(raw, strict=True)
    except OSError:
        # Path does not exist or is unreadable — Node's `fs.realpathSync.native`
        # throws here and the JS `catch {}` falls back to the raw input.
        canonical = raw
    base = os.path.basename(raw) or "workspace"
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", base)
    slug = slug.strip("-") or "workspace"
    hash_hex = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return slug, hash_hex


def codex_companion_state_dir(workspace_root: Path) -> Path:
    """Where codex-companion writes state.json + jobs/<id>.json.

    Mirrors state.mjs exactly: $CLAUDE_PLUGIN_DATA/state/<slug>-<hash>/ if
    CLAUDE_PLUGIN_DATA is set; else $TMPDIR/codex-companion/<slug>-<hash>/.
    """
    slug, hash_hex = workspace_slug_hash(workspace_root)
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        return Path(plugin_data) / "state" / f"{slug}-{hash_hex}"
    import tempfile
    return Path(tempfile.gettempdir()) / "codex-companion" / f"{slug}-{hash_hex}"


def load_manifest(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        with path.open() as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def list_worktree_paths(repo_root: Path) -> list[str]:
    rc, out, _ = sh(["git", "worktree", "list", "--porcelain"], cwd=repo_root)
    if rc != 0:
        return []
    paths = []
    for line in out.splitlines():
        if line.startswith("worktree "):
            paths.append(line[len("worktree "):])
    return paths


def pid_alive(pid: Any) -> bool | None:
    """True if pid alive, False if dead, None if pid is unknown/invalid."""
    if pid is None:
        return None
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return None
    if pid_int <= 0:
        return None
    try:
        os.kill(pid_int, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists, but not ours — still alive
        return True
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False
        return None


def file_size_or_none(path: str | None) -> int | None:
    if not path:
        return None
    try:
        return os.path.getsize(path)
    except OSError:
        return None


def file_mtime_or_none(path: str | None) -> float | None:
    if not path:
        return None
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def load_codex_companion_jobs(state_dir: Path) -> dict[str, dict]:
    """Load all jobs/<id>.json under codex-companion's state dir, keyed by jobId."""
    jobs_dir = state_dir / "jobs"
    if not jobs_dir.is_dir():
        return {}
    out: dict[str, dict] = {}
    try:
        for entry in jobs_dir.iterdir():
            if not entry.is_file() or not entry.name.endswith(".json"):
                continue
            try:
                with entry.open() as f:
                    payload = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            jid = payload.get("id") or entry.stem
            out[jid] = payload
    except OSError:
        pass
    return out


def _resolve_answer_fallback(entry: dict, manifest_mode: str | None,
                             workspace_root: Path, monitor_root: str | None) -> str | None:
    """Filesystem-fallback for batch entries with null `answer_path`.

    When mode is batch and the manifest entry doesn't carry an answer_path,
    look at <workspace_root>/answers/<slug>.md (the run-batch.sh default).
    Returns the absolute path if a non-empty file exists; else None.
    """
    if manifest_mode != "batch":
        return None
    if entry.get("answer_path"):
        return None
    slug = entry.get("slug") or entry.get("id")
    if not slug:
        return None
    candidates = []
    candidates.append(workspace_root / "answers" / f"{slug}.md")
    if monitor_root:
        candidates.append(Path(monitor_root) / "answers" / f"{slug}.md")
    for cand in candidates:
        try:
            if cand.is_file() and cand.stat().st_size > 0:
                return str(cand)
        except OSError:
            continue
    return None


def assess_entry(
    entry: dict,
    cc_jobs: dict[str, dict],
    fs_worktree_set: set[str],
    now: float,
    stale_secs: int,
    manifest_mode: str | None = None,
    workspace_root: Path | None = None,
    monitor_root: str | None = None,
) -> dict:
    """Build per-entry drift annotations. Read-only; doesn't mutate `entry`.

    `drift` is a list of human strings. `drift_kinds` is a parallel list of
    stable slugs (e.g. "worktree_missing") for tooling.
    """
    annotation: dict[str, Any] = {
        "id": entry.get("id"),
        "slug": entry.get("slug"),
        "status": entry.get("status"),
        "attempts": entry.get("attempts"),
        "exit_code": entry.get("exit_code"),
        "drift": [],
        "drift_kinds": [],
    }

    wt = entry.get("worktree_path") or ""
    if wt:
        annotation["worktree_path"] = wt
        annotation["worktree_present"] = os.path.isdir(wt)
        annotation["worktree_in_git"] = wt in fs_worktree_set
        # Drift: worktree_path is set in manifest but the directory doesn't
        # exist on disk AND git doesn't know about it. This is the most
        # common operational drift (worktree deleted out from under us).
        if (not annotation["worktree_present"]) and (not annotation["worktree_in_git"]):
            msg = (
                f"worktree_path set but missing on disk and not in "
                f"`git worktree list`: {wt}"
            )
            annotation["drift"].append(msg)
            annotation["drift_kinds"].append("worktree_missing")
        elif annotation["worktree_present"] and not annotation["worktree_in_git"]:
            msg = "worktree_path exists on disk but not registered with git"
            annotation["drift"].append(msg)
            annotation["drift_kinds"].append("worktree_unregistered")
    else:
        annotation["worktree_present"] = None
        annotation["worktree_in_git"] = None

    log_path = entry.get("log_path") or ""
    annotation["log_path"] = log_path
    annotation["log_size"] = file_size_or_none(log_path)
    annotation["log_mtime"] = file_mtime_or_none(log_path)
    if annotation["log_mtime"] is not None:
        annotation["log_age_seconds"] = int(now - annotation["log_mtime"])
    else:
        annotation["log_age_seconds"] = None

    answer_path = entry.get("answer_path") or ""
    answer_fallback_used = False
    if not answer_path and workspace_root is not None:
        fb = _resolve_answer_fallback(entry, manifest_mode, workspace_root, monitor_root)
        if fb:
            answer_path = fb
            answer_fallback_used = True
    annotation["answer_path"] = answer_path
    annotation["answer_size"] = file_size_or_none(answer_path) if answer_path else None
    annotation["answer_path_source"] = "fallback" if answer_fallback_used else "manifest"

    jsonl_path = entry.get("jsonl_path") or ""
    annotation["jsonl_path"] = jsonl_path
    annotation["jsonl_size"] = file_size_or_none(jsonl_path)

    # Cross-correlate with codex-companion job records via codex_session_id (=jobId).
    sid = entry.get("codex_session_id") or entry.get("codex_thread_id")
    annotation["codex_session_id"] = entry.get("codex_session_id")
    annotation["codex_thread_id"] = entry.get("codex_thread_id")
    if sid and sid in cc_jobs:
        cc = cc_jobs[sid]
        annotation["cc_status"] = cc.get("status")
        annotation["cc_phase"] = cc.get("phase")
        annotation["cc_pid"] = cc.get("pid")
        annotation["cc_pid_alive"] = pid_alive(cc.get("pid"))
        annotation["cc_updated_at"] = cc.get("updatedAt")
    else:
        annotation["cc_status"] = None
        annotation["cc_pid"] = None
        annotation["cc_pid_alive"] = None

    # Drift detection rules
    status = entry.get("status")
    if status == "running":
        if annotation["cc_pid"] is not None and annotation["cc_pid_alive"] is False:
            annotation["drift"].append("status=running but codex-companion pid is dead")
            annotation["drift_kinds"].append("pid_dead")
        if annotation["log_age_seconds"] is not None and annotation["log_age_seconds"] > stale_secs:
            annotation["drift"].append(
                f"status=running but log is stale ({annotation['log_age_seconds']}s)"
            )
            annotation["drift_kinds"].append("log_stale")
        if log_path and annotation["log_size"] in (None, 0):
            annotation["drift"].append("status=running but log is missing or empty")
            annotation["drift_kinds"].append("log_missing")
    elif status == "done":
        if log_path and not annotation["log_size"]:
            annotation["drift"].append("status=done but log file missing or empty")
            annotation["drift_kinds"].append("log_missing")
        if answer_path and (annotation["answer_size"] is None or annotation["answer_size"] == 0):
            annotation["drift"].append("status=done but answer file missing or empty")
            annotation["drift_kinds"].append("answer_missing")
        # Batch-mode advisory: if the entry's answer_path was null in the
        # manifest but a filesystem-fallback turned up evidence, surface it
        # as a soft drift so the operator knows the manifest is sparse.
        if (manifest_mode == "batch" and not entry.get("answer_path")
                and answer_fallback_used and annotation["answer_size"]):
            annotation["drift"].append(
                f"manifest answer_path null but found {answer_path} "
                f"({annotation['answer_size']}B) on filesystem fallback"
            )
            annotation["drift_kinds"].append("answer_path_null_with_fs_evidence")
    elif status == "failed":
        if entry.get("exit_code") in (None, 0):
            annotation["drift"].append("status=failed but exit_code is 0/null")
            annotation["drift_kinds"].append("failed_without_exit_code")
    elif status == "queued":
        if log_path and annotation["log_size"] not in (None, 0):
            annotation["drift"].append("status=queued but log file already has content")
            annotation["drift_kinds"].append("queued_with_log_content")

    return annotation


def detect_orphan_worktrees(
    fs_worktrees: list[str],
    manifest: dict,
    repo_name: str,
) -> list[str]:
    """Worktree paths on disk matching the orchestrate-codex naming pattern
    (../<repo>-wt-<mode>-<slug>) that are not referenced by any manifest entry.
    """
    if not manifest or not isinstance(manifest.get("entries"), list):
        return []
    manifest_paths = {
        e.get("worktree_path") or ""
        for e in manifest["entries"]
        if isinstance(e, dict)
    }
    pattern = re.compile(rf"{re.escape(repo_name)}-wt-")
    out = []
    for path in fs_worktrees:
        name = os.path.basename(path)
        if pattern.search(name) and path not in manifest_paths:
            out.append(path)
    return out


def build_report(args, manifest: dict | None) -> dict:
    # Workspace-root resolution priority:
    #   1. explicit --workspace-root flag
    #   2. manifest's recorded `workspace_root` field
    #   3. cwd
    # NOTE: do NOT pre-resolve symlinks (no `.resolve()`). The slug-hash
    # function below mirrors codex-companion's `fs.realpathSync.native` +
    # JS-side catch fallback exactly; pre-resolving here would diverge for
    # symlinked roots like /tmp on macOS or for missing paths.
    workspace_root_source = "cwd"
    if args.workspace_root:
        workspace_root = Path(args.workspace_root)
        workspace_root_source = "flag"
    elif manifest and isinstance(manifest.get("workspace_root"), str) and manifest["workspace_root"]:
        workspace_root = Path(manifest["workspace_root"])
        workspace_root_source = "manifest"
    else:
        workspace_root = Path.cwd()

    repo_root = find_repo_root(workspace_root)
    repo_name = repo_root.name if repo_root else workspace_root.name

    cc_state_dir = codex_companion_state_dir(repo_root if repo_root else workspace_root)
    cc_jobs = load_codex_companion_jobs(cc_state_dir)

    fs_worktrees = list_worktree_paths(repo_root) if repo_root else []
    fs_worktree_set = set(fs_worktrees)

    now = time.time()
    stale_secs = args.stale_minutes * 60

    manifest_mode = manifest.get("mode") if manifest else None
    monitor_root = manifest.get("monitor_root") if manifest else None

    entries_report = []
    if manifest and isinstance(manifest.get("entries"), list):
        for entry in manifest["entries"]:
            if isinstance(entry, dict):
                entries_report.append(
                    assess_entry(
                        entry, cc_jobs, fs_worktree_set, now, stale_secs,
                        manifest_mode=manifest_mode,
                        workspace_root=workspace_root,
                        monitor_root=monitor_root,
                    )
                )

    orphans = detect_orphan_worktrees(fs_worktrees, manifest or {}, repo_name)

    counts = {
        "queued": 0, "running": 0, "done": 0,
        "failed": 0, "skipped": 0, "rescued": 0, "other": 0,
    }
    for er in entries_report:
        s = er.get("status")
        if s in counts:
            counts[s] += 1
        else:
            counts["other"] += 1

    drift_total = sum(len(e.get("drift") or []) for e in entries_report)

    # Aggregate drift kinds for the summary line + recommendations.
    drift_kind_counts: dict[str, int] = {}
    for er in entries_report:
        for k in er.get("drift_kinds") or []:
            drift_kind_counts[k] = drift_kind_counts.get(k, 0) + 1

    drift_summary = _format_drift_summary(drift_kind_counts, len(orphans))
    recommendations = _build_recommendations(drift_kind_counts, len(orphans),
                                             counts["running"])

    return {
        "manifest_path": str(args.manifest),
        "manifest_present": manifest is not None,
        "workspace_root": str(workspace_root),
        "workspace_root_source": workspace_root_source,
        "repo_root": str(repo_root) if repo_root else None,
        "repo_name": repo_name,
        "codex_companion_state_dir": str(cc_state_dir),
        "codex_companion_state_present": cc_state_dir.is_dir(),
        "codex_companion_jobs_known": len(cc_jobs),
        "fs_worktree_count": len(fs_worktrees),
        "fs_worktrees": fs_worktrees,
        "orphan_worktrees": orphans,
        "manifest_run_id": manifest.get("run_id") if manifest else None,
        "manifest_mode": manifest_mode,
        "manifest_started_at": manifest.get("started_at") if manifest else None,
        "manifest_concurrency_cap": manifest.get("concurrency_cap") if manifest else None,
        "manifest_policy": manifest.get("policy") if manifest else None,
        "monitor_root": monitor_root,
        "counts": counts,
        "entries": entries_report,
        "drift_total": drift_total,
        "drift_kinds": drift_kind_counts,
        "drift_summary": drift_summary,
        "recommendations": recommendations,
    }


def _format_drift_summary(drift_kind_counts: dict[str, int], orphans_count: int) -> str:
    """Compose the one-line drift summary."""
    if not drift_kind_counts and not orphans_count:
        return "no drift detected"
    parts = []
    label_map = {
        "worktree_missing": "missing worktree",
        "worktree_unregistered": "unregistered worktree",
        "log_stale": "stale running log",
        "log_missing": "missing/empty log",
        "pid_dead": "dead pid (status=running)",
        "answer_missing": "missing/empty answer",
        "answer_path_null_with_fs_evidence": "answer_path null with fs evidence",
        "failed_without_exit_code": "failed w/o exit_code",
        "queued_with_log_content": "queued but log non-empty",
    }
    for kind, count in sorted(drift_kind_counts.items()):
        label = label_map.get(kind, kind)
        parts.append(f"{count} {label}")
    if orphans_count:
        parts.append(f"{orphans_count} orphan worktree(s)")
    return "Drift summary: " + "; ".join(parts) + "."


def _build_recommendations(drift_kind_counts: dict[str, int],
                           orphans_count: int, running_count: int) -> list[str]:
    """Per drift kind, suggest the next action. One string per recommendation."""
    recs: list[str] = []
    if drift_kind_counts.get("worktree_missing"):
        recs.append(
            "Run rescue mode for entries with `worktree_missing` drift "
            "(manifest still says active but worktree is gone)."
        )
    if drift_kind_counts.get("pid_dead") or drift_kind_counts.get("log_stale"):
        recs.append(
            "Run `python3 scripts/rescue-detect.py --manifest <m> --json` and "
            "redispatch the stale/dead-pid entries via rescue mode."
        )
    if drift_kind_counts.get("answer_missing"):
        recs.append(
            "Flip status=failed via `manifest-update.py --set status=failed` "
            "for done-without-answer entries; then rescue."
        )
    if drift_kind_counts.get("answer_path_null_with_fs_evidence"):
        recs.append(
            "Update batch entries' answer_path via "
            "`manifest-update.py --set answer_path=<found-path>` so future "
            "audits see the evidence."
        )
    if drift_kind_counts.get("failed_without_exit_code"):
        recs.append(
            "Fill in `exit_code` on failed entries (manifest-update.py); "
            "audit treats null exit_code on failed status as drift."
        )
    if orphans_count:
        recs.append(
            f"{orphans_count} orphan worktree(s) on disk are not in the "
            "manifest. Inspect with `list-worktrees.py` before deciding to "
            "remove them."
        )
    return recs


def actionable(report: dict) -> bool:
    if not report["manifest_present"]:
        return True
    if report["orphan_worktrees"]:
        return True
    if report["drift_total"] > 0:
        return True
    return False


def render(report: dict) -> str:
    lines: list[str] = []
    lines.append("─" * 64)
    lines.append("orchestrate-codex fleet state")
    lines.append("─" * 64)
    lines.append(f"manifest:        {report['manifest_path']}")
    lines.append(f"  present:       {report['manifest_present']}")
    if report["manifest_present"]:
        lines.append(f"  run_id:        {report['manifest_run_id']}")
        lines.append(f"  mode:          {report['manifest_mode']}")
        lines.append(f"  started_at:    {report['manifest_started_at']}")
        lines.append(f"  concurrency:   {report['manifest_concurrency_cap']}")
    lines.append(
        f"workspace_root:  {report['workspace_root']} "
        f"(source: {report.get('workspace_root_source', 'cwd')})"
    )
    lines.append(f"repo_root:       {report['repo_root']}")
    lines.append(f"cc state dir:    {report['codex_companion_state_dir']}")
    lines.append(f"  present:       {report['codex_companion_state_present']}")
    lines.append(f"  jobs known:    {report['codex_companion_jobs_known']}")
    lines.append("")
    counts = report["counts"]
    lines.append(
        "entries:         "
        f"queued={counts['queued']} running={counts['running']} "
        f"done={counts['done']} failed={counts['failed']} "
        f"skipped={counts['skipped']} rescued={counts['rescued']} "
        f"other={counts['other']}"
    )
    lines.append("")

    for er in report["entries"]:
        marker = {
            "queued": "[Q]", "running": "[R]", "done": "[D]",
            "failed": "[F]", "skipped": "[S]", "rescued": "[X]",
        }.get(er.get("status"), "[?]")
        lines.append(f"  {marker} {er.get('id')}  ({er.get('status')})")
        wt = er.get("worktree_path")
        if wt:
            present = "✓" if er.get("worktree_present") else "✗"
            in_git = "✓" if er.get("worktree_in_git") else "✗"
            lines.append(f"      worktree fs={present} git={in_git} {wt}")
        if er.get("log_size") is not None:
            age = er.get("log_age_seconds")
            age_str = f"{age}s" if age is not None else "?"
            lines.append(f"      log {er['log_size']}B age={age_str}  {er.get('log_path')}")
        if er.get("answer_size") is not None:
            lines.append(f"      answer {er['answer_size']}B  {er.get('answer_path')}")
        if er.get("cc_status"):
            alive = er.get("cc_pid_alive")
            alive_str = "alive" if alive else ("dead" if alive is False else "?")
            lines.append(
                f"      cc status={er['cc_status']} pid={er.get('cc_pid')} ({alive_str})"
            )
        for d in er.get("drift") or []:
            lines.append(f"      ⚠ DRIFT: {d}")

    if report["orphan_worktrees"]:
        lines.append("")
        lines.append(f"⚠ ORPHAN worktrees ({len(report['orphan_worktrees'])}):")
        for p in report["orphan_worktrees"]:
            lines.append(f"  • {p}")

    lines.append("")
    lines.append(report.get("drift_summary") or "Drift summary: no drift detected.")
    if report.get("recommendations"):
        lines.append("")
        lines.append("Recommendations:")
        for rec in report["recommendations"]:
            lines.append(f"  • {rec}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True, help="Path to manifest.json")
    ap.add_argument("--workspace-root", default=None,
                    help="Workspace root for repo / state-dir resolution. Default: cwd.")
    ap.add_argument("--stale-minutes", type=int, default=DEFAULT_STALE_MINUTES,
                    help=f"Log freshness threshold in minutes. Default {DEFAULT_STALE_MINUTES}.")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of human text.")
    args = ap.parse_args(argv)

    manifest_path = Path(args.manifest)
    args.manifest = str(manifest_path)
    manifest = load_manifest(manifest_path)
    if manifest is None and not manifest_path.is_file():
        # absent manifest: still emit a report (the manifest may be intentionally
        # gone after a successful tidy), but flag actionable.
        manifest = None

    try:
        report = build_report(args, manifest)
    except OSError as exc:
        print(f"audit-fleet-state: {exc}", file=sys.stderr)
        return 3

    is_actionable = actionable(report)
    if args.json:
        report["actionable"] = is_actionable
        print(json.dumps(report, indent=2, default=str))
    else:
        print(render(report))
        if not report["manifest_present"]:
            print("→ manifest absent (could be intentional if last run tidied)")
        if is_actionable:
            print("→ ACTIONABLE")
        else:
            print("→ CLEAN")
    return 1 if is_actionable else 0


if __name__ == "__main__":
    sys.exit(main())
