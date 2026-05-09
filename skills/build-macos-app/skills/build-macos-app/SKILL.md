---
name: build-macos-app
description: Use skill if you are building, auditing, or shipping a production-grade macOS SwiftUI or AppKit app needing HIG compliance, Liquid Glass design, snapshot validation, SwiftLint/SwiftFormat hooks, or Convex+Clerk cloud sync.
---

# Build macOS App

Build, audit, or ship native macOS SwiftUI/AppKit apps with HIG compliance, Liquid Glass visual treatment, expectation-first visual validation, Swift quality hooks, and optional Convex + Clerk cloud sync.

Keep this file as the spine. Load references only for the branch being executed.

## Trigger Boundary

Use this skill for:

- Native macOS app work: new app scaffolds, feature implementation, redesigns, audits, migrations, release prep, or quality setup.
- SwiftUI/AppKit projects with `*.xcodeproj`, `*.xcworkspace`, `Package.swift`, or Swift files that include a macOS app target.
- macOS UI concerns: menus, keyboard shortcuts, windows, sidebars, toolbars, settings, accessibility, HIG conformance, Liquid Glass, snapshots, SwiftLint, SwiftFormat, or pre-commit hooks.
- Multi-platform Apple repos only when a macOS target exists.
- Convex + Clerk Swift client work when the app has a macOS surface.

Do NOT use this skill for:

- iOS-only, iPadOS-only, visionOS-only, watchOS-only, or tvOS-only work without a macOS target.
- Generic Swift package work with no app, UI, or macOS surface.
- Pure server-side Convex, TypeScript, or backend-only work.
- Non-Apple Swift on Linux or server-side Swift.
- Browser automation or web snapshot testing; route those to browser or Playwright skills.

Quality-hook platform references for iOS, tvOS, watchOS, and visionOS exist only for multi-platform Apple repos that also include macOS. They are not standalone triggers.

## Platform Stance

| Scope | Rule |
|---|---|
| Primary scope | Native macOS SwiftUI/AppKit apps. |
| Multi-platform repos | In scope only when a macOS target exists. |
| Out of scope | iOS-only, iPadOS-only, visionOS-only, watchOS-only, tvOS-only, non-Apple Swift, and pure server-side Convex. |
| Liquid Glass target | macOS 26+ with the Xcode 26 SDK. |
| Backward-compatible target | macOS 14+ with availability guards where Liquid Glass or Clerk paths require them. |
| Clerk + Convex path | Apple Silicon macOS only per current ConvexMobile limitations. |

## HIG vs Liquid Glass

| Decision | Apply |
|---|---|
| Interaction, menus, windows, keyboard shortcuts, settings, accessibility, typography, spacing, and standard controls | HIG is always the baseline. |
| macOS 26 / Tahoe-era visual treatment for navigation, chrome, toolbars, sidebars, floating controls, sheets, popovers, and overlays | Liquid Glass may apply after HIG is satisfied. |
| Content rows, text, tables, form fields, cards, and data surfaces | Never apply glass. Keep content readable and semantically styled. |
| macOS 14/15 support | Gate Liquid Glass APIs with `#available(macOS 26, *)`; provide `NSVisualEffectView` or standard SwiftUI fallbacks. |

## Operations

Detect the operation from the user's request, then load the narrowest reference set.

| Operation | Trigger | Route |
|---|---|---|
| Bootstrap | New macOS app or first production scaffold | [references/workflow/bootstrap-new-app.md](references/workflow/bootstrap-new-app.md) |
| Build | Add a screen, view, app feature, command, or window behavior | Apply Three Questions, then route by subsystem below |
| Redesign | Make it native, Apple-like, Tahoe-ready, or Liquid Glass | [references/liquid-glass/design-diagnosis.md](references/liquid-glass/design-diagnosis.md) |
| Audit | Review, assess, find issues, or preflight quality | [references/workflow/audit-existing.md](references/workflow/audit-existing.md) |
| Migrate | Pre-Tahoe code moving to macOS 26 | [references/liquid-glass/migration-guide.md](references/liquid-glass/migration-guide.md) |
| Install hooks | SwiftLint, SwiftFormat, pre-commit, or CI quality setup | [references/quality-hooks/hook-architecture.md](references/quality-hooks/hook-architecture.md) |
| Add visual tests | Screenshot validation or snapshot harness | [references/visual-validation/snapshot-testing-spm.md](references/visual-validation/snapshot-testing-spm.md) |
| Wire cloud sync | Convex, Clerk, real-time queries, subscriptions, or auth-gated data | [references/cloud-sync/overview.md](references/cloud-sync/overview.md) |
| Ship | Release checklist or final app-store/direct-distribution pass | [references/workflow/ship-checklist.md](references/workflow/ship-checklist.md) |

