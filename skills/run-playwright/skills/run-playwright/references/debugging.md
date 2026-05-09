# Debugging And Diagnostics

Use this reference when diagnosing browser failures with console output, request logs, routing, traces, or truth checks in `playwright-cli`.

## Table Of Contents

- [Output Semantics](#output-semantics)
- [Console](#console)
- [Requests](#requests)
- [Network Routing And Mocking](#network-routing-and-mocking)
- [Tracing](#tracing)
- [Truth Checks With eval](#truth-checks-with-eval)
- [Diagnosis Workflow](#diagnosis-workflow)
- [Troubleshooting](#troubleshooting)

## Output Semantics

Current `@playwright/cli` commands may print inline data, a Markdown link to an artifact, or a filesystem path depending on command, config, and output mode.

Rule:

1. Inspect the command output first.
2. If it contains a path or Markdown artifact link, read that artifact before making a claim.
3. If docs and installed help disagree, prefer `playwright-cli --help <command>`.

Snapshots and traces commonly return artifact links. Response bodies may print inline for text and save binary bodies to a file. Do not assume every debug command is file-only.

## Console

```bash
playwright-cli console
playwright-cli console error
playwright-cli console warning
playwright-cli console --clear
```

Capture errors around one action:

```bash
playwright-cli console --clear
playwright-cli click e5
playwright-cli snapshot
playwright-cli console error
```

`console --clear` may produce little or no output. Treat that as normal and continue to the capture command.

Console noise from public sites is common. Tie bug claims to the flow you reproduced, not to unrelated telemetry, GPU, hydration, or analytics noise.

## Requests

Executable help for `@playwright/cli@0.1.13` exposes `requests`, not `network`.

```bash
playwright-cli requests
playwright-cli requests --filter="/api/.*user"
playwright-cli requests --static
playwright-cli requests --clear
```

Inspect a request listed by `requests`:

```bash
playwright-cli request 3
playwright-cli request-headers 3
playwright-cli request-body 3
playwright-cli response-headers 3
playwright-cli response-body 3
```

Use `requests --clear` before reproducing a failure, then inspect the new entries:

```bash
playwright-cli requests --clear
playwright-cli click e7
playwright-cli requests --filter="/api/"
playwright-cli request 0
```

Version drift note: some official docs still show `network` and `network --clear`. In the verified package, `playwright-cli --help network` falls back to the global help because `network` is not an executable command. Use `requests`.

## Network Routing And Mocking

Use CLI route commands for simple mocks:

```bash
playwright-cli route "**/api/users" --body='[{"name":"Alice"}]' --content-type=application/json
playwright-cli route "**/*.jpg" --status=404
playwright-cli route-list
playwright-cli unroute "**/api/users"
playwright-cli unroute
playwright-cli network-state-set offline
playwright-cli network-state-set online
```

For conditional logic, delays, or request-body inspection, use `run-code`:

```bash
playwright-cli run-code "async page => {
  await page.route('**/api/login', async route => {
    const body = route.request().postDataJSON();
    await route.fulfill({
      status: body.username === 'admin' ? 200 : 401,
      contentType: 'application/json',
      body: JSON.stringify({ ok: body.username === 'admin' })
    });
  });
}"
```

Always remove route mocks you created:

```bash
playwright-cli route-list
playwright-cli unroute "**/api/login"
```

## Tracing

```bash
playwright-cli tracing-start
playwright-cli goto https://example.com
playwright-cli click e5
playwright-cli tracing-stop
```

`tracing-stop` saves a trace and prints the path or artifact link. Use that returned path as the source of truth.

Open traces with Playwright's trace viewer:

```bash
npx playwright show-trace .playwright-cli/trace.zip
```

Trace when:

- the failure is hard to explain from a snapshot
- timing, DOM before/after, console, and request timeline matter
- you need a shareable artifact for a reproduced flow

## Truth Checks With eval

Use `eval` for state that screenshots and snapshots do not prove:

```bash
playwright-cli eval "() => window.location.href"
playwright-cli eval "() => document.title"
playwright-cli eval "() => document.readyState"
playwright-cli eval "(el) => el.value" e3
playwright-cli eval "(el) => el.checked" e8
playwright-cli eval "() => JSON.stringify(localStorage)"
```

Prefer primitive values, JSON-serializable objects, and short expressions. For longer code, use `run-code` and re-snapshot afterward.

## Diagnosis Workflow

```bash
# 1. Start from known state.
playwright-cli snapshot
playwright-cli eval "() => window.location.href"
playwright-cli screenshot --filename=debug-start.png

# 2. Clear evidence buffers.
playwright-cli console --clear
playwright-cli requests --clear

# 3. Reproduce once.
playwright-cli click e5
playwright-cli snapshot
playwright-cli screenshot --filename=after-click.png

# 4. Gather evidence.
playwright-cli console error
playwright-cli requests --filter="/api/"
playwright-cli eval "() => document.title"

# 5. Add trace only if the above is insufficient.
playwright-cli tracing-start
# reproduce a shorter focused flow
playwright-cli tracing-stop
```

Return the relevant artifact paths and the verification rung reached.

## Troubleshooting

| Problem | Recovery |
|---|---|
| `network` examples fail | Use `requests`; confirm with `playwright-cli --help requests`. |
| Console or requests clear prints no useful text | Continue; clear commands are setup steps. |
| Artifact path is unclear | Re-run with `--json` or inspect the Markdown link/path in output. |
| Ref not found | Run `snapshot` again and use fresh refs. |
| Page appears blank | Wait for a visible selector with `run-code`, then `snapshot`. |
| Submit hangs | Use `requests --clear`, reproduce, inspect API entries, then add a trace if needed. |
| Route mock keeps affecting later steps | `route-list`, then `unroute <pattern>` or `unroute` for mocks you own. |
