#!/usr/bin/env python3
"""ci-watch.py — provider-neutral, diff-gated CI/CD watcher for agent event tools.

Emits only state CHANGES plus liveness heartbeats, and guarantees exactly one
terminal line on every exit path. Silence past the deadline is structurally
impossible. Designed to be armed via a background-event tool (e.g. Claude Code's
Monitor) so the session keeps working while CI runs.

BUILT-IN MODE (GitHub Actions; needs `gh` authenticated):

    ci-watch.py --sha <40-char-sha> [--branch <branch>] [--repo owner/name]

  Watches every workflow triggered for that SHA. Because it queries by SHA, one
  watch survives "push, then open a PR" — runs that register later are picked up.

GENERIC MODE (GitLab, Buildkite, CircleCI, Jenkins, EAS, any deploy API):

    ci-watch.py --cmd '<probe>'

  PROBE CONTRACT: print one line per watched unit, "<name>: <state>". Lines are
  diffed as a set, so only changes are emitted. When the watch should end, print
  "TERMINAL: <verdict...>" — first word `success` exits 0, anything else exits 1.
  Exit non-zero from the probe itself to signal a probe error. Pin identifiers
  (SHA, build id) BEFORE arming; never re-resolve a moving ref inside the probe.

EVENTS (pick a stable prefix scheme; these are the defaults)
  CI-RUN   units registered
  CI-CHG   a unit changed state (act on the first failure, don't wait for DONE)
  CI-HB    liveness tick; keep the interval below the model's prompt-cache TTL
  CI-ERR   probe failing repeatedly (still retrying)
  CI-DONE  terminal verdict — always printed exactly once

VERDICTS: success · failure · no-run · superseded · timeout · probe-dead · interrupted
EXIT CODES: 0 success (or expected no-run) · 1 failure/unknown · 124 timeout · 130 interrupted

Python 3 stdlib only.
"""
import argparse
import json
import subprocess
import sys
import time

PROBE_CAP_SEC = 45
# States that count as green. Every other completed conclusion is a failure unless
# the branch moved, in which case the whole pinned watch is superseded first.
OK_CONCLUSIONS = {"success", "skipped", "neutral"}


def emit(line):
    print(line, flush=True)


def run(cmd, timeout=PROBE_CAP_SEC):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def gh_json(args):
    out = run(["gh"] + args)
    if out.returncode != 0:
        raise RuntimeError((out.stderr.strip() or f"exit {out.returncode}")[:200])
    return json.loads(out.stdout or "[]")


def branch_tip(branch, repo):
    """Resolve the branch's real tip from the ref.

    Deliberately NOT `gh run list --branch --limit 1`: that returns the latest
    RUN, which — for a branch whose newest push has not registered yet — is an
    OLDER sha, so the newest commit would be reported as superseded by its own
    ancestor. The ref is the only correct source of "what is the tip now".
    """
    remote = f"https://github.com/{repo}" if repo else "origin"
    out = run(["git", "ls-remote", remote, f"refs/heads/{branch}"])
    if out.returncode != 0:
        raise RuntimeError((out.stderr.strip() or "git ls-remote failed")[:200])
    return out.stdout.split()[0] if out.stdout.strip() else ""


def github_runs(sha, repo):
    """Fetch every Actions run for a SHA, following all API pages."""
    if repo:
        slug = repo
    else:
        out = run(["gh", "repo", "view", "--json", "nameWithOwner",
                   "--jq", ".nameWithOwner"])
        if out.returncode != 0:
            raise RuntimeError((out.stderr.strip() or "cannot resolve repository")[:200])
        slug = out.stdout.strip()
    pages = gh_json([
        "api", "--paginate", "--slurp",
        f"repos/{slug}/actions/runs?head_sha={sha}&per_page=100",
    ])
    return [item for page in pages for item in page.get("workflow_runs", [])]


def github_probe(sha, branch, repo):
    """Return (state_lines, terminal_or_None) for a pinned GitHub Actions SHA."""
    runs = github_runs(sha, repo)
    newer = ""
    if branch:
        tip = branch_tip(branch, repo)
        newer = tip if tip and tip != sha else ""

    state = set()
    for r in runs:
        label = r["status"] + (" -> " + r["conclusion"] if r.get("conclusion") else "")
        state.add(f"{r['name']} [{r['id']}]: {label}")

    # A moved branch makes this pinned watch stale even while old runs remain active.
    if newer:
        return state, f"superseded by {newer[:9]}"

    if runs and all(r["status"] == "completed" for r in runs):
        bad = sorted({r["name"] for r in runs
                      if (r.get("conclusion") or "") not in OK_CONCLUSIONS})
        if not bad:
            return state, f"success ({len(runs)} runs for {sha[:9]})"
        failed = next((r for r in runs if r.get("conclusion") == "failure"), None)
        hint = (f" — logs: gh run view {failed['id']}"
                + (f" --repo {repo}" if repo else "")
                + " --log-failed") if failed else ""
        return state, f"failure — {', '.join(bad)}{hint}"

    return state, None


