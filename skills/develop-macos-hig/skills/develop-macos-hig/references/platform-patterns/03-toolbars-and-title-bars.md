# macOS Toolbars and Title Bars Reference

> **Scope:** macOS only. Covers window toolbars (NSToolbar/AppKit) and title bar integration.
> **Last researched:** 2026-04-05 against macOS Sequoia 15 / WWDC20 session 10104 / AppKit documentation.

---

## 1. Toolbar Styles

Toolbar styles were introduced as a formal enum (`NSWindow.ToolbarStyle`) in macOS 11 Big Sur. The style determines where the toolbar appears relative to the title bar and how items are sized and labeled.

| Style | Enum Case | Use Case | Item Labels | Layout |
|---|---|---|---|---|
| Unified | `.unified` | Most apps (default) | Hidden by default | Window controls + title + items share one row |
| Unified Compact | `.unifiedCompact` | Apps needing more content space | Hidden by default | Same as unified but shorter height |
| Expanded | `.expanded` | Document-based apps | Shown by default, compact | Title bar above; items row below |
| Preference | `.preference` | Settings windows | Shown; selected item highlighted | Title bar above; items row below, centered |
| Automatic | `.automatic` | System-chosen (preserves pre-Big Sur layout) | Varies | System decides based on window structure |

### Height

Apple's WWDC20 session 10104 describes the heights qualitatively rather than with fixed pixel values — the system manages exact height based on control sizes:

- **Unified:** Taller than previous toolbars. Introduced a **large control size** for toolbar items, making controls and icons larger and heavier weight.
- **Unified Compact:** "A more compressed layout with regular-sized controls and a smaller toolbar height" (WWDC20 transcript). Uses **regular** (not large) controls — same size mode as pre-Big Sur.
- **Expanded:** Title sits above the toolbar row. Height of the title bar area and toolbar row are separate.
- **Preference:** Similar structure to expanded; items are larger and centered.

No pixel value for window toolbar height is published in Apple's HIG. The height is determined by the toolbar's `sizeMode` (`.regular` or `.small`) and the `controlSize` of items. Apple explicitly deprecated `NSToolbarItem.minSize` / `maxSize` starting macOS Ventura — sizing is now entirely via Auto Layout and `controlSize`.

**Practical reference from NSToolbar.SizeMode (official API documentation):**

| Size Mode | Enum Case | Icon Canvas | Controls |
|---|---|---|---|
| Regular (default) | `.regular` | 32 × 32 pt | Regular-sized |
| Small | `.small` | 24 × 24 pt | Small-sized |

The unified style introduces a third tier — **large control size** — which is set per-item via `button.controlSize = .large`, not via `sizeMode`. Large controls are larger than the regular 32 pt canvas; the system handles the expanded height automatically.

### API

```swift
// Set toolbar style on the window (macOS 11+)
window.toolbarStyle = .unified          // or .unifiedCompact, .expanded, .preference

// Set size mode on the toolbar object (legacy, still functional)
toolbar.sizeMode = .regular             // or .small

// Set large control size on a button item (macOS 11+)
button.controlSize = .large
```

---

## 2. Toolbar Items

### Item Types

| Item Class / Identifier | Description | macOS Version |
|---|---|---|
| `NSToolbarItem` | Standard item: icon, label, action | 10.0+ |
| `NSToolbarItemGroup` | Collection of subitems; renders as segmented control or picker | 10.0+ |
| `NSSearchToolbarItem` | Adaptive search field; collapses to icon, expands on click | 11.0+ |
| `NSMenuToolbarItem` | Toolbar button with an attached dropdown menu | 11.0+ |
| `NSSharingServicePickerToolbarItem` | System share sheet button; full delegate setup included | 11.0+ |
| `NSTrackingSeparatorToolbarItem` | Vertical separator that tracks a split-view divider | 11.0+ |
| `.flexibleSpace` (identifier) | Expands to fill remaining space | 10.0+ |
| `.space` (identifier) | Fixed-width space | 10.0+ |
| `.toggleSidebar` (identifier) | Built-in sidebar toggle with correct icon, labels, and action | 11.0+ |
| `.sidebarTrackingSeparator` (identifier) | Separator that aligns with the sidebar split-view divider | 11.0+ |
| `.toggleInspector` (identifier) | Built-in inspector sidebar toggle | 13.0+ |
| `.inspectorTrackingSeparator` (identifier) | Separator that aligns with the inspector split-view divider | 13.0+ |
| `.cloudSharing` (identifier) | iCloud sharing interface button | 10.12+ |
| `.writingToolsItemIdentifier` (identifier) | Apple Intelligence Writing Tools UI | 15.0+ |

