"""Deterministic regression suite for skills/ci-cd-optimize/scripts/ci-watch.py.

Covers the full verdict matrix and every pathological branch derived from the
open-PR defect corpus (see evals/requirements-matrix.json). Unit tests inject
a fake clock and scripted probes; CLI tests run the real script over fixture
envelopes with a tiny subprocess probe. No network access.
"""

import importlib.util
import io
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[1]
SCRIPT = REPO_ROOT / "skills" / "ci-cd-optimize" / "scripts" / "ci-watch.py"
FIXTURES = TESTS_DIR / "fixtures" / "watcher"

# Importing the script must never litter the packaged skill with bytecode:
# the repo validator bans __pycache__ inside skill directories.
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("ci_watch", SCRIPT)
ci_watch = importlib.util.module_from_spec(spec)
sys.modules["ci_watch"] = ci_watch
spec.loader.exec_module(ci_watch)

SHA = "a" * 40
OTHER = "b" * 40


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        # A zero-length sleep still advances time so scenarios always progress.
        self.now += max(seconds, 0.01)


class ScriptedProbe:
    """Yields scripted envelopes/errors; repeats the last step when exhausted.

    `cost` simulates probe wall time, bounded by `remaining` exactly like a
    real subprocess timeout would bound it.
    """

    def __init__(self, steps, clock=None, cost=0.0):
        assert steps, "ScriptedProbe needs at least one step"
        self.steps = list(steps)
        self.last = self.steps[-1]
        self.clock = clock
        self.cost = cost
        self.remaining_seen = []

    def fetch(self, remaining):
        self.remaining_seen.append(remaining)
        if self.clock is not None and self.cost:
            self.clock.now += min(self.cost, remaining)
        step = self.steps.pop(0) if self.steps else self.last
        if isinstance(step, Exception):
            raise step
        return step


class FakeRunner:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def run(self, argv, timeout, env=None):
        self.calls.append({"argv": argv, "timeout": timeout, "env": env})
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def unit(run_id, state, attempt=1, name=None):
    scope = f"github:o/r:{run_id}"
    return ci_watch.Unit(
        key=f"{scope}:{attempt}", scope=scope, attempt=attempt,
        name=name or f"wf-{run_id}", state=state,
    )


def envelope(*units, tip=None, tip_error=None, early_reds=()):
    return ci_watch.Envelope(units=list(units), branch_tip=tip,
                             tip_error=tip_error, early_reds=list(early_reds))


def make_config(**overrides):
    values = dict(
        sha=SHA, repo="o/r", branch=None, deadline=600.0,
        registration_deadline=120.0, settle_deadline=30.0, interval=5.0,
        heartbeat=60.0, max_probe_errors=3, expect_none=False,
        allow_neutral=False,
    )
    values.update(overrides)
    return ci_watch.Config(**values)


def run_watch(steps, probe_cost=0.0, **config_overrides):
    clock = FakeClock()
    out = io.StringIO()
    probe = ScriptedProbe(steps, clock=clock, cost=probe_cost)
    watcher = ci_watch.Watcher(make_config(**config_overrides), probe, clock, out)
    code = watcher.run()
    lines = out.getvalue().splitlines()
    done_lines = [line for line in lines if line.startswith("CI-DONE ")]
    done = json.loads(done_lines[0].split(" ", 1)[1]) if done_lines else None
    return code, lines, done_lines, done, probe, clock


