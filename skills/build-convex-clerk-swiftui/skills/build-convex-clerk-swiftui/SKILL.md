---
name: build-convex-clerk-swiftui
description: "Use skill if you are building a SwiftUI app with Convex backend and Clerk auth — covers reactive subscriptions, TypeScript server functions, schema design, auth integration, and iOS/macOS production patterns."
---

# Build Convex With Clerk Backend For SwiftUI Devs

Use this skill to keep Swift-side guidance and Convex-backend guidance aligned.
Use the research corpus for the broad Convex/Swift mental model, and use the verified Clerk facts captured in the auth, client-sdk, playbook, and operations docs here for official `clerk-convex-swift` / `WorkoutTracker` behavior.

## Workflow
1. Decide whether Convex fits the product.
   - Start with [references/onboarding/04-adoption-checklist-and-hard-stops.md](references/onboarding/04-adoption-checklist-and-hard-stops.md).
   - Then read [references/onboarding/02-convex-vs-firebase-vs-supabase.md](references/onboarding/02-convex-vs-firebase-vs-supabase.md) if backend choice is still open.
2. If starting from scratch, follow the setup walkthrough.
   - Read [references/setup/01-installing-convex-and-node-prerequisites.md](references/setup/01-installing-convex-and-node-prerequisites.md) through [references/setup/05-first-run-npx-convex-dev.md](references/setup/05-first-run-npx-convex-dev.md).
3. Reset the mental model before recommending architecture.
   - Read [references/onboarding/03-mental-model-live-data-functions-and-state.md](references/onboarding/03-mental-model-live-data-functions-and-state.md).
   - Use [references/onboarding/01-why-convex-fits-swiftui.md](references/onboarding/01-why-convex-fits-swiftui.md) when the user is SwiftUI-strong but backend-new.
4. Lock auth and root ownership.
   - Default to [references/authentication/01-clerk-first-setup.md](references/authentication/01-clerk-first-setup.md).
   - If the task involves Firebase, a custom provider, or the exact `AuthProvider` contract, also read [references/authentication/02-custom-auth-provider-and-firebase-fallback.md](references/authentication/02-custom-auth-provider-and-firebase-fallback.md).
   - If the task involves Sign in with Apple, Keychain policy, or cached-session restore, also read [references/authentication/03-sign-in-with-apple-keychain-and-session-restoration.md](references/authentication/03-sign-in-with-apple-keychain-and-session-restoration.md).
   - Then read [references/swiftui/04-environment-injection-and-root-architecture.md](references/swiftui/04-environment-injection-and-root-architecture.md).
5. Design the backend before wiring the UI.
   - Read [references/backend/01-schema-document-model-and-relationships.md](references/backend/01-schema-document-model-and-relationships.md).
   - Then [references/backend/02-indexes-query-shaping-and-performance.md](references/backend/02-indexes-query-shaping-and-performance.md), [references/backend/03-queries-mutations-actions-scheduling.md](references/backend/03-queries-mutations-actions-scheduling.md), and [references/backend/04-auth-rules-and-server-ownership.md](references/backend/04-auth-rules-and-server-ownership.md).
   - For internal functions, scheduling, errors, and file organization: [references/backend/05-internal-functions-and-helpers.md](references/backend/05-internal-functions-and-helpers.md) through [references/backend/08-file-organization-and-naming.md](references/backend/08-file-organization-and-naming.md).
6. Design client consumption and ownership.
   - Read [references/client-sdk/01-client-surface-runtime-and-auth-bridge.md](references/client-sdk/01-client-surface-runtime-and-auth-bridge.md), [references/client-sdk/02-type-system-wire-format-and-modeling.md](references/client-sdk/02-type-system-wire-format-and-modeling.md), [references/client-sdk/03-subscriptions-errors-logging-and-connection-state.md](references/client-sdk/03-subscriptions-errors-logging-and-connection-state.md).
   - For pipeline termination (critical): [references/client-sdk/04-pipeline-termination-and-recovery.md](references/client-sdk/04-pipeline-termination-and-recovery.md).
   - Read [references/swiftui/01-consumption-patterns.md](references/swiftui/01-consumption-patterns.md), [references/swiftui/02-observation-and-ownership.md](references/swiftui/02-observation-and-ownership.md), and [references/swiftui/03-lifecycle-navigation-tabs-and-sheets.md](references/swiftui/03-lifecycle-navigation-tabs-and-sheets.md).
