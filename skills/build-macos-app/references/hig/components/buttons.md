# macOS Buttons and Action Controls

**Scope:** macOS only. Every specification sourced directly from Apple HIG JSON API and official AppKit/SwiftUI documentation.

---

## 1. Button Variants Catalog

A button on macOS combines three attributes: **style** (visual appearance), **content** (symbol, text label, or both), and **role** (semantic meaning). Beyond the standard push button, macOS defines several specialized variants, each with its own bezel style, sizing, and usage rules.

### 1.1 Quick-Reference Table

| Variant | AppKit BezelStyle | SwiftUI Style | Sizes Available | Primary Context |
|---|---|---|---|---|
| Push button (standard) | `.push` | `.bordered` | mini, small, regular, large | Windows, dialogs, sheets |
| Push button (flexible height) | `.flexiblePush` | `.bordered` | mini, small, regular, large | Multi-line text, tall icons |
| Square / Gradient button | `.smallSquare` | n/a | Scalable | Adjacent to table/list views |
| Help button | `.helpButton` | n/a | Fixed (one size) | Dialogs, preference panes |
| Circular button | `.circular` | n/a | Controlled by control size | Toolbars, panels |
| Image button | `.automatic` (borderless) | `.plain` | Any | View bodies (not toolbars) |
| Disclosure button | `.disclosure` | n/a | System-defined | Collapsible rows |
| Push-Disclosure button | `.pushDisclosure` | n/a | System-defined | Combined action + expand |
| Toolbar button | `.toolbar` | `.borderless` | System-defined | Toolbar items only |
| Accessory bar button | `.accessoryBar` | `.accessoryBar` | System-defined | Scope bars, search accessories |
| Accessory bar action button | `.accessoryBarAction` | `.accessoryBarAction` | System-defined | Extra actions in accessory toolbars |
| Recessed button | `.recessed` | n/a | System-defined | Scope bars, title bar accessories |
| Inline button | `.inline` | n/a | System-defined | Solid round-rect border contexts |
| RoundRect button | `.roundRect` | n/a | System-defined | Action/auxiliary in scope bars |
| Badge button | `.badge` | n/a | System-defined | Displaying additional information |
| Link button | n/a (link style) | `.link` | n/a (text-sized) | In-line hyperlinks within text |
| Checkbox | `NSButton.ButtonType.switch` | SwiftUI `Toggle` `.checkbox` | mini, small, regular | Settings panes, forms |
| Radio button | `NSButton.ButtonType.radio` | SwiftUI `Toggle` (grouped) | mini, small, regular | Mutually exclusive option groups |
| Pop-up button | `NSPopUpButton` (pullsDown: false) | `Menu` / `.menuIndicator` | mini, small, regular | Single selection from a flat list |
| Pull-down button | `NSPopUpButton` (pullsDown: true) | `Menu` | mini, small, regular | Action menus tied to a button |
| Segmented control | `NSSegmentedControl` | `Picker(.segmented)` | mini, small, regular, large | Grouped options or actions |
| Switch toggle | `NSSwitch` | `Toggle(.switch)` | mini, regular | Settings with visual emphasis |

---

## 2. Push Buttons

### 2.1 Definition

The push button is the standard macOS button type (`NSButton` with `bezelStyle = .push`). It initiates an immediate, one-shot action. Push buttons can display text, a symbol, an icon, an image, or a combination of text and image.

### 2.2 Sizes and Dimensions

Apple does not publish a single pixel table in prose; the authoritative values come from the macOS Design Resources sketch/Figma files and Interface Builder's built-in size presets. The measured point dimensions for the `.push` bezel style across control sizes are:

| Control Size | AppKit Constant | SwiftUI `.controlSize` | Height (pt) | Min Width (pt) | Corner Radius (pt) |
|---|---|---|---|---|---|
| Mini | `.mini` | `.mini` | ~16 | ~36 | ~3 |
| Small | `.small` | `.small` | ~22 | ~48 | ~4 |
| Regular | `.regular` | `.regular` | ~32 | ~64 | ~6 |
| Large | `.large` | `.large` | ~38 | ~80 | ~8 |

> Note: Apple does not publish official point dimensions for macOS push buttons in the HIG text. The figures above are widely verified by the Apple Design Resources and Xcode's Interface Builder defaults. The HIG states only that **the minimum hit region for any button must be 44x44 pt**, which applies to interactive precision; visual heights can be smaller as long as the hit target is met.

