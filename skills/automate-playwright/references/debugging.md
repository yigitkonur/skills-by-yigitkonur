# Debugging and DevTools

## Table of Contents

- [What the debug commands return](#what-the-debug-commands-return)
- [Console logs](#console-logs)
- [Network logs](#network-logs)
- [eval](#eval)
- [run-code](#run-code)
- [Troubleshooting guide](#troubleshooting-guide)

---

## What the debug commands return

A major correction from the earlier docs:

- `console` and `network` return artifact file paths,
- those files may contain useful entries or may be empty,
- you must inspect the returned file instead of expecting inline diagnosis.

Also note that artifact paths should be treated as runtime outputs, not guessed from repo layout.
Artifact existence alone is not proof: the file may be empty, noisy, or irrelevant to the exact flow you are testing.

---

## Console logs

### Basic usage

```bash
console
console error
console warning
console --clear
```

### Workflow

```bash
console --clear
# reproduce the issue
console error
```

Then open the returned file path.

Observed behavior:
- the CLI prints a path like `.playwright-cli/console-...log`;
- some pages generate meaningful browser errors;
- some returned files can be empty.

### Real-world example

On a public Amazon search page, console output included:
- 405 errors on suggestions endpoints,
- 400 reporting-related failures,
- 429 bot-policy related events,
- GPU / ReadPixels warnings.

That means console logs are useful evidence, but public production sites can also emit noisy telemetry failures that are not necessarily regressions in your app.
Do not convert public-site noise into a bug claim unless the logs line up with the broken flow you are verifying.

---

## Network logs

### Basic usage

```bash
network
network --static
network --clear
```

### Workflow

```bash
network --clear
# reproduce the issue
network
```

Then open the returned file.

Observed behavior:
- the returned file can include request method, URL, and status;
- it may also be empty depending on when you captured it;
- `--static` is useful when asset failures matter.

### Practical use

Use network logs to answer questions like:
- did a request 4xx/5xx?
- did a filter click navigate correctly?
- are requests being blocked or rate-limited?

---

## eval

Use `eval` for truth checks.

### Page context

```bash
eval "() => document.title"
eval "() => window.location.href"
eval "() => document.querySelectorAll('.item').length"
```

### Element context

```bash
eval "(el) => el.value" <ref>
eval "(el) => el.textContent" <ref>
eval "(el) => el.checked" <ref>
eval "(el) => getComputedStyle(el).color" <ref>
```

### Why `eval` matters

In several real tests, `eval(() => window.location.href)` was more trustworthy than surrounding command headers when tab state or page metadata looked suspicious.
Use the same habit for field values, checked state, and uploaded filenames when correctness matters.

---

## run-code

Use `run-code` when the CLI cannot express the step cleanly.

Good use cases:
- waits (`waitForSelector`, `waitForResponse`, `waitForURL`)
- popup handling
- download handling
- file-input fallback with `setInputFiles`
- browser-context features like media emulation

### Syntax

```bash
run-code 'async (page) => {
  await page.waitForSelector(".loaded")
  return "done"
}'
```

### Quoting rule

Use single quotes outside and double quotes inside.

### Re-entry rule

After `run-code`, do not trust old refs.
Re-enter the normal CLI evidence loop before continuing.

```bash
snapshot
screenshot --filename=after-run-code.png
```

---

## Troubleshooting guide

### "Ref not found"
Your refs are stale.

```bash
snapshot
```

### Upload fails with modal-state error
You called `upload` before triggering a file chooser.

Safe pattern:

```bash
click <upload-trigger-ref>
upload /absolute/path/to/file
```

### Upload fails with path denied
The file is outside allowed roots. Move or copy it into an allowed location.

### A command did not print a snapshot
Do not assume command outputs are uniform.

```bash
[action]
snapshot
```

### URL or page header seems inconsistent
Use:

```bash
eval "() => window.location.href"
```

### zsh rejects the URL before the CLI runs
Quote the URL:

```bash
open "https://www.amazon.com/s?k=fidget+spinner"
```

### Public-site noise
Production sites may emit telemetry, anti-bot, or graphics warnings. Treat these as evidence to interpret, not automatic proof of a bug in your app.
Tie any bug claim back to page truth such as `eval "() => window.location.href"`, the actual UI state, and the flow you just reproduced.
