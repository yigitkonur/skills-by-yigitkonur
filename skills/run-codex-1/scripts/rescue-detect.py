#!/usr/bin/env python3
"""Classify run-codex-1 manifest entries for rescue-mode operator review.

Reads the manifest, the filesystem (worktrees, log/answer/jsonl files) and
codex-companion's per-job state records (when present) and classifies each
entry into one of:

    done           — completed successfully (status==done AND log/answer
                     present AND, if exec mode, branch committed past base)
    failed         — terminal failure (status==failed OR exit_code != 0)
                     OR worktree dirty + no commits + worker pid dead
    never_started  — status==queued AND no log file AND (no worktree if exec)
    in_flight      — status==running AND worker pid alive AND log growing
    unknown        — anything else (running w/ pid gone, stale codex state, etc)

Read-only. Outputs JSON for the dispatcher (run-codex-1.mjs) or human
text for direct invocation. The dispatcher embeds the JSON output in the
classification envelope; redispatch is explicit via
`run-codex-1.mjs rescue --redo failed|never-started|all-non-done`.

Usage:
    rescue-detect.py --manifest <path>
    rescue-detect.py --manifest <path> --json
    rescue-detect.py --manifest <path> --workspace-root /repo
    rescue-detect.py --manifest <path> --stale-tick-seconds 60

Exit codes:
    0  classification complete (regardless of how many entries failed)
    2  manifest missing or malformed; or bad input
    3  environmental error (permission, etc)
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

DEFAULT_STALE_TICK_SECONDS = 60  # codex-companion default updateAt cadence
DEFAULT_STALE_MULTIPLIER = 3      # log/job idle > N×tick → treat as stale


def sh(cmd: list[str], cwd: Path | None = None, timeout: int | None = 10) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                              check=False, timeout=timeout)
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
    """
    raw = str(workspace_root)
    try:
        canonical = os.path.realpath(raw, strict=True)
    except OSError:
        canonical = raw
    base = os.path.basename(raw) or "workspace"
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", base)
    slug = slug.strip("-") or "workspace"
    hash_hex = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return slug, hash_hex


def codex_companion_state_dir(workspace_root: Path) -> Path:
    """Mirror state.mjs: $CLAUDE_PLUGIN_DATA/state/<slug>-<hash>/, else
    $TMPDIR/codex-companion/<slug>-<hash>/."""
    slug, hash_hex = workspace_slug_hash(workspace_root)
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        return Path(plugin_data) / "state" / f"{slug}-{hash_hex}"
    import tempfile
    return Path(tempfile.gettempdir()) / "codex-companion" / f"{slug}-{hash_hex}"


def load_codex_companion_jobs(state_dir: Path) -> dict[str, dict]:
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


def pid_alive(pid: Any) -> bool | None:
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
        return True
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False
        return None


def file_size(path: str | None) -> int | None:
    if not path:
        return None
    try:
        return os.path.getsize(path)
    except OSError:
        return None


def file_mtime(path: str | None) -> float | None:
    if not path:
        return None
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def parse_iso_to_epoch(value: Any) -> float | None:
    if not value or not isinstance(value, str):
        return None
    try:
        from datetime import datetime, timezone
        # Accept both compact (20260508T182030Z) and standard ISO-8601
        if value.endswith("Z"):
            v = value[:-1] + "+00:00"
        else:
            v = value
        try:
            return datetime.fromisoformat(v).timestamp()
        except ValueError:
            # Try compact form
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(
                tzinfo=timezone.utc
            ).timestamp()
    except Exception:
        return None


def worktree_has_commits_past_base(wt: str, base_commit: str | None) -> bool | None:
    """Returns True if the worktree's HEAD has commits beyond <base_commit>,
    False if it's at base_commit (or behind), None if unknown."""
    if not wt or not os.path.isdir(wt):
        return None
    if not base_commit:
        return None
    rc, out, _ = sh(
        ["git", "rev-list", "--count", f"{base_commit}..HEAD"], cwd=Path(wt)
    )
    if rc != 0:
        return None
    try:
        return int(out.strip()) > 0
    except ValueError:
        return None


