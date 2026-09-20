# Herdr Native Acceptance Scenarios & Forward-Test Specifications

## 1. Acceptance Criteria (K1-K7)
These tests must pass for any orchestration framework changes:

- **K1**: The EM can dispatch a worker into a separate worktree and tab without breaking topology.
- **K2**: The worker publishes a handback report containing its exact SHA and check results.
- **K3**: The EM spawns a reviewer agent pointing to that exact SHA.
- **K4**: The reviewer rejects a deliberately broken diff, invalidating the state.
- **K5**: The worker fixes the code, commits a new SHA, and hands back.
- **K6**: The reviewer approves the new SHA.
- **K7**: The integration executor merges the approved SHA, runs generic checks, and pushes.

## 2. Small Smoke Test
A fast validation of the core loop:
1. EM is started in the right pane of the CTO tab.
2. EM assigns a documentation task to a worker.
3. Worker completes the documentation task, publishes a report, and notifies EM.
4. EM acknowledges completion.

## 3. Historical Scenario Catalog (Optional)
The original 14 heavy scenarios are preserved here as a catalogue. Do not execute them unless explicitly requested.

- `SCEN-01`: Cold Bootstrap & EM Initialization
- `SCEN-02`: Clean-Context Worktree Allocation & Concurrent Synthesis
- `SCEN-03`: TDD Red-to-Green & Isolated Commits
- `SCEN-04`: Immutable Report Handback & Non-Blocking EM Intake
- `SCEN-05`: Independent Exact-SHA Review & Rejection
- `SCEN-06`: Diagnostic Recovery & Prompt Bridge Fallback
- `SCEN-07`: Continuous Parralel Drafting & Review
- `SCEN-08`: Resolution of Reviewer Rejection
- `SCEN-09`: Serial Rebase & Merge Conflict Resolution
- `SCEN-10`: Review Invalidation via Changing HEAD
- `SCEN-11`: Generation & Diff Hygiene Verification
- `SCEN-12`: Mission-Specific PR Hold & Candidate Validation
- `SCEN-13`: Safe Sequential Teardown
- `SCEN-14`: Final EM Handback to CTO