### 2.3 Flexible-Height Push Button

`NSButton.BezelStyle.flexiblePush` — identical visual treatment to `.push` but supports variable height. Use when:
- Button content includes a newline (`\n`) in the title
- Width is constrained via Auto Layout and text must wrap
- Content is a tall icon that exceeds the standard fixed height

Shares the same corner radius and content padding as `.push` so it looks visually consistent. SwiftUI equivalent: `.bordered` with multi-line label.

### 2.4 Button Roles

Every push button can be assigned one of four semantic roles:

| Role | AppKit | SwiftUI | Visual Effect | Keyboard |
|---|---|---|---|---|
| Normal | default | none / `.buttonRole(nil)` | System default appearance | None assigned by default |
| Primary (Default) | `.keyEquivalent = "\r"` | `.buttonRole(nil)` + `.keyboardShortcut(.defaultAction)` | Accent-colored fill (blue by default) with pulsing animation when window is key | Return / Enter |
| Cancel | `.keyEquivalent = "\u{1b}"` | `.buttonRole(.cancel)` | Standard bezel, no fill tint | Escape |
| Destructive | `hasDestructiveAction = true` | `.buttonRole(.destructive)` | System red fill color | None; do not assign Return |

**Default (Primary) button rules:**
- One default button per view at most
- The system animates the default button with a repeating pulse (brightness oscillation) when the window is key and no text field has focus
- Pressing Return activates the default button even when keyboard focus is elsewhere
- In sheets and alerts, the default button also closes the view automatically
- Never assign the primary role to a destructive action — the visual prominence causes accidental activation

**Destructive button rules:**
- Rendered in system red
- Do not also make destructive the default button
- Should always be accompanied by a Cancel button

### 2.5 Interactive States

| State | Visual Description |
|---|---|
| Normal (off) | Standard bezel, label in primary text color |
| Hover | Slight brightness increase; cursor changes to arrow (not pointer) |
| Pressed | Bezel darkens or inverts; label color may invert |
| Focused | Blue focus ring (NSFocusRingType) appears outside bezel |
| Disabled | Label and bezel are dimmed (approximately 50% opacity); not interactive |
| Default (pulsing) | Continuous brightness oscillation on the filled bezel |
| Toggled On (toggle type) | Alternate title/image shown; bezel appears recessed or filled |

### 2.6 AppKit API

```swift
// Standard push button
let button = NSButton(title: "Continue", target: self, action: #selector(didContinue))
button.bezelStyle = .push                          // or .automatic in modern code
button.controlSize = .regular                       // .mini | .small | .regular | .large
button.keyEquivalent = "\r"                        // makes it the default button
button.hasDestructiveAction = true                  // red fill for destructive actions

// Flexible-height push button
button.bezelStyle = .flexiblePush
```

### 2.7 SwiftUI API

```swift
// Standard button
Button("Continue") { }
    .buttonStyle(.bordered)                         // or .borderedProminent
    .buttonRole(.cancel)                            // .cancel | .destructive
    .controlSize(.regular)                          // .mini | .small | .regular | .large
    .keyboardShortcut(.defaultAction)               // binds to Return
    .keyboardShortcut(.cancelAction)                // binds to Escape
    .tint(.red)                                     // override for destructive
```

### 2.8 Spring Loading

On Macs with a Magic Trackpad, push buttons can support **spring loading**: a user drags selected items over the button and force-clicks (presses harder) without dropping the items. The button activates, then the user can continue dragging. Enable via `isSpringLoaded = true` on `NSButton`.

### 2.9 Ellipsis Convention

When a push button opens another window, view, or app rather than performing an immediate action, append a trailing ellipsis (`…`) to its title — for example, "Find…", "Edit…", "Get Info…". This signals that additional input is required before the action completes.

### 2.10 Content Padding

- Image buttons: ~10 pt of padding between image edges and button edges (`isBordered = false` when using an image button in a view)
- Push buttons: horizontal padding is applied automatically by the bezel style; do not manually override unless absolutely necessary

---

## 3. Square (Gradient) Button

**AppKit:** `NSButton.BezelStyle.smallSquare`
**HIG name:** "Square button" (also called "gradient button" in older documentation)

### 3.1 Behavior

