---
name: develop-macos-liquid-glass
description: Build, migrate, or review macOS apps with Apple's Liquid Glass design system (macOS 26 Tahoe+). Use when implementing .glassEffect() on macOS, creating glass toolbars/sidebars/windows in SwiftUI, bridging to NSGlassEffectView in AppKit, migrating from NSVisualEffectView, or reviewing macOS Liquid Glass code for correctness. Trigger terms include macOS glass effect, macOS Tahoe design, SwiftUI macOS glass, NSGlassEffectView, glass toolbar macOS, migrate macOS glass, Liquid Glass macOS. Do NOT use for iOS-only glass (use liquid-glass skill), web glassmorphism CSS, visionOS spatial glass, or general SwiftUI without glass context.
---

# Develop macOS Liquid Glass

Build, migrate, and review macOS apps using Apple's Liquid Glass design language (macOS 26 Tahoe+). Covers both SwiftUI and AppKit.

## Trigger Boundary

### Use this skill when

- Building new macOS SwiftUI views with Liquid Glass
- Adding `.glassEffect()` to macOS toolbars, sidebars, or custom controls
- Using `NSGlassEffectView` or `NSGlassEffectContainerView` in AppKit
- Migrating an existing macOS app to Liquid Glass (from NSVisualEffectView or materials)
- Reviewing macOS glass implementation for correctness, performance, or design alignment
- Working with macOS-specific glass patterns: window styles, toolbar glass, sidebar glass, inspector panels
- Bridging between SwiftUI glass and AppKit glass

### Do NOT use this skill when

- Working on iOS-only glass features (use the `liquid-glass` skill)
- Building web glassmorphism with CSS
- Working on visionOS spatial glass
- General SwiftUI development without Liquid Glass context
- Building for watchOS or tvOS glass (minimal glass API, auto-applied)

## Core Principle

**Glass is for the navigation layer only.** Apply glass to toolbars, sidebars, floating controls, sheets, and popovers. Never apply glass to content (lists, tables, media, text blocks).

## Workflow

Choose the path that matches the request:

### Path 1: Build a new macOS feature with Liquid Glass

1. **Identify glass surfaces** -- which elements belong to the navigation layer?
2. **Choose glass variant** -- `.regular` (95% of cases) or `.clear` (media-rich backgrounds only; never mix with `.regular`)
3. **Read** `references/api-reference.md` for the API you need
4. **Read** `references/macos-patterns.md` for the macOS pattern (toolbar, sidebar, window, inspector)
5. **Implement** following the modifier order rule: layout modifiers first, then `.glassEffect()` last
6. **Wrap** grouped glass elements in `GlassEffectContainer`
7. **Add** `.backgroundExtensionEffect()` where content extends behind navigation
8. **Gate** with `#available(macOS 26, *)` and provide non-glass fallback
9. **Test** accessibility (Reduce Transparency, Increase Contrast, Reduce Motion)
10. **Review** against the checklist below

### Path 2: Migrate an existing macOS app to Liquid Glass

1. **Read** `references/migration-guide.md` for the 5-phase workflow
2. **Compile** with Xcode 26 -- system components auto-adopt glass
3. **Remove** conflicting customizations (`.toolbarBackground()`, `.presentationBackground()`, custom materials)
4. **Enhance** with glass APIs (`.backgroundExtensionEffect()`, `GlassEffectContainer`, glass button styles)
5. **Refine** for macOS: `.tint(.clear)` on buttons, `scrollEdgeEffectStyle`, control sizing
6. **Bridge** to AppKit where needed -- read `references/appkit-bridging.md`
7. **Test** accessibility and backward compatibility
8. **Check** for known pitfalls -- read `references/pitfalls-and-solutions.md`

### Path 3: Review macOS Liquid Glass implementation

1. **Run** the review checklist below
2. **Check** for pitfalls -- read `references/pitfalls-and-solutions.md`
3. **Verify** macOS-specific patterns -- read `references/macos-patterns.md`
4. **Report** findings with severity and fix recommendations

## Quick API Reference (macOS)

### SwiftUI Glass

