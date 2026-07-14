# Token setup: get it, store it, make it permanent (Linux + macOS)

Use this the first time you touch a Coolify Cloud API or CLI operation. Almost every failure early in a session traces back to a missing, wrong-scope, or non-persistent token. Do this once, correctly, and the rest of the skill just works.

## Step 0: is a token already available?

Check before asking the user for anything:

```bash
# already in this shell?
[ -n "${COOLIFY_CLOUD_API_TOKEN:-}" ] && echo "token present in env"

# saved in the durable file?
[ -f "$HOME/.config/coolify-cloud.env" ] && echo "env file exists"

# CLI context configured?
coolify context list 2>/dev/null
```

If the env file exists, load it and verify:

```bash
source "$HOME/.config/coolify-cloud.env"
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $COOLIFY_CLOUD_API_TOKEN" \
  "${COOLIFY_BASE_URL:-https://app.coolify.io}/api/v1/servers"   # 200 = good, 401 = bad/expired
```

Only proceed to "ask the user" if there is genuinely no working token.

## Step 1: mint a token (user action — you cannot do this for them)

The token is a user-only secret. Ask the user to create one:

1. Go to `app.coolify.io` → **Keys & Tokens** (self-hosted: `<instance>/security/api-tokens`).
2. Create a token with **read + write + deploy** scope (root). Read-only cannot create services or deploy.
3. Copy it once (it is shown once).

Tell them plainly: connecting a server in the UI does **not** create an API token — these are separate credentials.

Prompt shape when you need it:

> I need a Coolify Cloud API token (read+write+deploy) from app.coolify.io → Keys & Tokens. Paste it and I'll store it securely at ~/.config/coolify-cloud.env (chmod 600) so you never have to paste it again.

## Step 2: store it durably (same file, both OSes)

Convention used across this skill: one env file, `chmod 600`, referenced — never inlined into scripts or compose.

```bash
mkdir -p "$HOME/.config"
umask 077
# Write the file WITHOUT the token appearing in shell history:
#   read it into a variable via a prompt, then write the file.
read -rs -p "Paste Coolify token: " CPA_TOKEN; echo
printf 'export COOLIFY_CLOUD_API_TOKEN=%s\n' "$CPA_TOKEN" >  "$HOME/.config/coolify-cloud.env"
printf 'export COOLIFY_BASE_URL=%s\n' "https://app.coolify.io" >> "$HOME/.config/coolify-cloud.env"
chmod 600 "$HOME/.config/coolify-cloud.env"
unset CPA_TOKEN
```

`scripts/setup-token.sh` does exactly this (idempotent: updates the token in place if the file already exists) and then verifies the token against the API.

## Step 3: make it load in every new shell (permanent)

Source the env file from the shell rc. Pick the file for the user's shell — this is the one cross-platform difference that bites people:

| Shell | rc file | Notes |
|---|---|---|
| zsh (macOS default since Catalina; common on Linux) | `~/.zshrc` | Default interactive shell on modern macOS. |
| bash (common Linux default) | `~/.bashrc` | On macOS, bash login shells read `~/.bash_profile`; source `~/.bashrc` from it if needed. |
| fish | `~/.config/fish/config.fish` | Use `set -x` / `bass`; the `export` file won't source directly. |

Add one guarded line (works for bash/zsh). Detect the rc file instead of hardcoding:

```bash
case "$(basename "${SHELL:-}")" in
  zsh)  RC="$HOME/.zshrc" ;;
  bash) RC="$HOME/.bashrc" ;;
  *)    RC="$HOME/.profile" ;;
esac
LINE='[ -f "$HOME/.config/coolify-cloud.env" ] && source "$HOME/.config/coolify-cloud.env"  # Coolify Cloud API token'
grep -qF "coolify-cloud.env" "$RC" 2>/dev/null || printf '%s\n' "$LINE" >> "$RC"
```

Then either open a new shell or `source "$RC"` in the current one.

## Step 4: configure the CLI context (optional but handy)

The CLI keeps its own token copy in its config file (see `cli-reference.md`). Point it at the same token:

```bash
source "$HOME/.config/coolify-cloud.env"
coolify context add cloud https://app.coolify.io "$COOLIFY_CLOUD_API_TOKEN"
coolify context verify        # expect: Connection / Auth / version OK
```

## Step 5: verify end to end

```bash
source "$HOME/.config/coolify-cloud.env"
curl -s -o /dev/null -w 'API: %{http_code}\n' -H "Authorization: Bearer $COOLIFY_CLOUD_API_TOKEN" \
  "$COOLIFY_BASE_URL/api/v1/servers"     # want: API: 200
coolify --context cloud context verify   # want: all checks pass
```

`200` + CLI verify pass = you are ready. `401` = wrong/expired/insufficient-scope token; re-mint with read+write+deploy.

## Security rules (do not skip)

- `chmod 600` the env file; never commit it or paste it into a repo, compose, or issue.
- Never echo the token to logs or chat. Mask when you must reference it (`abcd***`).
- Rotate by editing the env file and re-running `coolify context add`/token update; do not scatter copies.
- One durable source of truth (the env file). Scripts read `$COOLIFY_CLOUD_API_TOKEN`; they never contain the value.

## Rotating a token

The safest cross-platform rotation path is to re-run the setup helper; it overwrites the env file with `printf` rather than using `sed`, so tokens containing delimiter characters such as `|` are handled correctly:

```bash
scripts/setup-token.sh
source "$HOME/.config/coolify-cloud.env"
coolify context add cloud https://app.coolify.io "$COOLIFY_CLOUD_API_TOKEN" -f
```

Then verify with the Step 5 commands above.
