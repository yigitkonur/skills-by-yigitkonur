# Feature and subfeature map

Record product behavior separately from surfaces observed in code. Replace example
rows; this map supports the allocated `feature` result and is not a test verdict.

| Feature | User goal / actor | Subfeature / transition | Product source | Located surface | Existing coverage | Unknowns |
|---|---|---|---|---|---|---|
| Allocated feature ID/title | Concrete user outcome | Independent behavior slice | Actual source or explicit unknown | Route/command/tool/view and source location | Existing scenario/case | Material unresolved expectation |

## Suggested authoring order

List bounded cases by risk and real prerequisite, including permissions, errors,
boundaries, and state reset where relevant. Do not turn this into a global wave
barrier or imply that implemented behavior is already correct.

## Scope decisions

Record imported scenarios, proposed additions, explicit exclusions, and the
authority/source of each decision. Pass missing decisions to the orchestrator.
