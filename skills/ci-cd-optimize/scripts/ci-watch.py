#!/usr/bin/env python3
"""Watch CI for one exact commit and emit a bounded, diff-gated event stream.

Built for autonomous agents that push and must learn the result without
stalling. Satisfies the contract in references/feedback-loops.md:

  - one line per state CHANGE (never re-prints unchanged state)
  - a heartbeat while healthy, so a long queue is never ambiguous
  - exactly one `CI-DONE <verdict>` on every path, then exit
  - a hard deadline, a registration deadline, and a settle window for
    workflow_run-style follow-ups that register after the first run goes green

Verdicts: success | failure | cancelled | timeout | no-run | superseded | probe-dead
Exit status: 0 only for `success`. stdlib only; no third-party imports.

Modes
-----
GitHub Actions (default) — requires an authenticated `gh`:

    ci-watch.py --sha "$(git rev-parse HEAD)" --branch main

In-progress runs are expanded to job level so a lane that fails early is
reported immediately, rather than waiting for the whole run to conclude.

Any other provider — supply a probe command that prints one `name: state`
line per unit of work, and `TERMINAL: <verdict>` once all are terminal:

    ci-watch.py --sha "$SHA" --cmd './ci/probe.sh'

The probe receives the watched commit as `$CI_WATCH_SHA` and should exit
non-zero only when the probe itself failed, never because the pipeline failed.
"""
import argparse
import json
import os
import subprocess
import sys
import time

# GitHub states used only in GitHub mode.
TERMINAL_OK = {"success", "skipped", "neutral"}
ACTIVE = {"queued", "in_progress", "waiting", "pending", "requested"}
VERDICTS = {"success", "failure", "cancelled", "timeout", "no-run",
            "superseded", "probe-dead"}


def positive_int(value):
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def nonnegative_int(value):
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def emit(line):
    print(line, flush=True)


def run(cmd, timeout, env=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, check=False,
                           shell=isinstance(cmd, str),
                           env=env)
        return p.returncode, p.stdout
    except (subprocess.TimeoutExpired, OSError):
        return 1, ""


def remaining_timeout(deadline_at, cap):
    return max(0.01, min(cap, deadline_at - time.monotonic()))


def probe_gh(sha, deadline_at, probe_cap, expand_jobs=True):
    """Return {name: (state, run_id)} for the exact SHA, or None if unavailable."""
    code, out = run(
        ["gh", "api", "--paginate", "--slurp", "-X", "GET",
         "repos/{owner}/{repo}/actions/runs", "-f", f"head_sha={sha}",
         "-f", "per_page=100"], remaining_timeout(deadline_at, probe_cap))
    if code != 0:
        return None
    try:
        pages = json.loads(out or "[]")
        runs = [item for page in pages
                for item in (page.get("workflow_runs") or [])]
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None
    # Defensive: some providers return one record per attempt under a shared
    # id. GitHub's API already returns the latest attempt for each run id.
    latest = {}
    for r in runs:
        rid = r.get("id")
        if rid not in latest or (r.get("run_attempt") or 1) > (latest[rid].get("run_attempt") or 1):
            latest[rid] = r

    result = {}
    for r in latest.values():
        rid = r.get("id")
        wf = r.get("name") or "?"
        status = r.get("status") or "unknown"
        # A run-level status stays `in_progress` until every job finishes, so
        # run granularity alone cannot surface an early per-job failure. Expand
        # only in-flight runs: completed ones already carry a conclusion.
        if expand_jobs and status in ACTIVE:
            if time.monotonic() >= deadline_at:
                return None
            jcode, jout = run(["gh", "run", "view", str(rid), "--json", "jobs"],
                              remaining_timeout(deadline_at, probe_cap))
            if jcode == 0:
                try:
                    jobs = (json.loads(jout or "{}") or {}).get("jobs") or []
                except json.JSONDecodeError:
                    jobs = []
                if jobs:
                    for j in jobs:
                        jstate = j.get("conclusion") or j.get("status") or "unknown"
                        result[f"{wf}#{rid}/{j.get('name', '?')}"] = (jstate, rid)
                    continue
        result[f"{wf}#{rid}"] = (r.get("conclusion") or status, rid)
    return result