If the requested operation is ambiguous, make the smallest reasonable assumption and proceed.

## Core Guardrails

### Three Laws Of macOS UI

1. Every action must be reachable from the menu bar; toolbars are optional chrome. See [references/hig/components/menus.md](references/hig/components/menus.md).
2. Standard keyboard shortcuts are reserved: `Cmd-N/O/S/Shift-S/Z/Shift-Z/Q/W/Comma/F/A/C/V/X`. See [references/hig/platform/keyboard-shortcuts.md](references/hig/platform/keyboard-shortcuts.md).
3. Settings take effect immediately. No Save, Cancel, or Apply buttons in preferences. See [references/hig/components/menus.md](references/hig/components/menus.md).

### Three Questions Before Any View

1. Is this navigation or content?
2. What is the one primary action?
3. Would this feel native beside Finder, Mail, Photos, or Settings?

Critical audit findings:

| Finding | Route |
|---|---|
| Glass on content, list rows, cards, table cells, or text | [references/liquid-glass/design-principles.md](references/liquid-glass/design-principles.md) |
| Multiple tinted primary actions on one screen | [references/liquid-glass/design-principles.md](references/liquid-glass/design-principles.md) |
| Hardcoded colors, fixed font sizes, iOS-scale rows, or custom dark-mode toggles | [references/hig/foundations/color-and-dark-mode.md](references/hig/foundations/color-and-dark-mode.md), [references/hig/foundations/typography.md](references/hig/foundations/typography.md) |
| `NavigationView`, missing `Settings`, missing commands, custom window chrome, or missing shortcuts | [references/hig/platform/windows.md](references/hig/platform/windows.md), [references/hig/platform/toolbars.md](references/hig/platform/toolbars.md), [references/liquid-glass/design-diagnosis.md](references/liquid-glass/design-diagnosis.md) |
| AppKit/SwiftUI ceiling confusion | [references/liquid-glass/appkit-bridging.md](references/liquid-glass/appkit-bridging.md), [references/hig/practitioner-insights.md](references/hig/practitioner-insights.md) |

## HIG Reference Routing

| Need | Read |
|---|---|
| Color, dark mode, semantic colors, and layer adaptation | [references/hig/foundations/color-and-dark-mode.md](references/hig/foundations/color-and-dark-mode.md) |
| Typography, weights, SF Pro Text vs Display | [references/hig/foundations/typography.md](references/hig/foundations/typography.md) |
| Spacing, alignment, 8pt grid, control size decisions | [references/hig/foundations/layout-spacing.md](references/hig/foundations/layout-spacing.md) |
| Icons, app icons, SF Symbols, animation | [references/hig/foundations/icons-and-sf-symbols.md](references/hig/foundations/icons-and-sf-symbols.md) |
| Materials, vibrancy, `.behindWindow`, `.withinWindow` | [references/hig/foundations/materials-and-vibrancy.md](references/hig/foundations/materials-and-vibrancy.md) |
| Motion timing, springs, Reduce Motion | [references/hig/foundations/motion.md](references/hig/foundations/motion.md) |
| Buttons and button hierarchy | [references/hig/components/buttons.md](references/hig/components/buttons.md) |
| Text fields, search fields, labels, validation | [references/hig/components/text-inputs.md](references/hig/components/text-inputs.md) |
| Pickers, sliders, steppers, toggles, checkboxes | [references/hig/components/selection-controls.md](references/hig/components/selection-controls.md) |
| Menus, menu bar, contextual menus, Services | [references/hig/components/menus.md](references/hig/components/menus.md) |
| Popovers, tooltips, disclosure, inspectors | [references/hig/components/popovers-and-disclosure.md](references/hig/components/popovers-and-disclosure.md) |
| Tables, lists, outlines, collection views | [references/hig/components/tables-and-lists.md](references/hig/components/tables-and-lists.md) |
| Alerts, sheets, dialogs, destructive actions | [references/hig/components/alerts-and-sheets.md](references/hig/components/alerts-and-sheets.md) |
| Windows, restoration, tabbing, traffic lights | [references/hig/platform/windows.md](references/hig/platform/windows.md) |
| Sidebars, split views, source lists, inspectors | [references/hig/platform/sidebars-and-split-views.md](references/hig/platform/sidebars-and-split-views.md) |
| Toolbars, title bars, customization | [references/hig/platform/toolbars.md](references/hig/platform/toolbars.md) |
| Keyboard shortcuts, focus, Escape hierarchy | [references/hig/platform/keyboard-shortcuts.md](references/hig/platform/keyboard-shortcuts.md) |
| Drag/drop, pasteboard, file promises, documents | [references/hig/platform/drag-drop-files.md](references/hig/platform/drag-drop-files.md) |
| Accessibility, VoiceOver, contrast, motion | [references/hig/technologies/accessibility.md](references/hig/technologies/accessibility.md) |
| Widgets, notifications, Spotlight, MenuBarExtra | [references/hig/technologies/widgets-and-notifications.md](references/hig/technologies/widgets-and-notifications.md) |
| Practitioner overrides and common real-world judgment calls | [references/hig/practitioner-insights.md](references/hig/practitioner-insights.md) |

