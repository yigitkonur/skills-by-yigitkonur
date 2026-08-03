# inspect-page.sh

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

The helper sources `~/.config/steel-browser-cdp.env`, creates a unique named agent-browser session, unsets the global provider variable only for each CDP subprocess, connects through `STEEL_AGENT_BROWSER_CDP`, and closes that task session on exit. It does not use the Patchright scrape pool or provider credits.

Artifacts can contain private page data; inspect them before sharing or committing.
