# Failure Modes

The recovery playbook. Every failure has a *diagnosis* (what went
wrong) and a *recovery* (what to do next). Skipping diagnosis and
going straight to retry is the most expensive anti-pattern.

Read this in **any wave** when something goes wrong.

## Subagent timeout

**Symptom**: subagent exceeds time budget without returning.

**Diagnosis**: scope too broad, or the subagent is looping on a
failing approach.

**Recovery**:
1. Split the scope (smaller mission with narrower DoD).
2. Retry once with the narrower brief.
3. If second attempt fails, log the gap in
   `_meta/07-dispatch-log.md` and either escalate to user or
   accept the gap.

**MAX 2 retries per agent per mission.** Pad budgets are wasted
on the third attempt.

## Subagent returns shallow output

**Symptom**: pack/cross file is thin; few sources cited; no
contradictions surfaced; numeric claims paraphrased rather than
quoted; missing axes silently absent.

**Depth-gate signals** (any one means shallow):
- ≤3 sources cited across the entire output.
- Zero `## Not found` references in the agent's handback.
- Zero `## Follow-up signals` harvested for round 2.
- Zero verbatim quotes for numeric claims.
- Generic "comprehensive coverage" claims without per-axis evidence.

**Recovery**:
1. Send back with specific gaps named: "The brief required 100%
   completion. The following gaps remain: [axis X has no content
   file or insufficient-evidence entry; axis Y's pricing claims
   are paraphrased rather than quoted; the audience-evidence
   section names no Reddit threads]. Address each before
   reporting back."
2. The agent's second attempt usually succeeds when gaps are
   named specifically.
3. If second attempt is still shallow, the brief itself was
   wrong. Rewrite the brief; re-dispatch.

## Two subagents disagree on a fact

**Symptom**: Wave 2 agent A claims X about a shared fact (e.g., a
pricing tier or a feature availability). Wave 3 synthesis surfaces
that agent B working on a different entity claims not-X about the
same fact.

**Diagnosis**: this is data, not error. Either A or B (or both)
is wrong, or the underlying fact has version/scale/context
dependency.

**Recovery**:
1. Surface the contradiction in the relevant `_cross/<axis-slug>/`
   file. Cite both quotes with attribution and date.
2. Tier by source credibility (vendor docs > maintainer > active
   forums > blogs > marketing).
