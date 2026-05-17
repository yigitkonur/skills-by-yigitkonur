# inspect-page.sh

Use this helper for a repeatable first-pass page inspection before writing custom browser steps or handing capture artifacts to another skill.

```bash
bash scripts/inspect-page.sh https://example.com /tmp/example-inspect
bash scripts/inspect-page.sh --screenshot https://example.com /tmp/example-inspect
```

Behavior:
- opens the URL in an isolated temporary `--session`
- waits for `networkidle`, with a short fixed wait fallback for pages that never become idle
- writes final URL, title, `snapshot -i --json`, and human-readable `snapshot -i`
- writes `screenshot.png` only when `--screenshot` is passed
- closes only the temporary session it created
- does not load, save, or persist auth state

Use the JSON snapshot for deterministic ref extraction. Use the text snapshot for quick human inspection. Use screenshots only when visual evidence matters.
