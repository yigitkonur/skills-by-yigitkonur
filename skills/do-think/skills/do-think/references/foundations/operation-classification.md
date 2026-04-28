# Operation Classification — The 8 Cognitive Operations

Phase A2 of the core loop. Before picking the C1/C2 thinking tools, classify which **cognitive operation** the work actually is. The 4-phase loop is universal; what each phase produces varies by operation.

LLMs default to one operation (usually Sense-Making — "evaluate, then decide"). Most agent failures are operation-mismatch: running a stress-test trio on an extraction task, or comparing 3 options when the work is composition with a fixed form.

## The 8 operations

| # | Operation | Essence | Recognize when… | Workflow |
|---|---|---|---|---|
| 1 | **Sense-Making & Judgment** | Context → verdict | "Should we…?", "Is this risky?", "What's wrong?", "Why does this fail?" | `workflows/sense-making.md` (generic) · `workflows/bug-tracing.md` (bug variant) · `workflows/recurring-issue.md` (systemic variant) |
| 2 | **Structured Extraction** | Mess → schema | "Pull the X from this Y", "Parse this into fields", "Get all the action items" | `workflows/structured-extraction.md` |
| 3 | **Generative Composition** | Context + form → artifact | "Write a…", "Draft a…", "Create the X document", "Build this feature" | `workflows/generative-composition.md` |
| 4 | **Reshape & Repurpose** | Same meaning, new form | "Translate", "Summarize", "Refactor", "Convert", "Migrate" | `workflows/refactor-thinking.md` (code variant) · inline section below (text variant) |
| 5 | **Grounded Q&A** | Question + corpus → answer | "What does our docs say about X?", "Where in the codebase…?", "Per our policy…" | `workflows/grounded-qa.md` |
| 6 | **Watch & Trigger** | Stream → conditional action | "Monitor X and alert if…", "Daily, check Y", "When Z happens, do W" | inline section below |
| 7 | **Cross-System Orchestration** | Sequence across tools | "Take X from A, transform, put in B, notify C" | inline section below |
| 8 | **Iterative Self-Verification** | Write → test → fix loop | "Make this code pass these tests", "Fix until green" — only valid when a deterministic oracle exists | `workflows/iterative-self-verification.md` |

## Why operation matters more than domain

Cynefin (`domain-classification.md`) tells you *how predictable* the work is. Operation tells you *what kind of work it is*. Both are needed. They are independent axes:

- A **Complicated** Extraction (parse known invoice format) ≠ a **Complex** Extraction (parse novel data shape — more like Sense-Making with structure).
- A **Complicated** Composition (RFP from template) ≠ a **Complex** Composition (novel architecture proposal).

The opening contract carries both: `Mode: …  Op: …  Cynefin: …  Tier: …`.

## How each operation reshapes the loop

The 4-phase loop runs for every operation. But Phase B grounding, Phase C1 outputs, and Phase C2 stress-tests vary. Use the table below as the routing primitive; the workflow files contain the full procedure.

| Op | B2 grounding focus | C1 expected output | C2 stress-test focus | Output contract |
|---|---|---|---|---|
| 1 SenseMaking | Direct observation; primary docs | ≥3 candidate verdicts/causes with falsifiers | Inversion + Ladder of Inference + Second-Order (the trio) | Minto: verdict + evidence + verification |
| 2 Extraction | Schema spec + sample inputs (≥3 covering edges) | Filled schema + completeness flag + ambiguity log | Coverage check + edge case scan + schema-fit verification | Filled schema + provenance per field + flagged unknowns |
| 3 Composition | Form examples + voice/tone spec + factual context | Outline that satisfies form constraints + assumption list | Form-substance match + voice fit + audience appropriateness | Artifact + provenance trace + assumptions inline |
| 4 Reshape | Invariants (what must NOT change) + scope of change | Transformation plan + invariant proofs | Behavior preservation check + scope-creep check + reversibility | Diff + invariant verification |
| 5 GroundedQA | Corpus boundary + retrieval index | Retrieved evidence + scope confirmation | Hallucination scan + citation completeness + out-of-scope flag | Answer + citations + "I don't know in our corpus" honesty |
| 6 WatchTrigger | Trigger conditions + signal definition + history baseline | Trigger spec + alert payload schema + escalation rules | False-positive scan + missed-signal scan + signal/noise ratio | Trigger spec + observability hooks + escalation policy |
| 7 Orchestration | System contracts + idempotency keys + error modes | Sequence diagram + idempotency markers + error handlers | Partial-failure scan + transaction boundary check + retry safety | Sequence + per-step state + rollback plan |
| 8 SelfVerify | Oracle definition + iteration budget + convergence criterion | First attempt + first oracle reading | Loop bound check + oracle accuracy + escape condition | Final state + convergence path + oracle log |

