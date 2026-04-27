# Mission Protocol Integration

Every sub-agent dispatched by this skill is briefed per **`~/MISSION_PROTOCOL.md`** — the single doctrine that governs how briefs are written. This file restates the rules in this skill's context and shows where the protocol applies.

## The single doctrine

`~/MISSION_PROTOCOL.md` is the orchestrator's constitution. Read it once, internalize it. Every brief in this skill complies with its skeleton:

```
1. Context Block          — Why this mission exists, what happened before,
                            what the agent needs to know, what to read,
                            mental model after reading.
2. Mission Objective      — One observable outcome. Hard constraints only.
                            Known risks. Priority signal.
3. Research & Tool Guidance — Calibrated to the assessment (Ambiguity /
                              Familiarity / Stakes). Capabilities, not steps.
                              Ceilings with release valves.
4. Definition of Done     — Every criterion Binary, Specific, Verifiable.
                            Soft language banned. 100% required.
5. Verification           — Evidence, not declaration. Run something, show
                            something, demonstrate something.
6. Failure Protocol       — If blocked: what was tried, what was found,
                            why it failed, what to try next.
7. Handback               — Summary, Changes, Evidence, Observations.
```

Maximum **5,000 words** per brief — a ceiling, not a target.

## Where briefs are dispatched in this skill

| Phase | Sub-agent | Brief lives in |
|---|---|---|
| 3 | Coordinator (per branch, parallel) | `parallel-subagent-protocol.md` |
| 3 | Worker (per round, fresh) | `parallel-subagent-protocol.md` |
| 5 | PR-Creator (per DONE branch) | `parallel-subagent-protocol.md` |
| 7 | Evaluator (per PR) | `parallel-subagent-protocol.md` |

Phase 8 is **main-agent direct** — no sub-agent. Main agent invokes `/do-review` skill in its own context to apply the evaluator's accepted subset.

## The mindset shift

The Mission Protocol is not a checklist. It is a way of thinking:

- **Context → Gravity → Standards → Verification → Trust the path, own the destination.**
- Define what *done* looks like with razor precision, then let the agent find the path.
- Set ceilings ("up to 80 search angles if needed — you may find what you need in 15"), never floors.
- Make the mission's gravity so strong that exploration always orbits back to the objective.
- The brief is the lever. Mediocre briefs produce mediocre output. There is no exception.

## Per-brief assessment (orchestrator's internal step)

Before writing any brief, classify the mission across three dimensions:

| Dimension | Levels |
|---|---|
| Ambiguity | Low / Medium / High |
| Familiarity | Familiar / Unfamiliar / Externally Dependent |
| Stakes | Low / Medium / High |

Then identify the **heavy layers** (Framing / Discovery / Evidence / Execution / Verification) and weight the brief accordingly. Don't write the assessment into the brief — it shapes the brief's intensity.

### Defaults for this skill

