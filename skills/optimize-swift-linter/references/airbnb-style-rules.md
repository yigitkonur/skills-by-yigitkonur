# Airbnb Swift Style Guide — Machine-Readable Reference

## 1. Quick Setup

Add to `Package.swift` dependencies:
```swift
.package(url: "https://github.com/airbnb/swift", from: "1.0.0")
```

Run formatting:
```bash
rtk swift package --allow-writing-to-package-directory format
rtk swift package --allow-writing-to-package-directory format --lint  # CI check
```

---

## 2. Formatting Rules (SwiftFormat)

### Indentation & Whitespace

**2 spaces, never tabs:**
```swift
// WRONG
func foo() {
    let x = 1   // 4-space
}
// RIGHT
func foo() {
  let x = 1
}
```

**No semicolons:**
```swift
// WRONG  let a = 1; let b = 2
// RIGHT  let a = 1 \n let b = 2
```

**Spaced empty braces:**
```swift
// WRONG  var didLoad: (() -> Void)?  // {}
// RIGHT  var didLoad: (() -> Void)? // { }
```

**`else`/`catch`/`while` on same line as closing brace; `guard else` on next line:**
```swift
// WRONG
if x { }
else { }
// RIGHT
if x { } else { }

// guard else always next line:
guard let x = x
else { return }
```

**Blank lines at start/end of scope — preserved (not added/removed by default); blank line after each switch case:**
```swift
case .foo:
  doSomething()

case .bar:   // blank line before each case
  doOther()
```

### Wrapping

**Max width 130 (recommended 100). Wrap arguments before-first:**
```swift
// WRONG
func foo(a: Int, b: Int, c: Int) { }
// RIGHT (when over limit)
func foo(
  a: Int,
  b: Int,
  c: Int)
{ }
```

**Trailing commas on multi-element lists (not single-line):**
```swift
// WRONG
let arr = [
  1,
  2
]
// RIGHT
let arr = [
  1,
  2,
]
```

**Attributes on previous line for func/type/computed-var/complex; same line for stored var:**
```swift
// WRONG
@discardableResult func foo() -> Int { }
// RIGHT
@discardableResult
func foo() -> Int { }

// Stored var — same line is correct:
@State private var isOn = false
```

**Ternary wraps before operators:**
```swift
// RIGHT
let value = condition
  ? trueValue
  : falseValue
```

### Redundancy Removal

**Remove `self.` unless necessary to disambiguate:**
```swift
// WRONG  self.view.backgroundColor = self.color
// RIGHT  view.backgroundColor = color
```

**Remove redundant return in single-expression closures/funcs:**
```swift
// WRONG  var doubled: Int { return value * 2 }
// RIGHT  var doubled: Int { value * 2 }
```

**Remove redundant type annotations when inferred:**
```swift
// WRONG  let count: Int = items.count
// RIGHT  let count = items.count
```

**Remove redundant `Void` return, `get {}` for read-only, redundant closures, redundant `internal`, redundant `throws`/`async`:**
```swift
// WRONG  func foo() -> Void { }
// RIGHT  func foo() { }

// WRONG  var x: Int { get { 1 } }
// RIGHT  var x: Int { 1 }
```

**`redundantPublic`: remove `public` from members that can't be accessed publicly anyway (e.g., inside `private` type).**

### Type Sugar

```swift
// WRONG  Array<Int>  Dictionary<String, Int>  Optional<Foo>
// RIGHT  [Int]       [String: Int]             Foo?
```

**`--some-any disabled` — `some`/`any` keywords are NOT enforced by formatter; use explicit generic parameters where named.**

### Organization (`organizeDeclarations`)

Applied to types with 20+ members. MARK sections in this visibility order:
```
// MARK: - Public   (open, public, package, internal, fileprivate, private)
```

Within each section, declaration type order:
```
nestedType → staticProperty → staticPropertyWithBody → classPropertyWithBody
→ swiftUIPropertyWrapper → instanceProperty → instancePropertyWithBody
→ staticMethod → classMethod → instanceMethod
```

**Imports sorted; `@testable` imports at bottom:**
```swift
import Foundation
import UIKit

@testable import MyModule
```

**Extensions: access control on declarations, not on extension keyword:**
```swift
// WRONG  public extension Foo { func bar() { } }
// RIGHT  extension Foo { public func bar() { } }
```

**`fileprivate` → `private` when possible (`redundantFileprivate`).**

