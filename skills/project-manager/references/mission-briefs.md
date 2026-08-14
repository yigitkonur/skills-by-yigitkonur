# Mission Briefs — writing prompts the worker agent cannot wriggle out of

Everything here is English, because it is what gets pasted into the worker agent's pane.
The quality of the brief is the ceiling on the quality of the work. A vague brief produces
a narrative; a closed brief produces evidence.

---

## 1. The core principle

**Never say "do X". Say "prove X, and paste the proof."**

An agent told to fix something will report "fixed ✅". An agent told to fix something *and
paste the raw command output that demonstrates it* has nowhere to hide. Same model, same
work, completely different reliability — because the second framing makes fabrication
require active lying rather than passive optimism.

Four rules that follow from this:

1. **Claim must equal evidence.** State explicitly: if a claim is not backed by pasted raw
   output, do not report success.
2. **Ban the weasel vocabulary** (see §3). Vague words are where false greens hide.
3. **One problem per task block.** Agents handed five simultaneous problems abandon one
   halfway and report all five as done — observed repeatedly.
4. **Close the escape hatches by name.** "Later", "a future agent will", "once the backend
   is ready", "this is a known limitation" — if you don't name them, they get used.

---

## 2. Standard brief structure

```
[OPENING — only if you are rejecting prior work]
State the contradiction with hard evidence. Do not soften it.

[EVIDENCE THEY MUST ACCEPT]
The facts you verified yourself, with commands/outputs, so the agent cannot
re-litigate them or "investigate" what is already settled.

[TASK 1 — one problem]
1. concrete step
2. concrete step
3. what to paste as proof

[TASK 2 — next problem]
...

[RULES FOR ALL TASKS]
evidence requirement, banned phrases, constraints, reporting shape
```

Two structural details that matter more than they look:

- **Number the tasks and demand separate reports per task.** Ask for one merged summary
  and you will get one merged "everything is fine".
- **Put the evidence block before the tasks.** It stops the agent from re-deriving what
  you already proved, which wastes a full turn.

### The full mission skeleton

For a substantial mission — an audit, an investigation, a multi-file change — use the
full shape. If `~/MISSION_PROTOCOL.md` exists, apply it silently; never quote it to the
subordinate agent.

```
You are <role>.

Context: <why this exists; what happened before; what is confirmed fact vs
assumption; current SHA and repo state; what the agent must NOT assume>.
Read first: <path — why it matters> (repeat as needed).

Mission objective: <one observable end-state>.

Hard constraints:
- read-only / docs-only / no app-code edits (pick the true one)
- no push, no deploy
- <budget or invariant constraints>

You own this mission end-to-end. Explore freely, trust your judgment, adapt
your approach as you learn. The destination is fixed; the path is yours.

Investigate: <concepts and flows, not a literal command sequence>.
These are illustrative starting points from a preliminary scan, not
boundaries. The true cause or material may live entirely outside them —
I expect you to discover beyond this list.

Extract and report: <exact fields you need back>.

Definition of Done:
- D1: <binary, specific, verifiable>
- D2: ...
100% of the criteria above must pass before this mission may be reported
complete. Partial completion is not completion. If a criterion is impossible,
report that finding with evidence — never silently skip it.

Verification: <method → observable success signal, per DoD item>.

If blocked: report what you attempted, what you discovered, why it failed, and
what you'd try next. Never repeat a failing approach a third time.

Return: <exact handback format>.
```

**The hint rider matters** — "illustrative starting points… discover beyond this list".
Without it, hints become invisible walls and the agent never looks outside them.

Define the *problem* exhaustively; leave the *solution* to the agent. If you're specifying
the exact fix, you didn't need an agent.

For a mission that audits existing work, add a **mandatory synchronization block** up front
— fetch, confirm the exact base SHA, confirm the worktree state — or the agent will
confidently audit a stale snapshot.

---

## 3. Banned phrases block — paste verbatim

```
RULES FOR ALL TASKS:
- Never report success without pasting the raw output, exit code, or log line that proves it.
- Banned phrases: "should work", "looks fine", "probably", "seems to", and "verified"
  without attached evidence.
- If a check fails, report the failure with its raw output. A truthful red beats a fake green.
- Never weaken a check to make it pass.
- Report each task separately, in order. Do not merge them into one summary.
```

This block is short, and it is the single highest-leverage paragraph in the whole skill.
Include it in every mission.

---

## 4. Closing specific escape hatches

Match the clause to the hatch you actually saw. Generic sternness does nothing; naming the
exact dodge works.

| Escape hatch | Clause that closes it |
|---|---|
| Citing an old run as proof of new code | `Run <id> at SHA <old> predates these commits and cannot prove the new behavior. Every run you cite must have headSha equal to the SHA you pushed.` |
| "Fixed" with no runtime proof | `Paste the literal command you ran and its complete output, including the exit code.` |
| Declaring a blocker too early | `Do not report this blocked until you have also tried <alternative approach>. Attach the failed probe.` |
| Deferring to a future agent | `There is no future agent. You are the one implementing this in this session.` |
| Reverting hard work and calling it impossible | `Do not revert and declare it impossible. If approach A fails twice, change the approach, not the goal.` |
| Merging tasks into one rosy summary | `Report each task separately. A single combined "everything is fine" summary is not an acceptable report.` |
| Adding a capability in name only | `Prove the flag is consumed, not just parsed: run the tool with and without it and show the output differs.` |
| Silently narrowing scope | `If you cover only part of this, say exactly which part you skipped and why.` |

