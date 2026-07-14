# find-polluter.sh

Purpose: multi-runner test-pollution bisection. Use when a target test passes in isolation but fails after other tests, usually because a prior test mutates shared state and leaves incomplete teardown.

## Supported runners

`find-polluter.sh` supports:

- `jest`
- `vitest`
- `pytest`
- `cargo`
- `gotest`
- `rspec`
- `mvn`
- `gradle`

Use `--runner auto` to detect from project manifests, or pass `--runner <name>` in monorepos or projects with multiple test stacks.

## Target selector shape

`--target` must be a runner-native selector, not a human test title.

| Runner | Required `--target` shape |
|---|---|
| `jest` / `vitest` | test-file path, such as `tests/auth.test.ts` |
| `pytest` | nodeid, such as `tests/test_auth.py::test_missing_token` |
| `cargo` | test function path/name, such as `auth::missing_token` |
| `gotest` | regex for `-run`, such as `^TestAuth_MissingToken$` |
| `rspec` | file:line selector or example id, such as `spec/auth_spec.rb:42` |
| `mvn` / `gradle` | test class or class/method selector, such as `com.example.AuthTest` or `AuthTest.testMissingToken` |

## When to use

Use during Phase 1 when the symptom is "passes alone, fails in suite" and the repro is not yet deterministic. The script turns the broad full-suite failure into a smaller reproducible ordering: polluter first, target second.

Use during bisection when `references/bisection-strategies.md` routes to test-pollution bisection.

Do not use it for compile errors, single-test deterministic failures, or failures caused by external services. Those should continue through normal Phase 1 evidence capture.

## Ordering and randomization caveats

The script forces ordering by running candidate subsets before the target and uses serial flags where runners expose them. Some projects still randomize or parallelize internally.

If output says no polluter was found but the full suite still fails, disable project-level randomization before retrying:

- pytest-randomly: `--randomly-seed=0` or disable the plugin
- Go: `-shuffle=off`
- RSpec: `--order defined`
- Jest/Vitest: avoid config-level sharding or file randomization

For test runners with no reliable intra-suite ordering guarantee, trust only the final minimal reproduction command the script prints, then rerun it manually.

## Sample commands

Auto-detect the runner:

```bash
bash skills/debug-runtime/skills/debug-runtime/scripts/find-polluter.sh \
  --target "tests/auth.test.ts" \
  --runner auto
```

Pytest with an explicit nodeid:

```bash
bash skills/debug-runtime/skills/debug-runtime/scripts/find-polluter.sh \
  --runner pytest \
  --target "tests/test_auth.py::test_missing_token"
```

Cargo with a constrained candidate list:

```bash
bash skills/debug-runtime/skills/debug-runtime/scripts/find-polluter.sh \
  --runner cargo \
  --target "auth::missing_token" \
  --candidates /tmp/pre-tests.txt
```

## Expected output

Successful output includes:

- detected runner
- target selector
- candidate count
- bisection progress ranges
- identified polluting test
- minimal reproduction command
- next action

The next diagnostic action is to read the polluting test and identify the shared state it mutates: in-memory cache, global singleton, module-level config, on-disk file, database row, feature flag, or environment variable. After naming the mutation, re-enter Phase 2 and state the candidate mechanism as `X caused Y because Z`.

If the target fails in isolation, this is not test pollution. Return to Phase 1 with the isolated failure as the symptom.

If the full candidate set does not trigger the target failure, the runner may still be randomizing or the candidate set is incomplete. Fix ordering first, then rerun the script.
