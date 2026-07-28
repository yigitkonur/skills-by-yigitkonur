#!/usr/bin/env python3
"""ci-watch.py -- watch CI for one exact commit; always end with a verdict.

Usage:
    scripts/ci-watch.py [SHA] [options]                # GitHub mode (needs gh)
    scripts/ci-watch.py [SHA] --cmd '<probe>' [options]  # any provider

Every exit path prints exactly one terminal line:

    CI-DONE <verdict> [-- detail]

Verdicts and exit codes:
    success     0    every registered run reached an explicit success
    failure     1    a run (or lane) failed -- the line carries the log command
    no-run      2    nothing registered within the registration window
                     (exit 0 with --expect-none: path filters make this normal)
    probe-dead  2    the probe itself failed repeatedly -- check auth/network
    superseded  3    only cancelled/neutral results and the branch tip moved on
    cancelled   3    cancelled on an unmoved branch -- manual or infra, not a
                     test failure; not a pass either
    timeout     124  still not terminal at the deadline -- stuck, not slow

Interpret 'no-run', 'probe-dead', and 'timeout' as *you still do not know* --
never record any of them as a pass. 'success' is decided by enumerating explicit
success conclusions; unknown conclusions count as failure, never as green.

Custom probe contract (--cmd): the command runs with $CI_WATCH_SHA set and must
print one "name: state" line per unit of work. Printing "TERMINAL: <verdict>"
ends the watch immediately with that verdict. A non-zero probe exit counts as a
probe error (streak of 10 -> probe-dead), not as a pipeline failure.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time

# Explicit success set: a verdict is green only when matched here. "Did not
# fail" is not green -- cancel-in-progress concurrency manufactures cancelled
# runs on every superseded push, and unknown states must never pass silently.
GH_SUCCESS = {"success"}
GH_FAILURE = {"failure", "timed_out", "startup_failure", "action_required"}
GH_NEUTRAL = {"cancelled", "skipped", "stale", "neutral"}
ACTIVE = {"queued", "in_progress", "waiting", "pending", "requested"}

CUSTOM_SUCCESS = {"success", "succeeded", "passed", "pass", "ok", "green", "live", "fixed"}
CUSTOM_FAILURE = {"failed", "failure", "error", "errored", "broken", "red"}
CUSTOM_NEUTRAL = {"cancelled", "canceled", "skipped", "manual", "blocked",
                  "not_run", "neutral", "stale"}

PROBE_TIMEOUT = 45      # one wedged request must not freeze the loop
MAX_RUNS = 1000        # fail closed rather than green an incomplete enumeration
WARN_STREAK = 3
DEAD_STREAK = 10

EXIT = {"success": 0, "failure": 1, "no-run": 2, "probe-dead": 2,
        "superseded": 3, "cancelled": 3, "timeout": 124}


def emit(line: str) -> None:
    print(line, flush=True)


def run(cmd: list[str], timeout: int = PROBE_TIMEOUT) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          check=True).stdout


def full_sha(candidate: str) -> str:
    # gh's --commit filter silently returns ZERO rows for a short SHA, which a
    # registration window would then misreport as no-run. Normalize first.
    if len(candidate) == 40:
        return candidate
    return run(["git", "rev-parse", candidate]).strip()


def branch_tip(repo_dir: str, branch: str) -> str | None:
    # The remote ref is the only correct source for supersession. The latest
    # *run*'s head SHA is wrong: before the newest push registers, it is an
    # older commit, and a watcher using it reports a commit superseded by its
    # own ancestor.
    try:
        out = run(["git", "-C", repo_dir, "ls-remote", "origin",
                   f"refs/heads/{branch}"])
        return out.split()[0] if out.strip() else None
    except Exception:
        return None


def gh_probe(sha: str, repo: str | None, expand_jobs: bool,
             deadline_at: float) -> dict[str, dict]:
    """Return {key: {name, state, conclusion, log_cmd}} keyed by run/lane id.

    Keyed by id, never by workflow name: two runs of one workflow (re-run,
    workflow_dispatch) would otherwise overwrite each other and the diff-gate
    would flap forever.
    """
    base = ["gh", "run", "list", "--commit", sha, "--limit", str(MAX_RUNS),
            "--json", "databaseId,workflowName,status,conclusion"]
    if repo:
        base += ["--repo", repo]
    remaining = deadline_at - time.monotonic()
    if remaining <= 0:
        raise subprocess.TimeoutExpired(base, 0)
    rows = json.loads(run(base, max(1, min(PROBE_TIMEOUT, int(remaining)))) or "[]")
    if len(rows) >= MAX_RUNS:
        raise RuntimeError(f"at least {MAX_RUNS} runs match {sha[:7]}; "
                           "refusing an incomplete verdict")
    snap: dict[str, dict] = {}
    for r in rows:
        rid = str(r["databaseId"])
        state = r.get("conclusion") or r.get("status") or "unknown"
        log = f"gh run view {rid} --log-failed" + (f" --repo {repo}" if repo else "")
        snap[rid] = {"name": r.get("workflowName") or rid, "state": state,
                     "active": (r.get("status") in ACTIVE), "log": log}
        # Run-level conclusion stays unset until every lane ends; expanding
        # in-flight runs to job level surfaces the first red lane early. Each
        # expansion is bounded by the watcher's remaining overall deadline.
        if expand_jobs and r.get("status") in ACTIVE:
            left = deadline_at - time.monotonic()
            if left <= 1:
                break
            try:
                jr = ["gh", "run", "view", rid, "--json", "jobs"]
                if repo:
                    jr += ["--repo", repo]
                for j in json.loads(run(jr, max(1, min(PROBE_TIMEOUT, int(left))))).get("jobs", []):
                    jid = f"{rid}/{j.get('databaseId', j.get('name'))}"
                    jstate = j.get("conclusion") or j.get("status") or "unknown"
                    snap[jid] = {"name": f"{snap[rid]['name']}:{j.get('name')}",
                                 "state": jstate,
                                 "active": (j.get("status") in ACTIVE),
                                 "log": log}
            except subprocess.TimeoutExpired:
                break  # run rows remain authoritative; lane detail is optional
            except Exception:
                pass  # lane detail is best-effort; the run row still verdicts
    return snap


def custom_probe(cmd: str, sha: str, timeout: int) -> tuple[dict[str, dict], str | None]:
    env = dict(os.environ, CI_WATCH_SHA=sha)
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          timeout=timeout, env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"probe exited {proc.returncode}: "
                           f"{proc.stderr.strip()[:200]}")
    snap: dict[str, dict] = {}
    forced = None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("TERMINAL:"):
            forced = line.split(":", 1)[1].strip().split()[0].lower()
            continue
        # rpartition: unit names legitimately contain ':' (GitLab test:unit).
        name, separator, state = line.rpartition(":")
        if not separator or not name.strip() or not state.strip():
            raise RuntimeError(f"malformed probe line: {line[:200]}")
        token = state.strip().lower().replace("-", "_")
        snap[name.strip()] = {
            "name": name.strip(), "state": token,
            "active": token in ACTIVE | {"running"},
            "log": "(see provider logs)"}
    return snap, forced


def classify(entry: dict, custom: bool) -> str:
    state = entry["state"]
    s, f, n = ((CUSTOM_SUCCESS, CUSTOM_FAILURE, CUSTOM_NEUTRAL) if custom
               else (GH_SUCCESS, GH_FAILURE, GH_NEUTRAL))
    if state in s:
        return "success"
    if state in n:
        return "neutral"
    if entry.get("active") or state in ACTIVE:
        return "active"   # honor the probe's own not-yet-terminal signal
    return "failure"   # unknown *terminal* conclusions are never green


class VerdictParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        emit(f"CI-DONE failure -- invalid arguments: {message}")
        raise SystemExit(EXIT["failure"])


def main() -> int:
    p = VerdictParser(description=__doc__,
                      formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sha", nargs="?", default=None)
    p.add_argument("--repo", help="owner/name for gh; defaults to the checkout's")
    p.add_argument("--branch", help="ref for supersession detection "
                   "(auto-detected; omitted when detached)")
    p.add_argument("--cmd", help="custom probe command (see module docstring)")
    p.add_argument("--deadline", type=int, default=1800, help="overall seconds; "
                   "size to the pipeline's p95 INCLUDING queue, plus headroom")
    p.add_argument("--register", type=int, default=240,
                   help="seconds a run may take to appear for this SHA")
    p.add_argument("--settle", type=int, default=0,
                   help="extra seconds to wait after green for chained "
                   "workflow_run follow-ups to register")
    p.add_argument("--interval", type=int, default=15)
    p.add_argument("--heartbeat", type=int, default=150)
    p.add_argument("--expect-none", action="store_true",
                   help="path filters make zero runs normal; no-run exits 0")
    a = p.parse_args()

    # An unreachable no-run is strictly worse than a reachable one: if the
    # registration window exceeds the deadline, every filtered commit reports
    # as timeout instead.
    a.register = min(a.register, max(30, a.deadline // 2))

    sha = full_sha(a.sha or "HEAD")
    short = sha[:7]
    branch = a.branch
    if branch is None:
        try:
            b = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
            branch = None if b == "HEAD" else b   # detached: no supersession
        except Exception:
            branch = None

    start = time.monotonic()
    deadline_at = start + a.deadline
    seen: dict[str, str] = {}
    prev_keys: frozenset = frozenset()
    stable = False
    green_since: float | None = None
    errors = 0
    last_beat = start
    warned_super = False

    def done(verdict: str, detail: str = "") -> int:
        emit(f"CI-DONE {verdict}" + (f" -- {detail}" if detail else ""))
        if verdict == "no-run" and a.expect_none:
            return 0
        return EXIT[verdict]

    def bounded_sleep() -> None:
        time.sleep(max(0, min(a.interval, deadline_at - time.monotonic())))

    while True:
        # Re-sample AFTER the probe as well -- a probe can take ~45s and the
        # deadline check must not lag it.
        if time.monotonic() - start > a.deadline:
            return done("timeout", f"not terminal after {a.deadline}s -- "
                        "inspect the run; stuck is not slow")
        forced = None
        try:
            remaining = deadline_at - time.monotonic()
            if remaining <= 0:
                return done("timeout", f"not terminal after {a.deadline}s -- "
                            "inspect the run; stuck is not slow")
            if a.cmd:
                snap, forced = custom_probe(
                    a.cmd, sha, max(1, min(PROBE_TIMEOUT, int(remaining))))
            else:
                snap = gh_probe(sha, a.repo, expand_jobs=True,
                                deadline_at=deadline_at)
            errors = 0
        except Exception as exc:
            errors += 1
            if errors == WARN_STREAK:
                emit(f"CI-WARN probe failing ({errors}x): {exc}")
            if errors >= DEAD_STREAK:
                return done("probe-dead",
                            f"{errors} consecutive probe failures: {exc}")
            bounded_sleep()
            continue

        if forced:
            return done(forced if forced in EXIT else "failure",
                        f"probe declared TERMINAL: {forced}")

        now = time.monotonic()
        if not snap:
            if not seen and now - start > a.register:
                return done("no-run",
                            f"nothing registered for {short} in {a.register}s")
            bounded_sleep()
            continue

        if not seen:
            states = " · ".join(f"{v['name']}:{v['state']}"
                                for v in list(snap.values())[:6])
            emit(f"CI-RUN {short} registered: {states}")

        for k, v in sorted(snap.items()):
            if seen.get(k) != v["state"]:
                arrow = f" -> {v['state']}" if k in seen else f": {v['state']}"
                emit(f"CI-CHG {v['name']}{arrow}")
                seen[k] = v["state"]
                last_beat = now

        keys = frozenset(snap)
        stable = keys == prev_keys
        prev_keys = keys

        classes = {k: classify(v, bool(a.cmd)) for k, v in snap.items()}
        run_classes = (list(classes.values()) if a.cmd else
                       [c for k, c in classes.items() if "/" not in k])

        # Precedence: an explicit red run answers "did this SHA pass" -- it is
        # a failure even if the branch has moved on. Supersession only explains
        # cancellation, never a real red.
        failed = next((k for k, c in classes.items() if c == "failure"
                       and not snap[k]["active"]), None)
        if failed:
            return done("failure",
                        f"{snap[failed]['name']} -- logs: {snap[failed]['log']}")

        if all(c != "active" for c in classes.values()):
            # all([]) is True -- but snap is non-empty here, so a verdict on an
            # empty poll cannot happen.
            all_success = run_classes and all(c == "success" for c in run_classes)
            if all_success:
                if now - start >= a.register:
                    if a.settle and green_since is None:
                        green_since = now
                    if green_since is None or now - green_since >= a.settle:
                        # Two-poll key-set stability catches late siblings after
                        # the full registration window has elapsed.
                        if stable:
                            return done("success", short)
            else:
                # At least one run is neutral. Cancelled by a newer push, or by
                # hand? Mixed success/neutral is not an all-green verdict.
                tip = branch_tip(os.getcwd(), branch) if branch else None
                if branch and tip is None:
                    if not warned_super:
                        emit("CI-WARN cannot read origin tip; retrying "
                             "supersession detection")
                        warned_super = True
                    bounded_sleep()
                    continue
                if tip and tip != sha:
                    return done("superseded",
                                f"{short} cancelled; {branch} moved to {tip[:7]}")
                return done("cancelled",
                            f"cancelled/neutral results prevent all-green for "
                            f"{short} on an unmoved branch -- not a pass, not a "
                            "test failure")
        else:
            green_since = None   # something went active again; reset settle

        if now - last_beat >= a.heartbeat:
            mins, total = int((now - start) / 60), int(a.deadline / 60)
            states = " · ".join(f"{v['name']}={v['state']}"
                                for k, v in sorted(snap.items()) if "/" not in k)
            emit(f"CI-HB {mins}/{total}m -- {states}")
            last_beat = now

        time.sleep(a.interval)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        emit("CI-DONE timeout -- interrupted")
        sys.exit(EXIT["timeout"])
    except SystemExit:
        raise  # a real verdict already printed; do not double-emit
    except BaseException as exc:  # silence must be structurally impossible
        emit(f"CI-DONE probe-dead -- {type(exc).__name__}: {exc}")
        sys.exit(EXIT["probe-dead"])