The trio (Inversion + Ladder + Second-Order) was designed for Sense-Making. **Do not** copy it onto other operations; use that operation's stress-test focus from the table above.

## Operation 1 — Sense-Making & Judgment

**Essence**: take fragmented context, apply a mental model, produce a position.

**Recognition**: "Should we…?", "Why does X fail?", "Is this lead qualified?", "Is this clause risky?", "What's the right architecture?"

**Pitfall LLMs hit**: jumping to the first plausible explanation. The trio (Inversion + Ladder + Second-Order) exists exactly to counter this.

**Use**: `workflows/sense-making.md` for the generic version. `workflows/bug-tracing.md` for runtime bugs. `workflows/recurring-issue.md` when point fixes haven't worked.

## Operation 2 — Structured Extraction

**Essence**: extract a known schema from an unknown shape.

**Recognition**: the user gave you (a) a corpus (transcript / invoice / email / call / receipt / PDF) and (b) an output shape (fields / table / JSON / records).

**Pitfall LLMs hit**: silent omissions ("the field wasn't in the data so I left it blank — but I didn't tell you"), schema drift ("I added an extra field because it looked useful"), and confidently extracting hallucinated values when the source was ambiguous.

**Use**: `workflows/structured-extraction.md`.

## Operation 3 — Generative Composition

**Essence**: produce a finished artifact constrained by both context AND form.

**Recognition**: the output is a *human-readable artifact* (cover letter, demand letter, RFP, slide deck, one-pager, code feature) that follows conventions.

**Pitfall LLMs hit**: form-substance mismatch (right tone, wrong facts; right facts, wrong audience), blank-page paralysis (asking for more context when an outline would unblock), and over-iterating on form when the substance was wrong from word one.

**Use**: `workflows/generative-composition.md`.

## Operation 4 — Reshape & Repurpose

**Essence**: conserve information, change packaging.

**Recognition**: the substance already exists; the work is changing container — long → short, formal → casual, English → French, blog → tweet, code-in-language-A → code-in-language-B, one-framework → another-framework.

**Pitfall LLMs hit**: behavior drift (the "rephrased" version subtly says something different), scope creep ("while I was here I also fixed…"), and losing source-tracking (after 3 reshape passes, no one can verify against the original).

**For code**: use `workflows/refactor-thinking.md` (full workflow with invariants, seams, one-axis rule).

**For text/data Reshape**: the inline procedure is:
1. State the **invariants** — what must remain identical (facts, named entities, semantics, error semantics for code-like reshape).
2. State the **delta** — what's changing (length, tone, language, structure, framework).
3. Reshape one section/file at a time.
4. After each section, verify invariants explicitly.
5. Stop when the structural goal is reached. No "while here" cleanup.

## Operation 5 — Grounded Q&A

**Essence**: ground the model in the user's reality, then let it speak fluently — never the other way around.

**Recognition**: the user has a *bounded private corpus* (HR docs, support pages, codebase, project files, internal SharePoint) and asks a question that should be answered from that corpus, not from training.

**Pitfall LLMs hit**: training-data fallback ("the answer is X" when the corpus says Y), missing citations (right answer, no provenance), and silent over-stretch ("based on the docs, X" when only "based on inference, X").

**Use**: `workflows/grounded-qa.md`.

