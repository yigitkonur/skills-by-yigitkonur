#!/usr/bin/env python3
"""Watch CI for one exact commit and emit a bounded, diff-gated event stream.

Built for agents and unattended sessions that must learn the result of a push,
re-run, dispatch, or deploy without blocking. One stdout line = one event, so it
fits background monitor tools naturally.

Guarantees:
  - one line per state CHANGE (never re-prints unchanged state)
  - a heartbeat while healthy, so a long queue is never ambiguous
  - exactly one `CI-DONE <verdict>` on every path, then exit
  - a hard deadline, a registration deadline, and a settle window for
    workflow_run-style follow-up workflows that register after the first run turns green

Verdicts: success | failure | cancelled | timeout | no-run | superseded | probe-dead
Exit status: 0 only for `success`.

Modes
-----
GitHub Actions (built in, zero config beyond authenticated `gh`):

    ci-watch.py --sha "$(git rev-parse HEAD)" --branch main

Any other provider: supply a probe command that prints one `<name>: <state>`
line per unit of work, and optionally `TERMINAL: <verdict>` once all are
terminal:

    ci-watch.py --sha "$SHA" --cmd './ci/probe.sh'

The probe receives the watched commit as `$CI_WATCH_SHA` and should exit non-zero
only when the probe itself failed, never because the pipeline failed.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

TERMINAL_OK = {"success", "skipped", "neutral"}
ACTIVE = {"queued", "in_progress", "waiting", "pending", "requested"}


def emit(line: str) -> None:
    print(line, flush=True)


def run(cmd: list[str] | str, timeout: int, env: dict[str, str] | None = None):
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=isinstance(cmd, str),
            env=env,
        )
        return proc.returncode, proc.stdout
    except (subprocess.TimeoutExpired, OSError):
        return 1, ""


def probe_gh(sha: str, timeout: int, expand_jobs: bool = True):
    """Return {name: (state, run_id)} for the exact SHA, or None if unavailable."""
    code, out = run(
        [
            "gh",
            "run",
            "list",
            "--commit",
            sha,
            "--limit",
            "100",
            "--json",
            "databaseId,name,status,conclusion,attempt",
        ],
        timeout,
    )
    if code != 0:
        return None
    try:
        runs = json.loads(out or "[]")
    except json.JSONDecodeError:
        return None

    # Defensive: some providers return one record per attempt. `gh` already
    # collapses, but this keeps the logic safe if the backing command is swapped.
    latest: dict[object, dict] = {}
    for r in runs:
        rid = r.get("databaseId")
        if rid not in latest or (r.get("attempt") or 1) > (latest[rid].get("attempt") or 1):
            latest[rid] = r

    result = {}
    for r in latest.values():
        rid = r.get("databaseId")
        wf = r.get("name") or "?"
        status = r.get("status") or "unknown"
        if expand_jobs and status in ACTIVE:
            jcode, jout = run(["gh", "run", "view", str(rid), "--json", "jobs"], timeout)
            if jcode == 0:
                try:
                    jobs = (json.loads(jout or "{}") or {}).get("jobs") or []
                except json.JSONDecodeError:
                    jobs = []
                if jobs:
                    for j in jobs:
                        jstate = j.get("conclusion") or j.get("status") or "unknown"
                        result[f"{wf}/{j.get('name', '?')}"] = (jstate, rid)
                    continue
        result[f"{wf}#{rid}"] = (r.get("conclusion") or status, rid)
    return result


def probe_cmd(command: str, timeout: int, sha: str):
    env = dict(os.environ, CI_WATCH_SHA=sha)
    code, out = run(command, timeout, env=env)
    if code != 0 and not out.strip():
        return None, None
    states, terminal = {}, None
    for raw in out.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.upper().startswith("TERMINAL:"):
            terminal = (line.split(":", 1)[1].strip() or "success").lower()
            continue
        if ":" in line:
            name, state = line.split(":", 1)
            states[name.strip()] = (state.strip(), None)
    return states, terminal


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sha", required=True, help="exact commit to watch")
    ap.add_argument("--branch", default="", help="retire if this branch moves past --sha")
    ap.add_argument("--cmd", default="", help="custom probe command (non-GitHub providers)")
    ap.add_argument("--deadline", type=int, default=1800, help="hard stop, seconds")
    ap.add_argument("--register-deadline", type=int, default=240, help="give up waiting for a run to appear, seconds")
    ap.add_argument("--settle", type=int, default=90, help="grace period after all-green for late follow-up workflows")
    ap.add_argument("--interval", type=int, default=20, help="poll interval, seconds")
    ap.add_argument("--heartbeat", type=int, default=150, help="heartbeat interval, seconds")
    ap.add_argument("--no-expand-jobs", action="store_true", help="GitHub mode: skip per-job expansion of in-progress runs")
    a = ap.parse_args()

    start = time.monotonic()
    last_hb = start
    seen: dict[str, str] = {}
    registered = False
    green_since = None
    fail_streak = 0
    supersede_warned = False
    probe_timeout = max(20, a.interval)

    def done(verdict: str, detail: str = ""):
        emit(f"CI-DONE {verdict}" + (f" — {detail}" if detail else ""))
        raise SystemExit(0 if verdict == "success" else 1)

    while True:
        now = time.monotonic()
        elapsed = now - start
        if elapsed > a.deadline:
            last = "; ".join(f"{k}:{v}" for k, v in seen.items()) or "none"
            done("timeout", f"{int(elapsed)}s elapsed; last state: {last}")

        explicit_terminal = None
        if a.cmd:
            states, explicit_terminal = probe_cmd(a.cmd, probe_timeout, a.sha)
        else:
            states = probe_gh(a.sha, probe_timeout, expand_jobs=not a.no_expand_jobs)

        if states is None:
            fail_streak += 1
            if fail_streak == 3:
                emit("CI-WARN probe failing (3 consecutive); still trying")
            if fail_streak >= 10:
                done("probe-dead", "10 consecutive probe failures; result unknown")
            time.sleep(a.interval)
            continue
        fail_streak = 0

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
            emit(
                f"CI-RUN registered {len(states)}: "
                + " · ".join(f"{n}: {s}" for n, (s, _) in states.items())
            )
        elif changes:
            emit("CI-CHG " + " · ".join(changes))

        if not registered and elapsed > a.register_deadline:
            done(
                "no-run",
                f"nothing registered for {a.sha[:8]} within {a.register_deadline}s (path filters may exclude this change)",
            )

        if a.branch and registered and not a.cmd:
            code, out = run(["git", "ls-remote", "origin", f"refs/heads/{a.branch}"], 15)
            if code != 0 or not out.split():
                if not supersede_warned:
                    supersede_warned = True
                    emit(f"CI-WARN cannot read origin/{a.branch}; supersede detection is OFF")
            else:
                tip = out.split()[0]
                if not (tip.startswith(a.sha[:12]) or a.sha.startswith(tip[:12])):
                    done("superseded", f"branch {a.branch} moved to {tip[:8]}")

        if registered:
            pending = [n for n, (s, _) in states.items() if s in ACTIVE]
            if not pending:
                bad = [(n, s) for n, (s, _) in states.items() if s not in TERMINAL_OK]
                if bad:
                    n, s = bad[0]
                    hint = states[n][1]
                    tail = f" — logs: gh run view {hint} --log-failed" if hint else ""
                    verdict = "cancelled" if all(x[1] == "cancelled" for x in bad) else "failure"
                    done(verdict, f"{n} -> {s}{tail}")
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

        time.sleep(a.interval)


if __name__ == "__main__":
    main()
