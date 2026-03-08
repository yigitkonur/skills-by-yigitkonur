# Forms, Inputs, Uploads, and Data Extraction

## Table of Contents

- [Core form rules](#core-form-rules)
- [fill vs type](#fill-vs-type)
- [Verification patterns](#verification-patterns)
- [Checkboxes and radios](#checkboxes-and-radios)
- [Selects](#selects)
- [File upload](#file-upload)
- [Extraction with eval](#extraction-with-eval)
- [Practical workflows](#practical-workflows)

---

## Core form rules

When working with forms in `playwright-cli`, trust the live browser state, not assumptions from the snapshot alone.
Snapshots are structural views; `eval` is the truth check when value, checked state, selected option, or uploaded filenames matter.

The safe pattern is:

```bash
snapshot
fill <ref> "value"
eval "(el) => el.value" <ref>
```

Why this matters:
- refs can go stale after page changes,
- some commands do not print a fresh snapshot automatically,
- snapshots are structural views, not guaranteed truth about live input state.

---

## fill vs type

### fill

```bash
fill <ref> "text"
fill <ref> "text" --submit
```

Use `fill` when you want to set a specific field by ref.

Observed behavior in testing:
- it replaces the field value;
- it may not print a fresh snapshot by itself;
- verifying with `eval` is the reliable pattern.

### type

```bash
type "text"
type "text" --submit
```

Use `type` only when the currently focused element is intentionally the target.
It is focus-driven, not ref-driven.

---

## Verification patterns

### Verify filled value

```bash
fill <ref> "admin@example.com"
eval "(el) => el.value" <ref>
```

### Verify text content changed

```bash
click <button-ref>
snapshot
eval "() => document.querySelector('#out').textContent"
```

### Verify URL after submit or redirect

```bash
click <submit-ref>
snapshot
eval "() => window.location.href"
```

---

## Checkboxes and radios

### Checkbox

```bash
check <ref>
eval "(el) => el.checked" <ref>

uncheck <ref>
eval "(el) => el.checked" <ref>
```

### Radio

Important correction: older repo guidance said to use `click` for radios. That was stale.

The installed CLI help documents `check` for radios, and live testing confirmed it worked.

Preferred pattern:

```bash
check <ref>
eval "(el) => el.checked" <ref>
```

If you intentionally want to simulate a user click rather than idempotent selection, `click` is still valid — but `check` is the safer default when the goal is simply “make this radio selected.”

---

## Selects

Use the option `value`, not visible label text.
Inspect the options first so you know the real value the control expects.

```bash
eval "(el) => [...el.options].map(o => ({ value: o.value, text: o.textContent.trim() }))" <ref>
select <ref> "two"
eval "(el) => el.value" <ref>
```

Real-world example from Amazon sort controls:

```bash
eval "(el) => [...el.options].map(o => ({ value: o.value, text: o.textContent.trim() }))" <sort-ref>
select <sort-ref> "review-rank"
```

---

## File upload

This repo previously documented upload incorrectly.

### What the installed CLI actually does

- `upload <ref> ...` is wrong for this installed CLI.
- `upload /absolute/path` only works when a file chooser modal is active.
- the file path must live inside an allowed root.
- success should be verified from browser state, not assumed from the command alone.

### Safe upload workflow

```bash
snapshot
click <upload-trigger-ref>
# page should now show modal state for a file chooser
upload /absolute/path/to/file
eval "() => [...document.querySelector('input[type=file]').files].map(f => f.name)"
```

### Verify uploaded files

```bash
eval "() => [...document.querySelector('input[type=file]').files].map(f => f.name)"
```

### Multiple files

```bash
upload /absolute/path/to/file-a /absolute/path/to/file-b
```

### Hidden or custom upload controls

Often the visible button triggers the chooser while the real input is hidden.
The CLI-friendly pattern is still:

```bash
click <visible-upload-trigger-ref>
upload /absolute/path/to/file
eval "() => [...document.querySelector('input[type=file]').files].map(f => f.name)"
```

If the chooser path is awkward or the input is deeply customized, fall back to `run-code`:

```bash
run-code 'async (page) => {
  await page.locator("input[type=file]").setInputFiles(["/absolute/path/to/file"])
  return "uploaded"
}'
snapshot
```

---

## Extraction with eval

Useful patterns:

### Read visible text

```bash
eval "(el) => el.textContent" <ref>
```

### Read a field value

```bash
eval "(el) => el.value" <ref>
```

### Read checked state

```bash
eval "(el) => el.checked" <ref>
```

### Read selected option text

```bash
eval "(el) => el.options[el.selectedIndex]?.textContent.trim()" <ref>
```

### Inspect all select options

```bash
eval "(el) => [...el.options].map(o => ({ value: o.value, text: o.textContent.trim() }))" <ref>
```

### Read uploaded filenames

```bash
eval "() => [...document.querySelector('input[type=file]').files].map(f => f.name)"
```

### Read layout or style data

```bash
eval "(el) => getComputedStyle(el).color" <ref>
eval "(el) => el.getBoundingClientRect()" <ref>
```

---

## Practical workflows

### Login flow

```bash
open https://app.example.com/login
snapshot
fill <email-ref> "admin@example.com"
eval "(el) => el.value" <email-ref>
fill <password-ref> "password123"
eval "(el) => el.value" <password-ref>
click <submit-ref>
snapshot
eval "() => window.location.href"
screenshot --filename=login-after-submit.png
```

### Search form flow

```bash
open "https://www.amazon.com/s?k=fidget+spinner"
snapshot
fill <searchbox-ref> "fidget spinner" --submit
snapshot
eval "() => window.location.href"
```

### Checkbox or radio selection

```bash
check <ref>
eval "(el) => el.checked" <ref>
```

### Select menu / sorting flow

```bash
eval "(el) => [...el.options].map(o => ({ value: o.value, text: o.textContent.trim() }))" <ref>
select <ref> "review-rank"
snapshot
eval "(el) => el.value" <ref>
```

### Upload flow

```bash
snapshot
click <upload-trigger-ref>
upload /absolute/path/to/file
eval "() => [...document.querySelector('input[type=file]').files].map(f => f.name)"
screenshot --filename=upload-selected.png
```