def _fs_fallback_paths(entry: dict, mode: str | None,
                       workspace_root: Path, monitor_root: str | None,
                       answers_dir_hint: str | None) -> tuple[str, str]:
    """Derive `(log_path, answer_path)` from filesystem when the manifest
    entry has them as null. Used for batch and (best-effort) single mode.

    For batch:
      - answer_path: <workspace_root>/answers/<slug>.md (run-batch.sh default)
                     or <answers_dir_hint>/<slug>.md
      - log_path:    <monitor_root>/logs/<slug>.log     (per-run-id subdir
                     varies; we glob the simple form first, then look one
                     directory deeper).

    Returns paths (possibly empty strings) the caller can stat.
    """
    log_path = entry.get("log_path") or ""
    answer_path = entry.get("answer_path") or ""

    if log_path and answer_path:
        return log_path, answer_path

    slug = entry.get("slug") or entry.get("id")
    if not slug:
        return log_path, answer_path

    if not answer_path and mode == "batch":
        candidates: list[Path] = []
        if answers_dir_hint:
            candidates.append(Path(answers_dir_hint) / f"{slug}.md")
        candidates.append(workspace_root / "answers" / f"{slug}.md")
        if monitor_root:
            candidates.append(Path(monitor_root) / "answers" / f"{slug}.md")
        for cand in candidates:
            try:
                if cand.is_file() and cand.stat().st_size > 0:
                    answer_path = str(cand)
                    break
            except OSError:
                continue

    if not log_path and mode == "batch":
        log_candidates: list[Path] = []
        if monitor_root:
            log_candidates.append(Path(monitor_root) / "logs" / f"{slug}.log")
            # also consider one nested level (run-id subdir)
            mr = Path(monitor_root)
            try:
                if mr.is_dir():
                    for sub in mr.glob("logs/*/{}.log".format(slug)):
                        log_candidates.append(sub)
            except OSError:
                pass
        log_candidates.append(workspace_root / "logs" / f"{slug}.log")
        for cand in log_candidates:
            try:
                if cand.is_file():
                    log_path = str(cand)
                    break
            except OSError:
                continue

    return log_path, answer_path


def _log_shows_clean_exit(log_path: str) -> bool | None:
    """Best-effort: does the log file end with a codex success marker?

    Returns True if a clean exit pattern is detected, False if a non-zero
    pattern is detected, None if uncertain. Used to override status=failed
    when filesystem evidence disagrees.
    """
    if not log_path:
        return None
    try:
        with open(log_path, "rb") as f:
            try:
                f.seek(-4096, os.SEEK_END)
            except OSError:
                f.seek(0)
            tail = f.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    low = tail.lower()
    # `--- all jobs finished ---` is run-batch.sh's success sentinel.
    if "all jobs finished" in low:
        return True
    if "codex exit 0" in low or '"exit_code": 0' in low:
        return True
    if re.search(r"codex exit [1-9]\d*", low):
        return False
    if re.search(r'"exit_code"\s*:\s*[1-9]\d*', low):
        return False
    return None