3. If a definitive resolver exists (changelog covering the
   relevant versions, maintainer's reply on the issue tracker),
   scrape it and resolve.
4. If unresolvable, mark in synthesis as "contested; both sources
   verbatim cited; the decider should test against their specific
   <variable>".

Never silently pick one side.

## Discovery missed a `core` entity

**Symptom**: Wave 1A surfaced N entities; during Wave 2, an
agent's research repeatedly references an entity not in
`_meta/02-entities.md`.

**Diagnosis**: the discovery sub-questions had a blind spot. The
missed entity is decision-relevant.

**Recovery**:
1. Add the entity to `_meta/02-entities.md` with the appropriate
   tier.
2. If `core`, add a Wave 4 mission for it (Wave-2-style brief).
3. Re-run Wave 3 cross synthesis after the missed entity's pack
   is complete (sub-wave per affected axis).

## Wave 2 evidence is uniformly thin for one axis

**Symptom**: across 5+ entities, the same axis has weak evidence
— mostly "insufficient evidence" entries.

**Diagnosis**: not that all entities are weak on this axis;
rather, the axis was wrong. Either the axis is not actually
decider-weighted (it's a feature category, not an axis), or the
practitioner channel identified in Wave 1B does not actually
carry this signal.

**Recovery**:
1. Stop. Do not dispatch Wave 3 for this axis.
2. Return to Wave 1B briefly (one targeted subagent) to re-derive
   this specific axis's primitive and channels.
3. Re-dispatch a small Wave 2 follow-up (one entity at a time)
   to fill the corrected axis.
4. If the axis turns out not to be decider-weighted, drop it from
   `_meta/03-axes.md` and remove the corresponding `_cross/`
   folder.

Charter errors are cheaper to fix upstream than to mask with more
research.

## MAX-N cap reached on a folder

**Symptom**: a Wave 2 or Wave 3 subagent's output exceeds the
cap.

**Diagnosis**: either (a) the folder genuinely has too much
content for one folder (rare), or (b) the agent is padding (more
common).

**Recovery**:
1. **If padding**: review the files; merge thin ones (two
   one-paragraph files become one file with two H2 sections).
2. **If genuine overflow**: split the folder. Example:
   `<entity-slug>/01-pricing-and-billing.md` becomes a subfolder
   `<entity-slug>/01-pricing/` with multiple files. Update
   `_meta/06-file-budget.md` to reflect the split.
3. **Never leave the folder over-cap.** The verification gate
   fails on this.

## Provider cascade failure on a key URL

**Symptom**: the run-research skill reports Jina → Scrape.do →
Kernel all failing on a specific URL inside a subagent's session.

**Diagnosis**: WAF or interstitial blocking on that domain. Not a
bug. Common on certain vendor docs portals and aggressively-protected
sites.

**Recovery** (the subagent should already do this per the
run-research failure-modes; if not, re-brief):

1. Find an alternate URL for the same content (vendor blog,
   GitHub mirror, web archive snapshot, postmortem replacing the
   changelog).
2. Scrape the alternate URL.
3. Note the provenance gap in the entity's `09-sources.md` (cite
   the alternate; mark inference where the canonical source is
   missing).

If the canonical content is critical and no alternate exists,
escalate to the user with a specific evidence-gap statement.

## Subagent claims completion without all DoD met

**Symptom**: handback says "100% complete" but verification
reveals a missing axis or missing citation.

**Diagnosis**: silent gap-skipping. The most insidious failure
mode.

**Recovery**:
1. Send back. Always. Silent skipping is the failure mode the
   orchestrator must catch.
2. Specifically name the failed criterion: "The brief required
   every axis addressed; axis X has no file and no
   insufficient-evidence entry. Address before reporting back."
3. If the second attempt also silently skips, the agent
   model/configuration is the issue. Escalate.

## The brief itself is wrong

**Symptom**: subagent reports "the mission is fundamentally
different than described" or returns work that fits the brief but
not the actual research need.

**Diagnosis**: the orchestrator's brief was based on a faulty
charter or a wrong axis catalog.

**Recovery**:
1. Stop dispatching more agents on the wrong basis.
2. Return to Phase 0 or Wave 1 to fix the charter.
3. Re-dispatch with a corrected brief.

This is a Phase 0/1 failure. Do not paper over with Wave 2/3
research.

## Scope creep mid-wave

**Symptom**: the orchestrator notices the brief growing during a
wave (e.g., "while you're at it, also research...").

**Diagnosis**: the original mission was under-scoped, or the new
scope is a Wave 4 mission that does not belong inside this wave.

**Recovery**:
1. Revert the brief to its original scope.
2. New scope = new mission, new wave. Add it to the dispatch log
   for after the current wave completes.

## Multiple Wave 2 agents return in sequence

**Symptom**: Wave 2 has 8 agents in flight; first 3 return;
should the orchestrator wait for all 8 or start integrating?

**Recovery**: process completed agents as they return.

1. Read each completed agent's pack.
2. Cross-reference against the brief's DoD.
3. Update `_meta/07-dispatch-log.md`.
4. Begin reading-and-thinking for the eventual master summary
   while later agents finish.

Do not gate on the slowest agent. The orchestrator's reading
budget is the bottleneck of Phase 7; spreading it across the wave
is more time-efficient.

## When to escalate to the user

The orchestrator handles most failures internally. Escalate to the
user only when:

- **The charter is wrong and the user's intent is unclear.** Ask
  one clarifying question.
- **A `core` entity is gated/waitlist and cannot be researched.**
  Ask whether to drop it from `core` or pause the corpus.
- **A decision-flipping axis cannot be researched (no public
  evidence exists).** Ask whether to commission expert input or
  accept the gap.
- **The corpus has run > 4 waves and gaps remain.** Surface the
  gaps and ask for prioritization.

In every case: name the specific failure, attempt a recommendation,
ask a single concrete question. Do not present a diffuse "what
should I do?" prompt.

## When NOT to retry

Some missions cannot be completed because the evidence does not
exist:

- Topic genuinely not on the open web (internal product, very
  recent release, NDA-gated).
- Provider cascade blocking on every relevant source.
- Question is fundamentally subjective (no source can settle it).

In these cases: document the gap in the master summary's "Open
gaps" section. A retry that finds the same nothing is wasted
budget. Surface the gap with reasoning; let the decider decide
whether to commission expert input or accept the uncertainty.

## The orchestrator's between-wave self-check

Before dispatching the next wave, the orchestrator runs a quick
self-check on the previous wave:

- **Coverage**: every brief's DoD criteria met?
- **Depth**: any depth-gate signals on the returned outputs?
- **Contradictions**: any cross-agent disagreements surfaced for
  Wave 3 or later?
- **Charter validity**: did anything in the wave's outputs
  contradict the charter?
- **Gap log**: is `_meta/07-dispatch-log.md` updated?

If any of these is "no" or "concerning", fix before dispatching
the next wave. Charter errors compound across waves; catch them
upstream.