class WatcherScenarioTests(unittest.TestCase):
    def assert_single_done(self, done_lines):
        self.assertEqual(len(done_lines), 1, "exactly one CI-DONE record required")

    def assert_all_lines_parse(self, lines):
        for line in lines:
            tag, _, payload = line.partition(" ")
            self.assertIn(tag, {"CI-EVENT", "CI-RED", "CI-ERR", "CI-HB", "CI-DONE"})
            json.loads(payload)

    def test_success_lifecycle(self):
        code, lines, done_lines, done, _, _ = run_watch(
            [envelope(unit(1, ci_watch.ACTIVE)), envelope(unit(1, ci_watch.GREEN))]
        )
        self.assertEqual((code, done["verdict"]), (0, "success"))
        self.assert_single_done(done_lines)
        self.assert_all_lines_parse(lines)

    def test_initial_red_emits_event_and_fails(self):
        code, lines, done_lines, done, _, _ = run_watch(
            [envelope(unit(1, ci_watch.RED))]
        )
        self.assertEqual((code, done["verdict"]), (1, "failure"))
        self.assertTrue(any(line.startswith("CI-RED ") for line in lines))
        self.assert_single_done(done_lines)

    def test_no_run_at_registration_deadline(self):
        code, _, done_lines, done, _, _ = run_watch([envelope()])
        self.assertEqual((code, done["verdict"]), (2, "no-run"))
        self.assert_single_done(done_lines)

    def test_expect_none_success_requires_proven_empty(self):
        code, _, _, done, _, _ = run_watch([envelope()], expect_none=True)
        self.assertEqual((code, done["verdict"]), (0, "success"))
        self.assertEqual(done["reason"], "expected-no-run-proven-empty")

    def test_expect_none_never_satisfied_by_dead_probe(self):
        code, _, _, done, _, _ = run_watch(
            [ci_watch.ProbeError("boom")], expect_none=True, max_probe_errors=2
        )
        self.assertEqual((code, done["verdict"]), (2, "probe-dead"))

    def test_probe_dead_after_error_streak_with_dedup(self):
        code, lines, done_lines, done, _, _ = run_watch(
            [ci_watch.ProbeError("api down")], max_probe_errors=3
        )
        self.assertEqual((code, done["verdict"]), (2, "probe-dead"))
        err_lines = [line for line in lines if line.startswith("CI-ERR ")]
        self.assertEqual(len(err_lines), 1, "identical errors must be deduplicated")
        self.assert_single_done(done_lines)

    def test_error_streak_resets_on_successful_probe(self):
        steps = [
            ci_watch.ProbeError("blip"), ci_watch.ProbeError("blip"),
            envelope(unit(1, ci_watch.ACTIVE)),
            ci_watch.ProbeError("blip"), ci_watch.ProbeError("blip"),
            envelope(unit(1, ci_watch.GREEN)),
        ]
        code, _, _, done, _, _ = run_watch(steps, max_probe_errors=3)
        self.assertEqual((code, done["verdict"]), (0, "success"))

    def test_timeout_with_active_units(self):
        code, _, _, done, _, _ = run_watch(
            [envelope(unit(1, ci_watch.ACTIVE))], deadline=100.0
        )
        self.assertEqual((code, done["verdict"]), (2, "timeout"))

    def test_proven_empty_at_overall_deadline_is_no_run(self):
        code, _, _, done, _, _ = run_watch(
            [envelope()], deadline=100.0, registration_deadline=100.0
        )
        self.assertEqual((code, done["verdict"]), (2, "no-run"))
        self.assertEqual(done["reason"], "proven-empty-at-deadline")

    def test_expect_none_honored_at_overall_deadline(self):
        code, _, _, done, _, _ = run_watch(
            [envelope()], deadline=100.0, registration_deadline=100.0,
            expect_none=True,
        )
        self.assertEqual((code, done["verdict"]), (0, "success"))
        self.assertEqual(done["reason"], "expected-no-run-proven-empty")

    def test_early_job_red_announced_once_never_gates_verdict(self):
        job = ci_watch.Unit(
            key="github:o/r:1:1:job:9", scope="github:o/r:1", attempt=1,
            name="lint", state=ci_watch.RED,
            log_hint=["gh", "run", "view", "--repo", "o/r", "--job", "9",
                      "--log-failed"],
        )
        steps = [
            envelope(unit(1, ci_watch.ACTIVE), early_reds=[job]),
            envelope(unit(1, ci_watch.ACTIVE), early_reds=[job]),
            # continue-on-error: the failed job's run still concludes green.
            envelope(unit(1, ci_watch.GREEN)),
        ]
        code, lines, done_lines, done, _, _ = run_watch(steps)
        self.assertEqual((code, done["verdict"]), (0, "success"))
        red_lines = [json.loads(l.split(" ", 1)[1]) for l in lines
                     if l.startswith("CI-RED ")]
        self.assertEqual(len(red_lines), 1, "early job red must announce once")
        self.assertEqual(red_lines[0]["scope"], "job")
        self.assert_single_done(done_lines)

    def test_interrupt_emits_terminal_record(self):
        class InterruptingProbe:
            def fetch(self, remaining):
                raise KeyboardInterrupt

        out = io.StringIO()
        watcher = ci_watch.Watcher(make_config(), InterruptingProbe(),
                                   FakeClock(), out)
        code = watcher.run()
        done_lines = [l for l in out.getvalue().splitlines()
                      if l.startswith("CI-DONE ")]
        self.assertEqual(len(done_lines), 1)
        done = json.loads(done_lines[0].split(" ", 1)[1])
        self.assertEqual((code, done["verdict"], done["reason"]),
                         (2, "probe-dead", "interrupted"))

    def test_red_takes_precedence_at_deadline(self):
        code, _, _, done, _, _ = run_watch(
            [envelope(unit(1, ci_watch.RED), unit(2, ci_watch.ACTIVE))],
            deadline=100.0,
        )
        self.assertEqual((code, done["verdict"]), (1, "failure"))

    def test_cancelled_without_proof_stays_cancelled(self):
        code, _, _, done, _, _ = run_watch([envelope(unit(1, ci_watch.CANCELLED))])
        self.assertEqual((code, done["verdict"]), (1, "cancelled"))

    def test_cancelled_with_proven_moved_tip_is_superseded(self):
        code, _, _, done, _, _ = run_watch(
            [envelope(unit(1, ci_watch.CANCELLED), tip=OTHER)]
        )
        self.assertEqual((code, done["verdict"]), (3, "superseded"))

    def test_genuine_red_precedes_supersession(self):
        code, _, _, done, _, _ = run_watch(
            [envelope(unit(1, ci_watch.RED), tip=OTHER)]
        )
        self.assertEqual((code, done["verdict"]), (1, "failure"))

    def test_superseded_before_registration(self):
        code, _, _, done, _, _ = run_watch([envelope(tip=OTHER)])
        self.assertEqual((code, done["verdict"]), (3, "superseded"))
        self.assertEqual(done["reason"], "branch-moved-before-registration")

    def test_tip_lookup_failure_cannot_prove_anything(self):
        code, lines, _, done, _, _ = run_watch(
            [envelope(unit(1, ci_watch.CANCELLED), tip_error="tip lookup failed")]
        )
        self.assertEqual((code, done["verdict"]), (1, "cancelled"))
        self.assertTrue(any('"kind": "branch-tip"' in line
                            for line in lines if line.startswith("CI-ERR ")))

    def test_unmoved_tip_is_not_supersession(self):
        code, _, _, done, _, _ = run_watch(
            [envelope(unit(1, ci_watch.GREEN), tip=SHA)]
        )
        self.assertEqual((code, done["verdict"]), (0, "success"))

    def test_late_sibling_resets_settle_and_counts(self):
        steps = [
            envelope(unit(1, ci_watch.GREEN)),
            envelope(unit(1, ci_watch.GREEN), unit(2, ci_watch.ACTIVE)),
            envelope(unit(1, ci_watch.GREEN), unit(2, ci_watch.GREEN)),
        ]
        code, lines, _, done, _, _ = run_watch(steps)
        self.assertEqual((code, done["verdict"]), (0, "success"))
        self.assertEqual(done["units_total"], 2)
        registered = [line for line in lines if '"kind": "registered"' in line]
        self.assertEqual(len(registered), 2)

    def test_chained_run_red_after_first_green_is_failure(self):
        steps = [
            envelope(unit(1, ci_watch.GREEN)),
            envelope(unit(1, ci_watch.GREEN), unit(2, ci_watch.ACTIVE)),
            envelope(unit(1, ci_watch.GREEN), unit(2, ci_watch.RED)),
        ]
        code, _, _, done, _, _ = run_watch(steps)
        self.assertEqual((code, done["verdict"]), (1, "failure"))

    def test_neutral_mixture_is_not_green(self):
        code, _, _, done, _, _ = run_watch(
            [envelope(unit(1, ci_watch.GREEN), unit(2, ci_watch.NEUTRAL))]
        )
        self.assertEqual((code, done["verdict"]), (1, "cancelled"))
        self.assertEqual(done["reason"], "skipped-or-neutral-units")

    def test_allow_neutral_permits_green(self):
        code, _, _, done, _, _ = run_watch(
            [envelope(unit(1, ci_watch.GREEN), unit(2, ci_watch.NEUTRAL))],
            allow_neutral=True,
        )
        self.assertEqual((code, done["verdict"]), (0, "success"))

    def test_green_plus_cancelled_is_not_green(self):
        code, _, _, done, _, _ = run_watch(
            [envelope(unit(1, ci_watch.GREEN), unit(2, ci_watch.CANCELLED))]
        )
        self.assertEqual((code, done["verdict"]), (1, "cancelled"))

    def test_rerun_attempt_retires_old_red(self):
        steps = [
            envelope(unit(1, ci_watch.RED), unit(2, ci_watch.ACTIVE)),
            envelope(unit(1, ci_watch.ACTIVE, attempt=2), unit(2, ci_watch.ACTIVE)),
            envelope(unit(1, ci_watch.GREEN, attempt=2), unit(2, ci_watch.GREEN)),
        ]
        code, lines, _, done, _, _ = run_watch(steps)
        self.assertEqual((code, done["verdict"]), (0, "success"),
                         "a green rerun must not be false-redded by the retired attempt")
        self.assertTrue(any('"kind": "attempt-retired"' in line for line in lines))

    def test_key_stability_across_completion(self):
        steps = [envelope(unit(1, ci_watch.ACTIVE)), envelope(unit(1, ci_watch.GREEN))]
        code, lines, _, done, _, _ = run_watch(steps)
        registered = [line for line in lines if '"kind": "registered"' in line]
        changes = [line for line in lines if '"kind": "state-change"' in line]
        self.assertEqual((len(registered), len(changes)), (1, 1))
        self.assertEqual(done["verdict"], "success")

    def test_duplicate_names_tracked_by_id(self):
        steps = [envelope(unit(1, ci_watch.GREEN, name="CI"),
                          unit(2, ci_watch.GREEN, name="CI"))]
        code, _, _, done, _, _ = run_watch(steps)
        self.assertEqual((code, done["units_total"]), (0, 2))

    def test_enumeration_loss_is_probe_error_not_verdict(self):
        steps = [envelope(unit(1, ci_watch.ACTIVE)), envelope()]
        code, lines, _, done, _, _ = run_watch(steps, max_probe_errors=1)
        self.assertEqual((code, done["verdict"]), (2, "probe-dead"))
        self.assertTrue(any("enumeration lost" in line for line in lines))

    def test_punctuation_names_stay_parseable(self):
        tricky = 'we "ship: it"/fast\tλ, ok'
        steps = [envelope(unit(1, ci_watch.GREEN, name=tricky))]
        code, lines, done_lines, done, _, _ = run_watch(steps)
        self.assertEqual(done["verdict"], "success")
        self.assert_all_lines_parse(lines)

    def test_heartbeats_while_quiet(self):
        code, lines, _, done, _, _ = run_watch(
            [envelope(unit(1, ci_watch.ACTIVE))], deadline=200.0, heartbeat=60.0
        )
        heartbeats = [line for line in lines if line.startswith("CI-HB ")]
        self.assertGreaterEqual(len(heartbeats), 2)
        self.assertEqual(done["verdict"], "timeout")

    def test_probe_remaining_is_bounded_and_shrinks(self):
        _, _, _, _, probe, _ = run_watch(
            [envelope(unit(1, ci_watch.ACTIVE))], deadline=100.0
        )
        self.assertTrue(all(0 < r <= 100.0 for r in probe.remaining_seen))
        self.assertLess(probe.remaining_seen[-1], probe.remaining_seen[0])

    def test_costly_probe_cannot_overrun_short_deadline(self):
        code, _, done_lines, done, _, clock = run_watch(
            [envelope(unit(1, ci_watch.ACTIVE))], deadline=30.0, probe_cost=50.0
        )
        self.assertEqual((code, done["verdict"]), (2, "timeout"))
        self.assertLessEqual(clock.now, 31.0)
        self.assert_single_done(done_lines)

    def test_settling_event_emitted(self):
        _, lines, _, done, _, _ = run_watch([envelope(unit(1, ci_watch.GREEN))])
        self.assertTrue(any('"kind": "settling"' in line for line in lines))
        self.assertEqual(done["verdict"], "success")

    def test_internal_error_still_emits_terminal_record(self):
        class ExplodingProbe:
            def fetch(self, remaining):
                raise RuntimeError("unexpected bug")

        out = io.StringIO()
        watcher = ci_watch.Watcher(make_config(), ExplodingProbe(), FakeClock(), out)
        code = watcher.run()
        done_lines = [l for l in out.getvalue().splitlines() if l.startswith("CI-DONE ")]
        self.assertEqual(code, 2)
        self.assertEqual(len(done_lines), 1)
        self.assertIn("internal-error", done_lines[0])


