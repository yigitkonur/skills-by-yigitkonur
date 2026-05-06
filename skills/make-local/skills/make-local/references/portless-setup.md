# Portless setup

[portless](https://github.com/vercel-labs/portless) replaces port numbers with stable named `.localhost` URLs on a real local cert. Default for `make local`.

## Install

**Pin via project devDependency** (preferred — every contributor gets the same version):

```bash
npm install -D portless
```

Then `npx portless` runs the project's pinned binary. No global install drift.

## Configure

`portless.json` at repo root:

```json
{ "name": "PROJECT_NAME" }
```

URL becomes `https://PROJECT_NAME.localhost`. Change `name` → restart → URL changes.

## First-run sudo

On first run on a fresh machine, portless does two privileged operations:

1. **Trust the local CA** — generates a CA, adds to system keychain. macOS sudo dialog. One-time.
2. **Bind port 443** — needed for HTTPS. macOS sudo dialog. One-time per reboot (then cached).

After both prompts succeed, subsequent runs are silent.

## How it picks the upstream port

Portless sets `PORT` env to a random port in 4000-4999. Most frameworks (Next.js, Express, Nuxt) respect that. For frameworks that ignore `PORT` (Vite, Astro, React Router), portless auto-injects `--port` + `--host` flags.

## Worktree behavior

In a git worktree, the URL becomes `https://<worktree>.<project>.localhost` automatically. Lets you have multiple branches running side-by-side without port juggling.

## Reset

```bash
npx portless clean   # removes state, trust entry, hosts block
npx portless prune   # kills orphaned dev servers from crashed sessions
```

## Detecting first run for the banner

Portless writes state to one of:
- `~/.portless/state.json`
- `~/Library/Application Support/portless/state.json`

The Makefile banner detects absence and warns about incoming sudo prompts:

```sh
@if [ ! -d $$HOME/.portless ] && [ ! -d "$$HOME/Library/Application Support/portless" ]; then \
  printf "first run on this machine — sudo prompts incoming for cert + :443\n"; \
fi
```

## Caveats

- Portless is pre-1.0. State directory format may change between versions; pinning via package.json prevents surprise.
- `*.localhost` is loopback per RFC 6761 → does NOT work cross-device. For phones/tablets, route to `make tunnel`.
- Some browser extensions (corporate VPN clients, ad blockers) interfere with `*.localhost` resolution. Switch off, or use `make local-lan`.