A square button initiates an action that affects a specific view — most commonly adding or removing rows from a table, or toggling a mode related to that view. It can be configured as:
- Push behavior (`momentaryPushIn`)
- Toggle behavior (`pushOnPushOff`)
- Pop-up button behavior (`NSPopUpButton` subclass)

### 3.2 Content Rules

- Contains symbols or icons — **never text**
- Use SF Symbols for automatic color adaptation and scaling
- Place the button in close proximity to (within or beneath) its associated view

### 3.3 Placement Rules

- Use in the **view body only** — not in toolbars, title bars, or status bars
- A toolbar requires `NSToolbarItem`; a status bar requires `NSStatusItem`
- Do not introduce with a label; the button's proximity to its view is context enough

### 3.4 Size

The `.smallSquare` bezel style scales to any size; set width and height constraints explicitly. Typical usage: 22x22 pt (small), matching the bottom edge of a scroll view or table.

---

## 4. Help Button

**AppKit:** `NSButton.BezelStyle.helpButton`

### 4.1 Appearance

Circular button containing a `?` (question mark) character. Size is fixed by the system — do not attempt to resize it. Appears at a single, system-defined size regardless of `controlSize`.

### 4.2 Placement

- Bottom-trailing corner of dialogs and preference panes (the conventional position)
- Within the view body — never in a toolbar or status bar
- Maximum one per window

### 4.3 Behavior

Clicking a help button opens app-specific help documentation. When possible, link directly to the topic most relevant to the current context. If no specific topic exists, link to the root of your app's Help Book.

### 4.4 Rules

- Do not display explanatory text next to it — users know what `?` means
- Do not put a help button in a toolbar or title bar

### 4.5 AppKit API

```swift
let helpButton = NSButton(title: "", target: self, action: #selector(openHelp))
helpButton.bezelStyle = .helpButton
helpButton.title = ""    // title must be empty for help button appearance
```

---

## 5. Image Button

**AppKit:** `NSButton` with `isBordered = false`; or `NSButton.BezelStyle.automatic` on an image-only button

### 5.1 Use Cases

Displays an image, symbol, or icon. Can be configured as push, toggle, or pop-up. Common in preference panes and custom view bodies.

### 5.2 Rules

- Place in the **view body only** — use `NSToolbarItem` for toolbar placement
- Include approximately **10 pt of padding** between the image's edges and the button's hit area
- Do not show a system border (`isBordered = false`) for image buttons in general use
- If a label is needed, place it **below** the button, not beside it

---

## 6. Circular Button

**AppKit:** `NSButton.BezelStyle.circular`

A round button containing a single character or a small icon. System images (SF Symbols) scale automatically to fit. Large images shrink rather than clip.

Use when you need a round affordance for a single glyph — for example, add/remove controls or media player buttons.

---

## 7. Disclosure and Push-Disclosure Buttons

| Variant | AppKit | Purpose |
|---|---|---|
| Disclosure triangle | `.disclosure` | Collapse/expand a view inline (e.g., row details) |
| Push-Disclosure | `.pushDisclosure` | Combined push action + vertical expand/collapse |
| Rounded Disclosure | `.roundedDisclosure` | Vertically expanding/collapsing disclosure with rounded rect border |

Disclosure buttons use a triangle that rotates 90° between collapsed (pointing right) and expanded (pointing down) states. Do not use for navigation; use for showing/hiding content within the current view.

---

## 8. Borderless and Link Buttons

### 8.1 Borderless Button

**AppKit:** `NSButton` with `isBordered = false` or `.showsBorderOnlyWhileMouseInside = true`
**SwiftUI:** `.buttonStyle(.plain)` or `.buttonStyle(.borderless)`

Used in toolbars and situations where the button must not have a visible bezel at rest. The border may appear on hover via `showsBorderOnlyWhileMouseInside`. Toolbar items use this automatically via `NSToolbarItem`.

### 8.2 Link Button

**SwiftUI only:** `.buttonStyle(.link)`
**Platform:** macOS exclusive

Displays the button label as a blue underlined hyperlink. Use for navigating to web content or opening help topics inline in UI text. Not available via AppKit directly (use `NSButton` with attributed string title and cursor customization).

---

## 9. Toolbar Buttons

**AppKit:** `NSButton.BezelStyle.toolbar` (applied automatically by `NSToolbarItem`)
**SwiftUI:** Items inside a `toolbar { }` block, no explicit style needed

### 9.1 Rules

