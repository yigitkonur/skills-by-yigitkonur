# Tool, Prompt, and Resource Testing

Use this guide once the session is already connected.

## Tools

```bash
mcpc @session tools-list --full
mcpc @session tools-get tool-name
mcpc --json @session tools-call tool-name '{"key":"value"}'
```

Rules:

- inspect schema before the first non-trivial call
- prefer full JSON payloads for arrays or nested objects
- always check `isError` in JSON mode

## Prompts

```bash
mcpc @everything-http prompts-list
mcpc @everything-http prompts-get args-prompt city:=Paris state:=Texas
mcpc @everything-http prompts-get args-prompt city:=Paris --schema ./expected-schema.json
```

`prompts-get` accepts `--schema` and `--schema-mode` in the current released CLI.

## Resources

```bash
mcpc @everything-http resources-list
mcpc @everything-http resources-read demo://resource/static/document/features.md
mcpc @everything-http resources-subscribe demo://resource/dynamic/config
mcpc @everything-http resources-unsubscribe demo://resource/dynamic/config
mcpc @everything-http resources-templates-list
```

Subscriptions are easiest to validate through JSON session output or bridge logs.

## Logging

```bash
mcpc @everything-http logging-set-level debug
```

Use this together with bridge logs when you need to understand list-changed notifications or server-side failures.
