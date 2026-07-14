# Makefile macbook — Scenario G ship pipeline

Scenario G is "build on this dev box, ship to a remote MacBook over SSH, kill-then-launch, verify the process is running." The skill generates `make ship` (alias `make macbook`) and `make ship-status`. Ship is build → preflight → graceful-quit → rsync to staging → atomic swap → launch → verify, in that exact order. Out of scope: code-signing automation (sign + notarize), Gatekeeper bypass for unsigned apps (a manual first-launch click is the right UX — anything else fights the OS), `.app` bundle source-tree manipulation. The skill ships what `make build` produced; what's inside the bundle is the build target's problem.

## Knobs

Every knob has a defaultable value. The agent asks the user only when no default can be derived from the project.

```makefile
REMOTE_HOST   ?= macbook                                       # SSH alias (~/.ssh/config Host block)
APP_NAME      ?= $(shell defaults read "$(LOCAL_BUNDLE)/Contents/Info" CFBundleName 2>/dev/null || basename "$(LOCAL_BUNDLE)" .app)
INSTALL_PATH  ?= /Applications/$(APP_NAME).app                 # default /Applications; ~/Applications is a knob
LOCAL_BUNDLE  ?= ./build/Release/$(APP_NAME).app               # Xcode default; Electron is ./out/$(APP_NAME)-darwin-*/$(APP_NAME).app
```

| Knob | Default | How to derive | Ask user only if |
|---|---|---|---|
| `REMOTE_HOST` | `macbook` | Look in `~/.ssh/config` for `Host macbook` | No `Host macbook` block exists or user wants a different alias |
| `APP_NAME` | derived | `defaults read $(LOCAL_BUNDLE)/Contents/Info CFBundleName` for built bundles; for Xcode pre-build, parse `*.xcodeproj/project.pbxproj` for the target name | Bundle isn't built yet AND no Xcode project name resolves |
| `INSTALL_PATH` | `/Applications/$(APP_NAME).app` | Convention | User wants per-user dir (`~/Applications/$(APP_NAME).app`) |
| `LOCAL_BUNDLE` | `./build/Release/$(APP_NAME).app` (Xcode) or `./out/$(APP_NAME)-darwin-*/$(APP_NAME).app` (Electron) | `xcodebuild -showBuildSettings \| awk '/BUILT_PRODUCTS_DIR/ {print $$3}'` for Xcode; `package.json` `build.directories.output` (or default `out/`) for Electron-Builder/Forge | Neither path resolves and the project has a custom build dir |

`?=` keeps every knob overridable per-invocation: `make ship REMOTE_HOST=mini APP_NAME="My App"`.

## The `make ship` target

The full chain. The user runs `make ship` (or `make macbook` — both alias to the same recipe). Each helper is its own `_`-prefixed target so individual steps can be invoked and re-tested in isolation.

```makefile
.PHONY: ship macbook ship-status \
        _preflight-mac _remote-quit _remote-stage _remote-swap _remote-launch _remote-verify

ship: build _preflight-mac _remote-quit _remote-stage _remote-swap _remote-launch _remote-verify ## build, ship to $(REMOTE_HOST), launch, verify
	@printf "$(G)✓ shipped $(APP_NAME) to $(REMOTE_HOST):$(INSTALL_PATH)$(Z)\n"

macbook: ship ## alias for make ship

ship-status: ## report PID of $(APP_NAME) on $(REMOTE_HOST), or "not running"
	@pid=$$(ssh -o BatchMode=yes -o ConnectTimeout=5 $(REMOTE_HOST) pgrep -x "$(APP_NAME)" 2>/dev/null || true); \
	if [ -n "$$pid" ]; then \
	  printf "$(G)✓ $(APP_NAME) running on $(REMOTE_HOST) (pid $$pid)$(Z)\n"; \
	else \
	  printf "$(D)$(APP_NAME) not running on $(REMOTE_HOST)$(Z)\n"; \
	fi
```

Order matters. `build` first because rsync needs a bundle on disk. Preflights second because there's no point building locally if the remote is unreachable — but we lose nothing by building first, and the user gets a useful artifact even if SSH fails. `_remote-quit` before `_remote-stage` because file handles in the running app block rsync (the macOS kernel doesn't unlink open files, so the staging mv would silently fail to clean up). `_remote-swap` before `_remote-launch` because LaunchServices caches the bundle path — launching before the swap launches the OLD bundle. Verify last; everything else is plumbing.

