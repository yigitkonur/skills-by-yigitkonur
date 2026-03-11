# Selectors

How to target elements in agent-browser. Choose the right selector type for your use case.

**Related**: [commands.md](commands.md) for full command reference, [snapshots.md](snapshots.md) for snapshot details.

## Contents

- [Refs (recommended)](#refs-recommended)
- [CSS Selectors](#css-selectors)
- [Text & XPath](#text--xpath)
- [Semantic Locators](#semantic-locators)
- [When to Use Each Type](#when-to-use-each-type)
- [Best Practices](#best-practices)

## Refs (recommended)

Refs provide deterministic element selection from snapshots. Best for AI agents.

```bash
# 1. Get snapshot with refs
agent-browser snapshot
# Output:
# - heading "Example Domain" [ref=e1] [level=1]
# - button "Submit" [ref=e2]
# - textbox "Email" [ref=e3]
# - link "Learn more" [ref=e4]

# 2. Use refs to interact
agent-browser click @e2                   # Click the button
agent-browser fill @e3 "test@example.com" # Fill the textbox
agent-browser get text @e1                # Get heading text
agent-browser hover @e4                   # Hover the link
```

### Why refs?

- **Deterministic** — Ref points to exact element from snapshot
- **Fast** — No DOM re-query needed
- **AI-friendly** — LLMs can reliably parse and use refs

### Ref format

```
@e1 [tag type="value"] "text content" placeholder="hint"
│    │   │             │               │
│    │   │             │               └─ Additional attributes
│    │   │             └─ Visible text
│    │   └─ Key attributes shown
│    └─ HTML tag name / role
└─ Unique ref ID
```

### Common ref patterns

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

### Ref lifecycle

Refs are invalidated when the page changes. Always re-snapshot after navigation or DOM updates:

```bash
agent-browser click @e4      # Navigates to new page
agent-browser snapshot -i    # Get fresh refs
agent-browser click @e1      # Use new refs — @e1 is now a different element
```

## CSS Selectors

Standard CSS query syntax works for any command accepting `<sel>`:

```bash
agent-browser click "#id"
agent-browser click ".class"
agent-browser click "div > button"
agent-browser click "[data-testid='submit']"
agent-browser click "button.primary:first-child"
agent-browser get text "h1"
agent-browser get count ".item"
```

## Text & XPath

For matching by visible text or XPath expressions:

```bash
# Text selector — matches element whose visible text equals the value
agent-browser click "text=Submit"

# XPath selector — full XPath expression
agent-browser click "xpath=//button[@type='submit']"
```

## Semantic Locators

Find elements by role, label, or other semantic properties. Combine a locator with an action (`click`, `fill`, `type`, `hover`, `focus`, `check`, `uncheck`, `text`):

```bash
# By ARIA role
agent-browser find role button click --name "Submit"

# By label text
agent-browser find label "Email" fill "test@test.com"

# By placeholder
agent-browser find placeholder "Search..." fill "query"

# By alt text
agent-browser find alt "Logo" click

# By title attribute
agent-browser find title "Close" click

# By data-testid
agent-browser find testid "submit-btn" click

# By visible text
agent-browser find text "Sign In" click
agent-browser find text "Sign In" click --exact    # Exact match only

# Positional
agent-browser find first ".item" click
agent-browser find last ".item" text
agent-browser find nth 2 ".card" hover
```

Options:
- `--name <name>` — filter role by accessible name
- `--exact` — require exact text match

## When to Use Each Type

| Selector Type | Best For | Trade-offs |
|---|---|---|
| **Refs** (`@e1`) | AI agent workflows, deterministic interaction | Must snapshot first; invalidated on page change |
| **CSS** (`"#id"`, `".class"`) | Known, stable selectors; `data-testid` attributes | Brittle if DOM structure changes |
| **Text** (`"text=Submit"`) | Quick one-off clicks on labeled elements | Breaks if text changes; not unique if duplicated |
| **XPath** (`"xpath=//..."`) | Complex DOM traversal, nth-child scenarios | Verbose; fragile to structure changes |
| **Semantic** (`find role/label/...`) | Accessibility-first targeting; no snapshot needed | More verbose syntax; slower than refs |

### Decision flow

1. **AI agent automating a page?** → Use refs (`snapshot -i` → `@eN`)
2. **Known stable selector?** → Use CSS (`"[data-testid='x']"`)
3. **Need to find by visible label?** → Use semantic (`find label "Email" fill "..."`)
4. **Quick one-off action?** → Use text (`"text=Submit"`)
5. **Complex DOM navigation?** → Use XPath as last resort

## Best Practices

1. **Prefer refs for AI workflows** — snapshot first, then use `@eN`. Most token-efficient and deterministic.
2. **Re-snapshot after page changes** — refs are invalidated on navigation or significant DOM updates.
3. **Use `data-testid` for stable CSS selectors** — `"[data-testid='submit']"` survives refactors better than class/structure selectors.
4. **Quote CSS selectors** — always wrap in quotes to prevent shell interpretation: `agent-browser click "#submit"`.
5. **Prefer semantic locators over XPath** — `find role button click --name "Submit"` is clearer and more maintainable than `xpath=//button[text()='Submit']`.
6. **Use `--exact` for precise text matching** — prevents partial matches when text locators would otherwise be ambiguous.
