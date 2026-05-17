# Device-Flow Login

`mcp-use login`, `whoami`, and `logout` manage Manufact Cloud credentials via OAuth device-code flow.

## Commands

```bash
mcp-use login
mcp-use whoami
mcp-use logout
```

## `mcp-use login`

Starts an OAuth device-code flow:

1. The CLI prints a verification URL and a one-time code.
2. The CLI opens the URL in your browser (when possible).
3. You approve the device in the browser.
4. The CLI polls until the approval lands, creates a persistent API key, and stores that key.

The device flow requests a device code from `/api/auth/device/code`, polls `/api/auth/device/token`, then creates a persistent API key for the CLI. Output is written to `~/.mcp-use/config.json`:

```json
{
  "apiKey": "your-api-key-here",
  "orgId": "org-id",
  "orgName": "Org Name",
  "orgSlug": "org-slug"
}
```

The file is user-scope, not project-scope — log in once per machine, not per project.

## Non-interactive login

For CI or agents, `@mcp-use/cli@3.1.2` supports an API-key path:

```bash
mcp-use login --api-key "$MCP_USE_API_KEY"
mcp-use login --api-key "$MCP_USE_API_KEY" --org acme-team
```

The command also reads `MCP_USE_API_KEY` when `--api-key` is omitted.

## `mcp-use whoami`

Print the active session:

```bash
mcp-use whoami
```

Output shape varies by version; expect logged-in account and active org. Use as a quick gate before destructive deploys:

```bash
mcp-use whoami && mcp-use deploy --env-file .env.prod
```

## `mcp-use logout`

Remove credentials from `~/.mcp-use/config.json`:

```bash
mcp-use logout
```

Use when rotating tokens, switching machines, or revoking access.

## When you get prompted

| Trigger | What happens |
|---|---|
| First `mcp-use deploy` on a fresh machine | Login required first; `deploy` aborts with a clear message |
| Token expired | `deploy` prompts for re-login |
| Switched orgs externally | Run `mcp-use whoami` to confirm; re-`login` if your token was invalidated |

## Non-interactive auth

The device-code flow assumes a human can open a browser. For CI where there is no browser:

| Approach | How |
|---|---|
| Use API key flag | `mcp-use login --api-key "$MCP_USE_API_KEY"` |
| Use API key env var | `MCP_USE_API_KEY=... mcp-use login` |
| Copy config file | Drop `~/.mcp-use/config.json` into the CI runner before `mcp-use deploy`. |

`MCP_USE_TOKEN` is not read by `@mcp-use/cli@3.1.2`; use `MCP_USE_API_KEY` or `--api-key`.

Verify CI auth works by running:

```bash
mcp-use whoami
```

before the first `mcp-use deploy` in the pipeline.

## Security notes

- `~/.mcp-use/config.json` contains an API key. Treat it as a secret — `chmod 600` if shared filesystems are involved.
- Don't commit `~/.mcp-use/config.json` to version control.
- Don't pass session tokens through shell history.
- Rotate via `mcp-use logout` then `mcp-use login` when in doubt.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Browser doesn't open | Headless / SSH session | Open the printed URL on a different device |
| `whoami` says not logged in but `~/.mcp-use/config.json` exists | Token expired or revoked | `mcp-use login` again |
| `deploy` 401s after login | Wrong org active | `mcp-use org list` and `mcp-use org switch` |

## See also

- `06-mcp-use-deploy.md` — what login enables
- `08-mcp-use-org-list-and-switch.md` — pick the active org after login
- `14-environment-variables.md` — CLI-side env vars including API-key auth
