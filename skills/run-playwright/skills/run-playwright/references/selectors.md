# Selectors, Refs, and Element Interaction

How the ref system works, how to select elements, use accessibility-tree
snapshots, fall back to CSS selectors, and extract data in `playwright-cli`.

---

## Table of Contents

- [How refs work](#how-refs-work)
- [Snapshot anatomy](#snapshot-anatomy)
- [Ref lifecycle](#ref-lifecycle)
- [Eval for data extraction](#eval-for-data-extraction)
- [CSS selector fallback](#css-selector-fallback)
- [Accessibility-tree selectors](#accessibility-tree-selectors)
- [run-code for complex selection](#run-code-for-complex-selection)
- [Iframe content](#iframe-content)
- [Shadow DOM](#shadow-dom)
- [Selector strategies](#selector-strategies)
- [Common extraction patterns](#common-extraction-patterns)

---

## How refs work

When you run `snapshot`, the CLI traverses the current page DOM and produces
an accessibility-tree dump. Interactive elements get assigned **ref identifiers**
like `e0`, `e1`, `e5`.

> **Steering experience:** `snapshot` writes a YAML file to `.playwright-cli/page-<timestamp>.yml` and prints the file path. It does NOT print the tree to the terminal. You must `cat` the printed path to read refs. The format is YAML (role/name/ref), not HTML.

```yaml
# Example from .playwright-cli/page-<timestamp>.yml
- role: button
  name: "Submit"
  ref: e0
- role: textbox
  name: "Name"
  ref: e1
- role: link
  name: "Login"
  ref: e2
```

These refs are the primary way to target elements in CLI commands:

```bash
click e0
fill e1 "Jane Doe"
click e2
```

### Key properties of refs

| Property | Detail |
|----------|--------|
| Format | `e` + sequential number (e.g., `e0`, `e5`, `e12`) |
| Source | Generated fresh by each `snapshot` call |
| Scope | Valid only until the page state changes |
| Ordering | Sequential, prioritizing actionable/visible elements |
| Coverage | Buttons, inputs, links, selects — things you can interact with |

---

## Snapshot anatomy

### Snapshot output (YAML file)

> **Steering experience:** This is the single most important thing to understand about `snapshot`. It writes a file and prints the path. You must read the file to see the tree.

```bash
snapshot
# Output: Snapshot saved to .playwright-cli/page-1710456789.yml
cat .playwright-cli/page-1710456789.yml
```

Writes the accessibility tree to a YAML file at `.playwright-cli/page-<timestamp>.yml`
and prints the file path. Read it with `cat <path>` to see the refs (e0, e1, ...).
Use those refs immediately in subsequent commands.

### Saved snapshot (file)

```bash
snapshot --filename=page-state.md
```

Writes a markdown-style outline file. Useful for:
- comparing page states over time
- sharing page structure with other agents
- archiving state at a specific point

### What snapshots capture

- Page structure (headings, sections, forms, lists)
- Interactive elements with refs (buttons, inputs, links)
- Element roles, labels, and text content
- Approximate visual hierarchy

### What snapshots do NOT capture

- CSS styles (colors, sizes, positioning)
- Images (content or src)
- Invisible/hidden elements (by default)
- Live input values (use `eval` for those)
- Canvas or WebGL content

---

## Ref lifecycle

Refs die when page state changes meaningfully:

| Trigger | Refs invalidated? |
|---------|-------------------|
| `open` / navigation | Yes |
| `go-back` / `go-forward` | Yes |
| `reload` | Yes |
| `tab-select` | Yes — new tab has its own refs |
| `click` that triggers re-render | Often yes |
| `fill` without re-render | Usually no |
| `run-code` that mutates DOM | Assume yes |
| `select` that triggers page update | Often yes |

**Rule:** if in doubt, re-snapshot. Refs are cheap to regenerate.

```bash
click <ref>
snapshot  # Always re-snapshot after meaningful changes
```

---

## Eval for data extraction

`eval` runs JavaScript in the browser and returns the result. It is the
truth-checking tool — use it whenever command output is not enough.

### Two forms

```bash
# Page context — no element needed
eval "() => document.title"

# Element context — uses a ref
eval "(el) => el.value" <ref>
```

### Rules for eval

| Rule | Why |
|------|-----|
| Return primitives or plain objects | DOM nodes cannot be serialized |
| Use arrow functions | CLI expects a function expression |
| Keep expressions short | Long evals are hard to debug |
| Prefer `eval` over snapshot for values | Snapshots show structure, not live state |

### Common eval patterns

```bash
# Page URL
eval "() => window.location.href"

# Page title
eval "() => document.title"

# Input value
eval "(el) => el.value" <ref>

# Text content
eval "(el) => el.textContent" <ref>

# Checked state
eval "(el) => el.checked" <ref>

# Element visibility
eval "(el) => getComputedStyle(el).display !== 'none'" <ref>

# Count elements
eval "() => document.querySelectorAll('.item').length"

# Selected option value
eval "(el) => el.value" <select-ref>

# Selected option text
eval "(el) => el.options[el.selectedIndex]?.textContent.trim()" <select-ref>

# All select options
eval "(el) => [...el.options].map(o => ({ value: o.value, text: o.textContent.trim() }))" <ref>

# Uploaded filenames
eval "() => [...document.querySelector('input[type=file]').files].map(f => f.name)"

# Computed style
eval "(el) => getComputedStyle(el).color" <ref>

# Bounding box
eval "(el) => el.getBoundingClientRect()" <ref>

# Data attribute
eval "(el) => el.dataset.status" <ref>

# ARIA label
eval "(el) => el.getAttribute('aria-label')" <ref>
```

---

## CSS selector fallback

When refs are not sufficient (e.g., targeting by attribute, class, or
complex structure), use `eval` with CSS selectors:

```bash
# Find element by data-testid
eval "() => document.querySelector('[data-testid=submit-btn]')?.textContent"

# Count items matching a selector
eval "() => document.querySelectorAll('.product-card').length"

# Get all link hrefs
eval "() => [...document.querySelectorAll('a')].map(a => a.href)"

# Find element by text content
eval "() => [...document.querySelectorAll('button')].find(b => b.textContent.includes('Submit'))?.textContent"
```

### Use run-code for complex CSS selection + action

```bash
run-code 'async (page) => {
  await page.locator("[data-testid=submit]").click()
  return "clicked"
}'
snapshot
```

---

## Accessibility-tree selectors

The snapshot output is an accessibility-tree representation. Elements are
identified by their role, name, and position.

### How to read the tree

```yaml
# Example snapshot YAML for a login page
- role: heading
  name: "Welcome"
  level: 1
- role: textbox
  name: "Email"
  ref: e3
- role: textbox
  name: "Password"
  ref: e4
- role: button
  name: "Sign In"
  ref: e5
- role: link
  name: "Forgot password?"
  ref: e6
```

### Matching strategy

| What you see in snapshot | How to target it |
|--------------------------|------------------|
| `ref: e5` | `click e5` |
| `role: button, name: "Sign In"` | `click e5` (use the ref) |
| `role: textbox, name: "Email"` | `fill e3 "user@test.com"` |
| No ref shown | Use `eval` with CSS selector |

### When refs are missing

Some elements may not get refs if they are:
- Non-interactive (static text, images)
- Hidden or off-screen
- Inside iframes (unless using `--full`)
- Dynamically added after snapshot

For these, use `eval` or `run-code`.

---

## run-code for complex selection

When CLI commands cannot express the selection cleanly:

### Click by test ID

```bash
run-code 'async (page) => {
  await page.locator("[data-testid=save-button]").click()
  return "clicked"
}'
snapshot
```

### Click by text

```bash
run-code 'async (page) => {
  await page.getByText("Accept cookies").click()
  return "clicked"
}'
snapshot
```

### Click by role

```bash
run-code 'async (page) => {
  await page.getByRole("button", { name: "Submit" }).click()
  return "clicked"
}'
snapshot
```

### Quoting rule

> **Steering experience:** Quoting errors are one of the most common causes of `run-code` failures. Always use single quotes for the outer wrapper and double quotes inside JavaScript.

Single quotes outside, double quotes inside:

```bash
run-code 'async (page) => {
  await page.locator("[data-id=\"my-element\"]").click()
  return "done"
}'
```

After `run-code`, always re-snapshot.

---

## Iframe content

Snapshot does not traverse into iframes by default.

### Read iframe content

```bash
run-code 'async (page) => {
  const frame = page.frameLocator("iframe")
  const text = await frame.locator("button").first().textContent()
  return text
}'
```

### Interact inside an iframe

```bash
run-code 'async (page) => {
  const frame = page.frameLocator("iframe#payment")
  await frame.locator("input[name=card]").fill("4242424242424242")
  return "filled"
}'
snapshot
```

---

## Shadow DOM

Elements inside shadow DOM are not visible in regular snapshots.

### Access shadow DOM elements

```bash
run-code 'async (page) => {
  const host = await page.locator("my-component")
  const shadow = host.locator("button.internal")
  await shadow.click()
  return "clicked shadow button"
}'
snapshot
```

---

## Selector strategies

### Decision guide

| Situation | Strategy |
|-----------|----------|
| Element has a ref in snapshot | Use the ref directly |
| Need to verify a value | `eval "(el) => el.value" <ref>` |
| Element has no ref | `eval` with CSS selector |
| Need to interact with hidden element | `run-code` with Playwright locator |
| Element inside iframe | `run-code` with `frameLocator` |
| Element inside shadow DOM | `run-code` with nested locators |
| Need to find by text | `run-code` with `getByText` |
| Need to find by role | `run-code` with `getByRole` |

### Reliability ranking

1. **Ref from snapshot** — most aligned with CLI workflow
2. **data-testid** — stable across renders
3. **ARIA role + name** — semantic and robust
4. **Text content** — fragile if text changes
5. **CSS class/id** — fragile in component-based UIs

---

## Common extraction patterns

```bash
# List of items
eval "() => [...document.querySelectorAll('.product-name')].map(el => el.textContent.trim())"

# Table data
eval "() => [...document.querySelectorAll('table tbody tr')].map(row =>
  [...row.querySelectorAll('td')].map(td => td.textContent.trim())
)"

# All links
eval "() => [...document.querySelectorAll('a[href]')].map(a => ({ text: a.textContent.trim(), href: a.href }))"

# Form fields
eval "() => [...document.querySelectorAll('input, select, textarea')].map(el => ({
  name: el.name, type: el.type, value: el.value
}))"
```