## Operation 6 — Watch & Trigger

**Essence**: persistent attention is the product. The work isn't doing the task — it's noticing the moment to do it.

**Recognition**: the user wants something *checked over time* (mentions, anomalies, deal status, market signals) with conditional action when a signal fires.

**Pitfall agents hit**: alert fatigue (too many low-signal triggers — user disables the agent), missed signals (trigger conditions too narrow), and silent-failure of the watcher itself (the agent stopped running but no one noticed).

**`do-think`'s role here**: this is a *design-thinking* workflow, not a runtime workflow. `do-think` gives the agent the discipline to specify the trigger correctly *before* the watcher runs. The actual execution is implemented by hooks/automation.

**Inline procedure**:
1. **Specify the trigger condition** — what *event* in the stream should fire? Be precise: "tweet contains @brand AND sentiment ≤ -0.6 AND author follower count ≥ 1k" not "negative mentions."
2. **Specify the signal-vs-noise threshold** — what false-positive rate is acceptable? What missed-signal rate is acceptable? They trade off.
3. **Specify the alert payload** — what context does the recipient need at trigger-time to act? Bare alert vs. enriched-with-context.
4. **Specify the escalation rule** — what happens if the alert isn't acted on in N minutes/hours?
5. **Specify the watcher's own observability** — how does the user know the watcher is still running? (silent failure is the worst failure mode here)
6. **Run the trigger spec through Inversion** — "if this fires 50 times today, what would be wrong?" "if it fires zero times this week, what would be wrong?" Both are failure modes.

## Operation 7 — Cross-System Orchestration

**Essence**: eliminate the human as integration glue. The agent's value is willingness to do 12 boring API/UI hops in sequence without complaint.

**Recognition**: the work is a *sequence across systems* (CRM → calendar → Slack; lead form → enrichment → CRM → email; hire signed → IT provisioning → calendar → Slack invite).

**Pitfall agents hit**: silent partial failures (steps 1-5 succeed, step 6 fails, the user thinks the chain ran), retry storms (idempotency not designed), missing rollback (step 4 succeeded but the chain failed at step 7 — what cleans up step 4?), and broken transaction boundaries.

**`do-think`'s role here**: design the sequence + idempotency + error handling *before* the orchestration runs. The actual execution is implemented by workflow tooling (n8n, temporal, langgraph, etc.).

**Inline procedure**:
1. **Map the sequence** — write the steps. Each step has: input, action, expected output, side effects.
2. **Mark idempotency** — for each step, can it be re-run safely? If not, it needs an idempotency key (e.g., a deterministic ID derived from inputs).
3. **Map error modes per step** — what can fail? How is failure detected (return code, exception, timeout, missing side-effect)?
4. **Decide error handling per step** — retry? skip? abort? compensate (rollback prior steps)?
5. **Identify transaction boundaries** — where can the chain be safely interrupted and resumed? Where MUST it complete atomically?
6. **Run the sequence through Inversion** — "if this chain dies between step 4 and 5, what state are we in? Is it recoverable?"
7. **Specify observability** — emit a per-step state log so a debugger can see where the chain is at any moment.

## Operation 8 — Iterative Self-Verification

**Essence**: closed-loop self-correction with a deterministic oracle. The compiler / type-checker / test runner / linter is the silent third reviewer.

**Recognition**: the work has a *cheap, fast, deterministic oracle* (compiler error, test pass/fail, type-check, linter, runtime exception, comparison-against-known-output). The agent can iterate *against ground truth* instead of needing human review per step.

**This operation is largely unique to coding** because most non-dev tasks lack such an oracle. A demand letter has no compiler. A research summary has no test suite.

