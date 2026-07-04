# Platform: visionOS

**visionOS is the highest-risk platform for the typecheck stage.** The simulator runtime is NOT preinstalled on every Xcode version, was removed from `macos-14` GitHub runners in Sept 2024 (#10559), and has had repeated availability gaps on `macos-15` (#11504, #12592). Treat `SWIFT_HOOK_TYPECHECK=1` for visionOS as **optional even when enabled** — the hook script gracefully skips if the runtime is missing.

## Hook configuration

Same `.githooks/pre-commit` and configs as macOS/iOS. SwiftLint/SwiftFormat unchanged.

## Typecheck stage configuration

```bash
SWIFT_HOOK_PLATFORM=visionOS
# auto-translates to:
# DESTINATION="generic/platform=visionOS Simulator"
```

Both `visionOS` (PascalCase) and `visionos` (lowercase) appear in current Apple docs and GitHub Actions issues — `visionOS` (PascalCase) is the safer default and mirrors the other platform spellings.

## Verify the simulator runtime is installed

Before enabling visionOS typecheck, confirm:

```bash
xcrun simctl list runtimes | grep -i vision
# Expected: "visionOS 1.x" or "visionOS 2.x" with a runtime path
```

If empty, install with:

```bash
sudo xcodebuild -downloadPlatform visionOS
```

This is a multi-GB download. Don't run it as part of the hook — install manually, once.

## Typical typecheck command

```bash
xcodebuild build \
  -scheme YourVisionApp \
  -destination "generic/platform=visionOS Simulator" \
  -configuration Debug \
  -derivedDataPath /tmp/swift-hook-build \
  -clonedSourcePackagesDirPath .spm-cache \
  -parallelizeTargets \
  -skipMacroValidation \
  -skipPackagePluginValidation \
  ONLY_ACTIVE_ARCH=YES \
  CODE_SIGNING_ALLOWED=NO \
  -quiet
```

## Speed expectations

- Incremental typecheck: **10-25 seconds** — heavier than iOS due to RealityKit/SwiftUI 3D toolchain weight
- First-time typecheck: 90-300 seconds — the toolchain itself loads slowly

## Known issues

- **visionOS Simulator runtime missing**: most common visionOS hook failure. The script's package-graph sanity check covers missing local packages but NOT missing Apple SDK runtimes. The hook will surface the xcodebuild error (`Unable to find a destination matching the provided destination specifier`). If users hit this often, document the `xcodebuild -downloadPlatform visionOS` command in the project README.
- **Xcode version drift on CI**: actions/runner-images#11504 (March 2025) reported the visionOS sim missing from Xcode 16.2 on `macos-15`. Workarounds: pin to a known-good Xcode + verify runtime, or skip visionOS in CI's typecheck matrix.
- **macOS 14 runner deprecation**: visionOS was removed from `macos-14` images in September 2024. Use `macos-15` or later for visionOS CI.

## CI considerations

The most fragile platform for CI typecheck. Strongly consider one of:

1. **Skip visionOS in pre-commit; check it only in CI** with explicit runtime install:
   ```yaml
   - name: Install visionOS Simulator
     run: sudo xcodebuild -downloadPlatform visionOS
   - name: Typecheck
     run: SWIFT_HOOK_PLATFORM=visionOS bash scripts/swift-typecheck.sh
   ```
2. **Use a marketplace action** like `muukii/actions-xcode-install-simulator` to manage the install.
3. **Skip pre-commit typecheck entirely for visionOS** (`SWIFT_HOOK_TYPECHECK` stays unset); rely on CI for the typecheck signal.

## Pure SPM visionOS package

```bash
xcodebuild -scheme MyVisionLib \
  -destination "generic/platform=visionOS Simulator" \
  -clonedSourcePackagesDirPath .spm-cache \
  build
```

## References

- `xcodebuild(1)` man page (note: older mirrors don't list visionOS — refer to current Xcode docs)
- `actions/runner-images#11504` — visionOS sim missing on macos-15
- `actions/runner-images#10559` — visionOS removed from macos-14 (Sept 2024)
- `actions/runner-images#12592` — visionOS availability gaps
- `XcodesOrg/xcodes#368` — `xcodebuild -downloadPlatform` discussion
