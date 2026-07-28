#!/usr/bin/env python3
"""ci-watch.py — emit one line per CI state change for a pushed commit, then exit.

Provider-neutral watcher for agent harnesses. Built for a background monitor
where each stdout line becomes one notification. The process ALWAYS terminates
with an explicit `CI-DONE <verdict>` line — including on crashes and missing
tooling — so silence past the deadline is structurally impossible.

Why not a foreground `run watch`: under an agent harness it re-renders the whole
job table each interval rather than emitting lines, gates its completion summary
behind an interactive stdout check, and carries no deadline — so a run that never
registers (path filter, disabled workflow) or an API outage hangs the session.

Event vocabulary (one line each, diff-gated — only CHANGES emit):
  CI-RUN   registered <n>: <name>: <state> · ...
  CI-CHG   <name>: <state> -> <state>
  CI-HB    <elapsed>/<deadline>m           liveness; keeps a prompt cache warm
  CI-WARN  <detail>                        non-terminal problem, still retrying
  CI-DONE  success|failure|cancelled|timeout|no-run|probe-dead|superseded — <detail>

Exit code is 0 only for `success` and `superseded`.

GitHub Actions (built in — needs authenticated `gh`, run from inside the repo
when `--repo` is omitted):
  ci-watch.py --sha "$(git rev-parse HEAD)" [--repo owner/name] [--branch main]

Any other provider — supply a probe printing one `<name>: <state>` line per job.
`$SHA` is exported to the probe's environment (not string-substituted):
  ci-watch.py --sha "$(git rev-parse HEAD)" \
      --cmd 'curl -sS "$API/pipelines?sha=$SHA" | jq -r ".[]|\\"\\(.name): \\(.status)\\""'

`--branch` is opt-in: supplying it retires the watch when that branch moves past
the pinned SHA. Omit it on feature branches, or the first poll self-retires.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

# GitHub Actions conclusions. Anything not in SUCCESS is not green — listing the
# bad states explicitly (rather than treating "not failure" as success) is what
# keeps a cancelled or skipped run from being reported as a false green.
GH_SUCCESS = {"success"}
GH_FAILURE = {"failure", "timed_out", "startup_failure", "action_required"}
GH_CANCELLED = {"cancelled", "skipped", "stale", "neutral"}

# Custom-probe state vocabulary. Exact matches on a normalised token, not
# substrings: substring matching reports "not_failed" as a failure and never
# terminates on "skipped".
CUSTOM_SUCCESS = {"success", "succeeded", "passed", "pass", "ok", "green", "fixed"}
CUSTOM_FAILURE = {"failed", "failure", "failing_final", "error", "errored", "broken", "red"}
CUSTOM_CANCELLED = {"cancelled", "canceled", "skipped", "manual", "blocked",
                    "not_run", "neutral", "stale", "timed_out", "timeout"}


def emit(line: str) -> None:
    """One event per line, flushed immediately: the monitor reads stdout live."""
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def run_capture(args: list[str] | str, timeout: int, shell: bool = False,
                env: dict[str, str] | None = None) -> subprocess.CompletedProcess | None:
    """Every probe call is individually bounded; a missing binary is not fatal here."""
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                              check=False, shell=shell, env=env)
    except (subprocess.TimeoutExpired, OSError):
        return None


def gh_json(args: list[str], timeout: int) -> object | None:
    out = run_capture(args, timeout)
    if out is None or out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout or "null")
    except json.JSONDecodeError:
        return None


def head_sha(repo: str | None, branch: str, timeout: int = 30) -> str | None:
    # NOT an f-string: gh expands the literal {owner}/{repo} placeholder from the
    # git remote of the current directory. Do not "fix" the braces.
    prefix = f"repos/{repo}" if repo else "repos/{owner}/{repo}"
    out = run_capture(["gh", "api", f"{prefix}/commits/{branch}", "--jq", ".sha"], timeout)
    if out is None or out.returncode != 0:
        return None
    return out.stdout.strip() or None


def classify_gh(conclusion: str | None, status: str) -> tuple[bool, str]:
    """(terminal, bucket) where bucket is success|failure|cancelled|running."""
    if status != "completed":
        return False, "running"
    if conclusion in GH_SUCCESS:
        return True, "success"
    if conclusion in GH_CANCELLED:
        return True, "cancelled"
    # Unknown conclusions are treated as failure: never assume green.
    return True, "failure"


def classify_custom(state: str) -> tuple[bool, str]:
    token = state.strip().lower().replace("-", "_").replace(" ", "_")
    if token in CUSTOM_SUCCESS:
        return True, "success"
    if token in CUSTOM_FAILURE:
        return True, "failure"
    if token in CUSTOM_CANCELLED:
        return True, "cancelled"
    return False, "running"


def poll_gh(repo: str | None, sha: str, timeout: int) -> list[dict] | None:
    """All runs for the pinned SHA — never 'latest', which can be another commit."""
    args = ["gh", "run", "list", "--commit", sha, "--limit", "100",
            "--json", "databaseId,workflowName,status,conclusion"]
    if repo:
        args += ["--repo", repo]
    data = gh_json(args, timeout)
    if not isinstance(data, list):
        return None
    rows = []
    for r in data:
        terminal, bucket = classify_gh(r.get("conclusion"), r.get("status", ""))
        rows.append({"key": str(r["databaseId"]), "name": r["workflowName"],
                     "state": r.get("conclusion") or r.get("status", ""),
                     "terminal": terminal, "bucket": bucket})
    return rows


def poll_custom(cmd: str, sha: str, timeout: int) -> list[dict] | None:
    """Probe contract: print one `<name>: <state>` line per job, nothing else."""
    env = {**os.environ, "SHA": sha}
    out = run_capture(cmd, timeout, shell=True, env=env)
    if out is None or out.returncode != 0:
        return None
    rows: list[dict] = []
    for line in out.stdout.splitlines():
        if ":" not in line:
            continue
        # rpartition: job names legitimately contain ':' (GitLab `test:unit`).
        name, _, state = line.rpartition(":")
        name, state = name.strip(), state.strip()
        if not name or not state:
            continue
        terminal, bucket = classify_custom(state)
        rows.append({"key": name, "name": name, "state": state.lower(),
                     "terminal": terminal, "bucket": bucket})
    return rows


def watch(a: argparse.Namespace) -> int:
    started = time.monotonic()
    deadline = started + a.deadline_min * 60
    register_by = started + a.register_min * 60
    next_beat = started + a.heartbeat_min * 60

    seen: dict[str, str] = {}
    registered = False
    err_streak = 0
    warned_at = 0
    last_keys: frozenset[str] | None = None
    polls_since_check = 0

    while True:
        runs = (poll_custom(a.cmd, a.sha, 45) if a.cmd
                else poll_gh(a.repo, a.sha, 45))

        if runs is None:
            err_streak += 1
            if err_streak >= 3 and err_streak != warned_at and err_streak % 3 == 0:
                emit(f"CI-WARN probe failing ({err_streak}x) — still retrying")
                warned_at = err_streak
            if err_streak >= 10:
                emit("CI-DONE probe-dead — 10 consecutive probe failures")
                return 1
        else:
            err_streak = 0
            if runs and not registered:
                registered = True
                emit(f"CI-RUN  registered {len(runs)}: "
                     + " · ".join(f"{r['name']}: {r['state']}" for r in runs))

            for r in runs:
                if seen.get(r["key"]) != r["state"]:
                    if r["key"] in seen:
                        emit(f"CI-CHG  {r['name']}: {seen[r['key']]} -> {r['state']}")
                    seen[r["key"]] = r["state"]

            keys = frozenset(r["key"] for r in runs)
            stable = last_keys == keys
            last_keys = keys

            # Do not call success while workflows may still be registering: a fast
            # job can finish before a slower sibling is even created.
            settled = stable or time.monotonic() > register_by
            if registered and runs and settled and all(r["terminal"] for r in runs):
                failed = [r for r in runs if r["bucket"] == "failure"]
                stopped = [r for r in runs if r["bucket"] == "cancelled"]
                if failed:
                    hint = ""
                    if not a.cmd:
                        flag = f" --repo {a.repo}" if a.repo else ""
                        hint = " — " + "; ".join(
                            f"gh run view {r['key']}{flag} --log-failed" for r in failed[:3])
                    emit(f"CI-DONE failure — {', '.join(r['name'] for r in failed)}{hint}")
                    return 1
                if stopped:
                    emit("CI-DONE cancelled — "
                         + ", ".join(f"{r['name']} ({r['state']})" for r in stopped)
                         + " — not a green result")
                    return 1
                emit(f"CI-DONE success — {len(runs)} workflow(s) green on {a.sha[:9]}")
                return 0

            # Opt-in supersession; polled sparsely to avoid doubling API calls.
            polls_since_check += 1
            if registered and a.branch and not a.cmd and polls_since_check >= 4:
                polls_since_check = 0
                tip = head_sha(a.repo, a.branch)
                if tip and tip != a.sha:
                    emit(f"CI-DONE superseded — {a.branch} moved to {tip[:9]}")
                    return 0

        now = time.monotonic()   # re-sampled: the probe above can take ~45s
        if not registered and now > register_by:
            emit(f"CI-DONE no-run — nothing registered for {a.sha[:9]} in "
                 f"{a.register_min:g}m (path filter? workflow disabled? wrong branch?)")
            return 1
        if now > deadline:
            pending = sum(1 for k in seen if k not in
                          {r["key"] for r in (runs or []) if r["terminal"]})
            emit(f"CI-DONE timeout — {a.deadline_min:g}m elapsed, {pending} still running")
            return 1
        if now >= next_beat:
            emit(f"CI-HB   {int((now - started) / 60)}/{a.deadline_min:g}m")
            next_beat = now + a.heartbeat_min * 60

        time.sleep(a.interval)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sha", required=True, help="full commit SHA that was pushed")
    p.add_argument("--repo", help="owner/name (GitHub mode; inferred from cwd if omitted)")
    p.add_argument("--branch", default="",
                   help="opt-in: retire the watch when this branch moves past --sha")
    p.add_argument("--cmd", help="probe printing '<name>: <state>' lines; $SHA is in its env")
    p.add_argument("--deadline-min", type=float, default=30.0)
    p.add_argument("--interval", type=float, default=15.0)
    p.add_argument("--heartbeat-min", type=float, default=2.5)
    p.add_argument("--register-min", type=float, default=4.0)
    a = p.parse_args()
    try:
        return watch(a)
    except KeyboardInterrupt:
        emit("CI-DONE timeout — interrupted")
        return 1
    except BaseException as exc:  # noqa: BLE001 — a crash must still emit a verdict
        emit(f"CI-DONE probe-dead — {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
