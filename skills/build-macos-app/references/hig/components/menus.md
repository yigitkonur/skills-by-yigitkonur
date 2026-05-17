# macOS Menu System — Definitive HIG Reference

> **Scope:** macOS only. Every standard menu with required items. Complete keyboard shortcut table.
> **Sources:** Apple Support (March 2026), Apple HIG, Apple legacy HIG (Mac OS 8 ellipsis rules), Bjango menu bar extras, AppCoda, Electron GitHub issue (SF Symbol specs for menus).

---

## 1. Menu Bar Structure

The macOS menu bar is persistent, screen-edge, shared across all apps. Menus belong to the frontmost app.

**Zones (left to right):**

| Zone | Contents |
|---|---|
| Apple menu | System-level commands (always present) |
| App menu | Named after running app, bold (required) |
| Standard menus | File, Edit, View, Format, Window, Help (fixed order) |
| App-specific menus | Between View and Window |
| Menu bar extras (right) | Status items, clock, Control Center |

---

## 2. Standard Menu Contents

### App Menu (bold app name)

| Item | Shortcut | Notes |
|---|---|---|
| About [AppName] | — | No ellipsis (no input needed) |
| Settings... (macOS 13+) / Preferences... | Cmd-, | Renamed in Ventura |
| Services | — | System-populated submenu |
| Hide [AppName] | Cmd-H | |
| Hide Others | Opt-Cmd-H | |
| Show All | — | |
| Quit [AppName] | Cmd-Q | |

### File Menu

| Item | Shortcut | Notes |
|---|---|---|
| New | Cmd-N | |
| Open... | Cmd-O | Ellipsis: dialog follows |
| Open Recent | — | Submenu with Clear Menu |
| Close | Cmd-W | Opt-Cmd-W = Close All |
| Save | Cmd-S | |
| Duplicate | — | Option changes to Save As... |
| Page Setup... | Shift-Cmd-P | |
| Print... | Cmd-P | |

### Edit Menu

| Item | Shortcut |
|---|---|
| Undo [action] | Cmd-Z |
| Redo [action] | Shift-Cmd-Z |
| Cut | Cmd-X |
| Copy | Cmd-C |
| Paste | Cmd-V |
| Paste and Match Style | Opt-Shift-Cmd-V |
| Select All | Cmd-A |
| Find... | Cmd-F |
| Find Next | Cmd-G |
| Find Previous | Shift-Cmd-G |
| Use Selection for Find | Cmd-E |
| Jump to Selection | Cmd-J |
| Emoji & Symbols | Ctrl-Cmd-Space |

### View Menu

| Item | Shortcut |
|---|---|
| Show/Hide Toolbar | Opt-Cmd-T |
| Show/Hide Sidebar | Ctrl-Cmd-S |
| Enter/Exit Full Screen | Ctrl-Cmd-F |

### Format Menu (text/document apps)

| Item | Shortcut |
|---|---|
| Show Fonts | Cmd-T |
| Bold | Cmd-B |
| Italic | Cmd-I |
| Underline | Cmd-U |
| Bigger | Cmd-+ |
| Smaller | Cmd-- |

### Window Menu

| Item | Shortcut |
|---|---|
| Minimize | Cmd-M |
| Minimize All | Opt-Cmd-M |
| Zoom | — |
| Tile Left | Ctrl-Cmd-Left |
| Tile Right | Ctrl-Cmd-Right |
| Bring All to Front | — |

### Help Menu

Always contains a **search field** at top (system-provided, cannot be removed). Cmd-? opens and focuses it. Searches both help content AND menu items with animated arrow highlighting.

---

## 3. Contextual (Right-Click) Menus

- Only actions relevant to the clicked object
- Most frequent items first; destructive last
- Disable rather than hide unavailable items
- Maximum ~15 items; use submenus sparingly (1 level max)
- Title case for all items

### Standard Patterns

| Object | Typical items |
|---|---|
| Text selection | Cut, Copy, Paste, Look Up, Translate, Share |
| File in Finder | Open, Open With, Get Info, Rename, Move to Trash, Share |
| Link | Open Link, Copy Link, Share |

---

## 4. Dock Menus

