# Keyboard Shortcuts and Command Palette

*Read this when using keyboard shortcuts to navigate the Inspector or accessing the command palette.*

## Keyboard shortcuts

Use shortcuts to move between Inspector views without leaving the current server context.

| Shortcut | Action | Works while typing? |
| --- | --- | --- |
| `Cmd/Ctrl + K` | Open the command palette. | Yes |
| `Cmd/Ctrl + O` | Start a new chat. | No |
| `Esc` | Close overlays, dialogs, or blur the focused element. | Yes |
| `t` | Open the Tools tab. | No |
| `p` | Open the Prompts tab. | No |
| `r` | Open the Resources tab. | No |
| `c` | Open the Chat tab. | No |
| `h` | Return to the dashboard. | No |
| `f` | Focus search in the current tab (if the tab has search). | No |

**Note:** `Cmd/Ctrl + K` is the only shortcut that intentionally works while an input field is focused. Single-letter shortcuts are disabled while you type in inputs, textareas, and content-editable elements.

## Command palette

Press `Cmd/Ctrl + K` to open the command palette from anywhere in the Inspector. It searches across your current Inspector state and lets you jump directly to any item.

### What the command palette searches

- Connected servers (by display name or URL)
- Tools (by name, description, and server)
- Prompts (by name, description, and server)
- Resources (by name, URI, and server)
- Saved tool requests
- Global navigation actions
- Add to Client actions for supported clients

Search is fuzzy, so partial words work. For example, `lin iss` can match a "Linear issue tool" if that tool is connected.

### Navigate the command palette

| Key | Action |
| --- | --- |
| `Up` / `Down` | Move through results. |
| `Enter` | Open the selected result or run the selected command. |
| `Esc` | Close the palette. |

### Use the command palette to run a tool

1. Press `Cmd/Ctrl + K`.
2. Type the tool name or part of its description.
3. Select the tool.
4. Fill the generated input form.
5. Run the tool.

The Inspector opens the Tools tab with that tool selected.

### Save and load requests

Saved requests appear in their own results category in the command palette. Select one to open the matching tool with its saved arguments already loaded.

Use saved requests for repeatable calls such as regression checks, widget test cases, or long input payloads.

### Switch servers

When more than one server is connected, search by server display name or URL. Selecting a server opens that server's Inspector view.

Display names are useful here — rename saved servers in Connection Settings when several URLs are hard to scan.

### Add a server to a client

**Add to Client** commands appear when a connected server can be installed or copied into a supported client. Search for the client name and choose the matching action.

Depending on the client, the action may open a deep link, download a configuration file, or copy a command to the clipboard.