7. Load only the platform and advanced docs that match the task.
   - iOS lifecycle or degraded state: [references/platforms/01-ios-backgrounding-reconnection-and-staleness.md](references/platforms/01-ios-backgrounding-reconnection-and-staleness.md), [references/platforms/02-offline-behavior-network-transitions-and-recovery.md](references/platforms/02-offline-behavior-network-transitions-and-recovery.md)
   - Performance, battery, binary-size: [references/platforms/03-performance-battery-and-threading.md](references/platforms/03-performance-battery-and-threading.md), [references/platforms/06-binary-size-and-instruments-profiling.md](references/platforms/06-binary-size-and-instruments-profiling.md)
   - macOS or shared apps: [references/platforms/04-macos-multi-window-menu-bar-and-support-limits.md](references/platforms/04-macos-multi-window-menu-bar-and-support-limits.md), [references/platforms/07-per-window-viewmodels-stateobject-gotcha.md](references/platforms/07-per-window-viewmodels-stateobject-gotcha.md)
   - Uploads, pagination, search, streaming: [references/advanced/01-pagination-live-tail-and-history.md](references/advanced/01-pagination-live-tail-and-history.md) through [references/advanced/08-convex-components-ecosystem.md](references/advanced/08-convex-components-ecosystem.md)
   - Common pitfalls: [references/pitfalls/](references/pitfalls/) (10 docs covering pipeline death, threading, auth, offline traps)
   - Testing: [references/testing/](references/testing/) (mock client, integration, previews, logging, server-side)
8. For a complete example app, read [references/walkthrough/](references/walkthrough/) (chat app from zero).
9. For fast lookup, use [references/quick-reference/](references/quick-reference/) (cheat sheets, decision trees, SQL mapping).
10. Before you answer with confidence, read [references/operations/01-verified-corrections-and-trust-boundaries.md](references/operations/01-verified-corrections-and-trust-boundaries.md) and surface any relevant limitation from [references/operations/02-known-gaps-limitations-and-non-goals.md](references/operations/02-known-gaps-limitations-and-non-goals.md).

## Default Stance
- Prefer Clerk as the default Swift auth path. Use the official `ClerkConvex` package (`clerk-convex-swift >= 0.1.0`) with `clerk-ios >= 1.0.0` and `convex-swift >= 0.8.0`.
- Prefer one `@MainActor` long-lived authenticated client per process, created with `ConvexClientWithAuth(deploymentUrl:authProvider: ClerkConvexAuthProvider())`.
- Prefer `ObservableObject` plus `@StateObject` for subscription-owning models.
- Treat `tokenIdentifier` as the canonical server ownership key, enforced via `convex-helpers` `userQuery`/`userMutation` wrappers.
- Use `AuthView()` and `UserButton()` from `ClerkKitUI` for interactive sign-in and user management. Do not build manual `client.login()` flows.
- Treat the official `WorkoutTracker` sample as the default small-app baseline, not as proof of every production or macOS architecture rule.
- Add `.prefetchClerkImages()` and `.environment(Clerk.shared)` on root views.
- Treat subscriptions as bounded live reads, not endless full-history pipes.
- Treat iOS as reconnecting-online, not offline-first.
- Treat macOS support as Apple Silicon only.
- Target iOS 17+ / macOS 14+ minimum (required by `clerk-convex-swift`).

## Hard Rules
- Do not recommend Convex as the default when offline-first, SQL-heavy, unsupported-platform, or Intel-macOS requirements are real blockers.
- Do not promise optimistic updates, native offline persistence, Catalyst support, watchOS support, tvOS support, or visionOS support.
- Do not use client-passed `userId` values for authorization design.
- Do not use `.filter()` or unbounded `.collect()` as the normal backend query strategy.
- Do not use `Date.now()` in Convex queries.
- Do not store unbounded growing arrays inside one document.
- Do not recommend long-lived view `.task` ownership for important shared live data.
- Do not assume subscription recovery after a terminal failure unless you explicitly rebuild the pipeline.
- Do not repeat stale or corrected claims without checking the operations docs.

## Reference Map
### Start Here
- [references/00-reference-map.md](references/00-reference-map.md): top-level routing and corrected-claim reminders.

