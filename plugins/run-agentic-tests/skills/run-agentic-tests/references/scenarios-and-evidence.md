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
interface: browser flows (`ego-browser`), CLI invocation, MCP exchanges (`test-by-mcpc-cli`),
or native mobile (`test-by-maestro`). Supplementary developer checks do not replace
the user journey.

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

## Guardrails for conditional test loops ("Test this, if not that, then do this")

When a scenario contains branching or fallback user journeys:

1. **Distinguish Execution Faults from Clean Falsity**:
   An unhandled exception, network timeout, HTTP 500 status, or browser crash is an
   **execution fault**, NOT an assertion evaluating to `false`. Treating a crash as a
   negative condition and branching into fallback logic silently conceals critical application
   regressions. If an action throws or times out unexpectedly, fail immediately.
2. **Explicit Condition Waits over Instantaneous Checks**:
   Modern SPAs render asynchronously. Instantaneous checks (`if (element.isVisible())`)
   fail prematurely during client-side hydration or animation. Require bounded condition
   waits (`waitForSelector`, `waitForFunction`) with an explicit timeout before concluding
   an element is absent.
3. **Atomic State Isolation & Teardown**:
   If Branch A partially executes (fills inputs, modifies local storage, toggles state)
   before failing, Branch B runs in a dirty DOM state. Enforce a state reset (page reload
   or fixture reset) before executing a fallback branch.
4. **Bounded Fallback Depth (No Circular Loops)**:
   Limit fallback depth to at most 1 (`fallback_depth <= 1`). Never permit circular
   "if A fails try B; if B fails try A" loops.
5. **Session Expiration Guard**:
   Check for HTTP 401/403 responses or URL redirection to a login screen before evaluating
   branch conditions to prevent misclassifying auth expiration as UI absence.
6. **Non-Idempotent Side Effects & Transactional Integrity**:
   If Branch A mutates application state (creates an account, charges a payment method, submits a form)
   before encountering a failure, taking Branch B without rollback causes duplicate mutations,
   409 Conflict errors, or financial discrepancies. Any branch with side effects must be strictly
   idempotent or execute an explicit transactional cleanup/rollback step before Branch B starts.
7. **Observable Fallback Recording (No Silent Concealment)**:
   Taking a fallback branch must never result in an invisible `PASS` that conceals primary flow
   regressions. The execution observation must record `FALLBACK_TAKEN` with evidence detailing why
   Branch A was bypassed.
8. **Branch Oracle & Verification Clarity**:
   The executor must explicitly record branch decision points, entry conditions, and selected paths
   so that independent blind verifiers know exactly which contract was evaluated.

## Capture an auditable observation

Executor reports contain one observation or explicit unavailable reason for every
expectation. Capture only what actually happened; preserve failure output and
intermediate state needed to explain the outcome.

| Interface | Runner tool | Useful evidence |
|---|---|---|
| Web | `ego-browser` | Screenshot of claimed state (retrieved via SCP if remote); relevant DOM/accessibility text (`page.snapshot()`); requests/responses or console logs |
| Mobile | `test-by-maestro` | Flow exit code, JUnit XML (`--format JUNIT`), 10-tool MCP server output (`inspect_screen` hierarchy JSON, bounds `[x,y,w,h]`, `take_screenshot` PNG), step screenshots, app logs |
| MCP | `test-by-mcpc-cli` | Session receipt, `tools-list`/`tools-call` output (`--json`), `skills-list`/`skills-get` manifests, `resources-directory-read`, exit codes (1 vs 2), server logs |
| CLI | Native process | Exact argv/cwd, exit status, stdout/stderr, resulting files/state |

Bind each artifact to expectation IDs, step, target, capture time/tool where
available, and a campaign-relative `evidences/` path. The submission computes
content hashes. Claim a screenshot only if the image exists; a screenshot path
or a prose description is not its visual content. Preserve original useful JSON
structure and error text. Redact secrets before sealing, record any relevant
redaction limitation, and never copy `.env` or unrelated project content.

### Remote artifact retrieval (SCP)
When `ego-browser` or `test-by-maestro` runs on a remote host (e.g., via SSH tunnel to a test server),
screenshots, test outputs, and downloaded files are written to the remote filesystem.
The executor must retrieve all remote artifacts to the local campaign's `evidences/`
directory via hardened `scp` before submitting:

```bash
# Enforce absolute remote path and safe quoting (survives OpenSSH 9.0+ SFTP defaults and spaces)
scp -p "$REMOTE_HOST:$ABSOLUTE_REMOTE_PATH" "$LOCAL_EVIDENCES_DIR/$ARTIFACT_NAME"

# If the remote environment lacks SFTP subsystem support, force legacy SCP protocol:
scp -O -p "$REMOTE_HOST:$ABSOLUTE_REMOTE_PATH" "$LOCAL_EVIDENCES_DIR/$ARTIFACT_NAME"
```

Rules for remote retrieval:
- **Always use absolute remote paths**: OpenSSH 9.0+ resolves relative paths against the remote user's home directory.
- **Escape spaces and special characters**: Quote remote paths to prevent remote shell splitting.
- **Honor SSH config**: If `$REMOTE_HOST` refers to an `~/.ssh/config` host alias, do not add conflicting `-P` port flags.

A file that remains on the remote host cannot be verified locally and will fail with `MISSING_ARTIFACT`.

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
and discussion. When `review_count: 2` is declared, dispatch Verifier A and
Verifier B **concurrently in parallel**. Both may read the same original case and execution
artifacts. Conflicting required reviews produce `INCONCLUSIVE`; averaging or a majority
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