**Modifier order (access first, then `override`, then `final`, then `static`/`class`):**
```
private / fileprivate / internal / package / public / open
→ private(set) … open(set)
→ override → final → dynamic → optional → required → convenience → indirect
→ isolated → nonisolated → nonisolated(unsafe) → lazy → weak → unowned
→ static → class → borrowing → consuming → mutating → nonmutating
→ prefix → infix → postfix → async
```

---

## 3. SwiftLint Built-in Rules (only_rules whitelist)

| Rule | What it catches |
|---|---|
| `fatal_error_message` | `fatalError()` without a message string |
| `implicitly_unwrapped_optional` | `Type!` declarations (use `?` + guard instead) |
| `legacy_cggeometry_functions` | `CGRectGetWidth(r)` → `r.width` |
| `legacy_constant` | `CGRectZero` → `.zero`, `M_PI` → `.pi` |
| `legacy_constructor` | `CGPointMake(x,y)` → `CGPoint(x:y:)` |
| `legacy_nsgeometry_functions` | `NSWidth(r)` → `r.width` |
| `unused_optional_binding` | `if let _ = x` → `if x != nil` |
| `unowned_variable_capture` | `[unowned self]` in closures (use `[weak self]`) |
| `superfluous_disable_command` | `// swiftlint:disable` for already-disabled rule |
| `invalid_swiftlint_command` | Malformed swiftlint comment directives |
| `custom_rules` | Enables the custom rules below |

---

## 4. Custom SwiftLint Rules

**no_objcMembers** — error
```swift
// WRONG  @objcMembers class Foo { … }
// RIGHT  class Foo { @objc func bar() { } }  // annotate each member explicitly
```

**no_direct_standard_out_logs** — error
```swift
// WRONG  print("debug")  debugPrint(obj)  dump(val)  _printChanges()
// RIGHT  logger.debug("…")  // or: // swiftlint:disable:next no_direct_standard_out_logs
```

**no_file_literal** — error
```swift
// WRONG  let f = #file
// RIGHT  let f = #fileID
```

**no_filepath_literal** — error
```swift
// WRONG  let p = #filePath
// RIGHT  let p = #fileID
```

**no_unchecked_sendable** — error
```swift
// WRONG  extension Foo: @unchecked Sendable { }
// RIGHT  // Prefer Sendable, @preconcurrency import, or @MainActor isolation.
// If truly needed: // swiftlint:disable:next no_unchecked_sendable (with comment explaining thread-safety)
```

---

## 5. Key Patterns

**Named types over caseless enums for namespaces — use `enum` (not `struct`) for namespace:**
```swift
// RIGHT
enum Constants {
  static let pi = 3.14
}
```

**Use `#URL()` macro for compile-time URL validation (Swift 5.9+):**
```swift
// WRONG  URL(string: "https://airbnb.com")!
// RIGHT  #URL("https://airbnb.com")
```

**`count(where:)` over filter+count (Swift 6.0+):**
```swift
// WRONG  items.filter { $0.isActive }.count
// RIGHT  items.count(where: \.isActive)
```

**Prefer `for … in` over `forEach` for simple iteration (`preferForLoop`):**
```swift
// WRONG  items.forEach { process($0) }
// RIGHT  for item in items { process(item) }
```

**Opaque generic parameters: use `some` when single concrete type returned; named generic when constraint is referenced multiple times or in func signature — `--some-any disabled` means formatter won't force this.**

**No force-try (`try!`) or force-unwrap (`!`) outside tests.**

**Prefer `final` on classes unless subclassing is intended (`preferFinalClasses`).**

**`guard` for early exit, not inside tests (`noGuardInTests`).**

**Conditional assignment with `if`/`switch` expressions:**
```swift
// WRONG
let x: Int
if condition { x = 1 } else { x = 2 }
// RIGHT
let x = if condition { 1 } else { 2 }
```

**`@preconcurrency import` instead of `@unchecked Sendable` when bridging pre-concurrency APIs.**

---

## 6. File Organization

**File structure order:**
1. Copyright header (if any)
2. `import` statements (sorted, `@testable` last)
3. Type declarations (each in its own `// MARK: -` section for 20+ members)

**MARK format:** `// MARK: - SectionName` (with dash, capital, space)

**One type per file preferred; extensions in same file or separate `TypeName+FeatureName.swift`.**

**`fileprivate` only when sharing across multiple types in one file; otherwise `private`.**

---

## 7. SwiftUI Rules

**SwiftUI property wrappers go in their own MARK section, sorted by first-appearance order (`--sort-swiftui-properties first-appearance-sort`):**
```swift
// MARK: - Internal

@State private var isLoading = false
@Environment(\.colorScheme) private var colorScheme
@Binding var isPresented: Bool
```

**Synthesized memberwise init for `internal` View/ViewBuilder structs (no manual init needed).**

