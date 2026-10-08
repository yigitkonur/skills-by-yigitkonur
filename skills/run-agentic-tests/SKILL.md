---
name: run-agentic-tests
description: "Use if orchestrating multi-agent E2E campaigns with independent evidence review, isolated runtimes, and defect fix/retest loops."
---

# Run Agentic Tests

Coordinate a real E2E campaign from scenarios to independently inspected evidence,
scoped repairs, integrated-target retests, and an inspectable HTML report. This skill
provides the operational harness for multi-agent testing across web, mobile, MCP, and CLI,
integrating directly with specialized test runners.

## Model selection & reasoning configuration per provider

Models are configured strictly per provider to balance execution speed, assertion accuracy, and token economics. **Core architectural rule:** Anthropic splits models by family (no reasoning level needed), while Codex and Gemini split capabilities primarily by reasoning effort.

| Provider | Task category | Model | Reasoning effort | Operational rule |
|---|---|---|---|---|
| **Anthropic** | All operations (execution, verification, diagnosis) | `sonnet-5.5` or `haiku-5.5` (use newer version if released) | *None* | Anthropic sorts models by family; reasoning level is omitted. Never use heavy flagship family models like Opus for automated loops. |
| **Codex** | Simple ops (routine execution, CLI commands, basic steps) | `gpt-6-luna` | `xhigh` | `luna` is a compact model; `xhigh` reasoning effort keeps tool calls and deterministic steps rock-solid. |
| **Codex** | Evidence checks (verifiers, assertion checks, artifact analysis) | `gpt-6.1-sol` | `medium` | Balanced reasoning ensures rigorous evaluation of screenshots, logs, and state evidence without timeout delays. |
| **Gemini** | Simple ops (routine execution, navigation, basic steps) | `gemini-3.8-flash` | `medium` | High throughput, fast response times for multi-step browser/CLI steps. |
| **Gemini** | Everything else (evidence checks, verification, diagnosis, planning) | `gemini-3.8-flash` | `high` | Increased reasoning depth for independent verification, root-cause diagnosis, and scenario authoring. |

## Tool dependencies & specialized sibling skills

This skill orchestrates campaigns; specialized domain testing is executed through dedicated peer skills. The system must verify prerequisites during Wave 0 and **fail fast** if the required runner is missing:

