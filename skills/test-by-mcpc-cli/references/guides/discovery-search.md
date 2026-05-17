# Discovery and Search

Start with the native discovery surface before building custom filters.

## First look

```bash
mcpc @session
mcpc @session help
mcpc @session tools-list
mcpc @session tools-list --full
mcpc @session resources-list
mcpc @session prompts-list
mcpc @session resources-templates-list
```

`mcpc @session` and `mcpc @session help` show server info, capabilities, instructions, and available commands.

## Native grep

```bash
mcpc grep search
mcpc @session grep actor
mcpc grep config --resources --prompts
mcpc grep 'search|find' -E
mcpc grep file -m 5 --json
```

Current behavior:

- default grep scope is tools plus instructions
- `--resources` and `--prompts` change the search domain; combine flags when needed
- session grep works on a single connected session

## Aliases that still work

Even though help prefers explicit list commands, these aliases still work:

```bash
mcpc @session tools
mcpc @session resources
mcpc @session prompts
```

Treat them as convenience aliases, not the form you teach first.

## When to switch to `jq`

Use JSON filtering after native discovery when you need:

- exact schema field extraction
- diffable machine output
- batch assertions in CI
- complex filters across annotations or task metadata

Routes:

- `references/patterns/jq-patterns.md`
- `references/patterns/tool-filtering.md`
