# macOS Sidebars, Source Lists, Split Views & Inspectors — Definitive Reference

> **Scope:** macOS only. All dimensions exact. API references for both AppKit and SwiftUI.
> **Sources:** Apple SDK headers (NSSplitViewItem.h, NSSplitViewController.h, NSSplitView.h, NSTableView.h, NSVisualEffectView.h), SwiftUI .swiftinterface, WWDC 2023 Session 10161, Apple HIG JSON API, community verification.

---

## 1. Sidebar Types

macOS recognizes three functional sidebar types via `NSSplitViewItem` behavior:

### Navigation Sidebar (`NSSplitViewItemBehaviorSidebar`)
Primary left-column panel for structural navigation (Finder, Mail, Notes, Xcode). Created with `NSSplitViewItem.sidebar(withViewController:)`.

- Translucent material background (vibrancy)
- Collapsible from user drag and window resize
- `springLoaded = YES` (temporarily reveals on drag hover)
- `canCollapseFromWindowResize = YES`
- `preferredThicknessFraction = 0.15` (15% of split view width)

### Content List (`NSSplitViewItemBehaviorContentList`)
Secondary structural column (Mail's message list, Notes' note list). Created with `NSSplitViewItem.contentList(withViewController:)`.

- `preferredThicknessFraction = 0.28` when sidebar visible; `0.33` without sidebar
- Opaque or lightly styled background

### Source List (Visual sub-type of Navigation Sidebar)
Not a separate behavior — it's the visual rendering style applied via `NSTableViewStyle.sourceList` (macOS 11.0+).

- Rounded-rectangle selection highlight in accent color
- Group row headers in small-caps uppercase, no background
- Typically in NSOutlineView (hierarchical) or NSTableView (flat)

### Inspector (`NSSplitViewItemBehaviorInspector`, macOS 11.0+)
Trailing panel for contextual detail. Created with `NSSplitViewItem.inspector(withViewController:)`.

- Standard system size: **270pt** (min = max, fixed by default)
- To enable user resizing, override with explicit min/max thickness
- `canCollapse = YES`

---

## 2. Sidebar Specs

### Width Dimensions

| Property | Value | Source |
|---|---|---|
| Sidebar `preferredThicknessFraction` | **0.15** (15%) | NSSplitViewItem.h |
| Content list fraction (with sidebar) | **0.28** | NSSplitViewItem.h |
| Content list fraction (no sidebar) | **0.33** | NSSplitViewItem.h |
| Inspector standard size | **270pt** (fixed) | NSSplitViewItem.h |

**Practical sidebar widths** (fraction x window width):
- 1000pt window → ~150pt
- 1200pt window → ~180pt
- 1440pt window → ~216pt

Commonly observed range in first-party apps: **160–400pt**.

**SwiftUI width override:**
```swift
.navigationSplitViewColumnWidth(200)                          // Fixed
.navigationSplitViewColumnWidth(min: 150, ideal: 220, max: 400) // Flexible
```

### Material and Vibrancy

| Component | Material | AppKit Enum | Since |
|---|---|---|---|
| Navigation sidebar | Sidebar | `NSVisualEffectMaterial.sidebar` (= 7) | macOS 10.11+ |
| Window background | Window background | `NSVisualEffectMaterial.windowBackground` (= 12) | macOS 10.14+ |
| Titlebar | Titlebar | `NSVisualEffectMaterial.titlebar` (= 3) | macOS 10.10+ |

The sidebar material is **semantic**: auto-adapts Light/Dark and respects "Reduce Transparency." Default blending: `.behindWindow`.

In SwiftUI, `List` with `.listStyle(.sidebar)` applies this material automatically.

---

## 3. Source Lists

### Visual Anatomy

| Row type | Rendering |
|---|---|
| Group row (section header) | Small-caps uppercase; no background; secondary text color |
| Regular item | Full-width; rounded-rect selection highlight in accent color |
| Expandable parent | Disclosure triangle on left |
| Leaf child | Indented, no disclosure triangle |

### Item Iconography
- Use SF Symbols at `.small`/`.medium` scale (16x16pt equivalent)
- Symbols render with system tint/accent color when selected
- Stick to symbolic, single-color icons

### Badges
- SwiftUI: `.badge(_:)` on `Label` inside sidebar `List`
- Short numeric counts ("12", "99+")
- Color adapts to selection state

### Selection Behavior
- Single selection is standard
- Persist with `@SceneStorage` or explicit state
- First-responder status changes highlight emphasis

---

## 4. Split Views

### Divider Styles

