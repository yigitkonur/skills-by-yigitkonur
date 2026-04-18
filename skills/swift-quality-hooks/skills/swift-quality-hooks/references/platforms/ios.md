# Platform: iOS

iOS shares the entire SwiftLint + SwiftFormat stage of the hook with macOS. Only the **typecheck stage destination** changes. The biggest practical question is **simulator vs device destination**.

## Hook configuration

Same `.githooks/pre-commit` and configs as macOS. SwiftLint and SwiftFormat are platform-agnostic — they don't care that the target is iOS.

## Typecheck stage: simulator vs device

| Destination | Pros | Cons | Recommended for |
|---|---|---|---|
| `generic/platform=iOS Simulator` | No code-signing config; works without provisioning profiles; simulator runtime preinstalled on `macos-15` runners | Slightly slower than device build | **Default for pre-commit hooks** |
| `generic/platform=iOS` | Marginally faster; matches release-build flags | Code-signing must be disabled (`CODE_SIGNING_ALLOWED=NO`) or hook fails on machines without team certs | CI-only; skip in pre-commit |

## In `scripts/swift-typecheck.sh`

```bash
SWIFT_HOOK_PLATFORM=iOS
# auto-translates to:
# DESTINATION="generic/platform=iOS Simulator"
```

## Typical typecheck command

```bash
xcodebuild build \
  -scheme YourApp \
  -destination "generic/platform=iOS Simulator" \
  -configuration Debug \
  -derivedDataPath /tmp/swift-hook-build \
  -clonedSourcePackagesDirPath .spm-cache \
  -parallelizeTargets \
  -skipMacroValidation \
  -skipPackagePluginValidation \
  ONLY_ACTIVE_ARCH=YES \
  CODE_SIGNING_ALLOWED=NO \
  CODE_SIGNING_REQUIRED=NO \
  -quiet
```

## Speed expectations

- Incremental typecheck on a typical (~30k LOC) iOS app: **5-15 seconds** with warm derived-data
- First-time typecheck: 60-180 seconds depending on dependency graph
- iOS targets that pull in Mapbox/Firebase/Realm typically dominate the typecheck time — those native dependencies don't recompile per change but do load slowly

## Known issues

- **Code-signing in pre-commit:** Always pass `CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO`. Without these, machines without provisioning profiles or expired certs fail every commit. Pre-commit isn't building for distribution — signing is irrelevant.
- **Xcode 15+ User Script Sandboxing:** Affects build-phase SwiftLint, not pre-commit hooks. Pre-commit hooks run outside the Xcode build sandbox.
- **Macro validation prompts:** First-time builds with macros (swift-syntax, OpenAPIKit, etc.) block on a "Trust & Enable" GUI prompt. The hook passes `-skipMacroValidation` and `-skipPackagePluginValidation` to bypass — accept the security tradeoff for hook speed.

## CI considerations

GitHub Actions `macos-15` runners ship the iOS Simulator runtime preinstalled. Reliable. No special setup needed beyond `xcode-select -s /Applications/Xcode_<ver>.app` if pinning a specific Xcode version.

## Pure SPM iOS package

If your library targets iOS via `Package.swift`:

```bash
# swift build --triple is unsupported for Apple non-host platforms (apple/swift-package-manager#6571)
# Use xcodebuild even for SPM packages:
xcodebuild -scheme MyLib \
  -destination "generic/platform=iOS Simulator" \
  -clonedSourcePackagesDirPath .spm-cache \
  build
```

## References

- `xcodebuild(1)` man page
- Apple build settings reference (`CODE_SIGNING_ALLOWED`, `ONLY_ACTIVE_ARCH`)
- mokacoding xcodebuild destination cheatsheet — https://mokacoding.com/blog/xcodebuild-destination-options/
- apple/swift-package-manager#6571 — `swift build --triple` unsupported
