# Thinking Methods Catalog

## Read this if
- You need to select methods intentionally instead of guessing.
- You want better planning quality under uncertainty.
- You want brief, use-case-driven guidance for each method.

## Planning vision
Use methods as lenses, not rituals. Pick the smallest method stack that improves clarity and decisions.

## Method selection flowchart

Use this to pick a starting method based on your situation:

```
What's your situation?
│
├── Unclear what the problem is
│   ├── Request is vague ──────────► First principles + Abstraction laddering
│   ├── Scope is messy ───────────► Issue trees + Concept map
│   └── Assumptions dominate ─────► First principles + Ladder of inference
│
├── Problem is clear, need to find cause
│   ├── Single incident ──────────► 5 Whys + Ishikawa
│   ├── Recurring pattern ────────► Iceberg Model + feedback loops
│   └── Complex multi-cause ──────► Fault tree + Hypothesis testing
│
├── Need to choose between options
│   ├── Quantifiable criteria ────► Decision matrix + RICE
│   ├── Values conflict ──────────► Hard choice model + Six Hats
│   └── High uncertainty ─────────► Cynefin + safe-to-learn experiments
│
├── Need to prioritize work
│   ├── Backlog overwhelm ────────► RICE + MoSCoW + Impact-Effort
│   ├── Urgency pressure ─────────► Eisenhower + OODA
│   └── Strategic sequencing ─────► Second-order thinking + dependency map
│
└── Need to communicate/align
    ├── Executive update ─────────► Minto Pyramid
    ├── Team feedback ────────────► SBI
    └── Cross-team conflict ──────► Six Hats + Conflict Resolution
```

## Method chooser by planning phase

- **Frame problem**: First principles, Abstraction laddering, Issue trees, Concept map
- **Diagnose cause**: Ishikawa Diagram, Iceberg Model, Inversion, Ladder of inference
- **Design options**: Zwicky box, Productive Thinking Model, Six Thinking Hats
- **Decide**: Decision matrix, Hard choice model, Second-order thinking, Cynefin framework
- **Prioritize and sequence**: Eisenhower Matrix, Impact-Effort Matrix, Confidence determines speed vs. quality
- **Execute adaptively**: OODA loop, balancing/reinforcing feedback loops
- **Align people**: Minto Pyramid, Situation-Behavior-Impact, Conflict Resolution Diagram

## Method evaluations (use case + planning posture)

### Decision Making

#### Six Thinking Hats
- Use case: group decisions with narrow perspective or repeated debate loops.
- Planning posture: split thinking modes (facts, caution, optimism, emotion, creativity, process control).
- Best output: balanced decision notes with explicit perspective coverage.
- Watch out: do not let one hat dominate the whole conversation.
- Skip when: the decision is data-driven with clear metrics — use a decision matrix instead.

#### Eisenhower Matrix
- Use case: overloaded task list where urgency crowds out strategic work.
- Planning posture: separate urgent from important before sequencing.
- Best output: do/schedule/delegate/drop map.
- Watch out: avoid labeling everything "urgent."
- Skip when: all tasks serve a single goal and sequencing is the real problem — use dependency mapping.

#### Second-order thinking
- Use case: decisions with delayed effects or ecosystem impact.
- Planning posture: trace consequence chains beyond first-order outcome.
- Best output: downstream impact map with risk checkpoints.
- Watch out: avoid analysis paralysis; go one useful layer deeper, not ten.
- Skip when: the decision is easily reversible and low-cost — just act and observe.

#### Decision matrix
- Use case: several options and measurable criteria.
- Planning posture: make criteria and weights explicit before selecting.
- Best output: transparent scoring table with rationale.
- Watch out: poor criteria weighting can fake objectivity.
- Skip when: options differ on values, not measurable attributes — use the hard choice model.

#### Impact-Effort Matrix
- Use case: backlog prioritization and sequencing.
- Planning posture: maximize high-impact/low-effort early gains.
- Best output: quick wins vs strategic bets plan.
- Watch out: easy work can crowd out foundational but harder work.
- Skip when: effort estimates are unreliable — validate estimates first or use RICE for a more structured score.

#### Hard choice model
- Use case: options are hard to compare because values conflict.
- Planning posture: acknowledge value conflict; choose principle-aligned direction.
- Best output: value-based decision statement.
- Watch out: pretending there is a purely objective winner.
- Skip when: criteria are clearly quantifiable — a decision matrix will be faster and more transparent.

