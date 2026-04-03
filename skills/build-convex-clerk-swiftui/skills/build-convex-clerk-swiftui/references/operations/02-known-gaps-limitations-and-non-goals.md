# Known Gaps, Limitations, And Non-Goals

## Use This When
- Deciding whether to recommend Convex for a specific Apple-platform product.
- Writing a plan that must acknowledge unsupported or immature parts of the stack.
- Reviewing a design for hidden product-risk mismatches.

## Product-Shaping Gaps
- No built-in offline persistence in the Swift SDK.
- No current optimistic-update support in the Swift SDK.
- File upload from Swift relies on upload URLs plus `URLSession`, not a polished native storage client API.
- Pagination exists, but there is no first-class Swift helper equivalent to richer JS ergonomics.

## Platform Gaps
- No Intel macOS support in the checked XCFramework.
- No Mac Catalyst, watchOS, tvOS, or visionOS support.
- iOS backgrounding still suspends the app and kills the websocket; Convex reconnects on foreground, but it does not bypass OS rules.

## Ecosystem Gaps
- The Swift SDK ecosystem is early and documentation is thin relative to the JS ecosystem.
- Public example coverage is limited, especially around advanced patterns.
- Teams should expect to read source, research issues, and rely on Discord or direct investigation more than with Firebase.

## Backend Capability Gaps
- No SQL, broad relational query language, or drop-in substitute for heavy analytics/reporting workflows.
- No broad `OR`/`IN` style indexed query flexibility.
- Search has meaningful constraints and is not a generic database-query replacement.
- Full-result re-send behavior can turn naive live lists into bandwidth issues.

## Non-Goals For This Skill
- Do not pretend Convex is the best fit for every Swift app.
- Do not promise unsupported Apple platforms or Intel Mac distribution.
- Do not present an offline-first architecture unless the design adds an explicit companion local layer.
- Do not hide that adopting Convex also means adopting a TypeScript backend.

## Mitigation Mindset
- Mitigate yellow flags explicitly.
- Escalate hard blockers early.
- Prefer alternative backends when the product shape fundamentally conflicts with these limits.

## Read Next
- [../onboarding/04-adoption-checklist-and-hard-stops.md](../onboarding/04-adoption-checklist-and-hard-stops.md)
- [../platforms/04-macos-multi-window-menu-bar-and-support-limits.md](../platforms/04-macos-multi-window-menu-bar-and-support-limits.md)
- [../advanced/04-streaming-workloads-and-transcription.md](../advanced/04-streaming-workloads-and-transcription.md)
