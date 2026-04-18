# Troubleshooting

Top 10 issues encountered when installing or running the Swift quality hook, with verified workarounds.

## 1. `swiftlint: command not found` after Homebrew install (Apple Silicon)

**Symptom:** `swiftlint --version` works in Terminal but the hook prints "swiftlint not installed". Always on Apple Silicon Macs.

**Cause:** Apple Silicon Homebrew installs to `/opt/homebrew/bin/`. Some shells (especially when invoked via git hooks) don't have it on `$PATH`.

**Fix:** Add to `~/.zshrc` or `~/.bash_profile`:

```bash
export PATH="/opt/homebrew/bin:$PATH"
```

Or symlink:

```bash
sudo ln -s /opt/homebrew/bin/swiftlint /usr/local/bin/swiftlint
sudo ln -s /opt/homebrew/bin/swiftformat /usr/local/bin/swiftformat
```

Documented in realm/SwiftLint README §Apple Silicon.

## 2. Xcode 15+ build-phase SwiftLint fails with sandbox error

**Symptom:** `Sandbox: swiftlint(NNN) deny(1) file-read-data /path/to/swift/file` in Xcode build log. Affects build-phase SwiftLint, NOT pre-commit hooks.

**Cause:** Xcode 15 flipped `ENABLE_USER_SCRIPT_SANDBOXING` default to `YES`.

**Fix:** Set `ENABLE_USER_SCRIPT_SANDBOXING = NO` in the affected target's build settings. Pre-commit hooks are unaffected because they run outside the Xcode sandbox.

Tracking: realm/SwiftLint#5053. Also documented in realm/SwiftLint README §Consideration for Xcode 15.0.

## 3. Pre-commit hook silently doesn't run

**Symptom:** `git commit` succeeds without printing any "→ pre-commit:" output, even though `.githooks/pre-commit` exists.

**Cause:** `core.hooksPath` not set, OR git is using a different hooks path (e.g., a global one).

**Diagnosis:**

```bash
git config --get core.hooksPath        # should print: .githooks
ls -la .githooks/pre-commit            # should be -rwxr-xr-x (executable)
```

**Fix:** `make install-hooks` (or `git config core.hooksPath .githooks`). If a global `core.hooksPath` is masking the repo override, the local config wins (per git's config priority rules), but verify by running `.githooks/pre-commit` directly.

## 4. visionOS typecheck fails: "Unable to find a destination matching..."

**Symptom:** `SWIFT_HOOK_TYPECHECK=1` with `SWIFT_HOOK_PLATFORM=visionOS` fails with destination-not-found error.

**Cause:** visionOS Simulator runtime not installed. Common on fresh Xcode installs and on `macos-15` GitHub Actions runners (intermittent — issues #11504, #12592).

**Fix:**

```bash
# Verify
xcrun simctl list runtimes | grep -i vision

# Install
sudo xcodebuild -downloadPlatform visionOS
```

If you can't install (CI without sudo), skip visionOS in the pre-commit matrix and check it CI-side only.

## 5. xcodebuild typecheck hangs forever on first run

**Symptom:** `bash scripts/swift-typecheck.sh` runs indefinitely on first invocation.

**Cause:** A swift-syntax-based macro or SPM Build Tool Plugin needs the "Trust & Enable" GUI prompt. Headless processes (including pre-commit hooks) hang waiting for the user to click.

**Fix:** The script already passes `-skipMacroValidation -skipPackagePluginValidation`. If it still hangs, the issue is a pre-script-arg cache state — open the project in Xcode once and click through the trust prompts manually, then retry the hook.

## 6. SwiftFormat keeps "fixing" code SwiftLint then complains about

**Symptom:** Endless loop — SwiftFormat rewrites a file, SwiftLint flags the result, you reformat, etc.

**Cause:** SwiftLint has rules enabled that SwiftFormat disagrees with. Common culprits: `opening_brace`, `trailing_comma`, `vertical_parameter_alignment_on_call`, `statement_position`.

**Fix:** Add to `.swiftlint.yml`:

```yaml
disabled_rules:
  - opening_brace
  - trailing_comma
  - vertical_parameter_alignment_on_call
  - statement_position
```

The skill's template `.swiftlint.yml` already has these disabled. If you customized your config, restore them.

## 7. Hook is too slow (>5s on staged files)

**Symptom:** Commit-time hook takes longer than expected on small staged sets.

**Cause:** Likely one of:
- `swiftlint analyze` rules accidentally enabled (these need a full compiler log)
- SwiftLint cache disabled or wrong path
- `SWIFT_HOOK_TYPECHECK=1` accidentally enabled (the typecheck stage is the slow one)

**Diagnosis:**

```bash
# Time each stage individually
time swiftlint lint --strict <staged_file.swift>
time swiftformat --lint <staged_file.swift>
time bash scripts/check-quality.sh
echo "TYPECHECK enabled? ${SWIFT_HOOK_TYPECHECK:-not set}"
```

**Fix:** Disable analyzer-only rules (`unused_import`, `unused_declaration`, etc.) from the pre-commit config — run them in CI instead. Verify SwiftLint cache: `ls ~/Library/Caches/SwiftLint/`. Set `unset SWIFT_HOOK_TYPECHECK` if you want fast hook.

## 8. `swiftlint: warning: While loading configuration...` repeated forever

**Symptom:** SwiftLint prints a config-load warning on every invocation.

**Cause:** Misnamed config key, deprecated rule name, or YAML syntax error in `.swiftlint.yml`.

**Fix:**

```bash
swiftlint lint --quiet 2>&1 | head -10    # surface the actual config error
```

Common renames in 0.63+: `redundant_self_in_closure` → `redundant_self`. Check the SwiftLint CHANGELOG for the version range you're upgrading across.

## 9. iOS typecheck fails: `errSecInternalComponent` / signing-related

**Symptom:** xcodebuild fails with codesign-related error (`errSecInternalComponent`, `Code Sign error`, etc.).

**Cause:** The iOS device destination requires code signing. Pre-commit hooks shouldn't need signing.

**Fix:** Use the simulator destination (default in the skill's script): `generic/platform=iOS Simulator`. And ensure the script passes `CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO` (it does by default).

## 10. SwiftLint Build Tool Plugin warnings missing in Xcode 16.3+

**Symptom:** `SwiftLintBuildToolPlugin` warnings don't appear in the Xcode Issue Navigator.

**Cause:** Known regression in Xcode 16.3 (realm/SwiftLint#6041, #6042).

**Fix:** Use the pre-commit hook (this skill's pattern) instead of the Build Tool Plugin. The hook is more reliable and works across all Xcode versions.

## Reset everything (nuclear option)

If the hook state is so confused that you want to start over:

```bash
# Remove repo hook config
git config --unset core.hooksPath || true

# Remove generated hook + scripts
rm -f .githooks/pre-commit scripts/swift-typecheck.sh scripts/check-quality.sh

# (Optional) remove configs
rm -f .swiftlint.yml .swiftformat .swiftlint-baseline.json

# Re-run the skill's install operation
```

## References

- realm/SwiftLint README — Apple Silicon, Xcode 15 sandbox
- realm/SwiftLint#5053 — Xcode 15 sandbox
- realm/SwiftLint#6041 / #6042 — Build Tool Plugin issues on Xcode 16.3
- realm/SwiftLint#5597 — baseline config consistency
- realm/SwiftLint#6511 — baseline doesn't fail on fixed violations
- actions/runner-images#11504, #12592, #10559 — visionOS sim availability gaps
