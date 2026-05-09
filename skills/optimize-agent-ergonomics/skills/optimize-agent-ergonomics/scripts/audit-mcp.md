# audit-mcp.sh

Run this helper when Mode A needs a conservative MCP source preflight before a full code audit.

## Inputs

```bash
bash scripts/audit-mcp.sh <path>
```

`<path>` can be a repo root, package directory, or single source file.

## Outputs

The script prints a markdown report with counts and sample matches for:

- tool registrations and server markers
- schema declarations
- transport strings
- error and retry patterns
- auth, session, CORS, rate-limit, and tenant signals
- possible stdout pollution hazards

The script exits `0` for an existing target and `2` for usage or missing-path errors.

## Limitations

This helper is static evidence only. It does not initialize the server, call tools, validate schemas, inspect generated schema output, verify auth, run MCP Inspector, or replace `test-by-mcpc-cli`. Use `../references/mcp/audit-existing.md` and `../references/mcp/patterns/testing.md` for the full audit path.
