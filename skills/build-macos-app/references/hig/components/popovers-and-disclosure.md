# macOS Transient and Progressive-Disclosure UI — Definitive Spec Reference

**Scope:** macOS only. AppKit and SwiftUI. Covers popovers, tooltips, disclosure triangles, disclosure buttons, disclosure groups, and the decision logic for choosing between them.

---

## 1. Popovers

### 1.1 What a Popover Is

A popover is a transient, non-modal overlay that appears anchored to a specific control or rectangular region. It points to its anchor with an arrow. The popover's content floats above the rest of the UI and disappears when dismissed. Popovers are used to expose a small amount of information or functionality without requiring the user to navigate away from the current context.

- **API class:** `NSPopover` (AppKit, macOS 10.7+); `.popover(isPresented:content:)` modifier (SwiftUI, macOS 10.15+)
- **Non-modal.** Does not block the rest of the UI (unless behavior is `.applicationDefined` and the app manually enforces that).
- **Contextual.** Always attached to and points at an anchor view or rectangle.

### 1.2 Sizing

There is no system-enforced minimum or maximum pixel size for an `NSPopover`. The popover's content area is set by the `contentSize` property on `NSPopover`, which defaults to the `preferredContentSize` of the `contentViewController`.

**Practical guidance confirmed by practitioner sources:**

| Guideline | Value | Source |
|---|---|---|
| Typical comfortable width | 300–400 pt | useyourloaf.com practitioner post |
| Width above which system may shrink content to keep popover on-screen | > 600 pt | useyourloaf.com practitioner post |
| Sizing approach (AppKit) | Set `preferredContentSize` on the view controller | Apple Developer Documentation |
| Sizing approach (Auto Layout) | Call `systemLayoutSizeFitting(.layoutFittingCompressedSize)` in `viewDidLoad` | useyourloaf.com |
| Sizing approach (SwiftUI) | Apply `.frame(width:height:)` to the popover's root view | Apple documentation / practitioner sources |

When the content uses Auto Layout, use the compressed fitting size so the popover exactly wraps its content:

```swift
// In the content view controller:
override func viewDidLoad() {
    super.viewDidLoad()
    preferredContentSize = view.systemLayoutSizeFitting(
        NSView.layoutFittingCompressedSize
    )
}
```

The `contentSize` can be changed while the popover is open. If `animates` is `true`, the popover animates to the new size.

### 1.3 Positioning and the Arrow

The popover is shown via:

```swift
// AppKit
popover.show(relativeTo: positioningRect, of: positioningView, preferredEdge: .minY)

// SwiftUI
.popover(isPresented: $show) { ContentView() }
```

**`preferredEdge` values** (determines which edge of the anchor the arrow points from):

| Value | Arrow appears on | Popover appears |
|---|---|---|
| `.minX` | Left edge of anchor | Popover extends to the left |
| `.maxX` | Right edge of anchor | Popover extends to the right |
| `.minY` | Bottom edge of anchor | Popover extends downward |
| `.maxY` | Top edge of anchor | Popover extends upward |

The system treats `preferredEdge` as a hint, not a guarantee. If there is insufficient screen space on the preferred side, the system automatically flips the popover to the opposite edge to keep it fully on-screen. This behavior cannot be overridden via the public API.

**Arrow behavior:**
- The arrow always points at the positioning view or rect.
- The arrow hides itself automatically when the positioning view is outside the visible rect of its window (e.g., scrolled out of view).
- Arrow position within an edge (how far left/right or up/down along that edge it sits) is determined by the system and cannot be manually set via the public API as of macOS 10.7 through the current release. Third-party solutions exist for custom arrow positioning.
- To present a popover without an arrow: show the popover normally, then immediately move the positioning view outside the visible area. This exploits the automatic hide behavior and requires no private APIs.

### 1.4 Behavior Types

The `NSPopover.behavior` property (type `NSPopover.Behavior`) controls when the system automatically dismisses the popover.

#### `.transient`
The popover closes automatically in response to any user interaction that occurs outside the popover's bounds, including mouse clicks anywhere else on screen. This is the most common behavior for quick-access overlays.

- Closes on: any click outside the popover
- Does not close on: interactions inside the popover
- Equivalent to "light dismiss"

#### `.semitransient`
The popover does not close from an event that results in opening or closing another popover. However:
- Showing a semitransient popover causes any other currently-visible semitransient popovers to close.
- Semitransient popovers cannot be shown relative to views that live inside other popovers.
- Semitransient popovers cannot be shown relative to views in child windows.
- The exact full set of interactions that trigger dismissal is undocumented by Apple; the behavior is partially opaque.

