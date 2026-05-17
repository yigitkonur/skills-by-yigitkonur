# macOS HIG Practitioner Insights

Community-sourced wisdom from real macOS developers and designers — what actually works,
what breaks, what Apple's own apps violate, and the gap between documentation and reality.

> This document captures the **practitioner voice**, not official documentation.
> Every finding is attributed to a specific community source.

---

## Summary

The macOS HIG is widely respected as a foundational document but is increasingly treated as a
reference rather than a rulebook — even by Apple itself. The central tension in 2023–2026 is
between SwiftUI's rapid adoption and its persistent secondary-citizen status on macOS: developers
consistently find that achieving a genuinely native macOS feel requires dipping into AppKit for
anything beyond basic layouts. Apple's own apps (System Settings, Music, Maps) violate HIG
conventions that third-party apps are expected to follow. Award-winning macOS apps (Things 3,
Craft, Pixelmator Pro, Raycast, IINA, Bear) succeed by combining strict HIG adherence for
structural patterns (window chrome, sidebar, keyboard shortcuts) with deliberate creative
departures for brand identity. The single greatest practitioner insight: **SwiftUI largely
implements HIG for you on iOS; on macOS, it fights you at every turn.**

---

## 1. Common Mistakes

### 1.1 Treating macOS as a Big iPad

**Mistake:** Using iOS-derived navigation patterns (tab bars at the bottom, full-screen sheets,
swipe-back gestures) without adapting them for macOS.

> "I don't know where I'm going wrong, but I just can't seem to make a very Mac-like UI with
> SwiftUI. It always ends up kind of janky and/or like it's a smartphone app, and usually both."
> — u/PerkeNdencen, r/SwiftUI, 2024

> "macOS and iOS/iPadOS are quite different in terms of navigation and gestures. Two apps/targets
> under the same workspace. Create one set of logic files that are shared between the two targets,
> then create separate UI/view files."
> — u/BL1860B, r/SwiftUI, 2025

**Consequence:** Users perceive the app as non-native and untrustworthy.

---

### 1.2 Settings Windows with Save/Cancel/Apply Buttons

**Mistake:** Displaying the app settings UI as a modal dialog or providing Save/Cancel/Apply buttons.

According to the macOS HIG (as analyzed by u/usagimaru, zenn.dev/usagimaru/articles/b2a328775124ef,
2024): settings changes on macOS should take effect immediately; the modal save-or-cancel pattern
is a Windows convention that violates macOS user expectations.

**Specific additional mistakes (same source):**
- Leaving minimize and maximize (yellow/green) buttons enabled in settings windows — HIG requires
  them dimmed
- Using "Preferences…" wording on macOS 13+ (system substitutes "Settings…" automatically but
  localized strings still need to support both)
- Omitting both icon AND label for each toolbar tab — leads to accessibility failures when the
  toolbar collapses
- Not persisting the last-selected tab across reopens
- Allowing toolbar customization in a settings window
- Using toggle switches for simple on/off settings instead of checkboxes

---

### 1.3 Ignoring the Full macOS App Contract

**Mistake:** Shipping an app that lacks the standard macOS "contract" features.

> "A Mac app should have a Help book, be scriptable, support the Services menu, and if it has
> documents, have a draggable proxy icon on the title bar that you can control-click to get the
> full path to the document. If it has text, it should support the full set of standard Edit menu
> commands (including undo and redo), the standard Find interface, and the standard contextual menu
> items. It should have Print. It should support side-by-side comparison with previous versions
> using the standard Revert To > Browse all versions… command."
> — u/david_phillip_oster (long-time Mac developer), r/SwiftUI, 2023

---

### 1.4 SwiftUI Vibrancy That Looks Flat

**Mistake:** Using SwiftUI's built-in `.ultraThinMaterial` and assuming it matches AppKit's
`NSVisualEffectView`.

From ohanaware.com (Sam Rowlands, macOS developer), 2025:

> SwiftUI's vibrancy is scoped to the window's content rather than the screen behind the window,
> which is different from AppKit's "behindWindow" blending. `.ultraThinMaterial` yields the
> strongest vibrancy effect in SwiftUI but still looks noticeably flat next to a native AppKit
> sidebar built with `NSVisualEffectView(material: .sidebar)`.

**Workaround (same source):**
```swift
public struct VisualEffectView: NSViewRepresentable {
    var material: NSVisualEffectView.Material
    var blending: NSVisualEffectView.BlendingMode = .behindWindow

    public func makeNSView(context: Context) -> NSVisualEffectView {
        let view = NSVisualEffectView()
        view.material = material
        view.blendingMode = blending
        return view
    }

    public func updateNSView(_ nsView: NSViewType, context: Context) {}
}
```