| Sub-agent | Ambiguity | Familiarity | Stakes | Heavy layers |
|---|---|---|---|---|
| Coordinator | Low | Familiar (the protocol is fixed) | Medium (one branch) | Execution + Verification |
| Worker (per round) | Medium (Codex's items vary) | Unfamiliar (each round may touch new code) | Medium-High (real fixes) | Framing + Evidence + Execution + Verification |
| PR-Creator | Low (the deliverable is fixed) | Unfamiliar (must read all changes) | Medium (PR is shared) | Discovery + Evidence + Execution + Verification |
| Evaluator | Medium-High (multiple sources contradict) | Unfamiliar (PR's changes are new context) | High (decisions drive Phase 8 apply) | Framing + Evidence + Verification |

Use these defaults; calibrate up or down for the specific case.

## Hard rules — restated for this skill

### Always

- **Context first.** A subagent with deep understanding makes better decisions than one with perfect instructions. Spend 60% of the brief's word budget on context.
- **Outcomes and constraints, not steps.** Define the destination. Define non-negotiables. Leave the path open.
- **BSV Definition of Done.** Every criterion Binary, Specific, Verifiable. Soft language ("clean", "good", "reasonable", "appropriate") is banned.
- **Verification required.** Evidence of completion, not declarations. The DoD includes the verification command for each criterion.
- **Failure protocol included.** The agent must know what to do when stuck. Silent failure is the only unacceptable failure.
- **Mission gravity.** The objective is so clear that exploration always orbits back to it.
- **Ceilings, not floors.** Always upper bounds with release valves ("up to 80 search angles if needed — you may find what you need in 15"). Never minimum-N.
- **Brief includes a handback skeleton.** The agent must hand back in a known structure: Summary, Changes, Evidence, Observations.

### Never

- **Never write code in the brief.** You provide a solution, you reduce the agent to a copy-paste machine. The agent loses authorial responsibility for correctness.
- **Never prescribe the method.** "Use grep to find X, then modify Y, then run Z" caps quality at your imagination.
- **Never use soft language in the DoD.** "Code is clean" / "Performance is acceptable" / "Error handling is good" — all banned.
- **Never assume the agent knows anything.** It starts at zero. Every time. Even if you dispatched the same agent type yesterday.
- **Never pad the brief.** Every sentence earns its place. If a sentence does not add information, raise the bar, or sharpen the objective — delete it.
- **Never set floors.** No "minimum 5 commits", "minimum 1000 words", "at least 10 searches". Floors incentivize waste.

## The Ceiling Principle (in this skill's context)

Where ceilings show up in this skill's briefs:

| Where | Ceiling | Release valve |
|---|---|---|
| Worker brief | "Up to 20 rounds total per branch" | "Most branches converge in 3–6 rounds" |
| Worker brief | "Up to 5 distinct fix approaches per major item" | "If the first approach lands cleanly, you're done with that item" |
| PR-Creator brief | "Body up to 50,000 characters" | "Coming in well under is fine; comprehensive ≠ verbose" |
| PR-Creator brief | "Up to 10 explicit reviewer questions" | "3–5 sharp questions outperform 10 mediocre ones" |
| Evaluator brief | "Up to 100 distinct review items across all sources" | "Group duplicates; one decision per logical item" |
| Evaluator brief | "Up to 5 cited file reads per item" | "Stop when the decision is clear" |

Floors I deliberately do **not** set:
- Minimum number of accepted items (wrong incentive — would force false positives in)
- Minimum body length (wrong incentive — produces filler)
- Minimum rounds (Codex sometimes converges in 1; that's fine)
- Minimum approaches before reporting failure (the agent may know after the first try; trust it)

## The Five Layers — applied per sub-agent

### Coordinator
- **Framing**: light (the protocol is fixed).
- **Discovery**: light (the protocol files are referenced).
- **Evidence**: medium (read manifest, classifier output, round logs).
- **Execution**: heavy (orchestrates the loop).
- **Verification**: heavy (must show terminal state with evidence).

### Worker (per round)
- **Framing**: medium-high (each round's items may have multiple interpretations).
- **Discovery**: medium-high (must trace cited code).
- **Evidence**: heavy (extract specific code citations, behavior, contracts).
- **Execution**: heavy (apply fixes via diff-walk).
- **Verification**: heavy (validate, push, confirm round-log update).

### PR-Creator
- **Framing**: light (the deliverable is fixed: a comprehensive PR).
- **Discovery**: heavy (must read all known changes — commits, files, diffs — plus repo-local AGENTS.md).
- **Evidence**: heavy (the PR body itself is evidence-rich).
- **Execution**: medium (gh pr create + body composition via /ask-review).
- **Verification**: heavy (PR URL on fork, body length cap, explicit questions present).

### Evaluator
- **Framing**: heavy (each item across multiple sources may be a real issue, false positive, or ambiguous).
- **Discovery**: medium (cited code reads, but bounded).
- **Evidence**: heavy (every decision must cite the code, the source, the rationale).
- **Execution**: light (just produce the decision JSON — no worktree modifications).
- **Verification**: medium (count checks, schema conformance, no worktree drift).

## The orchestrator's most precise instrument

The `what_to_extract` mindset (from the protocol's Tool Intelligence section) applies here:

- **Coordinator brief** specifies: extract status transitions, round numbers, terminal_reason text, head SHA after push.
- **Worker brief** specifies: extract per-item decisions, per-item rationales, per-item commit SHAs (if accepted), validation output.
- **PR-Creator brief** specifies: extract PR number, PR URL, body length, list of explicit reviewer questions.
- **Evaluator brief** specifies: extract per-item decisions per source, deduplication map, cross-source contradictions.

Specifying `what_to_extract` is the one place where orchestrator specificity directly improves output quality without constraining approach.

## Anti-patterns when writing briefs in this skill

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| "Just fix the Codex issues." | No context. No constraints. No DoD. | Full skeleton. Include the round JSON path, the worktree path, the validation command. |
| "Try to be thorough." | Soft language. Not BSV. | "All major items have a decision (accepted / rejected / ambiguous). Decisions are evidence-cited." |
| "Use git, then run codex, then…" | Prescribes the method. Caps quality. | "Achieve a pushed branch where validation exits 0 and the round log is updated." |
| Pasting the full Codex output as the brief. | No assessment, no context, no objective. | Cite the round log path. Brief states the objective; agent reads the JSON. |
| Brief over 5,000 words. | Padding diluted the gravity. | Cut. Every sentence earns its place. |
| Including "minimum 3 commits" or similar. | Floor — incentivizes waste. | Remove. Trust the agent to find natural granularity. |
| "Probably you should…" | Soft prescription. | Either it's a constraint (state it) or it's not (omit it). |
| "Definition of Done: clean code." | Banned soft language. | "Definition of Done: validation command (`python3 -m py_compile <files>`) exits 0 with no output." |

## Quality bar — internal check before dispatch

Before sending any brief, ask:

1. Does the brief enable a zero-context agent to make good autonomous decisions?
2. Is every DoD criterion Binary / Specific / Verifiable? (Two reviewers would interpret it identically?)
3. Have I described outcomes, or have I prescribed steps?
4. Is there mission gravity — would the agent know to come back if it explored a tangent?
5. Are ceilings set with release valves? Are there any unwanted floors?
6. Is the failure protocol clear? Does the agent know what to do when stuck?
7. Is the handback structure unambiguous?

If any answer is no, revise the brief before dispatch. The brief is the lever — wrong brief = wrong work, no matter how capable the agent is.

## The two-level pattern in Phase 3

The coordinator dispatches a fresh worker per round. The coordinator's brief and the worker's brief are different:

- **Coordinator** orchestrates over time (loop counter, terminal-state decision, dispatch).
- **Worker** acts in a moment (one round, one fix-set, one push).

Both follow MISSION_PROTOCOL. The coordinator's DoD is "branch reaches terminal state with all rounds logged"; the worker's DoD is "this round's accepted items applied, validated, pushed".

The two-level structure ensures:
- Each round's worker is fresh (no stale context).
- Each round's brief gets the full protocol treatment (no degraded discipline over time).
- The coordinator owns the convergence decision, not any single worker.
- Failure of one worker doesn't compound across rounds (next round = fresh worker).

## Common sub-agent dispatch failures (skill-specific)

| Failure | Brief defect |
|---|---|
| Worker over-applies items the user would have rejected | DoD didn't require evaluator-style accepted / rejected / ambiguous decision |
| PR body has no reviewer questions | Brief didn't make "explicit questions ≥ 3" a BSV criterion |
| PR body exceeds 50k chars | Brief didn't include the wc -c verification step |
| Evaluator marks everything accepted | Brief didn't include the rejection criteria + ambiguous escape valve |
| Coordinator never marks DONE despite no major items | Brief didn't make the classifier exit-1 condition a BSV terminal trigger |

When you see one of these, fix the brief, not the agent.

## Bottom line

Every sub-agent in this skill is briefed per `~/MISSION_PROTOCOL.md`. The skeleton is fixed. The hard rules are universal. The brief is the lever. Without the protocol, parallel sub-agents drift toward mediocre. With it, they hit the ceiling.

> *Context → Gravity → Standards → Verification → Trust the path, own the destination.*