```swift
// Basic glass effect
view.glassEffect(.regular, in: .rect(cornerRadius: 16))

// Glass button styles
Button("Action") { }.buttonStyle(.glass)           // Secondary
Button("Save") { }.buttonStyle(.glassProminent)     // Primary

// Container for multiple glass elements (required)
GlassEffectContainer(spacing: 16) {
    glassViewA.glassEffect().glassEffectID("a", in: ns)
    glassViewB.glassEffect().glassEffectID("b", in: ns)
}

// Extend content behind sidebar/toolbar
Image("hero").backgroundExtensionEffect()

// macOS scroll edge default
List { }.scrollEdgeEffectStyle(.hard, for: .top)
```

### AppKit Glass

```swift
// Glass view (replaces NSVisualEffectView for Liquid Glass)
let glass = NSGlassEffectView()
glass.contentView = myView
glass.cornerRadius = 12
glass.tintColor = .systemBlue

// Container (does NOT propagate cornerRadius)
let container = NSGlassEffectContainerView()
container.contentView = stackView

// Glass button bezel
button.bezelStyle = .glass
button.tintProminence = .primary

// Toolbar badge
toolbarItem.badge = NSItemBadge.count(4)
```

### Variant Selection

| Variant | When to use | Transparency |
|---------|------------|--------------|
| `.regular` | 95% of cases. Toolbars, buttons, sidebars, controls. | Medium |
| `.clear` | Media-rich backgrounds where content is bold/bright. | High |
| `.identity` | Conditionally disable glass (accessibility). | None |

**Rule:** Never mix `.regular` and `.clear` in the same view hierarchy.

### macOS-Specific Rules

- **`.interactive()` is iOS-only** -- do not use on macOS; use `.onHover {}` instead
- **`.tint(.clear)`** on glass buttons for correct macOS rendering
- **`.scrollEdgeEffectStyle(.hard)`** is the macOS default (iOS defaults to `.soft`)
- **`prefersCompactControlSizeMetrics = true`** to revert taller controls to pre-Tahoe sizing
- **TabView on macOS** uses `.tabViewStyle(.sidebarAdaptable)` (sidebar), not floating tab bar

### Window Corner Radii (macOS 26)

| Window Type | Radius | When |
|------------|--------|------|
| No toolbar (titlebar-only) | ~12pt | Plain windows, settings |
| Compact toolbar | ~20pt | Icon-only toolbars |
| Standard toolbar | ~26pt | Full toolbar |

No public API to control. Use `NSView.LayoutRegion` for corner avoidance in AppKit.

## Decision Rules

- If the element is part of the **navigation layer** (toolbar, sidebar, floating control, sheet) -> apply glass
- If the element is **content** (list, table, text, media) -> do NOT apply glass
- If multiple glass elements are **near each other** -> wrap in `GlassEffectContainer`
- If glass needs to **morph between states** -> use `@Namespace` + `glassEffectID`
- If the view needs to **extend behind navigation** -> add `.backgroundExtensionEffect()`
- If targeting **pre-Tahoe macOS** -> gate with `#available(macOS 26, *)` and fallback to `.ultraThinMaterial`
- If SwiftUI `.toolbar` is **insufficient** -> bridge to `NSToolbar` (read `references/appkit-bridging.md`)
- If using `NSVisualEffectView` -> consider migrating to `NSGlassEffectView` (read `references/migration-guide.md`)

## Do This, Not That

| Do this | Not that |
|---------|---------|
| Apply glass to navigation-layer elements only | Apply glass to content (lists, cards, text) |
| Use `GlassEffectContainer` for groups | Put multiple standalone `.glassEffect()` calls near each other |
| Use `.tint(.clear)` on macOS glass buttons | Use default tinting (renders incorrectly on macOS) |
| Remove `.toolbarBackground()` on macOS 26 | Keep custom toolbar backgrounds (blocks glass) |
| Use `.scrollEdgeEffectStyle(.hard)` (macOS default) | Assume `.soft` like iOS |
| Gate with `#available(macOS 26, *)` | Assume macOS 26 is the minimum |
| Use `.regular` variant (95% of cases) | Use `.clear` unless you have a media-rich background |
| Test with Reduce Transparency, Increase Contrast | Assume accessibility settings work automatically |
| Bridge to AppKit for NSToolbar customization | Fight SwiftUI `.toolbar` limitations |
| Remove `.presentationBackground()` on sheets | Override system glass on sheets |