Apple Feedback case **FB17381328** requests macOS-specific materials matching AppKit.

---

### 1.5 Not Handling the Window Lifecycle

**Mistake:** Assuming SwiftUI's `WindowGroup` handles all macOS window behavior correctly.

> "The management of Windows via WindowGroup and DocumentGroup is INSANELY bad. We couldn't do
> basic things without a mountain of hacks which broke under pressure. No documentation, no
> examples. Out-of-the-box, without falling back on AppKit, you can't have many features of
> AppDelegates. So no quitting the app when the last window closes."
> — u/h1jvpy (SwiftUI rant post author, 10+ years iOS experience), r/swift, 2024

Also documented (u/ActualSalmoon, r/SwiftUI, 2023):
- No SwiftUI-native animated window resizing (settings windows "jump" to new size)
- Sheet dimensions are broken on macOS — they do not resize to fit content
- Cannot animate the appearance/disappearance of H/VSplitViews

---

### 1.6 List and Table Performance

**Mistake:** Using SwiftUI `List` or `Table` for large datasets on macOS.

> "SwiftUI Table became smoother with macOS 15.4 — before that, even opening a table was taking a
> lot of time with just a few rows. Scrolling was laggy, adding interactions to cells made
> everything worse."
> — u/Alexey566, r/SwiftUI, 2024

> "I've had to rewrite every table view / list in AppKit because the performance is so bad, and
> customization is so limited. (Yes, we tried every SwiftUI performance trick in the book.)"
> — u/h1jvpy, r/swift, 2024 (startup CTO, data science software)

**Rule of thumb from community consensus:** Use SwiftUI `List`/`Table` for simple, small datasets;
fall back to `NSTableView` or custom `LazyVStack`-based implementations for anything that exceeds
a few hundred rows or requires fine-grained cell interaction.

---

### 1.7 macOS-Specific Inconsistencies Apple Itself Ships

Documented by awebdeveloper (Medium, "Inconsistency in Apple's macOS Design", updated through
Sequoia):

- **Search box placement:** Apple's own apps place the search field in three different locations
  (top-right in Notes/Finder; sidebar in Maps/Stocks; middle pane in Contacts)
- **Hide-sidebar behavior:** Some apps have a hide/show icon; others don't; the menu item label
  varies ("Folders" in Notes vs "Sidebar" in Mail)
- **Transparency handling:** Most sidebars are translucent, but Maps fails to show content behind
  its sidebar
- **Tab placement:** Some apps show tabs below the title bar (Dictionary, Keychain); others embed
  them in the title bar (TV, Activity Monitor, Calendar)
- **Click-to-expand title bar:** Works in Mail, Maps, Photos; does nothing in Contacts, Music

> "Such 'lapses' are large for a detail-oriented company like Apple."
> — awebdeveloper, Medium, 2024

**Practitioner impact:** These inconsistencies give developers implicit permission to deviate from
HIG — but they also create a muddled visual landscape that sophisticated users notice.

---

## 2. Critical HIG Rules

### 2.1 Keyboard Shortcuts Are Non-Negotiable

> "Once you've been a Mac user for a while, you know Command+, opens preferences in any app,
> Command+W closes windows, Command+N opens new documents. Break one of these and users will
> notice immediately."
> — Synthesized from multiple r/macapps and r/MacOS threads, 2023–2025

The HIG mandates:
- `⌘,` for Settings/Preferences
- `⌘W` to close frontmost window
- `⌘Q` to quit
- Standard Edit menu shortcuts (`⌘Z`, `⌘X`, `⌘C`, `⌘V`, `⌘A`, `⌘F`)

Failing these is cited as an immediately noticeable quality signal.

---

### 2.2 The Menubar Is Sacred

> "macOS going backwards in terms of UI usability … The UI guidelines seem to be used steadily
> less and less, making learning curves between apps more challenging."
> — u/ddiddk (Mac user since 1987), r/MacOS, Jan 2025 (234 upvotes, 390 comments)

> "I've been barking about this since they implemented [the new System Settings]. It's macOS doing
> Windows XP style of design."
> — u/chookalana, r/MacOS, March 2025 (351 upvotes)

The menubar provides discoverability. Every action should be accessible through the menubar, not
just keyboard shortcuts or toolbar icons. Apps that hide functionality exclusively in toolbars
break the HIG's discoverability principle and alienate power users.

---

### 2.3 Support the Standard Edit and Services Menus

