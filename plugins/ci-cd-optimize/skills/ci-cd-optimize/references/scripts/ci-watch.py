#!/usr/bin/env python3
"""ci-watch.py — provider-neutral, diff-gated CI watcher for agent event tools.

Emits only state CHANGES plus liveness heartbeats, and guarantees exactly one
terminal line on every exit path. Silence past the deadline is structurally
impossible. Designed to be armed via a background-event tool (e.g. Claude Code's
Monitor) so the session keeps working while CI runs.

BUILT-IN MODE (GitHub Actions; needs `gh` authenticated):

    ci-watch.py --sha <40-char-sha> [--branch <branch>] [--repo owner/name]

  Watches every workflow triggered for that SHA. Because it queries by SHA, one
  watch survives "push, then open a PR" — runs registering later are picked up.

GENERIC MODE (GitLab, Buildkite, CircleCI, EAS, any deploy API):

    ci-watch.py --cmd '<probe>'

  PROBE CONTRACT: print one line per watched unit, "<name>: <state>". Lines are
  diffed as a set, so only changes are emitted. When the watch should end, print
  "TERMINAL: <verdict...>" — the first word selects the exit code (see EXIT
  CODES below). Exit non-zero from the probe itself to signal a probe error. Pin identifiers
  (SHA, build id) BEFORE arming; never re-resolve a moving ref inside the probe.

EVENTS
  CI-RUN   units registered
  CI-CHG   a unit changed state (act on the first failure)
  CI-HB    liveness tick; keep below the model's prompt-cache TTL
  CI-ERR   probe failing repeatedly
  CI-DONE  terminal verdict — always printed exactly once

EXIT CODES: 0 success (or expected no-run) · 1 failure · 2 timeout/no-run/probe-dead
            · 3 superseded — differentiated so `watch && deploy` cannot proceed on a non-verdict

Python 3 stdlib only.
"""
import argparse
import json
import math
import re
import subprocess
import sys
import time

PROBE_CAP_SEC = 45
OK_CONCLUSIONS = {"success", "skipped", "neutral"}


def emit(line):
    print(line, flush=True)


def run(cmd, timeout=PROBE_CAP_SEC):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def gh_json(args, timeout=PROBE_CAP_SEC):
    out = run(["gh"] + args, timeout)
    if out.returncode != 0:
        raise RuntimeError((out.stderr.strip() or f"exit {out.returncode}")[:200])
    return json.loads(out.stdout or "[]")


def branch_tip(branch, repo, timeout):
    """Resolve the branch's real tip.

    Deliberately NOT `gh run list --branch --limit 1`: that returns the latest
    RUN, which for a branch whose newest push has not registered yet is an OLDER
    sha — reporting the newest commit as superseded by its own ancestor. The ref
    is the only correct source.
    """
    if repo:
        ref = gh_json(["api", f"repos/{repo}/git/ref/heads/{branch}"], timeout)
        return ref.get("object", {}).get("sha", "")
    out = run(["git", "ls-remote", "origin", f"refs/heads/{branch}"], timeout)
    if out.returncode != 0:
        raise RuntimeError((out.stderr.strip() or "git ls-remote failed")[:200])
    return out.stdout.split()[0] if out.stdout.strip() else ""


def github_probe(sha, branch, repo, run_limit, timeout):
    """Return (state_lines, terminal_or_None) for a pinned GitHub Actions SHA."""
    repo_args = ["--repo", repo] if repo else []
    runs = gh_json(repo_args + [
        "run", "list", "--commit", sha, "--limit", str(run_limit),
        "--json", "databaseId,workflowName,status,conclusion",
    ], timeout)
    newer = ""
    if branch:
        tip = branch_tip(branch, repo, timeout)
        newer = tip if tip and tip != sha else ""

    state = set()
    for r in runs:
        label = r["status"] + (" -> " + r["conclusion"] if r.get("conclusion") else "")
        state.add(f"{r['workflowName']}: {label}")

    if runs and all(r["status"] == "completed" for r in runs):
        bad = sorted({r["workflowName"] for r in runs
                      if (r.get("conclusion") or "") not in OK_CONCLUSIONS})
        if not bad:
            return state, f"success ({len(runs)} workflows)"
        only_cancelled = all((r.get("conclusion") or "") in OK_CONCLUSIONS | {"cancelled"}
                             for r in runs)
        if newer and only_cancelled:
            return state, f"superseded by {newer[:9]} (auto-cancelled: {', '.join(bad)})"
        failed = next((r for r in runs if r.get("conclusion") == "failure"), None)
        hint = f" — logs: gh run view {failed['databaseId']} --log-failed" if failed else ""
        return state, f"failure — {', '.join(bad)}{hint}"

    if not runs and newer:
        return state, f"superseded by {newer[:9]} (no runs registered for {sha[:9]})"
    return state, None


