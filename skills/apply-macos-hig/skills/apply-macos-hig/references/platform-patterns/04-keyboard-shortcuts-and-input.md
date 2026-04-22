# macOS Keyboard Interaction Model

Complete reference for keyboard shortcuts, focus system, key equivalents, function keys, and input method handling on macOS. Every claim is sourced below.

---

## 1. System Keyboard Shortcuts Table

### 1.1 Cut, Copy, Paste, and Core Editing

| Shortcut | Action | Context | System-Reserved? |
|---|---|---|---|
| ⌘X | Cut selected item to Clipboard | Global | Yes |
| ⌘C | Copy selected item to Clipboard | Global | Yes |
| ⌘V | Paste from Clipboard | Global | Yes |
| ⌘Z | Undo previous command | Global | Yes |
| ⇧⌘Z | Redo (reverse undo) | Global | Yes |
| ⌘A | Select All | Global | Yes |
| ⌘F | Find / open Find window | Global | Yes |
| ⌘G | Find Next occurrence | Global | Yes |
| ⇧⌘G | Find Previous occurrence | Global | Yes |
| ⌘S | Save current document | Global | Yes |
| ⇧⌘S | Save As / Duplicate | Global | Yes |
| ⌘P | Print | Global | Yes |
| ⌘Q | Quit app | Global | Yes |
| ⌘W | Close front window | Global | Yes |
| ⌥⌘W | Close all windows of app | Global | Yes |
| ⌘H | Hide front app windows | Global | Yes |
| ⌥⌘H | Hide all other apps | Global | Yes |
| ⌘M | Minimize front window to Dock | Global | Yes |
| ⌥⌘M | Minimize all windows of front app | Global | Yes |
| ⌘O | Open selected item or file dialog | Global | Yes |
| ⌘N | New document or window | App | No (app-defined) |
| ⌘T | New tab | App | No (app-defined) |
| ⌘, | Open app Settings/Preferences | Global | Yes |
| ⌘? (⇧⌘/) | Open Help menu | Global | Yes |

### 1.2 Sleep, Log Out, Shut Down

| Shortcut | Action | Context |
|---|---|---|
| Power button (press) | Turn on / wake from sleep | System |
| Power button (hold 1.5s) | Sleep (built-in kbd without Touch ID) | System |
| ⌃⇧Power | Put displays to sleep (built-in kbd) | System |
| ⌃Power | Show Restart/Sleep/Shut Down dialog | System |
| ⌃⌘Power | Force restart without saving prompts | System |
| ⌃⌥⌘Power | Quit all apps, then shut down | System |
| ⌃⌘Q | Lock screen | System |
| ⇧⌘Q | Log out (with confirmation) | System |
| ⌥⇧⌘Q | Log out immediately without confirmation | System |

### 1.3 App Switching and Window Management