> "The entire Apple ecosystem has global services integration. If your app handles text and
> doesn't support the Services menu, you're a first-class jerk."
> — u/david_phillip_oster, r/SwiftUI, 2023

SwiftUI apps often skip `NSServicesMenuRequestor` implementation. Users who rely on text
processors, OCR tools, or Raycast integrations will notice.

---

### 2.4 Dark Mode Must Be System-Integrated, Not Custom-Implemented

**Common mistake:** Implementing custom dark/light mode toggles in the app instead of respecting
`NSAppearance` and the system setting.

From ohanaware.com: SwiftUI only exposes `.primary` and `.secondary` as semantic colors; `.tertiary`
and `.quaternary` are available as `foregroundStyle` only, not as `Color`. Using hardcoded colors
that look fine in one appearance and break in the other is a persistent community complaint.

---

### 2.5 The Native Font Is a Feature

> "The default system font plays a big part, together with the Retina resolution. The default macOS
> San Francisco font is gorgeous. I have to run Windows on a Mac occasionally and it's one of the
> first things I notice."
> — u/ChemistryMost4957, r/MacOS, 2024 (40 upvotes)

Using non-system fonts for UI chrome (not content) is a HIG violation that users — even
non-technical ones — perceive as "off." Use `.font(.body)`, `.font(.callout)`, etc. rather than
custom typefaces for any standard UI text.

---

### 2.6 Window Resizing and Minimum Sizes

From swiftwithmajid.com (Majid Jabrayilov, 2024):

- `defaultSize` only sets the initial size; user resizing is not constrained unless
  `windowResizability` is also applied
- `windowResizability(.contentSize)` prevents shrinking below content size but does NOT restrict
  the maximum size
- There is no SwiftUI API to enforce a maximum window size — AppKit fallback required for strict
  limits

Minimum sizes that force horizontal scrolling or clip content are a frequent user complaint in
r/macapps.

---

## 3. HIG Rules Practitioners Override

### 3.1 "Follow the HIG Settings Window Pattern" → Use a Custom Pattern

**Why devs override it:** The native `Settings {}` scene in SwiftUI does not match what Apple
itself ships in System Settings (Ventura+). The HIG prescribes the classic tabbed-preferences
window, but System Settings uses a sidebar-based navigation model.

> "Apple's native solutions usually lag behind their HIG recommendations. I feel like the guidelines
> are still written with UIKit in mind even though SwiftUI is steadily replacing all of it."
> — u/Yaysonn, r/SwiftUI, 2023

**What they do instead:** Developers build custom settings windows using `NSWindow` extensions,
`NavigationSplitView`, or third-party libraries that mimic the System Settings style.

---

### 3.2 "Use Standard Window Chrome" → Remove Titlebar Separator

Many apps (Raycast, Alfred, productivity tools) use `.titlebarSeparatorStyle = .none` and
`.titlebarAppearsTransparent = true` to create a unified toolbar look that doesn't exist in
stock SwiftUI.

Workaround (u/stephancasas, r/SwiftUI, 2023):
```swift
DispatchQueue.main.async {
    guard let window = NSApplication.shared.windows.first else { return }
    window.titlebarAppearsTransparent = true
    window.titlebarSeparatorStyle = .none
}
```

---

### 3.3 "Use System Colors Only" → Apply Brand Colors

**Why devs override it:** Craft, Bear, and Raycast all use strong brand color accents that
technically deviate from pure HIG color usage but are widely praised for design quality.

The community distinction: u/AkhlysShallRise (r/macapps, 127 upvotes, 2025):
> "For me, 'beautiful' and 'over-designed' are two different things. Apps made by Apple are almost
> never over-designed or overly 'beautiful.' I can look at Craft all day because it's so pretty,
> but I'd argue that Apple would never make something as pretty as that."

Consensus: Apply HIG structural rules strictly; apply brand identity in color, illustration, and
iconography while keeping semantic colors for interactive elements.

---

### 3.4 "Use Standard Toolbar Items" → Remove Toggle Sidebar Button

HIG adds a toggle-sidebar button automatically in `NavigationSplitView`. Most settings-style apps
want to remove it. There is no SwiftUI-native way to do this.

Workaround (u/austincondiff, CodeEdit project, r/SwiftUI, 2023):
```swift
.task {
    let window = NSApp.windows.first {
        $0.identifier?.rawValue == "com_apple_SwiftUI_Settings_window"
    }!
    window.toolbarStyle = .unified
    let sidebaritem = "com.apple.SwiftUI.navigationSplitView.toggleSidebar"
    let index = window.toolbar?.items.firstIndex {
        $0.itemIdentifier.rawValue == sidebaritem
    }
    if let index { window.toolbar?.removeItem(at: index) }
}
```

