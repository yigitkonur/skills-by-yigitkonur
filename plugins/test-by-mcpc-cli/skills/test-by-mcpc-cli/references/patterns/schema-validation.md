# Schema Validation

`mcpc` exposes schema validation through `--schema` and `--schema-mode`.

## Current commands that matter

```bash
mcpc @research-test tools-get search-reddit --schema ./tool-schema.json
mcpc @research-test tools-call search-reddit '{"queries":["OpenAI MCP"]}' --schema ./result-schema.json
mcpc @everything-http prompts-get args-prompt city:=Paris --schema ./prompt-schema.json
```

## Modes

- `strict`
- `compatible`
- `ignore`

`compatible` is the default.

## Important nuance

`tools-get` is a CLI convenience backed by discovery metadata, not a native MCP `tools/get` method.
That does not make schema validation less useful, but it changes what you are really validating.

## Good uses

- regression checks for required tool fields
- prompt argument contract checks
- confirming a schema file is actually wired into the command path
