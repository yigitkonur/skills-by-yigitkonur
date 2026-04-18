---
name: swift-quality-hooks
description: Use skill if you are installing or configuring a Swift pre-commit hook with SwiftLint and SwiftFormat on a macOS, iOS, tvOS, watchOS, or visionOS project.
---

# Swift Quality Hooks

Install a fast (<1s on staged files), clean-code-suite git pre-commit hook for any Apple-platform Swift project. The hook runs SwiftLint `--strict` + SwiftFormat (or Apple's swift-format) `--lint` on staged `.swift` files only, with an opt-in xcodebuild typecheck stage gated by an environment variable.

This skill generalizes a battle-tested implementation that took a real ~50k LOC macOS app from **333 → 0 SwiftLint violations** (verified across 288 Swift files; hook E2E-tested across 12 scenarios). The same architecture applies to iOS / tvOS / watchOS / visionOS by swapping one xcodebuild `-destination` flag.

## When to use this skill

- User says any of: "set up Swift pre-commit hook", "swift code quality automation", "install SwiftLint hook", "swiftformat hook", "swift git hook", "Apple platform pre-commit", "ios/macos/tvos/watchos/visionos pre-commit lint"
- User has an Xcode project, Xcode workspace, or `Package.swift` and wants commit-time enforcement
- User asks to migrate from no hook → hook, or from `.git/hooks/` → `core.hooksPath` versioned hooks

## When NOT to use

- Generic "set up git hooks" requests with no Swift context → use a generic git-hooks skill
- "Configure SwiftLint inside Xcode build phase only" with no commit-time enforcement requested → SwiftLint docs cover that directly
- Non-Apple Swift (server-side Swift on Linux without Xcode) → adapt manually; the typecheck stage assumes xcodebuild

## Operations

This skill dispatches based on what the user is asking for:

| User intent | Operation | What runs |
|---|---|---|
| "Set up the hook" / "install" / "add a pre-commit hook" | **install** | Detect platform + project type → write configs → install `.githooks/pre-commit` → wire `core.hooksPath` → verify |
| "Audit / analyze" / "check what's missing" / "do I need a hook" | **audit** | Inventory existing config files, hook state, tool versions; report what to add. No file writes. |
| "Verify / test the hook" / "make sure my hook works" | **verify** | Run hook with empty staged → expect 0; with bad staged → expect block; report results. No persistent changes. |
| "Update / refresh" / "bump versions" / "regenerate baseline" | **update** | Refresh tool versions, regenerate `.swiftlint-baseline.json`, sync rule additions from upstream releases |

Default to **install** if intent is ambiguous and no hook is currently installed. Default to **audit** if a hook already exists and the user hasn't said "reinstall".

## Workflow

### Step 0 — Verify tools exist (auto-resolve)

Both `swiftlint` and `swiftformat` (or `swift-format`) must be on `$PATH`. Apple Silicon Homebrew installs to `/opt/homebrew/bin/`; if the user's shell doesn't have it on PATH, the hook will silently degrade.

```bash
command -v swiftlint   || brew install swiftlint
command -v swiftformat || brew install swiftformat
xcrun --find xcodebuild >/dev/null   # Xcode CLT must be installed
```

If a tool is missing AND Homebrew is present, install it. If Homebrew is missing, ask the user before installing.

### Step 1 — Detect platform + project type

Run inside the repo root:

```bash
detect_project_type() {
  if   [ -f Package.swift ] && ! ls *.xcworkspace >/dev/null 2>&1 && ! ls *.xcodeproj >/dev/null 2>&1; then echo "spm"
  elif ls *.xcworkspace >/dev/null 2>&1; then echo "workspace"
  elif ls *.xcodeproj   >/dev/null 2>&1; then echo "xcodeproj"
  else echo "unknown"; fi
}
```

For platform: read `Package.swift` (look for `platforms:` array) or `xcodebuild -list -json` (look for the scheme's `SUPPORTED_PLATFORMS` build setting). If the user has stated the platform, trust them.

When uncertain, default to **macOS**. macOS is the only Apple platform that needs no simulator runtime, has no signing complications, and runs the fastest typecheck. The skill's defaults bias toward macOS-first elegance with platform-specific notes loaded on demand.

→ Per-platform details live in `references/platforms/<platform>.md`. Load only the platform you're actually configuring.

### Step 2 — Choose the formatter (decide once per repo)

```
Does the repo already have a `.swift-format` JSON file, OR is the team
already using Xcode 16's built-in formatter, OR is this destined for
swiftlang/ open-source publication?
├── YES → swift-format (Apple's formatter)
└── NO  → SwiftFormat (Nick Lockwood's; this skill's default)
```

**Default to SwiftFormat** for any new repo or any repo without an explicit signal toward swift-format. Justification: 4:1 community install share, faster on staged-files invocations, richer rule set, ships an official `.pre-commit-hooks.yaml`. Both formatters are platform-agnostic — neither cares whether the target is macOS, iOS, tvOS, watchOS, or visionOS.

→ Full decision criteria + per-formatter config templates: `references/configs/swiftformat-config.md`.

### Step 3 — Write the configs

Write three files at the repo root (skip any that already exist; ask before overwriting):

1. `.swiftlint.yml` — opt-in rules, custom rules, thresholds tuned to the realm/SwiftLint dogfood values
2. `.swiftformat` (or `.swift-format`) — formatter config aligned with SwiftLint's disabled_rules
3. `.swiftlint-baseline.json` — `[]` for greenfield, or generated via `swiftlint --write-baseline` for legacy code

→ Recommended `.swiftlint.yml`: `references/configs/swiftlint-config.md`
→ Recommended formatter config: `references/configs/swiftformat-config.md`
→ Baseline workflow for legacy code: `references/baseline-workflow.md`

### Step 4 — Install the hook

Write `.githooks/pre-commit` from the asset template, make it executable, and wire `core.hooksPath`:

```bash
mkdir -p .githooks
cp <skill-dir>/assets/githooks/pre-commit .githooks/pre-commit
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```

The hook runs against staged `.swift` files only. It runs in 4 stages, aborting on first failure:

1. **SwiftLint --strict** — every warning becomes a commit-blocking error
2. **SwiftFormat --lint** — fails if formatting would change any staged file
3. **(optional)** `scripts/check-quality.sh` — repo-side custom guardrail hook (the skill installs an empty stub the repo can fill in)
4. **(opt-in)** `scripts/swift-typecheck.sh` — gated by `SWIFT_HOOK_TYPECHECK=1`; runs `xcodebuild build` with the right per-platform `-destination`

CI auto-skips the hook (`$CI` check); CI pipelines should run the same checks via `make lint-all` or equivalent.

→ Full hook anatomy + `make install-hooks` / `uninstall-hooks` targets: `references/hook-architecture.md`
→ Opt-in typecheck stage with per-platform destinations: `references/typecheck-stage.md`

### Step 5 — Verify

Run the hook with no staged files (expect exit 0), then with a deliberately-failing staged Swift change (expect exit 1 + diagnostic). For new installs, also run `swiftlint lint` to surface any pre-existing violations the user should baseline or fix.

```bash
.githooks/pre-commit                                    # → exit 0 if no .swift staged
echo 'print("test")' >> SomeFile.swift && git add SomeFile.swift
.githooks/pre-commit                                    # → exit 1 with no_print_statements error
git reset HEAD SomeFile.swift && git checkout SomeFile.swift
```

## Decision rules

- **Ambiguous platform → macOS.** macOS-first elegance: no simulator, no signing, fastest typecheck. Per-platform refs are loaded only when the platform is known.
- **Ambiguous formatter choice → SwiftFormat (nicklockwood).** Default for community fit; offer `swift-format` as alternative when Apple-aligned signals are present.
- **Legacy codebase with many violations → baseline first, fix later.** Use `swiftlint --write-baseline .swiftlint-baseline.json` to lock in current debt; future PRs fail only on NEW violations.
- **Tools missing AND Homebrew present → auto-install.** Tools missing AND no Homebrew → ask before bootstrapping anything global.
- **Build broken (missing packages, dependency drift) → typecheck stage stays opt-in.** Never enable `SWIFT_HOOK_TYPECHECK=1` by default; document the env var for opt-in.
- **Hook conflicts with existing `.git/hooks/pre-commit` → migrate, don't merge.** Move the user's existing logic into `.githooks/pre-commit` (or a `scripts/check-quality.sh` they wire in) before flipping `core.hooksPath`.

## Hard guardrails

- **Never write to `.git/hooks/` directly.** Always use `.githooks/` + `git config core.hooksPath`. Versioned, shareable, survives clones.
- **Never enable the typecheck stage by default.** Apple-platform builds break transiently (package sync, missing visionOS sim runtime, expired certs). Hook must stay deterministic.
- **Never install global tools without confirmation.** `brew install swiftlint` requires sudo on first install on some Macs; ask first.
- **Never bypass the user's existing global git hooks path.** If `git config --global core.hooksPath` returns a value, warn the user that the repo override will mask it; offer an opt-out.
- **Never commit `.swiftlint-baseline.json` as `[]` and call it done on a legacy codebase.** Either run `swiftlint lint` first and ask the user how to handle pre-existing violations, or run `--write-baseline` and tell the user what was suppressed.
- **Never claim the typecheck works without verifying.** If `SWIFT_HOOK_TYPECHECK=1` is enabled, run the typecheck once during install verification — graceful skip on missing packages is a feature, but silent failure is a bug.

## Output contract

When asked to **install**, deliver:

1. Confirmation of detected platform + project type
2. List of files written (configs + hook + scripts) with one-line purpose each
3. Output of `git config --get core.hooksPath` proving install
4. Output of `.githooks/pre-commit` (with no staged files; should exit 0)
5. Pre-existing SwiftLint violation count (so the user knows what's already in baseline vs. what's new)

When asked to **audit**, deliver:

1. Tool availability matrix (swiftlint version, swiftformat/swift-format version, Xcode version)
2. Existing config inventory (which of `.swiftlint.yml`, `.swiftformat`, `.swiftlint-baseline.json`, `.githooks/pre-commit` exist; current `core.hooksPath`)
3. Recommended next steps (which configs to add, whether to install hook, whether to baseline)

When asked to **verify**, deliver:

1. Empty-staged test result
2. Bad-Swift-staged test result (lint should block)
3. Format-diff test result (format should block)
4. CI-skip test result (`CI=1 .githooks/pre-commit` should exit 0 silently)
5. Optional typecheck test if `SWIFT_HOOK_TYPECHECK=1` (skip if build is broken)

## Reference routing

Load only the references relevant to the current operation and platform.

### Configs (load when writing/tuning configs)

| File | Load when |
|---|---|
| `references/configs/swiftlint-config.md` | Writing or tuning `.swiftlint.yml` — full opt-in rule list, threshold values from realm/SwiftLint dogfood, custom rule patterns, baseline workflow |
| `references/configs/swiftformat-config.md` | Choosing formatter, writing `.swiftformat` or `.swift-format`, configuring SwiftLint disabled_rules to coexist |

### Platforms (load only the platform being configured)

| File | Load when |
|---|---|
| `references/platforms/macos.md` | macOS app, macOS framework, Catalyst — typecheck destination, no-signing-needed config |
| `references/platforms/ios.md` | iOS app, iOS framework — `generic/platform=iOS Simulator` vs device, signing, `CODE_SIGNING_ALLOWED=NO` |
| `references/platforms/tvos.md` | tvOS app — destination flag and known issues |
| `references/platforms/watchos.md` | watchOS app — pairing for `test` (not `build`), SPM XCTest unavailability |
| `references/platforms/visionos.md` | visionOS app — runtime gap warning (highest CI risk), download command |
| `references/platforms/multiplatform.md` | Project targets ≥2 Apple platforms — auto-detection, scheme matrix, multi-destination strategy |

### Mechanics (load when explaining or troubleshooting)

| File | Load when |
|---|---|
| `references/hook-architecture.md` | Explaining the 4-stage hook anatomy, `core.hooksPath` rationale, CI auto-skip pattern, `make install-hooks` integration |
| `references/typecheck-stage.md` | Setting up the opt-in xcodebuild typecheck stage; per-platform destination matrix; package-graph sanity check |
| `references/baseline-workflow.md` | Rolling out strict linting on a legacy codebase — `--write-baseline`, when to commit, how to retire the baseline |
| `references/troubleshooting.md` | Top 10 pitfalls — Xcode 15 sandbox, Apple Silicon PATH, visionOS sim missing, macro-validation prompts, build-tool-plugin silent on Xcode 16.3, etc. |

### Assets (copied into the user's repo, not loaded)

| Path | Purpose |
|---|---|
| `assets/githooks/pre-commit` | Template hook script — single source of truth for the 4-stage pipeline |
| `assets/swiftlint.yml` | Template `.swiftlint.yml` based on realm/SwiftLint's own values |
| `assets/swiftformat` | Template `.swiftformat` config |
| `assets/scripts/swift-typecheck.sh` | Opt-in xcodebuild typecheck script |
| `assets/Makefile.fragment` | Drop-in `install-hooks` / `uninstall-hooks` / `lint` / `lint-fix` / `format` / `lint-baseline` targets |

## Verification before completion

Before declaring the install successful, run all of:

- `git config --get core.hooksPath` returns `.githooks`
- `.githooks/pre-commit` is executable (`-rwxr-xr-x`)
- `swiftlint --version` and `swiftformat --version` print without error
- `.githooks/pre-commit` with no staged files exits 0 in <1s
- For verify operation: also confirm a deliberately-bad staged file is blocked

If any check fails, report the specific failure and stop — never claim done with broken state.

## Failure protocol

When a step fails, return structured intelligence:

1. **What was attempted** — the exact command run
2. **What happened** — the exit code and relevant stderr/stdout (trimmed)
3. **Why it likely failed** — best diagnosis (missing tool, broken build, sandbox issue)
4. **What to try next** — concrete remediation, or "needs user decision" with the question

Do not silently skip. Do not present a workaround as a solution without flagging the gap. If a per-platform typecheck destination is rejected by xcodebuild, report it; do not silently fall back to macOS.

## Sources

The skill is synthesized from:

- First-hand evidence: `~/dev/fast-talk` (3 commits — `c527623`, `84c41b5`, `53283f0`; 333 → 0 SwiftLint violations across 288 files)
- realm/SwiftLint repo + release notes (0.62.x – 0.64.0-rc.1)
- nicklockwood/SwiftFormat repo + Rules.md
- swiftlang/swift-format Configuration.md (`602.0.0`)
- Apple `xcodebuild(1)` man page (per-platform destination semantics)
- `actions/runner-images` issues #11504, #10559, #12541 (CI runner state)
- realm/SwiftLint issues #5053, #6041, #5597, #6511 (sandbox, plugin silent, baseline drift)
- 5 community skills downloaded via `skill-dl` — inherited mode-dispatch + language-detection patterns, avoided `prek` dependency and raw `.git/hooks/` writes

All non-trivial claims in the references include URLs accessed 2026-04-18.