---

### 3.5 "Provide System Alerts for Destructive Actions" → Skip Confirmation Dialogs

In productivity tools where speed is the primary value (Raycast, LaunchBar), confirmation dialogs
for destructive actions are omitted when undo is available. The HIG recommends confirmation; power
user audiences tolerate the override because they prefer speed over safety theater.

---

### 3.6 "Always Use AppKit for macOS" → Use SwiftUI + AppKit Hybrid

The community consensus (2023–2025) is against the extremes:

> "Start with SwiftUI, but be prepared to face the fact that macOS is a secondary citizen. Apple
> just doesn't care about SwiftUI on the Mac. Every single of my projects has to use, at least, a
> delegate adaptor for implementing an AppDelegate."
> — u/ActualSalmoon (shipped multiple macOS apps), r/SwiftUI, 2023

**Best practice:** Build lifecycle, windowing, and complex data views in AppKit; build content
views and forms in SwiftUI.

> "A good workflow is: build all the lifecycle and windowing in AppKit and the views in SwiftUI."
> — u/NilValues215, r/SwiftUI, 2023

---

## 4. HIG vs Reality

### 4.1 SwiftUI on macOS Is Explicitly Second-Class

Multiple independent developers with 10+ years of experience confirm that macOS is not a first-class
SwiftUI target:

**Specific gaps (as of macOS 15, early 2025):**

| Feature | iOS/SwiftUI | macOS/SwiftUI | Workaround |
|---|---|---|---|
| Searchable modifier | Full feature | Limited | `NSSearchField` via `NSViewRepresentable` |
| List performance | Good | Poor until macOS 15.4 | `NSTableView` |
| Sheet dimensions | Auto-sizes | Broken | `NSWindow` delegate |
| Window animations | N/A | Jumps, no easing | `NSAnimation` |
| File picker dialogs | `.fileImporter` | Limited vs `NSOpenPanel` | Fall back to AppKit |
| NSTextField | — | Misses features | `NSTextField` via `NSViewRepresentable` |
| Drag and drop (multiple selection) | Good | Limited | AppKit `NSPasteboard` |
| Menu keyboard shortcuts | Works | Incomplete responder chain | `NSMenuItem` actions |
| NSSplitView | — | Buggy in SwiftUI | `NSSplitViewController` |
| Animated `DisclosureGroup` resizing | N/A | Broken | AppKit animation block |

Sources: u/ActualSalmoon (r/SwiftUI, 2023), u/Fantastic_Resolve364 (r/SwiftUI, 2024),
u/GoalFar4011 (r/SwiftUI, 2024)

---

### 4.2 The HIG Settings Window Pattern vs SwiftUI's `Settings {}` Scene

The HIG prescribes a tabbed settings window with icons and labels. SwiftUI's `Settings {}` renders
this correctly. But Apple's own System Settings (Ventura+) uses a completely different sidebar
pattern — and the built-in `Settings {}` does NOT replicate it.

> "Apple's own [HIG] prescribes that style of settings UI… but Apple's native solutions usually
> lag behind their HIG recommendations."
> — u/Yaysonn, r/SwiftUI, 2023

This puts developers in an awkward position: follow the HIG and use the old-style tabbed prefs,
or follow what Apple actually ships in its modern apps.

---

### 4.3 `NSToolbar` vs SwiftUI Toolbar

From u/stephancasas (NSWindow exploration, r/SwiftUI, 2023):
> "Some SwiftUI components are context-aware and others are not. The buttons I added to the title
> toolbar were automatically styled as toolbar buttons despite not being added using a SwiftUI
> toolbar component. On the other hand, adding a SwiftUI toolbar to the body of the rootView in
> an NSHostingView won't automatically implement and style the toolbar."

NSToolbar APIs require the style to be set through `NSWindow.toolbarStyle`, not `NSToolbar` itself
— a distinction not documented clearly and discovered through trial-and-error.

---

### 4.4 Vibrancy: SwiftUI Material vs AppKit NSVisualEffectView

The HIG specifies that macOS sidebars, toolbars, and panels should use vibrancy effects. In
practice (ohanaware.com, Sam Rowlands, 2025):

- SwiftUI `.ultraThinMaterial` blends only within the window's content
- AppKit `NSVisualEffectView(material: .sidebar, blending: .behindWindow)` blends against the
  desktop and windows behind it
- The visual difference is immediately perceptible in side-by-side comparison
- This is confirmed as possibly intentional to maintain cross-platform consistency, but it means
  SwiftUI-only macOS apps look "flat" on standard sidebars

---

