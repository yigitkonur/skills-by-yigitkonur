#!/usr/bin/env python3
"""Trigger /codex:resc --background --fresh --model gpt-5.5 --effort xhigh on a PR.

Codex rescue is Codex's own background sub-agent (not a Claude Agent dispatched
by us). We hand it the PR link; Codex's infrastructure spawns the review job;
the review lands on the PR like any other reviewer's comments.

This script invokes the codex CLI's rescue form, captures the rescue job id,
and updates the manifest entry for the branch with rescue_review_id /
rescue_started_at. Returns immediately — does not poll. Phase 6's
await-pr-reviews.py owns the wait.

Usage:
    python3 trigger-codex-rescue.py --pr 42 --branch feat/foo
    python3 trigger-codex-rescue.py --pr 42 --branch feat/foo --dry-run
    python3 trigger-codex-rescue.py --pr 42 --branch feat/foo \\
        --model gpt-5.5 --effort xhigh

Exit codes:
    0  rescue triggered; manifest updated
    1  triggered but couldn't parse a job id (synthetic id used; manifest still updated)
    2  codex CLI failed; manifest marked rescue_status=failed
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
DEFAULT_MODEL = "gpt-5.5"
DEFAULT_EFFORT = "xhigh"


def sh(cmd, cwd=None, timeout=None):
    try:
        p = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True,
            check=False, timeout=timeout,
        )
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "command timed out"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic_write(path: str, content: str):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".rescue.", suffix=".tmp")
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


def update_manifest_entry(path: str, branch: str, updates: dict) -> bool:
    manifest = load_manifest(path)
    if manifest is None:
        return False
    found = False
    for entry in manifest.get("branches", []):
        if entry.get("branch") == branch:
            entry.update(updates)
            entry["updated_at"] = utc_now_iso()
            found = True
            break
    if not found:
        return False
    atomic_write(path, json.dumps(manifest, indent=2))
    return True


# ─── Codex rescue invocation — adjustment point per environment ──────────────

def invoke_rescue(pr: int, model: str, effort: str, wt: Path) -> tuple[int, str, str]:
    """Launch codex rescue in --background mode. Return (rc, stdout, stderr).

    Adjust the command form here to match the codex CLI in your environment.
    Common forms (try in order):
      - codex review --rescue --background --fresh --model <m> --effort <e> --pr <n>
      - codex rescue --background --fresh --model <m> --effort <e> --pr <n>
      - codex resc --background --fresh --model <m> --effort <e> --pr <n>
    """
    candidates = [
        ["codex", "review", "--rescue", "--background", "--fresh",
         "--model", model, "--effort", effort, "--pr", str(pr)],
        ["codex", "rescue", "--background", "--fresh",
         "--model", model, "--effort", effort, "--pr", str(pr)],
        ["codex", "resc", "--background", "--fresh",
         "--model", model, "--effort", effort, "--pr", str(pr)],
    ]
    for cmd in candidates:
        rc, out, err = sh(cmd, cwd=wt, timeout=120)
        if rc != 127:  # found the binary, even if it failed for other reasons
            return rc, out, err
    return 127, "", "no codex rescue CLI form succeeded; check codex install / PATH"


def parse_rescue_job_id(stdout: str) -> str | None:
    """Extract a rescue job id from launch stdout. Adjust regex per CLI output."""
    patterns = [
        r"\brescue[- ]?job[- ]?id[:=]\s*([A-Za-z0-9_-]+)",
        r"\b(cdx[- ]?rescue[- ]?[A-Za-z0-9_-]+)",
        r"\bjob[- ]?id[:=]\s*([A-Za-z0-9_-]+)",
        r"\bbackground job[:=]\s*([A-Za-z0-9_-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, stdout, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pr", type=int, required=True, help="PR number")
    ap.add_argument("--branch", required=True, help="branch name (manifest entry key)")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--effort", default=DEFAULT_EFFORT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manifest = load_manifest(args.manifest)
    if manifest is None:
        print(f"manifest absent or unreadable: {args.manifest}", file=sys.stderr)
        return 2

    entry = next((e for e in manifest.get("branches", []) if e.get("branch") == args.branch), None)
    if entry is None:
        print(f"branch {args.branch} not in manifest", file=sys.stderr)
        return 2

    wt = Path(entry.get("worktree_path", ""))
    if not wt.is_dir():
        print(f"worktree not found: {wt}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"DRY-RUN: would invoke codex rescue for PR #{args.pr} in {wt}")
        print(f"  branch: {args.branch}")
        print(f"  model:  {args.model}")
        print(f"  effort: {args.effort}")
        print(f"  manifest entry would be updated with rescue_review_id (synthetic if no parse)")
        return 0

    print(f"triggering codex rescue: PR #{args.pr} in {wt} ({args.model}, effort={args.effort})...")
    started_at = utc_now_iso()
    rc, out, err = invoke_rescue(args.pr, args.model, args.effort, wt)

    if rc == 127:
        print(f"✗ codex CLI not found: {err}", file=sys.stderr)
        update_manifest_entry(args.manifest, args.branch, {
            "rescue_status": "failed",
            "rescue_error": "codex CLI not on PATH",
            "rescue_started_at": started_at,
        })
        return 2

    if rc not in (0, 1):  # 0 = ok, 1 sometimes used for "submitted with warnings"
        print(f"✗ codex rescue failed (rc={rc}): {err}", file=sys.stderr)
        update_manifest_entry(args.manifest, args.branch, {
            "rescue_status": "failed",
            "rescue_error": (err or out)[:500],
            "rescue_started_at": started_at,
        })
        return 2

    job_id = parse_rescue_job_id(out) or parse_rescue_job_id(err)
    parse_failure = False
    if not job_id:
        job_id = f"cdx-rescue-unknown-{int(time.time())}"
        parse_failure = True
        print(f"⚠  no recognizable rescue job id in launch output; using synthetic: {job_id}")

    update_manifest_entry(args.manifest, args.branch, {
        "rescue_review_id": job_id,
        "rescue_started_at": started_at,
        "rescue_status": "running",
        "rescue_pr_number": args.pr,
        "rescue_model": args.model,
        "rescue_effort": args.effort,
    })
    print(f"  ✓ rescue triggered: job id = {job_id}")
    print(f"  ✓ manifest updated: {args.manifest}")
    return 1 if parse_failure else 0


if __name__ == "__main__":
    sys.exit(main())