**Remove redundant `@ViewBuilder` when body is single expression (`redundantViewBuilder`):**
```swift
// WRONG
@ViewBuilder var content: some View { Text("hi") }
// RIGHT
var content: some View { Text("hi") }
```

**`@Entry` macro for custom `EnvironmentKey`:**
```swift
// WRONG — manual EnvironmentKey boilerplate
// RIGHT
extension EnvironmentValues {
  @Entry var myValue = MyType.default
}
```

**`environmentEntry` rule enforces this pattern.**

---

## 8. Testing Rules

**Swift Testing — test functions use raw identifiers for human-readable names:**
```swift
// WRONG  func testAddition() { }
// RIGHT  @Test func "1 + 1 = 2"() { }  // or descriptive func name
```

**`validateTestCases` — ensures test methods follow naming conventions.**
**`swiftTestingTestCaseNames` — Swift Testing test names style.**
**`redundantSwiftTestingSuite` — remove `@Suite` when redundant.**
**`testSuiteAccessControl` — test suites must be `internal` (default) or higher.**

**No force-try or force-unwrap in tests; use `#require` (Swift Testing) or `XCTUnwrap` (XCTest):**
```swift
// WRONG  let value = try! expression
// RIGHT (Swift Testing)  let value = try #require(expression)
// RIGHT (XCTest)         let value = try XCTUnwrap(expression)
```

**No `guard` in tests — use `#require`/`XCTUnwrap` instead (`noGuardInTests`).**

**`noForceTryInTests` and `noForceUnwrapInTests` rules enforce this.**

---

## 9. Complete Config Files

### `.swiftformat` (place at repo root)
```
--exclude Carthage,Pods,.build
--swift-version 6.2
--language-mode 5
--self remove
--import-grouping testable-bottom
--trailing-commas multi-element-lists
--trim-whitespace always
--indent 2
--ifdef no-indent
--indent-strings true
--wrap-arguments before-first
--wrap-parameters before-first
--wrap-collections before-first
--wrap-conditions before-first
--wrap-return-type never
--wrap-effects never
--closing-paren balanced
--call-site-paren balanced
--wrap-type-aliases before-first
--allow-partial-wrapping false
--func-attributes prev-line
--computed-var-attributes prev-line
--stored-var-attributes same-line
--complex-attributes prev-line
--type-attributes prev-line
--wrap-ternary before-operators
--wrap-string-interpolation preserve
--mark-struct-threshold 20
--mark-enum-threshold 20
--organize-types class,struct,enum,extension,actor,protocol
--visibility-order beforeMarks,instanceLifecycle,open,public,package,internal,fileprivate,private
--type-order nestedType,staticProperty,staticPropertyWithBody,classPropertyWithBody,swiftUIPropertyWrapper,instanceProperty,instancePropertyWithBody,staticMethod,classMethod,instanceMethod
--sort-swiftui-properties first-appearance-sort
--type-body-marks remove
--extension-acl on-declarations
--pattern-let inline
--property-types inferred
--type-blank-lines preserve
--empty-braces spaced
--ranges preserve
--operator-func no-space
--some-any disabled
--else-position same-line
--guard-else next-line
--single-line-for-each convert
--short-optionals always
--semicolons never
--doc-comments preserve
--prefer-synthesized-init-for-internal-structs View,ViewBuilder
--modifier-order private,fileprivate,internal,package,public,open,private(set),fileprivate(set),internal(set),package(set),public(set),open(set),override,final,dynamic,optional,required,convenience,indirect,isolated,nonisolated,nonisolated(unsafe),lazy,weak,unowned,unowned(safe),unowned(unsafe),static,class,borrowing,consuming,mutating,nonmutating,prefix,infix,postfix,async
--max-width 130
--rules anyObjectProtocol,blankLinesBetweenScopes,consecutiveSpaces,consecutiveBlankLines,duplicateImports,extensionAccessControl,environmentEntry,hoistPatternLet,indent,markTypes,organizeDeclarations,redundantParens,redundantReturn,redundantSelf,redundantType,redundantPattern,redundantGet,redundantFileprivate,redundantRawValues,redundantEquatable,sortImports,sortDeclarations,strongifiedSelf,trailingCommas,trailingSpace,linebreakAtEndOfFile,typeSugar,wrap,wrapMultilineStatementBraces,wrapArguments,wrapAttributes,wrapEnumCases,singlePropertyPerLine,braces,redundantClosure,redundantInit,redundantVoidReturnType,redundantOptionalBinding,redundantInternal,redundantPublic,redundantVariable,unusedArguments,spaceInsideBrackets,spaceInsideBraces,spaceAroundBraces,spaceInsideParens,spaceAroundParens,spaceAroundOperators,enumNamespaces,blockComments,docComments,docCommentsBeforeModifiers,spaceAroundComments,spaceInsideComments,blankLinesAtStartOfScope,blankLinesAtEndOfScope,emptyBraces,andOperator,opaqueGenericParameters,genericExtensions,trailingClosures,elseOnSameLine,sortTypealiases,preferForLoop,conditionalAssignment,wrapMultilineConditionalAssignment,wrapFunctionBodies,wrapPropertyBodies,void,blankLineAfterSwitchCase,consistentSwitchCaseSpacing,semicolons,propertyTypes,blankLinesBetweenChainedFunctions,preferCountWhere,swiftTestingTestCaseNames,redundantSwiftTestingSuite,modifiersOnSameLine,noForceTryInTests,noForceUnwrapInTests,redundantThrows,redundantAsync,noGuardInTests,testSuiteAccessControl,validateTestCases,redundantMemberwiseInit,redundantBreak,redundantTypedThrows,preferFinalClasses,simplifyGenericConstraints,redundantViewBuilder
```