### 4.5 The Liquid Glass Transition (macOS 26 / WWDC 25)

From swiftwithmajid.com (Majid Jabrayilov, June/July 2025):

New APIs for the Liquid Glass design language require **iOS 18 / macOS Sequoia or later**:
- `Tab` struct replaces the old `TabView`-style placement; omitting `.sidebarAdaptable` breaks the
  expected Liquid Glass look on macOS
- `ToolbarSpacer` is new and guards are needed for pre-Liquid Glass OS versions
- `ToolbarItemPlacement` now dictates both position AND visual style — wrong placement yields
  unexpected appearance
- `@SceneStorage` for tab selection is now required for state restoration

**Developer gotcha:** The migration is NOT backward-compatible. Apps targeting macOS 15 and earlier
receive none of the Liquid Glass features and need conditional code paths.

---

### 4.6 System Settings as a Cautionary Tale

The redesign of System Settings in macOS Ventura (2022) is the most cited example of Apple
violating its own HIG principles:

> "The old System Preferences was literally fine. I hate that they just grafted the iOS settings
> app into macOS."
> — u/Admiral_Ackbar_1325, r/MacOS, 2025 (150 upvotes)

> "Can't find anything in System Settings unless you search and search for the exact term."
> — u/chookalana, r/MacOS, 2025 (351 upvotes)

The search functionality in the new System Settings is widely criticized for failing to find
settings even when the exact term is entered (multiple threads, 2024–2025). This is cited as a
direct consequence of iOS-ification — importing interaction patterns that work for touch-based
hierarchical navigation into a desktop context where breadth-first browsable menus work better.

---

## 5. Exemplary macOS Apps

### 5.1 Apps Cited as Design Exemplars (Community Consensus)

The following apps appear repeatedly across r/macapps and r/SwiftUI as exemplars of macOS-native
design (sourced from threads with 50+ upvotes, 2024–2025):

**Pixelmator Pro**
> "Not only is the UI the same as Pages/Numbers/Keynote, the workflow is also extremely integrated
> with macOS."
> — u/AkhlysShallRise, r/macapps, 2025 (127 upvotes)
- Acquired by Apple in 2023; widely considered the most macOS-native third-party creative app
- Deep integration with macOS features: Continuity Camera, Shortcuts, Photos library

**Things 3 (Cultured Code)**
> "Maybe the pinnacle in app design."
> — u/amerpie citing AppAddict article, r/macapps, 2025
- Minimal friction philosophy: quick-entry via global shortcut, natural language input for
  recurring tasks
- Community split: some find it too simple (lacks attachments, subtask reminders); defenders
  say the simplicity IS the design

**IINA**
> "Basically VLC, if it were designed specifically for macOS."
> — u/Careful_Practice_486, r/macapps, 2025 (117 upvotes)
- Open-source media player that uses native macOS controls throughout
- Cited as an example of a utility app that prioritizes macOS idioms over cross-platform parity

**Craft**
> "Uses native macOS design language but puts its own colorful spin on it."
> — u/[deleted], r/macapps, 2025
- One of the most visually praised apps but noted for being "more beautiful than Apple would ever
  make themselves"
- Uses CloudKit for sync, eliminating server costs and guaranteeing macOS/iOS integration

**Raycast**
> "A very powerful Spotlight replacement that has macOS native-esque design language and is just
> so satisfying to use."
> — u/weirdfishesarpeggii, r/macapps, 2025
- Designed as a launcher: single-window, keyboard-first interaction model
- Electron alternative to Alfred that nonetheless achieves a near-native feel

**Bear**
> "Adheres to Apple's visual guidelines and uses their APIs better than 98% of apps on the market."
> — u/fireball_jones, r/macapps, 2024
- CloudKit sync, no custom server required
- Community debate: some find it "not Apple-like" due to its colorful branding; others call it
  the best integration of custom brand identity within HIG constraints

**Git Tower**
> Cited by OP in r/macapps "beautiful native Mac apps" thread as a reference benchmark
- Professional developer tool that maintains macOS conventions despite high feature density

**Panic (Transmit, Nova)**
> "Has a well-deserved rep for crafting great Mac apps."
> — u/BluesMaster, r/macapps, 2025
- Panic's apps are cited as templates for: proper document proxy icons, drag-and-drop integration,
  complete menubar coverage, HIG-compliant toolbar design

---

### 5.2 What These Apps Do Differently

Synthesized from community discussion (r/macapps, r/MacOS, 2024–2025):

1. **Single-window focus:** Award-winning apps rarely open multiple windows by default; they
   use panels, popovers, and inspectors instead of spawning new windows for secondary tasks.

