# Schema Validation

`mcpc` exposes schema validation through `--schema` and `--schema-mode`, scoped to `tools-get` and `tools-call` only.

## Current commands that matter

```bash
mcpc @research-test tools-get web-search --schema ./tool-schema.json
mcpc @research-test tools-call web-search '{"queries":["OpenAI MCP"]}' --schema ./tool-schema.json
```

`prompts-get` does **not** accept `--schema` — it was removed from `prompts-get` (schema validation there was confusing and rarely used). `mcpc @everything-http prompts-get args-prompt city:=Paris --schema ./prompt-schema.json` fails with `unknown option '--schema'`, exit 1.

Save the expected schema once with `tools-get --json` (the full `Tool` object — `name`, `title`, `description`, `inputSchema`, `outputSchema`, `annotations`, `execution` — only `inputSchema`/`outputSchema` are diffed), then validate later calls against it:

```bash
mcpc --json @research-test tools-get web-search > tool-schema.json
mcpc @research-test tools-call web-search --schema ./tool-schema.json '{"queries":["OpenAI MCP"]}'
```

## Modes

- `strict` — full schema must match exactly (description, input, output).
- `compatible` (default) — scope differs by command: `tools-get` diffs the whole input/output schema shape and fails on any added, removed, or changed property, required or not; `tools-call` only validates the arguments actually being passed, tolerates unrelated optional-property drift, but still fails ("New required field ... added (breaking change)") when the live schema now requires a field your snapshot lacks and you don't supply it.
- `ignore` — skips validation entirely, even if `--schema` is set. Confirmed live: `tools-get --schema <mismatched-file> --schema-mode ignore` prints the normal tool block, exit 0.

## On failure

A schema mismatch is a **client error**: it throws before the tool ever runs, prints the mismatched fields, and exits **1** — not the `isError:true`/exit-2 path a runtime tool failure takes, because no MCP call happened. Confirmed live against `research-mcp.yigitkonur.com/mcp` on 0.6.0: a type-mismatched schema file (`queries: string` vs the live `array`) makes both `tools-get web-search --schema <file>` and `tools-call web-search --schema <file> ...` print `Error: Schema validation failed for tool "web-search": ...` and exit 1, in both `compatible` (default) and `strict` mode.

## Important nuance

`tools-get` is a CLI convenience backed by discovery metadata, not a native MCP `tools/get` method — schema validation here checks metadata, not a live call.

## Good uses

- regression checks for required tool fields
- confirming a schema file is actually wired into the command path
- CI drift guard: snapshot `tools-get --json` once, fail fast if the live schema moves
