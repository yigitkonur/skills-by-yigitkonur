# Language-Specific Review Patterns

Common patterns and pitfalls by language. Reference this when reviewing code in a specific language.

## TypeScript / JavaScript

### Critical patterns
- `any` type usage — weakens type safety, check if avoidable
- `as` type assertion — may hide type errors at runtime
- `@ts-ignore` / `@ts-expect-error` — investigate why the type system is being bypassed
- `eval()` or `new Function()` — potential code injection
- `innerHTML` assignment with user input — XSS vulnerability
- Unhandled promise rejections — missing `await`, missing `.catch()`
- `==` instead of `===` — type coercion bugs

### Common mistakes
- Mutable default parameters in functions
- Closures capturing loop variables (use `let` not `var`)
- Missing `break` in switch statements
- Async functions that don't `await` promises
- `JSON.parse` without try/catch
- `Array.prototype.find` result used without null check

### React-specific
- Missing dependency array in `useEffect`
- State mutations instead of immutable updates
- Missing `key` prop in list rendering
- Side effects in render function
- Memory leaks (subscriptions not cleaned up in useEffect return)

## Python

### Critical patterns
- `pickle.loads()` on untrusted data — remote code execution
- `subprocess.shell=True` with user input — command injection
- `eval()` / `exec()` — code injection
- SQL string formatting instead of parameterized queries
- `assert` used for validation (disabled with `python -O`)
- Mutable default arguments (`def f(x=[])`) — shared state across calls

### Common mistakes
- Bare `except:` catching everything (including `KeyboardInterrupt`)
- Not using context managers for file/resource handling
- `is` for value comparison instead of `==`
- Forgetting to call `super().__init__()` in child classes
- Modifying a list while iterating over it

## Go

### Critical patterns
- Unchecked errors (`_, err := f(); _ = err` or just ignoring return)
- Data races (shared mutable state without sync primitives)
- SQL injection (string formatting in queries)
- `defer` in loops (resource leak)

### Common mistakes
- Returning pointer to loop variable
- Goroutine leaks (no way to stop them)
- Not checking `rows.Err()` after iteration
- Using `interface{}` / `any` when a concrete type would work

## Rust

### Common patterns to verify
- `unwrap()` / `expect()` in production code — should these be proper error handling?
- `unsafe` blocks — review thoroughly, is it truly necessary?
- `clone()` overuse — performance concern
- Missing `Send` / `Sync` bounds in concurrent code

## Java / Kotlin

### Critical patterns
- `equals()` vs `==` confusion (object identity vs value)
- Unvalidated redirects / forwards
- XXE (XML External Entity) in XML parsers
- Thread-unsafe collections used in concurrent code

### Common mistakes
- Resource leaks (missing try-with-resources)
- Catching `Exception` or `Throwable` too broadly
- Mutable objects as HashMap keys
- Nullable types not handled (Kotlin: `!!` overuse)

## SQL / Migrations

### Critical patterns
- Dropping columns/tables without data backup plan
- Non-reversible migrations (no down/rollback)
- Adding NOT NULL columns without defaults (breaks existing rows)
- Missing indexes on foreign keys or frequently queried columns
- Large table alterations without considering lock time

For each language, apply the relevant checks during cluster review based on the file extensions in the cluster being reviewed.