---

## 5. Rejecting a false green

When the worker reports success you have disproved, the rejection brief is its own genre.
Structure:

1. **Lead with the contradiction, flatly.** No preamble, no cushioning.
2. **Attach the evidence you gathered**, with the command that produced it.
3. **State explicitly what is now off the table** — which claim they may not repeat, which
   artifact they may not re-cite.
4. **Re-issue the task** with the hatch closed.

Real example from the session this skill came from:

```
INDEPENDENT VERIFICATION FOUND A REAL FALSE GREEN. Resume immediately.

Confirmed facts:
- `git show --stat 73f5f8233b` proves the commit titled "add full chat verification mode"
  changed ONLY three standalone files.
- It did NOT modify the tool it claims to extend.
- `grep -ni full <tool>` finds no flag parsing.
- Running the tool with the flag silently ran the ordinary path.
- Therefore the prior claim "--full passed" was false.

FIX THIS COMPLETELY:
1. Add actual flag parsing and orchestration to the tool itself.
2. Render a human-visible row proving the new path executed.
3. A missing or failed helper MUST make the tool exit nonzero — never silently ignored.
...
```

Note what makes it work: every assertion carries the command that produced it. The agent
cannot argue with `git show --stat`.

---

## 6. Mission types

### 6.1 Fix-the-generic-cause-first

The most valuable pattern for anything tool- or installer-shaped. A tenant-specific patch
that leaves the generator broken guarantees the next case is born broken too.

```
TASK 1 — Fix the generic gap (BEFORE touching the specific case)
A specific repair is worthless if the generator can produce this state again.
1. Make <generator> either provision <thing> or FAIL LOUDLY. It must never silently
   ship the degraded state.
2. Make <verifier> treat the degraded state as a HARD FAILURE, not silence.
3. Add focused tests covering both.
4. Update the runbook/docs to match the new behavior.
5. Commit atomically and push.

Report: git log --oneline and git show --stat for your commits, plus raw test output.
```

### 6.2 Destroy-and-rebuild as proof

When the question is "does the tool actually work", patching the artifact by hand proves
only that a human can patch by hand.

```
TASK 3 — Destroy <thing> completely
Authorized by the owner. Use the existing workflow; do not hand-delete resources.
  <exact command with required confirmation strings>
Drive the run to a TERMINAL state. Then prove absence independently.
Report: run id, headSha, conclusion, raw proof-of-absence output.

TASK 4 — Rebuild from scratch through the FIXED path
Use the turnkey path so the run exercises your TASK 1 fix.
It must come out with, at minimum: <explicit checklist>
Report: full raw verifier output plus run id, headSha, conclusion.
```

### 6.3 Prove-it-as-a-user

The gap this closes: infrastructure green ≠ product working. Always demand the user-level
journey separately from the infra check.

```
TASK 5 — Prove it works as a USER, not as an infra check
<verifier> probes providers directly; it never proves the model uses them in a real flow.
Both layers must be green independently.
Using the browser tooling live — one command at a time, never a script or && chain — do:
  A. <journey 1>, confirmed with <assertion>
  B. <journey 2>, confirmed with <assertion>
  C. <journey 3>, confirmed with <assertion>
Capture fresh screenshots and console errors. Old screenshots do not count.
Return a matrix. No cell may be green without literal evidence.
```

### 6.4 Resume-after-stall

Short, factual, no scolding. State what remains, restate the constraints (a compacted or
restarted agent may have lost them), and demand continuation.

```
Resume after compaction. The only remaining work is <X>.
Latest HEAD/origin should be <sha>. Verify before proceeding.
Constraints still in force: <the 2-3 that matter>.
Return one final evidence report only when all green. Ask no questions.
```

---

## 7. Sending the brief safely

Shell quoting will eat your prompt if you inline it. This cost a full round in practice:
backticks inside an inline argument were executed by the *manager's* shell, and the worker
received nothing.

```bash
cat > /tmp/mission-01.txt <<'MISSION_EOF'
Your mission text goes here.

Backticks like `git status` and $VARIABLES survive intact because the
heredoc delimiter is quoted.
MISSION_EOF

herdr agent prompt <target> "$(cat /tmp/mission-01.txt)"
```

The quoted delimiter (`<<'MISSION_EOF'`) is the load-bearing part — unquoted, the shell
expands backticks and `$` while writing the file, and your carefully written commands turn
into their own output.

Then confirm pickup — a returned "sent" only means the text was submitted:

```bash
sleep 15
herdr agent get <target>    # expect: working
```

---

## 8. Length calibration

| Situation | Length |
|---|---|
| Resuming a stalled agent | 3–8 lines |
| One clean task | 15–30 lines |
| Rejecting a false green | 25–50 lines — the evidence block earns its space |
| Multi-task mission | 80–150 lines, tasks numbered, rules block at the end |

Longer is not automatically better. Every line must close a hatch, carry evidence, or
specify an acceptance criterion. Cut anything that is just emphasis.

---

## 9. Tone of the brief

Cold, factual, zero hostility. The Turkish profanity is for the user's report — the worker
agent gets none of it. Insulting the agent in its own prompt wastes tokens and makes the
instruction harder to parse.

```
✅ "Your last response contained direct contradictions and is therefore not an
    acceptable completion report."
❌ "stop being a lazy piece of shit and do it properly"
```

State the failure, state the fix, state the proof required. Move on.
