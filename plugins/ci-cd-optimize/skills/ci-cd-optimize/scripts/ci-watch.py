#!/usr/bin/env python3
"""ci-watch: fail-closed, exact-SHA CI watcher for agent feedback loops.

Watches every CI run for one exact commit SHA until a single terminal verdict
is reached, then prints exactly one CI-DONE record and exits with a verdict
class code. Designed for agents: append-only line output, no TTY redraw,
bounded deadlines, and no false greens.

Verdicts and exit codes:
    success     0   every run-level unit explicitly green after the settle window
    failure     1   at least one genuine red unit for the pinned SHA
    cancelled   1   cancelled/skipped/neutral units without proven supersession
    timeout     2   overall deadline reached with active units and no red
    no-run      2   nothing registered within the registration deadline
    probe-dead  2   probe/config failures exhausted the error budget
    superseded  3   branch tip provably moved and no genuine red evidence

Output protocol (one JSON payload per line, append-only):
    CI-EVENT {...}   registration, state changes, retired attempts (diff-gated)
    CI-RED   {...}   first observation of a red unit, with a log-hint argv
    CI-ERR   {...}   deduplicated probe/branch-tip errors
    CI-HB    {...}   heartbeat while otherwise quiet
    CI-DONE  {...}   exactly one, on every operational exit path

Only Python stdlib is used. Probes run as argument vectors, never through a
shell. A nonzero probe exit invalidates all of its output. Unknown states,
malformed envelopes, and incomplete enumeration fail closed toward
probe-dead — never toward success.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field

SCHEMA_VERSION = 1
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")

VERDICT_EXIT = {
    "success": 0,
    "failure": 1,
    "cancelled": 1,
    "timeout": 2,
    "no-run": 2,
    "probe-dead": 2,
    "superseded": 3,
}

# Unit classification. Run-level conclusions decide the verdict; job-level
# data only enriches events (early red detection, log hints).
ACTIVE, GREEN, RED, CANCELLED, NEUTRAL = "active", "green", "red", "cancelled", "neutral"

GITHUB_STATUS_ACTIVE = {"queued", "in_progress", "waiting", "requested", "pending"}
GITHUB_CONCLUSION = {
    "success": GREEN,
    "failure": RED,
    "timed_out": RED,
    "action_required": RED,
    "startup_failure": RED,  # zero-job failures surface at run level
    "stale": RED,
    "cancelled": CANCELLED,
    "skipped": NEUTRAL,
    "neutral": NEUTRAL,
}

# Custom probes translate provider-specific states themselves and speak only
# this canonical vocabulary. Anything else fails closed.
CANONICAL_STATES = {ACTIVE, GREEN, RED, CANCELLED, NEUTRAL}


class ProbeError(Exception):
    """Any condition that makes the current probe cycle untrustworthy."""


@dataclass
class Unit:
    key: str
    scope: str  # provider:repo:run_id — attempts within a scope supersede
    attempt: int
    name: str
    state: str
    url: str = ""
    log_hint: list[str] = field(default_factory=list)


@dataclass
class Envelope:
    units: list[Unit]
    branch_tip: str | None = None  # full sha = proven; None = unknown
    tip_error: str | None = None   # auxiliary failure; never fails the cycle


class Clock:
    def monotonic(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)


class SubprocessRunner:
    """Runs argv without a shell; returns (exit_code, stdout)."""

    def run(self, argv: list[str], timeout: float, env: dict | None = None) -> tuple[int, str]:
        merged = dict(os.environ)
        if env:
            merged.update(env)
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=max(timeout, 0.001),
                env=merged,
            )
        except FileNotFoundError as exc:
            raise ProbeError(f"probe executable not found: {argv[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ProbeError(f"probe timed out after {timeout:.1f}s: {argv[0]}") from exc
        return proc.returncode, proc.stdout


class GithubProbe:
    """Built-in GitHub Actions adapter using `gh api` with full pagination.

    gh walks every page itself; a mid-pagination failure exits nonzero, which
    invalidates the whole cycle — incomplete enumeration can never look green.
    The runs endpoint returns one row per run at its latest attempt, so rerun
    supersession is expressed through the `run_attempt` field.
    """

    def __init__(self, repo: str, sha: str, branch: str | None, runner, probe_timeout: float):
        self.repo = repo
        self.sha = sha
        self.branch = branch
        self.runner = runner
        self.probe_timeout = probe_timeout

    def _classify_run(self, run: dict) -> str:
        status = run.get("status")
        conclusion = run.get("conclusion")
        if status in GITHUB_STATUS_ACTIVE or (status != "completed" and conclusion is None):
            return ACTIVE
        if status == "completed":
            if conclusion in GITHUB_CONCLUSION:
                return GITHUB_CONCLUSION[conclusion]
            raise ProbeError(f"unknown GitHub run conclusion: {conclusion!r}")
        raise ProbeError(f"unknown GitHub run status: {status!r}")

    def fetch(self, remaining: float) -> Envelope:
        timeout = min(self.probe_timeout, remaining)
        rc, out = self.runner.run(
            [
                "gh", "api",
                f"repos/{self.repo}/actions/runs?head_sha={self.sha}&per_page=100",
                "--paginate", "--jq", ".workflow_runs[]",
            ],
            timeout=timeout,
        )
        if rc != 0:
            raise ProbeError(f"gh api run enumeration failed (exit {rc})")
        units = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                run = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ProbeError("malformed gh api run output") from exc
            head = str(run.get("head_sha", "")).lower()
            if head != self.sha:
                raise ProbeError(f"run {run.get('id')} head_sha {head!r} != requested sha")
            run_id = run.get("id")
            attempt = run.get("run_attempt")
            if run_id is None or attempt is None:
                raise ProbeError("run missing id/run_attempt")
            state = self._classify_run(run)
            scope = f"github:{self.repo}:{run_id}"
            hint = ["gh", "run", "view", str(run_id), "--repo", self.repo, "--log-failed"]
            units.append(
                Unit(
                    key=f"{scope}:{attempt}",
                    scope=scope,
                    attempt=int(attempt),
                    name=str(run.get("name") or run.get("display_title") or run_id),
                    state=state,
                    url=str(run.get("html_url", "")),
                    log_hint=hint if state == RED else [],
                )
            )
        branch_tip = None
        tip_error = None
        if self.branch:
            rc, out = self.runner.run(
                [
                    "gh", "api",
                    f"repos/{self.repo}/git/ref/heads/{self.branch}",
                    "--jq", ".object.sha",
                ],
                timeout=min(self.probe_timeout, remaining),
            )
            tip = out.strip().lower()
            if rc == 0 and FULL_SHA.match(tip):
                branch_tip = tip
            else:
                # Lookup failure cannot prove supersession or cancellation.
                tip_error = f"branch tip lookup failed for {self.branch} (exit {rc})"
        return Envelope(units=units, branch_tip=branch_tip, tip_error=tip_error)


class CommandProbe:
    """Custom provider probe: argv emits one canonical JSON envelope."""

    def __init__(self, argv: list[str], repo: str, sha: str, branch: str | None,
                 runner, probe_timeout: float):
        self.argv = argv
        self.repo = repo
        self.sha = sha
        self.branch = branch
        self.runner = runner
        self.probe_timeout = probe_timeout

    def fetch(self, remaining: float) -> Envelope:
        env = {
            "CI_WATCH_SHA": self.sha,
            "CI_WATCH_REPO": self.repo,
            "CI_WATCH_BRANCH": self.branch or "",
        }
        rc, out = self.runner.run(
            self.argv, timeout=min(self.probe_timeout, remaining), env=env
        )
        if rc != 0:
            # Partial stdout from a failed probe is never trusted.
            raise ProbeError(f"probe command exited {rc}")
        try:
            doc = json.loads(out)
        except json.JSONDecodeError as exc:
            raise ProbeError("probe emitted malformed JSON") from exc
        if not isinstance(doc, dict):
            raise ProbeError("probe envelope must be a JSON object")
        if doc.get("schema_version") != SCHEMA_VERSION:
            raise ProbeError(
                f"unsupported envelope schema_version: {doc.get('schema_version')!r}"
            )
        if doc.get("complete") is not True:
            raise ProbeError("probe envelope not marked complete; enumeration unproven")
        if str(doc.get("sha", "")).lower() != self.sha:
            raise ProbeError("probe envelope sha does not match requested sha")
        if doc.get("repository") != self.repo:
            raise ProbeError("probe envelope repository does not match requested repository")
        units = []
        for raw in doc.get("units", []):
            state = raw.get("state")
            if state not in CANONICAL_STATES:
                raise ProbeError(f"unknown canonical unit state: {state!r}")
            run_id = raw.get("run_id")
            if run_id in (None, ""):
                raise ProbeError("unit missing run_id")
            attempt = raw.get("attempt", 1)
            if not isinstance(attempt, int) or attempt < 1:
                raise ProbeError(f"unit attempt must be an integer >= 1, got {attempt!r}")
            job_id = raw.get("job_id")
            scope = f"custom:{self.repo}:{run_id}" + (f":{job_id}" if job_id else "")
            hint = raw.get("log_hint", [])
            if hint and not (isinstance(hint, list) and all(isinstance(a, str) for a in hint)):
                raise ProbeError("log_hint must be a list of strings (argv form)")
            units.append(
                Unit(
                    key=f"{scope}:{attempt}",
                    scope=scope,
                    attempt=attempt,
                    name=str(raw.get("name", run_id)),
                    state=state,
                    url=str(raw.get("url", "")),
                    log_hint=list(hint),
                )
            )
        tip = doc.get("branch_tip")
        if tip is not None:
            tip = str(tip).lower()
            if not FULL_SHA.match(tip):
                raise ProbeError("branch_tip must be a full 40-hex sha or null")
        return Envelope(units=units, branch_tip=tip)


@dataclass
class Config:
    sha: str
    repo: str
    branch: str | None
    deadline: float
    registration_deadline: float
    settle_deadline: float
    interval: float
    heartbeat: float
    max_probe_errors: int
    expect_none: bool
    allow_neutral: bool


class Watcher:
    def __init__(self, cfg: Config, probe, clock: Clock, out=None):
        self.cfg = cfg
        self.probe = probe
        self.clock = clock
        self.out = out or sys.stdout
        self.seq = 0
        self.done = False
        self.units: dict[str, Unit] = {}
        self.red_announced: set[str] = set()
        self.registered = False
        self.proven_empty = False
        self.branch_moved: bool | None = None  # None until proven either way
        self.last_error = ""
        self.last_tip_error = ""

    # -- output ------------------------------------------------------------

    def _emit(self, tag: str, payload: dict) -> None:
        self.seq += 1
        payload = {"seq": self.seq, **payload}
        self.out.write(f"{tag} {json.dumps(payload, sort_keys=True)}\n")
        self.out.flush()

    def _finish(self, verdict: str, reason: str) -> int:
        if self.done:
            return VERDICT_EXIT[verdict]
        self.done = True
        states = [u.state for u in self.units.values()]
        self._emit(
            "CI-DONE",
            {
                "verdict": verdict,
                "reason": reason,
                "sha": self.cfg.sha,
                "repo": self.cfg.repo,
                "units_total": len(self.units),
                "units_by_state": {s: states.count(s) for s in set(states)},
                "exit_code": VERDICT_EXIT[verdict],
            },
        )
        return VERDICT_EXIT[verdict]

    # -- state -------------------------------------------------------------

    def _any_red(self) -> bool:
        return any(u.state == RED for u in self.units.values())

    def _all_terminal(self) -> bool:
        return bool(self.units) and all(u.state != ACTIVE for u in self.units.values())

    def _retire_older_attempts(self, incoming: Unit) -> bool:
        """A rerun replaces earlier attempts of the same scope. Old evidence,
        including red, belongs to the retired attempt — the latest attempt is
        the authoritative one for the pinned SHA."""
        retired = False
        for key in list(self.units):
            existing = self.units[key]
            if existing.scope == incoming.scope and existing.attempt < incoming.attempt:
                del self.units[key]
                self.red_announced.discard(key)
                retired = True
                self._emit(
                    "CI-EVENT",
                    {"kind": "attempt-retired", "key": key, "name": existing.name,
                     "superseded_by_attempt": incoming.attempt},
                )
        return retired

    def _merge(self, env: Envelope, settle_until: float | None) -> float | None:
        if self.registered and not env.units:
            # Registered units disappearing from a "complete" snapshot is a
            # provider inconsistency, not evidence of anything.
            raise ProbeError("enumeration lost previously registered units")
        new_settle = settle_until
        for unit in env.units:
            if self._retire_older_attempts(unit):
                new_settle = None
            previous = self.units.get(unit.key)
            if previous is None:
                self.registered = True
                new_settle = None  # any new unit re-opens the settle window
                self._emit(
                    "CI-EVENT",
                    {"kind": "registered", "key": unit.key, "name": unit.name,
                     "state": unit.state, "url": unit.url},
                )
            elif previous.state != unit.state:
                if unit.state == ACTIVE:
                    new_settle = None
                self._emit(
                    "CI-EVENT",
                    {"kind": "state-change", "key": unit.key, "name": unit.name,
                     "from": previous.state, "to": unit.state},
                )
            self.units[unit.key] = unit
            if unit.state == RED and unit.key not in self.red_announced:
                self.red_announced.add(unit.key)
                self._emit(
                    "CI-RED",
                    {"key": unit.key, "name": unit.name, "url": unit.url,
                     "log_hint": unit.log_hint},
                )
        if env.tip_error and env.tip_error != self.last_tip_error:
            self.last_tip_error = env.tip_error
            self._emit("CI-ERR", {"error": env.tip_error, "kind": "branch-tip"})
        if env.branch_tip is not None:
            moved = env.branch_tip != self.cfg.sha
            if self.branch_moved is not moved:
                self.branch_moved = moved
                self._emit(
                    "CI-EVENT",
                    {"kind": "branch-tip", "tip": env.branch_tip, "moved": moved},
                )
        if not env.units and not self.registered:
            self.proven_empty = True
        return new_settle

    def _evaluate_terminal(self) -> tuple[str, str]:
        states = {u.state for u in self.units.values()}
        if RED in states:
            return "failure", "red-unit"
        if CANCELLED in states:
            if self.branch_moved is True:
                return "superseded", "cancelled-and-branch-moved"
            return "cancelled", "cancelled-unit"
        if NEUTRAL in states and not self.cfg.allow_neutral:
            return "cancelled", "skipped-or-neutral-units"
        return "success", "all-green"

    # -- loop --------------------------------------------------------------

    def run(self) -> int:
        try:
            return self._run_inner()
        except Exception as exc:  # never exit without a terminal record
            return self._finish("probe-dead", f"internal-error: {type(exc).__name__}: {exc}")

    def _run_inner(self) -> int:
        cfg = self.cfg
        start = self.clock.monotonic()
        deadline = start + cfg.deadline
        reg_deadline = start + cfg.registration_deadline
        next_heartbeat = start + cfg.heartbeat
        settle_until: float | None = None
        error_streak = 0

        while True:
            now = self.clock.monotonic()
            if now >= deadline:
                if self._any_red():
                    return self._finish("failure", "red-before-deadline")
                if self._all_terminal():
                    verdict, reason = self._evaluate_terminal()
                    return self._finish(verdict, reason)
                return self._finish("timeout", "overall-deadline")

            try:
                env = self.probe.fetch(remaining=deadline - now)
                error_streak = 0
                settle_until = self._merge(env, settle_until)
            except ProbeError as exc:
                error_streak += 1
                message = str(exc)
                if message != self.last_error:
                    self.last_error = message
                    self._emit("CI-ERR", {"error": message, "streak": error_streak})
                if error_streak >= cfg.max_probe_errors:
                    return self._finish("probe-dead", f"probe-error-streak: {message}")
                self._sleep_bounded(deadline)
                continue

            now = self.clock.monotonic()

            if not self.registered:
                if self.branch_moved is True:
                    return self._finish("superseded", "branch-moved-before-registration")
                if now >= reg_deadline:
                    if cfg.expect_none and self.proven_empty:
                        return self._finish("success", "expected-no-run-proven-empty")
                    return self._finish("no-run", "registration-deadline")
            elif self._all_terminal():
                if self._any_red():
                    return self._finish("failure", "red-unit")
                if settle_until is None:
                    settle_until = now + cfg.settle_deadline
                    if cfg.settle_deadline > 0:
                        self._emit(
                            "CI-EVENT",
                            {"kind": "settling", "seconds": cfg.settle_deadline},
                        )
                if now >= settle_until:
                    verdict, reason = self._evaluate_terminal()
                    return self._finish(verdict, reason)
            else:
                settle_until = None

            if now >= next_heartbeat:
                next_heartbeat = now + cfg.heartbeat
                states = [u.state for u in self.units.values()]
                self._emit(
                    "CI-HB",
                    {"elapsed": round(now - start, 1),
                     "active": states.count(ACTIVE),
                     "terminal": len(states) - states.count(ACTIVE)},
                )

            self._sleep_bounded(deadline, settle_until, next_heartbeat)

    def _sleep_bounded(self, deadline: float, *boundaries: float | None) -> None:
        now = self.clock.monotonic()
        sleep_for = min(self.cfg.interval, max(deadline - now, 0.0))
        for boundary in boundaries:
            if boundary is not None:
                sleep_for = min(sleep_for, max(boundary - now, 0.0))
        self.clock.sleep(max(sleep_for, 0.0))


# -- CLI --------------------------------------------------------------------


def _positive(value: float, name: str) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and > 0, got {value!r}")
    return float(value)


def _non_negative(value: float, name: str) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and >= 0, got {value!r}")
    return float(value)


def build_config(args) -> Config:
    sha = args.sha.lower()
    if not FULL_SHA.match(sha):
        raise ValueError("sha must be a full 40-character hex commit SHA")
    if "/" not in args.repo:
        raise ValueError("--repo must be OWNER/REPO")
    if args.max_probe_errors < 1:
        raise ValueError("--max-probe-errors must be >= 1")
    return Config(
        sha=sha,
        repo=args.repo,
        branch=args.branch,
        deadline=_positive(args.deadline, "--deadline"),
        registration_deadline=_positive(args.registration_deadline, "--registration-deadline"),
        settle_deadline=_non_negative(args.settle_deadline, "--settle-deadline"),
        interval=_positive(args.interval, "--interval"),
        heartbeat=_positive(args.heartbeat, "--heartbeat"),
        max_probe_errors=args.max_probe_errors,
        expect_none=args.expect_none,
        allow_neutral=args.allow_neutral,
    )


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci-watch.py",
        description=(
            "Fail-closed exact-SHA CI watcher. Exits 0 success, 1 failure/"
            "cancelled, 2 timeout/no-run/probe-dead, 3 superseded. Argparse "
            "usage errors exit 2 without a CI-DONE record; every other path "
            "emits exactly one CI-DONE line."
        ),
    )
    parser.add_argument("sha", help="full 40-hex commit SHA to watch")
    parser.add_argument("--repo", required=True, help="OWNER/REPO")
    parser.add_argument("--branch", default=None,
                        help="branch whose tip proves supersession (optional)")
    parser.add_argument("--deadline", type=float, default=1800.0,
                        help="hard overall deadline in seconds (default 1800)")
    parser.add_argument("--registration-deadline", type=float, default=180.0,
                        help="seconds to wait for the first unit (default 180)")
    parser.add_argument("--settle-deadline", type=float, default=60.0,
                        help="quiet seconds after all units terminal before success "
                             "(catches late siblings/chained runs; default 60)")
    parser.add_argument("--interval", type=float, default=15.0,
                        help="poll interval seconds (default 15)")
    parser.add_argument("--heartbeat", type=float, default=120.0,
                        help="heartbeat interval seconds while quiet (default 120)")
    parser.add_argument("--probe-timeout", type=float, default=60.0,
                        help="per-probe subprocess timeout seconds (default 60)")
    parser.add_argument("--max-probe-errors", type=int, default=5,
                        help="consecutive probe failures before probe-dead (default 5)")
    parser.add_argument("--expect-none", action="store_true",
                        help="success only if a successful probe proves zero runs "
                             "through the registration window (e.g. path filters)")
    parser.add_argument("--allow-neutral", action="store_true",
                        help="treat run-level skipped/neutral conclusions as green "
                             "(only when the effectiveness contract permits it)")
    parser.add_argument("--probe-command", nargs=argparse.REMAINDER, default=None,
                        help="custom probe argv emitting a canonical JSON envelope; "
                             "must be the last option — it consumes all remaining "
                             "arguments")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    out = sys.stdout

    def die(reason: str) -> int:
        payload = {"seq": 1, "verdict": "probe-dead", "reason": reason, "exit_code": 2}
        out.write(f"CI-DONE {json.dumps(payload, sort_keys=True)}\n")
        out.flush()
        return 2

    try:
        probe_timeout = _positive(args.probe_timeout, "--probe-timeout")
        cfg = build_config(args)
    except ValueError as exc:
        return die(f"invalid-arguments: {exc}")

    runner = SubprocessRunner()
    if args.probe_command:
        probe = CommandProbe(args.probe_command, cfg.repo, cfg.sha, cfg.branch,
                             runner, probe_timeout)
    else:
        probe = GithubProbe(cfg.repo, cfg.sha, cfg.branch, runner, probe_timeout)
    return Watcher(cfg, probe, Clock(), out).run()


if __name__ == "__main__":
    sys.exit(main())