### `.swiftlint.yml` (place at repo root)
```yaml
only_rules:
  - fatal_error_message
  - implicitly_unwrapped_optional
  - legacy_cggeometry_functions
  - legacy_constant
  - legacy_constructor
  - legacy_nsgeometry_functions
  - unused_optional_binding
  - unowned_variable_capture
  - superfluous_disable_command
  - invalid_swiftlint_command
  - custom_rules

excluded:
  - Carthage
  - Pods
  - .build

indentation: 2

custom_rules:
  no_objcMembers:
    name: "@objcMembers"
    regex: "@objcMembers"
    message: "Explicitly use @objc on each member you want to expose to Objective-C"
    severity: error
  no_direct_standard_out_logs:
    name: "Writing log messages directly to standard out is disallowed"
    regex: "(\\bprint|\\bdebugPrint|\\bdump|Swift\\.print|Swift\\.debugPrint|Swift\\.dump|_printChanges)\\s*\\("
    match_kinds:
    - identifier
    message: "Don't commit print/debugPrint/dump/_printChanges. Use a logging system or suppress with // swiftlint:disable:next no_direct_standard_out_logs"
    severity: error
  no_file_literal:
    name: "#file is disallowed"
    regex: "(\\b#file\\b)"
    match_kinds:
    - identifier
    message: "Instead of #file, use #fileID"
    severity: error
  no_filepath_literal:
    name: "#filePath is disallowed"
    regex: "(\\b#filePath\\b)"
    match_kinds:
    - identifier
    message: "Instead of #filePath, use #fileID."
    severity: error
  no_unchecked_sendable:
    name: "`@unchecked Sendable` is discouraged."
    regex: "@unchecked Sendable"
    match_kinds:
    - attribute.builtin
    - typeidentifier
    message: "Use Sendable, @preconcurrency import, or @MainActor. If truly needed, add // swiftlint:disable:next no_unchecked_sendable with thread-safety explanation."
    severity: error
```

---

## 10. Concurrency Rules (Swift 6)

**Prefer `Sendable` conformance over `@unchecked Sendable`.**

**Safe alternatives to `@unchecked Sendable` (in preference order):**
1. Genuine `Sendable` conformance (immutable struct, actor, etc.)
2. `@MainActor` isolation for UI types
3. `@preconcurrency import FrameworkName` for pre-concurrency Apple APIs
4. `nonisolated(unsafe)` for properties known safe but not provable by compiler

**`@unchecked Sendable` only when all alternatives fail — requires inline comment explaining thread-safety guarantee.**

**Actor isolation patterns:**
```swift
// UI types — isolate to MainActor
@MainActor
final class ViewModel: ObservableObject { … }

// Background work
actor DataStore {
  private var cache: [String: Data] = [:]
  func fetch(_ key: String) -> Data? { cache[key] }
}
```

**`nonisolated` for computed properties that don't need isolation:**
```swift
// RIGHT
nonisolated var description: String { "…" }
```

**`isolated` parameter for passing actor context explicitly:**
```swift
func update(on actor: isolated MyActor) { … }
```

**Capture semantics — `[weak self]` preferred over `[unowned self]` in closures (SwiftLint `unowned_variable_capture` error).**

**Swift 6 language mode**: the `.swiftformat` config uses `--swift-version 6.2` with `--language-mode 5` — strict concurrency checking enabled via `--swift-version` but module interface generation targets Swift 6.2 features.
