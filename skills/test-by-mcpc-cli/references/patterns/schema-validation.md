# Schema Validation

`mcpc` exposes schema validation through `--schema` and `--schema-mode`, scoped to `tools-get` and `tools-call` only.

## Current commands that matter

```bash
mcpc @research-test tools-get web-search --schema ./tool-schema.json
mcpc @research-test tools-call web-search '{"queries":["OpenAI MCP"]}' --schema ./tool-schema.json
```

`prompts-get` does **not** accept `--schema` — it was removed from `prompts-get` (schema validation there was confusing and rarely used). `mcpc @everything-http prompts-get args-prompt city:=Paris --schema ./prompt-schema.json` fails with `unknown option '--schema'`, exit 1.

Save the expected schema once with `tools-get --json` (the raw `Tool` object: `name`, `description`, `inputSchema`, `outputSchema`), then validate later calls against it:

```bash
mcpc --json @research-test tools-get web-search > tool-schema.json
mcpc @research-test tools-call web-search --schema ./tool-schema.json '{"queries":["OpenAI MCP"]}'
```

## Modes

- `strict` — full schema must match exactly (description, input, output).
- `compatible` (default) — with `tools-call`, only validates arguments actually being passed; ignores changes to optional arguments not in use; still flags new required arguments as breaking.
- `ignore` — skips validation entirely, even if `--schema` is set.

## On failure

A schema mismatch is a **client error**: it throws before the tool ever runs, prints the mismatched fields, and exits **1** — not the `isError:true`/exit-2 path a runtime tool failure takes, because no MCP call happened. Confirmed live against `research-mcp.yigitkonur.com/mcp`: `tools-get web-search --schema <mismatched-file>` and `tools-call web-search --schema <mismatched-file> ...` both print `Error: Schema validation failed for tool "web-search": ...` and exit 1.

## Important nuance

`tools-get` is a CLI convenience backed by discovery metadata, not a native MCP `tools/get` method.
That does not make schema validation less useful, but it changes what you are really validating.

## Good uses

- regression checks for required tool fields
- confirming a schema file is actually wired into the command path
- CI drift guard: snapshot `tools-get --json` once, fail fast if the live schema moves