**System items (always present):** Window list, Options submenu, Show All Windows, Hide, Quit.

**Custom items** via `applicationDockMenu(_:)` — 3-5 max, only actions useful when app isn't frontmost.

---

## 5. Menu Bar Extras (Status Items)

| Attribute | Specification |
|---|---|
| Menu bar height | **24 pt** (Big Sur+) |
| Working area per extra | **22 pt** (fixed) |
| Recommended icon size | **16 x 16 pt** |
| Max icon height | **22 pt** |

Use template images (`isTemplate = true`) for automatic light/dark adaptation. For menu-bar-only apps: `LSUIElement = YES` in Info.plist.

---

## 6. Menu Item Types

| Type | Visual | API |
|---|---|---|
| Action | Text + optional icon + optional shortcut | `NSMenuItem(title:action:keyEquivalent:)` |
| Toggle/Checkbox | Checkmark when `.on`, dash when `.mixed` | `menuItem.state = .on/.off/.mixed` |
| Submenu | Title + triangle arrow | `menuItem.submenu = NSMenu(...)` |
| Separator | Thin horizontal line (~11pt) | `NSMenuItem.separator()` |

### Specs

| Element | Value |
|---|---|
| Standard item height | ~22 pt |
| Separator height | ~11 pt |
| Item font | System font ~13 pt Regular |
| Icon area | 16 x 16 pt |
| SF Symbol specs for menu icons | **13 pt, Semibold, Small scale, Monochrome** |

---

## 7. Menu Design Rules

### Naming
- **Title case** for all items
- **Ellipsis (Option-;)** only when further input is required (Open..., Save As...) — NOT for About, Get Info, Quit
- **Verbs** for actions: Open, Save, Delete
- **Toggle titles** describe action to take: "Show Toolbar" when hidden, "Hide Toolbar" when visible

### Keyboard Shortcuts
- Cmd alone = primary action
- Shift-Cmd = variant/reverse
- Opt-Cmd = extended/"all" variant
- Ctrl-Cmd = system-level
- Don't override reserved: Cmd-Q, Cmd-H, Cmd-,, Cmd-Tab, Cmd-Space

### Modifier Glyph Order (canonical)
**Fn -> Ctrl -> Opt -> Shift -> Cmd**

### Separators
- Group logically related items
- Never at top/bottom of menu
- Never two adjacent separators
- Groups should have 2+ items

---

## 8. Do's and Don'ts