## Liquid Glass Routing

| Need | Read |
|---|---|
| SwiftUI and AppKit API surface | [references/liquid-glass/api-reference.md](references/liquid-glass/api-reference.md) |
| Navigation/content divide, concentricity, tint hierarchy | [references/liquid-glass/design-principles.md](references/liquid-glass/design-principles.md) |
| Deprecated APIs, smell catalog, audit heuristics | [references/liquid-glass/design-diagnosis.md](references/liquid-glass/design-diagnosis.md) |
| Toolbar, sidebar, window, Settings recipes | [references/liquid-glass/macos-patterns.md](references/liquid-glass/macos-patterns.md) |
| Pre-Tahoe migration sequence | [references/liquid-glass/migration-guide.md](references/liquid-glass/migration-guide.md) |
| Known bugs, crashes, and workarounds | [references/liquid-glass/pitfalls-and-solutions.md](references/liquid-glass/pitfalls-and-solutions.md) |
| AppKit and SwiftUI bridge choices | [references/liquid-glass/appkit-bridging.md](references/liquid-glass/appkit-bridging.md) |

Liquid Glass references carry WWDC 2025 session context. Do not duplicate session lists in the spine.

## Visual Validation Routing

Expectation-first discipline is separate from the pixel-diff library.

| Need | Read |
|---|---|
| Expectation-first loop and report buckets | [references/visual-validation/expectation-loop.md](references/visual-validation/expectation-loop.md) |
| Capture-mode selection for native, hybrid, and fallback paths | [references/visual-validation/capture-modes.md](references/visual-validation/capture-modes.md) |
| Drift taxonomy and narrowest-layer fix choice | [references/visual-validation/drift-analysis.md](references/visual-validation/drift-analysis.md) |
| Point-Free `swift-snapshot-testing` SPM wiring, record/verify mode, CI artifacts | [references/visual-validation/snapshot-testing-spm.md](references/visual-validation/snapshot-testing-spm.md) |
| Blank screenshots, focus failures, permissions, unstable runners | [references/visual-validation/troubleshooting.md](references/visual-validation/troubleshooting.md) |

## Quality Hooks Routing

Hard guardrails:

- Never write to `.git/hooks/` directly; use `git config core.hooksPath .githooks`.
- Never enable typecheck stage by default; opt in with `SWIFT_HOOK_TYPECHECK=1`.
- Never install global tools without confirmation.
- Never commit an empty SwiftLint baseline as a legacy-project solution.
- Never claim typecheck works without running it once end to end.

Copy the bundled assets from the outer skill root:

| Source | Destination | Purpose |
|---|---|---|
| `assets/swiftlint.yml` | `.swiftlint.yml` | SwiftLint rules and custom rules |
| `assets/swiftformat` | `.swiftformat` | SwiftFormat allowlist |
| `assets/githooks/pre-commit` | `.githooks/pre-commit` | Staged Swift lint/format/typecheck hook |
| `assets/scripts/swift-typecheck.sh` | `scripts/swift-typecheck.sh` | Per-platform `xcodebuild` matrix |
| `assets/Makefile.fragment` | append to `Makefile` | Lint, format, hook install targets |
| `assets/github-workflows/swift-quality.yml` | `.github/workflows/swift-quality.yml` | CI matrix and snapshot artifacts |

