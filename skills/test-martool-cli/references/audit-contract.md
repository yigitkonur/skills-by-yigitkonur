# Audit and report contract

Use this contract to decide what the combined runner proves and what its JSON may legitimately be called.

## Authoritative inputs

The runner delegates to martool's current executable harnesses:

| Matrix | Martool entrypoint | Scope |
|---|---|---|
| Generated commands | `scripts/audit-martool-generated-flags.mjs` | Commands and flags published in the generated command manifest |
| Platform commands | `scripts/audit-martool-platform-flags.mjs` | Platform leaves, positionals, flags, aliases, repeatable forms, scoped usage, and failure channels |

Both harnesses obtain their plan from the built CLI's `usage --json` output. The skill runner must not maintain a second list of commands, flags, enums, aliases, or expected case counts.

## Full versus diagnostic scope

| Invocation | Combined verdict on success | Exhaustive claim allowed? |
|---|---|---|
| `--matrix all`, no command filter | `verified` | Yes, for the pinned target and this run |
| One `--matrix` only | `diagnostic-pass` | No |
| Any `--command` filter | `diagnostic-pass` | No |

Exit zero means the selected scope passed. It does not expand a diagnostic scope into full release evidence. Always read `selection` and `verdict` together.

## Required generated-matrix invariants

The generated report passes only when:

- `schema_version` is `1`;
- `audit` is `martool-generated-flags`;
- variant and baseline failure totals are zero;
- `coverage.complete` is true;
- missing and unexpected case lists are empty; and
- planned/completed case IDs contain no duplicates.

The harness creates a fresh HOME, XDG roots, working directory, and martool workspace for every runtime case. Provider-capable generated commands execute in sandbox/dry-run/read-only test conditions.

## Required platform-matrix invariants

Every platform report, including a diagnostic, requires:

- `schema_version` is `1`;
- `audit` is `martool-platform-flags`;
- at least one selected case was attempted;
- the failed-case total is zero;
- manifest duplicate command and flag lists are empty;
- unexpected and duplicate-plan case lists are empty;
- `safety.provider_calls` is zero; and
- `safety.paid_provider_calls` is zero.

A full platform run additionally requires no missing cases, uncovered flags, or uncovered positionals, and `reachable_commands` equal to `total_commands`.

The harness routes provider-capable identity to an owned loopback counter. Any observed provider call fails the run; credentials are neither necessary nor a valid repair.

## Target pinning

Source mode records the checkout path, built binary, and Git commit when available.

Coolify mode records:

- SSH host alias or hostname;
- Coolify project and service label values;
- container ID and name;
- configured image reference;
- immutable Docker image ID; and
- health before and after the matrices.

The runner re-inspects the exact container ID after the audits. A missing container, changed image ID, stopped container, or non-healthy state invalidates the combined proof even if raw cases passed.

## Combined report

`combined.json` uses this top-level shape:

```json
{
  "schema_version": "1",
  "audit": "martool-cli-combined",
  "target": {},
  "selection": {
    "matrix": "all",
    "command": null,
    "executed_matrices": ["generated", "platform"]
  },
  "version": {},
  "manifest": {
    "generated_commands": 0,
    "platform_commands": 0,
    "unique_commands": 0
  },
  "checks": {},
  "safety": {
    "local_docker_used": false,
    "paid_provider_calls_allowed": false,
    "remote_environment_dumped": false
  },
  "verdict": "verified",
  "artifacts": {}
}
```

The zero counts above demonstrate types, not expected values. Actual counts are derived from the target manifest.

Each executed check includes its process exit, compact totals/coverage, failures, raw report filename, and SHA-256 hash. Inspect the named raw report for individual case evidence.

## Stream and exit behavior

- stdout: exactly one compact combined JSON object, except human-readable `--help`;
- stderr: progress and underlying harness diagnostics;
- exit `0`: selected scope passed;
- exit `1`: audit, coverage, safety, pinning, or unexpected runtime failure;
- exit `2`: invalid arguments, missing prerequisites, SSH/discovery failure, or other preflight failure.

Do not parse progress text as evidence. Consume stdout or the saved `combined.json`.

## Historical evidence

Earlier martool verification observed 25 generated commands and 35 platform commands, with thousands of derived cases and zero provider calls. These figures are dated examples, not acceptance constants. A later CLI may legitimately change them; exact reconciliation against its own manifest is the invariant.