def classify_entry(
    entry: dict,
    cc_jobs: dict[str, dict],
    base_commit: str | None,
    mode: str | None,
    now: float,
    stale_secs: int,
    workspace_root: Path | None = None,
    monitor_root: str | None = None,
    answers_dir_hint: str | None = None,
) -> dict:
    """Apply the rescue classification rules.

    Rules (from plan):
        done: status==done AND log file exists
              AND (answer non-empty if applicable)
              AND (worktree committed past baseline if applicable)
        failed: status==failed OR exit_code != 0
                OR worktree dirty + no commits + worker pid dead
        never_started: status==queued AND no log file
                       AND (no worktree if exec mode)
        in_flight: status==running AND worker pid alive AND log growing
        unknown: anything else
    """
    eid = entry.get("id") or entry.get("slug") or "<unknown>"
    status = entry.get("status")
    exit_code = entry.get("exit_code")
    wt = entry.get("worktree_path") or ""

    # Filesystem-fallback for batch entries with null answer/log paths.
    log_path = entry.get("log_path") or ""
    answer_path = entry.get("answer_path") or ""
    fs_fallback_used = False
    if (not log_path or not answer_path) and workspace_root is not None:
        derived_log, derived_answer = _fs_fallback_paths(
            entry, mode, workspace_root, monitor_root, answers_dir_hint
        )
        if derived_log != log_path or derived_answer != answer_path:
            fs_fallback_used = True
        log_path = derived_log
        answer_path = derived_answer

    log_size = file_size(log_path)
    log_mtime = file_mtime(log_path)
    log_age = (now - log_mtime) if log_mtime is not None else None
    log_present = log_size is not None and log_size > 0

    answer_size = file_size(answer_path)
    answer_present = answer_size is not None and answer_size > 0

    wt_present = bool(wt) and os.path.isdir(wt)
    wt_dirty = None
    if wt_present:
        rc, sout, _ = sh(["git", "status", "--porcelain=1"], cwd=Path(wt))
        wt_dirty = (rc != 0) or bool(sout.strip())

    wt_committed = worktree_has_commits_past_base(wt, base_commit)

    # Try codex_session_id first (cc-companion's job id), fall back to
    # codex_thread_id (batch never sets session_id).
    sid = (
        entry.get("codex_session_id")
        or entry.get("codex_thread_id")
        or None
    )
    cc = cc_jobs.get(sid) if sid else None
    cc_pid = cc.get("pid") if cc else None
    cc_alive = pid_alive(cc_pid) if cc_pid else None
    cc_status = cc.get("status") if cc else None
    cc_updated_at = cc.get("updatedAt") if cc else None
    cc_age = None
    cc_updated_epoch = parse_iso_to_epoch(cc_updated_at)
    if cc_updated_epoch is not None:
        cc_age = now - cc_updated_epoch

    # ----- Apply rules -----
    classification = "unknown"
    reason = None
    warnings: list[str] = []

    if status == "done":
        # done: log present, answer non-empty if applicable, committed past base if exec
        ok = log_present
        if answer_path and not answer_present:
            ok = False
            reason = "status=done but answer file empty"
        if ok and mode == "exec" and wt_committed is False:
            ok = False
            reason = "status=done (exec) but worktree has no commits past base"
        if ok:
            classification = "done"
        else:
            classification = "unknown"
            reason = reason or "status=done but evidence is missing"

    elif status == "skipped":
        # `skipped` is a terminal-OK status (e.g. batch found a pre-existing
        # non-empty answer). For redispatch purposes it's equivalent to done.
        classification = "done"
        reason = "status=skipped (treated as done for redispatch)"

    elif status == "failed" or (
        (exit_code is not None) and isinstance(exit_code, (int, float)) and exit_code != 0
    ):
        # Cross-check: if the manifest says failed but the worktree carries
        # commits past base AND the log shows a clean codex exit, the failure
        # marker may be stale (writer crashed before flipping status). Surface
        # as `unknown` with a warning instead of silently treating as failure.
        log_clean = _log_shows_clean_exit(log_path)
        if (
            wt_committed is True
            and log_clean is True
        ):
            classification = "unknown"
            reason = (
                "status=failed but worktree has commits past base AND log "
                "shows codex exit 0 — manifest writer may have crashed before "
                "status flip; verify before redispatching"
            )
            warnings.append(reason)
        elif status == "failed":
            classification = "failed"
            reason = "status=failed"
        else:
            classification = "failed"
            reason = f"exit_code={exit_code}"

    elif status == "queued":
        if not log_present and (mode != "exec" or not wt_present):
            classification = "never_started"
            reason = "status=queued, no log, no worktree"
        elif not log_present:
            classification = "never_started"
            reason = "status=queued, no log"
        else:
            classification = "unknown"
            reason = "status=queued but log present (orphan log? interrupted setup?)"

    elif status == "running":
        # running: pid alive AND log growing → in_flight; else stale/dead
        if cc_alive is True and log_age is not None and log_age <= stale_secs:
            classification = "in_flight"
            reason = "pid alive, log fresh"
        elif cc_alive is False:
            # pid dead
            if wt_present and wt_dirty and wt_committed in (False, None):
                classification = "failed"
                reason = "status=running but pid dead and worktree dirty without commits"
            else:
                classification = "failed"
                reason = "status=running but worker pid dead"
        elif cc_alive is None and log_age is not None and log_age > stale_secs:
            classification = "unknown"
            reason = f"status=running, no pid info, log stale ({int(log_age)}s)"
        elif cc_alive is None and log_age is None:
            classification = "unknown"
            reason = "status=running, no pid info, no log"
        else:
            classification = "in_flight"
            reason = "pid alive, log presence undetermined"

    elif status == "rescued":
        # `rescued` is a terminal status (rescue mode replayed and superseded
        # this entry). Treated as done for redispatch purposes.
        classification = "done"
        reason = "status=rescued (terminal; treated as done)"

    else:
        classification = "unknown"
        reason = f"unrecognized status: {status!r}"

    # Filesystem-fallback inference for batch entries: when the manifest
    # entry has null log/answer paths but evidence on disk says the work
    # finished, surface a soft hint. Don't override an explicit `failed`.
    if (
        mode == "batch"
        and fs_fallback_used
        and answer_present
        and classification not in ("done", "failed", "in_flight")
    ):
        warnings.append(
            f"manifest paths null but found {answer_path} ({answer_size}B) "
            f"on filesystem — promoted to done"
        )
        classification = "done"
        reason = (
            "filesystem fallback: answer file present and non-empty "
            "despite null/missing manifest paths"
        )

    recommended_action = {
        "done":          "skip (already complete)",
        "failed":        "redispatch (rescue this entry)",
        "never_started": "dispatch (first attempt; safe replay)",
        "in_flight":     "wait (do not duplicate; let it finish)",
        "unknown":       "operator-decision (gather logs, then choose)",
    }[classification]

    result: dict = {
        "id": eid,
        "slug": entry.get("slug"),
        "manifest_status": status,
        "exit_code": exit_code,
        "classification": classification,
        "reason": reason,
        "warnings": warnings,
        "recommended_action": recommended_action,
        "evidence": {
            "log_path": log_path,
            "log_size": log_size,
            "log_age_seconds": int(log_age) if log_age is not None else None,
            "answer_path": answer_path,
            "answer_size": answer_size,
            "worktree_path": wt,
            "worktree_present": wt_present,
            "worktree_dirty": wt_dirty,
            "worktree_committed_past_base": wt_committed,
            "codex_session_id": entry.get("codex_session_id"),
            "codex_thread_id": entry.get("codex_thread_id"),
            "correlation_id": sid,
            "cc_pid": cc_pid,
            "cc_pid_alive": cc_alive,
            "cc_status": cc_status,
            "cc_updated_at": cc_updated_at,
            "cc_age_seconds": int(cc_age) if cc_age is not None else None,
            "fs_fallback_used": fs_fallback_used,
            # Surface the manifest's last_error verbatim so operators with
            # mixed failure causes (rate_limit_503, dirty_worktree,
            # post_verify_fail, …) can pick `--apply ids:s1,s2` surgically
            # without re-reading the manifest. selectRescueSubset filters on
            # status only; this field gives the operator (and downstream
            # automation) the missing axis.
            "last_error": entry.get("last_error"),
        },
    }

    # For single mode, surface a `codex exec resume <thread-id>` hint when
    # the entry carries a thread id. Callers (orchestrator) use this to build
    # a one-line action without re-deriving from evidence.
    thread_id = entry.get("codex_thread_id")
    if mode == "single" and thread_id:
        result["resume_hint"] = f"codex exec resume {thread_id}"

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True, help="Path to run-codex-1 manifest.json")
    ap.add_argument("--workspace-root", default=None,
                    help="Workspace root for codex-companion state lookup. Default: cwd.")
    ap.add_argument("--stale-tick-seconds", type=int, default=DEFAULT_STALE_TICK_SECONDS,
                    help="Single-tick threshold (seconds). log/job idle > tick × multiplier "
                         f"is treated as stale. Default {DEFAULT_STALE_TICK_SECONDS}.")
    ap.add_argument("--stale-multiplier", type=int, default=DEFAULT_STALE_MULTIPLIER,
                    help=f"Stale threshold multiplier. Default {DEFAULT_STALE_MULTIPLIER}.")
    ap.add_argument("--json", action="store_true", help="Emit JSON output for run-codex-1.mjs.")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(f"rescue-detect: manifest not found: {manifest_path}", file=sys.stderr)
        return 2
    try:
        with manifest_path.open() as f:
            manifest = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"rescue-detect: malformed manifest JSON: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"rescue-detect: cannot read manifest: {exc}", file=sys.stderr)
        return 3

    if not isinstance(manifest, dict):
        print("rescue-detect: manifest root must be an object", file=sys.stderr)
        return 2

    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        print("rescue-detect: manifest has no entries[] array", file=sys.stderr)
        return 2

    # NOTE: do NOT pre-resolve symlinks (no `.resolve()`). The slug-hash
    # function below mirrors codex-companion's `fs.realpathSync.native` +
    # JS-side catch fallback exactly; pre-resolving here would diverge for
    # symlinked roots like /tmp on macOS or for missing paths.
    #
    # Workspace-root resolution priority:
    #   1. explicit --workspace-root
    #   2. manifest.workspace_root (when present)
    #   3. cwd
    workspace_root_source = "cwd"
    if args.workspace_root:
        workspace_root = Path(args.workspace_root)
        workspace_root_source = "flag"
    elif isinstance(manifest.get("workspace_root"), str) and manifest["workspace_root"]:
        workspace_root = Path(manifest["workspace_root"])
        workspace_root_source = "manifest"
    else:
        workspace_root = Path.cwd()

    repo_root = find_repo_root(workspace_root)
    cc_state = codex_companion_state_dir(repo_root if repo_root else workspace_root)
    cc_jobs = load_codex_companion_jobs(cc_state)

    base_commit = manifest.get("base_commit")
    mode = manifest.get("mode")
    monitor_root = manifest.get("monitor_root")
    answers_dir_hint = manifest.get("answers_dir")  # set by some dispatcher paths
    now = time.time()
    stale_secs = max(1, args.stale_tick_seconds * args.stale_multiplier)

    classified = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        classified.append(classify_entry(
            entry, cc_jobs, base_commit, mode, now, stale_secs,
            workspace_root=workspace_root,
            monitor_root=monitor_root,
            answers_dir_hint=answers_dir_hint,
        ))

    counts = {"done": 0, "failed": 0, "never_started": 0, "in_flight": 0, "unknown": 0}
    for c in classified:
        counts[c["classification"]] = counts.get(c["classification"], 0) + 1

    redispatch_failed_only = [c["id"] for c in classified if c["classification"] == "failed"]
    redispatch_never_started_only = [
        c["id"] for c in classified if c["classification"] == "never_started"
    ]
    redispatch_all_non_done = [
        c["id"] for c in classified
        if c["classification"] in ("failed", "never_started", "unknown")
    ]

    # Aggregate per-entry warnings into a top-level list for callers.
    aggregated_warnings: list[str] = []
    for c in classified:
        for w in c.get("warnings") or []:
            aggregated_warnings.append(f"[{c['id']}] {w}")

    out = {
        "manifest_path": str(manifest_path),
        "manifest_run_id": manifest.get("run_id"),
        "manifest_mode": mode,
        "manifest_base_commit": base_commit,
        "workspace_root": str(workspace_root),
        "workspace_root_source": workspace_root_source,
        "repo_root": str(repo_root) if repo_root else None,
        "codex_companion_state_dir": str(cc_state),
        "codex_companion_state_present": cc_state.is_dir(),
        "codex_companion_jobs_known": len(cc_jobs),
        "stale_threshold_seconds": stale_secs,
        "counts": counts,
        "redispatch_options": {
            "failed_only": redispatch_failed_only,
            "never_started_only": redispatch_never_started_only,
            "all_non_done": redispatch_all_non_done,
        },
        "warnings": aggregated_warnings,
        "entries": classified,
    }

    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        print("─" * 64)
        print(f"rescue-detect for {manifest_path}")
        print("─" * 64)
        print(f"  run_id:      {out['manifest_run_id']}")
        print(f"  mode:        {out['manifest_mode']}")
        print(f"  base_commit: {out['manifest_base_commit']}")
        print(f"  cc state:    {out['codex_companion_state_dir']}")
        print(f"  cc present:  {out['codex_companion_state_present']} ({out['codex_companion_jobs_known']} jobs)")
        print(f"  stale > {stale_secs}s")
        print()
        c = out["counts"]
        print(f"counts: done={c['done']} failed={c['failed']} "
              f"never_started={c['never_started']} in_flight={c['in_flight']} "
              f"unknown={c['unknown']}")
        print()
        for r in classified:
            marker = {
                "done":          "[D]",
                "failed":        "[F]",
                "never_started": "[N]",
                "in_flight":     "[R]",
                "unknown":       "[?]",
            }.get(r["classification"], "[?]")
            print(f"  {marker} {r['id']}  → {r['classification']}: {r['reason']}")
            print(f"      recommended: {r['recommended_action']}")
        print()
        print("Redispatch options:")
        print(f"  failed-only:        {len(redispatch_failed_only)} entries → "
              f"{redispatch_failed_only or '(empty)'}")
        print(f"  never-started-only: {len(redispatch_never_started_only)} entries → "
              f"{redispatch_never_started_only or '(empty)'}")
        print(f"  all-non-done:       {len(redispatch_all_non_done)} entries → "
              f"{redispatch_all_non_done or '(empty)'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
