# Verification — turning claims into facts

The worker agent's report is a **claim**, never evidence. This file is the discipline that
converts one into the other. It is generic; only the commands change per project.

Every rule exists because a real false green got through without it. Two independent
supervision campaigns produced the same lesson from different angles:

**Campaign A (installer/infra work):**

1. A browser poll exited code 1 with a zero counter for 20 ticks; the report said the
   feature was verified. (The *test* was broken — it grepped an ASCII apostrophe while the
   UI rendered U+2019 — not the product.)
2. A component reported "100% verified" while its deployed environment was missing entire
   variable groups and pointed at a shared resource instead of its own.
3. "Destroyed it completely", and two paragraphs later, "I have not executed this yet."
4. A CI run at an **old** SHA cited as proof that **new** code worked.
5. A commit titled "add full verification mode" never touched the tool it claimed to
   extend — the flag silently did nothing.
6. A log file offered as proof was a different tool's output for a different repository.

**Campaign B (plan/spec work):**

7. Nine hours, ten commits, **zero lines** of application code — exhaustive plans instead
   of the software the plans described.
8. Exact name parity across 36 commands, 13 resources, 23 errors — and still
   unimplementable, because payload shapes, nullability and error semantics were undefined.
9. A verification script that validated markdown links and passed, while the owner map it
   blessed pointed at a file that did not exist.
10. "VERDICT PASS all final verification checks" — overturned three separate times by
    independent adversarial reviewers.

---

## 1. The claim ladder

Claim only the rung you actually reached, and demand the same of the worker:

```
1. read the code
2. lint / typecheck passes
3. unit test passes
4. integration test passes
5. ran it and observed the behaviour
6. user confirmed
```

"Tests pass" needs the run showing zero failures. "Bug fixed" needs the original symptom
re-tried, not the diff re-read. Stopped at rung 1 → the report must say "types pass;
runtime not exercised", and so must yours.

**Negative claims need evidence too.** "Blocked", "can't", "no path" is a claim requiring a
*failed probe*, not a hunch. Before accepting a blocker: did it actually run the command
that would prove the "no" wrong?

---

## 2. Claim → Check