| Shortcut | Action | Context | System-Reserved? |
|---|---|---|---|
| ⌘Tab | Switch to next most-recently-used app | System | Yes |
| ⌘` (grave) | Switch between windows of front app | System | Yes |
| ⇧⌘` | Switch to previous window of front app | System | Yes |
| ⌥⌘` | Move focus to window drawer | System | No |
| ⌃F4 / Fn⌃F4 | Move focus to active or next window | System | Yes |
| ⌃⌘F | Toggle full screen | App | No |
| Space | Quick Look preview of selected item | Finder | No |

### 1.4 Screenshots and Screen Recording

| Shortcut | Action |
|---|---|
| ⇧⌘3 | Capture entire screen |
| ⇧⌘4 | Capture selected area |
| ⇧⌘5 | Open screenshot/recording toolbar (macOS Mojave+) |
| ⇧⌘6 | Capture Touch Bar (if present) |

### 1.5 System and Spotlight

| Shortcut | Action | System-Reserved? |
|---|---|---|
| ⌘Space | Show/hide Spotlight search | Yes |
| ⌥⌘Space | Spotlight search from Finder window | Yes |
| ⌃⌘Space / Fn-E | Show Character Viewer | Yes |
| ⌃Space | Select next input source | Yes (if multiple input sources enabled) |
| ⌃⌥Space | Select previous input source | Yes (if multiple input sources enabled) |
| Fn-D | Start/stop Dictation | Yes |
| Fn-Q | Create Quick Note | Yes |
| Fn-A | Show/hide Dock | Yes |
| Fn-C | Show/hide Control Center | Yes |
| Fn-N | Show/hide Notification Center | Yes |
| Fn-⇧A | Show/hide Apps/Launchpad (macOS Tahoe+) | Yes |

### 1.6 Finder Shortcuts

| Shortcut | Action |
|---|---|
| ⌘D | Duplicate selected files |
| ⌘E | Eject selected disk/volume |
| ⌘I | Show Get Info |
| ⌘R | Show original of selected alias; or Reload |
| ⌘N | Open new Finder window |
| ⇧⌘N | Create new folder |
| ⌃⌘N | Create new folder from selected items |
| ⌥⌘N | Create new Smart Folder |
| ⌘Delete | Move to Trash |
| ⇧⌘Delete | Empty Trash |
| ⌥⇧⌘Delete | Empty Trash without confirmation |
| ⌘1 | Icon view |
| ⌘2 | List view |
| ⌘3 | Column view |
| ⌘4 | Gallery view |
| ⌘[ | Go to previous folder |
| ⌘] | Go to next folder |
| ⌘↑ | Open enclosing folder |
| ⌃⌘↑ | Open enclosing folder in new window |
| ⌘↓ | Open selected item |
| → (list view) | Open selected folder |
| ← (list view) | Close selected folder |
| ⌘J | Show View Options |
| ⌘K | Connect to Server |
| ⌃⌘A | Make alias of selected item |
| ⌘Y | Quick Look preview |
| ⌥⌘Y | Quick Look slideshow |
| ⇧⌘C | Open Computer window |
| ⇧⌘D | Open Desktop folder |
| ⇧⌘F | Open Recents |
| ⇧⌘G | Open Go to Folder dialog |
| ⇧⌘H | Open Home folder |
| ⇧⌘I | Open iCloud Drive |
| ⇧⌘K | Open Network window |
| ⌥⌘L | Open Downloads folder |
| ⇧⌘O | Open Documents folder |
| ⇧⌘R | Open AirDrop window |
| ⇧⌘U | Open Utilities folder |
| ⌥⌘D | Show/hide Dock |
| ⌥⌘P | Hide/show path bar |
| ⌥⌘S | Hide/show Sidebar |
| ⌘/ | Hide/show status bar |
| ⌃⌘T | Add selected item to sidebar |
| ⌃⇧⌘T | Add selected Finder item to Dock |

### 1.7 Text Editing Shortcuts

| Shortcut | Action |
|---|---|
| ⌘B | Bold / toggle bold |
| ⌘I | Italic / toggle italic |
| ⌘U | Underline / toggle underline |
| ⌘K | Add web link |
| ⌘{ | Left align |
| ⌘} | Right align |
| ⇧⌘\| | Center align |
| ⇧⌘- | Decrease size of selected item |
| ⇧⌘+ (or ⌘=) | Increase size of selected item |
| ⌃⌘D | Show/hide definition of selected word |
| ⇧⌘: | Show Spelling and Grammar window |
| ⌘; | Find misspelled words |
| ⌥Delete | Delete word to left of insertion point |
| Fn-Delete | Forward delete (keyboards without Fwd Delete key) |
| ⌃D | Delete character to right of insertion point |
| ⌃H | Delete character to left of insertion point |
| ⌃K | Cut text to end of paragraph (app clipboard) |
| ⌃Y | Paste from app clipboard (from ⌃K) |
| ⌃O | Insert new line after insertion point |
| ⌃T | Transpose characters around insertion point |

### 1.8 Text Navigation (Insertion Point Movement)

| Shortcut | Action |
|---|---|
| ⌘↑ | Move to beginning of document |
| ⌘↓ | Move to end of document |
| ⌘← | Move to beginning of current line |
| ⌘→ | Move to end of current line |
| ⌥← | Move to beginning of previous word |
| ⌥→ | Move to end of next word |
| ⌥↑ | Move to beginning of current paragraph |
| ⌥↓ | Move to end of current paragraph |
| Fn↑ | Page Up: scroll up one page |
| Fn↓ | Page Down: scroll down one page |
| Fn← | Home: scroll to beginning of document |
| Fn→ | End: scroll to end of document |
| ⌃A | Move to beginning of line or paragraph |
| ⌃E | Move to end of line or paragraph |
| ⌃F | Move one character forward |
| ⌃B | Move one character backward |
| ⌃P | Move up one line |
| ⌃N | Move down one line |
| ⌃L | Center cursor or selection in visible area |

### 1.9 Text Selection Extensions

All navigation shortcuts above can be combined with ⇧ to extend the selection rather than simply move the insertion point.

| Shortcut | Action |
|---|---|
| ⇧⌘↑ | Select to beginning of document |
| ⇧⌘↓ | Select to end of document |
| ⇧⌘← | Select to beginning of current line |
| ⇧⌘→ | Select to end of current line |
| ⇧↑ | Extend selection up one line |
| ⇧↓ | Extend selection down one line |
| ⇧← | Extend selection one character left |
| ⇧→ | Extend selection one character right |
| ⌥⇧↑ | Extend selection to beginning of paragraph |
| ⌥⇧↓ | Extend selection to end of paragraph |
| ⌥⇧← | Extend selection to beginning of word |
| ⌥⇧→ | Extend selection to end of word |

### 1.10 Keyboard Focus Shortcuts (Accessibility)

| Shortcut | Action |
|---|---|
| ⌃F2 / Fn⌃F2 | Move focus to menu bar |
| ⌃F3 / Fn⌃F3 | Move focus to Dock |
| ⌃F4 / Fn⌃F4 | Move focus to active/next window |
| ⌃F5 / Fn⌃F5 | Move focus to window toolbar |
| ⌃F6 / Fn⌃F6 | Move focus to floating window |
| ⌃⇧F6 | Move focus to previous panel |
| ⌃F7 / Fn⌃F7 | Toggle Tab focus mode: all controls vs. text boxes+lists only |
| ⌃F8 / Fn⌃F8 | Move focus to status menu in menu bar |
| Tab | Move focus to next control |
| ⇧Tab | Move focus to previous control |
| ⌃Tab | Move to next control when text field is selected |
| ⌃⇧Tab | Move to previous grouping of controls |
| ↑ ↓ ← → | Move to adjacent item in list, tab group, or menu |
| ⌃↑ ⌃↓ ⌃← ⌃→ | Move to control adjacent to current text field |

### 1.11 Accessibility Vision Shortcuts

| Shortcut | Action | Must Enable First |
|---|---|---|
| ⌃⌥⌘8 | Invert colors | Yes, in Keyboard Shortcuts > Accessibility |
| ⌃⌥⌘, | Reduce contrast | Yes |
| ⌃⌥⌘. | Increase contrast | Yes |
| ⌥⌘F5 / triple Touch ID | Show Accessibility Shortcuts panel | No |

---

## 2. Modifier Keys

### 2.1 Symbols and Names

| Key Name | Symbol | Notes |
|---|---|---|
| Function / Globe | Fn / 🌐 | Present on all modern Apple keyboards |
| Control | ⌃ | Bottom-left cluster |
| Option (Alt) | ⌥ | Bottom-left cluster |
| Shift | ⇧ | Left and right sides |
| Caps Lock | ⇪ | Left side |
| Command | ⌘ | Bottom-left cluster, primary modifier |
| Escape | ⎋ | Top-left |
| Tab | ⇥ | Left side |
| Delete (Backspace) | ⌫ | Top-right area |
| Return | ⏎ | Right side |

### 2.2 Canonical Modifier Key Order

When a shortcut uses multiple modifiers, they must be listed in this exact order:

**Fn → ⌃ → ⌥ → ⇧ → ⌘**

This order mirrors the physical bottom-left keyboard cluster layout and is mandated by Apple's Style Guide and enforced by macOS menu display. System APIs expose modifier flags in this same sequence.

Examples:
- Correct: ⌃⌥⌘P (Control-Option-Command-P)
- Correct: ⌥⇧⌘V (Option-Shift-Command-V)
- Incorrect: ⌘⌥⌃ (Command listed before Option and Control)

### 2.3 Writing Conventions

| Format | When to Use | Example |
|---|---|---|
| Glyphs without hyphens | UI display (menu bar, button labels) | ⌘C, ⌥⇧⌘V |
| Hyphenated names | Prose / written documentation | Command-C, Option-Shift-Command-V |
| Always capitalize the letter key | Both glyph and prose forms | ⌘C not ⌘c; Command-C not Command-c |
| "+" and "-" shortcuts | Use the key's printed character, not Shift description | ⌘+ for Zoom In, ⌘- for Zoom Out |
| Mouse/trackpad in shortcuts | Write the gesture in lowercase | Option-click, Option-swipe with three fingers |

> Apple Style Guide explicitly deprecates the term "Command-key equivalent" — use "keyboard shortcut" instead.

---

## 3. Reserved Shortcuts (System-Reserved, Cannot Be Overridden by Apps)

The following shortcuts are controlled by macOS and cannot be reliably overridden by third-party apps. Some can be reassigned by the user in System Settings > Keyboard > Keyboard Shortcuts, but apps must not assume they are available.

### 3.1 Globally Reserved (System Takes These First)

| Shortcut | Reserved For |
|---|---|
| ⌘Space | Spotlight |
| ⌥⌘Space | Spotlight in Finder |
| ⌘Tab | App Switcher |
| ⌘` | Window switcher within app |
| ⇧⌘3 | Screenshot (full screen) |
| ⇧⌘4 | Screenshot (selection) |
| ⇧⌘5 | Screenshot/recording toolbar |
| ⌃⌘Q | Lock screen |
| ⌃⌘Space | Character Viewer |
| ⌥⌘Esc | Force Quit |
| ⌃Space | Next input source |
| ⌃⌥Space | Previous input source |
| ⌃F2 | Focus: menu bar |
| ⌃F3 | Focus: Dock |
| ⌃F4 | Focus: next window |
| ⌃F7 | Toggle Tab focus mode |
| Fn-D | Dictation |
| Fn-E | Character Viewer |

