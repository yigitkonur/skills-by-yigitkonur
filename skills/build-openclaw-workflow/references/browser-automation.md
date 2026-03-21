# Browser Automation Patterns

OpenClaw includes a built-in `browser` tool that controls a Chromium instance. It supports navigation, clicking, form filling, screenshots, and content extraction. The `canvas` tool drives node-Canvas for visual output.

**Important:** This reference covers OpenClaw's built-in browser tool, NOT `agent-browser` CLI or Playwright. If the user wants `agent-browser`, use the `run-agent-browser` skill. If they want Playwright, use the `run-playwright` skill.

## Tool reference

### browser tool

| Property | Value |
|---|---|
| Provider | Built-in |
| Group | `group:ui` |
| Risk level | HIGH |
| Capabilities | Navigate, click, type, screenshot, extract text, manage tabs |

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
4. Confirm the user understands the tool will interact with live websites

## Core browser operations

### Navigation

```
browser navigate to URL
browser go back
browser go forward
browser refresh
```

After every navigation action, verify the current state before proceeding:

- Check the current URL
- Check the page title
- Take a screenshot if visual confirmation is needed

### Interaction

```
browser click SELECTOR
browser type SELECTOR "text to type"
browser select SELECTOR "option value"
browser check SELECTOR
browser uncheck SELECTOR
```

After every interaction:

- Verify the action took effect (check values, visibility, URL changes)
- Wait for any dynamic content to load
- Re-inspect the page before the next action

### Extraction

```
browser get text SELECTOR
browser get attribute SELECTOR "attribute-name"
browser get url
browser get title
```

### Screenshots

```
browser screenshot
browser screenshot FILEPATH
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
2. Verify the form is visible (screenshot or text extraction)
3. Fill each field one at a time
4. Verify each field's value after filling
5. Screenshot the filled form before submission
6. Submit the form
7. Verify the submission result (URL change, confirmation text)
8. Screenshot the result
```

### Data extraction

```
1. Navigate to the data page
2. Extract the target content using selectors
3. If content is paginated, navigate through pages and extract from each
4. Verify extracted data is complete and well-formed
5. Pass extracted data to LLM Task or exec for processing
```

### Multi-page workflow

```
1. Navigate to starting page
2. Extract or interact on page 1
3. Navigate to page 2 (via click or direct URL)
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

## Selectors

When targeting elements in the browser tool:

1. **Prefer IDs** -- `#submit-button` is the most reliable
2. **Use data attributes** -- `[data-testid="login-form"]` is stable across UI changes
3. **Use semantic selectors** -- `button[type="submit"]` is better than class-based
4. **Avoid fragile selectors** -- long CSS paths like `div > div > span:nth-child(3)` break easily

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Element not found | Page not fully loaded, or wrong selector | Wait for page load, verify with screenshot, try different selector |
| Click has no effect | Element is hidden, overlapped, or not interactive | Check visibility, scroll to element, check for overlays |
| Form submission fails | Missing required fields, validation errors | Fill all required fields, check for client-side validation |
| Screenshot is blank | Page still loading or render error | Add wait after navigation, check for errors |
| Wrong page after navigation | Redirect or authentication required | Check URL after navigation, handle auth flow first |
| Stale selectors after interaction | Dynamic content changed the DOM | Re-inspect the page after every action that changes content |