Use `.semitransient` for toolbar items and controls where the user may need to interact with other controls without accidentally dismissing the popover (e.g., a search bar that coexists with a formatting popover).

#### `.applicationDefined`
The app is fully responsible for dismissing the popover. The system never automatically closes it. The app must call `popover.close()` or `popover.performClose(_:)` explicitly.

Use `.applicationDefined` when you need to persist the popover across interactions, or when you implement custom dismissal logic (e.g., a "pin" behavior).

**Behavior comparison table:**

| Behavior | Auto-dismiss on outside click | Stays open alongside other popovers | App controls dismissal |
|---|---|---|---|
| `.transient` | Yes | No | No |
| `.semitransient` | Partially (see above) | Yes (partially) | Partially |
| `.applicationDefined` | Never | Yes | Yes (required) |

### 1.5 Detachment

An `NSPopover` can become detached — converted into a floating panel — when the user drags it away from its anchor. The `detachable` behavior is controlled via the delegate:

```swift
func popoverShouldDetach(_ popover: NSPopover) -> Bool {
    return true // return false to prevent detachment
}
```

When detached:
- The popover loses its arrow.
- It becomes an independent, movable window.
- The `detached` property on the popover reads `true`.
- The `CloseReason` will be `.detachToWindow` if the detachment causes the original popover to close.

### 1.6 Appearance and Animation

- **Background:** vibrancy material; follows the system's translucency setting.
- **Animation:** The `animates` property (default: `true`) controls whether the popover fades/scales in and out. Set to `false` to suppress animation (rarely appropriate; prefer the default).
- **Content size animation:** When `contentSize` changes while the popover is open and `animates` is `true`, the popover smoothly resizes.
- **Dark Mode:** The popover material adapts automatically.

### 1.7 Delegate Callbacks

`NSPopoverDelegate` provides lifecycle hooks:

```swift
func popoverWillShow(_ notification: Notification)
func popoverDidShow(_ notification: Notification)
func popoverWillClose(_ notification: Notification)
func popoverDidClose(_ notification: Notification)
func popoverShouldDetach(_ popover: NSPopover) -> Bool
func popoverShouldClose(_ popover: NSPopover) -> Bool // return false to veto close
```

Notification constants: `NSPopover.willShowNotification`, `NSPopover.didShowNotification`, `NSPopover.willCloseNotification`, `NSPopover.didCloseNotification`.

---

## 2. Tooltips

### 2.1 What a Tooltip Is

A tooltip is a small, single-line (or occasionally multi-line) text label that appears near the cursor after the user hovers over a UI element for a delay period. It provides supplementary information about the element — typically its name or function when that is not otherwise apparent.

- **API (AppKit):** `NSView.toolTip: String?` property; also `NSView.addToolTip(_:owner:userData:)` for dynamic tooltips
- **API (SwiftUI):** `.help(_ text: LocalizedStringKey)` modifier
- **Non-interactive.** Tooltips cannot contain buttons or interactive elements.
- **Auto-dismissed.** Tooltips disappear when the cursor moves away from the trigger.

### 2.2 Timing

| Parameter | Default Value | Notes |
|---|---|---|
| Show delay (NSInitialToolTipDelay) | **2000 ms (2 seconds)** | Confirmed by macOS user defaults; the `NSInitialToolTipDelay` key controls this. Removed in macOS Monterey 12.0–12.3; restored in 12.4. |
| Customizing system-wide delay | `defaults write -g NSInitialToolTipDelay -int <ms>` | Any integer in milliseconds; e.g., `-int 500` for 500 ms. Requires app restart. |
| Per-app delay override (AppKit) | `[NSToolTipManager.sharedToolTipManager() setInitialToolTipDelay:0.1]` | Value in seconds; can be set at runtime |
| Per-object delay | Not natively supported. Workaround: use mouse-tracking regions and adjust the shared manager on `mouseEntered:` / `mouseExited:` | Stack Overflow practitioner pattern |
| Hide delay / display duration | Not exposed via a public system default. Tooltips hide when the cursor leaves the trigger view. | No confirmed public API for duration cap |

