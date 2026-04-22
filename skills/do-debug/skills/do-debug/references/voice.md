# Voice — Debugging-Specific Forbidden Phrases and Required Forms

This file scopes the voice discipline to debugging. For general completion-voice rules (e.g., "looks good", "probably fine" in status reports), see `skills/check-completion/skills/check-completion/references/voice-discipline.md` — the two are complementary, not overlapping.

## The principle

Debugging voice is the tell. Agents rationalize skipping Phase 1 or Phase 3 by describing fixes with phrases that sound like progress but carry no evidence. A disciplined agent either writes a named mechanism + evidence, or admits uncertainty explicitly. This file enumerates the forbidden phrases and the required forms that replace them.

## Forbidden phrases

The ten phrases below are the tells that an agent is about to skip a phase. Every one of them is banned in progress updates, code comments, commit messages, and internal reasoning during a debug session.

| Forbidden | Why banned |
|---|---|
| "Let me just try…" | "Just" signals skipping. Every fix attempt requires a Phase 3 falsification prediction. |
| "Probably a quick fix" | "Probably" is not a status. Before editing, state the mechanism and the evidence. |
| "I know what this is" (without naming mechanism) | Say the mechanism out loud, or you do not know what this is. |
| "This feels like last time" | Gut-match is Phase 2 raw material, not Phase 3 confirmation. Verify independently. |
| "Should be fine now" | "Should" is untested. Run the Phase 1 repro and report the result. |
| "Worth a shot" | Every fix needs a falsification prediction. "Worth a shot" is code for "I have no prediction." |
| "I see the issue" (without mechanism statement) | You have seen the symptom. The issue is the mechanism, which you have not named. |
| "Just a hunch" | Hunches are Phase 2 candidates. Test the hunch in Phase 3 or discard it. |
| "I already know because…" | If the "because" clause references a prior bug's pattern without current evidence, you are skipping to Phase 4. |
| "This is similar to the one I fixed last week" | Similarity is Phase 2 raw material. Similar bugs have non-similar mechanisms often enough to warrant Phase 3 verification. |

If you catch yourself writing any of these — in any medium, including internal reasoning — stop. Replace with one of the required forms below.

## Required forms

The seven templates below replace the forbidden phrases with evidence-bearing alternatives.

### Phase 1 status

> **"Phase 1 symptom card:**
> Symptom: <observable failure>
> Repro: <command / steps, fails N/N>
> Evidence: <trace / log / diff / config value>"

Not: "Looking into the bug now."

### Phase 2 candidate listing

> **"Phase 2 candidates:**
> 1. <mechanism: 'X caused Y because Z'> — evidence: <...>
> 2. <mechanism> — evidence: <...>
> 3. <mechanism> — evidence: <...>
> Ranked by disprovability: 1, 2, 3."

Not: "I have a few ideas."

### Phase 3 falsification prediction

> **"Phase 3 experiment:**
> Candidate: <mechanism from Phase 2>
> True prediction: if the hypothesis holds, <observable>
> False prediction: if the hypothesis is wrong, <observable different from above>
> Experiment: <command / test>
> Result: <observed>"

Not: "Let me add a log and see what happens."

### Phase 4 fix + regression guard

> **"Phase 4 fix:**
> Mechanism confirmed: <from Phase 3>
> Layer (from defense-in-depth): <1 / 2 / 3 / 4>
> Narrowest change: <diff or description, scoped to the mechanism>
> Regression guard: <test / assertion / invariant that fails without the fix>
> Verification: <Phase 1 repro result>"

Not: "Fixed it, shipping."

### Uncertainty / "I don't know yet"

> **"Uncertain:**
> What I know: <the evidence so far>
> What I don't know: <the specific gap>
> Next cheap check: <what I will do to close the gap>"

Not: "Hmm, not sure."

### Handoff to another skill

> **"Routing to <skill>:**
> Why: <one sentence — stuck-point this skill does not resolve>
> Context: <Phase 1/2/3 artifacts that the target skill needs>
> Expected return: <what I need back from the target skill before re-entering>"

Not: "Let me run brainstorm."

### Pushback on the user or a senior's diagnosis

> **"Pushing back:**
> The proposed mechanism: <what they said>
> My Phase 3 experiment: <test you ran>
> Result: <observed — does not match the proposed mechanism>
> Candidate I'm testing instead: <mechanism>"

Not: "I don't think that's right."

## Commitment checkpoints

Persuasion principle (Commitment) applied: announce phase entry. This is a checkpoint the next phase can verify.

- At Phase 1 entry: "Entering Phase 1. Symptom card to follow."
- At Phase 2 entry: "Phase 1 complete. Symptom card: <card>. Entering Phase 2."
- At Phase 3 entry: "Phase 2 complete. Ranked candidates: <list>. Entering Phase 3 with top candidate: <name>."
- At Phase 4 entry: "Phase 3 complete. Mechanism confirmed: <name>. Entering Phase 4."
- At done: "Phase 4 complete. Fix: <name>. Regression guard: <name>. Phase 1 repro: passes. Routing to check-completion / declaring done."

These feel formal. That's the point — the formality is the commitment.

## Authority framing

Persuasion principle (Authority) applied: evidence-bearing language signals authority, not swagger.

- Evidence-bearing: "I traced the call chain in root-cause-tracing.md §1.1. The violation enters at frame 2."
- Not: "I'm pretty sure the issue is at frame 2."

- Evidence-bearing: "The repro fails 10/10 with `pnpm test`; passes 10/10 with `pnpm test auth`."
- Not: "It seems to fail in CI."

- Evidence-bearing: "Phase 3 experiment predicted `observed_value=3`. Observed: 3. Candidate confirmed."
- Not: "My fix worked."

Authority comes from the evidence. Omit the evidence and you lose the authority.

## Scarcity framing

Persuasion principle (Scarcity) applied: the Iron Law creates scarcity of shortcut paths.

- Scarcity: "No fix without root cause. This is non-negotiable."
- Not scarcity: "We should probably investigate first."

- Scarcity: "Only one hypothesis gets tested at a time. Testing two fixes simultaneously discards the signal of both."
- Not scarcity: "It's usually a good idea to test one thing at a time."

Scarcity does not mean aggressive language. It means the rule has no exception path; making that visible prevents the rationalization "just this once."

## Persuasion principles applied — the research

Meincke et al. (2025) tested Authority + Commitment + Scarcity on LLM compliance and observed compliance shift from 33% to 72% (p<.001). For a discipline skill (this one), the three principles apply as:

- **Authority** — evidence-bearing voice (above)
- **Commitment** — phase-entry announcements (above)
- **Scarcity** — the Iron Law with no exception path (above)

This is why the voice rules are non-decorative. They measurably raise the probability that the skill's discipline holds under pressure.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Writing "Let me just try…" anywhere | Delete mid-sentence; replace with Phase 3 experiment template |
| Saying "probably" without evidence | Either attach evidence or admit uncertainty ("uncertain: …") |
| Announcing the fix worked before running the Phase 1 repro | The Phase 1 repro result IS the claim. Report it, not "worked". |
| Describing the mechanism as "similar to" something | Similarity is Phase 2 raw material; state the specific mechanism |
| Using "we can always" / "let's just" / "obvious that" | All three are tells — stop and apply a required form |