| Need | Read |
|---|---|
| Hook architecture and install semantics | [references/quality-hooks/hook-architecture.md](references/quality-hooks/hook-architecture.md) |
| Greenfield vs legacy SwiftLint baselines | [references/quality-hooks/baseline-workflow.md](references/quality-hooks/baseline-workflow.md) |
| Opt-in typecheck stage and project detection | [references/quality-hooks/typecheck-stage.md](references/quality-hooks/typecheck-stage.md) |
| SwiftLint config rationale | [references/quality-hooks/configs/swiftlint-config.md](references/quality-hooks/configs/swiftlint-config.md) |
| SwiftFormat config rationale | [references/quality-hooks/configs/swiftformat-config.md](references/quality-hooks/configs/swiftformat-config.md) |
| Hook troubleshooting | [references/quality-hooks/troubleshooting.md](references/quality-hooks/troubleshooting.md) |
| macOS typecheck destination | [references/quality-hooks/platforms/macos.md](references/quality-hooks/platforms/macos.md) |
| Multi-platform Apple CI matrix | [references/quality-hooks/platforms/multiplatform.md](references/quality-hooks/platforms/multiplatform.md) |
| iOS companion targets in macOS repos | [references/quality-hooks/platforms/ios.md](references/quality-hooks/platforms/ios.md) |
| tvOS companion targets in macOS repos | [references/quality-hooks/platforms/tvos.md](references/quality-hooks/platforms/tvos.md) |
| watchOS companion targets in macOS repos | [references/quality-hooks/platforms/watchos.md](references/quality-hooks/platforms/watchos.md) |
| visionOS companion targets in macOS repos | [references/quality-hooks/platforms/visionos.md](references/quality-hooks/platforms/visionos.md) |

## Cloud Sync Routing

Engage only when `Package.swift` or the request mentions `ConvexMobile`, `ClerkKit`, `ClerkConvex`, Convex, Clerk, real-time queries, multi-device sync, auth-gated cloud data, or live subscriptions. Skip this track for local-only Core Data or SwiftData apps.

Default stance:

- Use Clerk as the default Swift auth path.
- Treat `clerk-convex-swift >= 0.1.0`, `clerk-ios >= 1.0.0`, and `convex-swift >= 0.8.0` as minimum supported bounds; use version audit notes in [references/cloud-sync/operations/verified-corrections.md](references/cloud-sync/operations/verified-corrections.md) for latest checked versions.
- Prefer one `@MainActor` long-lived authenticated client per process: `ConvexClientWithAuth(deploymentUrl:authProvider: ClerkConvexAuthProvider())`.
- Use `AuthView()` and `UserButton()` from `ClerkKitUI`; do not roll a manual SIWA flow around `ASAuthorizationController`.
- Treat the Swift SDK as reconnecting-online, not offline-first.
- Treat macOS support as Apple Silicon only through this stack.

Hard rules:

- Do not promise optimistic updates, native offline persistence, Catalyst, Intel Mac, watchOS, tvOS, or visionOS support for ConvexMobile.
- Do not trust client-passed `userId` values. Server-side Clerk JWT identity is the authorization boundary.
- Do not use `Date.now()` inside Convex queries; pass stable client timestamps.
- Do not assume a subscription recovers after terminal Combine failure; rebuild with `resubscribe()`.
- Do not declare subscription-owning view models at the App scene level on macOS; use per-window or in-hierarchy ownership.

### Cloud Sync Start Points

| Decision | Read |
|---|---|
| Whole corpus map and narrow routing | [references/cloud-sync/overview.md](references/cloud-sync/overview.md) |
| Current limitations and hard stops | [references/cloud-sync/limitations.md](references/cloud-sync/limitations.md), [references/cloud-sync/operations/known-gaps.md](references/cloud-sync/operations/known-gaps.md) |
| Adoption constraints before committing | [references/cloud-sync/adoption-checklist.md](references/cloud-sync/adoption-checklist.md) |
| Backend fit and alternatives | [references/cloud-sync/onboarding/convex-vs-alternatives.md](references/cloud-sync/onboarding/convex-vs-alternatives.md), [references/cloud-sync/onboarding/why-convex-fits-swiftui.md](references/cloud-sync/onboarding/why-convex-fits-swiftui.md) |
| Live-data mental model | [references/cloud-sync/onboarding/mental-model.md](references/cloud-sync/onboarding/mental-model.md) |
| Verified corrections and trust boundary | [references/cloud-sync/operations/verified-corrections.md](references/cloud-sync/operations/verified-corrections.md) |

### Cloud Sync Setup And Auth

