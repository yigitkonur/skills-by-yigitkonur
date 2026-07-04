# make-local-template — wiring `make local` into a project

Goal: a `make local` target that takes the project from "nothing running" to "public `.ts.net` URL printed" with verified rungs along the way, and a `make local-down` that tears it down safely.

The pattern below assumes the project ships a small `Makefile` and wraps the skill's two scripts. The scripts live at `~/.claude/skills/run-tailscale-funnel/scripts/`. If the skill might not be installed on every developer's machine (CI runners, fresh clones), copy the scripts into the project under `scripts/funnel-up.sh` and `scripts/funnel-down.sh` and reference those.

## The Makefile target

```makefile
# Skill location — adjust if scripts are vendored locally.
SKILL_ROOT  ?= $(HOME)/.claude/skills/run-tailscale-funnel

# Where the local app listens. Override per-project: `make local LOCAL_PORT=3000`.
LOCAL_PORT  ?= 4321

# Which Funnel slot to use. Override if 10000 is taken: `make local FUNNEL_PORT=8443`.
# Valid values: 443, 8443, 10000.
FUNNEL_PORT ?= 10000

.PHONY: local local-down

local: ## Expose the local server at a public .ts.net URL via Tailscale Funnel
	@bash $(SKILL_ROOT)/scripts/funnel-up.sh $(LOCAL_PORT) $(FUNNEL_PORT)

local-down: ## Tear down only this project's Funnel mapping
	@bash $(SKILL_ROOT)/scripts/funnel-down.sh $(FUNNEL_PORT)
```

Drop this into the project's `Makefile`. If a `Makefile` already exists, append. If the user uses a different recipe-runner (`just`, `task`), the shape is the same — invoke the two scripts with the two arguments.

## How to start the backend so the Make target works

`make local` does not start the backend — it only sets up Funnel. The backend must already be listening on `127.0.0.1:$(LOCAL_PORT)` before you invoke `make local`.

For a static build:

```bash
# In one terminal — build then serve the static output
npm run build
cd dist && python3 -m http.server 4321 --bind 127.0.0.1
```

For a dev server (which means you also need to set `allowedHosts` — see `backend-host-validation.md`):

```bash
# In one terminal — Astro dev
astro dev --port 4321 --host 127.0.0.1
```

Then in another terminal:

```bash
make local
```

The script prints:

```
[funnel-up] preflight passed
[funnel-up] funnel slot 10000 free
[funnel-up] mapping :10000 → 127.0.0.1:4321
[funnel-up] rung 1 (auth DNS) ✓
[funnel-up] rung 2 (ingress curl) ✓
[funnel-up] public URL → https://macmini.tail2fcc55.ts.net:10000/
```

If any rung fails, the script exits non-zero with the troubleshooting hint specific to that rung.

## Why the two-script split

`scripts/funnel-up.sh` does the preflight, the bind check (just verifies, doesn't start the app), the slot check, the mapping, and the three-rung verification. It is idempotent — running it twice in a row doesn't break anything; if the mapping already points at the right target, it skips.

`scripts/funnel-down.sh` removes one specific port mapping. It refuses to act unless the port matches what `funnel-up.sh` last set up (state lives at `/tmp/tailscale-funnel-state-$(uid)-<port>.txt`). This is the safety against running `make local-down` and tearing down someone else's mapping.

Neither script ever runs `reset`.

## When the backend isn't started yet

If `funnel-up.sh` runs while `127.0.0.1:<port>` is empty, it warns:

```
[funnel-up] WARNING: nothing listening on 127.0.0.1:4321 — Funnel will return 502 until the backend starts
```

But continues — the Funnel mapping itself is valid even with no backend, and the user might intend to start the backend afterwards. The 502 will clear automatically once the backend comes up. No action required.

## Persistence across reboots

`tailscale funnel --bg` (which the script uses) makes the mapping persistent across Tailscale daemon restarts and reboots. The URL stays live indefinitely until `make local-down` (or manual `tailscale funnel --https=<port> off`) tears it down.

This is the right default for personal-grade public sharing. If the user wants the mapping ephemeral (auto-cleanup on exit), wrap the `make local` call in a shell with a trap:

```bash
make local && trap 'make local-down' EXIT
```

Or, in scripts, the cleaner shape:

```bash
make local
trap 'make local-down' EXIT
# ... work that needs the public URL ...
```

## Picking the right Funnel slot per project

If the user runs multiple `make local` projects, only one can use each slot (`443`, `8443`, `10000`). Pattern:

```makefile
# project-a/Makefile
FUNNEL_PORT ?= 10000

# project-b/Makefile
FUNNEL_PORT ?= 8443
```

This way `make local` in either project doesn't collide. The skill's `funnel-up.sh` will refuse to overwrite a mapping it didn't create — if a project hits a slot another project owns, the user gets an explicit error and the choice to override or pick a different slot.

## CI integration

The same script runs in CI for jobs that need a public URL (browser-test-against-built-site, screenshot regression). Provide an Tailscale auth key with funnel-eligible nodeAttr to the CI environment. The script does not assume an interactive user — exits cleanly on failure and prints the URL on success.

```yaml
# example: GitHub Actions step
- name: Tailscale connect
  uses: tailscale/github-action@v3
  with:
    authkey: ${{ secrets.TAILSCALE_AUTHKEY }}
    tags: tag:ci

- name: Expose local server
  run: |
    npm run build
    cd dist && python3 -m http.server 4321 --bind 127.0.0.1 &
    bash scripts/funnel-up.sh 4321 10000  # vendored copy of the skill script
```

(Use the skill's scripts vendored into the repo for CI — depending on a global install means CI runners need the skill installed too.)

## What the Make target does NOT do

- It does not start the backend. The user does that.
- It does not change which port the backend listens on. The user picks it; the user passes it in.
- It does not enable Funnel at the tailnet level. The user grants `funnel` nodeAttr in the admin console once per tailnet.
- It does not install `/etc/resolver/<tailnet>.ts.net`. The script detects whether DNS resolves correctly and tells the user to run the install if not — see `macos-dns-fixup.md`.

These are deliberate. Funnel exposes to the public internet — automation should not silently install new system-level resolvers or grant new ACLs.
