# SwiftLint Configuration

Tuned to **realm/SwiftLint's own dogfooded values** plus selective opt-in additions from the 0.62-0.63 release cycle. The most authoritative reference is the SwiftLint repo's own `.swiftlint.yml` (cdn.jsdelivr.net/gh/realm/SwiftLint@main/.swiftlint.yml) — Apple's own swift packages don't ship `.swiftlint.yml` because Apple uses swift-format internally, so realm's config is the closest to a community standard.

Latest stable as of 2026-04: **SwiftLint 0.63.2** ("High-Speed Extraction"). 0.64.0-rc.1 adds experimental Windows support but no behavior changes for Apple platforms. The 0.62.0 release **requires a Swift 6 compiler to build SwiftLint itself**; the SPM plugin still supports Swift 5.9+ on the consuming side.

## Recommended `.swiftlint.yml` for new Apple-platform projects

Drop this at the repo root.

```yaml
excluded:
  - .build
  - .spm-cache
  - Packages
  - DerivedData
  - "*.xcodeproj"
  - .factory
  - vendor

opt_in_rules:
  # SwiftUI / UIKit
  - private_swiftui_state              # @State must be private — Apple sample-code convention
  - accessibility_label_for_image      # VoiceOver compliance
  - accessibility_trait_for_button     # Tap-gesture views need .button trait
  - prefer_asset_symbols               # Image("name") → Image(.name) for type-safe asset refs

  # Concurrency (Swift 6 ready)
  - incompatible_concurrency_annotation  # public @MainActor / Sendable need @preconcurrency
  - redundant_sendable                   # remove Sendable on actor-isolated types
  - unhandled_throwing_task              # Task { try ... } silently swallows errors
  - async_without_await                  # async func with no await
  - weak_delegate                        # delegate must be weak

  # Code quality
  - first_where, last_where              # .first/.last(where:) over .filter().first
  - contains_over_filter_count           # .contains(where:) over .filter().count > 0
  - contains_over_filter_is_empty        # .contains(where:) over .filter().isEmpty
  - sorted_first_last                    # .min()/.max() over .sorted().first/.last
  - empty_count, empty_string            # .isEmpty over .count == 0 / == ""
  - reduce_into                          # .reduce(into:_:) for mutating accumulators
  - flatmap_over_map_reduce              # .flatMap over .map { ... }.reduce(+)
  - toggle_bool                          # .toggle() over `x = !x`
  - shorthand_optional_binding           # if let x { ... } over if let x = x { ... }
  - discouraged_optional_boolean         # avoid Bool? (use enum or default)

  # Style
  - modifier_order                       # consistent override/public/static ordering
  - implicit_return                      # trailing return in single-expression closures
  - prefer_self_in_static_references     # Self.foo over TypeName.foo
  - direct_return                        # eliminate intermediate var before return
  - superfluous_else                     # remove else after early-exit return/throw/break
  - prefer_condition_list                # if a, b over if a && b
  - unneeded_throws_rethrows             # functions marked throws that never throw
  - redundant_nil_coalescing             # x ?? nil
  - identical_operands                   # catch x == x bugs
  - convenience_type                     # caseless enum for static-only types
  - fatal_error_message                  # require message in fatalError()
  - period_spacing                       # catch double-space after period

  # Limits
  - closure_body_length

disabled_rules:
  - trailing_whitespace                  # SwiftFormat owns this
  - trailing_comma                       # SwiftFormat adds trailing commas — disable to avoid conflict
  - opening_brace                        # SwiftFormat owns brace placement
  - statement_position                   # SwiftFormat owns `else` placement
  - vertical_parameter_alignment_on_call # SwiftFormat owns wrap style
  - todo                                 # too noisy in active development
  - blanket_disable_command              # we use targeted disables, not blanket

# Thresholds — tuned to realm/SwiftLint's own values where they exist
line_length:
  warning: 140
  error: 250
  ignores_urls: true
  ignores_comments: true

file_length:
  warning: 800
  error: 1500

type_body_length:
  warning: 500
  error: 1000

function_body_length:
  warning: 100
  error: 250

closure_body_length:
  warning: 80
  error: 300

cyclomatic_complexity:
  warning: 15
  error: 25
  ignores_case_statements: true

function_parameter_count:
  warning: 5
  error: 8

large_tuple:
  warning: 3
  error: 4

nesting:
  type_level: 3
  function_level: 10

identifier_name:
  min_length:
    warning: 2
  max_length:
    warning: 60
  excluded:
    - id
    - to
    - in
    - ok
    - x
    - y
    - z
    - i
    - j

type_name:
  min_length:
    warning: 3
  max_length:
    warning: 50
    error: 60
  excluded:
    - T  # generic type parameters

custom_rules:
  no_print_statements:
    name: "No print()"
    regex: '^\s*print\s*\('
    message: "Use Logger / OSLog instead of print() in production code."
    severity: warning

  swiftui_state_must_be_private:
    name: "Private @State"
    regex: '^\s*@State\s+(?!private)'
    message: "@State properties must be private (SwiftUI sample-code convention)."
    severity: warning

  no_force_try:
    name: "No try!"
    regex: '\btry!'
    message: "Avoid try!; handle the error or use try? with a fallback."
    severity: warning

  fatal_error_attribution:
    name: "fatalError() needs context"
    regex: 'fatalError\(\s*\)'
    message: "fatalError must include a non-empty message for crash triage."
    severity: error

  unchecked_sendable_audit:
    name: "@unchecked Sendable audit"
    regex: '@unchecked\s+Sendable'
    message: "Document why @unchecked Sendable is safe in a comment, or use a true Sendable type."
    severity: warning
```