2. **Keyboard shortcut completeness:** Every significant action has a discoverable keyboard
   shortcut, accessible via the menu bar.

3. **Drag-and-drop as a first-class interaction:** Not bolted on — built into the architecture.

4. **Respects system-wide preferences:** Dynamic Type, reduced motion, high contrast, VoiceOver
   — all respected without requiring the user to find an in-app setting.

5. **Proxy icon behavior:** Document-based apps (Nova, Transmit) implement draggable proxy icons
   in the title bar, a distinctly macOS feature that users with workflow automation rely on.

---

### 5.3 Anti-Examples (Apps With Poor macOS Design)

Community-cited examples of poor macOS design (r/macapps, 2025):

- **Steam:** Sharp window corners, Rosetta 2 on Apple Silicon, 30-second launch time, multiple
  inconsistent UI generations within one app, ignores standard keyboard shortcuts
- **Microsoft Office (Mac):** "Most Microsoft apps — you'd think a company this huge could hire
  some decent UI designers?"
- **Adobe Acrobat Pro:** "Villainous" — cited alongside DevonThink and any XnSoft app
- Any Electron-based app that does not invest heavily in platform integration

---

## 6. SwiftUI-Specific Gotchas

### 6.1 Performance Anti-Patterns (Documented by Community)

From u/hishnash (r/iOSProgramming, 2025, explaining correct SwiftUI usage):

