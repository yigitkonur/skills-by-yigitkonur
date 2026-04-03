# Tooling & Project Setup

Production-ready configurations derived from analysis of realm/SwiftLint (84/100, 19.5k stars), nicklockwood/SwiftFormat (78/100), peripheryapp/periphery (76/100), tuist/tuist (81/100), and mas-cli/mas (72/100, 6 lint tools in CI).

---

## 1. SwiftLint

**Preferred installation: Swift Package Manager plugin** (no global binary required).

### Package.swift (SPM plugin)
```swift
// Add to Package.swift dependencies:
.package(url: "https://github.com/realm/SwiftLint", from: "0.57.0"),

// Add to target:
.plugin(name: "SwiftLintBuildToolPlugin", package: "SwiftLint")
```

### Xcode Build Phase (alternative)
```bash
# "Run Script" build phase — runs on every build
if which swiftlint > /dev/null; then
  swiftlint
else
  echo "warning: SwiftLint not installed, download from https://github.com/realm/SwiftLint"
fi
```

### Recommended `.swiftlint.yml` (production-ready, full config in section 11)

Key principles: enable strict rules, disable noisy ones, exclude generated code and third-party.

---

## 2. SwiftFormat

**Installation (Homebrew):**
```bash
rtk brew install swiftformat
```

**Xcode Extension:** Install SwiftFormat for Xcode from the App Store for Format on Save.

### Pre-commit hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
git diff --cached --name-only --diff-filter=ACM | grep "\.swift$" | while read file; do
  swiftformat "$file" --quiet
  git add "$file"
done
```

**SwiftFormat vs swift-format (Apple):**
- `SwiftFormat` (nicklockwood): 100+ opinionated rules, highly configurable, community standard
- `swift-format` (Apple/swiftlang): fewer rules, tied to Swift toolchain, used in Apple repos
- **Recommendation**: Use SwiftFormat for team projects; use swift-format only if contributing to Apple OSS

Full `.swiftformat` config in section 12.

---

## 3. Periphery (Dead Code Detection)

**Installation:**
```bash
rtk brew install peripheryapp/periphery/periphery
```

**Basic scan:**
```bash
rtk periphery scan --project MyApp.xcodeproj --schemes MyApp --targets MyApp
```

**SPM-only project:**
```bash
rtk periphery scan
```

### `.periphery.yml`
```yaml
project: MyApp.xcodeproj
schemes:
  - MyApp
targets:
  - MyApp
index_exclude:
  - "**/*.generated.swift"
  - "**/Generated/**"
  - "**/Pods/**"
retain_objc_accessible: true
retain_public: false         # set true for frameworks/libraries
clean_build: false
```

**Excluding false positives:**
```swift
// In code — suppress specific warnings:
// periphery:ignore
private func unusedButDynamicallyLoaded() { }

// periphery:ignore:all — ignore entire file (add to top)
```

**CI integration** (GitHub Actions step):
```yaml
- name: Dead Code Detection
  run: rtk periphery scan --quiet --format checkstyle > periphery.xml
  continue-on-error: true
```

---

## 4. SwiftLint + SwiftFormat Together

**Rule of thumb:**
- SwiftLint = code quality, style enforcement, bug prevention
- SwiftFormat = whitespace, indentation, mechanical formatting

**Avoiding conflicts:**
- Disable SwiftLint's `comma` rule — SwiftFormat handles trailing commas
- Disable SwiftLint's `opening_brace` — SwiftFormat handles brace spacing
- Let SwiftFormat run first (pre-commit), SwiftLint second (CI)

**sindresorhus/swiftlint-config** as a starting point:
```bash
# Install:
rtk brew install swiftlint
# Download sindresorhus config:
rtk curl -o .swiftlint.yml https://raw.githubusercontent.com/sindresorhus/swiftlint-config/main/.swiftlint.yml
```

**airbnb/swift** style guide maps closely to the config in section 11.

---

## 5. Swift Package Manager

### `Package.swift` structure
```swift
// swift-tools-version: 5.10
import PackageDescription

