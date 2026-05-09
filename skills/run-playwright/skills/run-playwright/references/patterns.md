# Common Automation Patterns

Use this reference for login, storage/authentication, downloads, network mocks, extraction, and end-to-end verification patterns in `playwright-cli`.

## Table Of Contents

- [Login](#login)
- [Session And Auth Persistence](#session-and-auth-persistence)
- [Cookies And Storage](#cookies-and-storage)
- [Downloads](#downloads)
- [Search And Filter](#search-and-filter)
- [Data Extraction](#data-extraction)
- [Network Mocks](#network-mocks)
- [E2E Verification Levels](#e2e-verification-levels)

## Login

```bash
playwright-cli open https://app.example.com/login
playwright-cli snapshot
playwright-cli fill e3 "user@example.com"
playwright-cli fill e5 "password"
playwright-cli requests --clear
playwright-cli click e7
playwright-cli snapshot
playwright-cli eval "() => window.location.href"
playwright-cli screenshot --filename=after-login.png
```

Always verify the final URL or an authenticated UI marker. Some SPAs fail login without navigating.

For OAuth popups, use `run-code` to capture the popup atomically, then re-enter the normal CLI loop:

```bash
playwright-cli run-code "async page => {
  const [popup] = await Promise.all([
    page.waitForEvent('popup'),
    page.locator('button.oauth-google').click()
  ]);
  await popup.waitForLoadState();
  return { title: await popup.title(), url: popup.url() };
}"
playwright-cli snapshot
playwright-cli eval "() => window.location.href"
```

## Session And Auth Persistence

Default sessions keep cookies/storage in memory between CLI calls and lose them when the browser closes.

Use named sessions for live reuse:

```bash
playwright-cli -s=auth open https://app.example.com/login
playwright-cli -s=auth snapshot
# complete login
playwright-cli -s=auth goto https://app.example.com/dashboard
playwright-cli -s=auth eval "() => window.location.href"
```

Set one default session for a shell/agent process:

```bash
export PLAYWRIGHT_CLI_SESSION=auth
playwright-cli snapshot
```

Use persistent profiles for disk-backed reuse:

```bash
playwright-cli -s=auth open https://app.example.com --persistent
playwright-cli -s=auth open https://app.example.com --profile=./profiles/auth
```

Use storage state files for portable auth:

```bash
# After login
playwright-cli state-save auth-state.json

# Later or in another session
playwright-cli state-load auth-state.json
playwright-cli goto https://app.example.com/dashboard
```

Never commit state files containing cookies or tokens.

## Cookies And Storage

```bash
playwright-cli cookie-list
playwright-cli cookie-list --domain=.example.com
playwright-cli cookie-get session_id
playwright-cli cookie-set theme light
playwright-cli cookie-set session abc123 --domain=.example.com --secure --http-only
playwright-cli cookie-delete session_id
playwright-cli cookie-clear
```

```bash
playwright-cli localstorage-list
playwright-cli localstorage-get theme
playwright-cli localstorage-set theme dark
playwright-cli localstorage-delete theme
playwright-cli localstorage-clear
```

```bash
playwright-cli sessionstorage-list
playwright-cli sessionstorage-get step
playwright-cli sessionstorage-set step 3
playwright-cli sessionstorage-delete step
playwright-cli sessionstorage-clear
```

For IndexedDB or multi-item mutations, use `run-code`:

```bash
playwright-cli run-code "async page => {
  await page.evaluate(() => {
    localStorage.setItem('theme', 'dark');
    sessionStorage.setItem('step', '3');
  });
}"
playwright-cli snapshot
```

## Downloads

The CLI does not expose a dedicated download command. Use `run-code`, then verify the file from the shell:

```bash
playwright-cli run-code "async page => {
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.locator('a.download-link').click()
  ]);
  const filename = download.suggestedFilename();
  await download.saveAs('./' + filename);
  return { filename, url: download.url() };
}"
ls -l ./downloaded-file-name
```

Keep downloaded files out of git unless the user explicitly asked for them as deliverables.

## Search And Filter

```bash
playwright-cli fill e3 "react hooks" --submit
playwright-cli snapshot
playwright-cli eval "() => window.location.href"

playwright-cli click e8
playwright-cli snapshot

playwright-cli eval "(el) => [...el.options].map(o => ({ value: o.value, text: o.textContent.trim() }))" e10
playwright-cli select e10 "price-low-to-high"
playwright-cli snapshot
playwright-cli eval "() => document.querySelectorAll('.result-item').length"
```

## Data Extraction

Use `eval` for small extraction:

```bash
playwright-cli eval "() => [...document.querySelectorAll('.product-title')].map(el => el.textContent.trim())"
playwright-cli eval "() => [...document.querySelectorAll('a[href]')].map(a => ({ text: a.textContent.trim(), href: a.href })).filter(a => a.text)"
```

Use `run-code` for pagination, async waits, or multi-step collection, then return JSON-serializable results.

## Network Mocks

```bash
playwright-cli route "**/api/users" --body='[{"id":1,"name":"Mock"}]' --content-type=application/json
playwright-cli route-list
playwright-cli reload
playwright-cli snapshot
playwright-cli unroute "**/api/users"
```

Test error handling:

```bash
playwright-cli route "**/api/data" --status=503
playwright-cli reload
playwright-cli snapshot
playwright-cli screenshot --filename=api-error-state.png
playwright-cli unroute "**/api/data"
```

## E2E Verification Levels

| Level | Evidence | Use |
|---|---|---|
| 1 - Existence | `open`/`goto`, `snapshot`, URL/title check | Page presence |
| 2 - Behavior | Level 1 plus interaction and `eval` state proof | Forms, filters, buttons |
| 3 - Visual | Level 2 plus screenshots/PDF/video | Layout and user-visible changes |
| 4 - Diagnosis | Level 3 plus console, requests, route state, or trace | Regressions and flaky flows |
| 5 - Test-debug | Attach to `--debug=cli`, step/resume, inspect failing point | Playwright test failures |

Final answers should name the level reached and return artifact paths.
