#!/usr/bin/env python3
"""Live table of branch round status. Read-only.

Reads the manifest + per-branch round logs and prints a scannable table
showing each branch's progress through the per-branch fix loop.

Usage:
    python3 loop-status.py
    python3 loop-status.py --watch
    python3 loop-status.py --watch --refresh 5
    python3 loop-status.py --json

Exit codes:
    0  always (read-only)
    2  not in a git repo / manifest unreadable
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_MANIFEST = "/tmp/codex-review-manifest.json"
DEFAULT_ROUNDS_DIR = "/tmp/codex-review-rounds/"
DEFAULT_STALE_MINUTES = 60


def load_manifest(path: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def slug_for(branch: str) -> str:
    return branch.replace("/", "-")


def latest_round_log_mtime(rounds_dir: str, branch: str) -> float | None:
    if not os.path.isdir(rounds_dir):
        return None
    prefix = slug_for(branch) + "."
    latest = None
    for entry in os.listdir(rounds_dir):
        if not entry.startswith(prefix) or not entry.endswith(".json"):
            continue
        full = os.path.join(rounds_dir, entry)
        try:
            mt = os.path.getmtime(full)
            if latest is None or mt > latest:
                latest = mt
        except OSError:
            pass
    return latest


def is_stale(mtime: float | None, stale_minutes: int) -> bool:
    if mtime is None:
        return False
    return (time.time() - mtime) > (stale_minutes * 60)


def derive_state(entry: dict, mtime: float | None, stale_minutes: int) -> str:
    """Compute the displayed state from manifest status + heartbeat."""
    status = entry.get("status", "?")
    if status in ("DONE", "CAP-REACHED", "BLOCKED", "FAILED"):
        return status
    if status == "SPAWNED":
        return "spawned"
    if status == "IN-LOOP":
        if is_stale(mtime, stale_minutes):
            return "STALE"
        return "in-loop"
    return status


def derive_last_status(entry: dict) -> str:
    summary = entry.get("last_classifier_summary") or {}
    if not summary:
        return "—"
    if entry.get("status") == "DONE":
        return "no-major"
    if entry.get("status") == "CAP-REACHED":
        return "cap"
    major = summary.get("major_n", 0)
    unc = summary.get("unclassified_n", 0)
    if major == 0 and unc == 0:
        return "no-major"
    return f"{major}+{unc}u"


def shorten(s: str, width: int) -> str:
    if s is None:
        return "?"
    s = str(s)
    return s if len(s) <= width else s[: width - 1] + "…"


def render_table(manifest: dict, rounds_dir: str, stale_minutes: int) -> str:
    branches = manifest.get("branches", []) if manifest else []
    if not branches:
        return "no branches in manifest"

    rows = []
    for entry in branches:
        branch = entry.get("branch", "?")
        mt = latest_round_log_mtime(rounds_dir, branch)
        state = derive_state(entry, mt, stale_minutes)
        last_status = derive_last_status(entry)
        rounds = entry.get("rounds", 0)
        wt = Path(entry.get("worktree_path", "?")).name
        age = "—"
        if mt is not None:
            age_min = int((time.time() - mt) / 60)
            age = f"{age_min}m"
        rows.append({
            "branch": branch,
            "worktree": wt,
            "rounds": rounds,
            "last_status": last_status,
            "state": state,
            "age": age,
        })

    # column widths
    w_b = max(len("Branch"), max((len(r["branch"]) for r in rows), default=6))
    w_w = max(len("Worktree"), max((len(r["worktree"]) for r in rows), default=8))
    w_r = max(len("Rounds"), 4)
    w_l = max(len("Last"), max((len(r["last_status"]) for r in rows), default=4))
    w_s = max(len("State"), max((len(r["state"]) for r in rows), default=5))
    w_a = max(len("Age"), 4)

    # cap widths to keep the table readable
    w_b = min(w_b, 32)
    w_w = min(w_w, 36)

    lines = []
    header = (
        f"{'Branch':<{w_b}}  {'Worktree':<{w_w}}  "
        f"{'Rounds':>{w_r}}  {'Last':<{w_l}}  {'State':<{w_s}}  {'Age':>{w_a}}"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for r in rows:
        lines.append(
            f"{shorten(r['branch'], w_b):<{w_b}}  "
            f"{shorten(r['worktree'], w_w):<{w_w}}  "
            f"{r['rounds']:>{w_r}}  "
            f"{shorten(r['last_status'], w_l):<{w_l}}  "
            f"{shorten(r['state'], w_s):<{w_s}}  "
            f"{r['age']:>{w_a}}"
        )

    # totals
    total = len(branches)
    by_state = {}
    for r in rows:
        by_state[r["state"]] = by_state.get(r["state"], 0) + 1
    breakdown = ", ".join(f"{k}: {v}" for k, v in sorted(by_state.items()))
    lines.append("")
    lines.append(f"total: {total}  ({breakdown})")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--rounds-dir", default=DEFAULT_ROUNDS_DIR)
    ap.add_argument("--stale-minutes", type=int, default=DEFAULT_STALE_MINUTES)
    ap.add_argument("--watch", action="store_true", help="redraw every --refresh seconds")
    ap.add_argument("--refresh", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    def render_once():
        manifest = load_manifest(args.manifest)
        if manifest is None:
            return f"manifest absent or unreadable: {args.manifest}"
        if args.json:
            return json.dumps(manifest, indent=2, default=str)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        return f"# loop-status @ {ts}\n\n" + render_table(
            manifest, args.rounds_dir, args.stale_minutes
        )

    if not args.watch:
        out = render_once()
        print(out)
        return 0

    # watch mode
    try:
        while True:
            sys.stdout.write("\033[2J\033[H")  # clear + home
            sys.stdout.write(render_once())
            sys.stdout.write("\n")
            sys.stdout.flush()
            time.sleep(args.refresh)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
