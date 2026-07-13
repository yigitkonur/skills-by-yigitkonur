# `inspect-page.sh`

Use this helper only when the user asked for a repeatable capture; ad hoc browser work should remain one command at a time.

```bash
bash scripts/inspect-page.sh https://example.com /tmp/example-inspect
bash scripts/inspect-page.sh --screenshot https://example.com /tmp/example-inspect
```

It writes:

- `final-url.txt`
- `title.txt`
- `snapshot-interactive.json`
- `snapshot-interactive.txt`
- `page.md`
- `errors.txt`
- optional `screenshot.png`

On Yigit's Mac it uses the managed headed-CDP pool, records the task tab, closes only that tab, and releases the lane with exact top-level `agent-browser close`. On hosts without the pool it creates and closes an isolated temporary upstream session. Artifacts may contain private page data; inspect them before sharing or committing.