The 2-second default is confirmed by:
- The Reddit thread `r/MacOS/comments/uz6tv4` (macOS 12.4 restoration announcement, 27 upvotes)
- The GitHub issue `p0deje/Maccy#282` ("current delay feels around two seconds")
- The `NSInitialToolTipDelay` user default documented in community sources

### 2.3 Content Rules

- **Text only.** A tooltip is a plain text string. There is no native API for rich text, images, or interactive elements inside an AppKit tooltip.
- **Brevity.** Apple's HIG states tooltips should be short — a word or phrase that names or briefly describes the element.
- **Language.** Use a noun phrase or imperative verb phrase (e.g., "Zoom In", "Share"). Do not repeat the visible label.
- **Avoid redundancy.** If the button already has a visible text label, a tooltip is usually unnecessary.
- **Character limits.** The macOS tooltip does not have a hard system-enforced character limit documented in Apple's current HIG. In practice, long strings wrap within the tooltip's display width. (Note: a separate Windows `TOOLTIPS_CLASS` 80-character limit does not apply to macOS — that is a Win32 API constraint.)

### 2.4 Visual Appearance

- Small rounded-rectangle label.
- Background: system tooltip background color (opaque light yellow-beige in Light Mode; dark gray in Dark Mode on recent macOS).
- Font: system font at small size (~11 pt).
- No arrow or anchor indicator.
- Appears near the cursor, offset slightly downward to avoid obscuring the element.
- Follows system translucency settings for the background material.

---

## 3. Disclosure Controls

### 3.1 Overview

macOS has two distinct AppKit disclosure controls, plus the SwiftUI `DisclosureGroup`. They differ in purpose, visual appearance, and usage rules.

| Control | AppKit API | Purpose | Usage limit |
|---|---|---|---|
| Disclosure Triangle | `NSButton` with `bezelStyle = .disclosure` | Reveal/hide hierarchical information (sections, list items, subordinate rows) | Can appear multiple times (e.g., in every row of an outline view) |
| Disclosure Button | `NSButton` with `bezelStyle = .roundedDisclosure` | Expand a dialog or panel to show additional options related to a specific control | Maximum one per view/window |

### 3.2 Disclosure Triangle

**Visual appearance:**
- An arrow (chevron/triangle).
- **Collapsed state:** arrow points to the right (→).
- **Expanded state:** arrow points downward (↓).
- Fixed size — does not change with control size settings.
- `buttonType` is typically "other" (not on/off).

**Behavior:**
- Toggle: clicking the triangle shows or hides its associated content and rotates the arrow.
- Action is sent to the controller; the controller is responsible for showing/hiding the target content.
- In Finder List view, Option+Command+Right Arrow expands all selected disclosure triangles simultaneously; Option+Command+Left Arrow collapses them.
- Accessibility role: `NSAccessibility.Role.disclosureTriangle`.

**When to use:**
- To reveal more detail about a specific item in a list or outline view.
- To show subordinate items in a hierarchical structure (e.g., folders in a file browser, child nodes in an outline).
- Any situation where multiple expandable sections exist in the same view.

**When NOT to use:**
- Do not use a disclosure triangle to show or hide additional options that are tightly coupled to a single specific control. Use a disclosure button instead.
- Do not use for progressive disclosure in a flat (non-hierarchical) dialog. Use a disclosure button.

### 3.3 Disclosure Button

**Visual appearance:**
- A small rectangular button containing a down-pointing arrow inside a rounded border.
- **Collapsed state:** arrow points downward, button appears "normal."
- **Expanded state:** button toggles to its alternate state; the appearance changes to signal that the content is shown.
- Fixed size.
- `buttonType` is `.onOff`.

**Behavior:**
- Expands or contracts a section of a dialog or panel to show or hide additional options.
- Typically placed in Save dialogs, Print dialogs, or any sheet that has basic and advanced modes.
- Only one disclosure button should appear in a single view. Multiple disclosure buttons in one view add complexity and are confusing.

**When to use:**
- Progressively reveal advanced or supplementary options in a dialog that has a simple/default state.
- Classic example: Save dialog expanding to show full file-system navigation.

**When NOT to use:**
- In hierarchical lists. Use a disclosure triangle instead.
- More than once per dialog/panel.

### 3.4 SwiftUI DisclosureGroup

`DisclosureGroup` is the SwiftUI equivalent covering both use cases (it maps to `NSDisclosureGroup` on macOS).

**Availability:** macOS 11.0+

