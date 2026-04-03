# Pagination, Live Tail, And History

## Use This When
- Building large feeds, chat histories, logs, or transcript timelines.
- Preventing wide live subscriptions from becoming bandwidth problems.
- Working around current Swift pagination ergonomics.

## Default Strategy
- Keep a small live tail as the reactive subscription.
- Fetch older history through paginated queries or explicit workaround flows.
- Treat "latest live" and "older history" as different concerns.

## Why This Matters
- Convex re-sends the full query result on invalidation.
- A giant live list becomes expensive even if each item is small.
- Latest-N live data plus paginated history is the safest default for mobile performance.

## Swift Reality
- The corpus does not describe a public one-shot `query()` helper in the current Swift SDK.
- Action-backed pagination workarounds may be necessary, but they are workarounds, not the core Convex ideal.
- Be explicit when a design uses workaround mechanics instead of first-class SDK ergonomics.

## UI Guidance
- Trigger history loads from scroll position or explicit user intent.
- Keep the live tail bounded and stable.
- Do not let the existence of pagination justify an oversized live subscription.

## Avoid
- One giant subscription for all history.
- Confusing helper-library limitations with core Convex behavior.
- Hiding that some pagination ergonomics are thinner on Swift than on JS.

## Read Next
- [04-streaming-workloads-and-transcription.md](04-streaming-workloads-and-transcription.md)
- [../backend/02-indexes-query-shaping-and-performance.md](../backend/02-indexes-query-shaping-and-performance.md)
- [../playbooks/03-streaming-and-transcription-playbook.md](../playbooks/03-streaming-and-transcription-playbook.md)
