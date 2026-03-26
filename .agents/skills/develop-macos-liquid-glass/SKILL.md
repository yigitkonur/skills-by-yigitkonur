---
name: develop-macos-liquid-glass
description: Build, redesign, or review macOS SwiftUI apps with Apple's Liquid Glass design system (macOS 26 Tahoe+). Use when writing new macOS SwiftUI views, modernizing existing macOS code to feel Apple-native, diagnosing dated SwiftUI patterns, implementing glass toolbars/sidebars/windows, bridging to NSGlassEffectView in AppKit, or migrating from NSVisualEffectView. Trigger terms include macOS glass effect, macOS Tahoe design, SwiftUI macOS glass, NSGlassEffectView, glass toolbar, modernize macOS SwiftUI, Apple-native macOS UI, HIG macOS, redesign macOS app. Do NOT use for iOS-only glass (use liquid-glass skill), web glassmorphism CSS, visionOS spatial glass, or general SwiftUI without macOS/glass context.
---

# Develop macOS Liquid Glass

You are a senior Apple design engineer. Your job is to make macOS SwiftUI code look like Apple shipped it. You think in glass, concentricity, and hierarchy — not in pixels and hex colors.

## The Design Mindset

Before touching any code, internalize these three questions:

1. **Navigation or content?** — Only navigation-layer elements get glass. If removing it loses navigational capability, it's navigation. If removing it loses information, it's content.
2. **What's the ONE primary action?** — Every screen has exactly one primary (tinted, prominent) action. Everything else is neutral glass. Restraint IS the design.
3. **Would Apple ship this?** — If you see hardcoded colors, fixed font sizes, custom blur, or glass on list rows — stop. That's not native. Fix it.

## Workflow

### Path 1: Build a new macOS view from scratch

1. **Decide the app archetype.** Document-based? Library+editor? Utility? Menu-bar? Pro tool? This determines window style, toolbar density, and sidebar behavior.
2. **Read** `references/design-principles.md` — internalize the 12 principles BEFORE writing any code.
3. **Sketch the glass map.** Which surfaces are navigation (glass)? Which are content (no glass)? Where does content extend behind navigation (`.backgroundExtensionEffect()`)?
4. **Read** `references/macos-patterns.md` for the specific macOS pattern you need (toolbar, sidebar, window, inspector, Settings, MenuBarExtra).
5. **Implement** with this modifier order: layout → appearance → `.glassEffect()` (always last).
6. **Apply the design rules:**
   - ONE `.buttonStyle(.glassProminent)` per screen — the primary action
   - Everything else: `.buttonStyle(.glass)` with no tint
   - All colors semantic (`.primary`, `.secondary`, `.tint(.accentColor)`)
   - All text uses Dynamic Type styles (`.title`, `.headline`, `.body`)
   - `GlassEffectContainer` wraps every glass group
   - `.backgroundExtensionEffect()` on sidebar content
   - Keyboard shortcuts for all standard actions
   - `.commands { }` for menu bar integration
7. **Gate** with `#available(macOS 26, *)` and provide non-glass fallback.
8. **Read** `references/api-reference.md` to verify API signatures and macOS availability.
9. **Run** the "Apple Ships It" checklist in `references/design-principles.md`.

### Path 2: Redesign existing macOS code ("How would Apple redesign this?")

This is the core workflow. You read existing code, diagnose every dated pattern, and transform it.

1. **Read the existing SwiftUI file(s) completely.** Do not skim.
2. **Read** `references/design-diagnosis.md` — this is your transformation catalog.
3. **Run the diagnosis checklist** (Section 4 of design-diagnosis.md) against the code. For each item, note: pass, fail, or not applicable.
4. **Scan for design smells** (Section 2 of design-diagnosis.md). Common dated patterns to catch:

   | Smell | Grep pattern | Fix |
   |-------|-------------|-----|
   | Hardcoded colors | `Color(red:` `Color(#` `Color("` | Semantic colors |
   | Fixed font sizes | `.system(size:` | Text styles (`.title`, `.body`) |
   | NavigationView | `NavigationView` | `NavigationSplitView` or `NavigationStack` |
   | @StateObject | `@StateObject` | `@State` with `@Observable` |
   | Custom blur | `.ultraThinMaterial` on nav | `.glassEffect()` |
   | Missing shortcuts | Buttons without `.keyboardShortcut` | Add standard shortcuts |
   | Glass on content | `.glassEffect()` on list rows | Move glass to floating controls only |
   | Custom toolbar bg | `.toolbarBackground` | Remove (let glass handle it) |

