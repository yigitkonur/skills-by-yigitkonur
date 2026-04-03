# Mental Model: Live Data, Functions, And State

## Use This When
- Teaching a SwiftUI developer how Convex thinks.
- Resetting a team that keeps translating Convex into REST, SQL, or callback-listener vocabulary.
- Making architecture choices before writing either Swift or TypeScript.

## The Core Reset
- Do not think in "fetch this row, then open another channel to watch it." Think in "subscribe to the query result I want and let the backend keep it current."
- Do not think in "endpoints." Think in typed backend functions grouped as queries, mutations, actions, and internal functions.
- Do not think in "security rules attached to tables." Think in server-side TypeScript guard code that decides access explicitly.

## The Three Runtime Shapes
- Query: read-only, deterministic, reactive, subscribable.
- Mutation: transactional write path, deterministic, server-retried on conflict.
- Action: non-transactional external I/O path for APIs, webhooks, AI, or long-running work.

## What "Live Query" Means
- The server runs the query immediately and returns current data.
- Convex tracks the documents that query touched.
- When those documents change, the server re-runs the query and ships a fresh full result.
- The subscription is the cache. Do not build a second manual cache unless you are compensating for a known product gap.

## What Determinism Means In Practice
- Queries must not depend on wall-clock time or random values.
- `Date.now()` inside a query is a design smell because time passing does not re-trigger query re-execution.
- Push time-sensitive behavior into scheduled functions, explicit arguments, or derived booleans.

## How This Maps To SwiftUI
- `@Published` or `@State` owns the current result.
- A Convex subscription updates that state whenever the backend result changes.
- A mutation or action is usually initiated from user intent, then the subscription reflects the updated truth.
- The best SwiftUI architecture places long-lived live data in long-lived models, not transient views.

## Server Ownership Model
- The client provides intent and arguments.
- The server validates auth, ownership, business rules, and write shape.
- The client should not be trusted for authorization identities or data visibility decisions.

## Common Misframings To Correct
- "Convex is just Firebase with TypeScript." No: the query/function model and server guard model are meaningfully different.
- "Action means background job." Not always: actions are for external I/O and may still be part of an interactive flow.
- "Subscription errors are temporary." Not in the Combine pipeline: the stream is terminal unless rebuilt.

## Read Next
- [../backend/03-queries-mutations-actions-scheduling.md](../backend/03-queries-mutations-actions-scheduling.md)
- [../swiftui/01-consumption-patterns.md](../swiftui/01-consumption-patterns.md)
- [../backend/04-auth-rules-and-server-ownership.md](../backend/04-auth-rules-and-server-ownership.md)
