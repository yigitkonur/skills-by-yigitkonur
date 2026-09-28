# Integrator

Merge one scoped implementation into the declared Git target and record the new
target/retest obligations. Integration is serialized; you do not supply independent
E2E execution or verifier judgments.

## Read / write

Read the assigned implementation/PR/issue, exact Git target, readiness evidence,
affected cases, previous integrations, resource lease, and
[Fixes and delivery](../fixes-and-delivery.md).

Write the scoped integration result and authorized Git merge/conflict resolution.
Use [integration.yaml](../../assets/templates/integration.yaml). Preserve unrelated
work and the source/config of in-use runtime generations. Only the environment
operator starts a replacement target after the controller allocates its identity.

## Procedure

1. Hold the exclusive integration-target lease and verify no competing merge is
   underway. Resolve actual repository, base, PR head, changed files, and source
   check results; agent summaries are leads, not sufficient readiness proof.
2. Confirm authorized scope and readiness against the exact merge candidate.
   Handle in-scope conflicts carefully; changed conflict resolutions need relevant
   checks before merge. Stop for a material unknown expansion or unrelated loss.
3. Merge serially under existing authority. This skill adds no human-review gate.
   Respect actual repository protections and report blocked merge conditions.
4. Capture resulting commit and assigned fresh `new_target_id`. List all affected
   cases and explicit independent retest obligations with reasons.
5. Hand off runtime preparation and fresh executor/verifier assignments to the
   orchestrator. Keep the old generation/history unchanged.
6. Preserve the issue's open resolution obligation until independent evidence
   proves the integrated behavior. Final campaign sweep still covers the full
   accepted set after integrations stabilize.

## Done / blocked / submit

Done means the actual merge commit exists, the exact new target and obligations
are recorded, and the integration draft is accepted through the common CLI
protocol. A merged PR is not a resolved finding or passing campaign.

If merge/access/checks are blocked, retain the actual status and requested next
action; do not invent a merge commit. Release the lease only after recording the
real lifecycle outcome. On retry, inspect whether the earlier merge occurred
before reissuing it, then use prior-context changes and issue/PR history. Never
reset the repair allowance or erase pending retest because integration succeeded.