### Setup
- [references/setup/01-installing-convex-and-node-prerequisites.md](references/setup/01-installing-convex-and-node-prerequisites.md): Node.js, npm, and Convex CLI setup.
- [references/setup/02-xcode-spm-setup-convexmobile.md](references/setup/02-xcode-spm-setup-convexmobile.md): SPM packages, ClerkKit, ClerkConvex, ConvexMobile.
- [references/setup/03-clerk-account-and-jwt-template-setup.md](references/setup/03-clerk-account-and-jwt-template-setup.md): Clerk dashboard and JWT template.
- [references/setup/04-connecting-clerk-to-convex-auth-config.md](references/setup/04-connecting-clerk-to-convex-auth-config.md): `auth.config.ts` and environment variables.
- [references/setup/05-first-run-npx-convex-dev.md](references/setup/05-first-run-npx-convex-dev.md): first `npx convex dev` run and verification.

### Onboarding
- [references/onboarding/01-why-convex-fits-swiftui.md](references/onboarding/01-why-convex-fits-swiftui.md): why the reactive model feels native in SwiftUI.
- [references/onboarding/02-convex-vs-firebase-vs-supabase.md](references/onboarding/02-convex-vs-firebase-vs-supabase.md): backend decision frame with decision tree and feature matrix.
- [references/onboarding/03-mental-model-live-data-functions-and-state.md](references/onboarding/03-mental-model-live-data-functions-and-state.md): conceptual reset for Convex.
- [references/onboarding/04-adoption-checklist-and-hard-stops.md](references/onboarding/04-adoption-checklist-and-hard-stops.md): go/no-go criteria.

### Backend
- [references/backend/01-schema-document-model-and-relationships.md](references/backend/01-schema-document-model-and-relationships.md): schema and relations.
- [references/backend/02-indexes-query-shaping-and-performance.md](references/backend/02-indexes-query-shaping-and-performance.md): indexes, search, and performance.
- [references/backend/03-queries-mutations-actions-scheduling.md](references/backend/03-queries-mutations-actions-scheduling.md): function taxonomy and safe side effects.
- [references/backend/04-auth-rules-and-server-ownership.md](references/backend/04-auth-rules-and-server-ownership.md): auth boundaries and server ownership.
- [references/backend/05-internal-functions-and-helpers.md](references/backend/05-internal-functions-and-helpers.md): internal functions, `convex-helpers` userQuery/userMutation.
- [references/backend/06-intent-plus-schedule-pattern.md](references/backend/06-intent-plus-schedule-pattern.md): mutation → scheduler → action pattern.
- [references/backend/07-structured-errors-convexerror.md](references/backend/07-structured-errors-convexerror.md): ConvexError, structured payloads, Swift handling.
- [references/backend/08-file-organization-and-naming.md](references/backend/08-file-organization-and-naming.md): project structure and file layout.

### Client SDK
- [references/client-sdk/01-client-surface-runtime-and-auth-bridge.md](references/client-sdk/01-client-surface-runtime-and-auth-bridge.md): public Swift API and auth bridge.
- [references/client-sdk/02-type-system-wire-format-and-modeling.md](references/client-sdk/02-type-system-wire-format-and-modeling.md): model decoding and argument encoding.
- [references/client-sdk/03-subscriptions-errors-logging-and-connection-state.md](references/client-sdk/03-subscriptions-errors-logging-and-connection-state.md): live-read behavior, failures, connection state, and logs.
- [references/client-sdk/04-pipeline-termination-and-recovery.md](references/client-sdk/04-pipeline-termination-and-recovery.md): **critical** — pipeline death after first error + Result-wrapping fix.
- [references/client-sdk/05-websocket-state-and-connection-banner.md](references/client-sdk/05-websocket-state-and-connection-banner.md): connection state banner UI pattern.
- [references/client-sdk/06-debug-logging.md](references/client-sdk/06-debug-logging.md): `initConvexLogging()`, Console.app filtering.
- [references/client-sdk/07-encoding-arguments-convexencodable.md](references/client-sdk/07-encoding-arguments-convexencodable.md): ConvexEncodable, argument dictionaries, optionals.

