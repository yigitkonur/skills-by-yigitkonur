# Recurring Issue — "We Already Fixed This"

Operation: **Sense-Making** (`Op: SenseMaking`), systemic variant. For one-off bugs use `bug-tracing.md`; for generic research/judgment use `sense-making.md`.

Workflow for problems where point fixes haven't worked, the symptom keeps coming back (or moves to a different surface), or a fix in one place re-creates the problem somewhere else.

The bug-tracing workflow (`bug-tracing.md`) finds the smallest causal point for a *specific* failure. Recurring-issue workflow finds the *structural* cause that generates the failure class. Use this when bug-tracing has already been applied 2-3 times and the same family of symptoms returns.

## Triggers

- "We've fixed this three times and it keeps coming back"
- A fix in module X re-creates a similar symptom in module Y
- Metrics improve briefly after each intervention then drift back
- The team uses phrases like "Whac-A-Mole" or "we keep papering over this"
- Bug class repeats across releases under different names

## Workflow

### 1. Iceberg Model — descend the levels

Run the four levels of the Iceberg Model (`frameworks/systems-tools.md` for full mechanics; relevant primer below).

| Level | Question |
|---|---|
| 1. Events | What happened *right now*? (the latest concrete instance) |
| 2. Patterns | What's been happening over time? Trends? |
| 3. Structures | What processes / dependencies / feedback loops produce the patterns? |
| 4. Mental models | What beliefs / values / assumptions drive the structures? |

Intervene at the deepest level you can credibly afford. Event-level fixes have the lowest leverage; mental-model fixes have the highest.

### 2. Connection Circles — map the circular causality

If the Iceberg surfaces structures, map them as a Connection Circle (`frameworks/systems-tools.md`):

1. List 5-10 system elements (each a noun that can increase/decrease).
2. Draw arrows showing direct causation, signed `+` (source increases target) or `−` (source decreases target).
3. Find closed loops — chains that cycle back to their start. Each closed loop is a feedback loop.

### 3. Classify each loop — Reinforcing or Balancing

Per loop, classify:

- **Reinforcing**: A↑ → B↑ → A↑↑ (exponential amplification). Virtuous (good direction) or vicious (bad direction).
- **Balancing**: A drifts away from goal → correction kicks in → A returns to goal (stability).

### 4. Pick the intervention

| Loop type | Intervention |
|---|---|
| Vicious reinforcing | Find the weakest link in the cycle; break it there. Do not add more of the amplifying input — you accelerate the wrong direction. |
| Virtuous reinforcing | Find the inputs that accelerate it; invest in those. |
| Balancing that resists your fix | Surface the *implicit goal* the loop defends. The goal is usually what needs to change, not the mechanism. |
| Balancing that's useful | Don't break it; understand what it's protecting. |

### 5. Apply the core loop on the chosen intervention

Treat the chosen intervention as the input to a normal Phase A → D pass. Tier is usually Medium or High because structural interventions touch multiple surfaces. Stress-test trio is mandatory.

## Worked example

Symptom: the same release-night bug pattern keeps appearing — different file each time, but always related to session state.

**Iceberg**:
- Events: bug in release 2024-11-02 — null session in middleware
- Patterns: 4 of last 5 releases shipped with session-related P1 bugs
- Structures: no pre-release QA gate; testing absorbed by on-call; deployment cadence outpaces test coverage growth
- Mental models: "QA slows us down", "bugs are an on-call problem, not an engineering problem"

**Connection Circle** (a subset):
```
deploy_frequency (+)→ feature_volume
feature_volume   (+)→ untested_paths
untested_paths   (+)→ release_bugs
release_bugs     (+)→ on_call_load
on_call_load     (−)→ engineering_capacity
engineering_capacity (−)→ test_coverage
test_coverage   (−)→ untested_paths   ← closes loop (REINFORCING, vicious)
```

**Classification**: vicious reinforcing loop (more deploys → more bugs → less capacity → less testing → more bugs).

**Intervention**: weakest link is `untested_paths`. Add a pre-release gate that holds the deploy until coverage on touched code is verified. Break the cycle there, not by hiring more on-call (which accelerates the wrong direction).

## When NOT to use this workflow

- The bug is genuinely a one-off (no pattern across releases) → use `bug-tracing.md`
- The system is stable (no feedback dynamics) → use `bug-tracing.md` + `frameworks/decomposition-tools.md`
- You are at Fail #1 of the 3-fails rule in `do-debug` — don't escalate prematurely; use bug-tracing first
- The "recurring" pattern is actually three distinct bugs that share a vague symptom → split them, treat each as its own bug

## Output (for Solo mode)

Per `foundations/output-contract.md` Minto Pyramid:

```
Recommendation: <intervention at the chosen Iceberg level + Connection Circle weakest link>.

Why:
- Iceberg findings: <pattern → structure → mental-model chain>
- Loop classification: <reinforcing/balancing> at <which elements>
- Weakest link: <where to intervene + why>

Stress-test passes (SenseMaking trio — required for this Op variant):
- Inversion: <H × H failure mode + mitigation>
- Ladder of Inference: <jumped rungs found in the chosen intervention's reasoning, or "none found">
- Second-Order: <10-month chain — does the intervention create a new loop?>

Verification: <metric to watch + threshold + observation window — typically 2-3 release cycles>
```

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Skipping Iceberg, going straight to Connection Circles | Connection Circles map the Structures level. Without Iceberg, you may map at the wrong level (events vs. structures) and find no leverage. |
| Mapping 30 elements in one Connection Circle | Cap at ~10. If the system has more, decompose into sub-systems first. |
| Treating a closed loop as linear cause-effect | If tracing arrows returns to the start, it's a loop — use feedback-loop terminology. Linear thinking misses the dynamic. |
| Trying to break a reinforcing loop by adding more input | You accelerate the direction. Break at the weakest edge instead. |
| Intervening on a balancing loop without finding the goal | The loop defends the goal — your intervention gets absorbed. Surface the goal first; consider whether the goal is what needs to change. |
| Stopping at the Patterns level | Leverage is at Structures + Mental Models. Push deeper. |
