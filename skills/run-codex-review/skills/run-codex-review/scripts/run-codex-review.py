#!/usr/bin/env python3
"""Wrap the OpenAI Codex Claude Code plugin's review for one branch; normalize
output to the round-log JSON schema in references/codex-review-contract.md.

Invokes `node codex-companion.mjs review --json` (or `adversarial-review --json`)
inside the branch's worktree. The companion script ignores `--background` for
review subcommands — it always runs synchronously. Each parallel coordinator
runs its own subprocess; parallelism comes from concurrent invocations, not
from background flags.

Usage:
    python3 run-codex-review.py --branch feat/foo --worktree /path/to/wt
    python3 run-codex-review.py --branch feat/foo --worktree /path/to/wt --dry-run
    python3 run-codex-review.py --branch feat/foo --worktree /path/to/wt \\
        --base main --timeout 1500 --mode review

    # Adversarial mode (structured findings — no regex, severities are
    # critical|high|medium|low):
    python3 run-codex-review.py --branch feat/foo --worktree /path/to/wt --mode adversarial

Exit codes:
    0  review available; round log written
    1  timeout (manifest marked 'timeout'; caller decides retry)
    2  codex/CLI failed (manifest marked 'failed'; caller decides FAILED)
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

DEFAULT_TIMEOUT = 1500  # 25 min wall-clock cap; Codex review can hang on remote tools
DEFAULT_MODE = "review"  # native (free-form parsed). "adversarial" → structured findings.


# ─── codex-companion.mjs discovery (version-agnostic) ─────────────────────────

def _find_codex_companion() -> Path:
    """Discover the OpenAI Codex plugin's codex-companion.mjs.

    Resolution order:
      1. ${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs (env var set by Claude
         Code harness when the plugin is loaded).
      2. Latest installed version under
         ~/.claude/plugins/cache/openai-codex/codex/<version>/scripts/codex-companion.mjs
         (semver-sorted; latest wins; falls back to lex-sort for non-semver dirs).

    Raises FileNotFoundError if neither resolves. Plugin source:
      https://github.com/openai/codex-plugin-cc/tree/main/plugins/codex
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


def repo_local_default(wt: Path, name: str) -> str:
    """Repo-local default for state files; main agent's session may pass --manifest
    explicitly. This default prevents cross-repo /tmp collisions."""
    # Find repo root from the worktree path (handle the worktree's own .git file)
    rc, out, _ = sh(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=wt)
    if rc == 0 and out:
        # git-common-dir points at the main checkout's .git directory; its parent is repo root
        return str(Path(out).parent / name)
    return f"/tmp/{name}"  # last-resort fallback


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


# ─── Codex invocation ─────────────────────────────────────────────────────────

def invoke_codex(branch: str, base: str, wt: Path, mode: str, timeout: int) -> tuple[int, str, str]:
    """Spawn codex-companion.mjs <mode> --base <ref> --json synchronously.

    The companion script's review and adversarial-review subcommands always run
    foreground regardless of any --background flag. Returns (rc, stdout, stderr).
    """
    try:
        companion = _find_codex_companion()
    except FileNotFoundError as e:
        return 127, "", str(e)

    subcmd = "review" if mode == "review" else "adversarial-review"
    cmd = [
        "node", str(companion), subcmd,
        "--base", base,
        "--scope", "branch",
        "--json",
    ]
    return sh(cmd, cwd=wt, timeout=timeout)


# ─── Output normalization ─────────────────────────────────────────────────────

# Severity tokens we recognize in free-form review output. Codex's native review
# emits items as `[Px] Title — file:line` or `[severity] Title — file:line`.
_SEV_TOKEN = r"P\d+|critical|high|medium|low"

_FREEFORM_PATTERN = re.compile(
    rf"^\s*\[(?P<sev>{_SEV_TOKEN})\]\s*"
    r"(?P<title>.+?)\s*[—–-]+\s*"
    r"(?P<file>[^\s:]+):(?P<line_start>\d+)(?:-(?P<line_end>\d+))?\s*$"
    rf"(?P<body>(?:\n(?!\s*\[(?:{_SEV_TOKEN})\]).*)*)",
    re.MULTILINE | re.IGNORECASE,
)


def parse_freeform_items(text: str) -> list[dict]:
    """Regex-parse Codex's free-form review text into items[].

    Matches header lines like:
        [P1] Title here — src/foo.ts:42
        <body line 1>
        <body line 2>

        [P2] Next item — src/bar.ts:13-15
        ...

    Severity tokens: P1 / P2 / P3 / P4 / critical / high / medium / low.
    """
    items: list[dict] = []
    for i, m in enumerate(_FREEFORM_PATTERN.finditer(text)):
        items.append({
            "id": f"cdx-{i}",
            "severity_raw": m["sev"].lower(),
            "file": m["file"],
            "line": int(m["line_start"]),
            "body": (m["body"] or "").strip() or m["title"].strip(),
        })
    return items


def normalize_review(raw_json: str, branch: str, head: str,
                     started_at: str, finished_at: str) -> dict:
    """Convert codex-companion's --json output to the round-log schema.

    Two input shapes:

    1. review (native):
        {
          "review": "Review",
          "target": {...}, "threadId": "...",
          "codex": { "status": 0, "stdout": "<free-form text>", "stderr": "...", "reasoning": null }
        }

    2. adversarial-review (structured):
        {
          "review": "Adversarial Review",
          "result": {
            "verdict": "approve|needs-attention",
            "summary": "...",
            "findings": [{ "severity": "critical|high|medium|low",
                           "title": "...", "body": "...",
                           "file": "...", "line_start": N, "line_end": N,
                           "confidence": 0.0..1.0,
                           "recommendation": "..." }],
            "next_steps": [...]
          },
          "rawOutput": "...", "parseError": null, ...
        }

    Output (round-log per references/codex-review-contract.md):
        {
          "review_id", "branch", "head_sha",
          "started_at", "finished_at",
          "raw_text", "items": [{ "id", "severity_raw", "file", "line", "body" }]
        }
    """
    try:
        payload = json.loads(raw_json)
    except (ValueError, TypeError):
        # Companion didn't emit valid JSON — degenerate path; pass raw text through
        # so the classifier's regex fallback can still try.
        return {
            "review_id": "",
            "branch": branch,
            "head_sha": head,
            "started_at": started_at,
            "finished_at": finished_at,
            "raw_text": raw_json,
            "items": [],
        }

    review_id = str(payload.get("threadId") or "")

    if payload.get("review") == "Adversarial Review":
        result = payload.get("result") or {}
        findings = result.get("findings") or []
        items = []
        for i, f in enumerate(findings):
            title = (f.get("title") or "").strip()
            body = (f.get("body") or "").strip()
            recommendation = (f.get("recommendation") or "").strip()
            combined = "\n\n".join(p for p in (title, body, recommendation) if p)
            items.append({
                "id": f"adv-{i}",
                "severity_raw": str(f.get("severity") or "unknown").lower(),
                "file": f.get("file") or "",
                "line": int(f.get("line_start") or 0),
                "body": combined or title,
            })
        raw_text = payload.get("rawOutput") or json.dumps(result, indent=2)
    else:
        # Native review — free-form text in codex.stdout.
        raw_text = (payload.get("codex") or {}).get("stdout") or ""
        items = parse_freeform_items(raw_text)

    return {
        "review_id": review_id,
        "branch": branch,
        "head_sha": head,
        "started_at": started_at,
        "finished_at": finished_at,
        "raw_text": raw_text,
        "items": items,
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--base", default="main")
    ap.add_argument("--manifest",
                    help="Path to the manifest JSON. Default: <repo-root>/.codex-review-manifest.json")
    ap.add_argument("--rounds-dir",
                    help="Directory for round-log JSON files. Default: <repo-root>/.codex-review-rounds/")
    ap.add_argument("--output",
                    help="Override round-log output path. If set, overrides --rounds-dir + --branch + round-N path computation.")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                    help=f"Wall-clock cap in seconds. Default {DEFAULT_TIMEOUT}s. "
                         "Codex review can hang on remote tools (codebase-search APIs etc.); "
                         "on hang, exit non-zero with terminal_reason 'review-hang past wall-clock cap'.")
    ap.add_argument("--mode", choices=["review", "adversarial"], default=DEFAULT_MODE,
                    help="codex-companion subcommand. 'review' = native (free-form text parsed via regex; "
                         "default). 'adversarial' = adversarial-review (structured findings; severities are "
                         "critical|high|medium|low).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Resolve the codex-companion path, validate worktree state, print intended invocation. Don't run codex.")
    args = ap.parse_args()

    wt = Path(args.worktree)
    if not wt.is_dir():
        print(f"worktree not found: {wt}", file=sys.stderr)
        return 2

    # Default manifest + rounds-dir to repo-local paths (avoids /tmp cross-repo collisions)
    manifest_path = args.manifest or repo_local_default(wt, ".codex-review-manifest.json")
    rounds_dir = args.rounds_dir or repo_local_default(wt, ".codex-review-rounds")

    # Pre-flight: branch is checked out in the worktree
    rc, branch_at_wt, _ = sh(["git", "symbolic-ref", "--short", "HEAD"], cwd=wt)
    if rc != 0 or branch_at_wt != args.branch:
        print(f"worktree {wt} is not on branch {args.branch} (HEAD={branch_at_wt or 'detached'})", file=sys.stderr)
        return 2

    head = head_sha(str(wt))
    started_at = utc_now_iso()

    if args.dry_run:
        try:
            companion = _find_codex_companion()
        except FileNotFoundError as e:
            print(f"DRY-RUN: {e}", file=sys.stderr)
            return 127
        subcmd = "review" if args.mode == "review" else "adversarial-review"
        print(f"DRY-RUN: would invoke")
        print(f"  node {companion} {subcmd} --base {args.base} --scope branch --json")
        print(f"  cwd:         {wt}")
        print(f"  branch:      {args.branch}")
        print(f"  head:        {head}")
        print(f"  manifest:    {manifest_path}")
        print(f"  rounds-dir:  {rounds_dir}")
        print(f"  timeout:     {args.timeout}s")
        print(f"  mode:        {args.mode}")
        return 0

    print(f"running codex-companion {args.mode} (sync) in {wt} ... timeout={args.timeout}s")
    rc, stdout, stderr = invoke_codex(args.branch, args.base, wt, args.mode, args.timeout)
    finished_at = utc_now_iso()

    if rc == 127:
        # Plugin missing — caller surfaces FAILED with the install instructions in stderr
        print(stderr or "codex plugin unavailable", file=sys.stderr)
        update_manifest_entry(manifest_path, args.branch, {"last_status": "plugin-missing"})
        return 127

    if rc == 124:
        print(f"✗ codex review timed out after {args.timeout}s", file=sys.stderr)
        update_manifest_entry(manifest_path, args.branch, {
            "last_review_at": finished_at,
            "last_status": "timeout",
            "terminal_reason": "review-hang past wall-clock cap",
        })
        return 1

    if rc != 0:
        # Companion exited non-zero; could be a Codex error or a parser error.
        # The JSON envelope might still be on stdout; if so, fall through to
        # normalize. Otherwise mark failed.
        if not stdout.strip():
            print(f"✗ codex review failed (rc={rc}): {stderr[:500]}", file=sys.stderr)
            update_manifest_entry(manifest_path, args.branch, {
                "last_review_at": finished_at,
                "last_status": "failed",
            })
            return 2
        # Try to normalize; some Codex paths exit non-zero even on usable output
        print(f"⚠  codex review exited rc={rc}; attempting to parse stdout anyway", file=sys.stderr)

    review = normalize_review(stdout, args.branch, head, started_at, finished_at)
    round_n = get_round_for_branch(manifest_path, args.branch) + 1

    if args.output:
        log_path = args.output
    else:
        log_path = os.path.join(rounds_dir, f"{slug(args.branch)}.{round_n:02d}.json")

    atomic_write(log_path, json.dumps(review, indent=2))
    print(f"  ✓ round log written: {log_path} (items={len(review['items'])})")

    history_entry = {
        "round": round_n,
        "review_id": review["review_id"],
        "completed_at": finished_at,
        "items_found": len(review["items"]),
    }
    update_manifest_entry(manifest_path, args.branch, {
        "last_review_id": review["review_id"],
        "last_review_at": finished_at,
        "last_status": "reviewed",
        "rounds": round_n,
        "head_sha_current": head,
    }, history_entry=history_entry)
    print(f"  ✓ manifest updated: rounds={round_n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
