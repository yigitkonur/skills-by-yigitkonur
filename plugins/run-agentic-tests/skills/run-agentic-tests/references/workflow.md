# Campaign workflow

Read this as the orchestrator. Workers use their assigned role reference and
handoff; they do not take over this loop.

## Workflow tracks: Streamlined vs. Full Campaign

Choose the workflow track based on campaign scope:

### Track A: Streamlined Fast-Path (Recommended for smoke checks, single journeys, or pre-authored suites)
Bypasses exploratory roles (Feature scout, Planner, Plan auditor, Ticket writer) to eliminate unnecessary latency and token burn:
1. **Wave 0 Readiness**: Verify runtime target, port leases, and specialized runner (`ego-browser`, `test-by-maestro`, `test-by-mcpc-cli`, or CLI process).
2. **Parallel Execution**: Dispatch executors concurrently across ready test cases up to host capacity. For remote web/mobile runners, retrieve remote artifacts via `scp` to local `evidences/`.
3. **Concurrent Verification**: When `review_count: 2` is declared, dispatch Verifier A and Verifier B **concurrently in parallel**. Reconcile verdicts immediately.

### Track B: Full Multi-Agent Campaign (Exploratory discovery, large product surfaces, or multi-team fixes)
Follows the comprehensive 12-role lifecycle detailed below.

## Establish the campaign

1. Inspect project instructions, Git state, remotes, the requested target, and
   existing test/scenario artifacts. Preserve unrelated work in its checkout.
2. Resolve interaction mode. In interactive mode, ask only when a missing
   decision changes product expectations, scope, a target, or permitted data
   effects. Prefer the host's question tool when available. Bundle closely
   related choices; continue independent work while waiting.
3. In autonomous mode, record a material unknown as a blocker and advance other
   branches. Silence is not approval. Routine worktree, runtime, commit, PR, and
   scoped merge actions use the task's existing authority.
4. Run `doctor`; use `doctor --setup` for the locked external dependency cache.
   Verify that required test runner skills/CLIs exist (`ego-browser`, `maestro`, `mcpc`).
   Initialize a unique campaign or read the existing campaign's status. Record
   decisions in `02-decisions.md` with source and affected scope.

Done: one exact project/target, one campaign, known mode/capacity, and no invented
product decision hidden in a default.

## Prepare scope and Wave 0

- If scenarios already exist, delegate importing them to the scenario author;
  preserve their intent, provenance, and exclusions in the fixed case layout.
- Otherwise delegate feature/subfeature discovery, then author cases from the
  resulting product map. Read [Scenarios and evidence](scenarios-and-evidence.md)
  for acceptable behavior sources. Material unknowns remain visible.
- Delegate environment preparation in parallel where its inputs are known.
  Wave 0 proves tool access, actual-client reachability, source identity,
  fixture/reset access, and owned resources. It does not execute the campaign's
  acceptance cases or award PASS.
- In Track B, delegate a plan from frozen case specs and available targets. A different
  plan-auditor context checks coverage, dependencies, resources, and review
  counts. Accept only its approved revision through `plan accept`.

Done: each runnable case has an oracle, execution recipe, expectation manifest,
ready target, declared dependencies/resources, and approved plan membership.

## Dispatch continuously

Use [Scheduling](scheduling.md). For each ready task: reserve it through the CLI,
launch one fresh host worker with the generated handoff and narrow reading set,
then bind its real host handle. Configure models per provider: Anthropic (`sonnet-5.5` or `haiku-5.5`, no reasoning level needed); Codex (`gpt-6-luna` with `xhigh` for simple ops, `gpt-6.1-sol` with `medium` for evidence checks); Gemini (`gemini-3.8-flash` with `medium` for simple ops, `high` for everything else). Messages (`send_message`) enable real-time
notifications and blocker escalation; files carry durable truth.

Reconcile accepted outputs and inspect `next_actions`; the CLI never spawns agents.
Execution produces observations and artifact references. The verifier opens
those artifacts and judges each expectation. Critical cases get the declared
blind second review dispatched concurrently in parallel with prompt/seed variance (conformance vs. adversarial lenses) to eliminate cache duplicates. Any additional experiment
is a new executor task, never an action performed by the verifier.

When a failure is verified, delegate diagnosis immediately. Implementation-bound
defects proceed to deduplicated tickets and scoped fixes; blockers and evidence
problems take their own recovery path. One blocked dependency chain does not
pause unrelated work. Correcting a rejected YAML draft is not a test retry.

Done for a round: all required reports are accepted, all assigned workers have
actually ended, and the controller has reconciled a sealed verdict or an explicit
next obligation. An empty ready queue is not campaign completion.

## Integrate and close

1. Serialize integrator tasks against the declared Git target. Each merge records
   its commit/new target and affected-case retest obligations.
2. Delegate independent retest execution; its executor and evidence verifiers
   must differ from the implementer. Preserve every earlier round as history.
3. Once delivery stabilizes, run the accepted case set on the final integrated
   target, including cases that passed before a merge. Historical PASS is useful
   context but cannot discharge this sweep.
4. Delegate an independent closure audit. It checks actual coverage, exhausted
   lineages, drift, pending reviews/retests/fixes, and scope decisions; it neither
   executes tests nor repairs the project.
5. Build/serve the report with [Reporting and recovery](reporting-and-recovery.md).
   Report explicit partial coverage when obligations remain. Keep the final app
   and report available for user inspection and identify their owned lifetimes.

Done: report current target, accepted coverage, final audit, issue/PR links,
unresolved obligations, and inspection endpoints. A full PASS requires all
accepted cases' current-target proof and no outstanding closure obligation.
