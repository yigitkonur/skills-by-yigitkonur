# Argument Parsing

## Current command family

```bash
mcpc connect https://research-mcp.yigitkonur.com/mcp @research
mcpc @research tools-call web-search '{"queries":["OpenAI MCP"]}'
mcpc @research tools-call args-tool city:=Paris enabled:=true
printf '%s' '{"queries":["OpenAI MCP"]}' | mcpc @research tools-call web-search
```

Same three forms work for `prompts-get` (`mcpc @research prompts-get some-prompt city:=Paris`).

## Supported argument shapes

### `key:=value`

Use this for simple typed values.
Each value is auto-parsed as JSON (strings, numbers, booleans, objects, arrays), falling back to a plain string on parse failure.

```bash
count:=10
enabled:=true
city:=Paris
tags:='["a","b"]'
config:='{"debug":true}'
```

Force a string when auto-parsing would otherwise coerce it: wrap it in quoted JSON, `id:='"123"'`.

If the tool expects an array, `queries:=OpenAI` is wrong because it is still a string. Use `queries:='["OpenAI"]'` instead.

A bare `=` (`queries=["x"]`, no colon) is not a valid form at all — mcpc rejects it client-side: `Error: Invalid argument format: "queries=[\"x\"]". Use key:=value pairs or inline JSON.`, exit 1. `:=` is the only assignment operator; there is no plain `key=value` string form.

### inline JSON

Use a single inline JSON document when you want to send the full argument payload yourself.
Do not mix it with `key:=value` pairs.

```bash
mcpc @research tools-call web-search '{"queries":["OpenAI MCP"]}'
```

### stdin JSON

Auto-detected when the input is piped and no positional args are given. Treat it the same way as an inline JSON payload.
In practice, most MCP tool and prompt inputs should still be JSON objects because their schemas are object-shaped.

## `tools-get`'s printed example can be wrong

`tools-get <tool>` prints a human-readable "Call example" line derived from the tool's schema. For an `array<string>` argument it can print the wrong shape — e.g. `urls:='"something"'` for a field that actually needs `urls:='["something"]'`. Trust the `Input:` type shown above it (`array<string>` vs `string`), not the literal example line; copy-pasting it verbatim for an array argument fails the tool's own schema check.

## Option parsing note

Document public help output, not internal parser quirks — if an option is not shown in `mcpc --help` or command help, do not treat it as public contract.
