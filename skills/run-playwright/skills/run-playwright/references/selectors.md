# Selectors, Refs, Eval, And Custom Code

Use this reference for `snapshot` refs, CSS/locator fallbacks, `eval`, `generate-locator`, `highlight`, iframes, shadow DOM, and `run-code`.

## Snapshot Refs

```bash
playwright-cli snapshot
```

Snapshot output includes an artifact link or returned text with roles, labels, and refs:

```yaml
- role: textbox
  name: "Email"
  ref: e3
- role: button
  name: "Sign in"
  ref: e5
```

Use refs immediately:

```bash
playwright-cli fill e3 "user@example.com"
playwright-cli click e5
```

Refs expire after navigation, tab switch, rerender, modal changes, form submit, route changes, or `run-code` that mutates DOM. Re-snapshot when unsure.

## Partial Snapshots

```bash
playwright-cli snapshot e10
playwright-cli snapshot "#main"
playwright-cli snapshot --depth=4
playwright-cli snapshot --boxes
playwright-cli snapshot --filename=after-submit.md
```

Use partial snapshots to reduce noisy pages. If `--filename` is used, read the returned file.

## Target Forms

Most interaction commands accept:

- exact refs from the latest snapshot, such as `e5`
- unique CSS selectors, such as `"#submit"`
- Playwright locators, such as `"getByRole('button', { name: 'Submit' })"`
- test id locators, such as `"getByTestId('submit-button')"`

Prefer refs when available. Use stable CSS/test IDs or locators when refs are missing or when generating test code.

## Eval

Page context:

```bash
playwright-cli eval "() => document.title"
playwright-cli eval "() => window.location.href"
playwright-cli eval "() => document.readyState"
playwright-cli eval "() => document.querySelectorAll('.item').length"
```

Element context:

```bash
playwright-cli eval "(el) => el.value" e3
playwright-cli eval "(el) => el.textContent" e5
playwright-cli eval "(el) => el.checked" e8
playwright-cli eval "(el) => el.getAttribute('data-testid')" e9
playwright-cli eval "(el) => getComputedStyle(el).display" e10
```

Return primitives or JSON-serializable objects. DOM nodes cannot be returned directly.

## Generate Locators And Highlight

Generate a Playwright locator for an element:

```bash
playwright-cli generate-locator e5
playwright-cli generate-locator "#submit"
```

Highlight elements for visual disambiguation:

```bash
playwright-cli highlight e5
playwright-cli highlight e5 --style="outline: 3px dashed red"
playwright-cli highlight e5 --hide
playwright-cli highlight --hide
```

Use `show` or screenshots after highlighting when you need visual proof.

## CSS Fallback

```bash
playwright-cli eval "() => document.querySelector('[data-testid=submit]')?.textContent"
playwright-cli eval "() => [...document.querySelectorAll('.product-card')].length"
playwright-cli eval "() => [...document.querySelectorAll('a[href]')].map(a => a.href)"
```

If CSS fallback becomes long or action-oriented, use `run-code`.

## Run Code

Use `run-code` when CLI commands cannot express a wait, locator, popup, iframe, shadow DOM, download, or complex extraction.

```bash
playwright-cli run-code "async page => {
  await page.getByRole('button', { name: 'Save' }).click();
  return await page.title();
}"
playwright-cli snapshot
```

Rules:

- Keep code short and purpose-specific.
- Return JSON-serializable results.
- Re-snapshot immediately after any DOM-changing code.
- Remove routes/listeners you create unless the next step depends on them.

## Iframes

```bash
playwright-cli run-code "async page => {
  const frame = page.frameLocator('iframe#payment');
  await frame.locator('input[name=card]').fill('4242424242424242');
  return 'filled';
}"
playwright-cli snapshot
```

## Shadow DOM

```bash
playwright-cli run-code "async page => {
  await page.locator('my-component').locator('button.internal').click();
  return 'clicked';
}"
playwright-cli snapshot
```

## Extraction Patterns

```bash
playwright-cli eval "() => [...document.querySelectorAll('.product-name')].map(el => el.textContent.trim())"

playwright-cli eval "() => [...document.querySelectorAll('table tbody tr')].map(row =>
  [...row.querySelectorAll('td')].map(td => td.textContent.trim())
)"

playwright-cli eval "() => [...document.querySelectorAll('input, select, textarea')].map(el => ({
  name: el.name,
  type: el.type,
  value: el.value
}))"
```

## Selector Priority

1. Fresh ref from `snapshot`.
2. Stable test id or semantic Playwright locator.
3. CSS selector with a clear uniqueness check.
4. `run-code` with Playwright locators for complex cases.
5. XPath only when no stable semantic or CSS selector exists.