| Decision | Read |
|---|---|
| Node and Convex CLI prerequisites | [references/cloud-sync/setup-extra/node-prerequisites.md](references/cloud-sync/setup-extra/node-prerequisites.md) |
| Xcode SPM setup and ConvexMobile client init | [references/cloud-sync/spm-setup.md](references/cloud-sync/spm-setup.md), [references/cloud-sync/client-surface.md](references/cloud-sync/client-surface.md) |
| First local `npx convex dev` run | [references/cloud-sync/setup-extra/first-run.md](references/cloud-sync/setup-extra/first-run.md) |
| Clerk account, JWT template, and Convex auth config | [references/cloud-sync/setup-extra/clerk-jwt-template.md](references/cloud-sync/setup-extra/clerk-jwt-template.md), [references/cloud-sync/setup-extra/auth-config-wiring.md](references/cloud-sync/setup-extra/auth-config-wiring.md) |
| Clerk-first Swift setup and root auth gate | [references/cloud-sync/clerk-setup.md](references/cloud-sync/clerk-setup.md) |
| Auth alternatives and custom provider fallback | [references/cloud-sync/auth-custom-provider.md](references/cloud-sync/auth-custom-provider.md) |
| Sign in with Apple, Keychain, and session restoration | [references/cloud-sync/sign-in-with-apple.md](references/cloud-sync/sign-in-with-apple.md) |
| Backend ownership and authorization | [references/cloud-sync/backend/auth-rules-and-server-ownership.md](references/cloud-sync/backend/auth-rules-and-server-ownership.md) |

### Cloud Sync SwiftUI, SDK, And Platform Behavior

| Decision | Read |
|---|---|
| Root architecture and environment injection | [references/cloud-sync/root-architecture.md](references/cloud-sync/root-architecture.md) |
| macOS app entry, MenuBarExtra, entitlements | [references/cloud-sync/macos-app-entry.md](references/cloud-sync/macos-app-entry.md) |
| Per-window view models | [references/cloud-sync/per-window-viewmodels.md](references/cloud-sync/per-window-viewmodels.md) |
| Observation ownership and re-init traps | [references/cloud-sync/observation-ownership.md](references/cloud-sync/observation-ownership.md), [references/cloud-sync/pitfall-observable-reinit.md](references/cloud-sync/pitfall-observable-reinit.md) |
| Navigation, tabs, sheets, and subscription lifecycle | [references/cloud-sync/lifecycle-navigation.md](references/cloud-sync/lifecycle-navigation.md), [references/cloud-sync/pitfall-task-cancellation.md](references/cloud-sync/pitfall-task-cancellation.md), [references/cloud-sync/swiftui-extra/navstack-subscription-lifecycle.md](references/cloud-sync/swiftui-extra/navstack-subscription-lifecycle.md), [references/cloud-sync/swiftui-extra/tabview-and-sheets.md](references/cloud-sync/swiftui-extra/tabview-and-sheets.md) |
| Reactive queries and parameterized subscriptions | [references/cloud-sync/reactive-queries.md](references/cloud-sync/reactive-queries.md) |
| Loading, errors, skeletons, and retry UI | [references/cloud-sync/loading-error-tristate.md](references/cloud-sync/loading-error-tristate.md), [references/cloud-sync/backend/structured-errors-convexerror.md](references/cloud-sync/backend/structured-errors-convexerror.md) |
| Connection banner, offline states, and recovery | [references/cloud-sync/connection-banner.md](references/cloud-sync/connection-banner.md), [references/cloud-sync/offline-ux-states.md](references/cloud-sync/offline-ux-states.md), [references/cloud-sync/pipeline-recovery.md](references/cloud-sync/pipeline-recovery.md), [references/cloud-sync/pitfall-pipeline-dies.md](references/cloud-sync/pitfall-pipeline-dies.md) |
| SDK wire types and modeling | [references/cloud-sync/client-sdk-extra/type-system-and-modeling.md](references/cloud-sync/client-sdk-extra/type-system-and-modeling.md), [references/cloud-sync/client-sdk-extra/convex-encodable.md](references/cloud-sync/client-sdk-extra/convex-encodable.md), [references/cloud-sync/client-sdk-extra/subscriptions-and-errors.md](references/cloud-sync/client-sdk-extra/subscriptions-and-errors.md), [references/cloud-sync/swift-sdk-cheatsheet.md](references/cloud-sync/swift-sdk-cheatsheet.md) |
| Debug logging and observability | [references/cloud-sync/client-sdk-extra/debug-logging.md](references/cloud-sync/client-sdk-extra/debug-logging.md) |
| iOS/macOS lifecycle caveats | [references/cloud-sync/platforms/ios-backgrounding-and-staleness.md](references/cloud-sync/platforms/ios-backgrounding-and-staleness.md) |
| Network awareness | [references/cloud-sync/platforms/nwpathmonitor.md](references/cloud-sync/platforms/nwpathmonitor.md) |
| Performance, threading, binary size | [references/cloud-sync/platforms/performance-and-threading.md](references/cloud-sync/platforms/performance-and-threading.md), [references/cloud-sync/platforms/binary-size-and-profiling.md](references/cloud-sync/platforms/binary-size-and-profiling.md) |