## Reference Routing

| Reference | Read when |
|-----------|-----------|
| `references/api-reference.md` | Looking up any Liquid Glass API (SwiftUI or AppKit), checking macOS vs iOS availability, or verifying API signatures |
| `references/macos-patterns.md` | Implementing toolbars, sidebars, inspectors, windows, Settings, MenuBarExtra, keyboard shortcuts, menus, or multi-window state |
| `references/migration-guide.md` | Migrating an existing macOS app to Liquid Glass, moving from NSVisualEffectView, or adding backward compatibility |
| `references/pitfalls-and-solutions.md` | Debugging glass rendering issues, checking for known bugs, or auditing for common mistakes |
| `references/appkit-bridging.md` | Bridging SwiftUI to AppKit for glass, using NSGlassEffectView in SwiftUI, or deciding when to bridge |

## Review Checklist

### Glass Placement
- [ ] Glass applied only to navigation-layer elements (toolbars, sidebars, floating controls, sheets)
- [ ] No glass on content (lists, tables, media, text blocks)
- [ ] `.regular` variant used unless media-rich background justifies `.clear`

### Container and Grouping
- [ ] Grouped glass elements wrapped in `GlassEffectContainer`
- [ ] `GlassEffectContainer` spacing parameter tuned for layout
- [ ] No standalone glass effects that should be grouped

### macOS-Specific
- [ ] `.tint(.clear)` on glass buttons for macOS rendering
- [ ] No `.interactive()` calls (iOS-only)
- [ ] `.scrollEdgeEffectStyle` matches intended behavior (macOS defaults to `.hard`)
- [ ] TabView uses `.tabViewStyle(.sidebarAdaptable)` on macOS
- [ ] Window style and toolbar style are appropriate for the app type

### Modifier Order
- [ ] `.glassEffect()` applied after layout and appearance modifiers
- [ ] `glassEffectID` used with `@Namespace` for morphing transitions
- [ ] `withAnimation` wraps state changes that trigger morphing

### Migration
- [ ] Custom `.toolbarBackground()` removed
- [ ] Custom `.presentationBackground()` removed on sheets
- [ ] Custom materials removed from navigation elements
- [ ] `.backgroundExtensionEffect()` added where content extends behind navigation

### Backward Compatibility
- [ ] `#available(macOS 26, *)` gates all Liquid Glass APIs
- [ ] Non-glass fallback provided (`.ultraThinMaterial` or plain background)
- [ ] No `.interactive()` leaking to macOS code paths

### Accessibility
- [ ] Tested with Reduce Transparency (glass becomes frosted)
- [ ] Tested with Increase Contrast (adds high-contrast borders)
- [ ] Tested with Reduce Motion (dampens animations)
- [ ] Text contrast sufficient over glass surfaces
- [ ] VoiceOver navigation works through glass elements
- [ ] Keyboard navigation (Tab/Shift+Tab) functions correctly

### Performance
- [ ] Glass elements grouped in containers (shared sampling)
- [ ] No glass applied to individual scroll items (glass on overlay/header instead)
- [ ] Tested on target hardware (Intel Macs may show ~45fps with 5-6 overlapping glass views)

## WWDC 2025 Sessions

| Session | When to watch |
|---------|---------------|
| **219: Meet Liquid Glass** | Understanding design principles, material variants, component hierarchy |
| **310: Build an AppKit app with the new design** | macOS-specific: NSGlassEffectView, NSToolbar, NSSplitView, controls |
| **323: Build a SwiftUI app with the new design** | SwiftUI APIs, .glassEffect, GlassEffectContainer, toolbar, sidebar |
| **356: Get to know the new design system** | Design guidelines, concentricity, shapes, scroll edge effects |