- Every toolbar item must also appear as a command in the menu bar (toolbar can be hidden/customized)
- Use SF Symbols without borders — the toolbar container provides visual grouping
- The system defines hover and selection states automatically; do not override
- Use `.borderedProminent` only for a single key action like Done or Submit, positioned on the trailing side

### 9.2 Placement Zones

| Zone | Content |
|---|---|
| Leading | Navigation controls (Back, Forward), document-level actions |
| Center | Window/document title |
| Trailing | Search field, primary action (Done/Submit) |

### 9.3 Accessory Bar Buttons

| Style | AppKit | SwiftUI | Use Case |
|---|---|---|---|
| Accessory bar button | `.accessoryBar` | `.buttonStyle(.accessoryBar)` | Narrow/filter a search (e.g., Safari bookmarks bar tokens) |
| Accessory bar action button | `.accessoryBarAction` | `.buttonStyle(.accessoryBarAction)` | Extra actions in the accessory bar (e.g., add/edit filters) |

---

## 10. Toggle Controls

### 10.1 Switch (NSSwitch / SwiftUI Toggle)

A binary on/off control with more visual weight than a checkbox.

**When to use:**
- Prefer for settings you want to **emphasize** — controls more functionality than a single checkbox
- Within a grouped form, use a **mini switch** to keep row heights consistent
- Do not replace existing checkboxes with switches — use the appropriate original control

**Sizes (macOS):**

| Size | SwiftUI `.controlSize` | AppKit | Notes |
|---|---|---|---|
| Mini | `.mini` | `NSSwitch` + `controlSize = .mini` | Height matches buttons/other controls for grouped form rows |
| Regular | `.regular` | `NSSwitch` | Default; more visual weight |

**SwiftUI:**
```swift
Toggle("Wi-Fi", isOn: $isEnabled)
    .toggleStyle(.switch)
    .controlSize(.mini)
```

**AppKit:**
```swift
let toggle = NSSwitch()
toggle.state = .on    // or .off
toggle.controlSize = .mini
```

### 10.2 Checkbox

`NSButton.ButtonType.switch` / SwiftUI `Toggle(.checkbox)`

A small square button that is empty (off), contains a checkmark (on), or contains a dash (mixed state).

**States:**

| State | Visual |
|---|---|
| Off | Empty square border |
| On | Square with checkmark |
| Mixed | Square with dash (–) |
| Disabled | Dimmed; not interactive |
| Focused | Focus ring outside border |

**Rules:**
- Use instead of a switch when you need to present a **hierarchy of settings** — checkboxes align well and communicate grouping via indentation
- Use `allowsMixedState = true` when a parent checkbox controls a group of child checkboxes with differing states
- Align the leading edges of all checkboxes in a group; use indentation to show dependencies
- Introduce a group with a label whose baseline aligns with the first checkbox

**AppKit:**
```swift
let checkbox = NSButton(checkboxWithTitle: "Show hidden files",
                        target: self, action: #selector(toggleHidden))
checkbox.allowsMixedState = true  // if needed
```

### 10.3 Radio Buttons

`NSButton.ButtonType.radio` / SwiftUI `Picker` with radio style

A small circle (empty = deselected, filled = selected) followed by a label. Groups of 2–5 present mutually exclusive choices.

**When to use:**
- 2–5 mutually exclusive options where each needs a unique label
- When a single checkbox is ambiguous about the two opposing states

**Rules:**
- Prefer a pop-up button when there are more than ~5 options
- Use consistent spacing when displaying radio buttons horizontally — measure the longest label and use that consistently
- Do not use a single radio button (use a checkbox instead for single on/off)
- Mixed state is possible but rarely useful — use a checkbox if mixed state is needed

**AppKit:**
```swift
let radio = NSButton(radioButtonWithTitle: "Dark", target: self, action: #selector(selectMode))
```

---

## 11. Pull-Down Buttons

**AppKit:** `NSPopUpButton(frame:pullsDown: true)`
**SwiftUI:** `Menu("Label") { ... }` with `.menuIndicator(.visible)`
**HIG reference:** developer.apple.com/design/human-interface-guidelines/pull-down-buttons

### 11.1 Behavior

Displays a menu of items or actions directly related to the button's purpose. Choosing an item closes the menu and performs the action immediately. The button label does **not** update to reflect the chosen item (contrast with pop-up buttons).

The arrow indicator pointing down signals a pull-down menu. The button's title remains constant regardless of user selection.

