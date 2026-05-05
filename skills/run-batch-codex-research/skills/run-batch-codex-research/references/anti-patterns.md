# Anti-patterns — what NOT to do

Concrete failure modes from real-world batch fanout. Each is paired with the right move.

## AP-1: Arming the Monitor after the runner starts

**Symptom:** First wave of START events is missing from the conversation. The user can't tell which jobs are inflight vs queued.

**Cause:** `tail -F` started after the runner has already written `START a`, `START b`, …, `START j`. Those lines pre-exist; tail follows from end-of-file forward, so it never sees them.

**Fix:** Always arm Monitor *before* launching the runner. The 5-iteration "wait for log to appear" loop in `watch-runner.sh` exists for this — the watcher tolerates the runner not yet having written, but cannot tolerate having missed prior writes.

## AP-2: Auto-retrying everything below MIN

**Symptom:** Batch is rerun in a loop chasing larger outputs. Some answers oscillate (good → bad → worse → bad). Token spend escalates.

**Cause:** Treating size as a deterministic quality verdict. Codex is non-deterministic; retry-by-size fights with the input's natural footprint rather than against actual failures.

**Fix:** Surface flagged answers, read them, decide manually. The audit script's recommendation is "inspect" not "retry-all". If you must automate, define a hard rule that captures the actual failure (e.g. answer text matches `^I cannot access`) — not the proxy.

## AP-3: Running two runners over the same workdir

**Symptom:** Same prompt processed twice. Logs interleaved. Race on the answer file.

**Cause:** User started a second runner thinking it would finish faster, or didn't notice the first one was still running.

**Fix:** Check before launching: `pgrep -f run-batch.sh` should be zero. If you really want more concurrency, kill the first and relaunch with a higher `JOBS`.

## AP-4: Ignoring SKIP semantics

**Symptom:** User sees 50 SKIP events on a rerun and worries the work didn't get done.

**Cause:** SKIP means "answer already exists, runner intentionally not re-doing the work." It's a healthy state, not a failure. Confusion comes from SKIP being lumped into "things that are not DONE."

**Fix:** Audit script reports DONE / FAIL / SKIP separately. SKIP count == "from prior runs"; DONE count == "this run". If you want to redo a SKIP, archive its answer and rerun.

## AP-5: Recursive worktree fanout

**Symptom:** User tries to run this skill from inside a `run-codex-exec` worktree, gets confused branch state, codex jobs interfere with each other.

**Cause:** Mixing workflows. This skill is for stateless prompt fanout in a flat dir. `run-codex-exec` is for coding work in git worktrees. They have different cwd assumptions and `run-codex-exec` mutates branches.

**Fix:** Use one skill per task. If you need to do bulk research that involves writing code as part of the answer, you probably want `run-codex-exec`, not this skill.

## AP-6: Runner without skip-existing guard

**Symptom:** Reruns redo all work, doubling cost. Manual interruption mid-batch loses partial progress.

**Cause:** Removing the `[ -s "$answer" ]` check (often during "let me clean this up" refactor). Or writing a runner from scratch and forgetting it.

**Fix:** The guard is two lines and is the cheapest correctness mechanism in the runner. Don't remove it. If you genuinely want to re-do everything, `rm -rf answers/` first — explicit.

## AP-7: Treating Monitor events as user messages

**Symptom:** The agent (or a watching human) responds to Monitor events as if the user said something. Confused threading. Wasted turns.

**Cause:** Monitor events arrive in the conversation looking like messages. They are not — they're system notifications.

**Fix:** Monitor events are signals to act, not turns to respond to. The Monitor docs are explicit about this. If you're acting on an event, act; don't say "you said X" to the user.

## AP-8: Not stopping the Monitor when the runner finishes

**Symptom:** Watcher process keeps running after the runner exits. Shows up in `pgrep`. Eventually the session ends and it's cleaned up — but during the session, it's holding resources for nothing.

**Cause:** `tail -F` doesn't exit when the file stops growing — it polls forever. The Monitor doesn't know "my runner is done" because the runner exit isn't observable to the watcher.

**Fix:** TaskStop the monitor task explicitly when `--- all jobs finished ---` lands. Or use `persistent: false` with a generous `timeout_ms` (max 1 hr) — but you lose the explicit-stop semantics.

## AP-9: Putting the placeholder where the user puts data

**Symptom:** Render script substitutes the placeholder, but the answer is bizarre because the substituted content also contains the placeholder string.

**Cause:** Default placeholder `XXXXXXXXXXXXX` happens to match an unusual input. Rare but real.

**Fix:** If your inputs might contain `X`-runs, choose a different placeholder. Pick something deliberately weird (`{{__INPUT__}}`, `<<replace-me>>`). Pass it as the 4th arg to `render-prompts.sh`.

## AP-10: Using `head` / `cat` / `echo` to "save tokens" instead of the right tool

**Symptom:** Doc/skill drift, hard to read for next session, breaks Read-tool integration.

**Cause:** Habit from a different harness. Claude Code has dedicated tools (Read, Edit, Write) that produce reviewable diffs and clean displays.

**Fix:** Use Read for reading, Edit for editing, Write for creating. Reserve Bash for shell-only operations (running scripts, git, system commands). This applies to every skill, not just this one.

## AP-11: Fan-out volume too high

**Symptom:** Codex hits 503 rate limits. Every job in the second wave fails. Whole batch needs to be rerun.

**Cause:** `JOBS` set above the provider's TPM/RPM headroom. Common when a user copies a runner from one provider to another with different limits.

**Fix:** Start at 10. Don't bump until you've measured *your* provider's tolerance. If you do bump, the audit script's FAIL count tells you when you've overshot.

## AP-12: Log file paths absolute instead of relative

**Symptom:** Skill copied to a new workdir doesn't find logs. Watcher silent. Audit empty.

**Cause:** Hardcoded paths like `/Users/foo/research/geo-research/logs/_runner.log` baked into a script. Survives copy but breaks for new locations.

**Fix:** All bundled scripts use `cd "$(dirname "$0")/.."` plus relative paths. Inherit that pattern in modifications.
