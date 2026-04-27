#!/usr/bin/env python3
"""Wrap /codex:review --background for one branch; normalize output to JSON.

Invokes the Codex CLI inside the branch's worktree, polls the background job
to completion, fetches the review artifact, normalizes to the JSON schema in
references/codex-review-contract.md, and writes the round log + manifest update.

The exact codex CLI form is environment-dependent; see invoke_codex() for the
adjustment point.

Usage:
    python3 run-codex-review.py --branch feat/foo --worktree /path/to/wt
    python3 run-codex-review.py --branch feat/foo --worktree /path/to/wt --dry-run
    python3 run-codex-review.py --branch feat/foo --worktree /path/to/wt \\
        --timeout 1800 --poll-interval 30

Exit codes:
    0  review available; round log written
    1  timeout (manifest marked 'timeout'; caller decides retry)
    2  codex/CLI failed (manifest marked 'failed'; caller decides FAILED)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_MANIFEST = "/tmp/codex-review-manifest.json"
DEFAULT_ROUNDS_DIR = "/tmp/codex-review-rounds/"
DEFAULT_TIMEOUT = 1800
DEFAULT_POLL_INTERVAL = 30


def sh(cmd, cwd=None, env=None, timeout=None):
    try:
        p = subprocess.run(
            cmd, cwd=cwd, env=env, capture_output=True,
            text=True, check=False, timeout=timeout,
        )
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "command timed out"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slug(branch: str) -> str:
    return branch.replace("/", "-")


def head_sha(wt: str) -> str:
    rc, out, _ = sh(["git", "rev-parse", "HEAD"], cwd=Path(wt))
    return out if rc == 0 else ""


def atomic_write(path: str, content: str):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".rcr.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise


def load_manifest(path: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def update_manifest_entry(path: str, branch: str, updates: dict, history_entry: dict | None = None):
    manifest = load_manifest(path)
    if manifest is None:
        return
    for entry in manifest.get("branches", []):
        if entry.get("branch") == branch:
            entry.update(updates)
            entry["updated_at"] = utc_now_iso()
            if history_entry is not None:
                entry.setdefault("round_history", []).append(history_entry)
            break
    atomic_write(path, json.dumps(manifest, indent=2))


def get_round_for_branch(path: str, branch: str) -> int:
    manifest = load_manifest(path)
    if manifest is None:
        return 0
    for entry in manifest.get("branches", []):
        if entry.get("branch") == branch:
            return entry.get("rounds", 0)
    return 0


# ─── Codex invocation — adjustment point per environment ──────────────────────

def invoke_codex(branch: str, base: str, wt: Path) -> tuple[int, str, str]:
    """Launch /codex:review --background. Return (rc, stdout, stderr).

    Adjust the command form here to match the codex CLI in your environment.
    Common forms (try in order):
      - codex review --background --branch <b> --base <base>
      - codex review --background
      - claude codex review --background
    """
    candidates = [
        ["codex", "review", "--background", "--branch", branch, "--base", base],
        ["codex", "review", "--background"],
    ]
    for cmd in candidates:
        rc, out, err = sh(cmd, cwd=wt, timeout=120)
        if rc != 127:  # found and ran (even if it failed for other reasons)
            return rc, out, err
    return 127, "", "no codex CLI form succeeded; check codex install / PATH"


def parse_job_id(stdout: str) -> str | None:
    """Extract a background job id from launch stdout.

    Adjust this regex to match what your codex CLI prints.
    """
    patterns = [
        r"\bjob[- ]?id[:=]\s*([A-Za-z0-9_-]+)",
        r"\b(cdx[- ]?job[- ]?[A-Za-z0-9_-]+)",
        r"\bbackground job[:=]\s*([A-Za-z0-9_-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, stdout, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def poll_job(job_id: str, wt: Path, poll_interval: int, timeout: int) -> tuple[str, str]:
    """Poll the codex job until completion. Returns (status, raw_artifact)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        rc, out, err = sh(["codex", "review", "--status", job_id], cwd=wt, timeout=60)
        if rc == 127:
            return "failed", f"codex --status not available: {err}"
        text = out.lower()
        if "completed" in text or "done" in text or "finished" in text:
            # fetch artifact
            rc2, art, err2 = sh(["codex", "review", "--fetch", job_id], cwd=wt, timeout=120)
            if rc2 == 0:
                return "completed", art
            return "failed", f"fetch failed: {err2}"
        if "failed" in text or "cancelled" in text or "errored" in text:
            return "failed", out
        time.sleep(poll_interval)
    return "timeout", ""


