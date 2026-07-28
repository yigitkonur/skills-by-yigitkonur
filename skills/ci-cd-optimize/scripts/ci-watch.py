#!/usr/bin/env python3
"""ci-watch.py — bounded, diff-gated CI watcher for agents and unattended sessions.

Stdlib only. Emits one line per state change and ALWAYS ends with a terminal verdict:

    CI-WATCH <repo>@<sha> deadline=<m>m
    CI-RUN   registered <n>: <name>: <state> ...
    CI-CHG   <name>: <state>
    CI-HB    <elapsed>/<deadline>m — <n> run(s) tracked
    CI-DONE  <success|failure|cancelled|timeout|no-run|superseded|probe-dead> — detail

Exit codes: 0 = success (or --expect-none satisfied) or superseded; 124 = timeout
(matches the GNU `timeout` convention); 1 = everything else.

Modes:
  GitHub (default): probes `gh run list --commit <sha>` — every workflow for the exact
  commit, never a branch tip.
  Generic (--cmd):  runs your probe each poll. The probe prints `<name>: <state>` lines
  and, when finished, one `TERMINAL: <verdict>` line. The watcher never guesses a
  verdict for a custom probe — the probe must declare it.

Design notes (each guards against a failure observed in real use):
  * Success is an explicit allowlist. "Did not fail" is not green — unknown
    conclusions count as failure.
  * Supersession is evaluated BEFORE failure. Under cancel-in-progress concurrency, a
    newer push cancels the old run; reporting that as `failure` sends the caller
    debugging a phantom break.
  * A settle window follows the first all-green state, because `workflow_run`-triggered
    follow-ups (deploy-after-build) do not exist yet when the first workflow passes.
  * The registration deadline is clamped below half the overall deadline, otherwise
    `no-run` becomes unreachable and every skipped pipeline misreports as `timeout`.
  * State is keyed by run id (one commit can run the same workflow twice — keyed by
    name, the states overwrite each other and the watcher flaps forever); the verdict
    considers only the newest run per workflow, so a concurrency-cancelled older
    sibling does not turn a green commit red.
  * Every subprocess call has its own timeout; transient errors retry, a streak dies
    loudly; even a crash in this script emits `CI-DONE probe-dead` before exiting.
"""

import argparse
import re
import subprocess
import sys
import time

GH_SUCCESS = {"success"}
GH_NEUTRAL = {"skipped", "neutral"}
GH_CANCELLED = {"cancelled", "stale"}
TERMINAL_VERDICTS = {
    "success", "failure", "cancelled", "timeout", "no-run", "superseded", "probe-dead",
}
TERMINAL_EXIT_CODES = {"success": 0, "superseded": 0, "timeout": 124}
# Everything else (failure, timed_out, startup_failure, action_required, unknown) = red.

HEARTBEAT_SECS = 150  # under a typical 5-minute prompt-cache TTL: a quiet run stays warm


def emit(line):
    print(line, flush=True)