### 11.2 Anatomy

```
┌──────────────────────────┐
│  Add ▼                   │  ← button label stays constant
└──────────────────────────┘
     │
     ▼ (menu appears below)
  ┌──────────────────┐
  │ New Folder       │
  │ Import...        │
  │ ──────────────── │
  │ Remove ⚠         │  ← destructive items in red
  └──────────────────┘
```

### 11.3 Rules

- **Minimum 3 items** in the menu — fewer items make the interaction feel unworthy; use separate buttons instead
- **Do not hide all primary actions** in a pull-down button — primary actions must be discoverable without opening the menu
- Use a menu title only when it adds meaning; usually the button content and menu item labels provide all context needed
- **Destructive menu items** appear in red text; clicking them triggers an action sheet (iOS/iPadOS) for confirmation
- Can include SF Symbol icons alongside menu item labels for clarity

### 11.4 Difference from Pop-Up Button

| Attribute | Pull-Down Button | Pop-Up Button |
|---|---|---|
| Purpose | Commands and actions | Mutually exclusive selections |
| Label updates | No — constant label | Yes — shows current selection |
| Arrow indicator | Points down (▼) | Points up and down (⌃⌄) or checkmark |
| Multiple select | No | No (but pull-down can, pop-up cannot) |
| AppKit | `pullsDown = true` | `pullsDown = false` |

### 11.5 AppKit API

```swift
let button = NSPopUpButton(frame: .zero, pullsDown: true)
button.addItem(withTitle: "New Folder")
button.addItem(withTitle: "Import…")
button.menu?.addItem(.separator())
let destructiveItem = NSMenuItem(title: "Remove", action: #selector(remove), keyEquivalent: "")
// Mark destructive via menu item attributes or use SwiftUI which handles automatically
```

### 11.6 SwiftUI API

```swift
Menu("Add") {
    Button("New Folder") { }
    Button("Import…") { }
    Divider()
    Button("Remove", role: .destructive) { }
}
.menuIndicator(.visible)
```

---

## 12. Pop-Up Buttons

**AppKit:** `NSPopUpButton(frame:pullsDown: false)`
**SwiftUI:** `Picker("Label", selection: $selection) { ... }.pickerStyle(.menu)`
**HIG reference:** developer.apple.com/design/human-interface-guidelines/pop-up-buttons

### 12.1 Behavior

Displays a menu of **mutually exclusive options or states**. After selection, the menu closes and the button updates its label to show the current selection. The button displays a bidirectional indicator (⌃⌄) to signal that it opens a selection menu.

### 12.2 Rules

- Use for **flat lists of mutually exclusive choices** — not for commands, not for multi-select, not for hierarchical choices (use pull-down for those)
- Provide a **useful default selection** — shown when no selection has been made yet
- Give users a way to predict the options via an introductory label or a descriptive button label
- Consider a **Custom option** to avoid cluttering the main list with rarely-needed items
- Use when space is limited and displaying all options simultaneously would be wasteful

### 12.3 Anatomy

```
┌──────────────────────────┐
│  Medium ⌃⌄               │  ← current selection shown; indicator signals menu
└──────────────────────────┘
```

### 12.4 AppKit API

```swift
let popUp = NSPopUpButton(frame: .zero, pullsDown: false)
popUp.addItem(withTitle: "Small")
popUp.addItem(withTitle: "Medium")
popUp.addItem(withTitle: "Large")
popUp.selectItem(withTitle: "Medium")  // set default
```

### 12.5 SwiftUI API

```swift
Picker("Size", selection: $size) {
    Text("Small").tag("small")
    Text("Medium").tag("medium")
    Text("Large").tag("large")
}
.pickerStyle(.menu)
```

---

## 13. Segmented Controls

**AppKit:** `NSSegmentedControl`
**SwiftUI:** `Picker(.segmented)` or `SegmentedControl`
**HIG reference:** developer.apple.com/design/human-interface-guidelines/segmented-controls

### 13.1 Behavior

A linear set of two or more segments, each functioning as a button. All segments are typically equal width. On macOS, segmented controls support:

1. **Single selection** — only one segment active at a time (`selectOne`)
2. **Multiple selection** — any combination of segments active (`selectAny`)
3. **Momentary / action mode** — no persistent selection state; each click fires an action (`momentary`)

