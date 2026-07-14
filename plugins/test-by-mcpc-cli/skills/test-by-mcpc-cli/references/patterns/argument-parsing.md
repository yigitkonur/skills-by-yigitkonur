# Argument Parsing

## Current command family

```bash
mcpc connect https://research.yigitkonur.com/mcp @research
mcpc @research tools-call search-reddit '{"queries":["OpenAI MCP"]}'
mcpc @research tools-call args-tool city:=Paris enabled:=true
printf '%s' '{"queries":["OpenAI MCP"]}' | mcpc @research tools-call search-reddit
```

## Supported argument shapes

### `key:=value`

Use this for simple typed values.
`mcpc` runs JSON parsing on the value part, so quoted JSON literals still work.

```bash
count:=10
enabled:=true
city:=Paris
tags:='["a","b"]'
config:='{"debug":true}'
```

If the tool expects an array, `queries:=OpenAI` is wrong because it is still a string.

### inline JSON

Use a single inline JSON document when you want to send the full argument payload yourself.
Do not mix it with `key:=value` pairs.

```bash
mcpc @research tools-call search-reddit '{"queries":["OpenAI MCP"]}'
```

### stdin JSON

Use stdin for scripted pipelines.
Treat it the same way as an inline JSON payload.
In practice, most MCP tool and prompt inputs should still be JSON objects because their schemas are object-shaped.

## Option parsing note

Document public help output, not internal parser quirks.
If an option is not shown in `mcpc --help` or command help, do not treat it as public contract.
