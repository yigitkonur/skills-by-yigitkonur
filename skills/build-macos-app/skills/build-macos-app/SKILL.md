---
name: build-macos-app
description: Use skill if you are building, auditing, or shipping a production-grade macOS SwiftUI or AppKit app needing HIG compliance, Liquid Glass design, snapshot validation, SwiftLint/SwiftFormat hooks, or Convex+Clerk cloud sync.
---

# Build macOS App — Production-Grade

You are a senior Apple design engineer. Your job is to make macOS code look like Apple shipped it. You think in glass, concentricity, and hierarchy — not in pixels and hex colors.

This skill orchestrates five production concerns: **HIG compliance**, **Liquid Glass design**, **visual validation discipline**, **Swift quality hooks**, and an optional **cloud-sync** track for apps with a Convex + Clerk backend. The load-bearing tables and rules live below; everything else is in `references/` — route deliberately, never speculate.

## When to use this skill

Trigger when the user says any of: *"build a macOS app"*, *"production-grade Mac app"*, *"ship a Mac app"*, *"audit my macOS UI"*, *"modernize for Tahoe"*, *"make this look like Apple shipped it"*, *"Mac app quality setup"*, *"bootstrap a SwiftUI macOS app"*, *"Liquid Glass review"*, *"set up snapshot tests for Swift"*, *"Swift pre-commit hook"*. Trigger when the directory contains `*.xcodeproj`, `*.xcworkspace`, `Package.swift`, or `*.swift` with a macOS target. Trigger on mentions of SwiftUI, AppKit, Liquid Glass, NavigationSplitView, NSGlassEffectView, Settings scene, MenuBarExtra, ConvexMobile, Clerk, ClerkConvex.

Do NOT use this skill when:
- The work is iOS-only / iPadOS-only with no macOS surface.
- The task is pure server-side Convex/JS work — this skill covers the Swift client only.
- The task is non-Apple Swift on Linux.

## Operations

Detect the operation from the user's intent, then route to the matching workflow file. If ambiguous, ask once.

| Operation | Trigger | Route to |
|---|---|---|
| **bootstrap** | Fresh project, "start a new Mac app" | [references/workflow/bootstrap-new-app.md](references/workflow/bootstrap-new-app.md) |
| **build** | "Add a view", "implement screen X" | Apply Three Questions, then load relevant references on demand |
| **redesign** | "Make this look like Apple", "modernize" | [references/liquid-glass/design-diagnosis.md](references/liquid-glass/design-diagnosis.md) |
| **audit** | "Review", "audit", "assess" | [references/workflow/audit-existing.md](references/workflow/audit-existing.md) |
| **migrate** | Pre-Tahoe code on macOS 26 | [references/liquid-glass/migration-guide.md](references/liquid-glass/migration-guide.md) |
| **install hooks** | Wants pre-commit lint/format | [references/quality-hooks/hook-architecture.md](references/quality-hooks/hook-architecture.md) |
| **add tests** | Snapshot/visual validation | [references/visual-validation/snapshot-testing-spm.md](references/visual-validation/snapshot-testing-spm.md) |
| **wire cloud sync** | Convex + Clerk backend | [references/cloud-sync/overview.md](references/cloud-sync/overview.md) |
| **ship** | Pre-release final pass | [references/workflow/ship-checklist.md](references/workflow/ship-checklist.md) |

---

## The Three Laws of macOS UI

These are non-negotiable. Violating any of them is a CRITICAL audit finding.

1. **Every action must be in the menu bar.** Toolbars are hideable; the menu bar is the source of truth. Every toolbar action needs a menu equivalent. → [references/hig/components/menus.md](references/hig/components/menus.md)
2. **Standard keyboard shortcuts are sacred.** `Cmd-N/O/S/Shift-S/Z/Shift-Z/Q/W/Comma/F/A/C/V/X`. Don't repurpose. → [references/hig/platform/keyboard-shortcuts.md](references/hig/platform/keyboard-shortcuts.md)
3. **Settings take effect immediately.** No Save / Cancel / Apply in preferences. → [references/hig/components/menus.md](references/hig/components/menus.md)

## The Three Questions

Ask these before writing or accepting any view:

1. **Is this navigation or content?** Glass goes on navigation; never on content rows, cards, or text.
2. **What is the ONE primary action?** Promote one button per screen (`.glassProminent` + `.tint(.accentColor)`, or `.keyboardShortcut(.defaultAction)`). All others are secondary.
3. **Would Apple ship this?** If it looks like a custom design system, you wrote it wrong. → [references/liquid-glass/design-principles.md](references/liquid-glass/design-principles.md)

## Glass Placement

| Layer | Glass? | Examples |
|---|---|---|
| **Navigation** | YES | Toolbars, sidebars, floating controls, sheets, popovers, menu overlays, tab bars |
| **Content** | NO | Lists, table rows, text, images, cards, form fields |

→ [references/liquid-glass/design-principles.md](references/liquid-glass/design-principles.md)

## Hierarchy Through Tinting

| Role | API | Rule |
|---|---|---|
| Primary | `.buttonStyle(.glassProminent)` + `.tint(.accentColor)` | **ONE per screen** |
| Secondary | `.buttonStyle(.glass)` (no tint) | Many allowed |
| Destructive | `.tint(.red)` or `.buttonRole(.destructive)` | Never the default |
| Informational | No tint, no prominence | Background actions |

macOS workaround: secondary glass buttons may need `.tint(.clear)` to suppress accent bleed (practitioner workaround, not official Apple guidance). → [references/liquid-glass/pitfalls-and-solutions.md](references/liquid-glass/pitfalls-and-solutions.md)

## macOS-Specific Non-Negotiables

- `.interactive()` is iOS-only. Do not use on macOS code paths.
- `.scrollEdgeEffectStyle(.hard)` is the macOS default; only override with reason.
- `.tabViewStyle(.sidebarAdaptable)` produces a macOS sidebar (and a floating tab bar on iOS).
- `Settings { … }` scene + `Cmd-,` is mandatory.
- `.commands { CommandGroup … }` wires app menus from SwiftUI.
- `NavigationSplitView` + `.backgroundExtensionEffect()` on the sidebar. Never `NavigationView`.
- Gate every Tahoe-specific API with `#available(macOS 26, *)`.
- Concentric corner radii (`.containerConcentric` or `ConcentricRectangle()`) wherever glass meets bordered content.

→ [references/liquid-glass/macos-patterns.md](references/liquid-glass/macos-patterns.md), [references/liquid-glass/api-reference.md](references/liquid-glass/api-reference.md)

---

## Spacing Scale (8pt grid)

| Token | px | Use |
|---|---|---|
| xxs | 1 | hairline |
| xs | 4 | tight inline |
| s | 6 | min between stacked controls |
| **m** | **8** | label-to-control |
| l | 10 | inline groups |
| ml | 12 | between paragraphs |
| xl | 14 | small section |
| xxl | 16 | GroupBox margin |
| **xxxl** | **20** | window content margin (L/R/B) |
| xxxxl | 24 | menu bar height |

**The 20-8-6 rule:** 20pt window margins, 8pt label-to-control gap, 6pt minimum between stacked controls. → [references/hig/foundations/layout-spacing.md](references/hig/foundations/layout-spacing.md)

## Typography (macOS body = 13pt, NOT 17pt)

| Style | Size | Weight | Use |
|---|---|---|---|
| Large Title | 26 | Regular | Hero, sparingly |
| Title 1 | 22 | Regular | Page heading |
| Title 2 | 17 | Regular | Section header |
| Title 3 | 15 | Regular | Subsection |
| **Headline** | **13** | **Bold** | Emphasis (NOT Semibold) |
| **Body** | **13** | Regular | **Default** |
| Callout | 12 | Regular | Tertiary |
| Subheadline | 11 | Regular | Captions |
| Footnote | 10 | Regular | Fine print |

SF Pro Text ≤19pt; SF Pro Display ≥20pt. → [references/hig/foundations/typography.md](references/hig/foundations/typography.md)

## Control Size Tiers

| Tier | px | SwiftUI | AppKit | Use |
|---|---|---|---|---|
| Mini | ~16 | `.controlSize(.mini)` | `.mini` | Inline within toolbars / dense forms |
| Small | ~19 | `.controlSize(.small)` | `.small` | Sidebars, palettes |
| **Regular** | **~22** | `.controlSize(.regular)` | `.regular` | **Default** for buttons, fields |
| Large | ~26-32 | `.controlSize(.large)` / `.extraLarge` | `.large` | Hero CTAs, watch-style buttons |