**Never do these in SwiftUI (causes excessive redraws):**
1. Create a `DateFormatter` inside a `View.body`
2. Use `.id(UUID())` on views (forces recreation every render)
3. Pass closures as props to child views (Swift cannot diff closures; all children re-evaluate)
4. Use `AnyView` (defeats SwiftUI's type-based diffing)
5. Use `GeometryReader` unnecessarily
6. Place logic in view `init` or in `@State` object init (re-evaluated on every parent redraw)
7. Use conditional `if/else` inside `ForEach` (forces evaluation of all items before layout)

**Performance rules:**
- Filter data before passing to `ForEach`, not inside it
- 1000+ separate small views is often faster than one large compound view
- Pass only data the view needs; every extra property is data SwiftUI must diff

---

### 6.2 SwiftUI macOS-Specific Bugs (As of 2024–2025)

From multiple Reddit threads:

- **`NavigationSplitView` sidebar glitch on collapse:** Sidebar has visual glitches when
  collapsing on macOS (u/SwiftUI, 2025: r/SwiftUI/comments/1iqq7lb)
- **Form alignment issues:** `DisclosureGroup` within `Form` causes alignment breakage that has
  no SwiftUI-only fix; requires AppKit workarounds
- **`@Observable` with `@State`:** Using `@State` with an `@Observable` viewmodel causes the init
  to be called on every view update — widely documented as a source of bugs (use `@StateObject`
  pattern instead)
- **Back button glitch:** Hiding the back button title on a NavigationStack's second view causes
  a glitchy arrow animation on push — known Apple bug, unfixed as of mid-2025
- **macOS `List` performance:** Significantly improved in macOS 15.4 (u/Alexey566, r/SwiftUI, 2024)
  but still inferior to `NSTableView` for complex cell interactions

---

### 6.3 Window ID Collisions

From hackingwithswift.com:
- Mismatched `Window` scene `id` strings cause `openWindow()` calls to silently fail with no
  error or warning
- Adding a `navigationTitle()` inside a `Window` scene replaces the window title entirely

---

### 6.4 The `NSHostingView` Context Problem

From u/stephancasas (r/SwiftUI, 2023):
> "Some SwiftUI components are context-aware and others are not… adding a SwiftUI toolbar to the
> body of the rootView in an `NSHostingView` won't automatically implement and style the toolbar."

When embedding SwiftUI views in `NSWindow` via `NSHostingView`, some SwiftUI modifiers (`.toolbar`,
`.searchable`) do not work as expected because they rely on the SwiftUI environment being provided
by a `WindowGroup` or `Window` scene, which is absent.

---

### 6.5 Liquid Glass Migration Gotchas (macOS 26+)

From swiftwithmajid.com (July 2025):
- Only one `TabRole` exists: `.search`; attempting others produces compile-time errors
- `tabViewBottomAccessory` is only rendered on macOS and iOS with Liquid Glass — it is silently
  absent on older OS versions
- The custom `LabelStyle` for backward-compatible toolbar items must be annotated with
  `@available(iOS, obsoleted: 26)` to force removal when the deployment target is raised

---

## 7. Top 10 Things Every macOS Developer Should Know About HIG

**1. SwiftUI implements HIG for you on iOS. On macOS, it fights you.**
Expect to write AppKit interop code for window management, toolbar customization, vibrancy,
settings windows, and drag-and-drop. This is not a failure — it is the expected workflow as of
macOS 15 (2024–2025).

**2. The settings window has five hard rules.**
Settings must be modeless (no Save/Cancel), activated by `⌘,`, have dimmed min/max buttons,
persist the last-selected tab, and use `.preference` toolbar style. Violating any of these signals
"Windows developer didn't read the HIG" to power users.
Source: u/usagimaru, zenn.dev macOS Settings Window Guidelines, 2024

**3. Keyboard shortcuts are a fundamental contract, not a nice-to-have.**
`⌘,`, `⌘W`, `⌘Q`, `⌘Z`, `⌘F` are load-bearing expectations. Every significant action must be
accessible from the menu bar. Apps that rely on toolbar icons or mouse-only interactions fail the
macOS expectation contract.

**4. SwiftUI vibrancy is visually different from AppKit vibrancy.**
Use `NSViewRepresentable` wrapping `NSVisualEffectView` when you need true behind-window blending.
SwiftUI `.ultraThinMaterial` is cross-platform and does not match native macOS sidebar vibrancy.
Source: ohanaware.com, 2025

**5. Apple's own apps violate the HIG in ways third-party apps cannot afford to.**
System Settings, Maps, and Music inconsistently apply sidebar behavior, transparency, and
keyboard shortcuts. Users notice when third-party apps do the same things. The standard applied
to developers is stricter than the one Apple applies to itself.
Source: awebdeveloper, Medium (Big Sur through Sequoia), 2024

**6. The award-winning apps follow structural HIG, then override aesthetic HIG.**
Craft, Bear, Raycast, and Things 3 are strict about window chrome, keyboard shortcuts, and
system integration — but use strong brand identity in colors and visual design. This is the
correct balance. Full HIG aesthetic compliance produces apps that look "generic."

**7. The macOS List/Table performance problem is real.**
Before macOS 15.4, SwiftUI `Table` could take seconds to open with minimal rows. `NSTableView`
remains the correct choice for datasets above a few hundred items or requiring complex cell
interactions.

**8. `NavigationSplitView` is not the whole macOS navigation story.**
The three-column split view is appropriate for hierarchical content. Menu-bar apps, utility apps,
and document-based apps each have their own HIG-mandated patterns. Defaulting to
`NavigationSplitView` for all macOS apps is the equivalent of using a tab bar for all iOS apps.

**9. Liquid Glass (macOS 26+) requires hard version guards.**
The new `Tab`, `ToolbarSpacer`, and `.sidebarAdaptable` APIs are not available on older systems.
Any app supporting macOS 14 or earlier must write conditional code paths. Rolling these APIs
without guards silently breaks on pre-Sequoia systems.
Source: swiftwithmajid.com, 2025

**10. "Read the HIG" is still the best advice — but treat it as a reference, not a rulebook.**
> "In the old MacOS Classic days we would study them like the Bible. Today everyone — even Apple
> — treats the current guidelines as suggestions."
> — u/chriswaco (Mac Classic developer), r/SwiftUI, 2025

The HIG is most valuable as a source of design intent. Use it to understand *why* macOS conventions
exist, not as a checklist to mechanically follow. The HIG that experienced developers defer to for
judgment is the structural/behavioral layer (shortcuts, window lifecycle, navigation patterns);
the aesthetic layer (colors, icon styles) is where successful apps apply creative judgment.

---

## 8. Sources

All sources verified through direct scraping or Reddit thread retrieval.

| # | Source | Author | URL | Date | Type |
|---|---|---|---|---|---|
| 1 | "Is Anyone Really Reading the Entire Human Interface Guidelines?" | u/CurlyBraceChad (34 upvotes, 29 comments) | https://reddit.com/r/SwiftUI/comments/1lcmvcb/ | Jun 2025 | Reddit r/SwiftUI |
| 2 | "Native Mac Application Development in 2023" | u/Top_Supermarket_4435 (35 upvotes, 22 comments); key reply u/ActualSalmoon (+48) | https://reddit.com/r/SwiftUI/comments/11g49wz/ | Mar 2023 | Reddit r/SwiftUI |
| 3 | "Native-like app settings for macOS" | u/stephancasas (69 upvotes, 24 comments) | https://reddit.com/r/SwiftUI/comments/11ud8al/ | Mar 2023 | Reddit r/SwiftUI |
| 4 | "SwiftUI for Mac: still unfinished?" | u/GoalFar4011 (various replies) | https://reddit.com/r/SwiftUI/comments/1kjtq8k/ | 2024 | Reddit r/SwiftUI |
| 5 | "Mac App Design vs iOS App Design" | u/VulcanCCIT (reply from u/BL1860B +6) | https://reddit.com/r/SwiftUI/comments/1p3e2cb/ | 2025 | Reddit r/SwiftUI |
| 6 | "Is macOS going backwards in terms of UI usability?" | u/ddiddk (234 upvotes, 390 comments) | https://reddit.com/r/MacOS/comments/1hvwlmx/ | Jan 2025 | Reddit r/MacOS |
| 7 | "Why do macOS apps look superior?" | u/pkcarreno (182 upvotes, 132 comments) | https://reddit.com/r/MacOS/comments/1erbzzf/ | 2024 | Reddit r/MacOS |
| 8 | "System Settings is an epitome of modern Apple" | various (multiple threads) | https://reddit.com/r/MacOS/comments/1j08oj9/ | Mar 2025 | Reddit r/MacOS |
| 9 | "I am looking for beautiful native Mac apps" | u/deadunderdog (289 upvotes, 165 comments) | https://reddit.com/r/macapps/comments/1qa3zq7/ | 2025 | Reddit r/macapps |
| 10 | "What are the best-designed Mac apps you've used?" | community thread (122 comments) | https://reddit.com/r/macapps/comments/1ku9l8z/ | 2025 | Reddit r/macapps |
| 11 | "My favorite (and least favorite)-designed Mac apps" | u/[deleted] (135 upvotes, 60 comments) | https://reddit.com/r/macapps/comments/1kuupcx/ | 2025 | Reddit r/macapps |
| 12 | "SwiftUI is garbage imo — a rant" | u/h1jvpy (179 comments, 14K+ words) | https://reddit.com/r/swift/comments/1h1jvpy/ | 2024 | Reddit r/swift |
| 13 | "SwiftUI was a mistake — and I've been using it since beta 1" | iOS dev, 14 years (185/203 comments) | https://reddit.com/r/iOSProgramming/comments/1kbbgui/ | Apr 2025 | Reddit r/iOSProgramming |
| 14 | "SwiftUI is easy, where is the catch?" | u/BeDevForLife (64 upvotes, 90 comments) | https://reddit.com/r/iOSProgramming/comments/1s8j00v/ | 2025 | Reddit r/iOSProgramming |
| 15 | "iOS devs who tried coding for macOS after 2020" | u/iLearn4ever | https://reddit.com/r/iOSProgramming/comments/xfl9dn/ | 2022 | Reddit r/iOSProgramming |
| 16 | "Is nobody using AppKit anymore to develop for macOS?" | r/swift thread | https://reddit.com/r/swift/comments/17jidxh/ | 2023 | Reddit r/swift |
| 17 | "Is SwiftUI on macOS that bad?" | r/SwiftUI thread | https://reddit.com/r/SwiftUI/comments/1qz9xuj/ | 2025 | Reddit r/SwiftUI |
| 18 | macOS Settings Window Implementation Guidelines | u/usagimaru | https://zenn.dev/usagimaru/articles/b2a328775124ef | 2024 | Blog (Japanese, English translation) |
| 19 | "SwiftUI macOS Vibrancy" | Sam Rowlands (Ohanaware) | https://ohanaware.com/swift/macOSVibrancy.html | 2025 | Developer blog |
| 20 | "Customizing Windows in SwiftUI" | Majid Jabrayilov | https://swiftwithmajid.com/2024/08/06/customizing-windows-in-swiftui/ | Aug 2024 | swiftwithmajid.com |
| 21 | "Glassifying Tabs in SwiftUI" | Majid Jabrayilov | https://swiftwithmajid.com/2025/06/24/glassifying-tabs-in-swiftui/ | Jun 2025 | swiftwithmajid.com |
| 22 | "Glassifying Toolbars in SwiftUI" | Majid Jabrayilov | https://swiftwithmajid.com/2025/07/01/glassifying-toolbars-in-swiftui/ | Jul 2025 | swiftwithmajid.com |
| 23 | "Inconsistency in Apple's macOS Design" | awebdeveloper | https://medium.com/awebdeveloper/inconsistency-in-apples-macos-design-9fdc4171af0 | Updated 2024 | Medium |
| 24 | "How to Open a New Window" | Paul Hudson | https://www.hackingwithswift.com/quick-start/swiftui/how-to-open-a-new-window | 2024 | Hacking with Swift |
| 25 | Cindori Developer Blog (Sparkle, AVKit articles) | Cindori team | https://cindori.com/developer/ | 2025 | Developer blog |