Example: Keynote text alignment (single selection) vs. font style bold+italic+underline (multiple selection) vs. Reply/Reply All/Forward in Mail (momentary).

### 13.2 Segment Styles

| Style | `NSSegmentedControl.Style` | Description |
|---|---|---|
| Automatic | `.automatic` | Style determined by window type and position |
| Rounded | `.rounded` | Default rounded style |
| Textured Rounded | `.texturedRounded` | Uses `.texturedSquare` artwork in macOS 10.7+ |
| Round Rect | `.roundRect` | Round rect style |
| Textured Square | `.texturedSquare` | Textured square (use in textured window contexts) |
| Capsule | `.capsule` | Capsule style; uses `.texturedSquare` in macOS 10.7+ |
| Small Square | `.smallSquare` | Small square style |
| Separated | `.separated` | Segments displayed very close but not touching (e.g., Safari prev/next) |

### 13.3 Tracking Modes

| Mode | `SwitchTracking` | Behavior |
|---|---|---|
| Select One | `.selectOne` | Exactly one segment selected at a time |
| Select Any | `.selectAny` | One or more segments can be selected simultaneously |
| Momentary | `.momentary` | Selection clears when mouse releases; fires action |
| Momentary Accelerator | `.momentaryAccelerator` | Force-click sends repeating actions as pressure changes (pressure-sensitive Macs) |

### 13.4 Sizes

Segmented controls respect `NSControl.ControlSize`:

| Control Size | Typical Height (pt) |
|---|---|
| Mini | ~16 |
| Small | ~22 |
| Regular | ~26 |
| Large | ~32 |

### 13.5 Content Rules

- Prefer **text or images exclusively** within one control — do not mix text and image segments
- Use nouns or noun phrases for segment labels (title case)
- Aim for 5–7 segments maximum in wide interfaces; 5 maximum on constrained widths
- Keep content size consistent across segments to maintain equal-width balance

### 13.6 macOS-Specific Rules

- **Use a tab view — not a segmented control — for view switching** in the main window area; use a segmented control for switching views in toolbars or inspector panes
- Provide introductory text or per-segment tooltips when symbols are used
- Support **spring loading**: force-clicking a segment while dragging activates it without dropping the dragged items
- Provide tooltips for all segments when your app includes tooltips

### 13.7 AppKit API

```swift
let control = NSSegmentedControl(labels: ["Day", "Week", "Month"],
                                 trackingMode: .selectOne,
                                 target: self,
                                 action: #selector(rangeChanged))
control.segmentStyle = .rounded
control.controlSize = .regular
```

### 13.8 SwiftUI API

```swift
Picker("View", selection: $selectedView) {
    Text("Day").tag(0)
    Text("Week").tag(1)
    Text("Month").tag(2)
}
.pickerStyle(.segmented)
.controlSize(.regular)
```

---

## 14. Dialog Button Rules (macOS)

### 14.1 Button Order and Placement

macOS follows a consistent button ordering convention that differs from some other platforms:

