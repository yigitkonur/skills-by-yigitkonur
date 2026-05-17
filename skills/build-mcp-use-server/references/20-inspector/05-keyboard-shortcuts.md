# Keyboard Shortcuts

The Inspector ships keyboard shortcuts for navigation and action. Most work without a modifier; the rule is **single-letter shortcuts only fire when no input is focused**, while `Cmd/Ctrl+K` always fires.

## Reference

| Shortcut | Action | Works in input fields? |
|---|---|---|
| `Cmd/Ctrl + K` | Open command palette | Yes |
| `Cmd/Ctrl + O` | New chat session | No |
| `Esc` | Close / blur modals, overlays, focused inputs | Yes |
| `t` | Tools tab | No |
| `p` | Prompts tab | No |
| `r` | Resources tab | No |
| `c` | Chat tab | No |
| `h` | Home / Dashboard | No |
| `f` | Focus search in current tab | No |

## Detail

### `Cmd/Ctrl + K` — Command Palette

Universal entry point. Fuzzy search and execute:

- Connect to new server
- Search and execute tools (jumps to Tools tab with the tool selected)
- Open saved requests (jumps to Tools tab with arguments pre-filled)
- Switch between connected servers
- "Open in Cursor / Claude / VS Code / Gemini / Codex CLI" actions
- Doc and Discord links
- Tab navigation

See `06-command-palette.md` for the full menu.

### `Cmd/Ctrl + O` — New chat

Starts a fresh chat session in the Chat tab. Use to reset context without losing the connection.

### `Esc` — Close / blur

- Close command palette
- Close dialogs and overlays
- Blur search inputs
- Exit fullscreen widgets

### Tab navigation: `t` `p` `r` `c` `h`

Single-letter jumps. Use when reading or interacting with results — none of these fire while typing.

| Key | Tab |
|---|---|
| `t` | Tools |
| `p` | Prompts |
| `r` | Resources |
| `c` | Chat |
| `h` | Home / Dashboard |

### `f` — Focus search

Focuses the search bar of the current tab (Tools / Prompts / Resources). No effect on other tabs.

## Behavior

### Input field detection

Single-letter shortcuts are disabled while typing in:

- `<input>` text fields
- `<textarea>`
- `[contenteditable]` elements

**Exception**: `Cmd/Ctrl + K` always works, including inside inputs.

### Browser-default conflicts

The Inspector does **not** override these:

- `Cmd/Ctrl + R` (refresh)
- `Cmd/Ctrl + W` (close tab)
- `Cmd/Ctrl + T` (new tab)

## Workflows

### Tool execution

1. `Cmd/Ctrl + K`
2. Type tool name
3. `Enter` → tool selected, ready for arguments
4. Fill arguments → execute

### Saved request replay

1. `Cmd/Ctrl + K`
2. Type request name
3. `Enter` from the **Saved Requests** category
4. Tools tab loads with the saved arguments

### Server switch

1. `Cmd/Ctrl + K`
2. Type server name or URL
3. `Enter` from **Connected Servers**

### Filter long lists

1. Switch to Tools / Prompts / Resources via `t` / `p` / `r`
2. `f` to focus search
3. Type to filter
4. `Esc` to clear focus
