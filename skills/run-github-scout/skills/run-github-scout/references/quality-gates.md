# Quality Gates

Decision points where the orchestrator checks results and decides whether to retry or proceed.

## Search Quality Gate (after each wave)

| Signal | Verdict | Action |
|---|---|---|
| 20+ relevant repos, diverse categories | PASS | Proceed to evaluation |
| 10-19 repos, mostly relevant | PASS with note | Proceed, note thin coverage in summary |
| 5-9 repos, relevant | MARGINAL | Proceed if 2+ waves done; retry if wave 1 |
| <5 repos total | FAIL | Retry with different angles (max 3 waves) |
| Most results are off-topic (wrong domain) | FAIL | Retry with feedback explaining what went wrong |
| Results are all from same org/author | FAIL | Retry broadening to competitors |
| All results are forks of same repo | FAIL | Retry with `-fork:true` or different terms |

## Evaluation Quality Gate (after all agents complete)

| Signal | Verdict | Action |
|---|---|---|
| All repos scored, no gaps | PASS | Proceed to synthesis |
| 1-2 repos have "no data" for a signal | MINOR GAP | Orchestrator fills gaps inline |
| Same repo scored by 2 agents with >15pt difference | INCONSISTENCY | Orchestrator re-evaluates that repo |
| Agent output file is empty/missing | AGENT FAILURE | Re-run that one agent |
| Feature Fit checklist doesn't match user needs | MISMATCH | Orchestrator adjusts scores manually |
| All repos score <40 | WEAK FIELD | Note in summary — the space is immature |

## Retry Budget

| Resource | Max | After exhaustion |
|---|---|---|
| Search waves | 3 | Present what you have, note gaps |
| Evaluation rounds | 2 | Present scores, flag low confidence |
| Agent re-runs (failure recovery) | 1 per agent | Score as "insufficient data" |
| User re-clarifications | 1 | Work with current understanding |

## Feature Detection Quality Gate (after Phase 3.5)

| Signal | Verdict | Action |
|---|---|---|
| All repos have all features checked | PASS | Proceed to synthesis |
| 1-2 repos missing feature data | MINOR GAP | Orchestrator fills inline |
| >50% of cells are "low" confidence | LOW QUALITY | Re-run with more targeted file reads |
| Agent returned no FEATURES_JSON block | AGENT FAILURE | Re-run that agent once |
| Feature list has >15 features | TOO BROAD | Orchestrator trims to top 15 by prevalence |

## When to Stop

Stop and present results when ANY of these is true:
- Search found 20+ repos AND evaluation completed for all
- 3 search waves exhausted
- 2 evaluation rounds completed
- User said "looks good" or "that's enough"
- Total session has dispatched 15+ subagents (cost guard)
