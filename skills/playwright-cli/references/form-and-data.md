# Form Filling and Data Extraction

## Table of Contents

- [Form Filling](#form-filling)
  - [fill vs type -- when to use each](#fill-vs-type----when-to-use-each)
  - [The --submit shortcut](#the---submit-shortcut)
  - [Form verification (critical section)](#form-verification-critical-section)
  - [Complete login workflow](#complete-login-workflow)
  - [Complete checkout verification workflow](#complete-checkout-verification-workflow)
  - [Clearing fields](#clearing-fields)
  - [Multi-field fill pattern](#multi-field-fill-pattern)
- [Data Extraction](#data-extraction)
  - [eval -- page context vs element context](#eval----page-context-vs-element-context)
  - [Common extraction patterns](#common-extraction-patterns)
  - [Don't return DOM nodes](#dont-return-dom-nodes)
  - [run-code for complex extraction](#run-code-for-complex-extraction)
- [Select Dropdowns](#select-dropdowns)
- [Checkboxes](#checkboxes)
- [File Upload](#file-upload)
- [Keyboard Input Patterns](#keyboard-input-patterns)

---

## Form Filling

### fill vs type -- when to use each

These two commands look similar but behave very differently under the hood.

**`fill <ref> "text"`** -- clears the field, then sets the value in one shot.

- Use this **95% of the time**. It is the default, correct choice for entering data into form fields.
- `fill` is instant. It sets the value property directly and dispatches `input` and `change` events.
- `fill` does **NOT** trigger individual keystroke events (`keydown`, `keypress`, `keyup`). If the application relies on keystroke events (e.g., autocomplete listeners, real-time validation on each character), `fill` will not trigger them.
- Works on `<input>`, `<textarea>`, and `[contenteditable]` elements.

**`type "text"`** -- appends characters one at a time to the currently focused element.

- Use this when you need keystroke-by-keystroke behavior: autocomplete/typeahead widgets, real-time search-as-you-type, or when the app explicitly listens for `keydown`/`keyup` on individual characters.
- `type` fires full keyboard event sequences for each character: `keydown` -> `keypress` -> `input` -> `keyup`.
- `type` does **not** clear the field first. It appends to whatever is already there.
- `type` operates on whatever element currently has focus. There is no ref argument -- you must focus the element first (e.g., `click <ref>` then `type "text"`).

**Decision rule:**

| Scenario | Use |
|---|---|
| Normal form field entry | `fill` |
| Search box with autocomplete | `type` |
| Password field | `fill` |
| Testing keystroke handlers | `type` |
| Clearing and replacing a value | `fill` |
| Appending to existing text | `type` |

### The --submit shortcut

```bash
fill <ref> "text" --submit
```

This fills the field and then immediately presses Enter. It combines two operations into one:

1. Clears and sets the value (same as `fill`).
2. Dispatches a `keydown` event for the Enter key, which triggers form submission.

**When to use it:**

- Search boxes where Enter triggers the search.
- Login forms where Enter submits credentials.
- Any single-field form where pressing Enter is the submit action.

**Why it matters:** Without `--submit`, you would need to `fill`, then `snapshot` (to get updated refs), then `click` the submit button. The `--submit` flag saves an entire snapshot-plus-click cycle, which is faster and reduces the number of steps.

```bash
# Without --submit (3 steps):
fill s1e4 "search query"
snapshot
click s2e7   # click the search button

# With --submit (1 step):
fill s1e4 "search query" --submit
```

### Form verification (critical section)

**This is the number one gotcha with forms: snapshots do NOT show form field values.**

The `snapshot` command returns the accessibility tree. The accessibility tree shows element roles, labels, and states -- but it does **not** show the `.value` property of input fields. After you `fill` a field, taking a snapshot will show the field exists, its label, and its role, but the actual text you entered will not appear.

**You must use `eval` to verify form values.** There is no other way.

**Verify text inputs and textareas:**

```bash
fill s1e4 "admin@example.com"
eval "(el) => el.value" s1e4
# Returns: "admin@example.com"
```

**Verify contenteditable elements:**

```bash
fill s1e10 "Rich text content"
eval "(el) => el.textContent" s1e10
# Returns: "Rich text content"
```

**Verify checkboxes:**

```bash
check s1e12
eval "(el) => el.checked" s1e12
# Returns: true
```

**Verify select dropdowns:**

```bash
select s1e14 "us-east-1"
eval "(el) => el.value" s1e14
# Returns: "us-east-1"
```

**Verify radio buttons:**

```bash
click s1e16
eval "(el) => el.checked" s1e16
# Returns: true
```

**Why this matters:** If you fill a field incorrectly (wrong ref, wrong value, element not interactable), `fill` will silently succeed but the value won't be set. Without `eval` verification, you won't know something went wrong until the form submission fails -- and then you'll have to debug backward through multiple steps.

### Complete login workflow

```bash
# Step 1: Navigate and take initial snapshot
open https://app.example.com/login
snapshot

# Step 2: Fill credentials
# Snapshot shows: s1e4 = email input, s1e6 = password input, s1e8 = login button
fill s1e4 "admin@example.com"
fill s1e6 "password123"

# Step 3: Verify fills before submitting
eval "(el) => el.value" s1e4
# Expected: "admin@example.com"
eval "(el) => el.value" s1e6
# Expected: "password123"

# Step 4: Submit
snapshot
click s2e8

# Step 5: Verify login succeeded
snapshot
# Look at the snapshot: does it show dashboard content?
# If it still shows the login page, check for error messages.
```

**Key points:**

- Always verify fills before submitting. A mistyped ref can silently fill the wrong field.
- After clicking submit, snapshot again to confirm navigation happened.
- If login fails, look for error message elements in the snapshot -- they often appear as `alert` or `status` roles.

### Complete checkout verification workflow

This pattern demonstrates filling a complex multi-section form, verifying every field, then submitting.

```bash
# Step 1: Navigate to checkout
open https://shop.example.com/checkout
snapshot

# Step 2: Fill shipping information
fill s1e10 "Jane Smith"           # Full name
fill s1e12 "123 Main Street"     # Address line 1
fill s1e14 "Apt 4B"              # Address line 2
fill s1e16 "New York"            # City
select s1e18 "NY"                # State dropdown
fill s1e20 "10001"               # ZIP code

# Step 3: Verify ALL shipping fields
eval "(el) => el.value" s1e10    # Expect: "Jane Smith"
eval "(el) => el.value" s1e12    # Expect: "123 Main Street"
eval "(el) => el.value" s1e14    # Expect: "Apt 4B"
eval "(el) => el.value" s1e16    # Expect: "New York"
eval "(el) => el.value" s1e18    # Expect: "NY"
eval "(el) => el.value" s1e20    # Expect: "10001"

# Step 4: Fill payment information
snapshot
fill s2e24 "4111111111111111"    # Card number
fill s2e26 "12/28"               # Expiration
fill s2e28 "123"                 # CVV

# Step 5: Verify payment fields
eval "(el) => el.value" s2e24    # Expect: "4111111111111111"
eval "(el) => el.value" s2e26    # Expect: "12/28"
eval "(el) => el.value" s2e28    # Expect: "123"

# Step 6: Check agreement checkbox and submit
check s2e30
eval "(el) => el.checked" s2e30  # Expect: true

snapshot
click s3e32                      # Place Order button

# Step 7: Verify order confirmation
snapshot
# Look for confirmation message, order number, etc.
```

### Clearing fields

To clear a field, fill it with an empty string:

```bash
fill <ref> ""
```

This sets the field's value to an empty string and dispatches the appropriate `input` and `change` events. Use this when you need to:

- Reset a field before entering a new value (though `fill` already clears before setting, so this is rarely needed).
- Test form validation for required fields -- clear a required field, then submit to trigger validation errors.
- Remove pre-filled values.

```bash
# Clear a pre-filled email field
fill s1e4 ""

# Verify it's empty
eval "(el) => el.value" s1e4
# Returns: ""
```

### Multi-field fill pattern

When filling multiple fields in a form, batch your `fill` commands together, then take a single snapshot afterward. Do not snapshot between each fill unless you need to interact with dynamic elements (like dropdowns that change the form layout).

**Efficient pattern:**

```bash
snapshot

# Fill all static fields in one batch
fill s1e4 "John"
fill s1e6 "Doe"
fill s1e8 "john.doe@example.com"
fill s1e10 "555-0100"

# One snapshot after all fills
snapshot

# Now interact with elements that may have changed
click s2e14   # Submit button
```

**When you DO need intermediate snapshots:**

- Filling a field that triggers dynamic content (e.g., selecting a country changes the state/province dropdown).
- Clicking a "Add another" button that creates new form fields.
- Interacting with autocomplete results that appear after typing.

```bash
snapshot

fill s1e4 "John"
fill s1e6 "Doe"

# Country selection changes the state dropdown options
select s1e8 "CA"
snapshot   # Need new snapshot because form structure changed

# Now the state dropdown has Canadian provinces
select s2e10 "ON"   # Ontario -- ref changed because of the re-render
```

---

## Data Extraction

### eval -- page context vs element context

The `eval` command runs JavaScript in the browser. It operates in two modes depending on whether you provide an element ref.

**Page context (no ref):**

When you omit the ref, the function receives no arguments. Use this to query the document, window, or any global state.

```bash
# Get the page title
eval "() => document.title"

# Get the current URL
eval "() => window.location.href"

# Count elements matching a selector
eval "() => document.querySelectorAll('.item').length"

# Check localStorage
eval "() => localStorage.getItem('authToken')"

# Get the full page text
eval "() => document.body.innerText"

# Read a meta tag
eval "() => document.querySelector('meta[name=\"description\"]')?.content"

# Get all cookies
eval "() => document.cookie"

# Check viewport dimensions
eval "() => ({ width: window.innerWidth, height: window.innerHeight })"
```

**Element context (with ref):**

When you provide a ref, the function receives the matching DOM element as its first argument. Use this to inspect a specific element.

```bash
# Get text content of an element
eval "(el) => el.textContent" s1e4

# Get the value of an input
eval "(el) => el.value" s1e6

# Get a link's href
eval "(el) => el.href" s1e8

# Get computed CSS properties
eval "(el) => getComputedStyle(el).color" s1e10

# Get bounding rectangle (position and size)
eval "(el) => el.getBoundingClientRect()" s1e12

# Get a data attribute
eval "(el) => el.dataset.userId" s1e14

# Get the element's outer HTML
eval "(el) => el.outerHTML" s1e16

# Check if element is disabled
eval "(el) => el.disabled" s1e18

# Get all class names
eval "(el) => [...el.classList]" s1e20

# Get an aria attribute
eval "(el) => el.getAttribute('aria-expanded')" s1e22
```

### Common extraction patterns

**Get page title:**

```bash
eval "() => document.title"
```

**Get current URL:**

```bash
eval "() => window.location.href"
```

**Count elements:**

```bash
eval "() => document.querySelectorAll('.card').length"
```

**Extract all links on the page:**

```bash
eval "() => [...document.querySelectorAll('a')].map(a => ({text: a.textContent.trim(), href: a.href}))"
```

**Check if an element exists:**

```bash
eval "() => !!document.querySelector('.error-message')"
```

**Get all table data as a 2D array:**

```bash
eval "() => [...document.querySelectorAll('tr')].map(tr => [...tr.querySelectorAll('th, td')].map(cell => cell.textContent.trim()))"
```

**Extract structured data from a list:**

```bash
eval "() => [...document.querySelectorAll('.product-card')].map(card => ({
  name: card.querySelector('.title')?.textContent?.trim(),
  price: card.querySelector('.price')?.textContent?.trim(),
  inStock: !card.querySelector('.out-of-stock')
}))"
```

**Get form validation errors:**

```bash
eval "() => [...document.querySelectorAll('.error, [role=\"alert\"]')].map(el => el.textContent.trim())"
```

**Extract selected option text from a dropdown:**

```bash
eval "(el) => el.options[el.selectedIndex]?.text" s1e14
```

**Get all input values in a form:**

```bash
eval "() => Object.fromEntries([...document.querySelectorAll('input, select, textarea')].map(el => [el.name || el.id, el.value]))"
```

### Don't return DOM nodes

`eval` serializes its return value as JSON to send it back from the browser to the CLI. DOM nodes are not JSON-serializable -- they contain circular references and host object properties that cannot be converted.

**This will fail or return empty:**

```bash
# BAD: returns a DOM element
eval "() => document.querySelector('.title')"

# BAD: returns a NodeList
eval "() => document.querySelectorAll('.item')"
```

**Extract the data you need first:**

```bash
# GOOD: return the text content
eval "() => document.querySelector('.title')?.textContent"

# GOOD: return an array of strings
eval "() => [...document.querySelectorAll('.item')].map(el => el.textContent.trim())"

# GOOD: return a plain object
eval "() => {
  const el = document.querySelector('.product');
  return { name: el?.textContent, id: el?.dataset?.id };
}"
```

**Rule of thumb:** Always return strings, numbers, booleans, arrays of primitives, or plain objects. Never return DOM elements, NodeLists, HTMLCollections, or any browser-native objects.

### run-code for complex extraction

When `eval` one-liners become unwieldy, use `run-code` for multi-step extraction logic. `run-code` gives you access to the full Playwright `page` object and supports `async/await`.

**Extract all rows from a table:**

```bash
run-code 'async (page) => {
  const rows = await page.$$eval("table tr", trs =>
    trs.map(tr => [...tr.querySelectorAll("td")].map(td => td.textContent.trim()))
  );
  return rows;
}'
```

**Scrape paginated data:**

```bash
run-code 'async (page) => {
  const allItems = [];
  while (true) {
    const items = await page.$$eval(".item", els =>
      els.map(el => ({
        title: el.querySelector(".title")?.textContent?.trim(),
        price: el.querySelector(".price")?.textContent?.trim()
      }))
    );
    allItems.push(...items);
    const nextBtn = await page.$("button.next:not([disabled])");
    if (!nextBtn) break;
    await nextBtn.click();
    await page.waitForLoadState("networkidle");
  }
  return allItems;
}'
```

**Wait for a value to appear, then extract:**

```bash
run-code 'async (page) => {
  await page.waitForSelector(".result-count");
  const count = await page.$eval(".result-count", el => el.textContent.trim());
  return count;
}'
```

**Extract data and download as JSON:**

```bash
run-code 'async (page) => {
  const data = await page.$$eval(".record", els =>
    els.map(el => ({
      id: el.dataset.id,
      name: el.querySelector(".name")?.textContent?.trim(),
      email: el.querySelector(".email")?.textContent?.trim(),
      status: el.querySelector(".status")?.textContent?.trim()
    }))
  );
  return JSON.stringify(data, null, 2);
}'
```

---

## Select Dropdowns

Use `select` to choose an option from a `<select>` element.

```bash
select <ref> "option-value"
```

The value is matched against the `value` attribute of the `<option>` elements, **not** the visible text. If you need to select by visible text, use `eval` to find the correct value first.

```bash
# Select by value attribute
select s1e14 "us-east-1"

# Verify the selection
eval "(el) => el.value" s1e14
# Returns: "us-east-1"

# Get the visible text of the selected option
eval "(el) => el.options[el.selectedIndex]?.text" s1e14
# Returns: "US East (N. Virginia)"
```

**Finding available options:**

```bash
# List all options with their values and text
eval "(el) => [...el.options].map(o => ({value: o.value, text: o.text}))" s1e14
```

**Multi-select:** Pass multiple values separated by the appropriate syntax if supported by the CLI. Otherwise, use `eval` with the element:

```bash
eval "(el) => { [...el.options].forEach(o => { o.selected = ['val1','val2'].includes(o.value) }); el.dispatchEvent(new Event('change')); }" s1e14
```

---

## Checkboxes

Use `check` and `uncheck` for checkbox elements. Both are idempotent -- calling `check` on an already-checked box does nothing, and `uncheck` on an already-unchecked box does nothing.

```bash
# Check a checkbox
check s1e12

# Uncheck a checkbox
uncheck s1e12

# Verify the state
eval "(el) => el.checked" s1e12
# Returns: true or false
```

**Important:** Do not use `click` on checkboxes unless you have a specific reason. `click` toggles the state, so if you're not sure of the current state, you might end up unchecking a box you intended to check. `check` and `uncheck` are always safe because they set the desired state regardless of the current state.

```bash
# RISKY: toggles -- might uncheck if already checked
click s1e12

# SAFE: always results in checked
check s1e12

# SAFE: always results in unchecked
uncheck s1e12
```

**For radio buttons:** There is no dedicated `check` for radios. Use `click`:

```bash
click s1e16   # Select a radio button
eval "(el) => el.checked" s1e16
# Returns: true
```

---

## File Upload

Upload a file to a file input element:

```bash
upload /path/to/file
```

The command targets the file input on the page. If there is ambiguity (multiple file inputs), use `click` on the specific file input ref first, then `upload`.

```bash
# Upload a single file
upload /Users/me/documents/report.pdf

# Upload to a specific file input when there are multiple
click s1e20    # Focus the correct file input
upload /Users/me/images/photo.jpg
```

**Important considerations:**

- The file path must be an absolute path accessible to the system running Playwright.
- For drag-and-drop upload zones that are not `<input type="file">` elements, you may need to use `run-code` with Playwright's `setInputFiles` or dispatch drag events manually.
- Some applications validate file types client-side. If the upload appears to do nothing, check for hidden error messages.

---

## Keyboard Input Patterns

Use `press` to send individual key events. These are dispatched to whatever element currently has focus.

**Navigation between fields:**

```bash
press Tab          # Move focus to next field
press Shift+Tab    # Move focus to previous field
```

**Form submission:**

```bash
press Enter        # Submit the currently focused form
```

**Closing overlays:**

```bash
press Escape       # Close dropdown, modal, or popover
```

**Autocomplete / typeahead workflow:**

```bash
# Step 1: Focus the field
click s1e4

# Step 2: Type to trigger autocomplete
type "new yor"

# Step 3: Wait for suggestions to appear
snapshot

# Step 4: Select from the dropdown
press ArrowDown    # Highlight first suggestion
press ArrowDown    # Highlight second suggestion (if needed)
press Enter        # Confirm selection

# Step 5: Verify the selected value
eval "(el) => el.value" s1e4
```

**Keyboard shortcuts:**

```bash
press Control+a    # Select all text in focused field
press Control+c    # Copy
press Control+v    # Paste
press Control+z    # Undo
press Backspace    # Delete character before cursor
press Delete       # Delete character after cursor
```

**Special keys reference:**

| Key | Usage |
|---|---|
| `Tab` | Move to next focusable element |
| `Shift+Tab` | Move to previous focusable element |
| `Enter` | Submit form or activate button |
| `Escape` | Close modal, dropdown, or cancel |
| `ArrowDown` | Navigate dropdown options |
| `ArrowUp` | Navigate dropdown options (reverse) |
| `Space` | Toggle checkbox, activate button |
| `Backspace` | Delete character before cursor |
| `Delete` | Delete character after cursor |
| `Home` | Move cursor to start of line |
| `End` | Move cursor to end of line |
| `Control+a` | Select all |
| `F2` | Some apps use this to enter edit mode |

**Combining type and press for complex input:**

```bash
# Date picker that requires specific format
click s1e8
type "03"
press /
type "15"
press /
type "2026"
press Tab    # Move to next field, triggering validation
```
