# Adoption Checklist And Hard Stops

## Use This When
- Deciding whether Convex + Clerk is a fit before designing implementation details.
- Surfacing product mismatches early.
- Turning enthusiasm into explicit go/no-go criteria.

## Required Checks
- Confirm the team is willing to write backend logic in TypeScript (including `convex-helpers` for user-guarded function wrappers).
- Confirm Clerk is acceptable as the default auth path, including:
  - The official `ClerkConvex` bridge package (`clerk-convex-swift >= 0.1.0`).
  - `ClerkKit` and `ClerkKitUI` from `clerk-ios >= 1.0.0` for `AuthView()`, `UserButton()`, and session management.
  - Clerk-owned interactive auth UX (Sign in with Apple, email, social methods via `AuthView()`).
  - Or there is explicit appetite to own a custom `AuthProvider`.
- Confirm `convex-swift >= 0.8.0` is acceptable (required for `onIdToken` callback model in `AuthProvider`).
- Confirm iOS 17+ / macOS 14+ minimum deployment targets are acceptable (required by `clerk-convex-swift`).
- Confirm whether the product can start with the official example's direct `tokenIdentifier` ownership model or already needs a richer `users` table and membership modeling.
- Confirm iOS can be treated as reconnecting-online, not offline-first.
- Confirm Apple Silicon-only macOS support is acceptable if shipping on Mac.
- Confirm missing Swift SDK features such as optimistic updates do not break the product concept.

## Hard Stops
- Offline-first product requirements.
- SQL-heavy backend needs, complex reporting, or query patterns that depend on broad relational power.
- Intel Mac distribution requirements.
- watchOS, tvOS, visionOS, Mac Catalyst, or other unsupported Apple platform requirements.
- A team that cannot or will not maintain TypeScript backend code.
- A product that needs broad regional deployment beyond the currently documented Convex regions.

## Yellow Flags
- Large binary-size sensitivity.
- Heavy file-upload UX expectations; Swift uses upload URL workflows instead of a high-level SDK API.
- Products that need very high community support volume, many public examples, or mature third-party libraries.
- Streaming workloads that could explode bandwidth if modeled naively.

## Green Flags
- Realtime collaboration, chat, dashboards, operator tools, and live feeds.
- SwiftUI teams that want the backend to feel state-driven instead of endpoint-driven.
- Apps that benefit from one subscription model spanning current data and future updates.
- Teams already considering Clerk and willing to accept Apple-platform caveats.

## Decision Rule
- If any hard stop is real, do not position Convex as the default.
- If only yellow flags apply, continue only with an explicit mitigation plan.
- If the product is strongly realtime and the hard stops are absent, Convex is a reasonable default candidate.

## Read Next
- [02-convex-vs-firebase-vs-supabase.md](02-convex-vs-firebase-vs-supabase.md)
- [../operations/02-known-gaps-limitations-and-non-goals.md](../operations/02-known-gaps-limitations-and-non-goals.md)
- [../playbooks/01-greenfield-swiftui-app-playbook.md](../playbooks/01-greenfield-swiftui-app-playbook.md)