**Initializers:**
```swift
// Simple: state managed internally
DisclosureGroup("Section Title") {
    // content views
}

// External state binding
DisclosureGroup(isExpanded: $isExpanded) {
    // content views
} label: {
    Text("Section Title")
}

// With localized key
DisclosureGroup("section.title.key") {
    // content views
}
```

**Visual behavior on macOS:**
- Renders with a disclosure indicator (chevron) to the left of the label.
- Collapsed: chevron points right.
- Expanded: chevron points down.
- Tapping/clicking the label or the chevron toggles the state.
- Supports keyboard navigation and focus ring.
- Aligns content vertically below the label when expanded.

**Animation:**
- Default animation is ease-in/ease-out on the expand/collapse transition.
- Can be customized: wrap state toggle in `withAnimation { isExpanded.toggle() }`.
- For a custom chevron that mimics the system indicator, rotate 0°→90° using `rotationEffect`:
```swift
Image(systemName: "chevron.right")
    .rotationEffect(isExpanded ? Angle(degrees: 90) : .zero)
```

**Style variants:**

| Style | API | Appearance |
|---|---|---|
| Automatic | `.disclosureGroupStyle(.automatic)` | Platform default (macOS: left-aligned chevron + label) |
| Navigation | Used in navigation lists | Integrated with list navigation affordances |

**DisclosureGroupStyle protocol:** Allows fully custom rendering of the disclosure control. Implement `makeBody(configuration:)` with `configuration.label`, `configuration.content`, and `configuration.isExpanded`.

### 3.5 Expandable Sections (SwiftUI List)

For list-style expandable sections (iOS 17+ / macOS 14+):
```swift
Section("Section Header", isExpanded: $isExpanded) {
    ForEach(items) { item in Text(item.name) }
}
```
This replaces the need for a `DisclosureGroup` when building expandable rows inside a `List`.

---

## 4. Progressive Disclosure Patterns

Progressive disclosure is the practice of initially presenting only the most important or commonly used options, and revealing additional complexity on demand. On macOS it is implemented via:

| Pattern | Control | Best for |
|---|---|---|
| Inline hierarchical expansion | Disclosure Triangle / `DisclosureGroup` | Outline views, settings lists, file browsers |
| Dialog expansion | Disclosure Button | Save/Print-style dialogs with basic vs. advanced modes |
| Contextual overlay | Popover | Focused, transient task without leaving current context |
| Side panel | Inspector (NSInspectorBar / `inspector(isPresented:content:)` on macOS 14+) | Persistent property editing alongside main content |
| Navigation drill-down | Sheet | Multi-step task requiring full focus |

**Design principles for progressive disclosure:**
1. Start with the minimum viable view. Show the most common path; hide the edge-case options.
2. The disclosure trigger (triangle, button, or chevron) should be adjacent to the content it controls.
3. Do not nest multiple levels of disclosure in a flat dialog (max one disclosure button per dialog).
4. If the expanded content requires its own scrolling, reconsider whether a separate panel or sheet is more appropriate.
5. Expanded state should persist across dismissals unless there is a reason to reset (e.g., a per-session advanced mode in a print dialog).

---

## 5. Decision Tree: Popover vs. Sheet vs. Alert vs. Inspector vs. Panel

Use this decision tree when choosing how to surface additional functionality or information.

### Step 1: Is user input required to unblock a critical operation?
- **Yes → Alert or Modal Dialog**
  - Use `NSAlert` for: confirmations before destructive actions, error notifications, permission prompts.
  - Use a modal sheet for: saving, exporting, printing, or any multi-step task that requires collecting structured input before proceeding.
  - Key rule from HIG: "windows forward even if they haven't dismissed the sheet yet" — sheets always appear attached to their parent window on macOS, never floating free.

### Step 2: Is the content tied to a specific anchor point and brief in scope?
- **Yes, and it disappears after the user finishes → Popover**
  - The user needs a small amount of information or a focused action related to one UI element.
  - Examples: formatting options for selected text, color picker attached to a color well, date picker attached to a date field, a share menu.
  - The popover should go away on its own (`.transient`) or with minimal user effort.
  - Rule from HIG: "limit the amount of functionality to a few related tasks."

### Step 3: Does the user need to repeatedly observe and adjust properties while keeping the main content visible?
- **Yes → Inspector Panel**
  - The inspector is a persistent, non-modal side panel.
  - On macOS 14+ SwiftUI: use the `.inspector(isPresented:content:)` modifier.
  - In AppKit: use a floating `NSPanel` or a split view with an inspector column.
  - Use an inspector instead of a sheet when "people need to repeatedly provide input and observe results" (Apple HIG, Sheets page).
  - Examples: Keynote's Format inspector, Xcode's Attributes inspector.

