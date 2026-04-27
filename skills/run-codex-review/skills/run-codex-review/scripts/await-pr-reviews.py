#!/usr/bin/env python3
"""Phase 6 wait + gather: 900s base + adaptive end + per-PR review aggregation.

Wait for review streams (codex rescue + external bots: copilot, greptile, devin)
to land on a PR. Adaptive end condition:
  - Wait base_wait seconds (default 900s = 15 min).
  - Loop:
      - If newest comment is older than quiet_window (default 180s = 3 min): break.
      - Elif (now - start_time) >= total_cap (default 1800s = 30 min): break.
      - Else: wait extension seconds (default 300s = 5 min); re-check.
  - Gather all reviews + comments via gh API.
  - Normalize per-source items into JSON.
  - Write to <rounds-dir>/<slug>.pr-reviews.json.

Usage:
    python3 await-pr-reviews.py --pr 42 --branch feat/foo
    python3 await-pr-reviews.py --pr 42 --branch feat/foo \\
        --base-wait 900 --quiet-window 180 --extension 300 --total-cap 1800
    python3 await-pr-reviews.py --pr 42 --branch feat/foo --no-wait

Exit codes:
    0  reviews gathered (with at least one source)
    1  wait terminated by total cap (still gathered what we have)
    2  not in a git repo / fatal subprocess error
    3  PR not found / gh CLI failure
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
DEFAULT_BASE_WAIT = 900       # 15 min
DEFAULT_QUIET_WINDOW = 180    # 3 min
DEFAULT_EXTENSION = 300       # 5 min
DEFAULT_TOTAL_CAP = 1800      # 30 min
DEFAULT_POLL_INTERVAL = 60    # 1 min between checks during waits

# External bot author logins (lowercased). Adjust per your repo's installs.
BOT_LOGINS = {
    "copilot": {"copilot", "copilot[bot]", "github-copilot[bot]", "github-actions[bot]"},
    "greptile": {"greptile-apps[bot]", "greptile[bot]", "greptileai[bot]"},
    "devin": {"devin-ai-integration[bot]", "devin[bot]", "devin-ai[bot]"},
    "codex-rescue": {"codex[bot]", "codex-rescue[bot]", "openai-codex[bot]"},
}


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


def slug(branch: str) -> str:
    return branch.replace("/", "-")


def atomic_write(path: str, content: str):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".await.", suffix=".tmp")
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


def update_manifest_entry(path: str, branch: str, updates: dict):
    manifest = load_manifest(path)
    if manifest is None:
        return
    for entry in manifest.get("branches", []):
        if entry.get("branch") == branch:
            entry.update(updates)
            entry["updated_at"] = utc_now_iso()
            break
    atomic_write(path, json.dumps(manifest, indent=2))


def fork_owner_repo(manifest: dict | None) -> str | None:
    return manifest.get("fork_owner_repo") if manifest else None


def gh_pr_view(pr: int, repo: str) -> dict | None:
    rc, out, _ = sh([
        "gh", "pr", "view", str(pr), "--repo", repo,
        "--json", "number,url,baseRefName,headRefName,title,body,state",
    ])
    if rc != 0:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def gh_pr_reviews(pr: int, repo: str) -> list[dict]:
    """All reviews (top-level: APPROVED/CHANGES_REQUESTED/COMMENTED with body)."""
    rc, out, _ = sh([
        "gh", "api", f"repos/{repo}/pulls/{pr}/reviews", "--paginate",
    ])
    if rc != 0:
        return []
    try:
        data = json.loads(out)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def gh_pr_comments(pr: int, repo: str) -> list[dict]:
    """Inline review comments attached to specific lines."""
    rc, out, _ = sh([
        "gh", "api", f"repos/{repo}/pulls/{pr}/comments", "--paginate",
    ])
    if rc != 0:
        return []
    try:
        data = json.loads(out)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def gh_issue_comments(pr: int, repo: str) -> list[dict]:
    """Top-level PR comments (not inline). PRs use the issue comments endpoint."""
    rc, out, _ = sh([
        "gh", "api", f"repos/{repo}/issues/{pr}/comments", "--paginate",
    ])
    if rc != 0:
        return []
    try:
        data = json.loads(out)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def parse_iso(ts: str) -> float | None:
    """Parse GitHub's ISO timestamps to unix epoch seconds. None on failure."""
    if not ts:
        return None
    # GitHub returns "2026-04-26T11:30:00Z"
    try:
        return datetime.strptime(ts.rstrip("Z"), "%Y-%m-%dT%H:%M:%S").replace(
            tzinfo=timezone.utc
        ).timestamp()
    except ValueError:
        # Try with fractional seconds
        try:
            return datetime.strptime(ts.rstrip("Z").split(".")[0], "%Y-%m-%dT%H:%M:%S").replace(
                tzinfo=timezone.utc
            ).timestamp()
        except ValueError:
            return None