### 3.2 Standard App-Level Shortcuts Apps Must Not Reassign

Even when technically not intercepted by the system, the following are de-facto reserved by HIG convention because users expect them universally:

| Shortcut | Expected Action |
|---|---|
| ⌘C | Copy |
| ⌘V | Paste |
| ⌘X | Cut |
| ⌘Z | Undo |
| ⇧⌘Z | Redo |
| ⌘A | Select All |
| ⌘S | Save |
| ⌘Q | Quit |
| ⌘W | Close window |
| ⌘H | Hide |
| ⌘M | Minimize |
| ⌘, | Preferences/Settings |
| ⌘? | Help |
| ⌘P | Print |
| ⌘F | Find |

---

## 4. Key Equivalent Assignment Principles

### 4.1 Core Rules

1. **Command is the primary modifier.** Single-key equivalents pair the character with ⌘. Multi-modifier combos add ⌥, ⌃, or ⇧ in that order.

2. **The character is extracted ignoring modifiers.** The system compares `[NSEvent charactersIgnoringModifiers]` against the registered key equivalent — not the shifted or modified character. This means ⌘+ and ⌘= can both be registered as the same equivalent.

3. **Key equivalents must be discoverable through the UI.** Every keyboard shortcut should be visible in a menu item or button label. Hidden shortcuts break discoverability.

