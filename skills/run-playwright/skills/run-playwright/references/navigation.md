# Navigation

Use this reference for opening pages, navigating existing sessions, handling redirects, waiting for SPAs, and verifying URLs in `playwright-cli`.

## Core Commands

```bash
playwright-cli open https://example.com
playwright-cli open https://example.com --headed
playwright-cli goto https://example.com/account
playwright-cli reload
playwright-cli go-back
playwright-cli go-forward
```

Use `open [url]` to create or configure a browser session. Use `goto <url>` when the session is already open and you only need to navigate the current page.

After any navigation command:

```bash
playwright-cli snapshot
playwright-cli eval "() => window.location.href"
```

## Quoting URLs

Quote URLs containing shell-sensitive characters:

```bash
playwright-cli goto "https://example.com/search?q=test&page=2"
playwright-cli goto "https://example.com/docs#section-3"
```

Verify the final URL with `eval`; redirects and shell quoting mistakes can make command echoes misleading.

## Headed Or Headless

The CLI runs headless by default.

Use headed mode for:

- live observation
- UI review
- 2FA/CAPTCHA handoff
- debugging where a human needs to see the page

```bash
playwright-cli open https://example.com --headed
```

Use default/headless mode for routine automated verification. Put stable mode choices in config/env only when repeated runs need the same behavior.

## Browser And Profile Options

```bash
playwright-cli open --browser=chrome https://example.com
playwright-cli open --browser=firefox https://example.com
playwright-cli open --device="iPhone 15" https://example.com
playwright-cli open --viewport-size=1280x720 https://example.com
playwright-cli open --persistent https://example.com
playwright-cli open --profile=./profile-dir https://example.com
playwright-cli --config .playwright/cli.config.json open https://example.com
```

Prefer command-line options for one-off runs. Use config files or environment variables for repeated, stable automation.

## Local Targets

Local URLs are valid if the browser can reach them:

```bash
playwright-cli open http://127.0.0.1:3000
playwright-cli open "file:///absolute/path/fixture.html"
```

If a local target fails:

1. Confirm the server is running or the file URL is absolute.
2. Use `eval "() => window.location.href"` and `snapshot` to see where the browser landed.
3. For tiny fixtures, use a `data:` URL.
4. For browser contexts that cannot reach local services, use a reachable staging or tunnel URL.

## Waiting For SPAs

Snapshots show current state; they do not wait for every app-specific condition. Use `run-code` for precise waits:

```bash
playwright-cli run-code "async page => {
  await page.waitForSelector('[data-testid=app-loaded]', { state: 'visible', timeout: 10000 });
}"
playwright-cli snapshot
```

Wait for URL changes:

```bash
playwright-cli run-code "async page => {
  await page.waitForURL('**/dashboard**');
  return page.url();
}"
playwright-cli snapshot
```

Wait for an API response:

```bash
playwright-cli run-code "async page => {
  const response = await page.waitForResponse(r => r.url().includes('/api/data'));
  return { url: response.url(), status: response.status() };
}"
```

## Redirects

```bash
playwright-cli goto https://example.com/old-path
playwright-cli eval "() => window.location.href"
playwright-cli snapshot
```

For auth redirects, verify both the login URL and the post-login target:

```bash
playwright-cli goto https://app.example.com/dashboard
playwright-cli eval "() => window.location.href"
playwright-cli snapshot
# complete login
playwright-cli eval "() => window.location.href"
```

## Tabs And New Pages

```bash
playwright-cli tab-list
playwright-cli tab-new https://example.com/docs
playwright-cli tab-select 0
playwright-cli tab-close 1
```

`tab-new [url]` is supported in current help and was smoke-tested against a `data:` URL. If a pinned older package opens `about:blank`, recover with:

```bash
playwright-cli tab-new
playwright-cli goto https://example.com/docs
```

## Scroll And Lazy Content

```bash
playwright-cli mousewheel 0 100
playwright-cli eval "() => window.scrollY"
playwright-cli mousewheel 0 900
playwright-cli snapshot
```

If the page scrolls the wrong axis in a pinned older version, try swapping arguments and verify again with `window.scrollY`.

## Navigation Health Check

```bash
playwright-cli goto https://example.com
playwright-cli snapshot
playwright-cli eval "() => window.location.href"
playwright-cli eval "() => document.title"
playwright-cli eval "() => document.readyState"
playwright-cli console error
playwright-cli requests
playwright-cli screenshot --filename=health-check.png
```