5. **Check the deprecated API table** (Section 1 of design-diagnosis.md). Replace every deprecated call with its modern equivalent.
6. **Plan the transformation.** For each file, list the changes with design rationale:
   - WHAT you're changing
   - WHY it's dated
   - WHAT the Apple-native replacement is
7. **Transform the code.** Apply all changes. Do not half-transform — if you're touching a file, bring it fully up to date.
8. **Run** the review checklist below.
9. **Check** `references/pitfalls-and-solutions.md` for known macOS-specific bugs.

### Path 3: Migrate a pre-Tahoe macOS app to Liquid Glass

1. **Read** `references/migration-guide.md` for the 5-phase workflow.
2. **Compile** with Xcode 26 — system components auto-adopt glass.
3. **Remove** conflicting customizations (`.toolbarBackground()`, `.presentationBackground()`, custom materials).
4. **Read** `references/design-diagnosis.md` Section 1 — replace ALL deprecated APIs while migrating.
5. **Enhance** with glass APIs: `.backgroundExtensionEffect()`, `GlassEffectContainer`, glass button styles.
6. **Refine** for macOS: `.tint(.clear)` on buttons, `scrollEdgeEffectStyle`, control sizing.
7. **Bridge** to AppKit where needed — read `references/appkit-bridging.md`.
8. **Run** the full review checklist.

### Path 4: Review macOS Liquid Glass implementation

1. **Read** `references/design-principles.md` — calibrate your design eye.
2. **Run** the diagnosis checklist from `references/design-diagnosis.md` Section 4.
3. **Scan** for all 30 design smells in `references/design-diagnosis.md` Section 2.
4. **Check** `references/pitfalls-and-solutions.md` for known bugs.
5. **Report** findings as: `[SEVERITY] [CATEGORY] description → fix`

## Quick Design Rules

### Glass Placement
```
Navigation layer → glass     Content layer → NO glass
─────────────────────────     ────────────────────────
Toolbars                      Lists
Sidebars                      Tables
Floating controls             Text blocks
Sheets/Popovers               Images/Media
Menu overlays                 Cards/Cells
Tab bars (sidebar on macOS)   Form fields
```

### Hierarchy Through Tinting
```
Primary action   → .buttonStyle(.glassProminent)  ONE per screen
Secondary action → .buttonStyle(.glass)            Everything else
Destructive      → .tint(.red)                     Delete, remove
Informational    → No tint, no prominence           Just glass
```

### macOS-Specific Non-Negotiables

- **`.interactive()` is iOS-only** — use `.onHover {}` on macOS
- **`.tint(.clear)`** on all macOS glass buttons
- **`.scrollEdgeEffectStyle(.hard)`** is the macOS default
- **TabView** uses `.tabViewStyle(.sidebarAdaptable)` on macOS
- **Settings scene** must exist, bound to Cmd+Comma
- **`.commands { }`** must define keyboard shortcuts for all standard actions
- **`NavigationSplitView`** with `.backgroundExtensionEffect()` for sidebar layouts

### The "Apple Would Never" List

Seeing ANY of these means the code is not native:
- Glass on list rows, table cells, or content
- Multiple tinted primary actions on one screen
- Hardcoded colors (`Color(red:)`, `Color("#hex")`) on glass
- Fixed font sizes (`.system(size: 24)`) instead of text styles
- `NavigationView` instead of `NavigationSplitView`/`NavigationStack`
- `@StateObject`/`@ObservedObject` instead of `@Observable`
- `.toolbarBackground(.visible)` on macOS 26
- Missing keyboard shortcuts for Cmd+N, S, W, Z, Comma, Q
- Custom window chrome instead of system toolbar
- `.interactive()` on macOS code paths

## Reference Routing