def custom_probe(cmd):
    out = run(["bash", "-c", cmd])
    if out.returncode != 0:
        raise RuntimeError((out.stderr.strip() or out.stdout.strip()
                            or f"exit {out.returncode}")[:200])
    lines = [l.strip() for l in out.stdout.splitlines() if l.strip()]
    terminal = next((l.split(":", 1)[1].strip() for l in lines
                     if l.startswith("TERMINAL:")), None)
    return {l for l in lines if not l.startswith("TERMINAL:")}, terminal


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--sha", help="pinned 40-char SHA (GitHub built-in mode)")
    src.add_argument("--cmd", help="custom probe shell command (generic mode)")
    ap.add_argument("--branch", default="", help="enables superseded detection")
    ap.add_argument("--repo", default="", help="owner/name; defaults to cwd's remote")
    ap.add_argument("--interval", type=float, default=20)
    ap.add_argument("--deadline-min", type=float, default=20)
    ap.add_argument("--reg-min", type=float, default=3,
                    help="give up if nothing registers within this many minutes")
    ap.add_argument("--expect-none", action="store_true",
                    help="zero runs is the expected outcome (path-filtered push)")
    ap.add_argument("--hb-sec", type=float, default=150, help="0 disables heartbeats")
    ap.add_argument("--settle-sec", type=float, default=60,
                    help="recheck this long before reporting GitHub success")
    ns = ap.parse_args()

    # A registration deadline longer than the overall deadline makes `no-run`
    # unreachable and every skipped pipeline reports `timeout` instead.
    reg_sec = min(ns.reg_min * 60, max(30, ns.deadline_min * 60 - 30))

    t0 = time.monotonic()
    deadline = t0 + ns.deadline_min * 60
    prev, last_emit, errs = None, t0, 0
    success_terminal, success_since = None, None

    def bounded_sleep():
        time.sleep(max(0, min(ns.interval, deadline - time.monotonic())))

    while True:
        elapsed = time.monotonic() - t0
        if time.monotonic() >= deadline:
            last = " · ".join(sorted(prev)) if prev else "nothing registered"
            emit(f"CI-DONE timeout at {ns.deadline_min:g}m · last state: {last}")
            return 124

        try:
            if ns.sha:
                state, terminal = github_probe(ns.sha, ns.branch, ns.repo)
            else:
                state, terminal = custom_probe(ns.cmd)
        except Exception as exc:  # noqa: BLE001 — any probe failure is retryable
            errs += 1
            now = time.monotonic()
            if errs == 3:
                emit(f"CI-ERR probe failing (3x consecutive): {exc}")
                last_emit = now
            if errs >= 10:
                emit(f"CI-DONE probe-dead after {errs} consecutive errors")
                return 1
            if ns.hb_sec and now - last_emit >= ns.hb_sec:
                emit(f"CI-HB {elapsed / 60:.0f}/{ns.deadline_min:g}m · probe errors: {errs}")
                last_emit = now
            bounded_sleep()
            continue
        errs = 0

        if terminal and ns.sha and terminal.startswith("success"):
            now = time.monotonic()
            if terminal != success_terminal:
                success_terminal, success_since = terminal, now
            if now - success_since < ns.settle_sec:
                terminal = None
        else:
            success_terminal, success_since = None, None

        if terminal:
            emit(f"CI-DONE {terminal}")
            return 0 if terminal.split()[0].lower() == "success" else 1

        if prev is None:
            if state:
                prev = state
                emit(f"CI-RUN registered {len(state)}: " + " · ".join(sorted(state)))
                last_emit = time.monotonic()
            elif elapsed > reg_sec:
                why = ("expected — path filters matched nothing" if ns.expect_none
                       else "workflow not triggered? path filters? wrong sha?")
                emit(f"CI-DONE no-run — nothing registered in {reg_sec / 60:g}m ({why})")
                return 0 if ns.expect_none else 1
        elif state and state - prev:
            for line in sorted(state - prev):
                emit(f"CI-CHG {line}")
            prev = state
            last_emit = time.monotonic()
        # An empty state after registration is a transient blip; keep prev.

        now = time.monotonic()
        if ns.hb_sec and now - last_emit >= ns.hb_sec:
            emit(f"CI-HB {elapsed / 60:.0f}/{ns.deadline_min:g}m")
            last_emit = now

        bounded_sleep()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        emit("CI-DONE interrupted — cancelled by operator")
        sys.exit(130)