4. **Do not override system-reserved shortcuts.** Attempting to intercept ⌘Space, ⌘Tab, or other system shortcuts from within an app is not supported and produces undefined behavior.

5. **Prefer the Cocoa text input manager.** Call `interpretKeyEvents:` rather than manually parsing key events. This respects user-defined key bindings, dead keys, and international input methods.

6. **Expose custom shortcuts through menus.** If a shortcut is not in a menu item, use `performKeyEquivalent:` in the view hierarchy. Return `YES` only when the event has been fully handled.

7. **Use ⌃ + letter for Emacs-style text shortcuts sparingly.** Several ⌃+letter combinations (⌃A, ⌃E, ⌃F, ⌃B, etc.) are system text-navigation standards. Avoid reassigning them in text-capable views.

8. **Avoid single function keys as key equivalents.** F-keys have dual roles (system vs. standard function) depending on user settings. Prefer ⌘+letter combinations for primary actions.

### 4.2 Responder Chain and Menu Routing

```
Key event →
  NSApp checks performKeyEquivalent: on window's view hierarchy (first responder up)
    → If handled (returns YES): done
    → If not handled: NSApp forwards to menu bar
      → If menu item matches: activates action
      → If not matched: event is discarded or becomes keyDown:
```

### 4.3 Key Equivalent Priority Order