#### OODA loop
- Use case: fast-changing conditions or uncertain execution.
- Planning posture: short cycles of observe-orient-decide-act.
- Best output: rapid iteration plan with review cadence.
- Watch out: acting quickly without proper orientation.
- Skip when: the environment is stable and a thorough upfront plan is feasible — speed cycling adds overhead.

#### Cynefin framework
- Use case: determining planning approach in different context types.
- Planning posture: classify context (clear/complicated/complex/chaotic) before action style.
- Best output: context-fit decision mode.
- Watch out: forcing complex situations into rigid best practices.
- Skip when: the domain is well-understood by everyone involved — classification adds no new insight.

#### Confidence determines speed vs. quality
- Use case: choosing execution pace under uncertainty.
- Planning posture: pace by confidence in problem importance and solution correctness.
- Best output: explicit operating mode (explore vs execute).
- Watch out: false confidence leading to premature lock-in.
- Skip when: external deadlines dictate pace regardless of confidence level.

#### RICE scoring
- Use case: backlog or feature prioritization when multiple factors matter.
- Planning posture: score each item on Reach, Impact, Confidence, and Effort to produce a single comparable number.
- Best output: ranked priority list with transparent rationale per item.
- Watch out: gaming confidence scores to inflate pet projects; ensure Reach and Impact use real data.
- Skip when: the backlog is small enough to reason about directly, or when qualitative judgment matters more than numeric ranking.

#### MoSCoW
- Use case: scope negotiation and release planning when stakeholders disagree on what to include.
- Planning posture: categorize items as Must have, Should have, Could have, Won't have (this time).
- Best output: clear scope boundary with explicit deferral list.
- Watch out: labeling everything "Must have" — if more than 60% is Must, the categorization has failed.
- Skip when: you need numeric ranking, not categorical buckets — use RICE or Impact-Effort instead.

### Problem Solving

#### Ishikawa Diagram
- Use case: many possible causes behind one visible problem.
- Planning posture: categorize causes before narrowing.
- Best output: cause map by category.
- Watch out: treating brainstormed causes as proven causes.
- Skip when: the cause is already known and you just need a fix — jump to solution design.

#### 5 Whys
- Use case: a single incident or failure needs root-cause tracing through a causal chain.
- Planning posture: ask "why" iteratively until you reach a systemic or actionable root cause (typically 3-7 iterations).
- Best output: causal chain from symptom to root cause with the deepest actionable intervention point identified.
- Watch out: stopping at symptoms disguised as causes; accepting a single linear chain when multiple causes interact; blame-oriented "whys" that target people instead of systems.
- Skip when: the problem has multiple independent causes — use Ishikawa or fault tree analysis instead.

#### Abstraction laddering
- Use case: team is stuck too high-level or too detailed.
- Planning posture: alternate "why" and "how" to find usable framing level.
- Best output: aligned problem statement across levels.
- Watch out: staying in abstraction without execution translation.
- Skip when: the problem framing is already agreed on — move to solution generation.

#### Conflict Resolution Diagram
- Use case: goals appear mutually exclusive across stakeholders.
- Planning posture: uncover shared objective beneath opposing demands.
- Best output: win-win constraint redesign.
- Watch out: solving positions instead of underlying needs.
- Skip when: the conflict is about resource allocation, not goals — use prioritization methods instead.

#### Zwicky box
- Use case: option space is too narrow or conventional.
- Planning posture: generate combinations across dimensions.
- Best output: expanded option set for evaluation.
- Watch out: excessive combinations without filtering criteria.
- Skip when: the solution space is already well-explored — generating more options delays decision.

#### Productive Thinking Model
- Use case: need creativity plus practical execution.
- Planning posture: move from "what is" to "what could be" to "what will be done."
- Best output: realistic innovation path.
- Watch out: skipping resource alignment step.
- Skip when: the problem needs speed, not novelty — use a simpler decide-and-act loop.

#### Pre-mortem / Inversion
- Use case: risk-heavy decisions, unclear path forward, or high-stakes launches where failure cost is severe.
- Planning posture: imagine the project has already failed, then work backward to identify what caused the failure. Complement with inversion: define what you must avoid, then design safeguards against each failure mode.
- Best output: ranked failure mode list with prevention triggers, ownership assignments, and early-warning signals.
- Watch out: becoming only defensive and not designing forward progress; anchoring on dramatic but unlikely failures while ignoring mundane ones; skipping the "what would we do differently" step after listing failures.
- Technique — pre-mortem steps: (1) assume failure, (2) each person independently lists reasons, (3) aggregate and rank by likelihood × impact, (4) assign prevention owners, (5) define tripwire metrics that trigger contingency.
- Skip when: the decision is low-stakes and easily reversible — the ceremony adds overhead without proportional risk reduction.