### Item Dimensions

| Attribute | Regular Mode | Small Mode | Notes |
|---|---|---|---|
| Icon canvas size | 32 × 32 pt | 24 × 24 pt | From `NSToolbar.SizeMode` API docs |
| Large control (unified style) | Larger than 32 pt | N/A | Exact size system-managed |
| `minSize` / `maxSize` | Deprecated (Ventura+) | Deprecated (Ventura+) | Use Auto Layout on item's view |
| Segmented control example | ~85 × 40 pt | — | Per-segment ~40 pt wide (practitioner reference) |

For custom view items, set constraints on `toolbarItem.view` using Auto Layout. The old `setMaxSize:` / `setMinSize:` APIs on `NSToolbarItem` are deprecated as of macOS Ventura and produce console warnings.

```swift
// Modern sizing for custom view items
let view = MyCustomView()
view.translatesAutoresizingMaskIntoConstraints = false
NSLayoutConstraint.activate([
    view.widthAnchor.constraint(equalToConstant: 80),
    view.heightAnchor.constraint(equalToConstant: 32)
])
toolbarItem.view = view
```

### Display Modes

The toolbar's `displayMode` controls what is shown for each item:

| Mode | Enum Case | Shows |
|---|---|---|
| Default (system) | `.default` | System-determined |
| Icon + Label | `.iconAndLabel` | Icon above label |
| Icon Only | `.iconOnly` | Icon; tooltip on hover |
| Label Only | `.labelOnly` | Label text only |

### Item Ordering Principles

1. Items most critical to the user's primary mental model go **leftmost**.
2. Logical groups follow in descending importance left to right.
3. **Global items** (Search, Share) go **trailing** (rightmost).
4. **Inspector toggle** must be the **trailing-most** item.
5. **Share** follows immediately before the Inspector toggle.
6. **Global Search** is next, since it expands horizontally when activated.
7. **Sidebar toggle** must be **anchored at the leading edge** — it must not move when the sidebar opens or closes.

### Centered Items

Use `NSToolbar.centeredItemIdentifiers` to designate one or more items as always-centered. This is appropriate for navigation controls (as in Music.app, Safari's address bar, Photos' view picker).

```swift
toolbar.centeredItemIdentifiers = [.navigationSegment]
```

### NSToolbarItemGroup (Segmented / Picker)

`NSToolbarItemGroup` holds subitems and renders as a segmented control when space allows, collapsing to a picker/menu when constrained.

```swift
let group = NSToolbarItemGroup(itemIdentifier: .navigationGroup)
let prevItem = NSToolbarItem(itemIdentifier: .previousItem)
prevItem.label = "Back"
let nextItem = NSToolbarItem(itemIdentifier: .nextItem)
nextItem.label = "Forward"

let segmented = NSSegmentedControl()
segmented.segmentCount = 2
segmented.setImage(NSImage(named: .goLeftTemplate)!, forSegment: 0)
segmented.setWidth(40, forSegment: 0)
segmented.setImage(NSImage(named: .goRightTemplate)!, forSegment: 1)
segmented.setWidth(40, forSegment: 1)

group.subitems = [prevItem, nextItem]
group.view = segmented
```

### NSSearchToolbarItem

Introduced in macOS 11. Replaces manually embedding an `NSSearchField` in a toolbar item. The item collapses to a search icon and expands to a search field when space is available or the user clicks it.

```swift
let searchItem = NSSearchToolbarItem(itemIdentifier: .search)
searchItem.searchField = existingSearchField   // attach your NSSearchField
```

### NSTrackingSeparatorToolbarItem