### Step 4: Is the content substantial enough to warrant a full panel but not worth blocking the main view?
- **Yes → Sheet**
  - Sheets are attached to the window that spawned them.
  - They focus the user on a specific task but do not block the entire application.
  - The user can bring other windows forward without dismissing the sheet.
  - Use sheets for: preferences, export options, account setup, multi-step configuration flows.

### Step 5: Should content appear inline within the existing layout hierarchy?
- **Yes → Disclosure Triangle / DisclosureGroup / Disclosure Button**
  - Inline expansion requires no overlay, no arrow, no transient layer.
  - Use when the detail is directly subordinate to a visible item in the current view.

### Summary decision matrix

| Question | Answer | Use |
|---|---|---|
| Blocks critical action? | Yes | NSAlert / Modal sheet |
| Anchored, brief, transient? | Yes | Popover (.transient) |
| Anchored, needs to persist alongside other interactions? | Yes | Popover (.semitransient or .applicationDefined) |
| Persistent property editing while main content stays visible? | Yes | Inspector panel |
| Full-focus task, parent window still accessible? | Yes | Sheet |
| Inline expansion within current layout? | Yes | Disclosure Triangle / Button / Group |
| New independent task in a separate workspace? | Yes | New window / document |

---

## 6. Do's and Don'ts

### Popovers

**Do:**
- Use popovers for contextual, focused interactions tied to a specific UI element.
- Set a reasonable `preferredContentSize` — 300–400 pt wide is the common comfortable range.
- Use `.transient` for most popovers; it matches user expectations for light-dismiss overlays.
- Use `.semitransient` for toolbar popovers where multiple toolbar controls may be used without closing the popover.
- Allow detachment (via the delegate) when the popover content benefits from being pinned as a floating window.
- Clean up the positioning view from the hierarchy in `popoverDidClose` when using the arrow-hide technique.

**Don't:**
- Don't make a popover so large it covers most of the screen. If content requires that much space, use a sheet or inspector.
- Don't put modal flows inside a popover. If the user must complete a sequence of steps before returning, use a sheet.
- Don't use a popover to show information that is always relevant. Use an inspector or sidebar instead.
- Don't use `.applicationDefined` behavior without providing a clear, explicit dismiss mechanism inside the popover.
- Don't hard-code size values if your content can self-size via Auto Layout.

### Tooltips

**Do:**
- Assign tooltips to all icon-only toolbar buttons and non-obvious controls.
- Keep tooltip text short: a noun phrase or imperative, ideally under 10 words.
- Use `NSView.toolTip` for static text; use `addToolTip(_:owner:userData:)` for dynamic content that changes based on state.
- Respect the system delay. Do not programmatically set `NSInitialToolTipDelay` to 0 in a shipping app — this is a user preference.

**Don't:**
- Don't repeat the visible label in a tooltip. Tooltips add information, not redundancy.
- Don't use tooltips as the only affordance for critical functionality. Tooltips are invisible until hovered; they are supplemental, not primary.
- Don't put multi-paragraph text in a tooltip. For richer contextual help, use a popover instead.
- Don't use tooltips on touch-based targets (this spec is macOS-only — tooltips are hover-dependent and do not function on touch).

### Disclosure Controls

**Do:**
- Use disclosure triangles throughout a list when every row can independently expand.
- Use exactly one disclosure button per dialog for progressively revealing advanced options.
- Use `DisclosureGroup` in SwiftUI for any collapsible section that needs a standard system appearance.
- Persist expanded state where it makes sense (e.g., a section the user has opened should stay open until they close it).
- Respect the visual convention: right-pointing = collapsed, down-pointing = expanded (macOS standard; note iOS has historically varied).

**Don't:**
- Don't use a disclosure triangle to reveal options for a single specific control — use a disclosure button.
- Don't place more than one disclosure button in a single window or panel.
- Don't use disclosure controls for primary navigation. They are for revealing/hiding content, not navigating to new contexts.
- Don't add custom animations that override the system ease-in/ease-out for the expand/collapse — it breaks the consistent platform feel. Use `withAnimation` wrapping the state toggle, which defers to the system default curve.

---

## 7. Sources

All claims in this document are sourced from the following:

| Source | Type | Coverage |
|---|---|---|
| `developer.apple.com/design/human-interface-guidelines/popovers` | Official Apple HIG | Popover design guidance |
| `developer.apple.com/design/human-interface-guidelines/disclosure-controls` | Official Apple HIG | Disclosure triangle and button design guidance |
| `developer.apple.com/design/human-interface-guidelines/sheets` | Official Apple HIG | Sheet usage rules; "use panel instead of sheet if repeatedly providing input" |
| `developer.apple.com/documentation/appkit/nspopover` | Official Apple API docs | NSPopover class — properties, methods, delegate |
| `developer.apple.com/documentation/appkit/nspopover/behavior-swift.enum` | Official Apple API docs | Behavior enum: transient, semitransient, applicationDefined |
| `developer.apple.com/documentation/appkit/nspopover/behavior-swift.enum/semitransient` | Official Apple API docs | Semitransient dismissal constraints |
| `developer.apple.com/documentation/appkit/nspopover/show(relativeto:of:preferrededge:)` | Official Apple API docs | Positioning method; preferred edge meaning |
| `developer.apple.com/documentation/SwiftUI/DisclosureGroup` | Official Apple API docs | DisclosureGroup init signatures, macOS availability (11.0+), keyboard navigation |
| `developer.apple.com/documentation/swiftui/disclosuregroupstyle` | Official Apple API docs | Style customization protocol |
| `developer.apple.com/documentation/AppKit/NSButton/BezelStyle-swift.enum/disclosure` | Official Apple API docs | Disclosure triangle bezel style |
| `learn.microsoft.com — AppKit.NSPopover` | Third-party API mirror | NSPopover properties: Animates, Behavior, ContentSize, ContentViewController, Detached, HasFullSizeContent, PositioningRect; NSPopover methods: Show, ShowRelative, Close, PerformClose; lifecycle notifications |
| `reddit.com/r/MacOS/comments/uz6tv4` | Community (Reddit, 27 upvotes) | NSInitialToolTipDelay default = 2000 ms; macOS 12.4 restored this preference |
| `github.com/p0deje/Maccy/issues/282` | Community (GitHub issue) | Tooltip default delay ~2 seconds |
| `stackoverflow.com/questions/24345004` (NSPopoverBehaviorSemitransient) | Community (Stack Overflow) | Semitransient behavior: does not close on events that open/close another popover; showing a semitransient closes other semitransient popovers |
| `stackoverflow.com/questions/30652593` (Cocoa tooltip delay) | Community (Stack Overflow) | NSToolTipManager.sharedToolTipManager().setInitialToolTipDelay(); per-object delay workaround via tracking regions |
| `stackoverflow.com/questions/10766819` (NSPopover arrow position) | Community (Stack Overflow) | Arrow position cannot be changed via public API in macOS 10.7+ |
| `nyrra33.com/2018/08/08` | Practitioner blog | Arrow-hide technique (move positioning view off-screen); preferred edge `.maxX`/`.maxY`/`.minX`/`.minY` behavior |
| `useyourloaf.com/blog/self-sizing-popovers/` | Practitioner blog | Recommended widths 300–400 pt; system shrinks above 600 pt; Auto Layout fitting size pattern |
| `mackuba.eu/2014/10/06/a-guide-to-nsbutton-styles/` | Practitioner reference | Disclosure triangle = `.disclosure` bezelStyle, fixed size, right-then-down arrow; disclosure button = `.roundedDisclosure`, max 1 per view; semantic distinction between the two types |
| `serialcoder.dev` (expandable sections SwiftUI) | Practitioner blog | Section(isExpanded:) iOS 17+/macOS 14+; withAnimation pattern; chevron rotationEffect 0°→90° |
| `ux.stackexchange.com/questions/124756` | Community (UX SE) | Popover vs. inspector vs. toolbar decision framework; Apple HIG quote on popover scope |
| `venkatasg.net/blog/disclosure-2023-01-13.html` | Practitioner analysis | Disclosure triangle vs. disclosure button/link distinction on macOS vs. iOS; right=collapsed, down=expanded convention |
| `apple.stackexchange.com/questions/462845` | Community (ASE) | NSInitialToolTipDelay user default; `defaults write -g NSInitialToolTipDelay -int 100` example |
| `github.com/github/Rebel/issues/94` | Community (GitHub) | NSPopover contentSize quote: "set to match the size of the content view when the content view controller is set; changes animate if animates is YES" |
