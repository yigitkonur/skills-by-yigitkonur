#!/usr/bin/env python3
"""Trigger codex rescue for a PR via the OpenAI Codex Claude Code plugin.

Wraps `node codex-companion.mjs task --background --write --fresh
--model gpt-5.5 --effort xhigh --prompt-file <path> --json` — the same
code path the `/codex:resc` slash command runs internally. The companion's
`task --background` is the one subcommand that actually honors `--background`:
it spawns a detached Codex worker and returns
`{ jobId, status: "queued", title, logFile }` immediately. Phase 6's
`await-pr-reviews.py` (or this script's `--wait` flag) owns the wait.

Usage:
    # Default: queue rescue, write rescue_review_id + rescue_started_at to manifest, return.
    python3 trigger-codex-rescue.py \\
        --pr 42 --branch feat/foo \\
        --worktree /path/to/wt \\
        --prompt-file /tmp/rescue-prompt-pr-42.md

    # If main agent has the prompt in stdin:
    cat prompt.md | python3 trigger-codex-rescue.py \\
        --pr 42 --branch feat/foo --worktree /path/to/wt

    # Block until the rescue job completes (default cap 30 min):
    python3 trigger-codex-rescue.py \\
        --pr 42 --branch feat/foo --worktree /path/to/wt \\
        --prompt-file /tmp/p.md --wait --timeout-ms 1800000

    # Optional: write to a non-default manifest:
    python3 trigger-codex-rescue.py ... --manifest /repo/.codex-review-manifest.json

Exit codes:
    0  rescue queued (and completed if --wait); manifest updated
    1  --wait specified but the job timed out before terminal status
    2  rescue queue failed (codex CLI error, manifest update failed)
  127  codex plugin not installed (caller surfaces FAILED)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_MODEL = "gpt-5.5"
DEFAULT_EFFORT = "xhigh"
DEFAULT_TIMEOUT_MS = 1_800_000  # 30 min — matches Phase 6 total cap


# ─── codex-companion.mjs discovery (version-agnostic) ─────────────────────────
# (Same shape as run-codex-review.py — duplicated by design; one shared helper
# for two callers was overengineering and would force sys.path hacks.)

def _find_codex_companion() -> Path:
    """Discover the OpenAI Codex plugin's codex-companion.mjs.

    Resolution order:
      1. ${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs (set by Claude Code harness).
      2. Latest semver-sorted version under
         ~/.claude/plugins/cache/openai-codex/codex/<version>/scripts/codex-companion.mjs.

    Plugin source: https://github.com/openai/codex-plugin-cc/tree/main/plugins/codex
    """
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        candidate = Path(plugin_root) / "scripts" / "codex-companion.mjs"
        if candidate.is_file():
            return candidate

    cache = Path.home() / ".claude" / "plugins" / "cache" / "openai-codex" / "codex"
    if cache.is_dir():
        def _key(p: Path) -> tuple:
            m = re.match(r"^(\d+)\.(\d+)\.(\d+)", p.name)
            return (1, int(m[1]), int(m[2]), int(m[3])) if m else (0, p.name)
        for v in sorted((p for p in cache.iterdir() if p.is_dir()), key=_key, reverse=True):
            candidate = v / "scripts" / "codex-companion.mjs"
            if candidate.is_file():
                return candidate

    raise FileNotFoundError(
        "codex-companion.mjs not found. Install the OpenAI Codex Claude Code plugin "
        "(https://github.com/openai/codex-plugin-cc) — expected at "
        "$CLAUDE_PLUGIN_ROOT/scripts/codex-companion.mjs or at "
        "~/.claude/plugins/cache/openai-codex/codex/<version>/scripts/codex-companion.mjs."
    )


# ─── Generic helpers ──────────────────────────────────────────────────────────

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


def repo_local_default(wt: Path, name: str) -> str:
    rc, out, _ = sh(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=wt)
    if rc == 0 and out:
        return str(Path(out).parent / name)
    return f"/tmp/{name}"


# ─── Codex rescue invocation ─────────────────────────────────────────────────

def write_prompt_file(prompt: str, pr: int) -> Path:
    """Persist the rescue prompt to a stable path so codex-companion can read it.
    Returns the path. /tmp is fine for the prompt — it's input, not state."""
    path = Path(f"/tmp/codex-rescue-prompt-pr-{pr}.md")
    path.write_text(prompt)
    return path


def invoke_rescue(pr: int, model: str, effort: str, prompt_file: Path,
                  wt: Path, timeout: int = 120) -> tuple[int, str, str]:
    """Spawn codex-companion task --background. Returns (rc, stdout, stderr).

    The companion's `task` subcommand DOES honor --background — unlike `review`,
    which runs synchronously regardless. Background returns
    `{ jobId, status: "queued", title, logFile }` on stdout immediately.
    """
    try:
        companion = _find_codex_companion()
    except FileNotFoundError as e:
        return 127, "", str(e)

    cmd = [
        "node", str(companion), "task",
        "--background",
        "--write",
        "--fresh",
        "--model", model,
        "--effort", effort,
        "--prompt-file", str(prompt_file),
        "--json",
    ]
    return sh(cmd, cwd=wt, timeout=timeout)


def wait_for_rescue(job_id: str, wt: Path, timeout_ms: int) -> tuple[int, dict | None, str]:
    """Poll codex-companion status <job-id> --wait until terminal.

    Returns (rc, parsed_status_payload, stderr).
    """
    try:
        companion = _find_codex_companion()
    except FileNotFoundError as e:
        return 127, None, str(e)

    cmd = [
        "node", str(companion), "status", job_id,
        "--wait",
        "--timeout-ms", str(timeout_ms),
        "--json",
    ]
    rc, out, err = sh(cmd, cwd=wt, timeout=(timeout_ms / 1000) + 60)
    if rc != 0:
        return rc, None, err or out
    try:
        return rc, json.loads(out), err
    except (ValueError, TypeError):
        return rc, None, f"could not parse status JSON: {out[:500]}"


# ─── Main ─────────────────────────────────────────────────────────────────────

def read_prompt(args) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("provide --prompt-file <path> or pipe the prompt on stdin")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pr", type=int, required=True, help="PR number")
    ap.add_argument("--branch", required=True, help="branch name (manifest entry key)")
    ap.add_argument("--worktree", required=True, help="worktree path; codex runs from here")
    ap.add_argument("--prompt-file",
                    help="Path to the comprehensive review prompt for Codex. If absent, reads stdin.")
    ap.add_argument("--manifest",
                    help="Manifest path. Default: <repo-root>/.codex-review-manifest.json")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--effort", default=DEFAULT_EFFORT,
                    help="Codex reasoning effort: none|minimal|low|medium|high|xhigh")
    ap.add_argument("--wait", action="store_true",
                    help="Block until the rescue job terminates (status ∈ completed|failed|cancelled). "
                         "Default: queue and return immediately.")
    ap.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS,
                    help=f"Total wall-clock cap when --wait is set. Default {DEFAULT_TIMEOUT_MS} ms (30 min).")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    wt = Path(args.worktree)
    if not wt.is_dir():
        print(f"worktree not found: {wt}", file=sys.stderr)
        return 2

    manifest_path = args.manifest or repo_local_default(wt, ".codex-review-manifest.json")

    if args.dry_run:
        try:
            companion = _find_codex_companion()
        except FileNotFoundError as e:
            print(f"DRY-RUN: {e}", file=sys.stderr)
            return 127
        print(f"DRY-RUN: would invoke")
        print(f"  node {companion} task --background --write --fresh "
              f"--model {args.model} --effort {args.effort} --prompt-file <prompt> --json")
        print(f"  cwd:        {wt}")
        print(f"  PR:         #{args.pr}")
        print(f"  branch:     {args.branch}")
        print(f"  manifest:   {manifest_path}")
        print(f"  wait:       {args.wait}")
        if args.wait:
            print(f"  timeout-ms: {args.timeout_ms}")
        return 0

    # Read the rescue prompt (file or stdin) and persist to /tmp so codex-companion
    # can --prompt-file it. Multiline content survives this round-trip.
    prompt = read_prompt(args)
    if not prompt.strip():
        print("rescue prompt is empty; aborting", file=sys.stderr)
        return 2
    prompt_path = write_prompt_file(prompt, args.pr)

    # Manifest is optional — if absent, we still queue the rescue but skip the update.
    manifest_present = load_manifest(manifest_path) is not None
    if not manifest_present:
        print(f"⚠  manifest not found at {manifest_path}; rescue will queue but no manifest update", file=sys.stderr)

    started_at = utc_now_iso()
    print(f"queueing codex rescue: PR #{args.pr} in {wt} ({args.model}, effort={args.effort})...")
    rc, out, err = invoke_rescue(args.pr, args.model, args.effort, prompt_path, wt)

    if rc == 127:
        print(err or "codex plugin unavailable", file=sys.stderr)
        if manifest_present:
            update_manifest_entry(manifest_path, args.branch, {
                "rescue_status": "failed",
                "rescue_error": "codex plugin unavailable",
                "rescue_started_at": started_at,
            })
        return 127

    if rc != 0:
        print(f"✗ codex task --background failed (rc={rc}): {err[:500]}", file=sys.stderr)
        if manifest_present:
            update_manifest_entry(manifest_path, args.branch, {
                "rescue_status": "failed",
                "rescue_error": (err or out)[:500],
                "rescue_started_at": started_at,
            })
        return 2

    # Parse the queued-job descriptor: { jobId, status: "queued", title, logFile, summary? }
    try:
        payload = json.loads(out)
    except (ValueError, TypeError):
        print(f"✗ could not parse codex queue response: {out[:500]}", file=sys.stderr)
        if manifest_present:
            update_manifest_entry(manifest_path, args.branch, {
                "rescue_status": "failed",
                "rescue_error": "unparseable queue response",
                "rescue_started_at": started_at,
            })
        return 2

    job_id = payload.get("jobId") or ""
    if not job_id:
        print(f"✗ no jobId in queue response: {payload}", file=sys.stderr)
        return 2

    queued_status = payload.get("status", "queued")
    title = payload.get("title", "")
    log_file = payload.get("logFile", "")
    print(f"  ✓ queued: jobId={job_id} status={queued_status}")
    if log_file:
        print(f"    logFile: {log_file}")

    if manifest_present:
        update_manifest_entry(manifest_path, args.branch, {
            "rescue_review_id": job_id,
            "rescue_started_at": started_at,
            "rescue_status": "running",
            "rescue_pr_number": args.pr,
            "rescue_model": args.model,
            "rescue_effort": args.effort,
            "rescue_title": title,
            "rescue_log_file": log_file,
        })
        print(f"  ✓ manifest updated: {manifest_path}")

    if not args.wait:
        return 0

    # --wait: block on status --wait until terminal
    print(f"  waiting up to {args.timeout_ms / 1000:.0f}s for rescue to finish...")
    rc, status_payload, err = wait_for_rescue(job_id, wt, args.timeout_ms)
    finished_at = utc_now_iso()

    if rc == 127:
        print(err, file=sys.stderr)
        return 127
    if rc != 0 or status_payload is None:
        print(f"✗ status --wait failed: rc={rc}: {err[:500]}", file=sys.stderr)
        if manifest_present:
            update_manifest_entry(manifest_path, args.branch, {
                "rescue_status": "failed",
                "rescue_error": (err or "wait failed")[:500],
                "rescue_finished_at": finished_at,
            })
        return 2

    job = status_payload.get("job") or {}
    final_status = job.get("status", "unknown")
    if final_status == "completed":
        print(f"  ✓ rescue completed (jobId={job_id})")
    elif final_status in {"failed", "cancelled"}:
        print(f"✗ rescue {final_status} (jobId={job_id})", file=sys.stderr)
    else:
        # Could be 'queued' or 'running' if status --wait timed out
        print(f"⚠  rescue not terminal yet: status={final_status} (jobId={job_id})", file=sys.stderr)

    if manifest_present:
        update_manifest_entry(manifest_path, args.branch, {
            "rescue_status": final_status,
            "rescue_finished_at": finished_at,
            "rescue_phase": job.get("phase", ""),
            "rescue_elapsed": job.get("elapsed", ""),
        })

    if final_status == "completed":
        return 0
    if final_status in {"queued", "running"}:
        return 1  # timed out before terminal
    return 2  # failed or cancelled


if __name__ == "__main__":
    sys.exit(main())