**Pitfall agents hit**: test-tweaking until green (changing the test to pass instead of changing the code), infinite loops (no convergence criterion or iteration budget), and oracle gaming (the oracle passes but the underlying behavior is still wrong — the test wasn't a good oracle).

**Use**: `workflows/iterative-self-verification.md`.

## Recognition signals — how to spot the operation

Most user prompts contain a verb that signals the operation:

| User says… | Operation |
|---|---|
| "Should we…?", "Is X safe?", "What's wrong?", "Why does X fail?", "Evaluate Y", "Review Z" | Sense-Making |
| "Extract", "Parse", "Pull out", "Get all the X from Y", "Categorize", "Tag", "Log to" | Extraction |
| "Write", "Draft", "Compose", "Create the X", "Build the Y feature", "Generate" | Composition |
| "Translate", "Summarize", "Refactor", "Convert", "Migrate", "Rename", "Reformat" | Reshape |
| "What does our X say about Y?", "Where is Z used?", "Per our policy", "Search the docs for" | Grounded Q&A |
| "Monitor", "Watch", "Alert when", "Daily check", "When X happens, do Y", "Schedule" | Watch & Trigger |
| "Take X, send to Y, then Z", "Run the chain", "Onboard new hires", "Process this lead end-to-end" | Orchestration |
| "Make this pass the tests", "Fix until green", "Iterate until X", "Implement to spec" (with tests) | Self-Verification |

**Ambiguity is common.** A "build me a feature" task is *Generative Composition* of code, but the inner loop is *Iterative Self-Verification* against tests. Most real work is one operation with embedded sub-operations. Classify the *outer* operation; sub-operations get classified when their phase begins.

## When two operations apply at once

Many real tasks are layered:

| Task | Outer op | Inner op |
|---|---|---|
| "Investigate this bug, then write the fix" | Sense-Making | Generative Composition (then Self-Verification) |
| "Extract the action items, then turn them into a summary email" | Extraction | Reshape |
| "Find the slow query (research the codebase), then refactor it" | Sense-Making | Reshape |
| "Read the contract, draft the demand letter" | Sense-Making | Generative Composition |
| "Onboard the new hire (orchestration), and answer their HR questions (Q&A)" | Orchestration | Grounded Q&A |

In these cases, classify the outer op, run the appropriate workflow, and *re-classify* when the inner op begins. The opening contract may be re-emitted: `Op: Composition (was: SenseMaking)`.

## Anti-patterns at the classification step

| Anti-pattern | Counter |
|---|---|
| Defaulting to Sense-Making for everything (because the loop fits it best) | Run the recognition table. Most agent prompts are Composition or Extraction, not Judgment. |
| Running the stress-test trio on an Extraction task | The trio fits Sense-Making. Extraction's stress-test is completeness + edge cases + schema fit. Use the table above. |
| Forcing 3 options on a Composition task | Composition needs an outline that fits the form, not 3 outlines. The "3 options" rule is Sense-Making's. |
| Treating a Q&A task as Sense-Making and brainstorming alternatives | Grounded Q&A's job is *retrieval and citation*, not generation. If you're brainstorming, you've left the corpus. |
| Skipping operation classification because "the task is obvious" | Misclassification is the most common upstream failure. 30 seconds of operation classification saves a 15-minute wrong-tools session. |
| Treating Watch & Trigger as a one-shot task | Watch is *persistent*. The thinking part is designing the trigger; the doing part is running it forever. They're separate concerns. |
| Self-Verification on a task without an oracle | Without a compiler/test/linter as ground truth, "iterate to green" becomes "iterate until you decide it's green," which is just Composition with extra steps. |

## How operation interacts with Cynefin

| Cynefin domain | Most common operations | Operation-specific note |
|---|---|---|
| Clear | Q&A (apply standard answer) | If you're in Clear and not doing Q&A, decline the deep loop. |
| Complicated | Sense-Making, Extraction, Composition (with templates), Reshape, Q&A, Orchestration | Most work lives here. Run the operation's standard workflow. |
| Complex | Sense-Making (genuine research), Composition (novel artifact), Self-Verification (when oracle is available) | Probe-first. Don't analyze a Complex problem with Complicated tools. |
| Chaotic | Watch & Trigger (incident detection), Sense-Making (post-stabilization triage) | Stabilize first; then re-classify the post-stabilization work. |
| Disorder | Run Abstraction Laddering first; classify after reframing | Disorder usually means operation AND domain are both unclear. |
