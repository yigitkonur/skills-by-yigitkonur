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
  CI-RUN    registered <n>: <name>: <state> · ...
  CI-CHG    <name>: <state> -> <state>          run-level, and job-level for
                                                in-flight runs (react to the
                                                first red job, not the verdict)
  CI-HB     <elapsed>/<deadline>m               liveness tick
  CI-SETTLE all green — holding <n>s for completion-triggered follow-ups
  CI-WARN   <detail>                            non-terminal problem, still retrying
  CI-DONE   success|failure|cancelled|timeout|no-run|probe-dead|superseded — <detail>

Exit code encodes the verdict so `ci-watch.py … && deploy` is safe:
  0 success (and no-run under --expect-none)
  1 failure, cancelled
  2 timeout, no-run, probe-dead      — indeterminate: you still do not know
  3 superseded                       — the pinned SHA never reached a verdict
Collapsing these to 0 (a tempting shortcut) makes `watch && deploy` ship a red
build; treating 2 as red hides that the answer is "unknown", not "no".

GitHub Actions (built in — needs authenticated `gh`; pass --repo when the
session cwd is not the target repo, e.g. another worktree):
  ci-watch.py --sha "$(git rev-parse HEAD)" [--repo owner/name] [--branch main]

Any other provider — supply a probe printing one `<name>: <state>` line per job.
`$SHA` is exported to the probe's environment (never string-substituted into the
command, which would be a quoting/injection hazard):
  ci-watch.py --sha "$(git rev-parse HEAD)" \
      --cmd 'curl -sS "$API/pipelines?sha=$SHA" | jq -r ".[]|\\"\\(.name): \\(.status)\\""'

Flags for specific pipeline shapes:
  --settle-sec N   hold an all-green result N seconds and re-probe before
                   declaring success. Use when one workflow triggers another on
                   completion (deploy after build): the follow-up does not exist
                   yet at the moment the first turns green.
  --expect-none    a path-filtered push may legitimately trigger nothing; make
                   "zero runs registered" an asserted expectation (exit 0)
                   instead of an ambiguous no-run (exit 2).
  --no-jobs        skip per-run job expansion in GitHub mode (halves API calls
                   on busy commits; you lose early job-level failure events).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

EXIT = {"success": 0, "failure": 1, "cancelled": 1,
        "timeout": 2, "no-run": 2, "probe-dead": 2, "superseded": 3}

# GitHub Actions conclusions. Anything not in SUCCESS is not green — enumerating
# success (rather than treating "not failure" as green) is what keeps a
# cancelled or skipped run from being reported as a false green.
GH_SUCCESS = {"success"}
GH_CANCELLED = {"cancelled", "skipped", "stale", "neutral"}

# Custom-probe state vocabulary. Exact matches on a normalised token, not
# substrings: substring matching reports "not_failed" as a failure and never
# terminates on "skipped".
CUSTOM_SUCCESS = {"success", "succeeded", "passed", "pass", "ok", "green", "fixed"}
CUSTOM_FAILURE = {"failed", "failure", "error", "errored", "broken", "red"}
CUSTOM_CANCELLED = {"cancelled", "canceled", "skipped", "manual", "blocked",
                    "not_run", "neutral", "stale", "timed_out", "timeout"}


def emit(line: str) -> None:
    """One event per line, flushed immediately: the monitor reads stdout live."""
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def done(verdict: str, detail: str) -> int:
    emit(f"CI-DONE {verdict} — {detail}")
    return EXIT[verdict]


def run_capture(args: list[str] | str, timeout: int, shell: bool = False,
                env: dict[str, str] | None = None) -> subprocess.CompletedProcess | None:
    """Every probe call is individually bounded; a wedged request must not
    freeze the loop, and a missing binary is handled by the caller."""
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                              check=False, shell=shell, env=env,
                              stdin=subprocess.DEVNULL)
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
    """Branch tip from the API — NOT `run list --branch --limit 1`, whose newest
    RUN can lag the newest COMMIT and report a push superseded by its own
    ancestor."""
    # NOT an f-string: gh expands the literal {owner}/{repo} placeholder from
    # the git remote of the current directory. Do not "fix" the braces.
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
    """All runs for the pinned SHA — never 'latest', which can be another commit.

    `gh run list` returns one row per run id already reflecting the latest
    attempt (verified against gh 2.x); providers whose listing returns one row
    per ATTEMPT need the highest attempt kept per id or the watcher oscillates.
    """
    args = ["gh", "run", "list", "--commit", sha, "--limit", "100",
            "--json", "databaseId,workflowName,event,status,conclusion"]
    if repo:
        args += ["--repo", repo]
    data = gh_json(args, timeout)
    if not isinstance(data, list):
        return None
    rows = []
    for r in data:
        terminal, bucket = classify_gh(r.get("conclusion"), r.get("status", ""))
        rows.append({"key": str(r["databaseId"]), "name": r["workflowName"],
                     "group": (r["workflowName"], r.get("event", "")),
                     "state": r.get("conclusion") or r.get("status", ""),
                     "terminal": terminal, "bucket": bucket})
    return rows