### SwiftUI
- [references/swiftui/01-consumption-patterns.md](references/swiftui/01-consumption-patterns.md): `.task`, `sink`, `assign`, `switchToLatest`, and Result patterns.
- [references/swiftui/02-observation-and-ownership.md](references/swiftui/02-observation-and-ownership.md): `ObservableObject`, `@StateObject`, `@Observable` guidance and mitigations.
- [references/swiftui/03-lifecycle-navigation-tabs-and-sheets.md](references/swiftui/03-lifecycle-navigation-tabs-and-sheets.md): cancellation and placement rules.
- [references/swiftui/04-environment-injection-and-root-architecture.md](references/swiftui/04-environment-injection-and-root-architecture.md): root ownership and dependency injection.
- [references/swiftui/05-navigation-stack-subscription-lifecycle.md](references/swiftui/05-navigation-stack-subscription-lifecycle.md): push/pop cancellation, `@StateObject` survival.
- [references/swiftui/06-tabview-and-sheet-patterns.md](references/swiftui/06-tabview-and-sheet-patterns.md): tab switch cancellation, sheet subscription lifecycle.
- [references/swiftui/07-loading-error-data-tri-state-pattern.md](references/swiftui/07-loading-error-data-tri-state-pattern.md): Loading/Error/Data enum, skeleton loading, error recovery.

### Authentication
- [references/authentication/01-clerk-first-setup.md](references/authentication/01-clerk-first-setup.md): default auth path.
- [references/authentication/02-custom-auth-provider-and-firebase-fallback.md](references/authentication/02-custom-auth-provider-and-firebase-fallback.md): custom provider contract and Firebase fallback.
- [references/authentication/03-sign-in-with-apple-keychain-and-session-restoration.md](references/authentication/03-sign-in-with-apple-keychain-and-session-restoration.md): SIWA, Keychain, and cached-session restore.

### Platforms
- [references/platforms/01-ios-backgrounding-reconnection-and-staleness.md](references/platforms/01-ios-backgrounding-reconnection-and-staleness.md): POSIX error 53, background/foreground sequence, scenePhase detection.
- [references/platforms/02-offline-behavior-network-transitions-and-recovery.md](references/platforms/02-offline-behavior-network-transitions-and-recovery.md): offline limits, four-state UX model, staleness detection.
- [references/platforms/03-performance-battery-and-threading.md](references/platforms/03-performance-battery-and-threading.md): performance, power, and threading rules.
- [references/platforms/04-macos-multi-window-menu-bar-and-support-limits.md](references/platforms/04-macos-multi-window-menu-bar-and-support-limits.md): multi-window, menu bar, App Nap, and support matrix.
- [references/platforms/05-nwpathmonitor-network-awareness.md](references/platforms/05-nwpathmonitor-network-awareness.md): NWPathMonitor integration and network-aware UI.
- [references/platforms/06-binary-size-and-instruments-profiling.md](references/platforms/06-binary-size-and-instruments-profiling.md): XCFramework size impact, Instruments profiling.
- [references/platforms/07-per-window-viewmodels-stateobject-gotcha.md](references/platforms/07-per-window-viewmodels-stateobject-gotcha.md): macOS per-window `@StateObject` ownership.

### Advanced
- [references/advanced/01-pagination-live-tail-and-history.md](references/advanced/01-pagination-live-tail-and-history.md): latest-N plus paginated history.
- [references/advanced/02-file-storage-upload-download-and-document-ids.md](references/advanced/02-file-storage-upload-download-and-document-ids.md): upload flow, storage access, and IDs.
- [references/advanced/03-testing-debugging-and-observability.md](references/advanced/03-testing-debugging-and-observability.md): testing overview (see also `testing/` for deep docs).
- [references/advanced/04-streaming-workloads-and-transcription.md](references/advanced/04-streaming-workloads-and-transcription.md): streaming writes and transcription workloads.
- [references/advanced/05-image-upload-photospicker-asyncimage.md](references/advanced/05-image-upload-photospicker-asyncimage.md): PhotosPicker → upload → AsyncImage flow.
- [references/advanced/06-full-text-search-reactive.md](references/advanced/06-full-text-search-reactive.md): search indexes and reactive search queries.
- [references/advanced/07-subscription-deduplication-and-fan-out.md](references/advanced/07-subscription-deduplication-and-fan-out.md): `.removeDuplicates()`, fan-out, subscription efficiency.
- [references/advanced/08-convex-components-ecosystem.md](references/advanced/08-convex-components-ecosystem.md): aggregate, rate-limiter, and other Convex components.

