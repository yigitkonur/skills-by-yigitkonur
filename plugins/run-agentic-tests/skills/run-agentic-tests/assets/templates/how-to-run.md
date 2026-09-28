# How to run T0001 / S001

Replace this recipe with discovered commands/tool operations for the assigned
application. An executor must not need the author's conversation to perform it.

## Before acting

1. Read the assigned environment record and exact target/source identity.
2. Check native tool/client access from its actual location.
3. Acquire the declared account/database/session/device resource leases.
4. Perform the verified reset and record the initial state.
5. Review retry context when supplied: prior failure, change, hypothesis,
   forbidden repetition, remaining attempts, and issue/PR links.

## Execution recipe

| Step | Actual tool/command and input | Expected observable boundary | Capture path/type and requirement IDs |
|---|---|---|---|
| S01 | Replace with verified setup interaction | Initial state confirmed | Assigned round evidence path |
| S02 | Replace with one actual user action | Result can be observed | ER01 and ER02 mapped to E01 |

Record exact argv/cwd or structured request when applicable. Do not include secret
values. Declare bounded waits based on observable state; do not hide retries
inside a command until it produces a preferred result.

## Stop conditions

Stop and report wrong target, missing lease/credential/tool, source drift, or an
unsafe/unavailable reset. Preserve the actual failure and evidence gaps. Ask the
orchestrator for a corrected assignment; do not edit the application or oracle.

## Outputs

- Assigned execution draft, one per case.
- Captured evidence under this round's `evidences/`, mapped to requirements.
- Every expectation observed or explicitly unavailable.
- `submit --check` and `submit` receipts using the bundled CLI.

The executor reports observations. Independent verifier(s) decide supported
expectation verdicts from these saved artifacts without rerunning the case.
