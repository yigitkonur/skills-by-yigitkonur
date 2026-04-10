# Auth Precedence

Use this order when reasoning about what auth reaches the wire in `mcpc 0.2.4`.

## Practical precedence

1. explicit `--header` values
2. explicit `--profile <name>`
3. auto-selected `default` profile for the same server
4. config-defined headers on a `file:entry` target
5. anonymous connection

## Modifiers that change the default path

- `--no-profile` disables default-profile auto-selection entirely
- `--x402` also skips default-profile auto-selection unless `--profile` is explicit

## Examples

```bash
mcpc connect https://mcp.example.com/mcp @header -H 'Authorization: Bearer token'
mcpc connect https://mcp.example.com/mcp @named --profile work
mcpc connect https://mcp.example.com/mcp @anon --no-profile
mcpc connect ~/.vscode/mcp.json:remote @from-config
mcpc connect https://mcp.example.com/mcp @paid --x402 --profile default
```

## Storage boundary

- OAuth profiles live in profile and credential storage
- per-session headers are stored with the session, not as reusable profiles
- `restart` does not take new auth flags; reconnect with a new session if the auth shape must change

## Related login options

```bash
mcpc login https://mcp.example.com/mcp --profile work --scope "read write"
mcpc login https://mcp.example.com/mcp --client-id cli --client-secret secret
```
