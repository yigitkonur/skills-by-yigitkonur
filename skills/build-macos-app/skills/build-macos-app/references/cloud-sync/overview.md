# Reference Map

## Use This Corpus For
- Designing a Convex + Clerk backend for a SwiftUI app that targets iPhone, Mac, or both.
- Deciding whether Convex is the right backend before implementation.
- Choosing production-safe client, auth, lifecycle, and backend patterns for the current Swift SDK.
- Loading only the narrowest reference needed instead of dumping the entire research set into context.

## Source Boundary
- Ground broad product and architecture guidance in the repo-local references listed below.
- Treat Clerk-specific implementation facts in this skill as verified against the official `clerk-convex-swift` package and its `Example/WorkoutTracker` sample, as summarized in the auth, client-sdk, playbook, and operations docs here.
- Treat this reference set as opinionated toward the March 28, 2026 source snapshot and ConvexMobile `0.8.1`.
- Present ecosystem and feature gaps honestly. Do not market around them.

## Start Here
1. Read [onboarding/04-adoption-checklist-and-hard-stops.md](onboarding/04-adoption-checklist-and-hard-stops.md) to decide whether Convex fits the app.
2. Read [onboarding/03-mental-model-live-data-functions-and-state.md](onboarding/03-mental-model-live-data-functions-and-state.md) before making architecture decisions.
3. Read [authentication/01-clerk-first-setup.md](authentication/01-clerk-first-setup.md) if the app needs user accounts.
4. Read [swiftui/04-environment-injection-and-root-architecture.md](swiftui/04-environment-injection-and-root-architecture.md) before placing the client or auth state.
5. Read [operations/01-verified-corrections-and-trust-boundaries.md](operations/01-verified-corrections-and-trust-boundaries.md) before repeating any claim as fact.

## Folder Guide
- `setup/`: zero-to-running with Node, SPM, Clerk, and first `npx convex dev` run.
- `onboarding/`: product fit, mental model, backend choice, and adoption constraints.
- `backend/`: schema, indexes, functions, scheduling, errors, auth rules, file organization, and server ownership.
- `client-sdk/`: public Swift API surface, type system, subscription behavior, pipeline termination, encoding, connection state, and logging.
- `swiftui/`: view-model patterns, lifecycle ownership, navigation/tab/sheet behavior, tri-state loading, and dependency injection.
- `authentication/`: Clerk-first setup, custom `AuthProvider` work, Firebase fallback, SIWA, and Keychain.
- `platforms/`: iOS suspension, POSIX error 53, offline limits, network recovery, NWPathMonitor, binary size, macOS windows/menu bar, per-window VMs, and support limits.
- `advanced/`: pagination, file storage, image upload, full-text search, streaming/transcription, subscription deduplication, and Convex components.
- `pitfalls/`: the 10 most common mistakes — pipeline termination, threading, auth, offline traps, and more.
- `walkthrough/`: complete chat app from zero — schema, backend, models, views, deployment.
- `quick-reference/`: backend cheat sheet, Swift SDK API surface, SQL mapping, function decision tree, subscription placement matrix.
- `testing/`: mock FFI client, integration tests, SwiftUI previews, OSLog/Console.app, and server-side `convex-test`.
- `playbooks/`: default end-to-end workflows for common app shapes.
- `operations/`: corrected claims, limitations, non-goals, and trust boundaries.