let package = Package(
    name: "MyApp",
    platforms: [.macOS(.v14), .iOS(.v17)],
    products: [
        .library(name: "MyFeature", targets: ["MyFeature"]),
    ],
    dependencies: [
        .package(url: "https://github.com/realm/SwiftLint", from: "0.57.0"),
        .package(url: "https://github.com/nicklockwood/SwiftFormat", from: "0.54.0"),
    ],
    targets: [
        .target(
            name: "MyFeature",
            dependencies: [],
            plugins: [
                .plugin(name: "SwiftLintBuildToolPlugin", package: "SwiftLint"),
            ]
        ),
        .testTarget(name: "MyFeatureTests", dependencies: ["MyFeature"]),
    ]
)
```

**Binary targets** (for pre-built tools):
```swift
.binaryTarget(
    name: "SwiftLintBinary",
    url: "https://github.com/realm/SwiftLint/releases/download/0.57.0/SwiftLintBinary-macos.artifactbundle.zip",
    checksum: "abc123..."
)
```

**Local packages for modularization:**
```swift
// In main Package.swift:
.package(path: "../SharedKit"),
// Keeps modules independently testable; mirrors the NetNewsWire pattern
```

---

## 6. Xcode Project Structure

**Recommended folder layout:**
```
MyApp/
├── App/                    # AppDelegate, SceneDelegate, entry points
├── Features/
│   ├── Home/
│   │   ├── HomeView.swift
│   │   ├── HomeViewModel.swift
│   │   └── HomeModel.swift
│   └── Settings/
├── Core/                   # Shared utilities, extensions, helpers
├── Services/               # Networking, persistence, analytics
├── Resources/              # Assets.xcassets, Localizable.strings
├── Generated/              # SwiftGen output — never edit manually
├── SupportingFiles/        # Info.plist, entitlements
└── Tests/
    ├── UnitTests/
    └── UITests/
```

**Groups vs folder references:**
- Use **folder references** (blue folders) for Resources and Generated — syncs automatically
- Use **groups** (yellow folders) for Swift source — matches Xcode's mental model
- `tuist` and `XcodeGen` both enforce folder-mirroring automatically

**Build configurations:**
- `Debug` — assertions on, optimizations off, local API endpoints
- `Staging` — resembles Release, staging API endpoints, TestFlight builds
- `Release` — optimizations on, assertions off, production endpoints

**Xcode schemes:** one scheme per configuration. Lock `Release` scheme to prevent accidental debug builds.

---

## 7. CI/CD Setup

Full workflow in section 13. Key patterns from mas-cli (6 lint tools in CI):

**Tool matrix:**
1. SwiftLint (lint)
2. SwiftFormat --lint (format check)
3. swift build (compile)
4. swift test (unit tests)
5. periphery scan (dead code)
6. (optional) danger (PR automation)

**Code signing in CI:**
```bash
# Match (Fastlane) — recommended for teams
rtk bundle exec fastlane match appstore --readonly true
```

**Fastlane basics (`fastlane/Fastfile`):**
```ruby
lane :test do
  run_tests(scheme: "MyApp", clean: true)
end

lane :beta do
  match(type: "appstore", readonly: true)
  increment_build_number
  build_app(scheme: "MyApp")
  upload_to_testflight
end
```

---

## 8. Git Configuration

### `.gitignore` for Swift/Xcode
```gitignore
# Xcode
*.xcodeproj/xcuserdata/
*.xcworkspace/xcuserdata/
*.xcworkspace/xcshareddata/IDEWorkspaceChecks.plist
DerivedData/
*.moved-aside
*.pbxuser
!default.pbxuser
*.mode1v3
!default.mode1v3
*.mode2v3
!default.mode2v3
*.perspectivev3
!default.perspectivev3

# SPM
.build/
.swiftpm/
*.resolved  # Commit this for apps, ignore for libraries

# macOS
.DS_Store
*.swp

# Fastlane
fastlane/report.xml
fastlane/Preview.html
fastlane/test_output/

# Generated
Generated/
```

### `.gitattributes` (Xcode merge conflict reduction)
```gitattributes
*.pbxproj merge=union
*.xccurrentversion merge=union
```

**Branch protection rules (GitHub):**
- Require status checks: `lint`, `test`, `build`
- Require PR reviews: 1 approver minimum
- Dismiss stale reviews on new commits
- Restrict force-push to main/main

---

## 9. Code Generation

| Tool | Use Case | When to Choose |
|------|----------|----------------|
| **SwiftGen** | Assets, strings, colors, fonts | Always — eliminates stringly-typed resources |
| **Sourcery** | Boilerplate (Equatable, Mocks, Lenses) | When writing repetitive protocol conformances |
| **Swift Macros** | Compile-time code generation | Swift 5.9+; prefer over Sourcery for new code |

**SwiftGen setup:**
```bash
rtk brew install swiftgen
# swiftgen.yml
strings:
  inputs: Resources/Localizable.strings
  outputs:
    - templateName: structured-swift5
      output: Generated/Strings.swift
xcassets:
  inputs: Resources/Assets.xcassets
  outputs:
    - templateName: swift5
      output: Generated/Assets.swift
```

**Swift Macro example** (avoids Sourcery for new code):
```swift
@Observable class ViewModel { ... }  // generates observation boilerplate
@Spyable protocol MyService { ... }  // generates test spy (swift-spyable)
```

---

## 10. EditorConfig & Formatting

### `.editorconfig`
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.swift]
indent_style = space
indent_size = 4

[*.{yml,yaml,json}]
indent_style = space
indent_size = 2

[Makefile]
indent_style = tab
```

