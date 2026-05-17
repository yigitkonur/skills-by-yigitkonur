# run-codex-1 test fixtures

Test fixtures pinning current skill behavior across the unification refactor. See `/Users/yigitkonur/dev/unification-strategy/tasks/01-phase-zero-baseline-and-tests.md` for the design.

## Layout

```
__fixtures__/
├── README.md                  ← this file
├── KNOWN-BUGS.md              ← KB-NNN entries: fixtures that capture documented bugs (refactor fixes them)
├── run-parity.mjs             ← test runner: replays fixtures, diffs against current/refactored output
├── bin/codex-stub             ← fake `codex` CLI emitting canned JSONL events per scenario
├── baseline/                  ← pre-refactor snapshots (Phase 0; KB updates write here)
│   ├── dispatcher/            ← envelope JSONs per (mode, scenario)
│   ├── runners/               ← stdout/stderr captures per (runner, scenario)
│   ├── monitor/               ← tick samples, sentinel lines
│   ├── filter/                ← codex-json-filter.sh per event type
│   ├── manifest/              ← manifest state transition snapshots
│   ├── help/                  ← --help output per script
│   ├── audit/                 ← audit-fleet-state.py / audit-sizes.sh / list-worktrees.py / classify / rescue outputs
│   └── audit-pass-v1.md       ← 22-agent audit pass against current docs (87 critical findings baseline)
└── golden/                    ← cross-language shared fixtures (consumed by both _lib.sh and _lib.py)
    ├── slug-derivation.json   ← input path → expected (slug, hash)
    ├── state-dir-resolution.json ← env combinations → expected state dirs
    ├── manifest-atomic-write.json ← input manifest + mutation → expected on-disk JSON
    └── monitor-tick-rule-engine.json ← input state → expected (note, flags)
```

## Running tests

```bash
node run-parity.mjs                       # all fixtures
node run-parity.mjs --target current      # against current/main scripts
node run-parity.mjs --target refactored   # against worktree scripts
node run-parity.mjs --filter dispatcher   # subset by name
node run-parity.mjs --bail                # stop on first fail
node run-parity.mjs --update              # rewrite fixtures from current output (DANGEROUS)
```

## Adding fixtures

For a new behavior you want to pin:

1. Decide the category (dispatcher / runner / monitor / filter / manifest / help / audit).
2. Add a fixture file under `baseline/<category>/<descriptive-name>.{stdout,exit,json}`.
3. Update `run-parity.mjs` if the category needs new invocation logic.
4. If the fixture captures a documented bug the refactor will fix, add a `KB-NNN` entry in `KNOWN-BUGS.md`.

## Fixture file conventions

- `<scenario>.stdout` — captured stdout (LF line endings, UTF-8)
- `<scenario>.stderr` — captured stderr
- `<scenario>.exit` — exit code as a single integer line
- `<scenario>.json` — captured JSON output (formatted)
- `<scenario>.cmd` — the command line used to capture (for reproduction)

## Cleanup

Tests clean up their own tmpdirs via `try/finally`. If a test process is killed, run:
```bash
rm -rf "$(dirname "$(mktemp -u)")/orchestrate-*"
```