### Do
- Include all expected items in standard menus
- Use "Settings" not "Preferences" on macOS 13+
- Dynamically update toggle titles (Show/Hide)
- Include action name in Undo/Redo ("Undo Typing")
- Disable unavailable items (don't hide them)
- Use SF Symbols at 13pt Semibold Small Monochrome for icons
- Use template images for status bar items

### Don't
- Don't use three periods (...) instead of ellipsis (...)
- Don't use ellipsis on items that execute immediately
- Don't nest submenus more than 2 levels
- Don't override system-reserved shortcuts
- Don't remove the Help menu search field
- Don't mix full-color and template images in same menu

---

## 9. Sources

1. Apple Support — Mac keyboard shortcuts (March 2026)
2. Apple Support — Keyboard symbols in menus
3. Apple HIG — Menus, The menu bar, Context menus, Dock menus
4. Apple HIG (legacy Mac OS 8) — Ellipsis rules
5. Bjango — Designing macOS menu bar extras (dimension source)
6. AppCoda — macOS Programming: Menus and Toolbar
7. 8th Light — Menu Bar Extra tutorial
8. Electron GitHub Issue #48909 — SF Symbol specs for menu items

---

## 10. NSMenu Delegate Lifecycle

| Method | Called when | Modify items? |
|---|---|---|
| `menuNeedsUpdate(_:)` | Before display | Yes — rebuild freely |
| `numberOfItems(in:)` + `menu(_:update:at:shouldCancel:)` | Before display (lazy, per-item) | Yes — update each item |
| `menuWillOpen(_:)` | After sizing, before display | No — state only |
| `menu(_:willHighlight:)` | Cursor moves to new item | No |
| `menuDidClose(_:)` | After dismissal | No |
| `menuHasKeyEquivalent(_:for:target:action:)` | Key-down, before population | No |

**Lifecycle order:** `menuNeedsUpdate` → `menuWillOpen` → tracking → `menuDidClose`

Use `menuNeedsUpdate` for fast rebuilds. Use `numberOfItems`+`update` pair for large menus (supports cancellation via `shouldCancel`).

## 11. Menu Item Validation

`NSMenu.autoenablesItems = true` (default). For each item, AppKit walks the responder chain to find a target responding to the item's `action`, then calls `validateMenuItem(_:)`.

```swift
func validateMenuItem(_ menuItem: NSMenuItem) -> Bool {
    switch menuItem.action {
    case #selector(copy(_:)):  return hasSelection
    case #selector(paste(_:)): return NSPasteboard.general.canReadItem(
        withDataConformingToTypes: [UTType.plainText.identifier])
    case #selector(toggleWordWrap(_:)):
        menuItem.state = isWordWrapEnabled ? .on : .off
        return true
    default: return responds(to: menuItem.action!)
    }
}
```

Use `validateUserInterfaceItem(_:)` for logic shared between toolbar items and menu items.

## 12. Dynamic Menu Construction

| Strategy | When | Method |
|---|---|---|
| Full rebuild | Fast, changing item count | `menuNeedsUpdate(_:)` — `removeAllItems()` + rebuild |
| Lazy per-item | Large data, cancellable | `numberOfItems(in:)` + `menu(_:update:at:shouldCancel:)` |
| State update only | Static structure, dynamic state | `menuWillOpen(_:)` — update titles/enabled/state |

Never do I/O in delegate callbacks. Use `representedObject` to bind data to items.

## 13. Services Menu Implementation

**Consuming:** Implement `NSServicesMenuRequestor` — `writeSelection(to:types:)` and `readSelection(from:)`.

**Providing:** Add `NSServices` array to Info.plist:
- `NSMenuItem` — menu title
- `NSMessage` — method name (without `:userData:error:`)
- `NSPortName` — app name
- `NSSendTypes` / `NSReturnTypes` — UTI strings

Handler signature: `methodName(_:userData:error:)`. Register with `NSApp.servicesProvider = self`. Force rescan: `NSUpdateDynamicServices()`.

## 14. Toggle State Management

| State | Constant | Visual |
|---|---|---|
| `.on` | 1 | Checkmark (✓) |
| `.off` | 0 | No indicator |
| `.mixed` | -1 | Dash (–) |

**Dynamic titles** must describe the action to take: "Hide Toolbar" when visible, "Show Toolbar" when hidden. Update in `validateMenuItem(_:)`, not in action handlers.

## 15. Format Menu — Complete Structure

```
Format
├── Font [submenu]
│   ├── Show Fonts      Cmd-T    → orderFrontFontPanel
│   ├── Bold            Cmd-B    → addFontTrait
│   ├── Italic          Cmd-I    → addFontTrait
│   ├── Underline       Cmd-U    → underline
│   ├── Bigger          Cmd-+    → modifyFont
│   ├── Smaller         Cmd--    → modifyFont
│   ├── Kern [submenu] (Default/None/Tighten/Loosen)
│   ├── Ligature [submenu] (Default/None/All)
│   ├── Baseline [submenu] (Default/Super/Sub/Raise/Lower)
│   └── Show Colors   Shift-Cmd-C → orderFrontColorPanel
├── Text [submenu]
│   ├── Align Left      Cmd-{    → alignLeft
│   ├── Center          Cmd-|    → alignCenter
│   ├── Justify                  → alignJustified
│   ├── Align Right     Cmd-}    → alignRight
│   ├── Writing Direction [submenu]
│   └── Show Ruler               → toggleRuler
└── Substitutions [submenu]
    ├── Smart Copy/Paste, Smart Quotes, Smart Dashes
    ├── Smart Links, Data Detectors, Text Replacement
    └── Show Substitutions
```

`NSFontManager.shared` coordinates Font panel, Font menu, and first responder. `NSTextView` responds to all standard selectors automatically.

**Sources:** Apple Developer Documentation (NSMenuDelegate, NSMenuItemValidation, NSServicesMenuRequestor, NSFontManager, NSTextView), Apple Archive (Application Menus, System Services).