**Xcode settings synchronization:**
- Set `Text Editing > Indentation` to 4 spaces in Xcode preferences
- Share `.xcode-version` (via `xcenv`) to lock Xcode version across the team:
  ```
  16.2
  ```
- Use `xcode-select` in CI to match the locked version

---

## 11. Complete `.swiftlint.yml`

```yaml
# Production-ready SwiftLint config
# Based on airbnb/swift + sindresorhus patterns
# Updated for SwiftLint 0.57+

disabled_rules:
  - trailing_whitespace          # SwiftFormat handles this
  - opening_brace                # SwiftFormat handles this
  - comma                        # SwiftFormat handles this
  - todo                         # TODOs are tracked in issues, not blocked in CI
  - nesting                      # SwiftUI DSL nesting is legitimate
  - multiple_closures_with_trailing_closure  # common SwiftUI pattern

opt_in_rules:
  - array_init
  - attributes
  - closure_body_length
  - closure_end_indentation
  - closure_spacing
  - collection_alignment
  - contains_over_filter_count
  - contains_over_filter_is_empty
  - contains_over_first_not_nil
  - contains_over_range_nil_comparison
  - discouraged_assert
  - discouraged_none_name
  - discouraged_object_literal
  - empty_collection_literal
  - empty_count
  - empty_string
  - enum_case_associated_values_count
  - expiring_todo
  - explicit_init
  - extension_access_modifier
  - fallthrough
  - fatal_error_message
  - file_name_no_space
  - first_where
  - flatmap_over_map_reduce
  - force_unwrapping
  - identical_operands
  - implicit_return
  - implicitly_unwrapped_optional
  - joined_default_parameter
  - last_where
  - legacy_multiple
  - legacy_objc_type
  - literal_expression_end_indentation
  - local_doc_comment
  - lower_acl_than_parent
  - missing_docs
  - modifier_order
  - multiline_arguments
  - multiline_function_chains
  - multiline_literal_brackets
  - multiline_parameters
  - nimble_operator
  - no_extension_access_modifier
  - no_magic_numbers
  - operator_usage_whitespace
  - optional_enum_case_matching
  - overridden_super_call
  - override_in_extension
  - pattern_matching_keywords
  - prefer_self_in_static_references
  - prefer_self_type_over_type_of_self
  - prefer_zero_over_explicit_init
  - private_action
  - private_outlet
  - private_subject
  - prohibited_nan_comparison
  - prohibited_super_call
  - quick_discouraged_call
  - quick_discouraged_focused_test
  - quick_discouraged_pending_test
  - raw_value_for_camel_cased_codable_enum
  - reduce_into
  - redundant_nil_coalescing
  - redundant_type_annotation
  - return_value_from_void_function
  - self_binding
  - shorthand_optional_binding
  - single_test_class
  - sorted_first_last
  - sorted_imports
  - static_operator
  - strong_iboutlet
  - switch_case_on_newline
  - toggle_bool
  - unavailable_function
  - unneeded_parentheses_in_closure_argument
  - unowned_variable_capture
  - untyped_error_in_catch
  - unused_import
  - vertical_parameter_alignment_on_call
  - vertical_whitespace_between_cases
  - vertical_whitespace_closing_braces
  - vertical_whitespace_opening_braces
  - weak_delegate
  - xct_specific_matcher
  - yoda_condition

analyzer_rules:
  - capture_variable
  - explicit_self
  - typesafe_array_init
  - unused_declaration
  - unused_import

excluded:
  - .build
  - DerivedData
  - Generated
  - Pods
  - vendor
  - "**/*.generated.swift"
  - Packages          # SPM checkouts

line_length:
  warning: 120
  error: 160
  ignores_urls: true
  ignores_function_declarations: true
  ignores_comments: true

file_length:
  warning: 400
  error: 600

type_body_length:
  warning: 250
  error: 350

function_body_length:
  warning: 40
  error: 60

function_parameter_count:
  warning: 6
  error: 8

cyclomatic_complexity:
  warning: 10
  error: 20

identifier_name:
  min_length:
    warning: 2
    error: 1
  max_length:
    warning: 50
    error: 70
  excluded:
    - id
    - x
    - y
    - z
    - i
    - j
    - k
    - t
    - T

type_name:
  min_length: 3
  max_length:
    warning: 50
    error: 70

nesting:
  type_level:
    warning: 3
  function_level:
    warning: 3

no_magic_numbers:
  test_parent_classes:
    - XCTestCase
    - QuickSpec

missing_docs:
  excludes_extensions: true
  excludes_inherited_types: true

# Per-directory overrides
custom_rules:
  no_print_in_production:
    name: "No print statements"
    regex: '^\s*print\('
    message: "Use Logger or os_log instead of print(). Remove before shipping."
    severity: warning
    excluded: ".*Tests.*"
```

