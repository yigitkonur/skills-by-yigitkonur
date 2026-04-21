# Rationalizations — RED Baseline for the Iron Law

The Iron Law ("no fix before root cause") is bypassable under pressure. This file catalogs the verbatim excuses agents generate to skip Phase 1 or Phase 3, each paired with a counter. Seeded from obra's three pressure scenarios + two extensions observed in this pack's other discipline skills.

See `build-skills/references/authoring/tdd-for-skills.md` for the RED-GREEN-REFACTOR pattern that produced this table.

## Why the discipline breaks

Four forces push agents to skip Phase 1 or Phase 3:

1. **Time pressure** — outage, deadline, user waiting
2. **Sunk cost** — hours already spent on a failing path, feels wasteful to restart
3. **Authority / social pressure** — someone more senior diagnosed it, team is watching
4. **Confidence theater** — "I see it" feels like evidence, it isn't

The table below catches all four.

## The rationalizations table

| # | Rationalization | Counter |
|---|---|---|
| 1 | "Just try this fix and see." | "See" = evidence. Write the falsification prediction before editing. |
| 2 | "The senior engineer already diagnosed it." | Their Phase 1 is not yours. Reproduce and read the evidence yourself. |
| 3 | "Sunk cost — 4 hours in, can't restart." | The 4 hours are the evidence the current path is dead. Restart Phase 1. |
| 4 | "We don't have time for root cause — production is down." | Cost of a blind fix that regresses = cost of the outage × 2. Phase 1 is faster than fix-guess-regress. |
| 5 | "It's probably just X like last time." | "Probably" is not a status. Pattern-match is Phase 2, not a skip to Phase 4. |
| 6 | "The tests pass now, so it's fixed." | Passing tests without a regression guard prove nothing durable. Add the guard, re-run the Phase 1 repro. |
| 7 | "I see the issue." (no mechanism stated) | Say the mechanism out loud, or you have not seen it. |
| 8 | "Let me add one more log and see what happens." | Logs are Phase 2/3 tools, not a hope strategy. Name the hypothesis the log falsifies. |
| 9 | "This is an emergency — rules off." | Rules are *especially* on under pressure. Emergencies multiply the cost of skipping. |
| 10 | "The bug moved — I must be close." | A moved bug is often the same bug with new symptoms. Re-run Phase 1 on the new form. |
| 11 | "I'll document the reasoning after I ship the fix." | The reasoning is the fix. Undocumented fixes resurrect as undocumented bugs. |
| 12 | "The CI passed, merging." | CI is one signal. Did the Phase 1 repro pass? Did the regression guard pass? |
| 13 | "The code is messy — probably a merge issue." | "Probably" again. Either bisect the merge (`references/bisection-strategies.md`) or investigate; do not narrate. |
| 14 | "It's an edge case, not worth a full investigation." | The edge-case label is a rationalization for skipping Phase 1. Reproduce first, classify after. |
| 15 | "I already spent too long on this — let me just patch it." | "Already spent too long" means Phase 1 was skipped and you know it. Restart. |

## How to catch yourself rationalizing

Voice patterns that signal one of the 15 excuses is forming:

- "Let me just…"
- "Probably just…"
- "We can always…"
- "It's obvious that…"
- "I don't have time to…"
- "I already know what this is because…"

When you write or say any of these, stop. Read the matching row in the table. Then write the counter in your own words before proceeding.

## Pressure-scenario sidebars

Full scenarios live in `references/pressure-tests/`. The summaries below name which rationalizations each scenario is designed to surface.

### Academic baseline (`pressure-tests/academic.md`)

No pressure. A clean lab-condition bug. The method should work without friction; the test is whether the skill's structure produces Phase 1 → 4 in order without the agent improvising.

**Surfaces**: none (baseline). If the agent skips Phases under calm conditions, the skill is broken.

### Financial outage (`pressure-tests/pressure-financial.md`)

$15k/min payment API outage. Minute 10: customer tweets. Minute 20: the CEO pings you. "Just get it working."

**Surfaces rationalizations**: #1 ("just try this fix"), #4 ("we don't have time for root cause"), #9 ("emergency, rules off").

**Counter applied**: the cost of a bad fix (regresses in prod, outage extends, rollback needed) exceeds the cost of Phase 1 (10 minutes). Iron Law holds *especially* here.

### Sunk cost (`pressure-tests/pressure-sunk-cost.md`)

4 hours of debugging. You've tried 3 hypotheses. Dinner in 30 minutes. One more idea: "increase the timeout." Tempting.

**Surfaces rationalizations**: #3 ("sunk cost, can't restart"), #15 ("spent too long"), #10 ("bug moved, must be close").

**Counter applied**: 4 failed hypotheses is evidence the Phase 2 pattern family was wrong. The 5th fix will also fail. Restart Phase 1 with the new information (*what did the 4 fails teach about the real mechanism?*).

### Authority / social (`pressure-tests/pressure-authority.md`)

Senior engineer: "I looked at it — the bug is on line 147 of `worker.ts`. Go fix it." Tech lead nods. The team is silent.

**Surfaces rationalizations**: #2 ("senior already diagnosed"), #5 ("probably X like last time"), #7 ("I see the issue").

**Counter applied**: the senior's diagnosis is a *candidate mechanism* (Phase 2 input), not a *confirmed mechanism* (Phase 3 output). Verify it independently. If the senior is wrong, the fix at line 147 fails fix #1, you reopen Phase 2, and you've now done the work you would have done anyway.

### Slack-visibility (extension beyond obra)

Stakeholders are watching in a public channel. Every message is visible. The temptation: perform progress by writing updates that read like progress ("Looking at it now", "Getting close", "Should have something soon") rather than doing Phase 1 investigation quietly.

**Surfaces rationalizations**: #7 ("I see the issue" without mechanism), #11 ("document after I ship"), #13 ("probably a merge issue").

**Counter applied**: progress updates are a separate artifact from the debugging work. Write one clear status per phase ("Phase 1 done — symptom card + 10/10 repro") and keep investigating. Performance for Slack is not performance for the bug.

## Using this table during a debug session

Before writing any fix — even a "quick" one — scan the table. If any row's left column matches what you are about to say or type, stop. Apply the counter. Then decide whether the fix is still justified.

In practice, this table becomes internal voice. The 15 excuses share a fingerprint: they all start with "just", "probably", "we can always", or an explicit appeal to pressure/authority/sunk-cost. Train yourself to hear the fingerprint.

## Extending the table

When a new rationalization surfaces under real pressure — something the table does not cover — add it with a counter. The table is meant to grow. But every new entry must name a specific failure mode; "do not be lazy" is not a row, "treating an 'obvious' fix as tested" is.