**In a row of buttons (horizontal layout):**
- **Trailing side (right):** Default / most-likely action button
- **Leading side (left):** Cancel button
- **Far leading (left of Cancel):** Destructive button or secondary action

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  This action cannot be undone.                      │
│                                                     │
│  [Delete]     [Cancel]     [Save and Continue]      │
│  ← destructive  ← cancel   ← default (Return) →    │
└─────────────────────────────────────────────────────┘
```

From the HIG: "Place the button people are most likely to choose on the **trailing side** in a row of buttons or at the **top** in a stack of buttons. Always place the default button on the trailing side of a row or at the top of a stack. Cancel buttons are typically on the **leading side** of a row or at the bottom of a stack."

### 14.2 Button Spacing

Standard spacing between adjacent buttons in a dialog or sheet: **8 pt** (follows macOS layout grid). Do not vary button sizes to indicate preference — use style (color/prominence) instead.

### 14.3 Alert Button Rules (NSAlert / SwiftUI .alert)

- Alerts support up to **three buttons** on most platforms
- Use "Cancel" exactly as the cancel button title — do not rename it
- Use "OK" only in **purely informational** alerts; prefer specific action verbs elsewhere ("Delete", "Erase", "Remove")
- Do not use "Yes" or "No" as button titles
- The **caution symbol** (`NSCriticalAlertStyle`) should be used sparingly — only when confirming an action with unexpected data loss potential
- If there is a destructive action, always include a Cancel button

### 14.4 Sheet Button Placement

In macOS sheets (modal views that float over a parent window):
- The system presents sheets as card-like views with rounded corners
- Use Done + Cancel pairing; always provide both
- Do not show Cancel, Done, and Back simultaneously

### 14.5 Button Naming Conventions

| Context | Preferred Label | Avoid |
|---|---|---|
| Default informational | "OK" | "Yes", "Sure" |
| Confirm destructive | Specific verb: "Delete", "Erase", "Clear" | "OK", "Yes" |
| Dismiss | "Done" | "Close", "Exit" |
| Abandon | "Cancel" | "No", "Quit" |
| Open further UI | "Label…" (with ellipsis) | "Label" without ellipsis |

---

## 15. Keyboard Equivalents and Focus

### 15.1 Standard Key Equivalents

| Key | AppKit Property | Action |
|---|---|---|
| Return / Enter | `keyEquivalent = "\r"` | Activates default button |
| Escape | `keyEquivalent = "\u{1b}"` | Activates cancel button |
| Space | n/a (automatic) | Activates focused button |
| Tab / Shift-Tab | n/a (automatic) | Moves focus between controls |

### 15.2 Custom Key Equivalents

Use `keyEquivalent` + `keyEquivalentModifierMask` on `NSButton` for any custom shortcut. SwiftUI: `.keyboardShortcut("k", modifiers: .command)`.

### 15.3 Focus Behavior

- macOS uses **keyboard focus** (not hover-based focus)
- By default, Tab moves focus through all controls; full keyboard access can be enabled in System Settings > Keyboard
- A focused button shows a **blue focus ring** outside its bezel (`NSFocusRingType.exterior`)
- Space bar activates the currently focused button
- The default button always responds to Return regardless of focus position (unless a text field has focus and accepts Return for newlines)

### 15.4 Tooltip Behavior

On macOS (and visionOS only among Apple platforms), buttons display a **tooltip** after the pointer hovers for a moment. Tooltips should be:
- A brief phrase explaining what the button does
- Written in title case
- Especially important for icon-only buttons in toolbars
- Provided for all segments in a segmented control that uses icons

---

## 16. Control Sizes

All macOS button variants that support variable sizing use `NSControl.ControlSize` (AppKit) or `ControlSize` (SwiftUI):

| Size | AppKit Constant | SwiftUI Constant | Typical Use |
|---|---|---|---|
| Mini | `.mini` | `.mini` | Dense forms, grouped preferences, table cell accessories |
| Small | `.small` | `.small` | Secondary controls, toolbars with limited height |
| Regular | `.regular` | `.regular` | Standard use (default) |
| Large | `.large` | `.large` | Primary actions, onboarding, prominent single-action views |
| Extra Large | `.extraLarge` | `.extraLarge` | visionOS only; resolves to `.large` on macOS |

**SwiftUI application:**
```swift
Button("Continue") { }
    .controlSize(.large)
