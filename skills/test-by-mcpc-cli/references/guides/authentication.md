# Authentication

Use this guide for OAuth, explicit bearer headers, anonymous mode, and x402 interactions.

## Core commands

```bash
mcpc login https://mcp.example.com/mcp
mcpc login https://mcp.example.com/mcp --profile work --scope "read write"
mcpc login https://mcp.example.com/mcp --client-id cli --client-secret secret
mcpc connect https://mcp.example.com/mcp @secured --profile work
mcpc connect https://mcp.example.com/mcp @anon --no-profile
mcpc connect https://mcp.example.com/mcp @header -H 'Authorization: Bearer token'
```

## Current rules that matter

- `--profile <name>` selects a saved OAuth profile explicitly
- omitting both `--profile` and `--no-profile` allows `mcpc` to auto-pick the `default` profile when one exists for that server
- `--no-profile` disables that auto-pick and forces anonymous connection behavior
- explicit `--header` values override profile-based auth on the wire
- `--x402` skips default-profile auto-detection unless `--profile` is explicit

## Headless or remote login

`mcpc login` prefers opening a browser, but it is not browser-only.
If the browser cannot open, `mcpc` prints a URL you can open manually and then asks you to paste the callback URL back into the CLI.

## JSON inspection

`mcpc --json` exposes profiles as an array.
Filter by server URL and profile name instead of assuming a host-keyed object.

```bash
mcpc --json | jq '.profiles[] | select(.serverUrl == "https://mcp.example.com/mcp" and .name == "default")'
```

Current profile metadata is flat and typically includes fields such as `name`, `serverUrl`, `authType`, and timestamps.
Do not document the old nested `userInfo` shape.

## Storage notes

- OAuth credentials prefer OS keychain storage when available
- `~/.mcpc/credentials.json` is the fallback when keychain integration is unavailable
- per-session headers are not OAuth profiles; they are stored with the session and cleaned with session cleanup

Route precedence edge cases to `references/patterns/auth-precedence.md`.