class CommandProbeTests(unittest.TestCase):
    def make_probe(self, results):
        runner = FakeRunner(results)
        probe = ci_watch.CommandProbe(
            ["probe-cmd"], "o/r", SHA, "feat/x", runner, probe_timeout=60.0
        )
        return probe, runner

    def fixture_text(self, name):
        return (FIXTURES / name).read_text()

    def test_nonzero_exit_invalidates_partial_output(self):
        probe, _ = self.make_probe([(1, self.fixture_text("success-lifecycle.json"))])
        with self.assertRaises(ci_watch.ProbeError):
            probe.fetch(remaining=100.0)

    def test_malformed_json_fails_closed(self):
        probe, _ = self.make_probe([(0, self.fixture_text("malformed.json"))])
        with self.assertRaises(ci_watch.ProbeError):
            probe.fetch(remaining=100.0)

    def test_unknown_state_fails_closed(self):
        doc = json.loads(self.fixture_text("success-lifecycle.json"))
        doc["units"][0]["state"] = "passed"
        probe, _ = self.make_probe([(0, json.dumps(doc))])
        with self.assertRaises(ci_watch.ProbeError):
            probe.fetch(remaining=100.0)

    def test_incomplete_enumeration_fails_closed(self):
        doc = json.loads(self.fixture_text("success-lifecycle.json"))
        doc["complete"] = False
        probe, _ = self.make_probe([(0, json.dumps(doc))])
        with self.assertRaises(ci_watch.ProbeError):
            probe.fetch(remaining=100.0)

    def test_sha_and_repo_mismatch_fail_closed(self):
        for field, value in (("sha", OTHER), ("repository", "x/y")):
            doc = json.loads(self.fixture_text("success-lifecycle.json"))
            doc[field] = value
            probe, _ = self.make_probe([(0, json.dumps(doc))])
            with self.assertRaises(ci_watch.ProbeError):
                probe.fetch(remaining=100.0)

    def test_invalid_attempt_fails_closed(self):
        for bad in (0, -1, "1", 1.5):
            doc = json.loads(self.fixture_text("success-lifecycle.json"))
            doc["units"][0]["attempt"] = bad
            probe, _ = self.make_probe([(0, json.dumps(doc))])
            with self.assertRaises(ci_watch.ProbeError):
                probe.fetch(remaining=100.0)

    def test_short_branch_tip_fails_closed(self):
        doc = json.loads(self.fixture_text("success-lifecycle.json"))
        doc["branch_tip"] = "abc123"
        probe, _ = self.make_probe([(0, json.dumps(doc))])
        with self.assertRaises(ci_watch.ProbeError):
            probe.fetch(remaining=100.0)

    def test_valid_envelope_parses_units_and_env(self):
        probe, runner = self.make_probe([(0, self.fixture_text("late-chained-run.json"))])
        env = probe.fetch(remaining=100.0)
        self.assertEqual(len(env.units), 2)
        self.assertEqual({u.state for u in env.units}, {ci_watch.GREEN, ci_watch.ACTIVE})
        call_env = runner.calls[0]["env"]
        self.assertEqual(call_env["CI_WATCH_SHA"], SHA)
        self.assertEqual(call_env["CI_WATCH_REPO"], "o/r")
        self.assertEqual(call_env["CI_WATCH_BRANCH"], "feat/x")

    def test_rerun_attempt_lands_in_key(self):
        probe, _ = self.make_probe([(0, self.fixture_text("rerun-attempt.json"))])
        env = probe.fetch(remaining=100.0)
        self.assertEqual(env.units[0].attempt, 2)
        self.assertTrue(env.units[0].key.endswith(":2"))

    def test_probe_timeout_bounded_by_remaining(self):
        probe, runner = self.make_probe([(0, self.fixture_text("transient-empty.json"))])
        probe.fetch(remaining=10.0)
        self.assertEqual(runner.calls[0]["timeout"], 10.0)


