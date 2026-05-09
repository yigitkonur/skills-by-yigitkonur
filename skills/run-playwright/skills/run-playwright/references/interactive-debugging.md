# Interactive Test Debugging

Use this reference when the task involves `npx playwright test --debug=cli`, attaching `playwright-cli` to a paused test, stepping through execution, inspecting locators, or using the dashboard.

## Start A CLI Debug Test

Run the failing test with Playwright's CLI debugger:

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test --debug=cli
```

For a specific test file:

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test tests/checkout.spec.ts --debug=cli
```

Keep the test process running. It pauses and prints a session name.

## Attach To The Paused Browser

```bash
playwright-cli attach <session-name>
playwright-cli snapshot
playwright-cli eval "() => document.title"
playwright-cli console error
```

If the debug output says a named session such as `tw-abcdef`, use that exact name:

```bash
playwright-cli attach tw-abcdef
```

## Control Test Execution

```bash
playwright-cli pause-at tests/checkout.spec.ts:42
playwright-cli resume
playwright-cli step-over
```

Use `pause-at` before the suspected failing step when possible. Use `step-over` to inspect one Playwright action at a time.

## Inspect And Generate Locators

```bash
playwright-cli snapshot
playwright-cli highlight e5
playwright-cli generate-locator e5
playwright-cli highlight --hide
```

Use generated locators as evidence for test fixes, not as a blind copy-paste. Prefer semantic locators when multiple choices are available.

## Dashboard

```bash
playwright-cli show
playwright-cli show --annotate
```

Use `show` for live observation or human takeover. Use `show --annotate` when the user needs to mark UI regions or give design/debug feedback.

Dashboard options:

```bash
playwright-cli show --port=0
playwright-cli show --host=localhost --port=9323
playwright-cli show --kill
```

## Trace While Debugging

```bash
playwright-cli tracing-start
playwright-cli resume
playwright-cli snapshot
playwright-cli step-over
playwright-cli tracing-stop
```

Open the returned trace:

```bash
npx playwright show-trace <trace.zip>
```

## Evidence To Return

After an interactive debug session, report:

- test command used
- session name attached
- pause location or step sequence
- current URL/title and relevant snapshot findings
- console/request findings
- generated locator(s), if any
- trace/screenshot paths, if captured
- whether the test process was stopped or left running intentionally

## Cleanup

Stop the background `npx playwright test --debug=cli` process after debugging unless the caller explicitly wants it left paused. Do not delete browser data unless it is a scratch session you created for this task.
