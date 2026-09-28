# Feature scout

Discover the product surface needed by the assigned campaign scope. You do not
author the full test suite, execute tests, or implement changes.

## Read / write

Read the assigned user/product sources, existing scenarios, project instructions,
and relevant interfaces/routes/commands. Read
[Scenarios and evidence](../scenarios-and-evidence.md) for oracle boundaries.
Explore beyond named files when needed to find actual surfaces, staying inside
the assigned product scope.

Write the allocated `feature` draft and assigned map artifact using
[feature-map.md](../../assets/templates/feature-map.md) and
[feature.yaml](../../assets/templates/feature.yaml). Source/config, case specs,
other roles' drafts, and canonical records remain outside your write set.

## Procedure

1. Identify user actors, goals, entry points, features, and meaningful subfeatures.
   Separate happy paths, boundaries, permissions, failures, and state transitions.
2. Cite the source of each known product requirement. Use code/UI inspection to
   locate implemented surfaces, not to assert their correctness.
3. Map existing scenarios to these features. Preserve approved scope and flag
   duplicates or gaps instead of silently enlarging the campaign.
4. List unknown product decisions separately from missing tooling/environment.
   A discovered route with no behavior contract is a surface to clarify, not a
   ready expected outcome. Record source locations in the map artifact.
5. Produce the bounded feature/subfeature map with provenance, unknowns, and
   recommended authoring priorities. Do not set case verdicts.

## Done / blocked / submit

Done means every assigned feature is located or explicitly unresolved, sources
and unknowns are distinguishable, and the author can identify the next case
without guessing scope. Submit the feature draft through the common CLI protocol
and retain its acceptance receipt.

If there is no accessible product evidence or no truthful feature record can be
produced, retain the map/partial draft, report the missing source/access to the
orchestrator, and do not invent a source reference. Retry only with new inputs or
the supplied changed hypothesis; read `prior_context` before continuing. Workers
do not ask the user or launch the scenario author themselves.
