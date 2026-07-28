# Avrea CLI auth and portability (`avr` 0.1.6)

Read this when account selection, configuration paths, environment variables,
direnv/worktrees, CI portability, or output behavior could change what `avr`
actually does. This file is pinned to the released Avrea CLI 0.1.6.

Pinned release identity:

- package: `avr-cli`
- executable: `avr`
- released version: `0.1.6`
- release tag: `v0.1.6`
- source SHA: `d1c368547a8ca31fad2ec0513c6a2cfc33e3cb80`

## Identity and installation

| Property | Verified value |
|---|---|
| Package | `avr-cli` |
| Primary executable | `avr` |
| Compatibility executable | `avr-cli` |
| `avrea` executable | not installed |
| Installed version in research env | `0.1.6` |
| Publish/install manager in research env | `pipx` |

Start with:

```bash
command -v avr && avr --version
```

If `avr` is missing or on a different version, do not trust version-sensitive
examples below without rechecking the release tag and local `--help` output.

## Configuration storage

Credential/config state lives in:

```text
$AVR_CONFIG_DIR/hosts.json
```

Otherwise path resolution is:

1. `AVR_CONFIG_DIR`
2. `$XDG_CONFIG_HOME/avrea`
3. `~/.config/avrea`

On macOS, the CLI still defaults to the Linux-style config path unless
`AVR_MACOS_NATIVE_PATHS=1` is set. The local hosts file is written with mode
`0600`; keep it out of repos and artifacts.

## Resolution precedence

### Host

```text
AVR_HOST
→ hosts.json default_host
→ https://api.avrea.com
```

### Token

```text
AVR_TOKEN
→ stored token for the resolved host
```

### Organization

```text
explicit --org
→ AVR_ORG
→ stored default_org for the resolved host
→ auto-select only when membership contains exactly one org
```

### Repository

```text
explicit --repo
→ AVR_REPO
→ git remote named origin
```

Only a remote named `origin` is auto-detected. If a checkout has no `origin`,
pass `--repo`, set `AVR_REPO`, or rename a remote. Never assume a worktree or
fork checkout resolves to the intended repository automatically.

## Environment variables

| Variable | Purpose |
|---|---|
| `AVR_HOST` | One-shot API endpoint override |
| `AVR_TOKEN` | Noninteractive token; overrides stored token |
| `AVR_ORG` | Default organization override |
| `AVR_REPO` | Default repository override |
| `AVR_BROWSER` | Preferred browser for login/`--web` |
| `AVR_PAGER` | Preferred pager; empty disables |
| `AVR_LINKS` | `0` disables OSC 8 links |
| `AVR_DEBUG` | `api` or truthy value enables API request logging |
| `AVR_PROMPT_DISABLED` | Disables interactive prompts |
| `AVR_CONFIG_DIR` | Alternate credential/config directory |
| `AVR_MACOS_NATIVE_PATHS` | Use native macOS config paths when `1` |
| `NO_COLOR` | Disable ANSI color |
| `XDG_CONFIG_HOME` | Parent for default Avrea config directory |
| `PAGER`, `LESS`, `BROWSER` | Standard pager/browser fallback |

Important caveat: `AVR_PROMPT_DISABLED=1` is **not** a mutation blocker. It
only prevents interactive prompts. A destructive command with `--yes` still
executes.

## Direnv, worktrees, and account switching

Repository-local `.envrc` files can switch Avrea accounts by exporting
`AVR_CONFIG_DIR`. This is useful, but only when explicitly intended.

Safe pattern:

```bash
export AVR_CONFIG_DIR="$HOME/.config/avrea-<scope>"
export AVR_ORG="my-org"
```

Rules:

- Treat `.envrc` as part of the operational environment. Read it before
  assuming which account `avr` will use.
- Keep tokens out of `.envrc`; store them in the corresponding `hosts.json`
  or inject `AVR_TOKEN` in CI.
- Worktrees may inherit the parent repository's `.envrc` expectations but not
  necessarily its prepared config directory. Verify with `avr auth status` in
  the worktree itself.
- For high-impact commands, prefer explicit `--org` and `--repo` even if the
  environment seems correct.

## CI portability

In CI or ephemeral automation:

1. Set `AVR_TOKEN` explicitly.
2. Set `AVR_ORG` and `AVR_REPO` explicitly.
3. Optionally point `AVR_CONFIG_DIR` to a temporary directory if any commands
   need local config writes.
4. Disable color and paging (`NO_COLOR=1`, `AVR_PAGER=''`).
5. Do not rely on browser flows, git auto-detection, or stored local defaults.

A reproducible noninteractive preflight:

```bash
export NO_COLOR=1
export AVR_PAGER=''
export AVR_TOKEN='***'
export AVR_ORG='my-org'
export AVR_REPO='owner/repo'
command -v avr && avr --version
avr auth status --json host,default_org,email
avr health --json status
```

Never use `avr auth status --show-token` in CI logs.

## Output behavior in scripts

- `--json '?'` lists fields without guessing.
- `--json '*'` returns the full documented projection.
- `-q/--jq` requires `--json` and uses the system `jq`.
- On a non-TTY, list output becomes tab-separated text, and watch output
  becomes NDJSON.
- `--web` opens a browser and is therefore unsuitable for CI automation.
- `AVR_PAGER=''` or `--no-pager` prevents interactive paging.
- `AVR_LINKS=0` disables OSC 8 links when terminal control sequences would be
  noisy or unsupported.
- `AVR_DEBUG=api` is useful for request diagnosis but can expose URLs and query
  parameters in logs; do not leave it enabled in shared transcripts.

## Authentication safety

- `avr auth status` is safe.
- `avr auth status --show-token` exposes the full token — treat it as a secret
  leak, not a convenience.
- `auth login` and `auth switch` change future command targeting; re-check the
  resolved host/org after either one.
- `auth logout` clears local credentials even if server-side revocation warns.

## Portability limits of this reference

This file documents the **released** CLI surface. It does not guarantee:

- that upstream `main` matches 0.1.6,
- that undocumented API fields remain available,
- that another environment has the same binary/package installation path,
- that a repository without `origin` or without the expected `.envrc` chooses
  the right target automatically.

The reference is therefore a starting point and a guard against silent target
changes, not permission to skip a preflight.

## Sources

- Release docs index: https://docs.avrea.com/cli/reference/ (accessed 2026-07-28)
- GitHub release tag: https://github.com/avrea-com/cli/releases/tag/v0.1.6 (accessed 2026-07-28)
- Release source tag: https://github.com/avrea-com/cli/tree/v0.1.6 (accessed 2026-07-28)
- Verified locally against installed `avr` 0.1.6 (2026-07-28)
