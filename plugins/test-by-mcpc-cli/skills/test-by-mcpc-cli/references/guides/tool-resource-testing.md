# Tool, Prompt, and Resource Testing

Use this guide once the session is already connected. Verified against `mcpc` 0.6.0.

## Tools

```bash
mcpc @session tools-list --full
mcpc @session tools-get tool-name
mcpc --json @session tools-call tool-name '{"key":"value"}'
```

Rules:

- inspect schema before the first non-trivial call
- prefer full JSON payloads for arrays or nested objects
- `tools-call` exits `2` when the result carries `isError: true` (since v0.5.0) — a clean signal on its own, but still inspect the payload for the failure reason

## Prompts

```bash
mcpc @everything-http prompts-list
mcpc @everything-http prompts-get args-prompt city:=Paris state:=Texas
```

`prompts-get` takes no `--schema`/`--schema-mode` flags — those were scoped to `tools-get`/`tools-call` only as of v0.2.5 and never applied to prompts. For prompt schema drift checks, diff `mcpc --json @session prompts-get <name> ...` output yourself.

## Resources

```bash
mcpc @everything-http resources-list
mcpc @everything-http resources-read demo://resource/static/document/features.md
mcpc @everything-http resources-read demo://resource/static/document/features.md -o ./features.md
mcpc @everything-http resources-subscribe demo://resource/dynamic/config ./config-sync.json
mcpc @everything-http resources-unsubscribe demo://resource/dynamic/config
mcpc @everything-http resources-templates-list
```

`resources-subscribe <uri> <file>` requires the `<file>` positional argument (since v0.4.0) — it downloads the resource to `<file>` immediately, then rewrites it on every server change notification for as long as the session stays connected, surviving reconnects and bridge restarts. Re-subscribing to the same `<uri>` just retargets `<file>`. `resources-unsubscribe` stops the sync but keeps the file on disk. `resources-read` supports `-o <file>`/`--output <file>` (binary-safe save) and `--raw` (bare content for piping); `--json` is needed to see all content items when a resource returns more than one.

Active subscriptions are not shown in plain `mcpc @session` output — check `mcpc --json @session` and read the `resourceSubscriptions` field on the session object.

## Logging

```bash
mcpc @everything-http logging-set-level debug
```

`logging-set-level` is deprecated: MCP 2026-07-28 removed `logging/setLevel`, so this only works against servers on protocol `2025-11-25` or older, and mcpc will drop the command in a future release. The warning fires even when talking to a `2025-11-25` server where the call still succeeds (exit `0`) — it is advance notice of upstream spec churn, not a failure of the current call. Use `mcpc @session logs` (with `-n`, `--follow`, `--since`) alongside it to read server-side log output.