Creates a visual separator that tracks a `NSSplitView` divider, keeping toolbar regions visually aligned with content columns.

```swift
let trackingItem = NSTrackingSeparatorToolbarItem(
    itemIdentifier: .sidebarTrackingSeparator,
    splitView: splitViewController.splitView,
    dividerIndex: 0
)
```

---

## 3. Toolbar Customization

### Enabling User Customization

When `allowsUserCustomization = true`, the user can access the customization palette via View > Customize Toolbar (or right-clicking the toolbar). They can add, remove, and reorder items from the allowed set.

```swift
toolbar.allowsUserCustomization = true
toolbar.autosavesConfiguration = true   // persists changes to user defaults
```

`autosavesConfiguration` keys off the toolbar's `identifier`, so toolbars sharing an identifier share the same saved configuration.

Disabling customization removes the "Customize Toolbar…" menu item but does not prevent the user from showing or hiding the toolbar entirely.

### Delegate Methods

The `NSToolbarDelegate` controls what items exist and how the toolbar is configured:

| Method | Purpose |
|---|---|
| `toolbar(_:itemForItemIdentifier:willBeInsertedIntoToolbar:)` | Creates and returns the `NSToolbarItem` for a given identifier |
| `toolbarDefaultItemIdentifiers(_:)` | Identifiers and order of items in the **default** configuration |
| `toolbarAllowedItemIdentifiers(_:)` | All identifiers that can appear in the toolbar or customization palette |
| `toolbarSelectableItemIdentifiers(_:)` | Identifiers of items the user can "select" (for preference-style highlighting) |
| `toolbarWillAddItem(_:)` | Called before an item is added |
| `toolbarDidRemoveItem(_:)` | Called after an item is removed |

### Default vs. Allowed Items

- **Default items** (`toolbarDefaultItemIdentifiers`): the initial arrangement when no saved configuration exists. Keep this to the most essential items.
- **Allowed items** (`toolbarAllowedItemIdentifiers`): the full superset of items available in the customization palette, including all items the user could ever add. Can include more items than the default set.
- Users can always restore to the default set via the "Use Default Set" button in the customization palette.

### Customization Palette (Sheet)

The customization sheet displays all allowed items not currently in the toolbar. Users drag items from the palette into the toolbar or drag items from the toolbar into the palette to remove them. The palette also shows the "Use Default Set" button.

```swift
// Programmatically open the customization palette
toolbar.runCustomizationPalette(sender)

// Check if palette is visible
let isOpen = toolbar.customizationPaletteIsRunning
```

---

## 4. Overflow Behavior

When the toolbar is too narrow to display all items, items are moved to an overflow menu represented by a chevron (`›`) at the trailing edge.

### Priority Rules (in order)

1. Items with **lower `visibilityPriority`** are hidden first, regardless of position in the toolbar.
2. Among items of equal priority, items are hidden **right to left**.

### Setting Priority

```swift
toolbarItem.visibilityPriority = .high    // NSToolbarItem.VisibilityPriority
// .high, .user, .low — standard constants
// Custom values: any NSToolbarItem.VisibilityPriority(rawValue:)
```

High-priority items (e.g., Compose, Get Mail in a mail app) should be `.high` to ensure they stay visible longest. Lower-priority items (Move, Flag) use `.user` or `.low`.

### Overflow Menu Behavior

- Items moved to overflow retain their full label and action.
- Items maintain their original order within the overflow menu.
- Hidden items (those the user has removed via customization) do not appear in the overflow menu — they are gone until the user restores them via the customization palette.
- **Important caveat (macOS Sonoma bug):** A bug introduced in macOS Sonoma causes toolbar items in the sidebar portion to move to the overflow menu incorrectly when the sidebar is hidden. The workaround is to set the sidebar's `minimumThickness` to be wide enough to accommodate its items.

### Sidebar Item Guidelines

The toolbar portion above a sidebar should have **no more than two items**. This prevents items from being sent to overflow when the sidebar is narrow. The recommendation is to place only the sidebar toggle in the sidebar toolbar and put additional sidebar-specific controls in a **Bottom Bar** below.

---

## 5. Title Bar Integration

### NSWindow.StyleMask Flags Relevant to Title Bar