class GithubProbeTests(unittest.TestCase):
    def make_probe(self, results, branch=None):
        runner = FakeRunner(results)
        probe = ci_watch.GithubProbe("o/r", SHA, branch, runner, probe_timeout=60.0)
        return probe, runner

    def test_full_vocabulary_classification(self):
        ndjson = (FIXTURES / "provider-vocabularies.json").read_text()
        # The three active runs each trigger one job-expansion lookup.
        probe, _ = self.make_probe([(0, ndjson), (0, ""), (0, ""), (0, "")])
        env = probe.fetch(remaining=100.0)
        states = {u.name: u.state for u in env.units}
        self.assertEqual(states["vocab-completed-success"], ci_watch.GREEN)
        for red in ("failure", "timed_out", "action_required", "startup_failure", "stale"):
            self.assertEqual(states[f"vocab-completed-{red}"], ci_watch.RED)
        self.assertEqual(states["vocab-completed-cancelled"], ci_watch.CANCELLED)
        for neutral in ("skipped", "neutral"):
            self.assertEqual(states[f"vocab-completed-{neutral}"], ci_watch.NEUTRAL)
        for active in ("in_progress", "queued", "waiting"):
            self.assertEqual(states[f"vocab-{active}-None"], ci_watch.ACTIVE)

    def test_unknown_conclusion_fails_closed(self):
        row = json.dumps({"id": 1, "run_attempt": 1, "status": "completed",
                          "conclusion": "mystery", "name": "x",
                          "html_url": "", "head_sha": SHA})
        probe, _ = self.make_probe([(0, row)])
        with self.assertRaises(ci_watch.ProbeError):
            probe.fetch(remaining=100.0)

    def test_head_sha_mismatch_fails_closed(self):
        row = json.dumps({"id": 1, "run_attempt": 1, "status": "completed",
                          "conclusion": "success", "name": "x",
                          "html_url": "", "head_sha": OTHER})
        probe, _ = self.make_probe([(0, row)])
        with self.assertRaises(ci_watch.ProbeError):
            probe.fetch(remaining=100.0)

    def test_enumeration_failure_is_probe_error(self):
        probe, _ = self.make_probe([(1, "")])
        with self.assertRaises(ci_watch.ProbeError):
            probe.fetch(remaining=100.0)

    def test_paginated_ndjson_all_rows_parsed(self):
        ndjson = (FIXTURES / "pagination.json").read_text()
        probe, _ = self.make_probe([(0, ndjson)])
        env = probe.fetch(remaining=100.0)
        self.assertEqual(len(env.units), 120)
        self.assertTrue(all(u.state == ci_watch.GREEN for u in env.units))

    def test_tip_lookup_failure_reports_without_raising(self):
        run_row = json.dumps({"id": 1, "run_attempt": 1, "status": "completed",
                              "conclusion": "success", "name": "x",
                              "html_url": "", "head_sha": SHA})
        probe, _ = self.make_probe([(0, run_row), (1, "")], branch="feat/x")
        env = probe.fetch(remaining=100.0)
        self.assertIsNone(env.branch_tip)
        self.assertIn("branch tip lookup failed", env.tip_error)

    def test_red_run_gets_log_hint_argv(self):
        row = json.dumps({"id": 42, "run_attempt": 1, "status": "completed",
                          "conclusion": "failure", "name": "x",
                          "html_url": "", "head_sha": SHA})
        probe, _ = self.make_probe([(0, row)])
        env = probe.fetch(remaining=100.0)
        self.assertEqual(
            env.units[0].log_hint,
            ["gh", "run", "view", "42", "--repo", "o/r", "--log-failed"],
        )

    def test_job_expansion_surfaces_failed_job_in_active_run(self):
        run_row = json.dumps({"id": 7, "run_attempt": 2, "status": "in_progress",
                              "conclusion": None, "name": "ci",
                              "html_url": "", "head_sha": SHA})
        jobs = "\n".join([
            json.dumps({"id": 91, "name": "lint", "status": "completed",
                        "conclusion": "failure", "html_url": "u"}),
            json.dumps({"id": 92, "name": "test", "status": "in_progress",
                        "conclusion": None}),
        ])
        probe, runner = self.make_probe([(0, run_row), (0, jobs)])
        env = probe.fetch(remaining=100.0)
        self.assertEqual([u.state for u in env.units], [ci_watch.ACTIVE])
        self.assertEqual(len(env.early_reds), 1)
        red = env.early_reds[0]
        self.assertEqual(red.key, "github:o/r:7:2:job:91")
        self.assertEqual(red.state, ci_watch.RED)
        self.assertEqual(
            red.log_hint,
            ["gh", "run", "view", "--repo", "o/r", "--job", "91", "--log-failed"],
        )
        self.assertIn("/actions/runs/7/jobs", runner.calls[1]["argv"][2])

    def test_job_expansion_failure_never_fails_the_cycle(self):
        run_row = json.dumps({"id": 7, "run_attempt": 1, "status": "in_progress",
                              "conclusion": None, "name": "ci",
                              "html_url": "", "head_sha": SHA})
        probe, _ = self.make_probe([(0, run_row), (1, "")])
        env = probe.fetch(remaining=100.0)
        self.assertEqual(len(env.units), 1)
        self.assertEqual(env.early_reds, [])

    def test_completed_runs_get_no_jobs_lookup(self):
        row = json.dumps({"id": 1, "run_attempt": 1, "status": "completed",
                          "conclusion": "success", "name": "x",
                          "html_url": "", "head_sha": SHA})
        probe, runner = self.make_probe([(0, row)])
        env = probe.fetch(remaining=100.0)
        self.assertEqual(env.early_reds, [])
        self.assertEqual(len(runner.calls), 1,
                         "completed runs must not pay a jobs lookup")


