# Convex vs Firebase vs Supabase

## Use This When
- Choosing a backend for a SwiftUI app.
- Explaining tradeoffs honestly to a team that already knows Firebase or Supabase.
- Deciding whether Convex's strengths matter more than its gaps for the current product.

## The Short Version
- Choose Convex when the app's primary value is live, reactive data that should flow into SwiftUI with minimal client-side glue.
- Choose Firebase when offline-first behavior and mature native-mobile ecosystem support are hard requirements.
- Choose Supabase when SQL, Postgres tooling, complex relational queries, or advanced filtering dominate the workload.

## Where Convex Wins
- One subscription model instead of separate initial-fetch and realtime channels.
- A Swift SDK that already speaks Combine and `AsyncSequence`.
- A backend model organized around queries, mutations, actions, and internal functions instead of ad hoc endpoints.
- Server-driven reactive invalidation that removes client cache merge code.
- Strong fit for SwiftUI teams who want the backend to feel like a continuation of state-driven UI.

## Where Firebase Wins
- Built-in offline persistence and queued local writes.
- Larger iOS ecosystem, more examples, and broader operational precedent.
- Better fit when planes, tunnels, or intermittent connectivity are core product requirements.
- Better fit when you need mature support across more Apple platforms without current Convex limitations.

## Where Supabase Wins
- PostgreSQL and SQL are first-class, not approximated.
- Better fit for `OR` queries, relational reporting, and query patterns that Convex explicitly does not optimize for.
- Broader Swift ecosystem adoption and more conventional backend expectations.
- Easier sell when the team already thinks in tables, joins, and SQL-admin workflows.

## Convex Hard Limits That Matter In Selection
- No built-in offline persistence.
- No SQL or true relational query language.
- No current optimistic-update support in the Swift SDK.
- File upload from Swift uses a workaround flow rather than a polished native client API.
- Apple-platform support is incomplete: no Intel macOS slice, no watchOS, tvOS, visionOS, or Catalyst support.

## Decision Tree

```
Does your app need to work offline (planes, subways, poor signal)?
├── YES → Firebase (built-in offline persistence)
│         Convex has NO offline support.
└── NO  → continue

Does your app need complex SQL queries (JOINs, GROUP BY, analytics)?
├── YES → Supabase (full PostgreSQL)
│         Convex has no SQL, no JOINs, no GROUP BY.
└── NO  → continue

Does your app need real-time data that multiple users see simultaneously?
├── YES → Convex is built for this. One subscription = always-current data.
│         Firebase requires manual listener management.
│         Supabase requires separate fetch + listen + merge.
└── NO  → Any backend works. Choose by team familiarity.

Are you building for Intel Mac, watchOS, tvOS, or visionOS?
├── YES → Firebase or Supabase (Convex is arm64-only, iOS/macOS only)
└── NO  → continue

Do you want Combine-native reactive data in SwiftUI?
├── YES → Convex — subscribe() returns AnyPublisher directly
└── NO  → Any backend works.
```

## Feature Matrix

| Feature | Convex | Firebase | Supabase |
|---|---|---|---|
| Reactive subscriptions | Native Combine publisher | Callback-based | Separate HTTP + WebSocket |
| Type safety | Compiler-checked generics | `[String: Any]` | Partial |
| Transactions | Every mutation (automatic) | Explicit, limited | PostgreSQL ACID |
| Auth (Swift) | Clerk (official package) | Built-in Firebase Auth | Built-in Supabase Auth |
| Offline | None | Automatic disk cache | Limited beta |
| SQL | None | None | Full PostgreSQL |
| File storage | URLSession workaround | SDK method | SDK method |
| Apple platforms | iOS, macOS (arm64) | iOS, macOS, watchOS, tvOS | iOS, macOS, watchOS, tvOS |
| Backend functions | TypeScript in `/convex` | Cloud Functions | Edge Functions |

## Scenario-Based Recommendations

| Your App | Best Choice | Why |
|---|---|---|
| Real-time chat/collaboration | Convex | One subscription, auto-current data, ACID mutations |
| Offline-first field app | Firebase | Built-in disk cache, write queue, sync-on-reconnect |
| Analytics dashboard | Supabase | Full SQL, GROUP BY, window functions |
| Sharing existing Convex web backend | Convex Swift | Zero server work, same queries/mutations |
| watchOS companion | Firebase/Supabase | Convex has no watchOS support |
| Intel Mac App Store | Firebase/Supabase | Convex only builds arm64 |
| Simple CRUD (no real-time) | Any | Choose by team familiarity |

## Decision Rules
- Prefer Convex for live query-driven products where the SwiftUI integration model matters every day.
- Prefer Firebase when product reliability offline matters more than reactive elegance.
- Prefer Supabase when backend query power is the dominant constraint.
- If two or more Convex hard limits are product blockers, stop trying to force Convex.

## Messaging Guidance
- Describe Convex as a better fit for a specific kind of SwiftUI product, not as a universally better backend.
- Present Firebase and Supabase as legitimate alternatives, not strawmen.
- Call out the ecosystem maturity gap and platform support limitations in the same conversation as the benefits.

## Read Next
- [01-why-convex-fits-swiftui.md](01-why-convex-fits-swiftui.md)
- [04-adoption-checklist-and-hard-stops.md](04-adoption-checklist-and-hard-stops.md)
- [../operations/02-known-gaps-limitations-and-non-goals.md](../operations/02-known-gaps-limitations-and-non-goals.md)