#### Issue trees
- Use case: complex problems need structured decomposition.
- Planning posture: break into MECE branches and prioritize branches.
- Best output: branch-based problem map.
- Watch out: over-decomposition into noise-level detail.
- Skip when: the problem is narrow and well-defined — decomposition adds unnecessary structure.

#### First principles
- Use case: inherited assumptions block better solutions.
- Planning posture: rebuild from basic truths.
- Best output: clean decision logic from fundamentals.
- Watch out: ignoring practical constraints while reasoning from fundamentals.
- Skip when: the domain has well-established best practices that genuinely apply — rebuilding from scratch wastes time.

### Systems Thinking

#### Iceberg Model
- Use case: recurring events suggest deeper system causes.
- Planning posture: analyze event -> pattern -> structure -> mental model.
- Best output: layered diagnosis.
- Watch out: stopping at pattern level without structure changes.
- Skip when: the event is genuinely one-off with no systemic pattern — use 5 Whys for the specific incident.

#### Connection circles
- Use case: complex interactions and unclear influence paths.
- Planning posture: map directional relationships and loop candidates.
- Best output: influence network with candidate loops.
- Watch out: too many variables reduce usefulness.
- Skip when: the system has fewer than four interacting variables — a simple list of dependencies suffices.

#### Concept map
- Use case: low shared understanding across stakeholders.
- Planning posture: explicitly define concepts and relations.
- Best output: shared map for planning alignment.
- Watch out: map becoming decorative instead of decision-supportive.
- Skip when: the team already has shared vocabulary and mental model — the map adds process without insight.

#### Balancing feedback loop
- Use case: interventions get neutralized over time.
- Planning posture: identify stabilizing forces and reduce counter-pressure.
- Best output: resistance-aware intervention plan.
- Watch out: assuming resistance means change is wrong.
- Skip when: the system is not self-correcting — look for reinforcing loops or external blockers instead.

#### Reinforcing feedback loop
- Use case: growth/decline accelerates nonlinearly.
- Planning posture: identify amplifiers and design control levers.
- Best output: amplification control strategy.
- Watch out: ignoring runaway negative loops until too late.
- Skip when: growth is linear and predictable — the feedback model adds false complexity.

### Communication

#### Situation-Behavior-Impact
- Use case: performance or process feedback needs clarity.
- Planning posture: describe observation and impact without judgment.
- Best output: actionable feedback message.
- Watch out: adding assumptions about intent as if they were facts.
- Skip when: the feedback is positive and simple — a direct "thank you, that helped because X" works fine.

#### Minto Pyramid
- Use case: decision communication to leaders or broad stakeholders.
- Planning posture: lead with recommendation, then grouped supporting logic.
- Best output: concise executive brief.
- Watch out: burying the recommendation in background detail.
- Skip when: the audience wants to explore options collaboratively — leading with a conclusion shuts down discussion.

#### Ladder of inference
- Use case: conversations suffer from conclusion-jumping.
- Planning posture: audit path from data to action.
- Best output: de-biased reasoning trace.
- Watch out: treating interpretation as objective reality.
- Skip when: the conclusion is based on direct, unambiguous data — the audit adds no value.

## Anti-patterns: common misuses of thinking methods

| Anti-pattern | Description | Fix |
|---|---|---|
| Decision matrix for values conflicts | Using weighted scores when options differ on principles, not metrics. Scores create false objectivity. | Switch to the hard choice model; make the value trade-off explicit. |
| 5 Whys stopping at symptoms | Accepting "human error" or "bad communication" as a root cause instead of asking what system allowed it. | Keep asking until you reach a systemic or structural cause you can change. |
| Systems thinking for obvious causes | Mapping feedback loops and icebergs when the cause is a known, isolated defect. | Use 5 Whys or direct fix; save systems thinking for recurring or emergent issues. |
| Eisenhower with no delegation path | Placing items in "delegate" quadrant when no one is available to take them. | Treat un-delegable items as do-or-drop; fix the delegation gap separately. |
| Six Hats as sequential monologue | One person cycling through all hats alone instead of the group wearing one hat at a time. | Enforce one hat at a time for the whole group; rotate together. |
| RICE without real data | Filling in Reach and Impact with guesses instead of metrics. Produces ranked noise. | Use rough estimates only when directionally useful; validate top items with data before committing. |
| MoSCoW with 80% Must-haves | Labeling nearly everything as Must, making the method useless for scope negotiation. | Cap Must-haves at 60% of capacity; force explicit trade-offs for the rest. |
| Pre-mortem anchoring on drama | Listing spectacular but unlikely failures while ignoring mundane, high-probability ones. | Score by likelihood × impact; prioritize boring-but-likely failures first. |
| Inversion without forward design | Spending all time listing what could go wrong and never designing the positive path. | Time-box the inversion phase; follow immediately with forward solution design. |
| Over-stacking methods | Applying four or five methods to a problem that needs one. Adds process overhead without proportional insight. | Start with one method; add a second only if the first leaves a clear gap. |