def classify_author(login: str) -> str:
    """Map a GitHub author login to a source name (codex-rescue / copilot / greptile / devin / human:<login>)."""
    if not login:
        return "human:unknown"
    lo = login.lower()
    for source, aliases in BOT_LOGINS.items():
        if lo in aliases:
            return source
    return f"human:{login}"


def extract_items_from_review(review: dict, source: str) -> list[dict]:
    """Top-level review may have a body (the summary) — turn it into one item."""
    body = (review.get("body") or "").strip()
    items = []
    if body:
        items.append({
            "id": f"{source}-review-{review.get('id')}",
            "severity_raw": review.get("state", "COMMENTED"),
            "file": None,
            "line": None,
            "body": body,
            "submitted_at": review.get("submitted_at"),
            "author": (review.get("user") or {}).get("login"),
        })
    return items


def extract_items_from_comment(comment: dict, source: str, kind: str) -> dict:
    return {
        "id": f"{source}-{kind}-{comment.get('id')}",
        "severity_raw": "comment",
        "file": comment.get("path"),
        "line": comment.get("line") or comment.get("original_line"),
        "body": (comment.get("body") or "").strip(),
        "submitted_at": comment.get("created_at") or comment.get("submitted_at"),
        "author": (comment.get("user") or {}).get("login"),
    }


def fetch_all_streams(pr: int, repo: str) -> dict:
    """Return {source: {raw_review_count, items[]}, ...} keyed by source name."""
    streams: dict[str, dict] = {}

    # Top-level reviews (with summary body)
    for review in gh_pr_reviews(pr, repo):
        login = (review.get("user") or {}).get("login")
        source = classify_author(login)
        for item in extract_items_from_review(review, source):
            streams.setdefault(source, {"items": [], "raw_count": 0})
            streams[source]["items"].append(item)
            streams[source]["raw_count"] += 1

    # Inline review comments
    for comment in gh_pr_comments(pr, repo):
        login = (comment.get("user") or {}).get("login")
        source = classify_author(login)
        item = extract_items_from_comment(comment, source, "inline")
        streams.setdefault(source, {"items": [], "raw_count": 0})
        streams[source]["items"].append(item)
        streams[source]["raw_count"] += 1

    # Top-level PR comments (issue comments endpoint)
    for comment in gh_issue_comments(pr, repo):
        login = (comment.get("user") or {}).get("login")
        source = classify_author(login)
        item = extract_items_from_comment(comment, source, "top-level")
        streams.setdefault(source, {"items": [], "raw_count": 0})
        streams[source]["items"].append(item)
        streams[source]["raw_count"] += 1

    return streams


def newest_comment_age(streams: dict) -> float | None:
    """Return age (in seconds) of the newest comment across all streams, or None if no comments."""
    newest_ts = None
    for source_data in streams.values():
        for item in source_data["items"]:
            ts = parse_iso(item.get("submitted_at"))
            if ts is not None and (newest_ts is None or ts > newest_ts):
                newest_ts = ts
    if newest_ts is None:
        return None
    return time.time() - newest_ts