def poll_gh_jobs(repo: str | None, run_key: str, timeout: int) -> list[dict]:
    """Jobs of one in-flight run. A run's status stays in_progress until every
    job finishes, so run-level polling cannot surface the first red job — this
    expansion is what makes 'react to the first failure' possible. Bounded to
    active runs so the extra API call does not multiply on finished work."""
    args = ["gh", "run", "view", run_key, "--json", "jobs"]
    if repo:
        args += ["--repo", repo]
    data = gh_json(args, timeout)
    if not isinstance(data, dict):
        return []
    rows = []
    for j in data.get("jobs", []):
        state = j.get("conclusion") or j.get("status") or ""
        rows.append({"key": f"{run_key}/{j.get('name', '?')}",
                     "name": j.get("name", "?"), "state": state})
    return rows


def newest_per_workflow(runs: list[dict]) -> list[dict]:
    """One commit can carry several runs of the same workflow (a rerun, or a
    concurrency-cancelled attempt beside its replacement). The newest run per
    (workflow, trigger event) decides the verdict; otherwise a cancelled
    sibling turns a green commit red. Grouping includes the EVENT because a
    workflow_dispatch rerun is a different validation surface than the push
    run it sits beside — a dispatch that skips a deploy job must not forgive
    the push run whose deploy job failed. GitHub run ids are monotonic, so
    max(id) is the newest within a group."""
    by_group: dict[tuple, dict] = {}
    for r in runs:
        group = r.get("group", (r["name"],))
        prev = by_group.get(group)
        if prev is None or _key_order(r["key"]) > _key_order(prev["key"]):
            by_group[group] = r
    return list(by_group.values())


