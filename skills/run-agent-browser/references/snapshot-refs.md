# Snapshot and Refs

Compact element references that reduce context usage dramatically for AI agents.

**Related**: [commands.md](commands.md) for full command reference, [SKILL.md](../SKILL.md) for quick start.

## Contents

- [How Refs Work](#how-refs-work)
- [Snapshot Command](#the-snapshot-command)
- [Using Refs](#using-refs)
- [Ref Lifecycle](#ref-lifecycle)
- [Best Practices](#best-practices)
- [Ref Notation Details](#ref-notation-details)
- [Troubleshooting](#troubleshooting)

## How Refs Work

Traditional approach:
```
Full DOM/HTML → AI parses → CSS selector → Action (~3000-5000 tokens)
```

agent-browser approach:
```
Compact snapshot → @refs assigned → Direct interaction (~200-400 tokens)
```

## The Snapshot Command

```bash
# Basic snapshot (shows page structure)
agent-browser snapshot

# Interactive snapshot (-i flag) - RECOMMENDED
agent-browser snapshot -i
```

### Snapshot Output Format

```
Page: Example Site - Home
URL: https://example.com

@e1 [header]
  @e2 [nav]
    @e3 [a] "Home"
    @e4 [a] "Products"
    @e5 [a] "About"
  @e6 [button] "Sign In"

@e7 [main]
  @e8 [h1] "Welcome"
  @e9 [form]
    @e10 [input type="email"] placeholder="Email"
    @e11 [input type="password"] placeholder="Password"
    @e12 [button type="submit"] "Log In"

@e13 [footer]
  @e14 [a] "Privacy Policy"
```

## Using Refs

Once you have refs, interact directly:

```bash
# Click the "Sign In" button
agent-browser click @e6

# Fill email input
agent-browser fill @e10 "user@example.com"

# Fill password
agent-browser fill @e11 "password123"

# Submit the form
agent-browser click @e12
```

## Ref Lifecycle

**IMPORTANT**: Refs are invalidated when the page changes!

```bash
# Get initial snapshot
agent-browser snapshot -i
# @e1 [button] "Next"

# Click triggers page change
agent-browser click @e1

# MUST re-snapshot to get new refs!
agent-browser snapshot -i
# @e1 [h1] "Page 2"  ← Different element now!
```

## Best Practices

### 1. Always Snapshot Before Interacting

```bash
# CORRECT
agent-browser open https://example.com
agent-browser snapshot -i          # Get refs first
agent-browser click @e1            # Use ref

# WRONG
agent-browser open https://example.com
agent-browser click @e1            # Ref doesn't exist yet!
```

### 2. Re-Snapshot After Navigation

```bash
agent-browser click @e5            # Navigates to new page
agent-browser snapshot -i          # Get new refs
agent-browser click @e1            # Use new refs
```

### 3. Re-Snapshot After Dynamic Changes

```bash
agent-browser click @e1            # Opens dropdown
agent-browser snapshot -i          # See dropdown items
agent-browser click @e7            # Select item
```

### 4. Snapshot Specific Regions

For complex pages, snapshot specific areas:

```bash
# Snapshot just the form
agent-browser snapshot @e9
```

## Ref Notation Details

```
@e1 [tag type="value"] "text content" placeholder="hint"
│    │   │             │               │
│    │   │             │               └─ Additional attributes
│    │   │             └─ Visible text
│    │   └─ Key attributes shown
│    └─ HTML tag name
└─ Unique ref ID
```

### Common Patterns

```
@e1 [button] "Submit"                    # Button with text
@e2 [input type="email"]                 # Email input
@e3 [input type="password"]              # Password input
@e4 [a href="/page"] "Link Text"         # Anchor link
@e5 [select]                             # Dropdown
@e6 [textarea] placeholder="Message"     # Text area
@e7 [div class="modal"]                  # Container (when relevant)
@e8 [img alt="Logo"]                     # Image
@e9 [checkbox] checked                   # Checked checkbox
@e10 [radio] selected                    # Selected radio
```

## snapshot -i Limitations

`snapshot -i` filters out non-interactive elements to minimize token usage.

### What snapshot -i shows

| Element Type | Shown | Examples |
|---|---|---|
| Links (a) | Yes | Navigation links, clickable text |
| Buttons (button) | Yes | Submit, toggle, action buttons |
| Inputs (input) | Yes | Text fields, checkboxes, radios |
| Textareas | Yes | Multi-line text inputs |
| Selects (select) | Yes | Dropdown menus |
| Headings (h1-h6) | No | Page titles, section headers |
| Paragraphs (p) | No | Body text, descriptions |
| Spans, divs (no role) | No | Labels, badges, status text |
| Table cells (td) | No | Data cells without links |
| Images (img) | No | Unless they have alt text |

### Alternatives for data extraction

```bash
# Full accessibility tree (shows everything, but more tokens)
agent-browser snapshot

# Get specific text by CSS selector (must match exactly 1 element)
agent-browser get text "h1"

# Scoped snapshot (reduces noise on complex pages)
agent-browser snapshot -i -s "#main-content"
```

For batch multi-element extraction, use `eval --stdin` with a heredoc. See `workflows.md` section 9.

## Hidden UI Components

Some page elements only appear in the DOM after a user action. They will NOT appear in `snapshot -i` until triggered.

### Common hidden component patterns

| Pattern | Trigger | What appears |
|---|---|---|
| Dropdown menu | Click toggle button | Menu items, options |
| Modal dialog | Click button | Form fields, action buttons |
| Accordion/collapse | Click header | Body content, nested elements |
| Popover/tooltip | Hover or click trigger | Info text, action links |
| Autocomplete | Type in search field | Suggestion list items |
| Tab panel | Click tab header | Panel content |

### Discovery workflow

```bash
# 1. Snapshot shows a button but no child options
agent-browser snapshot -i
# Shows: button "Language" [ref=e5] -- Likely a dropdown trigger

# 2. Click the trigger
agent-browser click @e5
agent-browser wait 500

# 3. Re-snapshot to see revealed elements
agent-browser snapshot -i

# 4. If clicking does not work, try hover or full snapshot
agent-browser hover @e5
agent-browser wait 500
agent-browser snapshot -i
```

## JSON Output Schema

When using `snapshot -i --json`, the output follows this schema:

```json
{
  "success": true,
  "data": {
    "origin": "https://example.com",
    "refs": {
      "e1": { "name": "Submit", "role": "button" },
      "e2": { "name": "Email", "role": "textbox" }
    },
    "snapshot": "- button Submit [ref=e1]..."
  },
  "error": null
}
```

### Key paths for jq

```bash
# Get all refs
agent-browser snapshot -i --json | jq '.data.refs'

# Filter by role
agent-browser snapshot -i --json | jq '.data.refs | to_entries[] | select(.value.role == "button")'

# Get ref list with names
agent-browser snapshot -i --json | jq '[.data.refs | to_entries[] | {ref: .key, name: .value.name, role: .value.role}]'
```

**Important:** The schema is `{success, data: {origin, refs, snapshot}, error}`. There is no `.elements[]` array -- use `.data.refs`. This is the canonical schema reference.

## Agent Steering Notes

### On content-heavy pages, scope your snapshot

When `snapshot -i` returns 50+ elements, scope to reduce noise:

```bash
agent-browser snapshot -i -s "main"     # Just the main content
agent-browser snapshot -i -s "form"     # Just the form
```

### Refs from different snapshots are incompatible

Each `snapshot -i` generates fresh refs. Never mix refs from different snapshots.

### The flat ref list does not show DOM hierarchy

A link labeled "JavaScript" could be in the nav, sidebar, or content. Use scoped snapshots or `get attr @eN href` to disambiguate.

## Troubleshooting

### "Ref not found" Error

```bash
# Ref may have changed - re-snapshot
agent-browser snapshot -i
```

### Element Not Visible in Snapshot

```bash
# Scroll down to reveal element
agent-browser scroll down 1000
agent-browser snapshot -i

# Or wait for dynamic content
agent-browser wait 1000
agent-browser snapshot -i
```

### Too Many Elements

```bash
# Snapshot specific container
agent-browser snapshot @e5

# Or use get text for content-only extraction
agent-browser get text @e5
```