→ [references/hig/components/buttons.md](references/hig/components/buttons.md), [references/hig/components/text-inputs.md](references/hig/components/text-inputs.md)

## Color Label Hierarchy

Use semantic colors only — never hardcoded hex on glass or content.

| Role | NSColor | SwiftUI | When |
|---|---|---|---|
| Primary | `.labelColor` | `.foregroundStyle(.primary)` | Default body text, headings |
| Secondary | `.secondaryLabelColor` | `.foregroundStyle(.secondary)` | Captions, metadata |
| Tertiary | `.tertiaryLabelColor` | `.foregroundStyle(.tertiary)` | Disabled labels, placeholders |
| Quaternary | `.quaternaryLabelColor` | `.foregroundStyle(.quaternary)` | Watermarks, decorative |

CALayer does NOT auto-adapt to appearance — refresh in `viewDidChangeEffectiveAppearance()`. Asset catalogs support 4 slots: Any, Dark, High-Contrast, HC-Dark.

→ [references/hig/foundations/color-and-dark-mode.md](references/hig/foundations/color-and-dark-mode.md)

## Materials — `.behindWindow` vs `.withinWindow`

| Surface | Material | Blending |
|---|---|---|
| Title bar | `.titlebar` | **`.withinWindow`** (mandatory — `.behindWindow` causes black gap) |
| Sidebar | `.sidebar` | `.behindWindow` (requires `window.isOpaque = false`) |
| Sheet content | `.contentBackground` | `.withinWindow` |
| HUD / floating panel | `.hudWindow` | `.behindWindow` |
| Pre-Tahoe glass surface | `.fullScreenUI` / `.menu` / `.popover` | per Apple docs |

For Tahoe (macOS 26): prefer `.glassEffect()` and `NSGlassEffectView` over the deprecated material list. → [references/hig/foundations/materials-and-vibrancy.md](references/hig/foundations/materials-and-vibrancy.md)

## Motion Timing

- `NSAnimationContext` default: **0.25s**.
- SwiftUI `.default`: **0.35s**.
- Window/sheet present-dismiss: ~**0.20s**.
- **Hard rule: <0.4s on macOS.** Anything longer feels sluggish.
- Springs: **no bounce** (or `response: 0.3, dampingFraction: 0.85+`).
- Honor `accessibilityReduceMotion` — substitute `.opacity` or instant cuts.

→ [references/hig/foundations/motion.md](references/hig/foundations/motion.md)

## SwiftUI vs AppKit — Decision Table

| Need | Choose |
|---|---|
| Forms, lists ≤1000 rows, settings panes | **SwiftUI** |
| Tables 5000+ rows, virtualization | **AppKit** (`NSTableView`) |
| Native sidebar vibrancy + source-list header | **AppKit** |
| Window lifecycle (delegate, full-screen quirks, restoration nuance) | **AppKit** (`NSWindow` delegate) |
| Rich drag-drop with file promises | **AppKit** (`NSPasteboard`) |
| Cross-platform iOS+macOS code | **SwiftUI** |
| Custom NSToolbar with badges + segmented overflow | **AppKit** + `NSToolbarItem` |
| Live Liquid Glass with dynamic `tintColor` | Either; `.glassEffect()` (SwiftUI) or `NSGlassEffectView` (AppKit) |

Quote: *"SwiftUI implements HIG for you on iOS; on macOS, it fights you at every turn."* — bridge to AppKit when the SwiftUI ceiling appears. → [references/liquid-glass/appkit-bridging.md](references/liquid-glass/appkit-bridging.md)

## Component Decision Trees

### Which container for additional UI?
- 1–2 lines of input + binary choice → **Alert**
- Form with 3–10 fields, modal task → **Sheet**
- Quick context, transient → **Popover** (`.transient`)
- Persistent context, user keeps editing main view → **Inspector** (sidebar trailing)
- Hide/show inline content → **DisclosureGroup**

### Which data display?
- Forms + ≤1000 rows → SwiftUI **List/Table**
- Hierarchical, ≤5000 rows → SwiftUI **OutlineGroup**
- Flat, 5000+ rows → AppKit **NSTableView**
- Hierarchical, large → AppKit **NSOutlineView**
- 2D grid + selection → AppKit **NSCollectionView** (Compositional Layout)
- Multi-column drill-down → AppKit **NSBrowser**

