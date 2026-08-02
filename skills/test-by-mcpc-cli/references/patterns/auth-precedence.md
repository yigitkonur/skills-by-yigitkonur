# Auth Precedence

Use this order when reasoning about what auth reaches the wire in `mcpc 0.6.0`.

## Practical precedence

1. explicit `--header` values
2. explicit `--profile <name>`
3. auto-selected `default` profile for the same server
4. config-defined headers on a `file:entry` target
5. anonymous connection

## Modifiers that change the default path

- `--no-profile` disables default-profile auto-selection entirely
- `--x402 [scheme]` also skips default-profile auto-selection unless `--profile` is explicit — but
  unlike `-H`, `--x402` CAN combine with `--profile` to use both (x402 payment + OAuth identity)
- `--header` cannot be combined with `--profile` on the same connect (they compete for the same slot)

## Grant type does not change precedence

`--grant client-credentials` / `--grant id-jag` on `mcpc login` (see
`references/guides/authentication.md`) only change how a profile is *acquired* — the resulting
profile is stored and selected the same way as an `authorization-code` profile, at precedence
rungs 2–3 above. There is no separate precedence rung for grant type.

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
mcpc login https://mcp.example.com/mcp --grant client-credentials --client-id svc --client-secret secret
```