1. System (OS-level intercept, before app sees event)
2. App menu bar key equivalents
3. `performKeyEquivalent:` in view hierarchy (first responder → root)
4. `keyDown:` / `interpretKeyEvents:`

---

## 5. Focus System

### 5.1 Focus Ring Appearance

The focus ring is a visual highlight drawn around the currently focused UI control. It appears when keyboard navigation is active.

| Property | Value / Behavior |
|---|---|
| Default color | System accent color (blue by default: approximately #0067F4 in Safari/macOS) |
| Shape | Follows the control's outline; rounded for buttons, rectangular for text fields |
| Rendering | Drawn outside the control bounds using `NSFocusRingPlacement` |
| Appearance modes | `.default` (exterior ring, below content), `.above` (drawn above content) |
| NSFocusRingType | `.default` (system standard), `.exterior` (outside bounds), `.none` (suppressed) |
| Custom views | Must implement `drawFocusRingMask()`, `focusRingMaskBounds`, and `canBecomeKeyView` |
| Mask requirement | `drawFocusRingMask()` must fill with any fully opaque color — the system uses the shape, not the color |

#### NSFocusRingType Constants

| Constant | Meaning |
|---|---|
| `.default` | Use the system standard focus ring style |
| `.exterior` | Draw the ring outside the control's bounds |
| `.none` | Do not draw a focus ring (use only when you provide an alternative visual indicator) |

#### NSFocusRingPlacement Constants

| Constant | Meaning |
|---|---|
| `NSFocusRingPlacementBelow` | Focus ring drawn below the view's content |
| `NSFocusRingPlacementAbove` | Focus ring drawn above the view's content |
| `NSFocusRingPlacementOnly` | Only the focus ring is drawn, not the view's normal appearance |

### 5.2 Tab Order (Key View Loop)

The key view loop determines which control receives focus when the user presses Tab or Shift-Tab.

#### Automatic Loop (Recommended)
```swift
window.autoRecalculatesKeyViewLoop = true
```
macOS automatically calculates the loop order geometrically: left-to-right, top-to-bottom. This is the default and is preferred because it remains correct after layout changes.

#### Manual Loop
```swift
window.autoRecalculatesKeyViewLoop = false
viewA.nextKeyView = viewB
viewB.nextKeyView = viewC
viewC.nextKeyView = viewA  // loops back
```

#### Required APIs for Custom Views to Participate

| API | Purpose |
|---|---|
| `canBecomeKeyView -> Bool` | Return `true` to include view in the Tab loop |
| `acceptsFirstResponder -> Bool` | Return `true` to allow the view to become first responder |
| `nextKeyView` | Link to the next view in the loop (readable and settable) |
| `previousKeyView` | Read-only; returns the view that links to this one |
| `selectNextKeyView(_:)` | Programmatically advance focus |
| `selectPreviousKeyView(_:)` | Programmatically retreat focus |
| `focusRingMaskBounds` | Rectangle (in view's coordinate space) enclosing the focus ring area |
| `drawFocusRingMask()` | Fill the focus ring mask shape with any opaque color |

### 5.3 Full Keyboard Access Mode

**What it is:** An accessibility mode that extends keyboard navigation to all UI controls, not just text boxes and lists.

**How to enable:**
- macOS Ventura+: System Settings → Keyboard → turn on "Keyboard navigation"
- Full Keyboard Access (for all controls): System Settings → Accessibility → Motor → Keyboard → Full Keyboard Access

**Behavior difference:**
| Mode | Tab navigates to |
|---|---|
| Default | Text fields and lists only |
| Keyboard Navigation on | All interactive controls (buttons, checkboxes, dropdowns, sliders, etc.) |
| Full Keyboard Access | All controls + system panels, floating windows, Dock, menu bar |

#### Full Keyboard Access Shortcuts

| Shortcut | Action |
|---|---|
| Tab | Move to next UI element |
| ⇧Tab | Move to previous UI element |
| Space | Activate/select highlighted item |
| ↑ ↓ ← → | Move within a group (list, sidebar, etc.) |
| ⌃Tab | Jump to next item across groups |
| ⌃⇧Tab | Jump to previous item across groups |
| Fn⌃F2 | Jump to menu bar |
| Fn-A | Jump to Dock |
| Fn-C | Open Control Center |
| Fn-N | Open Notification Center |
| ⌃⌥⌘P | Toggle Pass-Through mode (temporarily disable FKA) |

#### Control Interaction in Full Keyboard Access

| Control Type | How to Interact |
|---|---|
| Text box / search field | Type directly |
| Dropdown / popup menu | ↑↓ or Space to open; ↑↓ to cycle; Space or Return to select |
| Range slider | ← → to adjust |
| Radio group | ← → or ↑ ↓ |
| Checkbox | Space to toggle |
| Stepper | ↑↓ to increase/decrease |
| Tab bar | ← → to cycle tabs |
| Icon or text button | Space to press |
| Default (full-color) button | Return to activate, regardless of which element has focus |
| Cancel button | Space (when Cancel has focus); Escape in most contexts |

---

## 6. Arrow Key Navigation Patterns

### 6.1 Lists (NSTableView)

- The entire table receives focus via Tab. Arrow keys move selection within the table.
- ↑ / ↓: Move selection to adjacent row
- Holding ⇧ while pressing ↑/↓ extends the selection to multiple rows
- Type Selection: Typing the first characters of an item's name jumps to the matching row (`typeSelectString` or equivalent in `NSTableView`)
- Home / Fn←: Move to first row
- End / Fn→: Move to last row
- Page Up / Fn↑: Scroll one page up
- Page Down / Fn↓: Scroll one page down

### 6.2 Grids (NSCollectionView)

- The entire collection receives focus via Tab
- ↑ ↓ ← →: Move selection to adjacent item in grid layout
- `allowsFocus = true` must be set on the collection view to opt into the focus system
- Items wrap at row/column boundaries based on layout

### 6.3 Outline Views (NSOutlineView)

- ↑ / ↓: Move to adjacent row
- → on collapsed row: Expand the row (show children)
- → on expanded row: Move focus to first child
- → on item with no children: No action
- ← on item with children (expanded): Collapse it
- ← on item with no children or already collapsed: Move to parent

### 6.4 Menus

- ↑ / ↓: Move between menu items
- → or Return: Open submenu or activate item
- ←: Close submenu, return to parent menu
- Escape: Close current menu level; press again to close menu bar
- Type first letter(s) of menu item name: Jump to that item in the menu
- ⌃F2 / Fn⌃F2: Open menu bar from keyboard without mouse

### 6.5 Text Fields and Text Views

| Key | Action |
|---|---|
| ← → | Move insertion point one character |
| ↑ ↓ | Move insertion point one line |
| ⌘← | Beginning of line |
| ⌘→ | End of line |
| ⌘↑ | Beginning of document |
| ⌘↓ | End of document |
| ⌥← | Beginning of previous word |
| ⌥→ | End of next word |
| ⌥↑ | Beginning of current paragraph |
| ⌥↓ | End of current paragraph |
| ⇧ + any above | Extend selection instead of moving |
| ↓ on last line | Move to end of that line |
| ↑ on first line | Move to beginning of that line |

### 6.6 Segmented Controls, Sliders, and Other Controls

| Control | Arrow Behavior |
|---|---|
| Segmented control (NSSegmentedControl) | ← → cycle through segments |
| Slider | ← → (or ↑ ↓) adjust value by one step |
| Radio group | ← → or ↑ ↓ select adjacent radio button |
| Tab bar | ← → cycle between tabs |

---

## 7. Function Keys and Special Keys

### 7.1 Default F-Key Behavior (Apple Keyboard Top Row)

By default, F-keys perform the hardware/system function printed on the key cap:

| Key | Default System Action |
|---|---|
| F1 | Decrease display brightness |
| F2 | Increase display brightness |
| F3 | Mission Control |
| F4 | Spotlight / Stage Manager (varies by macOS version) |
| F5 | Dictation |
| F6 | Do Not Disturb (Focus) |
| F7 | Media: Previous / Rewind |
| F8 | Media: Play / Pause |
| F9 | Media: Next / Fast Forward |
| F10 | Mute |
| F11 | Volume Down |
| F12 | Volume Up |

### 7.2 Using F-Keys as Standard Function Keys

**Per-press:** Hold Fn (or Globe key) while pressing the F-key to invoke the standard F1–F12 function.

**Always standard:** System Settings → Keyboard → Keyboard Shortcuts → Function Keys → "Use F1, F2, etc. keys as standard function keys". When enabled, Fn+F-key invokes the hardware action instead.

**Non-Apple keyboards:** May require a third-party utility; the Fn key behavior is manufacturer-defined.

### 7.3 Keyboard Focus F-Keys

When Keyboard Navigation or Full Keyboard Access is active, the following F-key shortcuts apply:

| Shortcut | Action |
|---|---|
| ⌃F2 / Fn⌃F2 | Focus: menu bar |
| ⌃F3 / Fn⌃F3 | Focus: Dock |
| ⌃F4 / Fn⌃F4 | Focus: active/next window |
| ⌃F5 / Fn⌃F5 | Focus: window toolbar |
| ⌃F6 / Fn⌃F6 | Focus: floating window |
| ⌃F7 / Fn⌃F7 | Toggle Tab focus mode |
| ⌃F8 / Fn⌃F8 | Focus: status menu in menu bar |

### 7.4 Escape Key Behavior Hierarchy

Escape is a hierarchical dismissal key. The system attempts to dismiss from the innermost context outward:

1. **Autocomplete / inline suggestion** — Escape cancels the suggestion and reverts to user-typed text
2. **Popover, picker, or dropdown sheet** — Escape closes it without committing
3. **Modal dialog or sheet** — Escape cancels/dismisses (equivalent to clicking Cancel); in NSAlert this sends `cancelOperation:`
4. **Find bar / search field** — Escape clears the search or closes the find bar
5. **Text field editing** — Escape in some controls reverts changes and moves focus away
6. **Menu navigation** — Escape closes the current menu level; press again to close the parent; press again to exit the menu bar entirely
7. **Full Screen mode** — Escape exits full-screen
8. **Modal loop (NSApp.runModal)** — Escape sends `stopModal` with a cancel code
9. **No modal context** — Event propagates up the responder chain and is typically discarded

---

## 8. Do's and Don'ts

### Do

- Use ⌘ as the primary modifier for app shortcuts; add ⌥, ⌃, ⇧ only when needed
- List modifier keys in the canonical order: Fn → ⌃ → ⌥ → ⇧ → ⌘ in all UI display and documentation
- Use glyphs without hyphens in menu bar and button labels; use hyphenated names in prose
- Always capitalize the letter key in both glyph and prose forms (⌘C, Command-C)
- Expose every keyboard shortcut through a visible menu item or button label
- Implement `canBecomeKeyView`, `acceptsFirstResponder`, `drawFocusRingMask()`, and `focusRingMaskBounds` in every custom focusable view
- Set `window.autoRecalculatesKeyViewLoop = true` unless there is a specific layout reason not to
- Use `interpretKeyEvents:` for text input handling, not raw `keyDown:` parsing
- Support Tab / Shift-Tab ordering that follows visual reading order (left-to-right, top-to-bottom)
- Give every interactive element a focus ring when it receives keyboard focus
- Support full keyboard access by ensuring all interactive controls can receive focus
- Provide type-to-select in any list that contains named items

### Do Not

- Override system-reserved shortcuts (⌘Space, ⌘Tab, ⇧⌘3, ⌃⌘Q, etc.)
- Use "Command-key equivalent" — the correct term is "keyboard shortcut"
- Suppress the focus ring (`NSFocusRingType.none`) without providing an alternative visual focus indicator
- Hard-code physical key characters for international input — use `interpretKeyEvents:`
- Rely on F-keys as primary shortcuts without providing a ⌘+letter fallback
- Assign shortcuts that conflict with the standard text-editing shortcuts (⌘Z, ⌘A, ⌘C, ⌘V, ⌘X, ⌘S, etc.)
- Disable Tab navigation inside a view without providing an alternative navigation mechanism
- Return `YES` from `performKeyEquivalent:` for events the view did not actually handle
- List modifiers in any order other than Fn → ⌃ → ⌥ → ⇧ → ⌘

---

## 9. Sources

| Source | URL | Date | Content Covered |
|---|---|---|---|
| Apple Support: Mac keyboard shortcuts | https://support.apple.com/en-us/102650 | March 10, 2026 | Complete system shortcut table, modifier key symbols, all categories |
| Apple Support: Function keys on Mac | https://support.apple.com/en-us/102439 | — | F-key default behavior, switching to standard function key mode |
| Apple Support: Full Keyboard Access | https://support.apple.com/en-ge/guide/mac-help/mchlc06d1059/mac | — | Full Keyboard Access shortcuts, enable/disable, Pass-Through mode |
| Apple Developer: Handling Key Events (Cocoa Event Handling Guide) | https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/EventOverview/HandlingKeyEvents/HandlingKeyEvents.html | — | Key event types, responder chain, key equivalent rules, modifier flags, key view loop APIs |
| Daring Fireball: Modifier Key Order for Keyboard Shortcuts | https://daringfireball.net/2026/03/modifier_key_order_for_keyboard_shortcuts | March 2026 | Canonical modifier order (Apple Style Guide), writing conventions, glyph vs. hyphenated forms |
| Dr. Drang / All This: Modifier key order | https://leancrew.com/all-this/2017/11/modifier-key-order/ | November 2017 | Modifier order: ⌃ ⌥ ⇧ ⌘ matches keyboard cluster layout |
| Microsoft Apple UX Guide: Keyboard Focus | https://microsoft.github.io/apple-ux-guide/KeyboardFocus.html | — | Key view loop, autoRecalculatesKeyViewLoop, NSTableView/NSCollectionView arrow key navigation |
| Zenn / usagimaru: Supporting Keyboard Navigation and Focus Rings for NSView | https://zenn.dev/usagimaru/articles/fb10c16654d030?locale=en | February 2024 | canBecomeKeyView, focusRingMaskBounds, drawFocusRingMask() implementation |
| gskinner blog: Mac Text Navigation Shortcuts | https://blog.gskinner.com/archives/2006/07/mac_text_naviga.html | 2006 (patterns unchanged) | Text navigation keyboard shortcuts, word/paragraph/line/document movement |
| tempertemper.net: Using the keyboard to navigate on macOS | https://www.tempertemper.net/blog/using-the-keyboard-to-navigate-on-macos | October 2020 | Keyboard navigation mode, control interaction patterns |
| Make Things Accessible: Focus indicators | https://www.makethingsaccessible.com/guides/the-importance-of-focus-indicators/ | June 2023 | Focus ring color specification (#0067F4 in Safari/macOS) |
| Swiftjective-C: Basic Keyboard Navigation for Collection & Tableview | https://swiftjectivec.com/Snip-Enable-Keyboard-Navigation-With-Focus-CollectionView-TableView/ | November 2022 | allowsFocus API for NSCollectionView/NSTableView |