### Checkbox vs Toggle?
- Multi-select list / form field → **Checkbox**
- Single boolean preference, takes effect immediately → **Toggle / NSSwitch**

→ [references/hig/components/buttons.md](references/hig/components/buttons.md), [references/hig/components/selection-controls.md](references/hig/components/selection-controls.md), [references/hig/components/alerts-and-sheets.md](references/hig/components/alerts-and-sheets.md), [references/hig/components/popovers-and-disclosure.md](references/hig/components/popovers-and-disclosure.md), [references/hig/components/tables-and-lists.md](references/hig/components/tables-and-lists.md)

## Dialog Button Placement

```
[Destructive]  [Cancel]  [Default Action]
```

- Default = trailing, accent fill, `Return` key.
- Cancel = `Escape` key.
- Destructive can never be the default. In `NSAlert`, never put it first — styling is suppressed on the first button.
- Use specific verbs: *Delete*, *Replace*, *Discard* — never "OK" or "Yes / No".

→ [references/hig/components/alerts-and-sheets.md](references/hig/components/alerts-and-sheets.md)

---

## The "Apple Would Never" List

1. Glass on list rows / table cells / content
2. Multiple tinted primary actions on one screen
3. Hardcoded colors (`Color(red:)`, hex literals) on glass
4. Fixed font sizes (`.font(.system(size: 14))`)
5. `NavigationView` instead of `NavigationSplitView` / `NavigationStack`
6. `@StateObject` / `@ObservedObject` (superseded — use `@Observable`)
7. `.toolbarBackground(.visible)` on macOS 26
8. Missing keyboard shortcuts (`Cmd-N/S/W/Z/Comma/Q`)
9. Custom window chrome (drag regions, custom traffic lights)
10. `.interactive()` on macOS code paths

## The 10 Common Mistakes

1. Treating macOS as a big iPad (no bottom tab bars, no full-screen sheets)
2. Save / Cancel / Apply in Settings (settings take effect immediately)
3. Missing standard keyboard shortcuts
4. Missing menu bar items (toolbar without menu equivalent)
5. iOS body text size (17pt) instead of macOS 13pt
6. iOS row heights (44pt) instead of macOS 22pt
7. Custom dark mode toggle (respect `NSAppearance` and system Settings)
8. SwiftUI `List` / `Table` for >1000 rows (use `NSTableView`)
9. Missing Services menu in text apps
10. Hardcoded colors instead of semantic (`.foregroundStyle(.primary)`, `.secondary`, `.accentColor`)

→ [references/hig/practitioner-insights.md](references/hig/practitioner-insights.md) for what real shipping macOS apps override and why.

---

## Visual Validation: 7 Non-Negotiable Rules

When validating UI with screenshots:

1. State the expectation BEFORE capture. Never retrofit expectations from a captured image.
2. Validate one target state per run.
3. Prefer the most deterministic capture path: in-app rendering → UI-test harness → browser driver (hybrid apps) → Accessibility / `screencapture` fallback.
4. Record layout facts (collapsed sidebars, compact toolbars, split-view sizes) before classifying drift.
5. Separate deterministic structure from data-dependent variation (item names, timestamps).
6. Report in three buckets: **Matches** / **Drift** / **Better than expected**.
7. Fix the narrowest correct layer (automation / app / expectation) and rerun the same target.

→ [references/visual-validation/expectation-loop.md](references/visual-validation/expectation-loop.md), [references/visual-validation/capture-modes.md](references/visual-validation/capture-modes.md), [references/visual-validation/drift-analysis.md](references/visual-validation/drift-analysis.md), [references/visual-validation/snapshot-testing-spm.md](references/visual-validation/snapshot-testing-spm.md), [references/visual-validation/troubleshooting.md](references/visual-validation/troubleshooting.md)

---

## Quality Hooks: Hard Guardrails

- **Never** write to `.git/hooks/` directly. Use `git config core.hooksPath .githooks`.
- **Never** enable typecheck stage by default — it's slow. User must opt in via `SWIFT_HOOK_TYPECHECK=1`.
- **Never** install global tools without confirmation.
- **Never** commit an empty SwiftLint baseline as "done" on a legacy project.
- **Never** claim typecheck works without running it once end-to-end.