def run_capture(cmd, timeout):
    """Run a command with its own timeout. Returns stdout or None on any error —
    one wedged call (or a probe emitting bytes that are not UTF-8) must never
    freeze or kill the loop; it counts as a probe error and retries."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           errors="replace", timeout=timeout)
        if p.returncode != 0:
            return None
        return p.stdout
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return None


def branch_tip(repo, branch, timeout):
    """Resolve the remote branch tip via git, NOT `run list --limit 1`: the newest
    push may not have registered a run yet, and the previous commit's run would
    masquerade as the tip — misreporting the new commit as superseded by its
    own ancestor."""
    out = run_capture(
        ["git", "ls-remote", f"https://github.com/{repo}.git", f"refs/heads/{branch}"],
        timeout,
    )
    if not out or not out.split():
        return None
    return out.split()[0]


def probe_github(repo, sha, timeout):
    """Return {run_id: (workflow_name, status, conclusion, run_id)} for the commit."""
    out = run_capture(
        [
            "gh", "run", "list", "--repo", repo, "--commit", sha, "--limit", "50",
            "--json", "databaseId,workflowName,status,conclusion,createdAt",
            "--jq",
            '.[] | [(.databaseId|tostring), .workflowName, .status, (.conclusion // ""), .createdAt] | @tsv',
        ],
        timeout,
    )
    if out is None:
        return None
    runs = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        run_id, name, status, conclusion, created = parts
        runs[run_id] = {"id": run_id, "name": name, "status": status,
                        "conclusion": conclusion, "created": created}
    return runs


def probe_custom(cmd, timeout):
    """Generic probe: `<name>: <state>` lines + `TERMINAL: <verdict>` when done."""
    out = run_capture(["bash", "-c", cmd], timeout)
    if out is None:
        return None
    runs, terminal = {}, None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("TERMINAL:"):
            fields = line.split(":", 1)[1].strip().split()
            terminal = fields[0].lower() if fields else ""
        elif ":" in line:
            name, state = line.split(":", 1)
            runs[name.strip()] = {"name": name.strip(), "status": state.strip(),
                                  "conclusion": "", "created": ""}
    return {"runs": runs, "terminal": terminal}


def newest_per_workflow(runs):
    """Verdict set = newest run per workflow. Older concurrency-cancelled siblings
    stay visible as CHG events but must not decide the verdict."""
    newest = {}
    for r in runs.values():
        prev = newest.get(r["name"])
        if prev is None or r["created"] > prev["created"]:
            newest[r["name"]] = r
    return newest


def classify(runs):
    """('pending'|'success'|'cancelled'|'failure', detail). Success is an explicit
    allowlist; anything unrecognized is failure — never assume green."""
    verdict_set = newest_per_workflow(runs)
    if any(r["status"] != "completed" for r in verdict_set.values()):
        return "pending", ""
    bad, cancelled = [], []
    for r in verdict_set.values():
        c = r["conclusion"]
        if c in GH_SUCCESS or c in GH_NEUTRAL:
            continue
        (cancelled if c in GH_CANCELLED else bad).append(f"{r['name']}:{c or 'unknown'}")
    if bad:
        return "failure", ", ".join(bad)
    if cancelled:
        return "cancelled", ", ".join(cancelled)
    return "success", ", ".join(sorted(verdict_set))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", help="org/name (GitHub mode)")
    ap.add_argument("--sha", help="full commit SHA to pin (GitHub mode)")
    ap.add_argument("--branch", help="enables supersession detection")
    ap.add_argument("--cmd", help="generic probe command instead of GitHub mode")
    ap.add_argument("--deadline-min", type=float, default=20)
    ap.add_argument("--register-min", type=float, default=4)
    ap.add_argument("--settle-sec", type=float, default=90,
                    help="hold after all-green for workflow_run follow-ups")
    ap.add_argument("--interval", type=float, default=20)
    ap.add_argument("--expect-none", action="store_true",
                    help="treat no-run as success (path-filtered pushes)")
    a = ap.parse_args()

    if not a.cmd and not (a.repo and a.sha):
        emit("CI-DONE probe-dead — need --repo and --sha, or --cmd")
        return 1
    if a.sha and not re.fullmatch(r"[0-9a-fA-F]{40}", a.sha):
        emit("CI-DONE probe-dead — pass the full 40-character hexadecimal SHA "
             "(short or malformed SHAs silently match zero runs)")
        return 1

    deadline = a.deadline_min * 60
    # Grace clamp: an unreachable register deadline turns every no-run into timeout.
    register_by = min(a.register_min * 60, deadline / 2)
    probe_timeout = max(20, a.interval)
    label = f"{a.repo}@{a.sha[:7]}" if a.sha else "custom probe"
    emit(f"CI-WATCH {label} deadline={a.deadline_min:g}m")

    start = time.monotonic()
    last_beat = start
    seen = {}          # run_id -> last emitted state
    registered = False
    err_streak = 0
    green_since = None
    supersede_skip = 0

    while True:
        elapsed = time.monotonic() - start

        if a.cmd:
            result = probe_custom(a.cmd, probe_timeout)
            runs = result["runs"] if result else None
            terminal = result["terminal"] if result else None
        else:
            runs = probe_github(a.repo, a.sha, probe_timeout)
            terminal = None

        if runs is None:
            err_streak += 1
            if err_streak == 3:
                emit("CI-WARN 3 consecutive probe errors — retrying")
            if err_streak >= 10:
                emit("CI-DONE probe-dead — 10 consecutive probe errors")
                return 1
        else:
            err_streak = 0

            was_registered = registered
            if runs and not registered:
                registered = True
                names = " · ".join(
                    f"{r['name']}: {r['conclusion'] or r['status']}"
                    for r in newest_per_workflow(runs).values())
                emit(f"CI-RUN registered {len(runs)}: {names}")

            for run_id, r in runs.items():
                state = r["conclusion"] or r["status"]
                if seen.get(run_id) != state:
                    if run_id in seen or was_registered:
                        emit(f"CI-CHG {r['name']}: {state}")
                    seen[run_id] = state

            if terminal is not None:
                if terminal not in TERMINAL_VERDICTS:
                    emit(f"CI-DONE probe-dead — invalid terminal verdict: "
                         f"{terminal or '<empty>'}")
                    return 1
                if terminal == "success" and not registered and not a.expect_none:
                    emit("CI-DONE probe-dead — probe declared success without any "
                         "registered units (use --expect-none if zero units are valid)")
                    return 1
                emit(f"CI-DONE {terminal} — declared by probe")
                return TERMINAL_EXIT_CODES.get(terminal, 1)

            if registered and not a.cmd:
                verdict, detail = classify(runs)
                if verdict == "failure":
                    failed = next(
                        r for r in newest_per_workflow(runs).values()
                        if r["conclusion"] not in GH_SUCCESS | GH_NEUTRAL | GH_CANCELLED
                    )
                    emit(f"CI-DONE failure — {detail} — logs: gh run view "
                         f"--repo {a.repo} {failed['id']} --log-failed")
                    return 1
                if verdict == "cancelled":
                    # Supersession BEFORE calling this red: a newer tip means the
                    # cancellation was the concurrency group doing its job.
                    if a.branch:
                        tip = branch_tip(a.repo, a.branch, probe_timeout)
                        if tip and tip != a.sha:
                            emit(f"CI-DONE superseded — {a.branch} moved to "
                                 f"{tip[:7]}; arm a new watch")
                            return 0
                    emit(f"CI-DONE cancelled — {detail} (branch unmoved: manual "
                         "cancel or infrastructure, not a test failure)")
                    return 1
                if verdict == "success":
                    if green_since is None:
                        green_since = time.monotonic()
                    if time.monotonic() - green_since >= a.settle_sec:
                        emit(f"CI-DONE success — {detail} @ {a.sha[:7]}")
                        return 0
                else:
                    green_since = None

            if not registered and elapsed > register_by:
                if a.expect_none:
                    emit(f"CI-DONE success — no runs registered and --expect-none "
                         f"set (path-filtered push)")
                    return 0
                emit(f"CI-DONE no-run — nothing registered in "
                     f"{register_by / 60:g}m: check triggers, path filters, and "
                     "that the push landed")
                return 1

        # Pre-registration supersession: every 4th poll to bound API cost.
        if a.branch and not registered and not a.cmd:
            supersede_skip += 1
            if supersede_skip >= 4:
                supersede_skip = 0
                tip = branch_tip(a.repo, a.branch, probe_timeout)
                if tip and tip != a.sha:
                    emit(f"CI-DONE superseded — {a.branch} moved to {tip[:7]}; "
                         "arm a new watch")
                    return 0

        if elapsed > deadline:
            state = ", ".join(f"{r['name']}:{seen.get(i, '?')}"
                              for i, r in (runs or {}).items()) or "nothing registered"
            emit(f"CI-DONE timeout — {a.deadline_min:g}m elapsed; last state: {state}")
            return 124

        if time.monotonic() - last_beat >= HEARTBEAT_SECS:
            last_beat = time.monotonic()
            emit(f"CI-HB {elapsed / 60:.0f}/{a.deadline_min:g}m — "
                 f"{len(runs or {})} run(s) tracked")

        time.sleep(a.interval)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as exc:  # even a bug here must produce a verdict
        emit(f"CI-DONE probe-dead — watcher crashed: {exc!r}")
        sys.exit(1)
