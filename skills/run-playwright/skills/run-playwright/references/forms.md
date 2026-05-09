# Forms

Use this reference for inputs, selects, checkboxes, radios, uploads, date fields, autocomplete, and form submission in `playwright-cli`.

## Core Rules

1. Snapshot before interacting with a form.
2. Verify live values with `eval`; command success alone is not proof.
3. Re-snapshot after submit, route change, modal open/close, or validation rerender.
4. Use `check` / `uncheck` for native checkboxes and radios.
5. Trigger file chooser UI before `upload`.

## Fill And Type

Use `fill` when you have a field ref and want to set a value:

```bash
playwright-cli snapshot
playwright-cli fill e3 "user@example.com"
playwright-cli eval "(el) => el.value" e3
```

Use `fill --submit` for single-field search or login flows where Enter submits:

```bash
playwright-cli fill e4 "playwright cli" --submit
playwright-cli snapshot
playwright-cli eval "() => window.location.href"
```

Use `type` when the field must receive real keystroke events:

```bash
playwright-cli click e5
playwright-cli type "new y"
playwright-cli snapshot
```

`type --submit` types into the focused element and presses Enter:

```bash
playwright-cli click e5
playwright-cli type "query" --submit
playwright-cli snapshot
```

Clear a field with an empty fill:

```bash
playwright-cli fill e3 ""
playwright-cli eval "(el) => el.value" e3
```

## Selects

Native selects use option values, not visible labels:

```bash
playwright-cli eval "(el) => [...el.options].map(o => ({ value: o.value, text: o.textContent.trim() }))" e6
playwright-cli select e6 "price-asc"
playwright-cli eval "(el) => el.value" e6
```

Custom dropdowns are click sequences:

```bash
playwright-cli click e7
playwright-cli snapshot
playwright-cli click e12
playwright-cli snapshot
```

For multi-selects or complex widgets, use `run-code`:

```bash
playwright-cli run-code "async page => {
  await page.locator('select[multiple]').selectOption(['a', 'b']);
}"
playwright-cli snapshot
```

## Checkboxes And Radios

```bash
playwright-cli check e8
playwright-cli eval "(el) => el.checked" e8

playwright-cli uncheck e8
playwright-cli eval "(el) => el.checked" e8
```

For a radio group:

```bash
playwright-cli check e10
playwright-cli eval "() => document.querySelector('input[name=plan]:checked')?.value"
```

If a toggle is a custom element instead of a native input, use `click` and verify the resulting state.

## File Upload And Drop

`upload` requires an active file chooser:

```bash
playwright-cli click e11
playwright-cli upload /absolute/path/to/file.pdf
playwright-cli eval "() => [...document.querySelector('input[type=file]').files].map(f => f.name)"
playwright-cli screenshot --filename=file-selected.png
```

Upload multiple files by passing multiple paths:

```bash
playwright-cli click e11
playwright-cli upload /absolute/path/a.png /absolute/path/b.png
```

Use `drop` for drag-and-drop upload targets:

```bash
playwright-cli drop e15 --path=/absolute/path/image.png
playwright-cli snapshot
```

Fallback for hidden file inputs:

```bash
playwright-cli run-code "async page => {
  await page.locator('input[type=file]').setInputFiles('/absolute/path/file.pdf');
}"
playwright-cli snapshot
```

## Date And Time Inputs

Native fields accept browser-standard values:

```bash
playwright-cli fill e12 "2026-12-31"
playwright-cli eval "(el) => el.value" e12

playwright-cli fill e13 "14:30"
playwright-cli eval "(el) => el.value" e13

playwright-cli fill e14 "2026-12-31T14:30"
playwright-cli eval "(el) => el.value" e14
```

Custom date pickers usually require click sequences or a targeted `run-code` fallback.

## Autocomplete

```bash
playwright-cli click e3
playwright-cli type "new y"
playwright-cli run-code "async page => {
  await page.waitForSelector('.autocomplete-dropdown', { state: 'visible' });
}"
playwright-cli snapshot
playwright-cli click e9
playwright-cli snapshot
```

## Submission Proof

```bash
playwright-cli console --clear
playwright-cli requests --clear
playwright-cli click e20
playwright-cli snapshot
playwright-cli eval "() => window.location.href"
playwright-cli requests --filter="/api/"
```

If the app does not navigate on submit, verify a state change, success message, request status, or stored value:

```bash
playwright-cli eval "() => document.querySelector('[data-status]')?.textContent"
playwright-cli eval "() => document.querySelector('form')?.checkValidity()"
```

## Troubleshooting

| Problem | Recovery |
|---|---|
| `fill` does nothing | Ref is stale; re-snapshot. |
| Value resets after fill | Framework rerendered; try `type` or dispatch events via `run-code`. |
| `select` picks nothing | Inspect option values first. |
| `upload` errors | Click the chooser trigger first and use absolute paths. |
| Checkbox does not change | It may be a custom component; click and verify UI state. |
| Submit appears idle | Clear requests, reproduce, inspect `requests`, then add a trace if needed. |