| Domain | Designated runner skill | Dependency & repository | Fail-fast requirement |
|---|---|---|---|
| **Web** | `ego-browser` | [citrolabs/ego-lite](https://github.com/citrolabs/ego-lite) · [ego-browser skill](https://github.com/citrolabs/ego-lite/blob/main/skills/ego-browser/SKILL.md) | Refuse to start if `ego-browser` skill/CLI is missing. If running remotely over SSH, remote screenshots **must be retrieved via SCP** to local `evidences/`. |
| **Mobile** | `test-by-maestro` | [test-by-maestro](https://github.com/yigitkonur/skills-by-yigitkonur/tree/main/skills/test-by-maestro) · [Maestro CLI](https://maestro.dev) | Requires Maestro CLI (`maestro --version` ≥ 2.11.0), Xcode for iOS Simulator, or ADB for Android. |
| **MCP** | `test-by-mcpc-cli` | [test-by-mcpc-cli](https://github.com/yigitkonur/skills-by-yigitkonur/tree/main/skills/test-by-mcpc-cli) · [@apify/mcpc](https://github.com/apify/mcpc) | Requires `mcpc` 0.7.x session-first CLI (`mcpc connect <url> @session`). Pre-0.7.0 syntax is obsolete. |
| **CLI** | Native process runner | Node.js ≥ 22, Bash/Zsh, POSIX tools | Bound process handles with real stdout/stderr capture and exit code checks. |

### Remote browser artifact transport (SCP)
When `ego-browser` runs against a remote host (e.g., via SSH tunnel to a remote browser machine), browser scripts execute remotely and write screenshots/downloads to the **remote filesystem**. The executor must transfer remote artifacts to the local campaign's `evidences/` path via `scp` (e.g. `scp $REMOTE_HOST:$REMOTE_PATH $LOCAL_EVIDENCE_PATH`) before sealing the execution submission. Unretrieved remote files will fail local verification with `MISSING_ARTIFACT`.

## Execution modes: Streamlined vs. Full Campaign

Choose the execution model matching the task scope to eliminate unnecessary serial overhead and token waste:

1. **Streamlined Fast-Path** (Single journey, smoke test, or pre-authored suite):
   - **Step 1: Environment Readiness (Wave 0)** — Verify target, leased ports, and tool runner.
   - **Step 2: Parallel Execution** — Dispatch executors concurrently across ready test cases up to host capacity.
   - **Step 3: Verification** — Dispatch independent verifier(s). If `review_count: 2`, dispatch Verifier A and Verifier B concurrently in parallel.
   - Bypass exploratory roles (Feature scout, Planner, Plan auditor, Ticket writer) when test cases already exist.

2. **Full Multi-Agent Campaign** (Large product surfaces, exploratory discovery, or multi-team fixes):
   - Follow the full 12-role DAG lifecycle for feature mapping, planning, audit, serialized worktree repairs, and final closure audit.

## Role taxonomy

The host orchestrator is the sole dispatcher. Workers never spawn workers. Use a fresh, isolated context for each assigned task; changing a role label inside one conversation does not create independence.

| Role | Read next | Result |
|---|---|---|
| Orchestrator | [Orchestrator](references/roles/orchestrator.md) | Dispatch, reconcile, recover, and hand off the campaign |
| Feature scout | [Feature scout](references/roles/feature-scout.md) | Feature/subfeature map with product-source gaps |
| Scenario author | [Scenario author](references/roles/scenario-author.md) | Gherkin case, expectation manifest, executable instructions |
| Planner | [Planner](references/roles/planner.md) | Coverage and dependency plan with resource claims |
| Plan auditor | [Plan auditor](references/roles/plan-auditor.md) | Independent plan or final closure audit |
| Environment operator | [Environment operator](references/roles/environment-operator.md) | Owned dev runtime and client/tool readiness |
| Executor | [Executor](references/roles/executor.md) | Observations and saved evidence, without a final verdict |
| Verifier | [Verifier](references/roles/verifier.md) | Evidence-only expectation review; never a test rerun |
| Diagnostician | [Diagnostician](references/roles/diagnostician.md) | Classified finding and confirmed or hypothetical cause |
| Ticket writer | [Ticket writer](references/roles/ticket-writer.md) | Deduplicated issue for an implementation-bound defect |
| Implementer | [Implementer](references/roles/implementer.md) | Scoped worktree fix, developer checks, and PR |
| Integrator | [Integrator](references/roles/integrator.md) | Serialized merge, new target, independent retest obligations |

## Edge cases in conditional test loops ("Test this, if not that, then do this")

When authoring or executing scenarios with conditional logic or fallback branches, enforce these guardrails:

1. **Distinguish Execution Faults from Clean Falsity**:
   An unhandled exception, network timeout, HTTP 500 error, or browser crash is an **execution failure**, NOT a condition evaluating to `false`. Treating a crash as a negative condition and taking the fallback branch silently masks critical bugs. If an action throws or times out unexpectedly, fail the step immediately.
2. **Explicit Condition Waits over Instantaneous Checks**:
   Modern web apps render asynchronously with client-side hydration. Checking `if (element.isVisible())` instantaneously evaluates `false` prematurely. Always use bounded condition waits (`waitForSelector`, `waitForFunction`) with an explicit timeout before concluding an element is absent.
3. **Atomic State Isolation & Teardown between Branches**:
   If Branch A partially executes (fills an input, mutates local storage, clicks a toggle) before failing, Branch B runs in a dirty DOM state. Enforce a state reset (page reload or fixture reset) before executing a fallback branch.
4. **Bounded Fallback Depth (No Circular Loops)**:
   Limit fallback depth to at most 1 (`fallback_depth <= 1`). Never allow "if A fails try B; if B fails try A" circular loops that burn tokens and hang execution.
5. **Session Expiration Guard**:
   Check for HTTP 401/403 or URL redirection to login before evaluating branch conditions to prevent misattributing expired credentials to application UI absence.

## Parallelism and loop optimization

- **Concurrent Dual Verification**: When an expectation declares `review_count: 2`, dispatch Verifier A and Verifier B **concurrently in parallel**. They are blind to each other; running them serially doubles verification time for zero gain.
- **DAG Branch Parallelism**: Ready tasks with orthogonal resource leases must be dispatched concurrently up to host capacity. Waves are visual groupings of dependencies, never global stop-the-world barriers.
- **Dynamic Sibling Scaling**: Sibling test cases sharing identical read fixtures scale concurrently up to host capacity rather than being artificially throttled.
- **Adaptive Retries**: For deterministic UI/assertion failures, do not burn a full 5-attempt retry cycle. Bound retries to 1–2 for deterministic defects, reserving 3 attempts strictly for verified timing flakiness.

## Start or resume

1. Read [Workflow](references/workflow.md) and [Harness portability](references/harness-portability.md). Resolve project, target, task authority, host worker capacity, and interaction mode.
2. From this skill's directory, inspect prerequisites:

   ```bash
   node scripts/agentic-tests.mjs doctor --project "$PROJECT"
   node scripts/agentic-tests.mjs doctor --project "$PROJECT" --setup
   ```

   Confirm runner readiness (`ego-browser` for web, `maestro` for mobile, `mcpc` for MCP).
3. Initialize the campaign layout using realistic host capacity (default 2–4 workers locally):

   ```bash
   node scripts/agentic-tests.mjs init --project "$PROJECT" --slug "$SLUG" \
     --mode interactive --max-active 4 --host-capacity "$CAPACITY" --max-attempts 3
   ```

4. Delegate Wave 0 environment setup and test preparation. Accept audited plans. Dispatch eligible DAG branches concurrently within resource leases.
5. Reconcile accepted reports as they arrive. Assign evidence verifiers immediately in parallel; dispatch diagnosis for verified failures while independent tests continue.
6. After serialized repairs, verify on the integrated target, conduct an independent closure audit, and serve the inspectable report.

## Invariants that govern every role

- Use frozen expectation IDs and product-source references. Code inspection discovers features; implementation behavior alone cannot define correctness.
- Keep author, executor, verifier, and implementer/retest contexts independent. Critical expectations need two blind verifier contexts dispatched concurrently. A verifier reads saved evidence; supplemental execution belongs to a fresh executor.
- Bound active workers by `min(max_active, host capacity)`. Default to realistic concurrency (2–4 for local hosts).
- Freeze source and configuration while a runtime generation is in use. Worktrees and data-resource isolation are separate obligations.
- Preserve honest FAIL, PARTIAL, and NOT_RUN submissions. A declared evidence gap may be accepted structurally; it cannot support PASS.
- Keep finding lineages stable: shared interventions apply across related cases. Retries require a stated change in hypothesis or execution approach.
- Bound Git delivery authority to the project's configured remote repository (GitHub, GitLab, or internal Git). Pass target repository explicitly to CLI tools (`gh`, `glab`).

## Common references

| Read when | Reference |
|---|---|
| Starting/resuming, choosing streamlined vs full workflow, or managing roles | [Workflow](references/workflow.md) |
| Reading records, lifecycle states, historical proof, or finding classes | [Records and states](references/records-and-states.md) |
| Running commands, drafting YAML, querying with optional yq, or submitting | [CLI and yq](references/cli-and-yq.md) |
| Writing expectations, capturing artifacts, remote SCP transfer, or conditional loops | [Scenarios and evidence](references/scenarios-and-evidence.md) |
| Selecting ready jobs, resource leases, parallel reviews, or adaptive retries | [Scheduling](references/scheduling.md) |
| Preparing web/CLI/MCP/mobile tools, worktrees, data, and runtime generations | [Runtimes and isolation](references/runtimes-and-isolation.md) |
| Connecting to MCP servers using mcpc 0.7.x session-first client | [MCPC session](references/mcpc-session.md) |
| A real remote HTTP client needs an application/report endpoint | [Cloudflare tunnels](references/cloudflare-tunnels.md) |
| Diagnosing a verified defect, opening Git records, fixing, or merging | [Fixes and delivery](references/fixes-and-delivery.md) |
| Building the report, recovering interrupted work, or deciding closure | [Reporting and recovery](references/reporting-and-recovery.md) |
| Mapping this protocol onto host agent tools, runner dependencies, and model rules | [Harness portability](references/harness-portability.md) |
| Auditing the design's provenance and inherit/avoid decisions | [Sources](references/sources.md) |