| Style | Enum | Description |
|---|---|---|
| `NSSplitViewDividerStyleThick` | 1 | Default for standalone NSSplitView; ~8–10pt with grab handle |
| `NSSplitViewDividerStyleThin` | 2 | Default for NSSplitViewController; **1pt hairline** |
| `NSSplitViewDividerStylePaneSplitter` | 3 | Deprecated aesthetic |

**NSSplitViewController always defaults to thin.** The hit target for thin dividers is expanded beyond the drawn frame for easier grabbing.

### Drag Behavior
- Delegate constrains positions via `splitView(_:constrainSplitPosition:ofSubviewAt:)`
- `holdingPriority` determines which pane absorbs resize pressure
- Default: `NSLayoutPriority.defaultLow`

### Proportional Resize
On window resize, `adjustSubviews` resizes all non-collapsed subviews proportionally. Override `splitView(_:shouldAdjustSizeOfSubview:)` to pin specific panes.

---

## 5. Layout Patterns

### Two-Column Layout
```
┌─────────────┬────────────────────────────────┐
│  Sidebar    │       Detail / Content         │
│  (leading)  │       (trailing)               │
└─────────────┴────────────────────────────────┘
```
SwiftUI: `NavigationSplitView { sidebar } detail: { detail }`

### Three-Column Layout (Mail Pattern)
```
┌───────────┬─────────────────┬────────────────┐
│ Sidebar   │  Content List   │    Detail      │
│ (leading) │  (middle)       │  (trailing)    │
└───────────┴─────────────────┴────────────────┘
```
SwiftUI: `NavigationSplitView { sidebar } content: { list } detail: { detail }`

| Column | preferredThicknessFraction |
|---|---|
| Sidebar | 0.15 |
| Content list (sidebar visible) | 0.28 |
| Content list (sidebar hidden) | 0.33 |
| Detail | Remainder |

### Three-Column with Inspector (Xcode Pattern)
```
┌───────────┬─────────────────────────┬──────────┐
│ Navigator │     Main Editor         │Inspector │
│ Sidebar   │                         │(trailing)│
└───────────┴─────────────────────────┴──────────┘
```
Inspector uses `NSSplitViewItemBehaviorInspector` (AppKit 11.0+) or `.inspector` (SwiftUI 14.0+).

---

## 6. Inspectors

### Specs

| Property | Value |
|---|---|
| Standard system size | **270pt** (min = max) |
| Not user-resizable by default | Yes |
| SwiftUI WWDC demo widths | min: 200pt, ideal: 300pt, max: 400pt |
| Placement | Trailing edge |
| AppKit availability | macOS 11.0 |
| SwiftUI `.inspector` availability | macOS 14.0 |

### Behavior

| Context | Behavior |
|---|---|
| Outside NavigationStack/SplitView | Full-height trailing column |
| Inside NavigationStack/SplitView | Under-toolbar placement |
| Compact horizontal size class | Automatically presents as sheet |

### SwiftUI Inspector
```swift
.inspector(isPresented: $inspectorShown) {
    InspectorContent()
        .inspectorColumnWidth(min: 200, ideal: 270, max: 400)
}
```

---

## 7. Collapse Behavior

### Sidebar Collapse

**Automatic:** `canCollapseFromWindowResize = true` (default). Collapses when window shrinks below minimum.

**Fullscreen:** Auto-collapsed sidebars re-appear as **overlays** (sliding from left edge).

**Double-click collapse:** Deprecated since macOS 10.15 — never called.

**AppKit programmatic:**
```swift
// Animated (0.25s, easeOut — matches system behavior)
NSAnimationContext.runAnimationGroup { context in
    context.duration = 0.25
    context.timingFunction = CAMediaTimingFunction(name: .easeOut)
    splitViewItem.animator().isCollapsed = true
}
```

**SwiftUI:**
```swift
@State private var columnVisibility = NavigationSplitViewVisibility.all
// Hide sidebar:
columnVisibility = .detailOnly
// Show both:
columnVisibility = .all
```

### NavigationSplitViewVisibility Cases

| Case | Effect |
|---|---|
| `.all` | All columns visible |
| `.doubleColumn` | Hide leading column |
| `.detailOnly` | Only detail visible |
| `.automatic` | System chooses |

### State Persistence
Set `NSSplitView.autosaveName` (AppKit) or use `@SceneStorage` (SwiftUI).

---

## 8. Do's and Don'ts

