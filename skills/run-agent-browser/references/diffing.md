# Diffing

Compare page states — structurally via accessibility tree snapshots, visually via pixel comparison, or across two different URLs.

## Commands

| Command | Description |
|---------|-------------|
| `diff snapshot` | Compare current snapshot to last snapshot in session |
| `diff snapshot --baseline <file>` | Compare current snapshot to a saved file |
| `diff screenshot --baseline <file>` | Visual pixel diff against a baseline image |
| `diff url <url1> <url2>` | Compare two pages (snapshot + optional screenshot) |

## Snapshot Diff

Compares the accessibility tree between two points in time using a line-level text diff.

```bash
# Compare against the last snapshot taken in this session
agent-browser diff snapshot

# Compare against a saved baseline file
agent-browser diff snapshot --baseline before.txt

# Scope to a specific part of the page
agent-browser diff snapshot --selector "#main" --compact
```

Without `--baseline`, the command automatically compares against the most recent snapshot taken in the current session. This is the primary use case for agents verifying that an action had the intended effect.

### Options

| Flag | Description |
|------|-------------|
| `-b, --baseline <file>` | Path to a saved snapshot file to compare against |
| `-s, --selector <sel>` | Scope the current snapshot to a CSS selector or @ref |
| `-c, --compact` | Use compact snapshot format |
| `-d, --depth <n>` | Limit snapshot tree depth |

### Output

The diff uses `+` for added lines and `-` for removed lines, similar to unified diff format. A summary line shows the count of additions, removals, and unchanged lines.

```
- button "Submit" [ref=e2]
+ button "Submit" [ref=e2] [disabled]
  3 additions, 2 removals, 41 unchanged
```

## Screenshot Diff

Compares the current page screenshot against a baseline image at the pixel level. Produces a diff image with changed pixels highlighted in red.

```bash
# Basic visual diff
agent-browser diff screenshot --baseline before.png

# Save diff image to a specific path
agent-browser diff screenshot --baseline before.png --output diff.png

# Adjust threshold and scope to element
agent-browser diff screenshot --baseline before.png --threshold 0.2 --selector "#hero"
```

### Options

| Flag | Description |
|------|-------------|
| `-b, --baseline <file>` | Baseline PNG/JPEG image to compare against (required) |
| `-o, --output <file>` | Path for the generated diff image (default: temp dir) |
| `-t, --threshold <0-1>` | Color distance threshold (default: 0.1). Higher = more tolerant |
| `-s, --selector <sel>` | Scope the current screenshot to an element |
| `--full` | Take a full-page screenshot |

### Output

Reports the diff image path, number of different pixels, and mismatch percentage. The diff image shows unchanged pixels dimmed with changed pixels in red.

```
✗ 2.37% pixels differ
Diff image: ~/.agent-browser/tmp/diffs/diff-1708473621.png
1,137 different / 48,000 total pixels
```

If the baseline and current images have different dimensions, the command reports a dimension mismatch instead of attempting pixel comparison.

## URL Diff

Compares two pages by navigating to each in sequence and diffing the results.

```bash
# Compare two URLs (snapshot diff)
agent-browser diff url https://staging.example.com https://prod.example.com

# Include visual comparison
agent-browser diff url https://v1.example.com https://v2.example.com --screenshot

# Full-page screenshot comparison
agent-browser diff url https://v1.example.com https://v2.example.com --screenshot --full
```

The command navigates to the first URL, captures state, then navigates to the second URL and captures again. Snapshot diff is always included. Screenshot diff requires the `--screenshot` flag.

After completion, the browser remains on the second URL.

### Options

| Flag | Description |
|------|-------------|
| `--screenshot` | Also perform visual screenshot comparison |
| `--full` | Use full-page screenshots |
| `--wait-until <strategy>` | Navigation wait strategy: `load`, `domcontentloaded`, `networkidle` (default: `load`) |
| `-s, --selector <sel>` | Scope snapshots to a CSS selector or @ref |
| `-c, --compact` | Use compact snapshot format |
| `-d, --depth <n>` | Limit snapshot tree depth |

## Use Cases

### 1. Verifying Agent Actions

The most common use case: confirm that an action (click, fill, submit) changed the page as expected.

```bash
agent-browser snapshot -i          # Take interactive-only snapshot (baseline)
agent-browser fill @e3 "test@example.com"
agent-browser diff snapshot        # Compare current snapshot to the baseline
```

Example output:

```
heading "Sign Up" [ref=e1]
text "Create your account" [ref=e2]
- textbox "Email" [ref=e3]
+ textbox "Email" [ref=e3]: "test@example.com"
- button "Submit" [ref=e4]
+ button "Submit" [ref=e4] [disabled]
+ status "Sending..." [ref=e7]
link "Already have an account?" [ref=e5]
3 additions, 2 removals, 3 unchanged
```

### 2. Monitoring for Changes

Periodically compare a page against a saved baseline to detect updates.

```bash
# Save baseline
agent-browser open https://example.com && agent-browser snapshot > baseline.txt

# Later, check for changes
agent-browser open https://example.com && agent-browser diff snapshot --baseline baseline.txt
```

### 3. Visual Regression Testing

Compare screenshots before and after a deploy to catch unintended visual changes.

```bash
agent-browser open https://staging.example.com && agent-browser screenshot baseline.png
# ... deploy happens ...
agent-browser open https://staging.example.com && agent-browser diff screenshot --baseline baseline.png
```

### 4. Comparing Environments

Diff staging against production to verify parity.

```bash
agent-browser diff url https://staging.example.com https://prod.example.com --screenshot
```
