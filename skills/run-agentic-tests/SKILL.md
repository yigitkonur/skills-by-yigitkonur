---
name: run-agentic-tests
description: "Use if orchestrating multi-agent E2E campaigns with independent evidence review, isolated runtimes, and defect fix/retest loops."
---

# Run Agentic Tests

Coordinate a real E2E campaign from scenarios to independently inspected evidence,
scoped repairs, integrated-target retests, and an inspectable HTML report. This is
one self-contained skill with role instructions; its roles are not separate skills.

## Entry boundary

Use for a delegated E2E campaign on web, CLI, MCP, or native mobile software,
including resuming an existing campaign and repairing its confirmed defects.
Honor an existing scenario set before discovering additional scope.

Use the direct workflow for a single local test command, unit-test authoring,
read-only code review, a one-page browser check, or tunnel setup alone. Those
tasks do not need this campaign machinery. Do not use a unit suite as a substitute
for exercising user behavior through the actual interface.

## Choose your role first

The host orchestrator is the sole dispatcher. Workers never spawn workers.
Use a fresh, actual isolated context for each assigned task; changing a role label
inside one conversation does not create independence.

Read your role row, [CLI and submission](references/cli-and-yq.md), and the
assigned handoff. Follow additional pointers only when their condition applies.
Do not preload the entire reference directory into every worker.

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

## Start or resume

1. Read [Workflow](references/workflow.md) and
   [Harness portability](references/harness-portability.md). Resolve the exact
   project, Git target, task authority, host worker capacity, and interaction mode.
   Native isolated agents are required; messaging is optional.
2. From this skill's directory, inspect prerequisites:

   ```bash
   node scripts/agentic-tests.mjs doctor --project "$PROJECT"
   node scripts/agentic-tests.mjs doctor --project "$PROJECT" --setup
   ```

   Setup uses the locked package dependencies in an external cache. It does not
   install another agent harness or require global npm packages. Read CLI help
   and the JSON result before proceeding.
3. For a new campaign, initialize the fixed filesystem layout. Use the actual
   host capacity, not the desired number of workers:

   ```bash
   node scripts/agentic-tests.mjs init --project "$PROJECT" --slug "$SLUG" \
     --mode interactive --max-active 20 --host-capacity "$CAPACITY" --max-attempts 5
   ```

   Use `--mode autonomous` only when the task calls for autonomous decisions.
   Retain the returned campaign path. Resume by inspecting `status` and canonical
   records at the existing path, never by initializing over them.
4. Delegate Wave 0 and scenario preparation. Accept a plan only after an
   independent plan audit. Dispatch every eligible DAG branch within capacity
   and declared resource leases. Waves visualize dependencies; they are not
   campaign-wide barriers.
5. Reconcile accepted reports as they arrive. Assign evidence review immediately;
   dispatch diagnosis and repair for verified failures while independent tests
   continue. Worker submission acceptance does not mean a test passed.
6. After serialized repairs, delegate execution and evidence review on the final
   integrated target, then an independent closure audit. Build and serve the
   report even if it contains explicit blockers. Keep the final application and
   report available for inspection; stop only owned, unused processes.

## Invariants that govern every role

- Use frozen expectation IDs and product-source references. Code inspection can
  discover features; implementation behavior alone cannot define correctness.
- Keep author, executor, verifier, and implementer/retest contexts independent.
  Critical expectations need two blind verifier contexts as declared before the
  run. A verifier reads saved evidence; any supplemental execution belongs to a
  fresh executor dispatched by the orchestrator.
- Bound active role workers by `min(20, host capacity)`. Reserved dispatches count
  until their workers actually finish. The CLI reserves work; the host launches
  and terminates agents.
- Freeze source and configuration while a runtime generation is in use. A new
  target cannot inherit an old PASS as current proof. Worktrees and data-resource
  isolation are separate obligations.
- Preserve honest FAIL, PARTIAL, and NOT_RUN submissions. A declared evidence gap
  may be accepted structurally; it cannot support PASS. Report uncertain evidence
  as uncertain evidence, not as an accusation about a worker.
- Keep one unresolved finding lineage across names, scenarios, and repairs:
  at most the first failed execution plus four corrective attempts. Each retry
  explains what changed and what evidence supports a different next action.
- Use existing scoped delivery authority for fixes, PRs, and serial merges.
  Unknown material product behavior or expanded scope follows campaign mode;
  do not add a separate human-review gate for an already authorized fix.

## Common references

| Read when | Reference |
|---|---|
| Starting/resuming, asking a material question, or choosing the next role | [Workflow](references/workflow.md) |
| Reading records, lifecycle states, historical proof, or finding classes | [Records and states](references/records-and-states.md) |
| Running commands, drafting YAML, querying with optional yq, or submitting | [CLI and yq](references/cli-and-yq.md) |
| Writing expectations, capturing artifacts, reviewing evidence, or scoping a side finding | [Scenarios and evidence](references/scenarios-and-evidence.md) |
| Selecting ready jobs, resource leases, critical reviews, or retries | [Scheduling](references/scheduling.md) |
| Preparing web/CLI/MCP/mobile tools, worktrees, data, and runtime generations | [Runtimes and isolation](references/runtimes-and-isolation.md) |
| A real remote HTTP client needs an application/report endpoint | [Cloudflare tunnels](references/cloudflare-tunnels.md) |
| Diagnosing a verified defect, opening GitHub records, fixing, or merging | [Fixes and delivery](references/fixes-and-delivery.md) |
| Building the report, recovering interrupted work, or deciding closure | [Reporting and recovery](references/reporting-and-recovery.md) |
| Mapping this protocol onto the current host's native agent/tools interface | [Harness portability](references/harness-portability.md) |
| Auditing the design's provenance and inherit/avoid decisions | [Sources](references/sources.md) |

## Assets and authority

Use the generated task draft as the base; preserve its allocated metadata.
Consult `assets/templates/` for field shapes and document sections. Copy a
template only when no generated draft exists; never submit example values.

The installed CLI and [record schema](schemas/records.schema.json) own machine
syntax. The references own the operational protocol. If they disagree, record
the exact mismatch and request a controller correction; do not invent flags,
relax validation, or hand-edit canonical records to bypass the contract.

Finish with the current integrated target, coverage and unresolved obligations,
report path/URL, source/issue/PR trail, and any explicit capability limitations.
Communicate with the user in their language; keep campaign instructions and
role prompts in English unless they request otherwise.