## Quick-reference card

| Method | Best for | Input needed | Output | Time |
|---|---|---|---|---|
| Six Thinking Hats | Group decisions, perspective diversity | Problem statement, group | Balanced decision notes | 30-60 min |
| Eisenhower Matrix | Task overload triage | Full task list | Do/schedule/delegate/drop map | 15-30 min |
| Second-order thinking | Delayed-effect decisions | Decision + context | Downstream impact map | 20-40 min |
| Decision matrix | Multi-criteria comparison | Options, criteria, weights | Scored ranking table | 20-45 min |
| Impact-Effort Matrix | Backlog prioritization | Item list with rough estimates | Quick wins vs. strategic bets | 15-30 min |
| Hard choice model | Values-conflict decisions | Options, competing values | Value-based decision statement | 20-40 min |
| OODA loop | Fast-changing execution | Real-time observations | Rapid iteration plan | 5-15 min/cycle |
| Cynefin framework | Context classification | Situation description | Context-fit action mode | 10-20 min |
| Confidence → speed/quality | Execution pace setting | Confidence assessment | Explore vs. execute mode | 5-10 min |
| RICE scoring | Feature/backlog ranking | Reach, Impact, Confidence, Effort | Ranked priority list | 30-60 min |
| MoSCoW | Scope negotiation | Feature/requirement list | Must/Should/Could/Won't buckets | 20-40 min |
| Ishikawa Diagram | Multi-cause diagnosis | Problem statement | Cause map by category | 30-60 min |
| 5 Whys | Single-incident root cause | Incident description | Causal chain to root cause | 10-20 min |
| Abstraction laddering | Problem reframing | Stuck problem statement | Aligned problem framing | 15-30 min |
| Conflict Resolution Diagram | Stakeholder goal conflicts | Opposing positions | Win-win constraint redesign | 30-60 min |
| Zwicky box | Option space expansion | Problem dimensions | Combinatorial option set | 30-60 min |
| Productive Thinking Model | Creative + practical solutions | Problem brief | Realistic innovation path | 45-90 min |
| Pre-mortem / Inversion | Risk-heavy decisions | Plan or proposal | Failure mode list + safeguards | 30-60 min |
| Issue trees | Complex problem decomposition | Problem statement | MECE branch map | 20-45 min |
| First principles | Assumption-blocked problems | Domain assumptions | Clean decision logic | 20-45 min |
| Iceberg Model | Recurring event diagnosis | Event history | Layered diagnosis (event→model) | 30-60 min |
| Connection circles | Complex system interactions | Variable list | Influence network + loops | 30-60 min |
| Concept map | Low shared understanding | Domain concepts | Shared concept-relation map | 30-60 min |
| Balancing feedback loop | Self-correcting system resistance | Intervention plan | Resistance-aware plan | 20-40 min |
| Reinforcing feedback loop | Nonlinear growth/decline | System variables | Amplification control strategy | 20-40 min |
| Situation-Behavior-Impact | Clear feedback delivery | Observed behavior | Actionable feedback message | 5-10 min |
| Minto Pyramid | Executive communication | Decision + reasoning | Concise executive brief | 15-30 min |
| Ladder of inference | De-biasing conclusions | Conclusion + data trail | Reasoning trace audit | 10-20 min |

## Recommended method stacks by use case

- **Unclear request** -> First principles + Abstraction laddering + Issue trees
- **Recurring incident** -> Ishikawa + Iceberg + Inversion
- **Competing strategy options** -> Decision matrix + Second-order thinking + Hard choice model
- **Fast-moving execution** -> OODA + Confidence determines speed vs. quality + Impact-Effort Matrix
- **System side effects** -> Connection circles + feedback loops + Concept map
- **Stakeholder friction** -> Six Thinking Hats + Conflict Resolution Diagram + SBI
- **Executive communication** -> Minto Pyramid + Ladder of inference check

## Practical caution
Do not use methods mechanically. Choose methods by decision need, context complexity, and available evidence.
