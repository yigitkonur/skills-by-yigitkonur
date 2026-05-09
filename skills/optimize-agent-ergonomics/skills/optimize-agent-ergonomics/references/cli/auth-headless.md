# cli/auth-headless.md

Agents run headless. A CLI whose only auth path is "open a browser and log in" cannot be driven by an agent. This file ranks auth patterns by agent-friendliness, defines env-var conventions, and covers the sandbox boundaries that determine which patterns work in CI vs on a developer machine.

## Auth pattern ranking

Listed best-to-worst for agent contexts. Pick the most agent-friendly one your security model allows.

### 1. API token via env var (best)

```bash
export MYTOOL_TOKEN="sk_live_..."
mytool create my-app
```

- Agent injects the env var once at session start.
- No file IO, no flags, no process-list exposure.
- Works identically in CI, in containers, in subprocess harnesses.

The CLI reads `MYTOOL_TOKEN` first in the credential chain. If set and valid, no other check runs.

### 2. Token via `--token-file=<path>`

```bash
mytool --token-file=/run/secrets/mytool create my-app
```

- File reads are auditable; rotation is "swap the file."
- Works with Kubernetes secrets, Docker secrets, systemd-creds.
- Avoids the env-var-leaks-into-child-processes problem (env vars propagate to every subprocess; file reads don't).
- Trade-off: needs a path in the runtime environment; one extra step.

### 3. Token via `--token-stdin`

```bash
echo "$TOKEN" | mytool --token-stdin create my-app
```

- Token never appears in `ps`, in logs, in env-var dumps.
- The most secure option for ad-hoc invocations; the agent pipes the token from a vault.
- Trade-off: every command run repeats the pipe; awkward for multi-command workflows.

### 4. Token via `--token=<value>` (acceptable, with warnings)

```bash
mytool --token=sk_live_xxx create my-app
```

- Visible in `ps -ef`. On a shared host, anyone can read it.
- Acceptable for one-off scripted runs where you trust the host. NOT acceptable in CI logs (the command line gets echoed by most CI runners).
- The CLI SHOULD print a warning to stderr: "warning: --token on command line is visible in process list; prefer --token-file or MYTOOL_TOKEN."

### 5. OS keyring

```bash
mytool auth login   # stores into Keychain / Secret Service / Credential Manager
mytool create my-app  # reads from keyring
```

- Works on a developer machine where the keyring is unlocked.
- Breaks in CI (no keyring), in containers (no keyring), in remote SSH (locked keyring).
- The agent can't predict whether the keyring is available; the CLI must fall back to env vars and fail gracefully when both are absent.

### 6. OAuth device flow (poor for agents)

```
mytool auth login
> Open https://mytool.dev/device in your browser
> Enter code: ABCD-1234
[CLI polls until the user completes the flow]
```

- Requires a browser. Agents don't have one.
- Works ONLY if a human is sitting at the terminal during the initial auth. Useful for first-time setup; useless for agent automation.
- The CLI should support device flow for human bootstrap AND env-var auth for subsequent agent runs. After the human logs in, the CLI persists a refresh token; agents read the refresh token from a file or vault.

### 7. OAuth web flow (worst)

```
mytool auth login
> Opening https://mytool.dev/oauth?...
[browser opens]
```

- Strictly worse than device flow: the CLI assumes a graphical environment exists.
- Almost never appropriate for an agent-ready CLI. If the auth provider only supports web flow, wrap it in a token-issuing service: the human authenticates once, gets a long-lived API token, the agent uses the token.

## Credential resolution chain

The CLI reads credentials in priority order. First match wins.

```
1. --token-stdin (if --token-stdin is passed, read entire stdin)
2. --token-file=<path>
3. --token=<value>
4. MYTOOL_TOKEN env var
5. Config file at ~/.config/mytool/config.toml: [auth] token=...
6. OS keyring (if available and unlocked)
7. OAuth refresh token (if a refresh_token file exists)
8. Fail with exit 4
```

The CLI MUST NOT prompt for credentials in non-TTY contexts. If steps 1–7 fail and stdin is not a TTY, fail with `error.code = "UNAUTHENTICATED"` and exit 4 — never block.

```python
def resolve_token():
    if args.token_stdin:
        return sys.stdin.read().strip()
    if args.token_file:
        return Path(args.token_file).read_text().strip()
    if args.token:
        return args.token
    if t := os.environ.get("MYTOOL_TOKEN"):
        return t
    if t := config_file_token():
        return t
    if t := keyring_token():
        return t
    if t := refresh_token_from_file():
        return t
    return None  # caller exits 4

token = resolve_token()
if not token:
    emit_error("UNAUTHENTICATED", "no credentials found", "run `mytool auth login` or set MYTOOL_TOKEN")
    sys.exit(4)
```

## Env var conventions

A CLI's env vars MUST be uniformly prefixed and documented. Pick a prefix on day one and never change it.

| Pattern | Example | Use |
|---|---|---|
| `<TOOL>_TOKEN` | `MYTOOL_TOKEN` | Primary credential |
| `<TOOL>_HOST` | `MYTOOL_HOST` | Override the API endpoint |
| `<TOOL>_CONFIG_DIR` | `MYTOOL_CONFIG_DIR` | Override the config directory |
| `<TOOL>_PROFILE` | `MYTOOL_PROFILE` | Active profile name in a multi-profile config |
| `<TOOL>_DEBUG` | `MYTOOL_DEBUG=1` | Enable extra stderr diagnostics |
| `<TOOL>_NO_TELEMETRY` | `MYTOOL_NO_TELEMETRY=1` | Opt out of telemetry |

Do NOT use generic names like `TOKEN` or `HOST` — they collide with other tools. The prefix is the namespace.

For workspace-style tools (multiple targets), prefix the var with the workspace:

```bash
export MYTOOL_PROD_TOKEN="..."
export MYTOOL_STAGING_TOKEN="..."
mytool --profile=prod create my-app
```

## "No auth required for read-only" pattern

Some CLIs offer a public-read mode that doesn't need a token. Useful for tools that wrap a public API or have a tier with anonymous access.

```bash
# Anonymous; only public resources visible.
mytool list --public

# Authenticated; full access.
MYTOOL_TOKEN=... mytool list
```

When implemented, document in `--help`: "this command works without authentication; pass `--token` or set `MYTOOL_TOKEN` for full access."

The agent uses `mytool list --public` for discovery and switches to authenticated mode only when it needs to act.

## Sandbox boundaries

What's safe in CI vs what's safe on a developer machine differs. The CLI should not assume.

| Concern | Developer machine | CI / container | Notes |
|---|---|---|---|
| Reading from OS keyring | Yes | No | Containers have no keyring |
| Writing to OS keyring | Yes (with consent) | No | Persisting tokens in CI is leaky |
| Reading `~/.config/mytool/config` | Yes | Yes if mounted | CI must mount the config or use env vars |
| Logging the auth method (not value) | OK | OK | "auth: env var" is fine; "auth: sk_live_xxx" is not |
| Logging the token value | NEVER | NEVER | Even in `--verbose`. Redact unconditionally. |
| Writing tokens to disk | OK with permissions (0600) | NEVER write new tokens; only read injected ones | CI's filesystem may be archived |

The redaction rule: `--verbose` and any debug logger MUST redact tokens. Treat any string matching `^(sk|sklive|sk-live|tok|tk|api[-_]key|bearer)[_-]\w{16,}$` (or the CLI's specific format) as sensitive. Print as `MYTOOL_TOKEN=sk_live_••••••••` (last 4 chars are sometimes acceptable for debugging; redact the rest).

## Logging vs persisting

A CLI may log "I authenticated using X method"; it must NOT log the token itself.

```python
log("auth resolved from env var MYTOOL_TOKEN")  # OK
log(f"using token {token}")                     # NEVER
log(f"using token ending in ...{token[-4:]}")   # OK for debug; still avoid in production logs
```

If the CLI persists tokens to disk (e.g., after `mytool auth login`), write to `~/.config/mytool/credentials` with mode 0600 and the directory mode 0700. On Windows, use the user's local app data folder with appropriate ACLs. Document the path in `mytool auth status`.

## Token refresh and expiration

If the auth uses access tokens with expiry, the CLI MUST handle refresh transparently:

```python
def get_authenticated_client():
    token, source = resolve_token_with_source()
    if is_expired(token) and source != "stdin":  # can't refresh stdin tokens
        new_token = refresh_with_refresh_token()
        if new_token:
            persist_token(new_token, source)
            token = new_token
        else:
            emit_error("TOKEN_EXPIRED", "token expired and refresh failed", "run `mytool auth login`")
            sys.exit(4)
    return Client(token)
```

The agent expects the CLI to handle refresh under the hood. If refresh fails (refresh token also expired), the CLI exits 4 with `error.code = "TOKEN_EXPIRED"`. The agent's policy is to escalate to a human caller — agents cannot complete a fresh OAuth flow.

## The "auth check" preflight

Every CLI MUST provide a fast auth-check command. Conventional name: `whoami` or `auth status`.

```bash
mytool whoami --json
```

Success:

```json
{
  "ok": true,
  "result": {
    "user": "alice@example.com",
    "auth_method": "env_var",
    "token_expires_at": "2026-06-01T00:00:00Z",
    "scopes": ["read", "write"]
  },
  "schema_version": "1"
}
```

Failure:

```json
{
  "ok": false,
  "error": {
    "code": "UNAUTHENTICATED",
    "message": "no credentials found",
    "next_action": "set MYTOOL_TOKEN or run `mytool auth login`"
  },
  "schema_version": "1"
}
```

Exit codes: 0 if authenticated, 4 if not. The agent runs `whoami` once at the start of a session and branches: success → proceed; failure → escalate.

The preflight MUST be a network call (or at minimum, a token-validity check), not just "is the env var set?". A CLI that reports `ok=true` because `MYTOOL_TOKEN` exists but the token is expired is broken.

## Code samples

### Python — token loading with fallback chain

```python
import os, sys
from pathlib import Path

class AuthError(Exception):
    pass

def resolve_token() -> tuple[str, str]:
    """Returns (token, source). Raises AuthError if no credential is found."""
    # 1. --token-stdin
    if "--token-stdin" in sys.argv:
        token = sys.stdin.read().strip()
        if token:
            return token, "stdin"

    # 2. --token-file
    for arg in sys.argv:
        if arg.startswith("--token-file="):
            path = arg.split("=", 1)[1]
            return Path(path).read_text().strip(), "token_file"

    # 3. --token
    for arg in sys.argv:
        if arg.startswith("--token="):
            return arg.split("=", 1)[1], "token_flag"

    # 4. env var
    if t := os.environ.get("MYTOOL_TOKEN"):
        return t, "env_var"

    # 5. config file
    config_path = Path(os.environ.get("MYTOOL_CONFIG_DIR", "~/.config/mytool")).expanduser() / "config.toml"
    if config_path.exists():
        import tomllib
        with config_path.open("rb") as f:
            cfg = tomllib.load(f)
        if t := cfg.get("auth", {}).get("token"):
            return t, "config_file"

    # 6. keyring (best-effort; skip if unavailable)
    try:
        import keyring
        if t := keyring.get_password("mytool", "default"):
            return t, "keyring"
    except (ImportError, Exception):
        pass

    raise AuthError("no credentials found")

# usage
try:
    token, source = resolve_token()
    log(f"auth resolved from {source}")
except AuthError as e:
    emit_error("UNAUTHENTICATED", str(e), "set MYTOOL_TOKEN or run `mytool auth login`")
    sys.exit(4)
```

### Bash — env-var-or-fail preflight

```bash
preflight_auth() {
    if [ -n "${MYTOOL_TOKEN:-}" ]; then return 0; fi
    if [ -f "${HOME}/.config/mytool/credentials" ]; then return 0; fi

    cat >&2 <<EOF
error: no credentials found.
  set MYTOOL_TOKEN, or
  pass --token-file=<path>, or
  run \`mytool auth login\` interactively.
EOF
    printf '{"ok":false,"error":{"code":"UNAUTHENTICATED","message":"no credentials","next_action":"set MYTOOL_TOKEN"},"schema_version":"1"}\n'
    exit 4
}

preflight_auth
# proceed with the actual command
```

## Anti-patterns

- **OAuth web flow with no fallback.** Agent can't open a browser; CLI hangs. Fix: support env-var auth.
- **Token leaks to logs.** `--verbose` prints the request URL with the bearer token. Fix: redact unconditionally.
- **Token argument visible in `ps`.** Use stdin or env var instead.
- **Different env-var names for different CLI versions.** `MYTOOL_API_KEY` vs `MYTOOL_TOKEN` — agent has to guess. Fix: pick one and never change.
- **No `whoami` command.** Agent can't preflight; finds out it's unauthenticated when the first real command fails. Fix: provide a fast auth-check.
- **`whoami` returns 0 even when the token is expired.** Agent skips re-auth, then fails downstream. Fix: validate against the server (or check expiry locally).
- **Persisting tokens with mode 0644.** World-readable on the user's machine. Fix: 0600 on the file, 0700 on the dir.
- **CLI prompts for password in non-TTY.** Hangs. Fix: detect non-TTY, exit 4 instead.

## Cross-references

- `flags-and-discovery.md` — `--token`, `--token-file`, `--token-stdin`, `--no-input`, `--config` flags.
- `exit-codes.md` — exit code 4 for auth failures.
- `output-envelope.md` — the `UNAUTHENTICATED` and `TOKEN_EXPIRED` error codes.
- `subprocess-harness.md` — how the harness escalates exit-4 failures.
- `../common/error-strategy.md` — cross-surface principles for transient vs permanent.