| StyleMask | Effect |
|---|---|
| `.titled` | Standard title bar with title text and traffic-light buttons |
| `.fullSizeContentView` | Content view extends under the title bar and toolbar area |
| `.unifiedTitleAndToolbar` | Legacy flag; since macOS Yosemite, title bar and toolbar are unified automatically |

### Title Visibility

`NSWindow.titleVisibility` controls whether the window title text is rendered:

| Value | Effect | Typical Usage |
|---|---|---|
| `.visible` (default) | Title text shown in title bar | Standard windows |
| `.hidden` | Title text hidden; traffic-light buttons remain | Unified toolbar apps (Calendar, Notes, Xcode) |

Setting `titleVisibility = .hidden` vertically centers the traffic-light buttons in the title bar area, which gives a cleaner unified look when the toolbar contains the conceptual "title" of the window.

### Title Bar Variants

#### Standard Title Bar

Default. Separate title bar row with window title text and traffic-light buttons. A toolbar (if present) appears as a separate row below.

```swift
window.titleVisibility = .visible
window.titlebarAppearsTransparent = false
```

#### Unified Title and Toolbar

Introduced formally in macOS 11 via `NSWindow.ToolbarStyle.unified`. The title bar and toolbar share the same visual area. The window title appears inline at the leading edge of the toolbar (next to the sidebar), or is hidden entirely.

```swift
window.toolbarStyle = .unified
// Optionally hide the title text if toolbar content serves as the title
window.titleVisibility = .hidden
```

#### Transparent Title Bar

`titlebarAppearsTransparent = true` removes the background of the title bar, allowing content to show through. The traffic-light buttons remain. Combine with `fullSizeContentView` to let the content view extend into the title bar region.

```swift
window.titlebarAppearsTransparent = true
window.styleMask.insert(.fullSizeContentView)
```

With both `titlebarAppearsTransparent` and `titleVisibility = .hidden`, the window has no visible title bar area — only the traffic-light buttons float above the content. This pattern is used by apps like Reeder.

For the translucency effect seen in Safari or Finder, simply use `toolbarStyle = .unified` on a window with a toolbar; the system applies the appropriate blur material automatically.

#### Hidden Title Bar

Complete removal of title bar rendering while keeping standard window chrome:

```swift
window.titlebarAppearsTransparent = true
window.titleVisibility = .hidden
window.styleMask.insert(.fullSizeContentView)
window.styleMask.insert(.titled)   // keeps traffic-light buttons
```

### Inline Title Display

The inline title places the window title as text inside the unified toolbar area rather than in a traditional title bar row. It appears at the **leading edge of the toolbar**, adjacent to the sidebar.

Supported in: `.unified` and `.unifiedCompact` toolbar styles.

**Subtitle support (macOS 11+):** `NSWindow.subtitle` displays secondary text beneath the primary title inline in the toolbar (e.g., an unread message count below a mailbox name).

```swift
window.title = "Inbox"
window.subtitle = "3 unread"    // appears below the inline title
```

### NSTitlebarAccessoryViewController

Use this class to embed custom views alongside the title bar. Three layout positions are available:

| Position | Description |
|---|---|
| `.bottom` | Below the title bar / toolbar area |
| `.left` | Left side of the title bar |
| `.right` | Right side of the title bar |

This is distinct from toolbar items. Accessory views are always visible regardless of toolbar visibility and cannot be customized by the user.

### Full-Height Sidebar Integration

For windows with full-height sidebars (macOS 11+), use:

```swift
// NSSplitViewItem for the sidebar
let sidebarItem = NSSplitViewItem(sidebarWithViewController: sidebarVC)
sidebarItem.allowsFullHeightLayout = true   // sidebar extends under title bar

// NSSplitViewItem for the content
let contentItem = NSSplitViewItem(contentListWithViewController: contentVC)
contentItem.allowsFullHeightLayout = true

// Toolbar identifiers for full-height layout
// .toggleSidebar and .sidebarTrackingSeparator must both be in the default item identifiers
```

---

## 6. Touch Bar

### Hardware Status