## Why these thresholds

| Threshold | Value | Justification |
|---|---|---|
| `line_length: 140 / 250` | Slightly more generous than realm's 110 | Modern monitors handle 140 well; descriptive Swift symbol names need headroom; 250 hard cap |
| `file_length: 800 / 1500` | More generous than default 400/1000 | Mature SwiftUI views legitimately exceed 400 lines; forces extraction at 800 |
| `function_body_length: 100 / 250` | Generous vs realm's 60 | SwiftUI bodies routinely cross 60; 100 catches genuine bloat |
| `closure_body_length: 80 / 300` | Matches realm; SwiftUI body closures need 50+ | View bodies are functionally function bodies |
| `cyclomatic_complexity: 15 / 25` | Generous vs default 10/20 | Switch-heavy state machines need exemption; `ignores_case_statements: true` helps |
| `large_tuple: 3 / 4` | Matches realm | Most tuples should be types, but `(label: String, value: Int, formatter: …)` patterns exist |
| `identifier_name: min 2` | Default is 3 | `id`, `to`, `i`, `j`, `x`, `y` are idiomatic; lowering avoids warning fatigue |

## Auto-correctable rules (applied via `swiftlint --fix`)

The skill teaches `make lint-fix` as `swiftlint --fix` to auto-correct what's possible, then `swiftlint --strict` to fail on the residue. The stable correctable set as of 0.63.2 includes (alphabetical, abbreviated):

`closing_brace`, `closure_end_indentation`, `closure_parameter_position`, `closure_spacing`, `colon`, `comma`, `comment_spacing`, `direct_return`, `duplicate_imports`, `empty_enum_arguments`, `empty_parameters`, `explicit_init`, `first_where`, `for_where`, `implicit_return`, `last_where`, `legacy_*` (cggeometry, constant, constructor, hashing, nsgeometry, random), `mark`, `modifier_order`, `multiline_*_brackets`, `number_separator`, `operator_usage_whitespace`, `prefer_zero_over_explicit_init`, `private_over_fileprivate`, `protocol_property_accessors_order`, `redundant_*` (discardable_let, nil_coalescing, objc_attribute, optional_initialization, self, set_access_control, string_enum_value, type_annotation, void_return), `return_arrow_whitespace`, `self_in_property_initialization`, `shorthand_operator`, `shorthand_optional_binding`, `sorted_first_last`, `sorted_imports`, `static_over_final_class`, `superfluous_else`, `switch_case_alignment`, `syntactic_sugar`, `toggle_bool`, `trailing_closure`, `trailing_comma`, `trailing_newline`, `trailing_semicolon`, `trailing_whitespace`, `unneeded_break_in_switch`, `unneeded_escaping`, `unneeded_parentheses_in_closure_argument`, `unused_*` (closure_parameter, control_flow_label, enumerated, optional_binding), `vertical_*` (parameter_alignment, whitespace, whitespace_*_braces), `void_function_in_ternary`, `void_return`, `weak_delegate`, `xct_specific_matcher`, `yoda_condition`.

The canonical machine-readable list is `swiftlint rules` CLI output (column "correctable").

## Custom-rule design notes

- The `regex` field is plain ICU regex; flags `s` (dotall) and `m` (multiline) are always enabled. To disable dotall, prepend `(?-s)`.
- `match_kinds` filters by SourceKit syntax kinds — useful to avoid matching `print` inside strings or comments. If the rule needs precision, add `match_kinds: [identifier]`.
- `excluded` accepts a glob pattern array; common exclusion: tests should be allowed to use `print` or `try!` more liberally — `excluded: [".*Tests.*\\.swift"]`.

## Threshold tuning by project age

| Project state | Recommendation |
|---|---|
| Greenfield Swift 6 project | Use the config above as-is. Run once, fix any startup violations, commit `.swiftlint-baseline.json` as `[]`. |
| Mature project (>50k LOC) with no prior linting | Run `swiftlint --write-baseline .swiftlint-baseline.json` first to capture the legacy debt; commit the baseline; future PRs fail only on NEW violations. |
| Project upgrading SwiftLint major version | Read the CHANGELOG between versions for renamed rules (e.g. 0.63.0 renamed `redundant_self_in_closure` → `redundant_self`); update disabled_rules accordingly. Regenerate baseline after upgrade. |

## Apple platform considerations

SwiftLint is **target-agnostic** — it operates on `.swift` source text via SwiftSyntax/SourceKit, not on compiled binaries or platform SDKs. There are no rules gated to a specific Apple platform. The same `.swiftlint.yml` works for macOS / iOS / tvOS / watchOS / visionOS targets. Multi-platform Swift packages can use one root `.swiftlint.yml`; nested per-target configs work but only one nested config is merged per file (per SwiftLint README §Nested Configurations).

## References

- realm/SwiftLint repo — https://github.com/realm/SwiftLint (accessed 2026-04-18)
- Authoritative `.swiftlint.yml` (realm dogfood) — https://cdn.jsdelivr.net/gh/realm/SwiftLint@main/.swiftlint.yml
- Rule directory — https://realm.github.io/SwiftLint/rule-directory.html
- Baseline API — https://realm.github.io/SwiftLint/Structs/Baseline.html
- Release notes 0.62.0 / 0.62.2 / 0.63.0 / 0.63.2 — https://github.com/realm/SwiftLint/releases
- gist (staged-files lint pattern) — https://gist.github.com/candostdagdeviren/9716e514355ab0fee4858c3d467269aa