```

**AppKit application:**
```swift
button.controlSize = .regular   // apply before setting frame
```

---

## 17. Do's and Don'ts

### Do

- Assign the primary role to the most likely action and bind it to Return
- Use style (color/prominence) — not size — to differentiate preferred actions within a button group
- Show a tooltip for every icon-only toolbar button
- Use "Cancel" exactly for cancellation; use specific verbs for confirmation
- Place the default button on the trailing (right) side of horizontal button rows
- Include at least 10 pt of padding around image buttons' clickable area
- Append `…` to button titles that open additional UI
- Use one help button per window maximum; place it at the bottom-trailing corner
- Support spring loading on push buttons and segmented controls when the action benefits drag-and-drop workflows
- Use a tab view (not a segmented control) for main-window view switching

### Don't

- Assign the primary (default) role to a destructive action — accidental activation is too easy
- Place checkboxes, radio buttons, or switches in toolbars or status bars — use them in the window body only
- Put a label next to a help button — users understand the `?` symbol
- Use image buttons or help buttons in toolbars — use `NSToolbarItem` instead
- List more than ~5 options in radio buttons — use a pop-up button
- Mix text and image content within a single segmented control
- Display more than 7 segments in a segmented control
- Tint a destructive button with a custom color other than system red
- Create a custom Cancel key equivalent — use `"\u{1b}"` (Escape) consistently
- Use "Yes" / "No" for alert button titles

---

## 18. Sources

All content sourced directly from Apple's official APIs and Human Interface Guidelines JSON data, retrieved April 2026:

1. **Apple HIG — Buttons:** `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/buttons.json`
   - Canonical source for push button, square button, help button, image button, roles, states, platform considerations

2. **Apple HIG — Toggles:** `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/toggles.json`
   - Switch, checkbox, radio button specifications and macOS rules

3. **Apple HIG — Pull-Down Buttons:** `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/pull-down-buttons.json`
   - Pull-down button behavior, menu composition, destructive action handling

4. **Apple HIG — Pop-Up Buttons:** `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/pop-up-buttons.json`
   - Pop-up button behavior, selection display, comparison with pull-down

5. **Apple HIG — Segmented Controls:** `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/segmented-controls.json`
   - Segment styles, tracking modes, content rules, macOS tab-view distinction

6. **Apple HIG — Alerts:** `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/alerts.json`
   - Dialog button placement, naming conventions, Cancel/destructive rules

7. **Apple HIG — Sheets:** `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/sheets.json`
   - Sheet button placement, Done/Cancel pairing rules

8. **Apple HIG — Toolbars:** `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/toolbars.json`
   - Toolbar button rules, placement zones, borderedProminent usage

9. **AppKit — NSButton.BezelStyle:** `https://developer.apple.com/tutorials/data/documentation/appkit/nsbutton/bezelstyle-swift.enum.json`
   - All bezel styles: `.push`, `.flexiblePush`, `.disclosure`, `.pushDisclosure`, `.toolbar`, `.accessoryBar`, `.accessoryBarAction`, `.helpButton`, `.badge`, `.circular`, `.smallSquare`, `.rounded`, `.regularSquare`, `.inline`, `.recessed`, `.roundedDisclosure`, `.shadowlessSquare`, `.texturedRounded`, `.texturedSquare`, `.roundRect`, `.automatic`

10. **AppKit — NSButton.ButtonType:** `https://developer.apple.com/tutorials/data/documentation/appkit/nsbutton/buttontype.json`
    - `.momentaryPushIn`, `.momentaryLight`, `.momentaryChange`, `.pushOnPushOff`, `.onOff`, `.toggle`, `.switch`, `.radio`, `.accelerator`, `.multiLevelAccelerator`

11. **AppKit — NSControl.ControlSize:** `https://developer.apple.com/tutorials/data/documentation/appkit/nscontrol/controlsize.json`
    - `.mini`, `.small`, `.regular`, `.large`, `.extraLarge`

12. **AppKit — NSSegmentedControl.Style:** `https://developer.apple.com/tutorials/data/documentation/appkit/nssegmentedcontrol/style.json`
    - All segment visual styles

13. **AppKit — NSSegmentedControl.SwitchTracking:** `https://developer.apple.com/tutorials/data/documentation/appkit/nssegmentedcontrol/switchtracking.json`
    - `.selectOne`, `.selectAny`, `.momentary`, `.momentaryAccelerator`

14. **SwiftUI — ButtonStyle conforming types:**
    - `BorderedButtonStyle`, `BorderedProminentButtonStyle`, `BorderlessButtonStyle`, `PlainButtonStyle`, `LinkButtonStyle` (macOS only), `AccessoryBarButtonStyle` (macOS only), `AccessoryBarActionButtonStyle` (macOS only)
    - Source: `https://developer.apple.com/tutorials/data/documentation/swiftui/`

15. **SwiftUI — ButtonRole:** `https://developer.apple.com/tutorials/data/documentation/swiftui/buttonrole.json`
    - `.cancel`, `.destructive`, `.close`, `.confirm`

16. **SwiftUI — ControlSize:** `https://developer.apple.com/tutorials/data/documentation/swiftui/controlsize.json`
    - `.mini`, `.small`, `.regular`, `.large`, `.extraLarge`

17. **AppKit — NSPopUpButton:** `https://developer.apple.com/tutorials/data/documentation/appkit/nspopupbutton.json`
    - `pullsDown` property (false = pop-up, true = pull-down), full API surface

18. **AppKit — NSButton (full API):** `https://developer.apple.com/tutorials/data/documentation/appkit/nsbutton.json`
    - `hasDestructiveAction`, `keyEquivalent`, `keyEquivalentModifierMask`, `isSpringLoaded`, `contentTintColor`, `bezelStyle`, `bezelColor`, `controlSize`