def _key_order(key: str):
    return (0, int(key)) if key.isdigit() else (1, key)


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
    green_since: float | None = None
    settle_announced = False
    polls_since_branch_check = 0

    while True:
        runs = (poll_custom(a.cmd, a.sha, 45) if a.cmd
                else poll_gh(a.repo, a.sha, 45))

        if runs is None:
            err_streak += 1
            if err_streak >= 3 and err_streak != warned_at and err_streak % 3 == 0:
                emit(f"CI-WARN probe failing ({err_streak}x) — still retrying")
                warned_at = err_streak
            if err_streak >= 10:
                return done("probe-dead", "10 consecutive probe failures")
        elif not runs and registered:
            # A transient empty result after registration is a blip, never a
            # verdict: `all([])` is True, and treating it as "all terminal and
            # nothing failed" manufactures a success out of an outage.
            green_since = None
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

            # Job-level expansion for in-flight runs only (GitHub mode): the
            # first red job surfaces minutes before the run's own conclusion.
            if not a.cmd and not a.no_jobs:
                for r in runs:
                    if not r["terminal"]:
                        for j in poll_gh_jobs(a.repo, r["key"], 30):
                            jk = j["key"]
                            if seen.get(jk) != j["state"] and j["state"]:
                                if jk in seen:
                                    emit(f"CI-CHG  {r['name']}/{j['name']}: "
                                         f"{seen[jk]} -> {j['state']}")
                                seen[jk] = j["state"]

            keys = frozenset(r["key"] for r in runs)
            stable = last_keys == keys
            last_keys = keys

            # The verdict comes from the newest run per workflow, and only once
            # the run SET has been stable across two polls (or registration has
            # closed): a fast workflow can finish before a slower sibling is
            # even created, and success-on-first-green would miss the sibling.
            decisive = newest_per_workflow(runs) if not a.cmd else runs
            settled = stable or time.monotonic() > register_by
            if registered and decisive and settled and all(r["terminal"] for r in decisive):
                failed = [r for r in decisive if r["bucket"] == "failure"]
                stopped = [r for r in decisive if r["bucket"] == "cancelled"]
                if failed:
                    # Failure outranks supersession: a completed red answers
                    # "did this SHA pass" regardless of where the branch went.
                    hint = ""
                    if not a.cmd:
                        flag = f" --repo {a.repo}" if a.repo else ""
                        hint = " — " + "; ".join(
                            f"gh run view {r['key']}{flag} --log-failed" for r in failed[:3])
                    return done("failure", ", ".join(r["name"] for r in failed) + hint)
                if stopped:
                    # Cancelled is ambiguous: under cancel-in-progress
                    # concurrency, a newer push cancels this SHA's runs. Check
                    # the branch tip to tell auto-supersession from a manual or
                    # infrastructure cancel.
                    names = ", ".join(f"{r['name']} ({r['state']})" for r in stopped)
                    if a.branch and not a.cmd:
                        tip = head_sha(a.repo, a.branch)
                        if tip and tip != a.sha:
                            return done("superseded",
                                        f"runs cancelled and {a.branch} moved to "
                                        f"{tip[:9]} — no verdict for {a.sha[:9]}")
                        return done("cancelled", names + " on an unmoved branch "
                                    "— not green, not superseded")
                    return done("cancelled", names + " — not a green result "
                                "(pass --branch to distinguish supersession)")
                if a.settle_sec > 0:
                    now = time.monotonic()
                    if green_since is None:
                        green_since = now
                        if not settle_announced:
                            emit(f"CI-SETTLE all green — holding {a.settle_sec:g}s "
                                 "for completion-triggered follow-ups")
                            settle_announced = True
                    if now - green_since < a.settle_sec:
                        time.sleep(a.interval)
                        continue
                return done("success",
                            f"{len(decisive)} workflow(s) green on {a.sha[:9]}")
            green_since = None

            # Mid-flight supersession (opt-in, sparse — the branch probe would
            # otherwise double API traffic). A moved branch retires a watch that
            # has no verdict yet; a finished verdict above always wins.
            polls_since_branch_check += 1
            if registered and a.branch and not a.cmd and polls_since_branch_check >= 4:
                polls_since_branch_check = 0
                tip = head_sha(a.repo, a.branch)
                if tip and tip != a.sha:
                    return done("superseded", f"{a.branch} moved to {tip[:9]}")

        now = time.monotonic()   # re-sampled: the probes above can take ~45s
        if not registered and now > register_by:
            if a.expect_none:
                emit(f"CI-DONE no-run — nothing registered for {a.sha[:9]} — "
                     "expected (declared path-filtered)")
                return 0
            return done("no-run",
                        f"nothing registered for {a.sha[:9]} in {a.register_min:g}m "
                        "(path filter? workflow disabled? wrong branch? short SHA?)")
        if now > deadline:
            pending = sum(1 for k, v in seen.items()
                          if "/" not in k and not classify_custom(v)[0]
                          and v not in ("completed",))
            return done("timeout",
                        f"{a.deadline_min:g}m elapsed, ~{pending} still running")
        if now >= next_beat:
            emit(f"CI-HB   {int((now - started) / 60)}/{a.deadline_min:g}m")
            next_beat = now + a.heartbeat_min * 60

        time.sleep(a.interval)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sha", required=True, help="full 40-char commit SHA that was pushed")
    p.add_argument("--repo", help="owner/name (GitHub mode; inferred from cwd if omitted "
                                  "— pass it explicitly when running from another worktree)")
    p.add_argument("--branch", default="",
                   help="opt-in: retire the watch when this branch moves past --sha")
    p.add_argument("--cmd", help="probe printing '<name>: <state>' lines; $SHA is in its env")
    p.add_argument("--deadline-min", type=float, default=30.0)
    p.add_argument("--interval", type=float, default=15.0)
    p.add_argument("--heartbeat-min", type=float, default=2.5)
    p.add_argument("--register-min", type=float, default=4.0)
    p.add_argument("--settle-sec", type=float, default=0.0,
                   help="hold all-green N seconds for completion-triggered follow-ups")
    p.add_argument("--expect-none", action="store_true",
                   help="zero registered runs is the expected outcome (exit 0)")
    p.add_argument("--no-jobs", action="store_true",
                   help="skip job-level expansion of in-flight GitHub runs")
    a = p.parse_args()

    # `gh run list --commit` silently returns ZERO rows for a short SHA, which
    # the registration deadline would then misreport as no-run. Fail fast.
    if not a.cmd and not re.fullmatch(r"[0-9a-f]{40}", a.sha):
        p.error("--sha must be the full 40-character lowercase SHA in GitHub mode "
                "(use \"$(git rev-parse HEAD)\")")
    # If the registration cutoff meets or exceeds the deadline, no-run becomes
    # unreachable and every skipped pipeline misreports as timeout.
    if a.register_min * 2 > a.deadline_min:
        a.register_min = a.deadline_min / 2
        emit(f"CI-WARN register window clamped to {a.register_min:g}m "
             f"(half of the {a.deadline_min:g}m deadline)")

    try:
        return watch(a)
    except KeyboardInterrupt:
        return done("timeout", "interrupted")
    except BaseException as exc:  # noqa: BLE001 — a crash must still emit a verdict
        return done("probe-dead", f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    sys.exit(main())
