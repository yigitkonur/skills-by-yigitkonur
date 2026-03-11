# Forms

How to fill inputs, select dropdowns, check boxes, upload files, handle date pickers,
and verify form state in `playwright-cli`.

---

## Table of Contents

- [Core form rules](#core-form-rules)
- [fill — set a field by ref](#fill--set-a-field-by-ref)
- [type — focus-driven typing](#type--focus-driven-typing)
- [select — dropdown menus](#select--dropdown-menus)
- [check and uncheck — checkboxes and radios](#check-and-uncheck--checkboxes-and-radios)
- [File upload](#file-upload)
- [Date and time inputs](#date-and-time-inputs)
- [Autocomplete and search inputs](#autocomplete-and-search-inputs)
- [Multi-step form flows](#multi-step-form-flows)
- [Form submission](#form-submission)
- [Verification patterns](#verification-patterns)
- [Troubleshooting forms](#troubleshooting-forms)

---

## Core form rules

1. **Snapshot first** — get fresh refs before interacting with any form element.
2. **Verify with eval** — do not trust command output alone; use `eval` to check live values.
3. **Refs die on re-render** — after submitting or navigating, re-snapshot before continuing.

The safe pattern:

```bash
snapshot
fill <ref> "value"
eval "(el) => el.value" <ref>
```

---

## fill — set a field by ref

```bash
fill <ref> <text>
fill <ref> <text> --submit
```

Replaces the current field value. Does not always print a fresh snapshot.

### Basic usage

```bash
fill <email-ref> "user@example.com"
eval "(el) => el.value" <email-ref>
```

### Fill and submit

```bash
fill <search-ref> "playwright testing" --submit
snapshot
eval "() => window.location.href"
```

### Clear a field

```bash
fill <ref> ""
eval "(el) => el.value" <ref>
```

### Fill multiple fields

```bash
snapshot
fill <first-name-ref> "Jane"
fill <last-name-ref> "Doe"
fill <email-ref> "jane@example.com"
eval "(el) => el.value" <email-ref>
screenshot --filename=form-filled.png
```

---

## type — focus-driven typing

```bash
type <text>
type <text> --submit
```

Targets the currently focused editable element. Simulates keystroke-by-keystroke
input, which triggers `input` and `keydown` events.

### When to use type vs fill

| Scenario | Use |
|----------|-----|
| Set a known field by ref | `fill` |
| Trigger autocomplete / search suggestions | `type` |
| Simulate real user typing behavior | `type` |
| Fill a contenteditable div | `type` (after clicking to focus) |

### Type into a focused field

```bash
click <search-ref>
type "react hooks tutorial"
snapshot
```

### Type with submission

```bash
click <search-ref>
type "playwright cli guide" --submit
snapshot
eval "() => window.location.href"
```

---

## select — dropdown menus

```bash
select <ref> <value>
```

The value must be the option's `value` attribute, not its visible label.

### Inspect options first

```bash
eval "(el) => [...el.options].map(o => ({ value: o.value, text: o.textContent.trim() }))" <ref>
```

### Select by value

```bash
select <sort-ref> "price-asc"
eval "(el) => el.value" <sort-ref>
```

### Verify selected option text

```bash
eval "(el) => el.options[el.selectedIndex]?.textContent.trim()" <ref>
```

### Multi-select (via run-code)

Native HTML multi-selects require `run-code`:

```bash
run-code 'async (page) => {
  await page.locator("select[multiple]").selectOption(["opt1", "opt2"])
  return "selected"
}'
snapshot
```

### Custom dropdown components

Many modern UIs use custom dropdowns (not native `<select>`). Handle them as
click sequences:

```bash
click <dropdown-trigger-ref>
snapshot
click <option-ref>
snapshot
```

---

## check and uncheck — checkboxes and radios

### Checkbox

```bash
check <ref>
eval "(el) => el.checked" <ref>
```

```bash
uncheck <ref>
eval "(el) => el.checked" <ref>
```

### Radio button

The `check` command works for both checkboxes and radios:

```bash
check <radio-ref>
eval "(el) => el.checked" <radio-ref>
```

Prefer `check` over `click` for radios — it is idempotent (safe to call
even if already selected).

### Verify a group of radios

```bash
eval "() => document.querySelector('input[name=plan]:checked')?.value"
```

### Toggle switches

Some toggle switches are styled checkboxes:

```bash
check <toggle-ref>
eval "(el) => el.checked" <toggle-ref>
```

If the toggle is a custom component, use `click` instead.

---

## File upload

Uploads are **modal-driven**, not ref-driven. The file chooser dialog
must be active before calling `upload`.

### Safe upload workflow

```bash
snapshot
click <upload-button-ref>
upload /absolute/path/to/file.pdf
eval "() => [...document.querySelector('input[type=file]').files].map(f => f.name)"
screenshot --filename=file-selected.png
```

### Multiple files

```bash
click <upload-button-ref>
upload /path/to/file-a.png /path/to/file-b.png
eval "() => [...document.querySelector('input[type=file]').files].map(f => f.name)"
```

### Hidden file input fallback

When the real `<input type=file>` is hidden behind a custom UI:

```bash
run-code 'async (page) => {
  await page.locator("input[type=file]").setInputFiles(["/absolute/path/to/file.pdf"])
  return "uploaded"
}'
snapshot
screenshot --filename=file-uploaded.png
```

### Upload rules

| Rule | Why |
|------|-----|
| Trigger file chooser first | `upload` only works when a chooser modal is active |
| Use absolute paths | Relative paths may resolve incorrectly |
| Files must be in allowed roots | Paths outside allowed directories are rejected |
| Verify with eval after upload | Command success alone is not proof |

---

## Date and time inputs

### Native date input

```bash
fill <date-ref> "2024-12-31"
eval "(el) => el.value" <date-ref>
```

### Native time input

```bash
fill <time-ref> "14:30"
eval "(el) => el.value" <time-ref>
```

### Native datetime-local input

```bash
fill <datetime-ref> "2024-12-31T14:30"
eval "(el) => el.value" <datetime-ref>
```

### Custom date pickers

Most custom date pickers require clicking through the calendar UI:

```bash
click <datepicker-trigger-ref>
snapshot
# Navigate to correct month if needed
click <prev-month-ref>
snapshot
click <day-15-ref>
snapshot
eval "() => document.querySelector('.date-input').value"
```

### Date picker via run-code

If the date picker is complex, set the value directly:

```bash
run-code 'async (page) => {
  const input = page.locator("input.date-field")
  await input.fill("2024-12-31")
  await input.dispatchEvent("change")
  return "date set"
}'
snapshot
```

---

## Autocomplete and search inputs

```bash
click <search-ref>
type "new y"
run-code 'async (page) => {
  await page.waitForSelector(".autocomplete-dropdown", { state: "visible" })
  return "suggestions visible"
}'
snapshot
click <suggestion-ref>
eval "(el) => el.value" <search-ref>
```

---

## Multi-step form flows

```bash
# Step 1
snapshot
fill <name-ref> "Jane Doe"
fill <email-ref> "jane@example.com"
click <next-ref>
snapshot

# Step 2
fill <address-ref> "123 Main St"
select <state-ref> "OR"
click <next-ref>
snapshot

# Step 3 — review and submit
click <submit-ref>
snapshot
eval "() => window.location.href"
screenshot --filename=confirmation.png
```

---

## Form submission

```bash
# Option 1: click submit
click <submit-ref>

# Option 2: fill with --submit
fill <search-ref> "query" --submit

# Option 3: press Enter
press Enter
```

---

## Verification patterns

```bash
eval "(el) => el.value" <ref>                    # field value
eval "(el) => el.checked" <ref>                  # checked state
eval "(el) => el.value" <select-ref>             # selected option
eval "() => document.querySelector('form').checkValidity()"
eval "() => [...document.querySelectorAll('.error')].map(e => e.textContent)"
```

---

## Troubleshooting forms

| Problem | Cause | Fix |
|---------|-------|-----|
| `fill` does nothing | Ref is stale | `snapshot` then retry with fresh ref |
| Value appears empty after `fill` | Framework resets value on re-render | Use `type` instead, or `run-code` with `dispatchEvent` |
| `select` fails silently | Used visible label instead of `value` | Inspect options with `eval` first |
| `upload` fails | No file chooser active | Click the upload trigger first |
| Upload path denied | File outside allowed roots | Move file to an allowed directory |
| Checkbox won't check | Element is a custom styled div, not an `<input>` | Use `click` instead of `check` |
| Form submits but nothing happens | SPA handling prevents navigation | Use `run-code` with `waitForResponse` |