def normalize_review(raw: str, review_id: str, branch: str, head: str,
                     started_at: str, finished_at: str) -> dict:
    """Best-effort normalization of the artifact to the schema in
    references/codex-review-contract.md. If the artifact is structured JSON,
    parse it. Otherwise treat as unstructured text and let the classifier
    fall back to regex over raw_text.
    """
    items = []
    parsed = None
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        parsed = None
    if isinstance(parsed, dict) and isinstance(parsed.get("items"), list):
        items = parsed["items"]
    elif isinstance(parsed, list):
        items = parsed

    return {
        "review_id": review_id,
        "branch": branch,
        "head_sha": head,
        "started_at": started_at,
        "finished_at": finished_at,
        "raw_text": raw,
        "items": items,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--base", default="main")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--rounds-dir", default=DEFAULT_ROUNDS_DIR)
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                    help="seconds to wait for the background job to complete")
    ap.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    wt = Path(args.worktree)
    if not wt.is_dir():
        print(f"worktree not found: {wt}", file=sys.stderr)
        return 2

    # Pre-flight: branch is checked out in the worktree
    rc, branch_at_wt, _ = sh(["git", "symbolic-ref", "--short", "HEAD"], cwd=wt)
    if rc != 0 or branch_at_wt != args.branch:
        print(f"worktree {wt} is not on branch {args.branch} (HEAD={branch_at_wt or 'detached'})", file=sys.stderr)
        return 2

    head = head_sha(str(wt))
    started_at = utc_now_iso()

    if args.dry_run:
        print(f"DRY-RUN: would invoke codex review --background in {wt}")
        print(f"  branch:      {args.branch}")
        print(f"  base:        {args.base}")
        print(f"  head:        {head}")
        print(f"  manifest:    {args.manifest}")
        print(f"  rounds-dir:  {args.rounds_dir}")
        print(f"  timeout:     {args.timeout}s, poll {args.poll_interval}s")
        return 0

    print(f"launching /codex:review --background in {wt} ...")
    rc, out, err = invoke_codex(args.branch, args.base, wt)
    if rc not in (0, 1):  # 0=ok, 1 sometimes used for "submitted with warnings"
        print(f"✗ codex launch failed (rc={rc}): {err}", file=sys.stderr)
        update_manifest_entry(args.manifest, args.branch, {"last_status": "failed"})
        return 2

    job_id = parse_job_id(out) or parse_job_id(err)
    if not job_id:
        # Heuristic: if codex returned 0 but no recognizable id, use a synthetic one
        job_id = f"cdx-job-unknown-{int(time.time())}"
        print(f"⚠  no recognizable job id in launch output; using synthetic: {job_id}")

    print(f"  job id: {job_id}; polling every {args.poll_interval}s up to {args.timeout}s...")
    status, raw = poll_job(job_id, wt, args.poll_interval, args.timeout)
    finished_at = utc_now_iso()

    if status == "timeout":
        print(f"✗ job {job_id} timed out after {args.timeout}s", file=sys.stderr)
        update_manifest_entry(args.manifest, args.branch, {
            "last_review_id": job_id,
            "last_review_at": finished_at,
            "last_status": "timeout",
        })
        return 1
    if status == "failed":
        print(f"✗ job {job_id} failed: {raw[:200]}", file=sys.stderr)
        update_manifest_entry(args.manifest, args.branch, {
            "last_review_id": job_id,
            "last_review_at": finished_at,
            "last_status": "failed",
        })
        return 2

    # status == "completed"
    review = normalize_review(raw, job_id, args.branch, head, started_at, finished_at)
    round_n = get_round_for_branch(args.manifest, args.branch) + 1
    log_path = os.path.join(args.rounds_dir, f"{slug(args.branch)}.{round_n:02d}.json")
    atomic_write(log_path, json.dumps(review, indent=2))
    print(f"  ✓ round log written: {log_path}")

    history_entry = {
        "round": round_n,
        "review_id": job_id,
        "completed_at": finished_at,
    }
    update_manifest_entry(args.manifest, args.branch, {
        "last_review_id": job_id,
        "last_review_at": finished_at,
        "last_status": "reviewed",
        "rounds": round_n,
        "head_sha_current": head,
    }, history_entry=history_entry)
    print(f"  ✓ manifest updated: rounds={round_n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