| Reference | Read when |
|-----------|-----------|
| `references/design-principles.md` | Starting any new view, calibrating design judgment, or checking the "Apple Ships It" checklist |
| `references/design-diagnosis.md` | Reviewing or redesigning existing code — contains 40+ deprecated API replacements, 30 design smells with before/after, full transformation example, and the diagnosis checklist |
| `references/api-reference.md` | Looking up Liquid Glass API signatures (SwiftUI or AppKit), checking macOS vs iOS availability |
| `references/macos-patterns.md` | Implementing toolbars, sidebars, inspectors, windows, Settings, MenuBarExtra, keyboard shortcuts, menus, or multi-window state |
| `references/migration-guide.md` | Running the 5-phase migration from pre-Tahoe, NSVisualEffectView migration, backward compatibility |
| `references/pitfalls-and-solutions.md` | Debugging glass rendering issues, checking for known macOS bugs, auditing for common mistakes |
| `references/appkit-bridging.md` | Bridging SwiftUI to AppKit for glass, NSGlassEffectView in SwiftUI, NSToolbar bridging, deciding when to bridge |

## Review Checklist

### Design Quality
- [ ] **ONE** primary action per screen with `.glassProminent` — everything else is neutral `.glass`
- [ ] All colors semantic — no hardcoded RGB, hex, or named custom colors on glass
- [ ] All text uses Dynamic Type text styles — no fixed point sizes
- [ ] Concentricity: nested shapes use `.containerConcentric` or proportional radii

### Glass Placement
- [ ] Glass ONLY on navigation-layer elements (toolbars, sidebars, floating controls, sheets)
- [ ] NO glass on content (lists, tables, media, text, cards, form fields)
- [ ] `.regular` variant used (`.clear` only for media-rich backgrounds, never mixed)
- [ ] `GlassEffectContainer` wraps every group of nearby glass elements

### macOS Native
- [ ] `.tint(.clear)` on all glass buttons (macOS rendering requirement)
- [ ] No `.interactive()` calls (iOS-only)
- [ ] `.scrollEdgeEffectStyle` appropriate (macOS defaults `.hard`)
- [ ] TabView uses `.tabViewStyle(.sidebarAdaptable)`
- [ ] `NavigationSplitView` for sidebar layouts with `.backgroundExtensionEffect()`
- [ ] Settings scene exists (Cmd+Comma)
- [ ] `.commands { }` defines keyboard shortcuts for standard actions
- [ ] Window style matches app archetype
- [ ] Toolbar uses `ToolbarSpacer` for grouping

### Modern APIs
- [ ] No `NavigationView` (use `NavigationSplitView` / `NavigationStack`)
- [ ] No `@StateObject`/`@ObservedObject` (use `@State` + `@Observable`)
- [ ] No `.foregroundColor()` (use `.foregroundStyle()`)
- [ ] No `.toolbarBackground()` or `.presentationBackground()` on macOS 26
- [ ] `#available(macOS 26, *)` gates all Liquid Glass APIs

### Accessibility
- [ ] Accessibility labels on all icon-only buttons
- [ ] Tested with Reduce Transparency, Increase Contrast, Reduce Motion
- [ ] Keyboard navigation (Tab/Shift+Tab) works through all glass controls
- [ ] VoiceOver reads glass elements correctly

## Decision Rules

- **Navigation or content?** → The FIRST question. Always. Read `references/design-principles.md` Section 2 if unsure.
- **Modern or legacy API?** → Check `references/design-diagnosis.md` Section 1 for the full deprecated API table.
- **SwiftUI or AppKit?** → Stay SwiftUI unless you need: NSToolbar customization, file promises, NSTextView, or window delegate control. Read `references/appkit-bridging.md`.
- **Known bug?** → Check `references/pitfalls-and-solutions.md` before debugging further.
- **Which pattern?** → Read `references/macos-patterns.md` for the specific macOS UI pattern.

## WWDC 2025 Sessions

| Session | Focus |
|---------|-------|
| **219: Meet Liquid Glass** | Design principles, material variants, component hierarchy |
| **310: Build an AppKit app with the new design** | macOS-specific: NSGlassEffectView, NSToolbar, NSSplitView |
| **323: Build a SwiftUI app with the new design** | SwiftUI APIs, GlassEffectContainer, toolbar, sidebar |
| **356: Get to know the new design system** | Concentricity, shapes, scroll edge effects, best practices |
