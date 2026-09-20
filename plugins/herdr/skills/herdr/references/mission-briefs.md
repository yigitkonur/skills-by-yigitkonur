# Standalone mission briefs

Read before handing work to an agent without the controller's conversation.
The mission must carry enough context to decide what to do, what not to change,
what proves completion and where an unfinished result goes. Prefer a static
brief file submitted through the observation reference's safe quoting pattern.

## Decide the boundary first

Give one agent an independently verifiable outcome. Split discovery from
implementation when an unresolved contract would otherwise force a guess.
Independent ready work belongs in the same wave; shared mutable contracts need
one owner. A review can run alongside unrelated writing, but its own candidate
must stay frozen. The controller owns topology, resource grants and integration.

Distinguish confirmed user decisions, observations and hypotheses. Preserve
accepted exclusions and rejected ideas so they do not return as "improvements."
A research result can recommend a choice without authorizing its implementation.
If the exact task is already fully specified, delegate execution explicitly;
otherwise define the problem and let the agent investigate the solution.

## Brief contents

Include these fields in the order that makes the specific task easiest to act on:

- **Relevant skills/tools:** only those needed for this mission and when to use
  each. State the requested model/effort and tool constraints when applicable.
- **Context and objective:** why the work matters, the accepted user outcome,
  existing behavior, verified baseline and what is already done. Give exact
  issue/PR links and source pointers; label unverified assumptions.
- **Ownership:** checkout, branch/base, allowed edits, exclusions, contract
  producer and dependent consumers. Name any external surface the agent may
  mutate; use existing authority rather than inventing an approval gate.
- **Investigation space:** the unresolved question and extraction fields needed
  for the next decision. Starting points are guidance, not permission to ignore
  evidence elsewhere. Keep discovery within the authorized surface.
- **Completion evidence:** observable acceptance criteria, focused check
  commands or evidence methods, actual resource grants and the requested PR
  state. Describe what each check proves and what it cannot establish.
- **Failure path:** exact blocker reporting, bounded recovery and escalation to
  the controller. Two equivalent infrastructure failures require a changed
  approach or handback before a third identical retry. A product failure calls
  for diagnosis, not a success claim with a caveat.
- **Handback:** outcome; files/artifacts; base/head and PR; commands/results;
  accepted-criteria coverage; decisions/assumptions; remaining gaps with next
  owner/action. A report is a claim to verify against the candidate.

Use the user's language for deliverables and requested language for prompts.
Keep long specs in linked files, but include the decisions essential to
execution in the brief. Do not make a worker reconstruct the assignment from a
chat transcript or an unexplained collection of issue IDs.

## Make the finish line honest

For implementation, a draft PR is an intermediate artifact unless draft-only
work was explicitly assigned. Say who performs pending tests/review and how
resource access is obtained. Requiring red-before-code while withholding all
compiler access is an impossible brief; resolve that before dispatch.

For research, completion means bounded findings with evidence, confidence and
unresolved questions; it does not close an implementation issue. For review,
name the exact candidate and user-relevant questions; separate material defects
from optional polish. After a correction, narrow the next brief to the changed
candidate and unresolved findings rather than replaying a whole audit.

A useful brief is complete, not padded. A continuation usually needs current
SHA, surviving gaps and constraints; a new subsystem needs more context. Check
that a cold agent can identify done, blocked and outside scope without guessing.

## Confirm pickup and preserve continuity

A sent message may be queued behind the active turn. For important corrections,
record acknowledgment or observed compliance before relying on the change.
After compaction, re-anchor completed work and current evidence so the agent
does not restart it. Keep the same task/attempt history and exact conversation
ID where recovery supports it; failed child workflows return to the controller
for reassignment instead of spawning duplicate writers.

Worker sessions stay interactive and visible under the main skill. Report
files preserve the final evidence while the user retains the ability to follow
progress and intervene in the pane.