## Fast Routing By Problem
- "Should we use Convex here?" -> [onboarding/02-convex-vs-firebase-vs-supabase.md](onboarding/02-convex-vs-firebase-vs-supabase.md), [onboarding/04-adoption-checklist-and-hard-stops.md](onboarding/04-adoption-checklist-and-hard-stops.md)
- "How do I set up from scratch?" -> [setup/01-installing-convex-and-node-prerequisites.md](setup/01-installing-convex-and-node-prerequisites.md) through [setup/05-first-run-npx-convex-dev.md](setup/05-first-run-npx-convex-dev.md)
- "How should SwiftUI think about Convex?" -> [onboarding/03-mental-model-live-data-functions-and-state.md](onboarding/03-mental-model-live-data-functions-and-state.md)
- "How should we model the backend?" -> [backend/01-schema-document-model-and-relationships.md](backend/01-schema-document-model-and-relationships.md), [backend/02-indexes-query-shaping-and-performance.md](backend/02-indexes-query-shaping-and-performance.md)
- "Which function type do we use?" -> [backend/03-queries-mutations-actions-scheduling.md](backend/03-queries-mutations-actions-scheduling.md), [quick-reference/04-function-decision-tree.md](quick-reference/04-function-decision-tree.md)
- "How do we wire Clerk?" -> [authentication/01-clerk-first-setup.md](authentication/01-clerk-first-setup.md)
- "How do subscriptions reach SwiftUI safely?" -> [client-sdk/03-subscriptions-errors-logging-and-connection-state.md](client-sdk/03-subscriptions-errors-logging-and-connection-state.md), [swiftui/01-consumption-patterns.md](swiftui/01-consumption-patterns.md)
- "Why did my subscription stop updating?" -> [pitfalls/01-pipeline-dies-after-first-error.md](pitfalls/01-pipeline-dies-after-first-error.md), [client-sdk/04-pipeline-termination-and-recovery.md](client-sdk/04-pipeline-termination-and-recovery.md)
- "Where should the client live?" -> [swiftui/04-environment-injection-and-root-architecture.md](swiftui/04-environment-injection-and-root-architecture.md)
- "Will iOS backgrounding break this?" -> [platforms/01-ios-backgrounding-reconnection-and-staleness.md](platforms/01-ios-backgrounding-reconnection-and-staleness.md)
- "What are the common mistakes?" -> [pitfalls/](pitfalls/) (start with 01)
- "How do we do uploads or pagination?" -> [advanced/01-pagination-live-tail-and-history.md](advanced/01-pagination-live-tail-and-history.md), [advanced/02-file-storage-upload-download-and-document-ids.md](advanced/02-file-storage-upload-download-and-document-ids.md)
- "How do we handle streaming or transcription?" -> [advanced/04-streaming-workloads-and-transcription.md](advanced/04-streaming-workloads-and-transcription.md), [playbooks/03-streaming-and-transcription-playbook.md](playbooks/03-streaming-and-transcription-playbook.md)
- "Show me a complete example" -> [walkthrough/01-from-zero-to-realtime-chat-app.md](walkthrough/01-from-zero-to-realtime-chat-app.md) through [walkthrough/05-deployment-checklist.md](walkthrough/05-deployment-checklist.md)
- "Quick lookup / cheat sheet" -> [quick-reference/](quick-reference/) (5 docs)
- "How do I test this?" -> [testing/01-mock-ffi-client-unit-testing.md](testing/01-mock-ffi-client-unit-testing.md) through [testing/05-server-side-testing-with-convex-test.md](testing/05-server-side-testing-with-convex-test.md)

## Non-Negotiable Defaults
- Prefer Clerk as the default Swift auth path.
- Prefer one long-lived authenticated client per process.
- Prefer `ObservableObject` plus `@StateObject` for subscription-owning models.
- Treat subscription errors as terminal unless you explicitly rebuild the pipeline.
- Treat iOS as online-only with reconnect, not offline-first.
- Treat macOS support as Apple Silicon only.
- Use verification notes to correct stale or overstated claims.

## Corrected Claims To Remember
- `TabView` does cancel `.task` on tab switch; do not write guidance that says the opposite.
- `@Observable` can run `init()` multiple times, but the stored-instance issue is side effects, not multiple active retained instances.
- The `convex-helpers` pagination/filter issue cited in the corpus is real history, but the referenced issue is closed.
- Binary-size impact is likely larger than the optimistic low-end estimate from the research set.

## Read Next By Outcome
- New greenfield app: [playbooks/01-greenfield-swiftui-app-playbook.md](playbooks/01-greenfield-swiftui-app-playbook.md)
- Shared iOS + macOS app: [playbooks/02-shared-ios-macos-app-playbook.md](playbooks/02-shared-ios-macos-app-playbook.md)
- Streaming/transcription app: [playbooks/03-streaming-and-transcription-playbook.md](playbooks/03-streaming-and-transcription-playbook.md)
