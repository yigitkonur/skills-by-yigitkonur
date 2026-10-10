---
name: run-agentic-tests
description: "Use if orchestrating multi-agent E2E campaigns with independent evidence review, isolated runtimes, and defect fix/retest loops."
disable-model-invocation: true
---

# Run Agentic Tests

Coordinate a real E2E campaign from scenarios to independently inspected evidence,
scoped repairs, integrated-target retests, and an inspectable HTML report. This skill
provides the operational harness for multi-agent testing across web, mobile, MCP, and CLI,
integrating directly with specialized test runners.

## Model selection & reasoning configuration per provider

Models are configured strictly per provider to balance execution speed, assertion accuracy, and token economics. **Core architectural rules:**
1. **Anthropic Sonnet Mandate**: Mandate Anthropic Sonnet (`claude-3-7-sonnet` primary, `claude-3-5-sonnet` baseline) with low or medium reasoning budget (`budget_tokens: 1,024–2,048`).
2. **Strict Prohibition of Opus (`claude-3-opus`)**: Never use Opus for automated test loops. Opus is 5x more expensive ($15/$75 per MTok input/output vs $3/$15 for Sonnet), introduces severe multi-turn tool latency across 20–50 turn automated loops, and yields zero assertion accuracy improvements over Sonnet.
3. **Reasoning Budget Caps**: Cap extended thinking to **1,024–2,048 tokens** (`budget_tokens: 1,024–2,048`); disable or set minimal (`budget_tokens: 1024`) for routine deterministic steps to prevent tool call timeouts.

| Provider | Task category & assigned roles | Model | Reasoning / Budget | Operational rule |
|---|---|---|---|---|
| **Anthropic** | Simple ops (Executor, Environment operator, Ticket writer, Integrator) | `claude-3-7-sonnet` (or `claude-3-5-sonnet`) | Minimal (`budget_tokens: 1,024` or disabled) | Fast turnaround and low token usage for multi-step browser/CLI flows. Extended thinking is disabled or capped to ≤1,024 tokens. |
| **Anthropic** | Evidence checks, verification & diagnosis (Verifier, Diagnostician, Plan auditor, Implementer, Scenario author, Planner) | `claude-3-7-sonnet` (or `claude-3-5-sonnet`) | `medium` (`budget_tokens: 1,024–2,048`) | Balanced reasoning ensures rigorous evaluation of screenshots, logs, and state evidence without timeouts. **STRICTLY PROHIBIT claude-3-opus** in automated loops. |
| **OpenAI / Codex** | Simple ops (Executor, Environment operator, Ticket writer, Integrator, Orchestrator, Feature scout) | `gpt-6-luna` | `low` (`reasoning_effort: "low"`) | `luna` is a compact model; `low` reasoning effort keeps tool calls fast and economical without burning tokens on mundane commands. |
| **OpenAI / Codex** | Evidence checks, verification & diagnosis (Verifier, Diagnostician, Plan auditor, Implementer, Scenario author, Planner) | `gpt-6.1-sol` | `medium` (`reasoning_effort: "medium"`) | Balanced reasoning ensures rigorous evaluation of screenshots, logs, and state evidence without timeout delays. Strictly avoid `high`/`xhigh` token burn. |
| **Gemini** | Simple ops (Executor, Environment operator, Integrator, Orchestrator, Feature scout) | `gemini-3.8-flash` | `low` | High throughput, fast response times for multi-step browser/CLI steps. |
| **Gemini** | Evidence checks & verification (Verifier, Plan auditor, Implementer) | `gemini-3.8-flash` | `medium` | Balanced reasoning depth for independent verification and assertion checks. |
| **Gemini** | Deep diagnosis & complex planning (Diagnostician, Planner, Scenario author) | `gemini-3.8-flash` | `high` | Increased reasoning depth reserved strictly for root-cause diagnosis, DAG planning, and scenario authoring. |

## Tool dependencies & specialized sibling skills

This skill orchestrates campaigns; specialized domain testing is executed through dedicated peer skills. The system must verify prerequisites during Wave 0 and **fail fast** if the required runner is missing:

| Domain | Designated runner skill | Dependency & repository | Fail-fast requirement |
|---|---|---|---|
| **Web** | `ego-browser` | [citrolabs/ego-lite](https://github.com/citrolabs/ego-lite) · [ego-browser skill](https://github.com/citrolabs/ego-lite/blob/main/skills/ego-browser/SKILL.md) | Refuse to start (`RUNNER_SKILL_MISSING` / `RUNNER_CLI_MISSING`) if `ego-browser` skill/CLI is missing. Connects over SSH to remote host `tugce` with automated reverse port forwarding. Remote screenshots **must be retrieved via SCP** to local `evidences/`. |
| **Mobile** | `test-by-maestro` | [test-by-maestro](https://github.com/yigitkonur/skills-by-yigitkonur/tree/main/skills/test-by-maestro) · [Maestro CLI](https://maestro.dev) | Refuse to start if `test-by-maestro` skill or Maestro CLI (`maestro --version` ≥ 2.10.0 / 2.11.0) is missing. Strictly requires Java 17+ (`$JAVA_HOME`). Leverages native 10-tool MCP server (`maestro mcp`). iOS Simulators require macOS (Darwin) with Xcode; Linux hosts cannot run iOS simulators locally (delegate to Maestro Cloud or SSH). Physical iOS devices fail fast in 2.11.0. Retrieve remote JUnit XML/screenshots via SCP. |
| **MCP** | `test-by-mcpc-cli` | [test-by-mcpc-cli](https://github.com/yigitkonur/skills-by-yigitkonur/tree/main/skills/test-by-mcpc-cli) · [@apify/mcpc](https://github.com/apify/mcpc) | Refuse to start if `test-by-mcpc-cli` skill or `mcpc` CLI is missing. Requires `mcpc` 0.7.x session-first CLI (`mcpc connect <url> @session`). Pre-0.7.0 syntax is obsolete. Supports official MCP skills extension (`skills-list`, `skills-get <skill> [file]`) and directory resources (`resources-directory-read`). |
| **CLI** | Native process runner | Node.js ≥ 22, Bash/Zsh, POSIX tools | Bound process handles with real stdout/stderr capture and exit code checks. |

### Remote artifact transport (SCP)
When `ego-browser` (e.g., via SSH tunnel to remote browser host `tugce`) or `test-by-maestro` (via SSH to a remote macOS simulator host) runs against a remote host, scripts execute remotely and write screenshots, test logs, and JUnit XML to the **remote filesystem**. The executor must transfer remote artifacts to the local campaign's `evidences/` path via hardened `scp` before sealing the execution submission:
- **Enforce absolute remote paths**: `scp -p "$REMOTE_HOST:$ABSOLUTE_REMOTE_PATH" "$LOCAL_EVIDENCE_PATH"` (OpenSSH 9.0+ defaults to SFTP and resolves unanchored paths relative to user home).
- **Escape special characters**: Quote paths on both sides to prevent remote shell splitting on spaces or query parameters.
- **Protocol fallback**: If the remote host lacks SFTP subsystem support (`subsystem request failed on channel 0`), pass `scp -O` to use the legacy SCP wire protocol.
- **Config aliases**: When `$REMOTE_HOST` is defined in `~/.ssh/config`, omit manual `-P <port>` flags to prevent connection collisions.
Unretrieved remote files will fail local verification with `MISSING_ARTIFACT`.

## Execution modes: Streamlined vs. Full Campaign

Choose the execution model matching the task scope to eliminate unnecessary serial overhead and token waste:

1. **Streamlined Fast-Path** (Single journey, smoke test, or pre-authored suite):
   - **Step 1: Environment Readiness (Wave 0)** — Verify target reachability, leased ports, and tool runner CLI/daemon (`ego-browser`, `maestro`, `mcpc`).
   - **Step 2: Parallel Execution** — Dispatch executors concurrently across ready test cases up to host capacity (`min(max_active, host_capacity)`). Retrieve remote artifacts via SCP if running remotely.
   - **Step 3: Verification** — Dispatch independent verifier(s). If `review_count: 2`, dispatch Verifier A and Verifier B concurrently in parallel with asymmetric evaluation lenses (Verifier A: specification conformance; Verifier B: adversarial/boundary scrutiny) and distinct seeds (`seed: sha256(campaign_id + task_id + "slot_a")` vs `"slot_b"`) to eliminate cache collision and guarantee mathematically independent reviews.
   - **Explicit Role Bypass**: Bypasses exploratory roles (`Feature scout`, `Scenario author`, `Planner`, `Plan auditor`, `Ticket writer`) when test cases already exist on disk.

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

When authoring or executing scenarios with conditional logic or fallback branches, enforce these 8 guardrails:

1. **Distinguish Execution Faults from Clean Falsity**:
   An unhandled JavaScript exception, network timeout, HTTP 500 error, or browser crash is an **execution failure**, NOT a business condition evaluating to `false`. Treating a crash as a negative condition and taking the fallback branch silently masks critical bugs. If an action throws or times out unexpectedly, fail the step immediately.
2. **Explicit Condition Waits over Instantaneous Checks**:
   Modern SPAs render asynchronously with client-side hydration. Checking `if (element.isVisible())` instantaneously evaluates `false` prematurely. Always use bounded condition waits (`waitForSelector`, `waitForFunction`, `toBeVisible({ timeout: 5000 })`) with an explicit timeout before concluding an element is absent.
3. **Atomic State Isolation & Teardown between Branches**:
   If Branch A partially executes (fills an input, mutates local storage, clicks a toggle) before failing, Branch B runs in a dirty DOM state. Enforce a state reset (page reload `page.goto()` / `page.reload()` or fixture reset) before executing a fallback branch.
4. **Bounded Fallback Depth (No Circular Loops)**:
   Limit fallback depth to at most 1 (`fallback_depth <= 1`). Never allow "if A fails try B; if B fails try A" circular loops that burn tokens and hang execution.
5. **Session Expiration Guard**:
   Check for HTTP 401/403 or URL redirection to login before evaluating branch conditions to prevent misattributing expired credentials to application UI absence. Trigger session re-auth instead of taking an unrelated fallback.
6. **Non-Idempotent Side Effects & Transactional Integrity**:
   If Branch A mutates state (submits a payment, creates an account, writes to a database) before encountering a UI failure, taking Branch B without rollback causes duplicate mutations, 409 Conflict errors, or double charges. Any branch containing mutating side effects must be strictly idempotent or provide an explicit transactional cleanup/rollback step before Branch B executes.
7. **Observable Fallback Recording (`FALLBACK_TAKEN`)**:
   Taking a fallback branch must never result in an invisible `PASS` that conceals primary flow regressions. The execution observation must explicitly record `FALLBACK_TAKEN` with evidence detailing why Branch A did not execute, preserving the primary failure for verifier inspection.
8. **Branch Oracle & Verification Clarity**:
   The executor must explicitly record branch decision points, entry conditions, and selected paths in `10-execution.record.yaml` so that independent blind verifiers know exactly which contract was evaluated.

## Parallelism and loop optimization

- **Concurrent Dual Verification with Asymmetric Lenses**: When an expectation declares `review_count: 2`, dispatch Verifier A and Verifier B **concurrently in parallel**. Verifier A evaluates via the Specification Conformance Lens (positive Given/When/Then adherence and schema checks), while Verifier B evaluates via the Adversarial & Boundary Scrutiny Lens (negative testing, visual glitches, fallback auditing, and capture gaps). Distinct seeds (`seed: sha256(campaign_id + task_id + "slot_a")` vs `"slot_b"`) ensure non-identical completion trajectories. Disagreements resolve to `INCONCLUSIVE` (never averaged).
- **Dynamic DAG Unblocking**: Ready tasks with orthogonal resource leases are unblocked and dispatched dynamically as soon as prerequisites pass. Waves are visual groupings of dependencies, never global stop-the-world barriers.
- **Dynamic Sibling Scaling**: Sibling test cases sharing identical read fixtures scale concurrently up to host capacity rather than being artificially throttled.
- **Adaptive Retries**: For deterministic UI/assertion failures, do not burn an automatic 5-attempt retry cycle. Bound retries to **1–2 attempts** for deterministic defects (a 2nd attempt requires a stated change in hypothesis/approach), reserving up to 3 attempts strictly for verified timing/network flakiness.

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