### Do
- Use `NSSplitViewItem.sidebar(withViewController:)` for system-standard behavior
- Use `.inspector(isPresented:)` (SwiftUI 14.0+) for trailing panels
- Apply `.listStyle(.sidebar)` in SwiftUI for correct material
- Use `NSTableViewStyle.sourceList` (macOS 11.0+) for source list aesthetics
- Set `autosaveName` on NSSplitView to persist divider positions
- Use SF Symbols for sidebar icons
- Use `inspectorColumnWidth(min:ideal:max:)` when inspector needs resizing

### Don't
- Don't set identical min/max thickness on resizable sidebars (locks width)
- Don't rely on double-click collapse (deprecated macOS 10.15)
- Don't use `NSVisualEffectMaterial.light` or `.dark` (deprecated)
- Don't use `NSTableViewSelectionHighlightStyleSourceList` (deprecated macOS 12.0)
- Don't use `NavigationView` with sidebar style (deprecated macOS 12.0)
- Don't place heavy content in inspectors — they show contextual metadata
- Don't over-customize sidebar row height — breaks system consistency

---

## 9. Sources

| Source | Type |
|---|---|
| NSSplitViewItem.h (Xcode SDK) | Official Apple SDK header |
| NSSplitViewController.h (Xcode SDK) | Official Apple SDK header |
| NSSplitView.h (Xcode SDK) | Official Apple SDK header |
| NSTableView.h (Xcode SDK) | Official Apple SDK header |
| NSVisualEffectView.h (Xcode SDK) | Official Apple SDK header |
| SwiftUI .swiftinterface (arm64e-apple-macos) | Official Apple SDK binary |
| WWDC 2023 Session 10161 "Inspectors in SwiftUI" | Official Apple WWDC |
| Apple HIG JSON API | Official Apple documentation |
| Stack Overflow (sidebar collapse animation) | Practitioner evidence |
| Reddit r/SwiftUI (inspector threads 2023–2025) | Community evidence |

---

## 10. macOS 26 (Tahoe) Floating Sidebar Changes

> **Availability:** macOS 26.0+ (Xcode 26 SDK required for automatic adoption)

### What Changed

Sidebars adopt a **floating Liquid Glass panel** visual instead of edge-attached translucent vibrancy. The physical attachment is unchanged (same NSSplitView column), but rendering material is now `NSGlassEffectView` instead of `NSVisualEffectView`.

| Dimension | macOS 10.11–15 | macOS 26 (Tahoe) |
|---|---|---|
| Material | `NSVisualEffectView` (sidebar) | `NSGlassEffectView` (Liquid Glass) |
| Edge attachment | True edge-to-edge, behind toolbar | Visually floating; inset with padding |
| Background | Behind-window blur | Lens-samples content behind sidebar panel |
| Color pickup | None | Ambient from adjacent content (automatic) |

### API Changes

**AppKit:** Automatic with Xcode 26 SDK. New properties:
```swift
// Let content extend under the floating sidebar
splitViewItem.automaticallyAdjustsSafeAreaInsets = true

// Per-split-item accessories (macOS 26+)
splitViewItem.addTopAlignedAccessoryViewController(accessory)
```

**SwiftUI:** `NavigationSplitView` auto-adopts. New modifiers:
```swift
SidebarView()
    .backgroundExtensionEffect()   // extends glass beyond safe area

SomeView()
    .glassEffect(in: RoundedRectangle(cornerRadius: 12))

GlassEffectContainer {
    // Groups glass elements to share one sampling region
}
```

### Migration Path

1. **Build with Xcode 26** — automatic Liquid Glass adoption
2. **Remove custom NSVisualEffectView** layered inside sidebar — blocks system material
3. **Remove custom `presentationBackground`** modifiers wrapping sidebar content
4. **Test insets** — sidebar now floats with padding; fixed top/bottom insets may look wrong

**Backward compatibility guard:**
```swift
if #available(macOS 26, *) {
    // NSGlassEffectView, glassEffect(), backgroundExtensionEffect()
}
```

**Opt out:** Apps can defer Liquid Glass via plist key (expected mandatory in Xcode 27).

### Known Issues

| Issue | Status |
|---|---|
| NSGlassEffectView fully transparent on window defocus with heavy tintColor | Bug (macOS 26.2) |
| NavigationSplitView floating sidebar requires top-level placement in WindowGroup | By design |
| Open panel sidebar too narrow to resize (26.0–26.1) | Fixed in later releases |
| Stacking glass on glass without GlassEffectContainer = visual inconsistency | By design |

**Sources:** WWDC25 Session 310 (AppKit), WWDC25 Session 323 (SwiftUI), ForkLift 4.4.3 release notes, Reddit r/SwiftUI, dev.to Liquid Glass best practices.