### Cloud Sync Pitfalls, Quick References, And Playbooks

| Decision | Read |
|---|---|
| Pitfalls index: side effects, array limits, `Date.now`, main thread delivery, auth trust, unbounded collect | [references/cloud-sync/pitfalls-extra/actions-as-side-effects.md](references/cloud-sync/pitfalls-extra/actions-as-side-effects.md), [references/cloud-sync/pitfalls-extra/arrays-8192-limit.md](references/cloud-sync/pitfalls-extra/arrays-8192-limit.md), [references/cloud-sync/pitfalls-extra/date-now-in-queries.md](references/cloud-sync/pitfalls-extra/date-now-in-queries.md), [references/cloud-sync/pitfalls-extra/receive-on-main.md](references/cloud-sync/pitfalls-extra/receive-on-main.md), [references/cloud-sync/pitfalls-extra/trusting-client-for-auth.md](references/cloud-sync/pitfalls-extra/trusting-client-for-auth.md), [references/cloud-sync/pitfalls-extra/unbounded-collect.md](references/cloud-sync/pitfalls-extra/unbounded-collect.md) |
| Quick reference cards and decision trees | [references/cloud-sync/quick-reference/backend-card.md](references/cloud-sync/quick-reference/backend-card.md), [references/cloud-sync/quick-reference/function-decision-tree.md](references/cloud-sync/quick-reference/function-decision-tree.md), [references/cloud-sync/quick-reference/subscription-placement.md](references/cloud-sync/quick-reference/subscription-placement.md) |
| Implementation playbooks | [references/cloud-sync/playbooks/greenfield-swiftui-app.md](references/cloud-sync/playbooks/greenfield-swiftui-app.md), [references/cloud-sync/playbooks/shared-ios-macos-app.md](references/cloud-sync/playbooks/shared-ios-macos-app.md), [references/cloud-sync/playbooks/streaming-and-transcription.md](references/cloud-sync/playbooks/streaming-and-transcription.md) |
| Complete walkthrough | [references/cloud-sync/walkthrough/01-zero-to-realtime-chat.md](references/cloud-sync/walkthrough/01-zero-to-realtime-chat.md), [references/cloud-sync/walkthrough/02-schema-and-backend-code.md](references/cloud-sync/walkthrough/02-schema-and-backend-code.md), [references/cloud-sync/walkthrough/03-swift-models-and-viewmodels.md](references/cloud-sync/walkthrough/03-swift-models-and-viewmodels.md), [references/cloud-sync/walkthrough/04-swiftui-views.md](references/cloud-sync/walkthrough/04-swiftui-views.md), [references/cloud-sync/walkthrough/05-deployment-checklist.md](references/cloud-sync/walkthrough/05-deployment-checklist.md) |

Cloud-sync UI still obeys HIG and Liquid Glass rules: loading states use skeletons or tri-state UI, errors provide a specific retry path, auth UI lives in sheets/toolbars where appropriate, and sync status belongs in subtle chrome rather than content rows.

## Workflow Routing

| Need | Read |
|---|---|
| Bootstrap a new app end to end | [references/workflow/bootstrap-new-app.md](references/workflow/bootstrap-new-app.md) |
| Audit existing code with severity-tagged findings | [references/workflow/audit-existing.md](references/workflow/audit-existing.md) |
| Run final pre-release checks | [references/workflow/ship-checklist.md](references/workflow/ship-checklist.md) |

## Output Contract

When work using this skill ends, report:

- What changed: file paths plus one line per change.
- Verification rung reached:

  | Rung | Meaning |
  |---|---|
  | 1 | Read the code |
  | 2 | Type-check or lint passes |
  | 3 | Unit tests pass |
  | 4 | Snapshot tests pass |
  | 5 | Ran the program and observed the change |
  | 6 | User confirmed the changed behavior |

- What remains, only if anything remains.

Never claim done while the working tree is dirty, a guardrail is violated, or the stated verification rung was not actually reached.
