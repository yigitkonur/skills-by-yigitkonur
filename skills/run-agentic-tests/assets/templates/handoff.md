# Worker handoff

The controller supplies exact values. Remove unused fields rather than leaving
ambiguous placeholders. This supplements the CLI-generated task/handoff; it does
not allocate identities or override its canonical task.

## Assignment

- Role and actual task/actor ID:
- Campaign path and installed CLI path:
- Requested action and bounded outcome:
- Case/spec/round/target/source identity, when applicable:
- Required role/common references and exact input artifact paths:
- Exact writable draft/artifact paths and required output kinds:
- Resource read/write claims and lease/reset boundaries:
- Native host handle, once bound:

## Completion contract

State what every required output must establish, the exact submission mechanism,
and the receipt fields that allow the worker to finish. The orchestrator confirms
actual host termination. If no truthful typed output is possible, retain the
partial draft and return the exact blocker; never fabricate mandatory fields.

## Retry context

- Previous failure with record/artifact references:
- What changed:
- New hypothesis and supporting evidence:
- What not to repeat:
- Stable finding/lineage and remaining attempts:
- Existing issue and PR references:

## Role boundaries

Name the assigned role's concrete read/write/execute permissions. Workers do not
spawn workers. An executor does not verify itself; an implementer does not count
its own run as the independent retest. A verifier inspects saved artifacts only;
new execution is requested from the orchestrator.

## Blind-verifier input check

For verifier B, include original spec/target/execution/evidence only. Exclude
verifier A's files, outcomes, discussion, and summaries from every input channel.
If the host inherited a peer judgment, report the lost blindness before review.
