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
