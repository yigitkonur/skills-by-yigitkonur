# Scenarios and evidence

Use this reference when authoring a case, executing it, reviewing its artifacts,
or deciding whether a discovered behavior belongs to the accepted scope.

## Establish the oracle before execution

Import existing approved scenarios into assigned case/spec paths without adding
behavioral scope. Otherwise map features and subfeatures to real user goals,
then write cases with the [scenario template](../assets/templates/scenario.md).
Each expectation must cite one source:

- Explicit user requirement, with a stable reference to the decision.
- Product contract, such as a supplied specification or documented interface.
- Approved prior scenario, preserving its revision and intent.
- Explicitly declared general invariant, such as not exposing another user's
  private record; label the invariant and its applicability.

Code, current UI text, and successful execution can locate surfaces but cannot
silently become the expected behavior. If a material expectation lacks an oracle,
record `SPEC_INVALID`/`SOURCE_SELECTION_REQUIRED` and route through the campaign's
interaction mode. In autonomous mode, continue independent cases without guessing.

Preserve the source's meaning and comparison strength. For example, "stderr
contains the required message" does not authorize requiring exactly one trailing
newline; JSON content requirements do not imply key order. Record normalization
only when the contract supports it. Cite the actual readable source and section,
not an imagined copy inside a task handoff. The plan auditor checks this semantic
traceability; schema validation cannot establish that an expectation is justified.

## Make one case executable

Write Given/When/Then steps with stable step and expectation IDs. Specify actor,
fixture, preconditions, user action, observable result, and reset. Use the actual
interface: browser flows, CLI invocation, MCP exchanges, or a native app driver.
Supplementary developer checks do not replace the user journey.

For each expectation, the manifest records statement, source, priority,
`review_count`, observable description, and evidence requirements. Declare
`review_count: 2` for critical, subjective, financial, authentication, and
integrity expectations before execution. The planner must preserve it; lowering
it after an inconvenient result changes the oracle and needs a new specification.

The [how-to-run template](../assets/templates/how-to-run.md) must tell a different
executor where to begin, which tool and exact target to use, how to reset, what
to capture at each step, and when to stop. Keep tool details verified against
the available interface; avoid invented commands or credentials.

Done: an executor can perform the case without asking its author what PASS means.

## Capture an auditable observation

Executor reports contain one observation or explicit unavailable reason for every
expectation. Capture only what actually happened; preserve failure output and
intermediate state needed to explain the outcome.

| Interface | Useful evidence |
|---|---|
| Web | Screenshot of claimed state; relevant DOM/accessibility text; requests/responses or console logs when the expectation needs them |
| CLI | Exact argv/cwd, exit status, stdout/stderr, and resulting files/state |
| MCP | Transport and server identity, initialization/capability result, tool request and structured response, relevant server logs |
| Native mobile | App/build and device identity, driver actions, screenshots/accessibility output, relevant app logs |

Bind each artifact to expectation IDs, step, target, capture time/tool where
available, and a campaign-relative `evidences/` path. The submission computes
content hashes. Claim a screenshot only if the image exists; a screenshot path
or a prose description is not its visual content. Preserve original useful JSON
structure and error text. Redact secrets before sealing, record any relevant
redaction limitation, and never copy `.env` or unrelated project content.

List the precise `requirement_ids` fulfilled by each artifact. Two required JSON
captures are not satisfied merely because one JSON file exists. An artifact may
explicitly support multiple requirements only when its actual contents establish
each one; the verifier inspects that mapping. Missing requirements need named gaps.

If capture failed, include a gap with its `requirement_id` and observed reason.
A missing claimed artifact is rejected. An honest gap is admissible evidence
of incomplete capture, not of the expected behavior. Use `PARTIAL`/`NOT_RUN` when
appropriate. A tool's exit 0 or the executor's prose cannot award PASS.

## Inspect, do not reenact

Verifiers receive the frozen case/spec, assigned target/round, execution record,
and captured artifacts. Open the actual images, JSON, and logs using available
read-only viewers. For each expectation, write expected, observed, verdict,
evidence IDs, and a precise reason. Record every inspected artifact's hash,
inspection method, and concrete observation. Evidence IDs alone do not prove
inspection.

A verifier never reruns a test, clicks through the application, repairs a fixture,
or captures new application evidence. Request a fresh executor through the
orchestrator when evidence is incomplete or a new experiment is needed.

The second verifier is blind to the first verifier's report, verdict, conclusions,
and discussion. Both may read the same original case and execution artifacts.
Independent review requires distinct actual contexts, not two prompts in one.
Conflicting required reviews produce `INCONCLUSIVE`; averaging or a majority
does not manufacture PASS. The controller chooses recovery, retaining both reviews.

## Side findings and expectation boundaries

An unrelated defect observed during a passing case is a separate `SIDE_FINDING`;
it does not change that case's frozen expectations or overwrite its supported
result. Capture enough evidence to locate it and link the original round.

In interactive mode, material expansion requires the user's scope decision. In
autonomous mode, a material related finding gets an independent confirmation
scenario before diagnosis/fix work proceeds. Out-of-scope findings remain visible
in coverage/reporting with their reason. Never rename a known unresolved defect
as a side finding to reset its attempt lineage.

The controller records the actual decision through the CLI:

```bash
node "$AT_CLI" finding decide --campaign "$CAMPAIGN" --finding-id "$FINDING_ID" \
  --scope in_scope --reason "$REASON" --source "$DECISION_SOURCE"
```

Use `out_of_scope` for a sourced exclusion. `source` identifies the actual user
decision or applicable autonomous-scope policy; an unanswered question is not a
decision. The command records disposition and provenance, without awarding PASS.
For an admitted side finding, create a `scenario-author` task with `finding_id`
set to its stable ID, then plan, execute, and independently verify that confirmation
case before opening a repair ticket. Do not hand-edit a finding's canonical YAML.
