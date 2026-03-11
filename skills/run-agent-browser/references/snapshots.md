# Snapshots

The `snapshot` command returns a compact accessibility tree with refs for element interaction. This is the primary way AI agents discover and interact with page elements.

**Related**: [selectors.md](selectors.md) for all selector types, [commands.md](commands.md) for full command reference.

## Contents

- [Snapshot Command](#snapshot-command)
- [Options](#options)
- [Cursor-Interactive Elements](#cursor-interactive-elements)
- [Output Format](#output-format)
- [Using Refs from Snapshots](#using-refs-from-snapshots)
- [Ref Lifecycle](#ref-lifecycle)
- [Annotated Screenshots](#annotated-screenshots)
- [JSON Output](#json-output)
- [Best Practices](#best-practices)

## Snapshot Command

```bash
agent-browser snapshot                      # Full accessibility tree
agent-browser snapshot -i                   # Interactive elements only (recommended)
agent-browser snapshot -i -C                # Include cursor-interactive elements
agent-browser snapshot -c                   # Compact (remove empty elements)
agent-browser snapshot -d 3                 # Limit depth to 3 levels
agent-browser snapshot -s "#main"           # Scope to CSS selector
agent-browser snapshot -i -c -d 5           # Combine options
```

## Options

| Option | Alias | Description |
|---|---|---|
| `-i` | `--interactive` | Only interactive elements (buttons, links, inputs) |
| `-C` | `--cursor` | Include cursor-interactive elements (cursor:pointer, onclick, tabindex) |
| `-c` | `--compact` | Remove empty structural elements |
| `-d` | `--depth <n>` | Limit tree depth to `n` levels |
| `-s` | `--selector <css>` | Scope snapshot to a CSS selector |
| `--json` | — | Produce JSON output instead of text |

## Cursor-Interactive Elements

Many modern web apps use custom clickable elements (divs, spans) instead of standard buttons or links. The `-C` flag detects these by looking for:

- `cursor: pointer` CSS style
- `onclick` attribute or handler
- `tabindex` attribute (keyboard focusable)

```bash
agent-browser snapshot -i -C
# Output includes:
# @e1 [button] "Submit"
# @e2 [link] "Learn more"
# Cursor-interactive elements:
# @e3 [clickable] "Menu Item" [cursor:pointer, onclick]
# @e4 [clickable] "Card" [cursor:pointer]
```

Use `-C` when standard `-i` misses clickable elements on SPAs or custom component libraries.

## Output Format

The default text output is compact and AI-friendly (~200–400 tokens vs ~3000–5000 for raw DOM):

```
agent-browser snapshot -i
# Output:
# @e1 [heading] "Example Domain" [level=1]
# @e2 [button] "Submit"
# @e3 [input type="email"] placeholder="Email"
# @e4 [link] "Learn more"
```

Each line contains:

```
@e1 [tag type="value"] "text content" placeholder="hint"
│    │   │             │               │
│    │   │             │               └─ Additional attributes
│    │   │             └─ Visible text
│    │   └─ Key attributes shown
│    └─ HTML tag name / role
└─ Unique ref ID
```

Full snapshot (without `-i`) includes structural elements like headers, navs, mains, footers with nested hierarchy:

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

## Using Refs from Snapshots

Refs from the snapshot map directly to commands:

```bash
# After snapshot shows @e2 [button] "Submit", @e3 [input type="email"]
agent-browser click @e2              # Click the Submit button
agent-browser fill @e3 "a@b.com"     # Fill the email input
agent-browser get text @e1           # Get heading text
agent-browser hover @e4              # Hover the link
```

### Workflow pattern

```bash
# 1. Navigate
agent-browser open https://example.com

# 2. Snapshot to discover elements
agent-browser snapshot -i

# 3. Interact using refs
agent-browser fill @e3 "user@example.com"
agent-browser fill @e4 "password123"
agent-browser click @e5
```

## Ref Lifecycle

**Refs are invalidated when the page changes.** Always re-snapshot after:

- Navigation (clicking a link, form submission, `open` command)
- Significant DOM updates (SPA route change, modal open/close, dynamic content load)

```bash
agent-browser snapshot -i
# @e1 [button] "Next"

agent-browser click @e1        # Triggers page change

# MUST re-snapshot — old refs are invalid
agent-browser snapshot -i
# @e1 [h1] "Page 2"           # @e1 is now a different element!
```

### Common mistakes

```bash
# WRONG — using refs without snapshot
agent-browser open https://example.com
agent-browser click @e1              # Ref doesn't exist yet!

# CORRECT
agent-browser open https://example.com
agent-browser snapshot -i            # Get refs first
agent-browser click @e1              # Now ref is valid

# WRONG — reusing stale refs after navigation
agent-browser click @e5              # Navigates to new page
agent-browser click @e3              # Stale ref — may fail or hit wrong element

# CORRECT
agent-browser click @e5              # Navigates to new page
agent-browser snapshot -i            # Get fresh refs
agent-browser click @e3              # New ref for new page
```

## Annotated Screenshots

For visual context alongside text snapshots, use `screenshot --annotate` to overlay numbered labels on interactive elements. Each label `[N]` maps to ref `@eN`:

```bash
agent-browser screenshot --annotate ./page.png
# -> Screenshot saved to ./page.png
#    [1] @e1 button "Submit"
#    [2] @e2 link "Home"
#    [3] @e3 textbox "Email"
agent-browser click @e2
```

Annotated screenshots also cache refs, so you can interact with elements immediately. This is useful when:

- The text snapshot is insufficient (unlabeled icons, canvas content)
- You need visual layout verification
- You want to combine visual + structural understanding

## JSON Output

For programmatic parsing in scripts:

```bash
agent-browser snapshot --json
# {"success":true,"data":{"snapshot":"...","refs":{"e1":{"role":"heading","name":"Title"},...}}}
```

JSON uses more tokens than text output. The default text format is preferred for AI agents.

## Best Practices

1. **Use `-i` to reduce output** — filters to actionable interactive elements only, dramatically reducing token usage.
2. **Re-snapshot after page changes** — refs are invalidated on navigation or significant DOM updates. Always snapshot again.
3. **Scope with `-s` for specific sections** — on complex pages, `snapshot -s "#main"` reduces noise from headers/footers.
4. **Use `-d` to limit depth** — on deeply nested pages, `-d 3` or `-d 5` keeps output manageable.
5. **Use `-C` for modern SPAs** — custom clickable divs/spans won't appear with `-i` alone; add `-C` to detect cursor-interactive elements.
6. **Combine options** — `snapshot -i -c -d 5` gives compact, interactive-only output with limited depth.
7. **Use `screenshot --annotate` for visual context** — when text snapshots aren't enough (icons, canvas, visual layout).
8. **Prefer text output over JSON for AI** — text format uses fewer tokens and is easier for LLMs to parse.
9. **Snapshot specific containers** — `snapshot -s "@e9"` to zoom into a form or region when the full page is too large.