The Touch Bar is **fully discontinued as of October 30, 2023**, when Apple discontinued the 13-inch MacBook Pro (M2) — the last Mac ever sold with a Touch Bar. The hardware ran from 2016 (first MacBook Pro with Touch Bar) through 2023.

- **Last model with Touch Bar:** 13-inch MacBook Pro (M2), discontinued October 2023
- **Replaced by:** 14-inch MacBook Pro (M3, base chip)
- **Hardware now sold:** No current Mac has a Touch Bar

**Timeline:**
- 2016: Touch Bar introduced on MacBook Pro (15-inch and 13-inch)
- 2021: 14-inch and 16-inch MacBook Pro (M1 Pro/Max) launch without Touch Bar
- 2022: 13-inch MacBook Pro (M2) — final Touch Bar model available new
- 2023 (October): 13-inch M2 MacBook Pro discontinued; Touch Bar ends

### API Status

`NSTouchBar` and related APIs remain in the SDK and are not formally deprecated in the API reference as of the research date. However:

- The HIG page for Touch Bar returns **404** (removed from the HIG).
- Apple has no current hardware that supports it.
- There is no developer-facing guidance to migrate away, but no reason to build new Touch Bar UI.

**Practical guidance:** Do not implement Touch Bar UI in new applications. Any essential functionality previously in the Touch Bar must be available in the main UI or via keyboard shortcuts. Existing NSTouchBar code will not crash but will silently do nothing on all current Mac hardware.

### Touch Bar Design Principles (Historical Reference)

When the Touch Bar was active, Apple's guidance was:

- Complement, never replace, primary UI actions
- Provide contextually relevant controls for the current task
- Mirror the most-used toolbar items as Touch Bar items
- Never require the Touch Bar for any essential function
- Provide physical keyboard alternatives (function keys, shortcuts) for every Touch Bar action
- Keep controls large enough for accurate touch (minimum ~44 pt on the Touch Bar's 2170 × 60 pt canvas)

The Touch Bar ran at 2170 × 60 pixels (physical), presented as a 1085 × 30 pt canvas to AppKit. Items were arranged left-to-right; the system reserved the far-right for the Control Strip (brightness, volume, Siri).

---

## 7. Do's and Don'ts

### Do's

- **Use `.unified` style** for most apps. It is the current macOS standard and makes your app look native.
- **Use `.unifiedCompact`** when vertical screen real estate is at a premium and your toolbar items are simple icon-only buttons.
- **Use `.expanded`** for document-based apps where the window title is long or needs to span the full width.
- **Use `.preference`** for Settings windows; it provides the highlighted-selection behavior expected by users.
- **Place the sidebar toggle at the leading edge and anchor it** so it does not shift when the sidebar opens or closes.
- **Use built-in identifiers** (`.toggleSidebar`, `.sidebarTrackingSeparator`, `.toggleInspector`, `.inspectorTrackingSeparator`) to get correct icons, labels, localization, and behavior for free.
- **Assign `visibilityPriority`** to every item so the most important items stay visible the longest as the window narrows.
- **Use `NSSearchToolbarItem`** for search; it handles the expand/collapse behavior automatically.
- **Provide a tooltip** (`toolTip`) and palette label (`paletteLabel`) for every item, even icon-only items.
- **Enable `autosavesConfiguration`** whenever `allowsUserCustomization` is true so user preferences persist.
- **Test toolbar appearance in both Light and Dark mode** and at all window widths.
- **Give every toolbar action a keyboard shortcut** accessible via the application's menu bar.
- **Use `NSWindow.subtitle`** (macOS 11+) instead of embedding secondary context text into the title string.
- **Set `allowsFullHeightLayout = true`** on `NSSplitViewItem`s when using full-height sidebars.

### Don'ts

- **Don't overload the toolbar.** Include only frequently-used commands. If in doubt, put it in the menu bar, not the toolbar.
- **Don't put a toolbar item for every menu command.** The relationship is one-way: toolbar items must have menu equivalents, but not vice versa.
- **Don't use `NSToolbarItem.minSize` / `maxSize`** on Ventura+; they are deprecated and produce console warnings. Use Auto Layout constraints on the item's view.
- **Don't rely on the Touch Bar** for any functionality. All current Mac hardware ships without it.
- **Don't place the Inspector toggle anywhere but the trailing-most position** in the toolbar.
- **Don't place the Sidebar toggle anywhere but the leading-most position**, and never let it move.
- **Don't put more than two items in the sidebar's toolbar portion.** Narrow sidebars will push them to overflow.
- **Don't embed interactive controls (text fields, sliders) in the toolbar without adequate padding.** Use `.fullSizeContentView` carefully if your toolbar items need touch/click precision near the window edge.
- **Don't set `displayMode = .labelOnly`** in the unified style; labels without icons look out of place.
- **Don't implement new Touch Bar UI** for new applications; no Mac ships with the hardware.

---

## 8. Sources

| Source | Type | URL / Reference |
|---|---|---|
| Apple HIG: Toolbars (scraped) | Official HIG | `https://developer.apple.com/design/human-interface-guidelines/toolbars` |
| WWDC20 Session 10104: Adopt the new look of macOS | Official session | `https://developer.apple.com/videos/play/wwdc2020/10104/` |
| NSToolbar.SizeMode API docs | Official API | `https://developer.apple.com/documentation/appkit/nstoolbar/sizemode-swift.enum` |
| NSWindow.ToolbarStyle API docs | Official API | `https://developer.apple.com/documentation/appkit/nswindow/toolbarstyle-swift.enum` |
| NSWindow.TitleVisibility API docs | Official API | `https://developer.apple.com/documentation/appkit/nswindow/titlevisibility-swift.enum` |
| NSWindow.titlebarAppearsTransparent API docs | Official API | `https://developer.apple.com/documentation/appkit/nswindow/titlebarappearstransparent` |
| NSToolbarDelegate.toolbarAllowedItemIdentifiers | Official API | `https://developer.apple.com/documentation/appkit/nstoolbardelegate/toolbaralloweditemidentifiers(_:)` |
| NSSearchToolbarItem API docs | Official API | `https://developer.apple.com/documentation/appkit/nssearchtoolbaritem` |
| NSTrackingSeparatorToolbarItem API docs | Official API | `https://developer.apple.com/documentation/appkit/nstrackingseparatortoolbaritem` |
| NSToolbarItemGroup API docs | Official API | `https://developer.apple.com/documentation/appkit/nstoolbaritemgroup` |
| NSToolbar class reference (Leopard ADC archive) | Official (legacy) | `https://leopard-adc.pepas.com/documentation/Cocoa/Reference/ApplicationKit/Classes/NSToolbar_Class/Reference/Reference.html` |
| Toolbar Guidelines — Mario Guzman | Practitioner (ex-Apple) | `https://marioaguzman.github.io/design/toolbarguidelines/` |
| TitlebarAndToolbar showcase — Robin | Developer showcase | `https://github.com/robin/TitlebarAndToolbar` |
| macOS full-height sidebar window — Paul Bancarel | Practitioner blog | `https://medium.com/@bancarel.paul/macos-full-height-sidebar-window-62a214309a80` |
| How to Create a Segmented NSToolbarItem — Christian Tietze | Practitioner blog | `https://christiantietze.de/posts/2016/06/segmented-nstoolbaritem/` |
| NSToolbarItem sizing post-Ventura — Stack Overflow | Community | `https://stackoverflow.com/questions/74742106/how-to-set-the-size-of-an-nstoolbaritem-on-macos-ventura-since-setmaxsize-is-dep` |
| Touch Bar fully discontinued — MacRumors | News (verified) | `https://www.macrumors.com/2023/10/31/touch-bar-discontinued/` |
| Goodbye Touch Bar — The Verge | News (verified) | `https://www.theverge.com/2023/10/31/23938841/apple-macbook-pro-touch-bar-discontinued-proof-of-concept` |
| Apple HIG: Touch Bar — 404 confirms removal | Official (removed) | `https://developer.apple.com/design/human-interface-guidelines/touch-bar` |
| WWDC Notes: Adopt the new look of macOS | Community notes | `https://wwdcnotes.com/documentation/wwdcnotes/wwdc20-10104-adopt-the-new-look-of-macos/` |