def probe_cmd(command, timeout, sha):
    """Parse `name: state` lines plus an optional `TERMINAL: <verdict>`."""
    env = dict(os.environ, CI_WATCH_SHA=sha)
    code, out = run(command, timeout, env=env)
    if code != 0:
        return None, None
    states, terminal = {}, None
    for raw in out.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.upper().startswith("TERMINAL:"):
            verdict = line.split(":", 1)[1].strip().lower()
            if verdict not in VERDICTS:
                return None, None
            terminal = verdict
            continue
        if ":" in line:
            name, state = line.split(":", 1)
            states[name.strip()] = (state.strip(), None)
    return states, terminal


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sha", required=True, help="exact commit to watch")
    ap.add_argument("--branch", default="", help="retire if this branch moves past --sha")
    ap.add_argument("--cmd", default="", help="custom probe command (non-GitHub providers)")
    ap.add_argument("--deadline", type=positive_int, default=1800, help="hard stop, seconds")
    ap.add_argument("--register-deadline", type=positive_int, default=240,
                    help="give up waiting for a run to appear, seconds")
    ap.add_argument("--settle", type=nonnegative_int, default=90,
                    help="grace period after all-green for late follow-up workflows")
    ap.add_argument("--interval", type=positive_int, default=20, help="poll interval, seconds")
    ap.add_argument("--heartbeat", type=positive_int, default=150, help="heartbeat interval, seconds")
    ap.add_argument("--no-expand-jobs", action="store_true",
                    help="GitHub mode: skip per-job expansion of in-progress runs")
    a = ap.parse_args()

    start = time.monotonic()
    deadline_at = start + a.deadline
    last_hb = start
    seen = {}
    registered = False
    green_since = None
    fail_streak = 0
    supersede_warned = False
    probe_timeout = max(20, a.interval)

    def done(verdict, detail=""):
        emit(f"CI-DONE {verdict}" + (f" — {detail}" if detail else ""))
        sys.exit(0 if verdict == "success" else 1)

    while True:
        now = time.monotonic()
        elapsed = now - start
        if now >= deadline_at:
            last = "; ".join(f"{k}:{v}" for k, v in seen.items()) or "none"
            done("timeout", f"{int(elapsed)}s elapsed; last state: {last}")

        explicit_terminal = None
        if a.cmd:
            states, explicit_terminal = probe_cmd(
                a.cmd, remaining_timeout(deadline_at, probe_timeout), a.sha)
        else:
            states = probe_gh(a.sha, deadline_at, probe_timeout,
                              expand_jobs=not a.no_expand_jobs)

        if registered and states == {} and not explicit_terminal:
            states = None

        if states is None:
            fail_streak += 1
            if fail_streak == 3:
                emit("CI-WARN probe failing (3 consecutive); still trying")
            if fail_streak >= 10:
                done("probe-dead", "10 consecutive probe failures; result unknown")
            remaining = deadline_at - time.monotonic()
            if remaining <= 0:
                continue
            time.sleep(min(a.interval, remaining))
            continue
        fail_streak = 0
        now = time.monotonic()
        elapsed = now - start
        if now >= deadline_at:
            continue

        # A probe may report a terminal verdict with no per-unit lines at all
        # (e.g. a deploy API that only answers "done"). Honour it regardless of
        # whether anything ever "registered".
        if explicit_terminal:
            done(explicit_terminal)

        changes = []
        for name, (state, _hint) in states.items():
            if name not in seen:
                if registered:
                    changes.append(f"{name}: {state}")
            elif seen[name] != state:
                changes.append(f"{name}: {seen[name]} -> {state}")
            seen[name] = state

        if states and not registered:
            registered = True
            emit(f"CI-RUN registered {len(states)}: " +
                 " · ".join(f"{n}: {s}" for n, (s, _) in states.items()))
        elif changes:
            emit("CI-CHG " + " · ".join(changes))

        # Supersession must be evaluated before the registration deadline and
        # before calling a cancelled run a failure. A newer branch tip means the
        # caller should retire this watcher and arm one for the new SHA.
        if a.branch and not a.cmd:
            code, out = run(
                ["git", "ls-remote", "origin", f"refs/heads/{a.branch}"],
                remaining_timeout(deadline_at, 15))
            if time.monotonic() >= deadline_at:
                continue
            if code != 0 or not out.split():
                if not supersede_warned:
                    supersede_warned = True
                    emit(f"CI-WARN cannot read origin/{a.branch}; supersede detection is OFF")
            else:
                tip = out.split()[0]
                if not (tip.startswith(a.sha[:12]) or a.sha.startswith(tip[:12])):
                    done("superseded", f"branch {a.branch} moved to {tip[:8]}")

        if not registered and elapsed > a.register_deadline:
            done("no-run", f"nothing registered for {a.sha[:8]} within "
                           f"{a.register_deadline}s (path filters may exclude this "
                           "change, which is not a failure)")

        # Custom probes own their state vocabulary and completion decision.
        # Their per-unit states are display-only; only a validated TERMINAL line
        # can produce a terminal verdict.
        if registered and not a.cmd:
            pending = [n for n, (s, _) in states.items() if s in ACTIVE]
            if not pending:
                bad = [(n, s) for n, (s, _) in states.items() if s not in TERMINAL_OK]
                if bad:
                    n, s = bad[0]
                    hint = states[n][1]
                    tail = f" — logs: gh run view {hint} --log-failed" if hint else ""
                    verdict = "cancelled" if all(x[1] == "cancelled" for x in bad) else "failure"
                    done(verdict, f"{n} -> {s}{tail}")
                # All green. A follow-up workflow triggered by this run may not
                # have registered yet; hold the settle window before declaring.
                if green_since is None:
                    green_since = now
                    if a.settle > 0:
                        emit(f"CI-SETTLE all green; waiting {a.settle}s for follow-up workflows")
                elif now - green_since >= a.settle:
                    done("success", " · ".join(sorted(seen)))
            else:
                green_since = None

        if now - last_hb >= a.heartbeat:
            last_hb = now
            emit(f"CI-HB {int(elapsed)}s/{a.deadline}s — {len(seen)} run(s) tracked")

        remaining = deadline_at - time.monotonic()
        if remaining > 0:
            time.sleep(min(a.interval, remaining))


if __name__ == "__main__":
    main()
