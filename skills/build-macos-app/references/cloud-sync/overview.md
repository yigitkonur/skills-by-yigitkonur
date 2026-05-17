# Cloud Sync Reference Map

## Use This Corpus For
- Designing the Swift client side of a Convex + Clerk app that includes a macOS target.
- Deciding whether Convex fits the product before implementation.
- Selecting production-safe client, auth, lifecycle, backend, and platform patterns for the current Swift SDK.
- Loading the narrowest reference needed instead of pulling the full cloud-sync corpus into context.

## Source Boundary
- Ground broad product and architecture guidance in the repo-local references listed below.
- Treat Clerk-specific implementation facts as verified against the official `clerk-convex-swift` package, Clerk docs, GitHub tags, and the `Example/WorkoutTracker` sample where those files say so.
- Treat this reference set as opinionated toward the latest checked 2026-05-09 source snapshot: `clerk-convex-swift 0.1.0`, `clerk-ios 1.1.2`, and ConvexMobile `0.8.1`.
- Present ecosystem and feature gaps honestly. Do not market around them.

## Start Here
1. Fit check: [adoption-checklist.md](adoption-checklist.md), [onboarding/convex-vs-alternatives.md](onboarding/convex-vs-alternatives.md), [limitations.md](limitations.md).
2. Mental model: [onboarding/mental-model.md](onboarding/mental-model.md), [onboarding/why-convex-fits-swiftui.md](onboarding/why-convex-fits-swiftui.md).
3. Setup path: [setup-extra/node-prerequisites.md](setup-extra/node-prerequisites.md), [spm-setup.md](spm-setup.md), [setup-extra/first-run.md](setup-extra/first-run.md).
4. Clerk path: [setup-extra/clerk-jwt-template.md](setup-extra/clerk-jwt-template.md), [setup-extra/auth-config-wiring.md](setup-extra/auth-config-wiring.md), [clerk-setup.md](clerk-setup.md), [sign-in-with-apple.md](sign-in-with-apple.md).
5. Trust boundary: [operations/verified-corrections.md](operations/verified-corrections.md), [backend/auth-rules-and-server-ownership.md](backend/auth-rules-and-server-ownership.md).

## Current Subdirectories
- `onboarding/`: backend fit, alternatives, and mental model.
- `setup-extra/`: Node, Clerk JWT template, Convex auth config, and first run sequence.
- `backend/`: server ownership and structured error behavior.
- `client-sdk-extra/`: wire types, `ConvexEncodable`, subscription errors, and debug logging.
- `platforms/`: iOS/macOS lifecycle caveats, NWPathMonitor, binary size, performance, and threading.
- `pitfalls-extra/`: production failure modes that need quick lookup.
- `quick-reference/`: backend card, function decision tree, and subscription placement matrix.
- `playbooks/`: greenfield, shared iOS/macOS, and streaming/transcription implementation paths.
- `swiftui-extra/`: navigation stack, tab, and sheet lifecycle extensions.
- `walkthrough/`: complete chat app sequence.

Top-level cloud-sync files cover macOS app entry, root architecture, per-window models, observation, reactive queries, loading/error UI, connection banners, offline states, pipeline recovery, SPM setup, Clerk setup, SIWA, SDK cheat sheets, and known limitations.

## Fast Routing By Problem
- Backend fit or alternatives: [onboarding/convex-vs-alternatives.md](onboarding/convex-vs-alternatives.md), [adoption-checklist.md](adoption-checklist.md), [operations/known-gaps.md](operations/known-gaps.md).
- Setup from scratch: [setup-extra/node-prerequisites.md](setup-extra/node-prerequisites.md), [spm-setup.md](spm-setup.md), [setup-extra/clerk-jwt-template.md](setup-extra/clerk-jwt-template.md), [setup-extra/auth-config-wiring.md](setup-extra/auth-config-wiring.md), [setup-extra/first-run.md](setup-extra/first-run.md).
- SwiftUI architecture: [root-architecture.md](root-architecture.md), [observation-ownership.md](observation-ownership.md), [reactive-queries.md](reactive-queries.md), [lifecycle-navigation.md](lifecycle-navigation.md).
- macOS lifecycle: [macos-app-entry.md](macos-app-entry.md), [per-window-viewmodels.md](per-window-viewmodels.md), [swiftui-extra/navstack-subscription-lifecycle.md](swiftui-extra/navstack-subscription-lifecycle.md), [swiftui-extra/tabview-and-sheets.md](swiftui-extra/tabview-and-sheets.md).
- Clerk auth: [clerk-setup.md](clerk-setup.md), [auth-custom-provider.md](auth-custom-provider.md), [sign-in-with-apple.md](sign-in-with-apple.md), [backend/auth-rules-and-server-ownership.md](backend/auth-rules-and-server-ownership.md).
- Subscription failures and recovery: [client-sdk-extra/subscriptions-and-errors.md](client-sdk-extra/subscriptions-and-errors.md), [pipeline-recovery.md](pipeline-recovery.md), [pitfall-pipeline-dies.md](pitfall-pipeline-dies.md).
- Loading, offline, and connection UX: [loading-error-tristate.md](loading-error-tristate.md), [connection-banner.md](connection-banner.md), [offline-ux-states.md](offline-ux-states.md), [platforms/nwpathmonitor.md](platforms/nwpathmonitor.md).
- Wire types and SDK surface: [client-surface.md](client-surface.md), [client-sdk-extra/type-system-and-modeling.md](client-sdk-extra/type-system-and-modeling.md), [client-sdk-extra/convex-encodable.md](client-sdk-extra/convex-encodable.md), [swift-sdk-cheatsheet.md](swift-sdk-cheatsheet.md).
- Common pitfalls: [pitfalls-extra/actions-as-side-effects.md](pitfalls-extra/actions-as-side-effects.md), [pitfalls-extra/arrays-8192-limit.md](pitfalls-extra/arrays-8192-limit.md), [pitfalls-extra/date-now-in-queries.md](pitfalls-extra/date-now-in-queries.md), [pitfalls-extra/receive-on-main.md](pitfalls-extra/receive-on-main.md), [pitfalls-extra/trusting-client-for-auth.md](pitfalls-extra/trusting-client-for-auth.md), [pitfalls-extra/unbounded-collect.md](pitfalls-extra/unbounded-collect.md).
- Implementation paths: [playbooks/greenfield-swiftui-app.md](playbooks/greenfield-swiftui-app.md), [playbooks/shared-ios-macos-app.md](playbooks/shared-ios-macos-app.md), [playbooks/streaming-and-transcription.md](playbooks/streaming-and-transcription.md).
- Complete example: [walkthrough/01-zero-to-realtime-chat.md](walkthrough/01-zero-to-realtime-chat.md), [walkthrough/02-schema-and-backend-code.md](walkthrough/02-schema-and-backend-code.md), [walkthrough/03-swift-models-and-viewmodels.md](walkthrough/03-swift-models-and-viewmodels.md), [walkthrough/04-swiftui-views.md](walkthrough/04-swiftui-views.md), [walkthrough/05-deployment-checklist.md](walkthrough/05-deployment-checklist.md).

## Non-Negotiable Defaults
- Prefer Clerk as the default Swift auth path.
- Prefer one long-lived authenticated client per process.
- Treat subscription errors as terminal unless the pipeline is explicitly rebuilt.
- Treat Swift SDK networking as reconnecting-online, not offline-first.
- Treat macOS support as Apple Silicon only for the ConvexMobile path.
- Use [operations/verified-corrections.md](operations/verified-corrections.md) before repeating version, support, or trust-boundary claims.
