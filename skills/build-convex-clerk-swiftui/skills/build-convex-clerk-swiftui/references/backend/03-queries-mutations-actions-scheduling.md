# Queries, Mutations, Actions, And Scheduling

## Use This When
- Choosing which Convex function type to write.
- Explaining the server architecture to Swift developers who are new to backend work.
- Reviewing action flows, background work, or external API integration.

## Function Taxonomy
- Query: deterministic, read-only, reactive, subscribable.
- Mutation: deterministic transactional write path with server-side OCC retry.
- Action: non-transactional path for external I/O, long-running work, or runtime-specific libraries.
- Internal functions: backend-only helpers callable from other Convex functions.
- HTTP actions: public endpoints for webhooks or custom integrations.
- Scheduled functions and crons: delayed or recurring execution owned by backend logic.

## Default Decision Guide
- If the UI needs live data, start with a query.
- If the user intent writes data, start with a mutation.
- If external APIs or heavy runtime work are involved, let a mutation record intent and schedule or call an action.
- Use internal functions for server-to-server calls, shared logic, and scheduled execution targets.
- For authenticated endpoints, use `userQuery`/`userMutation` wrappers from `convex-helpers` instead of raw `query`/`mutation` (see [04-auth-rules-and-server-ownership.md](04-auth-rules-and-server-ownership.md)).

## The Intent Plus Schedule Pattern
- Record the durable state change in a mutation first.
- Schedule follow-up work from that mutation so the schedule is rollback-safe.
- Let the action call external APIs and then write results back through internal mutations.
- Expose job status through queries if the Swift UI needs progress.

## Runtime Rules
- Do not put external side effects inside mutations.
- Do not mix `"use node"` files with queries or mutations.
- Use `runAction` only when crossing runtimes, not as a general abstraction tool.
- Avoid sequential `ctx.runQuery` or `ctx.runMutation` chains in actions when one internal mutation can do the work atomically.

## Error Handling Rule
- Throw structured `ConvexError` payloads when the client needs machine-readable failure data.
- Keep unexpected infrastructure failures distinct from product validation errors.
- Plan client messaging around that distinction.

## Scheduling Rule
- Scheduling from mutations is atomic with the mutation.
- Scheduled functions do not inherit auth context.
- Pass identity or ownership args explicitly if background work must act on behalf of a user.

## Avoid
- Public `api.*` references for scheduled or backend-only calls.
- Actions as a shortcut for normal write paths.
- Treating queries as if they were REST handlers with side effects.
- Hiding long-running external effects behind mutations.

## Read Next
- [04-auth-rules-and-server-ownership.md](04-auth-rules-and-server-ownership.md)
- [../advanced/04-streaming-workloads-and-transcription.md](../advanced/04-streaming-workloads-and-transcription.md)
- [../playbooks/03-streaming-and-transcription-playbook.md](../playbooks/03-streaming-and-transcription-playbook.md)