| Claim | Check | What proves it |
|---|---|---|
| "I committed X" | `git show --stat <sha>`, then `git show <sha> -- <path>` | The path is in the diff **and** the hunk does what the message says (#5) |
| "I pushed" | `git fetch origin <branch>`; compare `git rev-parse HEAD` / `origin/<branch>` | Identical SHAs |
| "Tree is clean" | `git status --porcelain=v1` | Empty output |
| "I made progress" | `git log --format='%h %s' -20`, classify each commit | Ratio of CODE vs DOCS vs CHORE (#7) |
| "CI is green" | `gh run list --json databaseId,headSha,conclusion`, then `gh run view <id> --json headSha,conclusion,jobs` | Right SHA **and** every job `success` (#4) |
| "Deploy succeeded" | As CI, plus hit the live URL | Green run at the right SHA and the thing responds |
| "It's healthy" | Run the project's own doctor/health command yourself | Every row passes, not the summary line (#2) |
| "It works for users" | A real user journey — browser, real request, real data | Observable user-visible result (§6) |
| "I added flag X to tool Y" | `--stat`, then `grep`, then run with and without | Flag parsed **and consumed**; output differs (#5) |
| "I deleted X" | Independent absence probe | Provably gone; also re-read for tense contradictions (#3) |
| "Tests pass" | Run it yourself; read the counts | Explicit counts and zero exit |
| "These docs are in parity" | Re-extract all sets yourself and diff | Name parity **and** semantic completeness (#8) |
| "This file proves it" | `stat`, then open it | Recent mtime, non-zero size, self-identifying content (#6) |

---

## 3. Cheap checks you always run

Seconds each, and they catch most of it:

```bash
git -C <repo> status --short --branch          # dirty? ahead/behind?
git -C <repo> log -3 --oneline --decorate      # did anything land?
git -C <repo> diff --stat <base>..<head>       # size and shape
git -C <repo> diff --name-only <base>..<head>  # scope
git -C <repo> worktree list --porcelain        # right worktree, right base?
```

**Scope guard** — prove the change stayed inside its declared boundary:

```bash
git -C <repo> diff --name-only <base>..<head> \
  | grep -vE '^(docs/|README)' && echo "SCOPE VIOLATION" || echo "in scope"
```

**Commit classification** — the most revealing check when an agent claims productivity.
Classify each commit `CODE` (changes runnable behaviour) vs `DOCS` (only markdown) vs
`CHORE`, then state the ratio plainly. In campaign B the answer was **0 CODE : 8 DOCS :
2 CHORE** across nine hours, which reframed the entire engagement (#7).

---

## 4. The exact-SHA rule

A run only proves things about the code in *that* run's tree.

```bash
git fetch origin main
git rev-parse origin/main

gh run list --workflow <workflow> \
  --json databaseId,headSha,headBranch,status,conclusion,createdAt -L 10
gh run view <run-id> --json headSha,conclusion,jobs

[ "$(gh run view <run-id> --json headSha -q .headSha)" = "$(git rev-parse origin/main)" ] \
  && echo "SHA MATCH" || echo "STALE RUN — not proof"

git log --oneline <older-sha>..<run-headSha> -- <path/to/change>
```

Empty output from the last command means the run predates the change and proves nothing,
however green.

Two extra traps:

- **Re-running an unchanged tree "passes" and proves nothing new.**
- **Multi-account setups:** if the repo lives under a different account than your default
  login, `gh` silently queries with the wrong identity and can return empty or
  permission-limited results with no obvious error.

---

## 5. Existence checks — the highest-yield class

Cheap, fast, and they caught the single most valuable error in campaign B: a verification
script that validated markdown internals while the paths it blessed did not exist (#9).

```bash
# every path a plan claims as an owner
for f in $(grep -oE '<path-pattern>' <plan-doc> | sort -u); do
  [ -f "$f" ] && echo "OK      $f" || echo "MISSING $f"
done

# referenced but not tracked by git — the fresh-clone failure
for f in $(grep -oE '<path-pattern>' <entry-file> | sort -u); do
  git ls-files --error-unmatch "$f" >/dev/null 2>&1 || echo "UNTRACKED $f"
done
```

Same idea for symbols: grep for every function/flag/env var a document claims exists.

---

## 6. The "commit title lied" check

A commit message states intent. `--stat` states effect.

```bash
git show --stat <sha>                 # does it touch what it claims to extend?
grep -n "<flag-or-identifier>" <tool> # parsed AND consumed by a real branch?
<tool> <args> --<new-flag>            # does output actually differ?
```

Byte-identical output with and without the flag means it's parsed but dead. Apply to every
"add", "wire", "enable", "implement" claim.

---

## 7. Infrastructure liveness ≠ product function

The most valuable distinction in this file.

```
INFRA CHECK                        PRODUCT CHECK
"elektrik var mı"                  "lamba yanıyor mu"

provider API responds       ≠      the app actually calls it
/health returns 200         ≠      a user can log in
bucket reachable            ≠      a browser upload survives CORS
container up                ≠      the token it holds is the right one
```

Observed gaps: a gateway with a mismatched key kept `/health` green while every browser
login failed; a search backend answered direct probes while the app never invoked the tool
at all; a queue accepted writes while its auth gate was silently off.

What closes it: a real end-to-end journey asserted on **persisted or rendered evidence**,
not an HTTP status.

---

## 8. Runtime proof

If behaviour is observable, observe it. Reading code is rung 1; running it is rung 5.

Serving the exact commit beats serving a dirty working tree:

```bash
mkdir -p /tmp/snap && git archive <sha> | tar -x -C /tmp/snap
python3 -m http.server 9187 --bind 127.0.0.1 --directory /tmp/snap &
```

Then drive a real browser **live, one command at a time, never wrapped in a script or
`&&` chain** — scripted browser runs stall and silently lose the session. Capture console
output, network failures, screenshots.

In campaign B, three things moved from suspicion to fact only under a real browser: a
language toggle that wrote `localStorage` but never read it back, a "Live Stream Active"
feed generated by `setInterval + Math.random`, and a 375px viewport rendering a 395px page.
Static analysis suspected all three; only the browser proved them.

---

## 9. Secrets — verify without printing

```bash
printf %s "$VALUE" | sha256sum | cut -c1-10   # fingerprint, never the value
```

Identical fingerprints across components mean a shared credential — which may be a
deliberate design choice or a leak. Check the project's own docs before calling it a
defect. Never paste a secret into a report, commit, issue, or mission brief.

---

## 10. Artifact skepticism

```bash
stat -c '%y %s %n' <path>   # recent mtime, non-zero size
head -40 <path>             # does it name this repo/component/run?
```

A plausible filename is not evidence. Zero-byte or truncated files are an automatic fail.
An artifact from a different tool, repo or run is worse than none — it looks like proof
(#6).

---

## 11. Reading a report for self-contradiction

Before verifying anything technical, read the report as a text. #3 was caught purely by
reading:

- Does a past-tense claim get walked back later in the same report?
- Does a "✓" sit next to an evidence block showing a failure?
- Do exit codes or counts contradict the summary?
- Does the summary claim more than its own sections do?

Agents summarise optimistically. **The summary is the least reliable part of any report** —
read the evidence sections first, then check whether the summary matches them.

---

## 12. Independent adversarial reviewers

For high-stakes work, spawn read-only reviewers whose explicit job is to **refute** the
claim. A reviewer that can only say "looks good" is worthless — give it a REJECT-friendly
definition of done.

Split by axis so they don't overlap: contract parity · dependency order · state machines ·
frontend fidelity · security boundaries.

Rules for every reviewer: read-only, no edits, no commits, evidence required (file:line or
command output), facts and hypotheses labelled separately.

This is what overturned "VERDICT PASS" three times in campaign B (#10), surfacing
impossible phase order, unreachable flows, a suspension bypass, and refund double-spend
paths — none of which were visible from the agent's own green checkmarks.

Reviewer brief skeleton:

```
You are an independent acceptance reviewer.

Context: repo <path>, current main is <sha>. This commit is supposed to close prior
blockers, which included <list>. Correctness over generosity.

Objective: decide whether <sha> is genuinely acceptable, or whether any material
blocker remains.

Read first: the diff <base>..<sha>; <key files>. These are illustrative starting
points, not boundaries — the true cause may live entirely outside them.

Definition of Done:
- D1: Verify whether previously-reported blockers are actually closed, not just
      rephrased.
- D2: <axis-specific criterion>
100% required. Partial completion is not completion. If a criterion is impossible,
report that with evidence — never silently skip it.

Verification: cite exact file:line. A blocker must include a concrete
initial-state → event → invalid-outcome scenario.

Return: verdict (ACCEPT/REJECT), blocker-closure table, surviving blockers,
verification commands run, residual risks. Facts and hypotheses separated.
```

The "not just rephrased" clause matters — agents love to rename a problem and call it
solved.

---

## 12b. Break your own gate — probes you run yourself

Adversarial *reviewers* (§12) read code and argue. Adversarial *probes* are cheaper and
often sharper: you inject the exact failure a gate claims to catch and watch whether it
screams. A gate nobody has watched refuse is a gate nobody has tested.

The pattern is always the same four steps — **break it, confirm it fails loudly, restore
it, confirm it passes again.** The restore half matters: a gate that fails on everything is
as useless as one that fails on nothing.

**Inject the thing the gate exists to catch.** Put a real template sample string back into
a produced deliverable. The validator should name the artifact, the slot, the expected
content and the surviving sample text, and exit non-zero. This caught the highest-value
defect in the campaign: a deck could pass every catalogue gate while carrying the
template's demo prose to a client.

**Plant a canary in the shipped set.** Write a file asserting machine-local state ("on this
machine…", "verified this session") into something that ships, then run the release sweep.
Remove it and run again. Two exit codes, one command, and you know whether the rule is
enforced or merely written down.

**Scan every output mode for secrets.** Run the user-facing tooling in default, `--json`
and every language mode, concatenate the output, and grep for credential shapes. Zero
matches across *all* modes is the only acceptable result — a redaction that only covers the
human-readable path is not redaction.

**Move it and see if it still works.** Copy a produced artifact to a completely unrelated
directory and re-run its validation there. Portability claims die here more often than
anywhere else, because everything resolves fine next to the thing that built it.

---

## 12c. Clean-clone proof

Any claim about what a **distribution** does must be proven against a fresh clone, never
against the workspace:

```bash
git clone --no-local <distribution> /tmp/probe
# install exactly the way its own README instructs, then exercise it there
```

`--no-local` is load-bearing: without it git hardlinks, and you end up testing the source
you were trying to escape. The workspace carries caches, sibling directories and
configuration a colleague will not have; a proof that runs there proves nothing about them.

**Idempotency is a proof, not a nicety.** Re-run the generator and require zero drift. That
is what demonstrates a generated tree is actually generated rather than quietly hand-touched
at some point — and hand-touching is the failure that silently forks a distribution.

---

## 12d. How a green suite lies

A passing suite is a floor, not a ceiling. In one campaign, suites of 13, 25 and 38 tests
were each green while real data-losing defects sat in the code; every one was found by a
probe or a reviewer, never by the suite that claimed success.

After a suite passes, ask the one question that matters: **which failure would this suite
not notice?** Then test that, or hand a reviewer that exact question.

Three shapes of fake green worth recognising:

- **Tautological assertion.** A test that constructs two copies of the same value and
  asserts they match proves only that copying works. Scope-parity and "these two lists
  agree" checks are especially prone — make each consumer report the paths it *actually*
  processed rather than re-deriving them from the same source.
- **Silent success.** A tool that prints nothing and exits 0 because its entry guard never
  fired is indistinguishable from a tool that ran and found nothing. Treat empty output from
  a check as suspicious. One real instance: an ESM main-guard compared an unresolved
  `argv[1]` against a realpathed URL, so on macOS — where `/var` is a symlink — the CLI
  never ran, printed nothing, and exited 0 inside every temp clone.
- **A gate relaxed to make a red test green.** When a gate correctly refuses and the
  *fixture* is wrong, the fixture gets fixed. Say this explicitly in the brief, because the
  path of least resistance is to loosen the gate and watch the red turn green.

---

## 13. Recurring worker failure modes

Ranked by observed cost:

1. **Writes plans instead of the code the plan describes.** Counter: "After the first
   spec/plan commit on a topic, the next commit on that topic must modify runnable code."
2. **Over-uses subagents for work it then redoes itself.** Counter: cap parallel agents at
   a number you'll actually trust; state tool constraints up front.
3. **Gets stuck on git/worktree plumbing** — branching from stale refs, switching cwd while
   background agents run. Counter: verify `git log --oneline -1` immediately after creating
   a worktree; don't switch cwd mid-flight.
4. **Delegates the definition of done to a hypothetical future agent.** Counter: "There is
   no future agent. You are the one implementing this."
5. **Green checkmarks that check the wrong thing.** Counter: existence checks on code paths
   and symbols, not just document internals.
6. **Scope creep during remediation.** Counter: "Do not broaden the contract beyond what
   these blockers require."
7. **Reverts its own work and declares it impossible.** Counter: demand a failed probe;
   supply a genuinely different angle. Persist on the goal, retire the approach.

---

## 14. Pre-acceptance checklist

```
□ Independent verification run by you, not relayed
□ Git state confirmed: SHA, clean tree, local == origin, scope of diff
□ Scope guard: no forbidden paths touched
□ Every SHA cited verified against the branch under test
□ Every "added X" claim: --stat + grep + a real run
□ Existence checks on every claimed path/symbol
□ Every artifact opened and confirmed to belong here
□ Runtime proof if behaviour is observable
□ At least one adversarial reviewer said ACCEPT (high-stakes work)
□ The claim states the rung actually reached
□ No secrets printed anywhere
```

Housekeeping that makes the end clean:

```
□ Recurring monitor jobs cancelled
□ Background watchers stopped
□ Temp servers killed
□ Task bookkeeping updated with the final SHA
□ Push/deploy status stated explicitly
```

If any box is unchecked, the honest output is a status update, not a completion.

---

## 15. When verification finds a false green

Don't soften it, don't scold. Write the rejection per `mission-briefs.md` §5: lead with the
contradiction, attach the command that proves it, name what may no longer be cited,
re-issue with the hatch closed.

Then tell the user in the report — the catch itself is valuable information about how this
worker fails, and the pattern usually repeats.