---

## 12. Complete `.swiftformat`

```
# SwiftFormat 0.54+ configuration
# nicklockwood/SwiftFormat

--swiftversion 5.10

# Indentation
--indent 4
--tabwidth 4
--indentcase false
--ifdef indent

# Line length
--maxwidth 120
--wraparguments before-first
--wrapparameters before-first
--wrapcollections before-first
--wrapreturntype if-multiline
--wrapconditions after-first
--closingparen balanced

# Braces
--allman false
--elseposition same-line
--guardelse same-line

# Spacing
--operatorfunc spaced
--nospaceoperators ..<,...
--ranges spaced
--trimwhitespace always

# Semicolons and colons
--semicolons never
--commas always
--stripunusedargs closure-only

# Imports
--importgrouping testable-last
--moduleimports group

# Self
--self init-only
--selfrequired

# Types
--shortoptionals always
--redundanttype infer-locals-only
--typeattributes prev-line
--funcattributes prev-line
--varattributes prev-line

# Closures
--trailingclosures
--nevertrailing

# Misc
--patternlet hoist
--header strip
--decimalgrouping 3,6
--binarygrouping 4,8
--hexgrouping 4,8
--exponentcase lowercase
--exponentgrouping disabled
--fractiongrouping disabled
--hexliteralcase uppercase
--octalgrouping never
--linebreaks lf
--emptybraces spaced
--emptylines trim

# Exclusions
--exclude .build,DerivedData,Generated,Pods,vendor
```

---

## 13. Complete GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: SwiftLint
    runs-on: macos-15
    steps:
      - uses: actions/checkout@v4
      - name: Cache SwiftLint
        uses: actions/cache@v4
        with:
          path: ~/.swiftlint
          key: swiftlint-${{ runner.os }}-0.57.0
      - name: Install SwiftLint
        run: rtk brew install swiftlint
      - name: Run SwiftLint
        run: rtk swiftlint lint --reporter github-actions-logging

  format-check:
    name: SwiftFormat Check
    runs-on: macos-15
    steps:
      - uses: actions/checkout@v4
      - name: Install SwiftFormat
        run: rtk brew install swiftformat
      - name: Check formatting
        run: rtk swiftformat --lint --quiet .

  build-and-test:
    name: Build & Test
    runs-on: macos-15
    strategy:
      matrix:
        destination:
          - "platform=iOS Simulator,name=iPhone 16,OS=latest"
          - "platform=macOS"
    steps:
      - uses: actions/checkout@v4
      - name: Select Xcode
        run: rtk sudo xcode-select -s /Applications/Xcode_16.2.app
      - name: Build
        run: |
          rtk xcodebuild build \
            -scheme MyApp \
            -destination "${{ matrix.destination }}" \
            CODE_SIGNING_ALLOWED=NO \
            | rtk xcpretty
      - name: Test
        run: |
          rtk xcodebuild test \
            -scheme MyApp \
            -destination "${{ matrix.destination }}" \
            -enableCodeCoverage YES \
            CODE_SIGNING_ALLOWED=NO \
            | rtk xcpretty

  spm-build:
    name: SPM Build & Test
    runs-on: macos-15
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: rtk swift build -c release
      - name: Test
        run: rtk swift test --parallel

  dead-code:
    name: Periphery (Dead Code)
    runs-on: macos-15
    needs: build-and-test
    steps:
      - uses: actions/checkout@v4
      - name: Install Periphery
        run: rtk brew install peripheryapp/periphery/periphery
      - name: Scan
        run: rtk periphery scan --quiet
        continue-on-error: true   # advisory; don't block PRs initially

  codeql:
    name: CodeQL Analysis
    runs-on: macos-15
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: swift
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3
```

---

## Quick Reference: Tool Decision Matrix

| Need | Tool | Config file |
|------|------|-------------|
| Enforce coding style rules | SwiftLint | `.swiftlint.yml` |
| Consistent formatting | SwiftFormat | `.swiftformat` |
| Find dead code | Periphery | `.periphery.yml` |
| Generate assets/strings code | SwiftGen | `swiftgen.yml` |
| Generate boilerplate | Swift Macros / Sourcery | `sourcery.yml` |
| Manage Xcode project | Tuist or XcodeGen | `Project.swift` / `project.yml` |
| Mac App Store CLI operations | mas-cli | — |
| Automate deployments | Fastlane | `Fastfile` |