def custom_probe(cmd, timeout):
    out = run(["bash", "-c", cmd], timeout)
    if out.returncode != 0:
        raise RuntimeError((out.stderr.strip() or out.stdout.strip()
                            or f"exit {out.returncode}")[:200])
    lines = [l.strip() for l in out.stdout.splitlines() if l.strip()]
    terminal = next((l.split(":", 1)[1].strip() for l in lines
                     if l.startswith("TERMINAL:")), None)
    return {l for l in lines if not l.startswith("TERMINAL:")}, terminal


def sha40(value):
    if not re.fullmatch(r"[0-9a-fA-F]{40}", value):
        raise argparse.ArgumentTypeError("must be a full 40-character hexadecimal SHA")
    return value.lower()


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def finite_nonnegative(value):
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("must be a finite non-negative number")
    return number


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--sha", type=sha40,
                     help="pinned 40-char SHA (GitHub built-in mode)")
    src.add_argument("--cmd", help="custom probe shell command")
    ap.add_argument("--branch", default="", help="enables superseded detection")
    ap.add_argument("--repo", default="", help="owner/name; defaults to cwd's remote")
    ap.add_argument("--run-limit", type=positive_int, default=1000,
                    help="maximum GitHub workflow runs to inspect (default: 1000)")
    ap.add_argument("--interval", type=float, default=20)
    ap.add_argument("--deadline-min", type=float, default=20)
    ap.add_argument("--reg-min", type=float, default=3,
                    help="give up if nothing registers within this many minutes")
    ap.add_argument("--expect-none", action="store_true",
                    help="zero runs is the expected outcome (path-filtered push)")
    ap.add_argument("--settle", type=finite_nonnegative, default=0,
                    help="seconds to hold an all-green state before declaring success, "
                         "so late-registering workflow_run follow-ups are observed")
    ap.add_argument("--hb-sec", type=float, default=150, help="0 disables heartbeats")
    ns = ap.parse_args()

    t0 = time.monotonic()
    deadline = t0 + ns.deadline_min * 60
    prev, last_emit, errs = None, t0, 0
    green_since = None

    while True:
        now = time.monotonic()
        remaining = deadline - now
        elapsed = now - t0
        if remaining <= 0:
            last = " · ".join(sorted(prev)) if prev else "nothing registered"
            emit(f"CI-DONE timeout at {ns.deadline_min:g}m · last state: {last}")
            return 2

        probe_timeout = min(PROBE_CAP_SEC, remaining)
        try:
            if ns.sha:
                state, terminal = github_probe(
                    ns.sha, ns.branch, ns.repo, ns.run_limit, probe_timeout
                )
            else:
                state, terminal = custom_probe(ns.cmd, probe_timeout)
        except Exception as exc:  # noqa: BLE001 — any probe failure is retryable
            errs += 1
            if errs == 3:
                emit(f"CI-ERR probe failing (3x consecutive): {exc}")
                last_emit = time.monotonic()
            if errs >= 10:
                emit(f"CI-DONE probe-dead after {errs} consecutive errors")
                return 2
            time.sleep(min(ns.interval, max(0, deadline - time.monotonic())))
            continue
        errs = 0

        if terminal:
            first = terminal.split()[0].lower()
            if first == "success" and ns.settle:
                if green_since is None:
                    green_since = time.monotonic()
                if time.monotonic() - green_since < ns.settle:
                    time.sleep(min(ns.interval, max(0, deadline - time.monotonic())))
                    continue
            emit(f"CI-DONE {terminal}")
            if first == "success":
                return 0
            if first == "no-run":
                return 0 if ns.expect_none else 2
            if first in {"timeout", "probe-dead"}:
                return 2
            return 3 if first == "superseded" else 1
        green_since = None

        if prev is None:
            if state:
                prev = state
                emit(f"CI-RUN registered {len(state)}: " + " · ".join(sorted(state)))
                last_emit = time.monotonic()
            elif elapsed > ns.reg_min * 60:
                why = ("expected — path filters matched nothing" if ns.expect_none
                       else "workflow not triggered? path filters? wrong sha?")
                emit(f"CI-DONE no-run — nothing registered in {ns.reg_min:g}m ({why})")
                return 0 if ns.expect_none else 2
        elif state and state - prev:
            for line in sorted(state - prev):
                emit(f"CI-CHG {line}")
            prev = state
            last_emit = time.monotonic()
        # an empty state after registration is a transient blip; keep prev

        now = time.monotonic()
        if ns.hb_sec and now - last_emit >= ns.hb_sec:
            emit(f"CI-HB {elapsed / 60:.0f}/{ns.deadline_min:g}m")
            last_emit = now

        time.sleep(min(ns.interval, max(0, deadline - time.monotonic())))


if __name__ == "__main__":
    sys.exit(main())
