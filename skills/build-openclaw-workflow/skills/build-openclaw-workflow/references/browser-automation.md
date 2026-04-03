# Browser Automation Patterns

OpenClaw includes a built-in `browser` tool that controls a Chromium instance. By default it uses the isolated `openclaw` browser profile; the higher-risk `user` profile attaches to the user's real signed-in browser session. The `canvas` tool drives node-Canvas for visual output.

**Important:** This reference covers OpenClaw's built-in browser tool, NOT `agent-browser` CLI or Playwright. If the user wants `agent-browser`, use the `run-agent-browser` skill. If they want Playwright, use the `run-playwright` skill.

## Tool reference

### browser tool

| Property | Value |
|---|---|
| Provider | Built-in |
| Group | `group:ui` |
| Risk level | HIGH |
| Capabilities | Navigate, click, type, drag, screenshot, extract text, manage tabs, snapshot refs |

### canvas tool

| Property | Value |
|---|---|
| Provider | Built-in |
| Group | `group:ui` |
| Risk level | Low |
| Capabilities | Draw shapes, render text, produce image output via node-Canvas |

## Risk acknowledgment

The browser tool is HIGH risk because it:

- Can navigate to arbitrary URLs
- Can submit forms and trigger actions on external websites
- Can interact with authenticated sessions
- Can download files
- Executes in the context of the OpenClaw instance's network

**Before any browser automation:**

1. Confirm the user explicitly wants browser automation
2. Identify which sites will be accessed
3. Determine if authentication is involved
4. Confirm whether the isolated `openclaw` profile is sufficient or whether `profile="user"` is required
5. Confirm the user understands the tool will interact with live websites

## Core browser flow

The browser API is ref-based. The CLI examples below show the exact action model; tool calls use the same operations and the same fresh refs.

### Start and inspect the browser

```bash
openclaw browser --browser-profile openclaw status
openclaw browser --browser-profile openclaw start
openclaw browser --browser-profile openclaw open https://example.com
```

Use `profile="user"` only when the task truly depends on the user's existing logged-in session and the user is present to approve the attach.

### Take a snapshot before acting

```bash
openclaw browser --browser-profile openclaw snapshot
openclaw browser --browser-profile openclaw snapshot --interactive
```

Snapshots return refs. Actions use those refs, not CSS selectors. Numeric refs come from the default AI snapshot. Role refs like `e12` come from `--interactive`.

### Act on refs

```bash
openclaw browser --browser-profile openclaw click 12
openclaw browser --browser-profile openclaw type e12 "hello"
openclaw browser --browser-profile openclaw select e14 OptionA
openclaw browser --browser-profile openclaw press Enter
```

After every interaction:

- Re-run `snapshot` after any DOM-changing action; refs are not stable across navigations
- Verify the action took effect before the next step
- Wait for dynamic content if the page updates asynchronously

### Wait and verify

```bash
openclaw browser --browser-profile openclaw wait --url "**/dashboard"
openclaw browser --browser-profile openclaw wait --load networkidle
openclaw browser --browser-profile openclaw wait "#main"
```

Use selectors for `wait` or snapshot scoping only. Do not try to `click` or `type` by CSS selector.

### Screenshots

```bash
openclaw browser --browser-profile openclaw screenshot
openclaw browser --browser-profile openclaw screenshot /tmp/openclaw-step.png
```

Use screenshots for:

- Verification after key actions
- Evidence for the user
- Debugging when text extraction is not sufficient
- Visual state capture before and after changes

## Workflow patterns

### Form filling

```
1. Navigate to the form page
2. Take `snapshot --interactive` and identify the relevant refs
3. Fill each field one at a time using fresh refs
4. Verify each field's value after filling
5. Screenshot the filled form before submission
6. Re-snapshot, then submit with the button's current ref
7. Verify the submission result (URL change, confirmation text)
8. Screenshot the result
```

### Data extraction

```
1. Navigate to the data page
2. Take a snapshot and capture the refs or text you need
3. If content is paginated, navigate through pages and extract from each
4. Verify extracted data is complete and well-formed
5. Pass extracted data to LLM Task or exec for processing
```

### Multi-page workflow

```
1. Navigate to starting page
2. Extract or interact on page 1
3. Navigate to page 2 (via a fresh click ref or direct URL)
4. Verify you are on page 2 (check URL and title)
5. Extract or interact on page 2
6. Continue until workflow is complete
7. Return to starting page or close as appropriate
```

## Combining browser with other tools

### Browser + LLM Task

Extract content with browser, analyze with LLM Task:

```
Step 1 (browser): Navigate and extract page text
Step 2 (LLM Task): Analyze extracted text, produce structured JSON
Step 3 (optional exec): Act on the analysis results
```

### Browser + Lobster

Wrap browser actions in Lobster steps for typed data flow and approval gates:

```
Lobster Workflow: web-monitoring
  Step 1 (browser): Navigate to target site, screenshot, extract text
  Step 2 (LLM Task): Compare current text to previous baseline
  Step 3 (approval): If changes detected, approve notification
  Step 4 (exec): Send notification
```

### Browser + cron

Schedule periodic browser checks via cron. Use carefully -- this means automated, unsupervised browser interaction.

**Safety:** Only use for monitoring and read-only extraction. Do NOT schedule automated form submissions or authenticated interactions via cron.

## Canvas tool

The canvas tool drives node-Canvas for programmatic image generation:

- Draw shapes (rectangles, circles, lines, paths)
- Render text with fonts and colors
- Composite images
- Produce PNG or JPEG output

Use canvas when:

- You need to generate images programmatically (charts, diagrams, badges)
- Visual output is required but does not need a real browser
- You want to annotate or transform existing images

Do NOT use canvas when:

- You need to interact with a website (use browser)
- You need to view a website's rendered output (use browser screenshot)
- The visual output requires complex CSS layout (use browser with HTML)

## Refs, not selectors

Browser actions require refs from `snapshot`. CSS selectors are for waiting or narrowing a snapshot, not for direct actions.

- Use `snapshot --interactive` when you want role refs like `e12`
- Re-snapshot after navigation or DOM changes because refs can go stale
- Use `highlight <ref>` when a click/type target is unclear
- Use selectors only for `wait` or snapshot filtering

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Element not found | Page not fully loaded, or you are using a stale ref | Wait for page load, take a fresh snapshot, try the new ref |
| Click has no effect | Element is hidden, overlapped, or not interactive | Re-snapshot, use `highlight <ref>`, check for overlays |
| Form submission fails | Missing required fields, validation errors | Fill all required fields, check for client-side validation |
| Screenshot is blank | Page still loading or render error | Add wait after navigation, check for errors |
| Wrong page after navigation | Redirect or authentication required | Check URL after navigation, handle auth flow first |
| Stale refs after interaction | Dynamic content changed the DOM | Re-run `snapshot` after every action that changes content |