## Helper 1 — `_preflight-mac`

Three independent checks. Fails fast and loudly.

```makefile
_preflight-mac:
	@# 1) SSH alias resolves to something other than the literal alias
	@host=$$(ssh -G $(REMOTE_HOST) | awk '/^hostname / {print $$2}'); \
	if [ "$$host" = "$(REMOTE_HOST)" ]; then \
	  printf "$(R)ssh alias $(REMOTE_HOST) does not resolve. Add a Host block to ~/.ssh/config.$(Z)\n"; \
	  exit 1; \
	fi
	@# 2) Reachability — non-interactive, no host-key prompt
	@ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new $(REMOTE_HOST) true \
	  || { printf "$(R)$(REMOTE_HOST) unreachable (BatchMode ssh failed in 5s)$(Z)\n"; exit 1; }
	@# 3) Local bundle exists; build it if not
	@[ -d "$(LOCAL_BUNDLE)" ] || $(MAKE) build
	@printf "$(D)preflight ok: alias→$$(ssh -G $(REMOTE_HOST) | awk '/^hostname / {print $$2}'), bundle=$(LOCAL_BUNDLE)$(Z)\n"
```

Why each piece:

- `ssh -G $(REMOTE_HOST) | awk '/^hostname / {print $$2}'` — `ssh -G` prints the resolved config without connecting. If `~/.ssh/config` has no matching `Host` block, ssh echoes the alias back as the hostname; comparing the output to the literal alias detects that case without trying to connect.
- `BatchMode=yes` — refuses any prompt (password, keyboard-interactive). In Make recipes, a prompt would block forever; BatchMode turns the failure into a non-zero exit immediately.
- `ConnectTimeout=5` — bound the failure mode. SSH's default is the OS TCP timeout (>30s). Five seconds is enough for a healthy LAN and gives up fast on a sleeping Mac.
- `StrictHostKeyChecking=accept-new` — first-time hosts are trusted automatically (TOFU). Unknown hosts that match a saved fingerprint still fail. Avoids the interactive "are you sure" prompt while keeping MITM detection on subsequent connections.
- `$(MAKE) build` — build is a separate scenario-aware target. We don't inline `xcodebuild` or `electron-builder` here — the build target owns that knowledge.

## Helper 2 — `_remote-quit`

Graceful first, escalate only if needed. Never lead with `kill -9`.

```makefile
_remote-quit:
	@ssh -o BatchMode=yes $(REMOTE_HOST) bash -se <<'EOS'
	APP="$(APP_NAME)"
	if pgrep -x "$$APP" >/dev/null; then
	  osascript -e "tell application \"$$APP\" to quit" || true
	  for i in 1 2 3 4 5; do
	    pgrep -x "$$APP" >/dev/null || break
	    sleep 1
	  done
	  if pgrep -x "$$APP" >/dev/null; then
	    pkill -x "$$APP" || true
	  fi
	fi
	EOS
```

The escalation ladder:

1. `osascript -e 'tell application "<APP>" to quit'` — sends an Apple Event. The app gets a chance to flush state, save windows, prompt the user about unsaved work (but in our case the user isn't there — apps with unsaved work hang on the prompt; that's fine, the loop catches it and pkills).
2. Poll `pgrep -x "<APP>"` for up to 5 seconds. `pgrep -x` matches the exact process name; `-x` is critical — without it `Mail` matches `Mailmate`, etc.
3. `pkill -x "<APP>"` — sends SIGTERM (still graceful by Unix conventions, but no Apple Event, so an unsaved-state prompt won't block us).
4. We do NOT escalate to `pkill -9 -x` here. If SIGTERM doesn't kill it within the rsync window the app's hung; the agent should surface that to the user, not paper over it.

The `<<'EOS'` heredoc uses single quotes so the inner `$$APP` is interpreted by the *remote* shell after Make expands `$(APP_NAME)`. Standard Make-double-dollar idiom for ssh-runs-bash patterns.

## Helper 3 — `_remote-stage`

Rsync to a `.app.new` staging path. Never `scp` an `.app` bundle.

```makefile
_remote-stage:
	@rsync -avzE --delete \
	  --exclude '.DS_Store' \
	  -e 'ssh -o BatchMode=yes' \
	  $(LOCAL_BUNDLE)/ $(REMOTE_HOST):$(INSTALL_PATH).new/
```

Flag meanings (macOS rsync, `man rsync` 2026):

| Flag | Why |
|---|---|
| `-a` | Archive: preserves permissions, timestamps, symlinks, group/owner. `.app` bundles contain symlinks (`Contents/MacOS/<binary>` → versioned binary in some Frameworks); `-a` keeps them. |
| `-v` | Verbose. Make output is otherwise silent during rsync; verbose gives the user a heartbeat. |
| `-z` | Compress in-flight. SSH's own compression interacts oddly; rsync's is well-tuned for the file mix in `.app` bundles (lots of small text in `Contents/Resources/`). |
| `-E` | **Macos extended attributes.** This is the irreplaceable flag for `.app` bundles — code-signing metadata, quarantine xattrs, resource forks all live in extended attributes. Without `-E`, the bundle arrives stripped, and macOS treats it as "modified" or "broken." |
| `--delete` | Mirror semantics — files removed locally get removed on the remote. `.app` bundles include build artifacts that change names between releases (`Contents/Frameworks/Foo.framework/Versions/A/Foo.dylib`); without `--delete` the staging dir accretes stale files. |
| `--exclude '.DS_Store'` | Finder writes `.DS_Store` whenever it visits a folder. Excluding stops needless transfers and prevents accidental remote-Finder state propagation. |
| `-e 'ssh -o BatchMode=yes'` | Force non-interactive SSH for the rsync transport. Same reason as `_preflight-mac`. |

Trailing slash on `$(LOCAL_BUNDLE)/` is required — rsync's "copy contents of, not directory itself" syntax. Without it, you get `$(INSTALL_PATH).new/$(APP_NAME).app/...` (one nesting level deeper than intended).

**NEVER `scp` for `.app` bundles.** `scp -r` doesn't preserve extended attributes (no `-E` equivalent). The bundle arrives and macOS thinks it's been tampered with — Gatekeeper rejects it with "App is damaged" even when the source was perfectly fine. This is the #1 root cause of "I shipped my app but the remote Mac says it's damaged."

## Helper 4 — `_remote-swap`

Atomic rename on the remote. APFS guarantees `mv` is atomic *on the same volume*.

```makefile
_remote-swap:
	@ssh -o BatchMode=yes $(REMOTE_HOST) bash -se <<EOS
	set -e
	if [ -d $(INSTALL_PATH) ]; then mv $(INSTALL_PATH) $(INSTALL_PATH).old; fi
	mv $(INSTALL_PATH).new $(INSTALL_PATH)
	rm -rf $(INSTALL_PATH).old
	EOS
```

The sequence:

1. **Sidestep the live bundle:** if `$(INSTALL_PATH)` exists, rename it to `.old`. This is the atomic step — APFS rename is one inode-table update on the same volume.
2. **Promote the staged bundle:** rename `.app.new` to the canonical path. Also one atomic rename.
3. **Garbage-collect the old:** `rm -rf .app.old`. Not atomic, doesn't matter — the canonical path is already the new bundle.

If anything fails after step 1, the remote is in a recoverable state (old bundle is at `.app.old`, can be moved back manually). The `set -e` ensures failures don't silently pass through. The `<<EOS` (no quotes) lets `$(INSTALL_PATH)` expand at Make-time so the remote shell sees a literal path.

**Same-volume rule.** `mv` between volumes is implemented as `cp` + `unlink`, which is *not* atomic — a process opening the path during the swap window can see a half-copied bundle. Keep `$(INSTALL_PATH).new` in the same volume as `$(INSTALL_PATH)`. With `/Applications/<App>.app` and `/Applications/<App>.app.new` that's automatic. Only fails if the user has set `INSTALL_PATH` to a different volume than the staging path; the skill should detect this with `df $(INSTALL_PATH).new $(INSTALL_PATH)` if it gets paranoid.

## Helper 5 — `_remote-launch`

Hand off to LaunchServices. Detached, non-blocking.

```makefile
_remote-launch:
	@ssh -o BatchMode=yes $(REMOTE_HOST) open $(INSTALL_PATH)
```

`open` is the macOS LaunchServices CLI. It registers the bundle (so `pgrep -x` finds it), launches it via the LaunchServices database (so the app gets the right environment, Dock icon, Apple Event registration), and *returns immediately* — the launched app is detached from the SSH session. No `nohup`/`disown` ceremony required.

Alternatives considered:

- `open -a "$(APP_NAME)"` — looks up the app by name in the LaunchServices DB, not by path. Works, but if the user has multiple copies (one in `/Applications/`, one in `~/Applications/`) it's nondeterministic which gets launched. Pass the path, not the name.
- `open -n $(INSTALL_PATH)` — `-n` forces a new instance even if one's running. We've already killed the running instance in `_remote-quit`, so `-n` is redundant.
- Direct `<bundle>/Contents/MacOS/<binary>` — bypasses LaunchServices. Loses the Dock icon, doesn't get registered, won't match Gatekeeper expectations. Don't.

## Helper 6 — `_remote-verify`

Confirm the launch took. `pgrep -x` is the rung-2 verification per `verification-ladder.md`.

```makefile
_remote-verify:
	@sleep 2
	@if ssh -o BatchMode=yes $(REMOTE_HOST) pgrep -x "$(APP_NAME)" >/dev/null; then \
	  printf "$(G)✓ $(APP_NAME) running on $(REMOTE_HOST)$(Z)\n"; \
	else \
	  printf "$(R)✗ $(APP_NAME) NOT running on $(REMOTE_HOST). Last 30s of system log:$(Z)\n"; \
	  ssh -o BatchMode=yes $(REMOTE_HOST) log show --last 30s --predicate 'process == "$(APP_NAME)"' --style compact || true; \
	  exit 1; \
	fi
```

The `sleep 2` is the floor — most apps register a process within ~500ms of `open`, but Electron apps with main-process bootstrap and cold-start Xcode bundles can take longer. Two seconds is generous without being annoying. If the user's app is slower (heavy first-launch initialization, cold-loaded ML models), `sleep` is overridable: `make ship VERIFY_SLEEP=5` if the skill exposed that knob — currently it does not.

On failure, dump the last 30 seconds of unified logs filtered to the app's process. `log show --last 30s --predicate 'process == "<name>"' --style compact` is the macOS Console equivalent: it gives the user the same trace they'd see in `Console.app` filtered by process. `--style compact` strips one log line per row.

## Quarantine xattr — when to strip, when not

`xattr -dr com.apple.quarantine $(INSTALL_PATH)` recursively removes the `com.apple.quarantine` extended attribute. **Only run this if the user reports a Gatekeeper "damaged" error AND `xattr -p com.apple.quarantine $(INSTALL_PATH)` confirms the attribute is present.**

When the quarantine attribute gets attached:

- Safari downloads → quarantine set
- `curl -O` (with NSURLDownload backend) → may set
- Browser-downloaded `.dmg` extracted to `/Applications/` → set on the bundle
- Files copied from another quarantined source → inherited

When it does NOT get attached:

- `rsync` over SSH → never sets quarantine
- `scp` → never sets quarantine
- Local `cp` from a non-quarantined source → not set
- `xcodebuild` output → not set

Therefore: **rsync-shipped bundles will not have the quarantine attribute.** Stripping it is a no-op and clutters the recipe. The skill does not include a default `xattr -dr` step. If a user reports a Gatekeeper error, the diagnostic flow is:

```bash
ssh $(REMOTE_HOST) xattr -p com.apple.quarantine $(INSTALL_PATH)
# Empty output → not present → quarantine isn't the cause; investigate code-signing instead.
# Non-empty → present → ssh $(REMOTE_HOST) xattr -dr com.apple.quarantine $(INSTALL_PATH)
```

## Code-signing and Gatekeeper — out of scope

Unsigned `.app` bundles trigger a Gatekeeper prompt on first launch ("Apple cannot check `<App>` for malicious software"). The user clicks "Open" once, and the prompt does not return for that bundle. This is the **correct** behavior — Apple intentionally makes blanket bypass hard.

What the skill does NOT do:

- `spctl --add $(INSTALL_PATH)` — adds a Gatekeeper exception. Requires admin (`sudo`), which the SSH session generally doesn't have.
- `spctl --master-disable` — disables Gatekeeper system-wide. Catastrophic security regression. The skill never suggests this.
- Programmatic auto-click of the Gatekeeper dialog — TCC won't allow it, and even if it did, this defeats the purpose of Gatekeeper.

The right answer for repeated unsigned-app shipping is **sign + notarize**. That's a build-time concern, not a ship-time concern. The skill defers this to the project's build pipeline (Xcode signing, `electron-builder` notarization config, etc.). For now, the user clicks "Open" once per release.

## Common failure modes

| Symptom | Root cause | Fix |
|---|---|---|
| "The application <App> is damaged and can't be opened" | `scp` was used (extended attributes lost) OR a `.app.new`-but-not-`.app` partial state OR genuine xattr corruption | Re-run `make ship` with the rsync path; if persistent, `xattr -p com.apple.quarantine` to confirm it's not quarantine |
| "Bad CPU type in executable" | Intel binary on Apple Silicon (or vice versa) | `lipo -info <bundle>/Contents/MacOS/<bin>` to inspect; rebuild with the right target arch (`arch -arm64 xcodebuild` etc.) |
| Rsync "vanished" warnings during transfer | Files were modified or open during the transfer; usually because graceful-quit didn't actually quit the app | Confirm `_remote-quit` ran; check for child processes (`ssh $(REMOTE_HOST) pgrep -fl "<App>"`) |
| `make ship` succeeds but app doesn't open | LaunchServices DB stale or bundle path mismatch | `ssh $(REMOTE_HOST) /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user`; re-run ship |
| Cross-volume mv "is not atomic" warning | `INSTALL_PATH` and `INSTALL_PATH.new` are on different volumes (e.g., `/Volumes/External/...`) | Move staging path to same volume as install path |
| `pgrep -x` returns no PID after `sleep 2` but app is visibly running | Process name in `pgrep` doesn't exact-match `CFBundleName` (rare; happens with apps that exec into a child binary with a different name) | Override `APP_NAME` to the actual process name; or use `pgrep -if "<App>"` for fuzzy match (less precise) |

## DO-NOT list

- **DO NOT use `scp` for `.app` bundles.** `scp -r` strips extended attributes; the bundle arrives "damaged" per Gatekeeper. Use `rsync -aE` only.
- **DO NOT lead with `kill -9` / `pkill -9`.** Apple Event quit first, then SIGTERM via `pkill -x`, then surface the failure if both fail. Never pre-emptively SIGKILL.
- **DO NOT strip `com.apple.quarantine` blindly.** Check it's present first (`xattr -p`). Stripping it on bundles that never had it is a wasted recipe step that hides what's actually wrong when Gatekeeper complains.
- **DO NOT try to programmatically approve Gatekeeper for unsigned apps.** The first-launch click is the correct UX; sign + notarize for proper automation.
- **DO NOT cross-volume `mv` for the atomic swap.** Keep `INSTALL_PATH.new` and `INSTALL_PATH` on the same volume. APFS atomicity only holds within one volume.
- **DO NOT skip `BatchMode=yes` on SSH.** Without it, the recipe can hang on a password or fingerprint prompt indefinitely.
- **DO NOT skip the `-E` flag on rsync.** No `-E` means no extended attributes, which means a "damaged" bundle on the remote even when the local bundle was fine.
- **DO NOT launch via `<bundle>/Contents/MacOS/<binary>`.** Use `open` so LaunchServices registers the bundle properly.
- **DO NOT `pkill -9 -x` the app as a generic recovery step.** A hung graceful-quit signals an actual problem (unsaved state prompt, hung subprocess); surface it instead of papering over it.
- **DO NOT modify `~/.ssh/config` from the recipe.** If the alias is missing, the preflight refuses and tells the user to add the Host block. SSH config is the user's domain.

## What this file does NOT cover

| Topic | Reference |
|---|---|
| Universal preamble (`SHELL`, `.SHELLFLAGS`, ANSI palette) | `makefile-base.md` |
| Port-hygiene helpers | `port-hygiene.md` |
| Verification rungs (rung 2 is what `_remote-verify` claims) | `verification-ladder.md` |
| AGENTS.md `## Make targets` section for Scenario G | `agents-md-update.md` |
| GitHub Actions wiring (Scenario G is local-build-only — no CI step) | `ci-cd-workflow.md` |
| Mac-app *development* standards (SwiftUI patterns, Xcode targets) | out of scope — this skill only scaffolds Make targets |