### Assets to copy into the user's repo

The merged skill ships a calibrated config bundle at the outer skill root. Copy verbatim:

| Source (this skill) | Destination (user repo) | Purpose |
|---|---|---|
| `<skill>/assets/swiftlint.yml` | `.swiftlint.yml` | 28 opt-in rules + 7 disabled + 5 custom rules |
| `<skill>/assets/swiftformat` | `.swiftformat` | 17-rule allowlist, Swift 6, 4-space indent |
| `<skill>/assets/githooks/pre-commit` | `.githooks/pre-commit` | Stages: detect → SwiftLint → SwiftFormat → optional typecheck |
| `<skill>/assets/scripts/swift-typecheck.sh` | `scripts/swift-typecheck.sh` | Per-platform xcodebuild matrix (macOS/iOS/tvOS/watchOS/visionOS) |
| `<skill>/assets/Makefile.fragment` | append to `Makefile` | `lint` / `lint-fix` / `lint-new` / `format` / `install-hooks` / `lint-all` |
| `<skill>/assets/github-workflows/swift-quality.yml` | `.github/workflows/swift-quality.yml` | CI matrix + snapshot diff artifact upload |

Then enable: `git config core.hooksPath .githooks`.

→ [references/quality-hooks/hook-architecture.md](references/quality-hooks/hook-architecture.md), [references/quality-hooks/baseline-workflow.md](references/quality-hooks/baseline-workflow.md), [references/quality-hooks/typecheck-stage.md](references/quality-hooks/typecheck-stage.md), [references/quality-hooks/configs/swiftlint-config.md](references/quality-hooks/configs/swiftlint-config.md), [references/quality-hooks/configs/swiftformat-config.md](references/quality-hooks/configs/swiftformat-config.md), [references/quality-hooks/troubleshooting.md](references/quality-hooks/troubleshooting.md), [references/quality-hooks/platforms/macos.md](references/quality-hooks/platforms/macos.md), [references/quality-hooks/platforms/ios.md](references/quality-hooks/platforms/ios.md), [references/quality-hooks/platforms/tvos.md](references/quality-hooks/platforms/tvos.md), [references/quality-hooks/platforms/watchos.md](references/quality-hooks/platforms/watchos.md), [references/quality-hooks/platforms/visionos.md](references/quality-hooks/platforms/visionos.md), [references/quality-hooks/platforms/multiplatform.md](references/quality-hooks/platforms/multiplatform.md)

---

## Cloud Sync (when the app talks to a backend)

Engage this track only when:
- `Package.swift` contains `ConvexMobile`, `ClerkKit`, or `ClerkConvex`, OR
- The user mentions Convex, Clerk, real-time queries, multi-device sync, auth-gated cloud data, or live subscriptions.

If the app is local-only (Core Data, SwiftData, no server), skip this entire track.

### Default stance — preserve verbatim, do not loosen

- Use **Clerk** as the default Swift auth path. Use the official `ClerkConvex` package (`clerk-convex-swift >= 0.1.0`) with `clerk-ios >= 1.0.0` and `convex-swift >= 0.8.0`.
- Prefer **one `@MainActor` long-lived authenticated client per process**, created with `ConvexClientWithAuth(deploymentUrl:authProvider: ClerkConvexAuthProvider())`.
- Use `AuthView()` and `UserButton()` from `ClerkKitUI` for sign-in. Never roll your own `ASAuthorizationController` for SIWA — `AuthView()` handles it.
- Add `.prefetchClerkImages()` and `.environment(Clerk.shared)` on root views.
- Treat the Swift SDK as **reconnecting-online**, NOT offline-first.
- Treat macOS support as **Apple Silicon only**. No Catalyst, no watchOS, no tvOS, no visionOS via this stack.
- Target iOS 17+ / macOS 14+ minimum.

### Hard rules

- Do NOT promise optimistic updates, native offline persistence, Catalyst, watchOS, tvOS, or visionOS support — the SDK does not have them.
- Do NOT use client-passed `userId` values for authorization. Server-side identity (Clerk JWT subject) is the only trustable source.
- Do NOT use `Date.now()` inside Convex queries — it breaks reactivity. Pass a stable client timestamp argument.
- Do NOT assume subscription recovery after a terminal `Combine` failure. Rebuild the pipeline with `resubscribe()`.
- Do NOT declare `@StateObject`/`@Observable` view models at the App scene level on macOS — they re-init across new windows. Declare them **inside** the view hierarchy.