PROBE_HELPER = """\
import sys
sys.stdout.write(open(sys.argv[1]).read())
"""


class CliTests(unittest.TestCase):
    """End-to-end runs of the real script with a fixture-emitting probe."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmp = tempfile.mkdtemp(prefix="ci-watch-test-")
        cls.probe_py = Path(cls.tmp) / "probe.py"
        cls.probe_py.write_text(PROBE_HELPER)

    def run_cli(self, *args):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True, text=True, timeout=120,
        )
        done_lines = [l for l in proc.stdout.splitlines() if l.startswith("CI-DONE ")]
        done = json.loads(done_lines[0].split(" ", 1)[1]) if done_lines else None
        return proc, done_lines, done

    def fast_args(self, fixture):
        return [
            SHA, "--repo", "o/r",
            "--deadline", "20", "--registration-deadline", "5",
            "--settle-deadline", "0.05", "--interval", "0.05",
            "--heartbeat", "50", "--max-probe-errors", "2",
            "--probe-command", sys.executable, str(self.probe_py),
            str(FIXTURES / fixture),
        ]

    def test_cli_success_exit_0(self):
        proc, done_lines, done = self.run_cli(*self.fast_args("success-lifecycle.json"))
        self.assertEqual((proc.returncode, done["verdict"]), (0, "success"))
        self.assertEqual(len(done_lines), 1)

    def test_cli_failure_exit_1(self):
        proc, _, done = self.run_cli(*self.fast_args("initial-failure.json"))
        self.assertEqual((proc.returncode, done["verdict"]), (1, "failure"))

    def test_cli_red_beats_superseded_exit_1(self):
        proc, _, done = self.run_cli(*self.fast_args("failure-then-superseded.json"))
        self.assertEqual((proc.returncode, done["verdict"]), (1, "failure"))

    def test_cli_superseded_exit_3(self):
        proc, _, done = self.run_cli(*self.fast_args("superseded.json"))
        self.assertEqual((proc.returncode, done["verdict"]), (3, "superseded"))

    def test_cli_cancelled_exit_1(self):
        proc, _, done = self.run_cli(*self.fast_args("cancelled.json"))
        self.assertEqual((proc.returncode, done["verdict"]), (1, "cancelled"))

    def test_cli_duplicate_names_success(self):
        proc, _, done = self.run_cli(*self.fast_args("duplicate-names.json"))
        self.assertEqual((proc.returncode, done["units_total"]), (0, 2))

    def test_cli_expect_none_success(self):
        args = self.fast_args("transient-empty.json")
        args.insert(1, "--expect-none")
        proc, _, done = self.run_cli(*args)
        self.assertEqual((proc.returncode, done["verdict"]), (0, "success"))
        self.assertEqual(done["reason"], "expected-no-run-proven-empty")

    def test_cli_invalid_sha_dies_structured(self):
        proc, done_lines, done = self.run_cli("deadbeef", "--repo", "o/r")
        self.assertEqual((proc.returncode, done["verdict"]), (2, "probe-dead"))
        self.assertIn("invalid-arguments", done["reason"])
        self.assertEqual(len(done_lines), 1)

    def test_cli_invalid_durations_die_structured(self):
        for flags in (["--interval", "0"], ["--deadline", "nan"],
                      ["--heartbeat", "-1"], ["--settle-deadline", "inf"],
                      ["--max-probe-errors", "0"]):
            proc, _, done = self.run_cli(SHA, "--repo", "o/r", *flags)
            self.assertEqual((proc.returncode, done["verdict"]), (2, "probe-dead"),
                             f"flags {flags} must die structured")

    def test_cli_help_documents_contract(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(proc.returncode, 0)
        for flag in ("--deadline", "--registration-deadline", "--settle-deadline",
                     "--interval", "--heartbeat", "--probe-timeout",
                     "--max-probe-errors", "--expect-none", "--allow-neutral",
                     "--probe-command"):
            self.assertIn(flag, proc.stdout)


class ConfigValidationTests(unittest.TestCase):
    def test_registration_deadline_clamped_to_deadline(self):
        parser = ci_watch.make_parser()
        cfg = ci_watch.build_config(
            parser.parse_args([SHA, "--repo", "o/r", "--deadline", "60"])
        )
        self.assertEqual(cfg.registration_deadline, 60.0,
                         "default 180s registration window must clamp to --deadline")

    def test_rejects_non_finite_and_non_positive(self):
        parser = ci_watch.make_parser()
        for argv in (
            [SHA, "--repo", "o/r", "--interval", "0"],
            [SHA, "--repo", "o/r", "--deadline", "-5"],
            [SHA, "--repo", "o/r", "--heartbeat", "nan"],
            [SHA, "--repo", "o/r", "--registration-deadline", "inf"],
            [SHA, "--repo", "o/r", "--settle-deadline", "-0.1"],
        ):
            with self.assertRaises(ValueError):
                ci_watch.build_config(parser.parse_args(argv))

    def test_rejects_short_and_non_hex_sha(self):
        parser = ci_watch.make_parser()
        for sha in ("deadbeef", "g" * 40, SHA[:-1]):
            with self.assertRaises(ValueError):
                ci_watch.build_config(parser.parse_args([sha, "--repo", "o/r"]))

    def test_accepts_uppercase_sha_normalized(self):
        parser = ci_watch.make_parser()
        cfg = ci_watch.build_config(parser.parse_args([SHA.upper(), "--repo", "o/r"]))
        self.assertEqual(cfg.sha, SHA)

    def test_exit_map_is_complete_and_correct(self):
        self.assertEqual(
            ci_watch.VERDICT_EXIT,
            {"success": 0, "failure": 1, "cancelled": 1, "timeout": 2,
             "no-run": 2, "probe-dead": 2, "superseded": 3},
        )


if __name__ == "__main__":
    unittest.main()