### Pitfalls
- [references/pitfalls/01-pipeline-dies-after-first-error.md](references/pitfalls/01-pipeline-dies-after-first-error.md): **#1 pitfall** — `.replaceError` kills the stream.
- [references/pitfalls/02-forgetting-receive-on-main.md](references/pitfalls/02-forgetting-receive-on-main.md): missing `.receive(on: DispatchQueue.main)`.
- [references/pitfalls/03-unbounded-collect-bandwidth-bomb.md](references/pitfalls/03-unbounded-collect-bandwidth-bomb.md): `.collect()` without limits.
- [references/pitfalls/04-arrays-as-fields-8192-limit.md](references/pitfalls/04-arrays-as-fields-8192-limit.md): document array size limits.
- [references/pitfalls/05-date-now-in-queries-breaks-reactivity.md](references/pitfalls/05-date-now-in-queries-breaks-reactivity.md): `Date.now()` in queries.
- [references/pitfalls/06-calling-actions-directly-for-side-effects.md](references/pitfalls/06-calling-actions-directly-for-side-effects.md): action misuse.
- [references/pitfalls/07-trusting-client-for-authorization.md](references/pitfalls/07-trusting-client-for-authorization.md): client-passed userId.
- [references/pitfalls/08-observable-macro-re-init-trap.md](references/pitfalls/08-observable-macro-re-init-trap.md): `@Observable` init side effects.
- [references/pitfalls/09-task-modifier-cancels-on-navigation.md](references/pitfalls/09-task-modifier-cancels-on-navigation.md): `.task` cancellation.
- [references/pitfalls/10-no-offline-no-optimistic-updates.md](references/pitfalls/10-no-offline-no-optimistic-updates.md): offline and optimistic update limits.

### Walkthrough
- [references/walkthrough/01-from-zero-to-realtime-chat-app.md](references/walkthrough/01-from-zero-to-realtime-chat-app.md): complete chat app overview.
- [references/walkthrough/02-complete-schema-and-backend-code.md](references/walkthrough/02-complete-schema-and-backend-code.md): full schema + TypeScript backend.
- [references/walkthrough/03-complete-swift-models-and-viewmodels.md](references/walkthrough/03-complete-swift-models-and-viewmodels.md): Swift models + ViewModels.
- [references/walkthrough/04-complete-swiftui-views.md](references/walkthrough/04-complete-swiftui-views.md): SwiftUI views.
- [references/walkthrough/05-deployment-checklist.md](references/walkthrough/05-deployment-checklist.md): production deployment checklist.

### Quick Reference
- [references/quick-reference/01-convex-backend-quick-reference-card.md](references/quick-reference/01-convex-backend-quick-reference-card.md): backend patterns cheat sheet.
- [references/quick-reference/02-swift-sdk-api-cheat-sheet.md](references/quick-reference/02-swift-sdk-api-cheat-sheet.md): Swift SDK API surface.
- [references/quick-reference/03-sql-to-convex-mapping-table.md](references/quick-reference/03-sql-to-convex-mapping-table.md): SQL → Convex translation.
- [references/quick-reference/04-function-decision-tree.md](references/quick-reference/04-function-decision-tree.md): query/mutation/action decision tree.
- [references/quick-reference/05-subscription-placement-decision-matrix.md](references/quick-reference/05-subscription-placement-decision-matrix.md): where to place subscriptions.

### Testing
- [references/testing/01-mock-ffi-client-unit-testing.md](references/testing/01-mock-ffi-client-unit-testing.md): mock FFI client for unit tests.
- [references/testing/02-integration-testing-with-test-deployment.md](references/testing/02-integration-testing-with-test-deployment.md): integration tests with test deployment.
- [references/testing/03-swiftui-preview-with-mock-client.md](references/testing/03-swiftui-preview-with-mock-client.md): SwiftUI previews with mock data.
- [references/testing/04-oslog-and-console-app-filtering.md](references/testing/04-oslog-and-console-app-filtering.md): OSLog and Console.app.
- [references/testing/05-server-side-testing-with-convex-test.md](references/testing/05-server-side-testing-with-convex-test.md): server-side testing with `convex-test`.

### Playbooks
- [references/playbooks/01-greenfield-swiftui-app-playbook.md](references/playbooks/01-greenfield-swiftui-app-playbook.md): default build order for a new app.
- [references/playbooks/02-shared-ios-macos-app-playbook.md](references/playbooks/02-shared-ios-macos-app-playbook.md): shared iPhone + Mac app guidance.
- [references/playbooks/03-streaming-and-transcription-playbook.md](references/playbooks/03-streaming-and-transcription-playbook.md): streaming and transcription build order.

### Operations
- [references/operations/01-verified-corrections-and-trust-boundaries.md](references/operations/01-verified-corrections-and-trust-boundaries.md): corrected or nuanced claims from the corpus.
- [references/operations/02-known-gaps-limitations-and-non-goals.md](references/operations/02-known-gaps-limitations-and-non-goals.md): current gaps and explicit non-goals.