→ [references/cloud-sync/overview.md](references/cloud-sync/overview.md), [references/cloud-sync/limitations.md](references/cloud-sync/limitations.md), [references/cloud-sync/adoption-checklist.md](references/cloud-sync/adoption-checklist.md)

### macOS-specific cloud-sync routing

| Concern | Read |
|---|---|
| App entry, MenuBarExtra, sandbox entitlements | [references/cloud-sync/macos-app-entry.md](references/cloud-sync/macos-app-entry.md) |
| Per-window view model gotcha (the #1 macOS multi-window bug) | [references/cloud-sync/per-window-viewmodels.md](references/cloud-sync/per-window-viewmodels.md) |
| Offline / network-transition UX (4 states) | [references/cloud-sync/offline-ux-states.md](references/cloud-sync/offline-ux-states.md) |
| Connection banner / sync indicator | [references/cloud-sync/connection-banner.md](references/cloud-sync/connection-banner.md) |
| Tri-state loading (loading / loaded / failed) + skeletons | [references/cloud-sync/loading-error-tristate.md](references/cloud-sync/loading-error-tristate.md) |
| Pipeline termination + `resubscribe()` (production-critical) | [references/cloud-sync/pipeline-recovery.md](references/cloud-sync/pipeline-recovery.md) |
| `Env` struct + module-level `@MainActor` client | [references/cloud-sync/root-architecture.md](references/cloud-sync/root-architecture.md) |
| Auth gate `LandingPage` + `AuthView()` sheet | [references/cloud-sync/clerk-setup.md](references/cloud-sync/clerk-setup.md) |
| SIWA + keychain + session restoration | [references/cloud-sync/sign-in-with-apple.md](references/cloud-sync/sign-in-with-apple.md) |
| `switchToLatest` parameterized subscriptions | [references/cloud-sync/reactive-queries.md](references/cloud-sync/reactive-queries.md) |
| `@Observable` re-init traps | [references/cloud-sync/observation-ownership.md](references/cloud-sync/observation-ownership.md), [references/cloud-sync/pitfall-observable-reinit.md](references/cloud-sync/pitfall-observable-reinit.md) |
| `TabView` cancels `.task`; `NavigationStack(path:)` patterns | [references/cloud-sync/lifecycle-navigation.md](references/cloud-sync/lifecycle-navigation.md), [references/cloud-sync/pitfall-task-cancellation.md](references/cloud-sync/pitfall-task-cancellation.md) |
| Pipeline-dies-after-first-error | [references/cloud-sync/pitfall-pipeline-dies.md](references/cloud-sync/pitfall-pipeline-dies.md) |
| Xcode SPM setup, `ConvexClient` init | [references/cloud-sync/spm-setup.md](references/cloud-sync/spm-setup.md), [references/cloud-sync/client-surface.md](references/cloud-sync/client-surface.md) |
| Swift SDK API cheat sheet (`subscribe`/`mutation`/`action`/`watchWebSocketState`) | [references/cloud-sync/swift-sdk-cheatsheet.md](references/cloud-sync/swift-sdk-cheatsheet.md) |

### How cloud-sync UI integrates with HIG / Liquid Glass

- **Loading**: prefer `ViewState<T>.loading` + `.redacted(reason: .placeholder)` skeletons over `ProgressView` everywhere.
- **Error**: tri-state `.failed(ClientError)` shows `Image(systemName: "exclamationmark.triangle")` + a `.borderedProminent` Retry button calling `vm.resubscribe()`.
- **Auth presentation**: `AuthView()` via `.sheet(isPresented:)` from a root `LandingPage`. `UserButton()` lives in `.toolbar { ToolbarItem(placement: .automatic) }`.
- **Sync indicator**: `Capsule`-shape banner with `ProgressView` + caption, animated with `.transition(.move(edge: .top).combined(with: .opacity))` and `.animation(.spring(response: 0.3))`. For permanent placement, use a small status dot (`Circle().fill().frame(width: 8, height: 8)` + caption) in the toolbar or sidebar footer.
- **Menu bar**: cloud-sync apps that need ambient status use `MenuBarExtra("Status", systemImage: …)` with `.menuBarExtraStyle(.window)` — the default `.menu` style does not behave like a normal SwiftUI surface.

These visual choices must reconcile with the **Hierarchy Through Tinting** rule above — at most ONE `.glassProminent` per screen, even when an auth flow is on top.

---

## Reference Routing

Single source of truth. When in doubt, scan this table and load the matching file.

### HIG — Foundations

| Topic | File |
|---|---|
| Color, dark mode, contrast, semantic tokens | [references/hig/foundations/color-and-dark-mode.md](references/hig/foundations/color-and-dark-mode.md) |
| Typography, weights, SF Pro Display vs Text | [references/hig/foundations/typography.md](references/hig/foundations/typography.md) |
| Spacing, alignment, 8pt grid, NSGridView | [references/hig/foundations/layout-spacing.md](references/hig/foundations/layout-spacing.md) |
| Icons, app icon sizes, SF Symbols + animation | [references/hig/foundations/icons-and-sf-symbols.md](references/hig/foundations/icons-and-sf-symbols.md) |
| Materials, vibrancy, `.behindWindow` vs `.withinWindow` | [references/hig/foundations/materials-and-vibrancy.md](references/hig/foundations/materials-and-vibrancy.md) |
| Motion, animation, springs, Reduce Motion | [references/hig/foundations/motion.md](references/hig/foundations/motion.md) |

### HIG — Components

| Topic | File |
|---|---|
| Buttons, toggles, switches, toolbar buttons | [references/hig/components/buttons.md](references/hig/components/buttons.md) |
| Text inputs, search, AutoFill, passkeys | [references/hig/components/text-inputs.md](references/hig/components/text-inputs.md) |
| Pickers, sliders, steppers, color wells | [references/hig/components/selection-controls.md](references/hig/components/selection-controls.md) |
| Menus, menu bar, contextual menus, Services | [references/hig/components/menus.md](references/hig/components/menus.md) |
| Popovers, tooltips, disclosure | [references/hig/components/popovers-and-disclosure.md](references/hig/components/popovers-and-disclosure.md) |
| Tables, lists, outlines, NSCollectionView | [references/hig/components/tables-and-lists.md](references/hig/components/tables-and-lists.md) |
| Alerts, sheets, dialogs, system panels | [references/hig/components/alerts-and-sheets.md](references/hig/components/alerts-and-sheets.md) |

### HIG — Platform patterns

| Topic | File |
|---|---|
| Window types, traffic lights, restoration, tabbing | [references/hig/platform/windows.md](references/hig/platform/windows.md) |
| Sidebars, source lists, split views, inspectors | [references/hig/platform/sidebars-and-split-views.md](references/hig/platform/sidebars-and-split-views.md) |
| Toolbars, title bars, customization | [references/hig/platform/toolbars.md](references/hig/platform/toolbars.md) |
| Keyboard shortcuts, focus, F-keys, Escape hierarchy | [references/hig/platform/keyboard-shortcuts.md](references/hig/platform/keyboard-shortcuts.md) |
| Drag-drop, file management, document types, Quick Look | [references/hig/platform/drag-drop-files.md](references/hig/platform/drag-drop-files.md) |

### HIG — Technologies

| Topic | File |
|---|---|
| VoiceOver, A11y APIs, Reduce Motion / Increase Contrast | [references/hig/technologies/accessibility.md](references/hig/technologies/accessibility.md) |
| Widgets, notifications, Spotlight, MenuBarExtras | [references/hig/technologies/widgets-and-notifications.md](references/hig/technologies/widgets-and-notifications.md) |
| Real-world overrides + practitioner perspective | [references/hig/practitioner-insights.md](references/hig/practitioner-insights.md) |

### Liquid Glass

| Topic | File |
|---|---|
| SwiftUI + AppKit Liquid Glass API surface | [references/liquid-glass/api-reference.md](references/liquid-glass/api-reference.md) |
| 12 design principles, concentricity, tinting hierarchy | [references/liquid-glass/design-principles.md](references/liquid-glass/design-principles.md) |
| Modernizing existing code (41-row deprecation table, 30 smells) | [references/liquid-glass/design-diagnosis.md](references/liquid-glass/design-diagnosis.md) |
| Toolbar / sidebar / window / Settings recipes | [references/liquid-glass/macos-patterns.md](references/liquid-glass/macos-patterns.md) |
| 5-phase migration from pre-Tahoe | [references/liquid-glass/migration-guide.md](references/liquid-glass/migration-guide.md) |
| 34 known glass bugs and workarounds | [references/liquid-glass/pitfalls-and-solutions.md](references/liquid-glass/pitfalls-and-solutions.md) |
| AppKit ↔ SwiftUI glass bridging | [references/liquid-glass/appkit-bridging.md](references/liquid-glass/appkit-bridging.md) |

#### WWDC 2025 sessions (authoritative source for Liquid Glass)

- **219** — *Meet Liquid Glass* — design language, lensing, motion, adaptive behavior.
- **310** — *Build a SwiftUI app with the new design* — `.glassEffect()`, container shapes, ornaments.
- **323** — *Update your AppKit app with the new design* — `NSGlassEffectView`, NSToolbar updates, `NSWindow` chrome.
- **356** — *Get to know the new design system* — concentricity rules, hierarchy, layout regions, accessibility.

### Visual validation

| Topic | File |
|---|---|
| Expectation-first 5-step loop | [references/visual-validation/expectation-loop.md](references/visual-validation/expectation-loop.md) |
| Capture-mode preference order | [references/visual-validation/capture-modes.md](references/visual-validation/capture-modes.md) |
| Drift taxonomy (5 categories) | [references/visual-validation/drift-analysis.md](references/visual-validation/drift-analysis.md) |
| `swift-snapshot-testing` SPM wiring + CI | [references/visual-validation/snapshot-testing-spm.md](references/visual-validation/snapshot-testing-spm.md) |
| Blank screenshots, focus failures, permission gotchas | [references/visual-validation/troubleshooting.md](references/visual-validation/troubleshooting.md) |

### Quality hooks

| Topic | File |
|---|---|
| 4-stage hook architecture rationale | [references/quality-hooks/hook-architecture.md](references/quality-hooks/hook-architecture.md) |
| Greenfield empty baseline vs `--write-baseline` for legacy | [references/quality-hooks/baseline-workflow.md](references/quality-hooks/baseline-workflow.md) |
| Typecheck stage opt-in + speed flags | [references/quality-hooks/typecheck-stage.md](references/quality-hooks/typecheck-stage.md) |
| SwiftLint config rationale | [references/quality-hooks/configs/swiftlint-config.md](references/quality-hooks/configs/swiftlint-config.md) |
| SwiftFormat config rationale | [references/quality-hooks/configs/swiftformat-config.md](references/quality-hooks/configs/swiftformat-config.md) |
| Hook failure debugging | [references/quality-hooks/troubleshooting.md](references/quality-hooks/troubleshooting.md) |
| Per-platform xcodebuild destination matrix | [references/quality-hooks/platforms/macos.md](references/quality-hooks/platforms/macos.md), [ios.md](references/quality-hooks/platforms/ios.md), [tvos.md](references/quality-hooks/platforms/tvos.md), [watchos.md](references/quality-hooks/platforms/watchos.md), [visionos.md](references/quality-hooks/platforms/visionos.md), [multiplatform.md](references/quality-hooks/platforms/multiplatform.md) |

### Cloud sync (Convex + Clerk)

See the **Cloud Sync** section above for the full routing table.

### Workflow

| Topic | File |
|---|---|
| Bootstrapping a fresh app end-to-end | [references/workflow/bootstrap-new-app.md](references/workflow/bootstrap-new-app.md) |
| Auditing existing code (severity-tagged report) | [references/workflow/audit-existing.md](references/workflow/audit-existing.md) |
| Pre-release ship checklist | [references/workflow/ship-checklist.md](references/workflow/ship-checklist.md) |

---

## Output contract

When you finish work in this skill, end with:

- **What changed**: file paths + one-line per change.
- **Verification rung reached**: which level of validation you actually completed.

  | Rung | Meaning |
  |---|---|
  | 1 | Read the code |
  | 2 | Type-check / lint passes |
  | 3 | Unit tests pass |
  | 4 | Snapshot tests pass |
  | 5 | Ran the program; observed the change |
  | 6 | User confirmed the changed behavior |

- **What's next**: explicit next action if anything remains.

Never claim "done" while:
- The working tree is dirty (commit first, then claim).
- Any guardrail above is violated.
- The verification rung you reached is below the rung the user requires.