def adaptive_wait(
    pr: int, repo: str,
    base_wait: int, quiet_window: int, extension: int, total_cap: int,
    poll_interval: int,
) -> tuple[dict, str, int]:
    """Run the adaptive wait. Returns (final_streams, terminated_by, total_seconds_waited)."""
    start_time = time.time()
    print(f"  base wait: {base_wait}s ({base_wait // 60} min)...")

    # Phase A: base wait, polling at poll_interval to surface progress
    deadline_a = start_time + base_wait
    while time.time() < deadline_a:
        # Periodic progress probe
        time.sleep(min(poll_interval, deadline_a - time.time()))
        streams = fetch_all_streams(pr, repo)
        n_items = sum(s["raw_count"] for s in streams.values())
        elapsed = int(time.time() - start_time)
        print(f"    [{elapsed}s] {len(streams)} sources, {n_items} items so far", flush=True)

    # Phase B: adaptive — extend if comments still flowing
    while True:
        elapsed = int(time.time() - start_time)
        if elapsed >= total_cap:
            print(f"    [{elapsed}s] total cap reached; stopping")
            streams = fetch_all_streams(pr, repo)
            return streams, "total_cap", elapsed

        streams = fetch_all_streams(pr, repo)
        age = newest_comment_age(streams)
        if age is None:
            print(f"    [{elapsed}s] no comments yet; treating as quiet")
            return streams, "quiet_no_comments", elapsed
        if age >= quiet_window:
            print(f"    [{elapsed}s] newest comment {int(age)}s old (≥ {quiet_window}s quiet); proceeding")
            return streams, "quiet", elapsed

        # Comments still arriving — extend
        time_left = total_cap - elapsed
        wait_for = min(extension, time_left)
        if wait_for <= 0:
            return streams, "total_cap", elapsed
        print(f"    [{elapsed}s] newest comment {int(age)}s old (< {quiet_window}s); waiting +{wait_for}s")
        time.sleep(wait_for)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--rounds-dir", default=DEFAULT_ROUNDS_DIR)
    ap.add_argument("--base-wait", type=int, default=DEFAULT_BASE_WAIT)
    ap.add_argument("--quiet-window", type=int, default=DEFAULT_QUIET_WINDOW)
    ap.add_argument("--extension", type=int, default=DEFAULT_EXTENSION)
    ap.add_argument("--total-cap", type=int, default=DEFAULT_TOTAL_CAP)
    ap.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL)
    ap.add_argument("--no-wait", action="store_true",
                    help="skip the wait; gather what's there now and return")
    args = ap.parse_args()

    manifest = load_manifest(args.manifest)
    if manifest is None:
        print(f"manifest absent or unreadable: {args.manifest}", file=sys.stderr)
        return 2

    repo = fork_owner_repo(manifest)
    if not repo:
        print("manifest has no fork_owner_repo set; cannot query gh", file=sys.stderr)
        return 2

    pr_info = gh_pr_view(args.pr, repo)
    if pr_info is None:
        print(f"could not fetch PR #{args.pr} from {repo}", file=sys.stderr)
        return 3

    print(f"PR:     #{args.pr}  {pr_info.get('url')}")
    print(f"branch: {args.branch}")
    print(f"repo:   {repo}")
    print(f"mode:   {'no-wait gather' if args.no_wait else 'adaptive wait + gather'}")

    if args.no_wait:
        print("")
        streams = fetch_all_streams(args.pr, repo)
        terminated_by = "no_wait"
        elapsed = 0
    else:
        print(f"  base_wait={args.base_wait}s  quiet_window={args.quiet_window}s  "
              f"extension={args.extension}s  total_cap={args.total_cap}s")
        print("")
        streams, terminated_by, elapsed = adaptive_wait(
            args.pr, repo,
            base_wait=args.base_wait,
            quiet_window=args.quiet_window,
            extension=args.extension,
            total_cap=args.total_cap,
            poll_interval=args.poll_interval,
        )

    # Build output JSON
    output = {
        "pr_number": args.pr,
        "pr_url": pr_info.get("url"),
        "branch": args.branch,
        "fetched_at": utc_now_iso(),
        "wait_terminated_by": terminated_by,
        "wait_seconds": elapsed,
        "sources": [
            {"source": source, "raw_count": data["raw_count"], "items": data["items"]}
            for source, data in sorted(streams.items())
        ],
    }

    out_path = os.path.join(args.rounds_dir, f"{slug(args.branch)}.pr-reviews.json")
    atomic_write(out_path, json.dumps(output, indent=2))
    print("")
    print(f"  ✓ gathered {sum(s['raw_count'] for s in streams.values())} items "
          f"across {len(streams)} sources")
    print(f"  ✓ written: {out_path}")

    update_manifest_entry(args.manifest, args.branch, {
        "pr_number": args.pr,
        "pr_url": pr_info.get("url"),
        "pr_reviews_path": out_path,
        "pr_reviews_terminated_by": terminated_by,
        "pr_reviews_wait_seconds": elapsed,
    })

    return 1 if terminated_by == "total_cap" else 0


if __name__ == "__main__":
    sys.exit(main())
