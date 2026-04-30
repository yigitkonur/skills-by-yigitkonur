# Setup, Auth, Workspaces

First-run setup, authentication, profile/workspace switching, doctor, and shell completions for `linear-cli`.

## First-run wizard

```bash
linear-cli setup       # guided onboarding (auth + default team + completions)
linear-cli doctor      # check config + connectivity
linear-cli doctor --fix
```

## Authentication

Two methods. Both work per-profile and per-workspace.

### API key (simplest, agent-friendly)

```bash
# Pipe in (don't echo a secret to argv / shell history)
printf '%s\n' "$LINEAR_API_KEY" | linear-cli config set-key

# Interactive prompt
linear-cli auth login

# Store in OS keyring (requires --features secure-storage build)
linear-cli auth login --secure

# Highest-priority override at runtime
export LINEAR_API_KEY=lin_api_xxx
```

Get an API key at <https://linear.app/settings/api>.

### OAuth 2.0 (Authorization Code + PKCE)

```bash
linear-cli auth oauth                    # opens browser
linear-cli auth oauth --secure           # store tokens in OS keyring
linear-cli auth oauth --client-id ID     # custom OAuth app
linear-cli auth status --validate --output json  # show auth type and validate API access
linear-cli auth revoke                   # revoke tokens
linear-cli auth logout                   # remove credentials
```

The callback server binds `127.0.0.1` only and validates `state` plus PKCE before token exchange. Tokens auto-refresh.

### Auth priority

`LINEAR_API_KEY` env var > OS keyring > OAuth tokens > config file API key.

For agent loops, prefer `LINEAR_API_KEY` from the environment — the same key works across containers, CI, and local shells without keyring prompts.

### macOS keyring caveats

`--secure` works best on signed release binaries (`cargo binstall linear-cli`). Locally rebuilt binaries can trigger repeated Keychain prompts and may fail readback verification. If that happens, fall back to `linear-cli auth oauth` (no keyring) or `LINEAR_API_KEY`.

## Workspaces and profiles

Multiple Linear workspaces, named profiles, switch on the fly.

```bash
linear-cli config workspace-add work KEY      # add a workspace profile
linear-cli config workspace-list
linear-cli config workspace-switch work
linear-cli config workspace-current
linear-cli config workspace-remove work

# Per-invocation override
linear-cli --profile work i list

# Session override
export LINEAR_CLI_PROFILE=work
```

## Config file

Stored at `~/.config/linear-cli/config.toml` (Linux/macOS) or `%APPDATA%\linear-cli\config.toml` (Windows).

```bash
linear-cli config show
linear-cli config get default_team
linear-cli config set default_team ENG
```

## Diagnostics

```bash
linear-cli doctor                # connectivity, auth, config sanity
linear-cli doctor --fix          # auto-remediate common issues
linear-cli cache status          # cache hit rate / size
linear-cli cache clear           # nuke cache
linear-cli update                # self-update the binary
linear-cli update --check        # report current vs latest, no install
linear-cli agent                 # print agent-focused capability summary
```

## Environment variables

| Variable | Purpose |
|---|---|
| `LINEAR_API_KEY` | API key; highest-priority auth source. |
| `LINEAR_CLI_OUTPUT` | Default output format for the session (`json`, `ndjson`, etc.). |
| `LINEAR_CLI_PROFILE` | Default workspace profile name. |
| `LINEAR_CLI_YES` | Auto-confirm all prompts (`--yes` everywhere). |
| `LINEAR_CLI_NO_PAGER` | Disable auto-paging through `less`. |
| `LINEAR_CLI_TRUST_PAGER` | Trust an absolute `PAGER` path you set explicitly. |

For agent runs, the canonical opener:

```bash
export LINEAR_CLI_OUTPUT=json
export LINEAR_CLI_NO_PAGER=1
# Leave LINEAR_CLI_YES unset until a specific destructive command needs it.
linear-cli auth status --validate --output json  # gate writes on exit code 0
linear-cli config workspace-current              # confirm intended profile/workspace
```

## Shell completions

### Static (command names + flags)

```bash
linear-cli completions static bash       > ~/.bash_completion.d/linear-cli
linear-cli completions static zsh        > ~/.zfunc/_linear-cli
linear-cli completions static fish       > ~/.config/fish/completions/linear-cli.fish
linear-cli completions static powershell > linear-cli.ps1
```

Legacy alias: `linear-cli config completions <shell>` also works.

### Dynamic (queries Linear API for team / project / issue / status names)

```bash
linear-cli completions dynamic bash       >> ~/.bashrc
linear-cli completions dynamic zsh        >> ~/.zshrc
linear-cli completions dynamic fish       >> ~/.config/fish/completions/linear-cli.fish
linear-cli completions dynamic powershell >> $PROFILE
```

## First-time setup checklist (agent)

```bash
# 1. Confirm binary
linear-cli --version

# 2. Confirm or set auth, then validate live API access
linear-cli auth status --validate --output json || {
  linear-cli auth login
  linear-cli auth status --validate --output json
}

# 3. Confirm workspace
linear-cli config workspace-current
linear-cli u me --output json       # who am I in this workspace?

# 4. Confirm default team, or resolve the first visible team key
TEAM=$(linear-cli config get default_team 2>/dev/null)
if [ -z "$TEAM" ]; then
  TEAM=$(linear-cli t list --output json --compact --fields key | jq -r '.[0].key // empty')
fi
[ -n "$TEAM" ] || { echo "No team key found; run linear-cli t list and choose one"; exit 1; }

# 5. Confirm we can read
linear-cli i list --mine --limit 1 --output json --compact

# 6. Confirm we can write (dry-run)
linear-cli i create "agent-smoke-test" -t "$TEAM" --dry-run
```

If any step fails, route to `troubleshooting.md`.
