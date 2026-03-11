# Derailment Test: plan-work Skill

**Skill under test:** `plan-work`
**Test task:** Monolith vs event-driven microservices decision for a RealWorld Express.js API
**Date:** 2026-03-11
**Method:** Follow SKILL.md steps 1–6 + Final Quality Gate exactly as written
**Tester:** AI agent (Claude) executing skill instructions literally

---

## Part 1: Full Planning Output (Produced by Following the Skill)

### 1. Mission Snapshot

**Classification:** This is primarily a *compare options* decision.
**Prerequisite noted:** Diagnosis of reliability root cause should inform the comparison but is subordinate to the final deliverable (a recommendation).

**Mission sentence:** We need to decide whether to keep the monolithic Express.js architecture (with hardening) or split into event-driven microservices, so that reliability complaints during peak usage are resolved, within the constraints of a six-week release target and a two-engineer team with distributed-systems experience.

### 2. Planning Job + Chosen Method(s)

- **Planning job:** Compare options (architecture decision)
- **Primary method:** Weighted decision matrix
- **Companion:** Sensitivity check (part of decision matrix workflow per reference 03)
- **Reversibility:** Type 1 — hard to reverse. Architecture changes of this scope require months to undo.
- **Reference files used:** `references/03-option-design-and-decision-quality.md`, `references/06-technical-strategy-and-architecture.md`

### 3. Facts, Assumptions, and Unknowns

| Category | Item |
|----------|------|
| **[FACT]** | Codebase is ~2,371 lines of TypeScript across 32 files |
| **[FACT]** | 4 domain areas: Articles, Auth, Profiles, Tags |
| **[FACT]** | Single Express.js process, PostgreSQL via Prisma ORM |
| **[FACT]** | No caching layer, no message queue, no rate limiting |
| **[FACT]** | No health checks, no horizontal scaling infrastructure |
| **[FACT]** | No connection pooling configuration (default Prisma single client) |
| **[FACT]** | Dependencies are minimal (express, prisma, bcrypt, jwt, slugify, cors) |
| **[FACT]** | Single Dockerfile, single-process deployment |
| **[FACT]** | All services directly import the single Prisma client |
| **[FACT]** | Two engineers have distributed-systems experience |
| **[FACT]** | Six-week release target |
| **[ASSUMPTION]** | "Reliability complaints during peak usage" are real and not perceived (no metrics provided) |
| **[ASSUMPTION]** | The reliability issues are caused by infrastructure limitations, not application bugs |
| **[ASSUMPTION]** | The team has bandwidth to execute beyond their current workload |
| **[ASSUMPTION]** | "Peak usage" means concurrent request volume that exceeds single-process capacity |
| **[UNKNOWN]** | What specific reliability failures occur? (timeouts? errors? crashes?) — Owner: requester, Resolve by: Week 1 |
| **[UNKNOWN]** | What is current peak traffic volume (req/s)? — Owner: requester, Resolve by: Week 1 |
| **[UNKNOWN]** | What SLAs or error rate targets exist? — Owner: requester, Resolve by: Week 1 |
| **[UNKNOWN]** | What monitoring/observability exists today? — Owner: requester, Resolve by: Week 1 |
| **[UNKNOWN]** | Is the PostgreSQL database the bottleneck or the application process? — Owner: requester, Resolve by: Week 1 |

### 4. Decision Frame

**Question:** Which architectural approach best resolves reliability issues within 6 weeks with 2 engineers?

**Criteria used to evaluate:**
1. Implementation Risk (30%) — can it be delivered in 6 weeks?
2. Reliability Improvement (25%) — does it address peak-usage complaints?
3. Team Capability Match (20%) — does it leverage the team's distributed-systems skills?
4. Operational Complexity (15%) — what's the ongoing maintenance burden?
5. Future Flexibility (10%) — does it preserve scaling options?

**Constraints narrowing the option space:**
- 6-week hard deadline
- 2 engineers available
- Must improve reliability (not just refactor for cleanliness)

### 5. Options Evaluated

**Option A: Keep Monolith + Harden**
Add caching (Redis), connection pooling, rate limiting, health checks, and basic horizontal scaling (PM2/cluster mode) to the existing monolith.

**Option B: Event-Driven Microservices**
Split into 4 services (Articles, Auth, Profiles, Tags) with an event broker (Kafka/RabbitMQ), separate databases, and async communication.

**Option C: Modular Monolith (Hybrid)**
Refactor internal boundaries into well-defined modules with explicit interfaces. Deploy as single unit. Add caching and health checks. Prepare extraction points for future service splitting.

#### Decision Matrix

| Criterion | Weight | Option A (Harden) | Wtd | Option B (Microservices) | Wtd | Option C (Modular) | Wtd |
|---|---|---|---|---|---|---|---|
| Implementation Risk | 30% | 5 (low risk) | 1.50 | 1 (extreme risk) | 0.30 | 4 (moderate) | 1.20 |
| Reliability Improvement | 25% | 4 (caching+pooling) | 1.00 | 4 (if done right) | 1.00 | 3 (structural+cache) | 0.75 |
| Team Capability Match | 20% | 2 (underutilizes) | 0.40 | 5 (full match) | 1.00 | 4 (meaningful work) | 0.80 |
| Operational Complexity | 15% | 5 (simple ops) | 0.75 | 1 (massive burden) | 0.15 | 4 (still single deploy) | 0.60 |
| Future Flexibility | 10% | 2 (still monolithic) | 0.20 | 5 (maximum flex) | 0.50 | 4 (extraction-ready) | 0.40 |
| **Total** | 100% | | **3.85** | | **2.95** | | **3.75** |

**Sensitivity check:** If Team Capability Match weight increases to 30% (and Implementation Risk drops to 20%), Option C wins at 3.85 vs Option A at 3.55. Decision is moderately sensitive to team utilization weighting. If Reliability Improvement had been weighted at 35% (and Future Flexibility at 0%), Option A still wins at 4.05.

### 6. Recommendation and Why Not the Alternatives

**Recommendation: Option A — Keep Monolith + Harden**

**Decision statement:** We will keep the monolithic architecture and add caching, connection pooling, rate limiting, and health checks to resolve reliability complaints within the 6-week window.

**Why it wins:**
- Lowest implementation risk (3 of 5 hardening tasks are configuration, not architecture)
- Directly addresses the stated problem (reliability under load) without introducing new failure modes
- Simplest operational model (no distributed tracing, no service mesh, no event schema management)
- Can be validated incrementally — each improvement (cache, pooling, rate limits) is independently testable

**Why NOT Option B (Microservices):**
- 2,371 lines of code across 4 tightly-coupled domains is far too small to justify microservices overhead
- 6 weeks is insufficient to design service boundaries, implement event schemas, set up inter-service auth, build distributed tracing, and handle data consistency
- 2 engineers cannot operate a distributed system while also building it — operational burden would consume the team
- Reference 06 "Do I need event-driven architecture?" quick guide: the codebase fails the operational capability check

**Why NOT Option C (Modular Monolith) as primary:**
- It scores close (3.75 vs 3.85) but the refactoring work doesn't directly fix reliability — it prepares for future splitting
- The 6-week window is better spent on hardening (which directly fixes complaints) than on internal restructuring
- However, Option C is the recommended Phase 2 follow-on

### 7. Execution Plan

| Phase | Week | Work | Owner |
|---|---|---|---|
| **Phase 0: Instrument** | Week 1 | Add APM/monitoring, establish baseline metrics (p99, error rate, throughput) | Engineer A |
| **Phase 1: Quick wins** | Week 1-2 | Add Redis caching for article list/feed queries, connection pooling for Prisma | Engineer B |
| **Phase 2: Resilience** | Week 3-4 | Add rate limiting, health/readiness endpoints, graceful shutdown, PM2 cluster mode | Engineer A + B |
| **Phase 3: Validate** | Week 5 | Load test against baseline, verify reliability improvements under simulated peak | Engineer A + B |
| **Phase 4: Ship** | Week 6 | Staged rollout, monitoring, documentation | Engineer A + B |

**Dependencies:**
- Phase 0 → Phase 3 (need baseline metrics to validate improvement)
- Phase 1 → Phase 2 (caching reduces load before adding rate limits)

### 8. Risks, Checkpoints, Pivot Triggers, and Verification

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Reliability issues are DB-bound, not app-bound | Medium | High | Phase 0 instrumentation will reveal; pivot to read replicas if true |
| Redis adds operational complexity | Low | Medium | Use managed Redis (ElastiCache/Upstash); keep cache-aside pattern simple |
| 6-week timeline slips | Medium | Medium | Phase 1 alone may be sufficient; each phase is independently valuable |
| Caching introduces stale data bugs | Low | Medium | Short TTLs (60s), cache invalidation on writes |

**Checkpoints:**
- End of Week 1: Monitoring in place, baseline established. If baseline shows DB is bottleneck (not app), pivot to database optimization.
- End of Week 2: Caching operational. Measure improvement. If < 20% improvement in p99, investigate query patterns before proceeding.
- End of Week 4: All resilience features in place. If peak simulation still fails, escalate and consider modular monolith (Phase 2) timeline.

**Pivot triggers:**
- If instrumentation reveals the bottleneck is PostgreSQL (slow queries, connection exhaustion) → pivot to database optimization (read replicas, query optimization, connection pool tuning)
- If after Phase 2, load tests show < 30% improvement → re-evaluate Option C (modular monolith) as next quarter initiative

**Verification:**
- Load test: simulate 2× current peak traffic; p99 < 500ms and error rate < 0.1%
- Chaos test: kill one process in cluster mode; verify automatic restart and zero downtime
- Canary: route 10% of traffic to hardened version for 48 hours before full rollout

### 9. Immediate Next Actions and Open Questions

**Immediate next actions (this week):**
1. Add APM tooling (e.g., Datadog, New Relic, or open-source: Prometheus + Grafana) to establish current performance baseline
2. Capture specific reliability complaints from users/support — what exactly fails?
3. Review PostgreSQL connection limits and query performance under current peak

**Open questions to resolve before Phase 1:**
- What is the current peak request volume? (determines caching strategy)
- Are the reliability complaints about latency, errors, or downtime?
- Is there a staging environment for load testing?
- What managed Redis option is available in the current infrastructure?

**Phase 2 recommendation (post 6-week window):**
After stabilizing, invest one quarter in Option C (modular monolith) to create clean domain boundaries and prepare extraction points for future service splitting if traffic growth justifies it.

---

## Part 2: Complete Friction Point Registry

### F-01 — Prerequisite job not handled (P1, O3)
Task requires diagnosing reliability issues BEFORE comparing options. The 6 job categories are presented as mutually exclusive ("pick ONE dominant job") but the skill gives no guidance when one job is a prerequisite for another. I had to use implicit knowledge to decide "compare options" is primary and diagnosis is subordinate.
**Fix:** Add guidance: "If the dominant job depends on answering a prerequisite question (e.g., you must diagnose before you can compare), note the prerequisite but classify by the final deliverable the requester needs."

### F-02 — No output destination for classification (P2, M2)
Step says "State it explicitly: This is primarily a ___ decision/problem" but does not say WHERE. In the final output? In working notes? As a heading? The output contract (section later) references "Planning Job + Chosen Method(s)" as item 2 but Step 1 does not cross-reference it.
**Fix:** Add "State it in your working notes; it will appear in the Planning Job section of the output contract."

### F-03 — When to load reference file unclear (P1, S3)
The "Reference router" section is placed BEFORE the workflow steps but is not referenced FROM Step 1. Should I load references/03 now (since I classified as "compare options")? Or wait until Step 3 ("Choose the smallest useful method")? Information is scattered across non-sequenced sections.
**Fix:** Add to Step 1: "After classifying, consult the Reference Router table above and load the matching reference file. You will use it in subsequent steps."

### F-04 — Single classification forces false choice (P1, O3)
The task is simultaneously a comparison (monolith vs microservices) AND a diagnostic (what is causing reliability issues). The skill says "Do not try to run every planning mode at once" but does not handle cases where diagnosis is a prerequisite for comparison. I chose "compare options" as dominant using my own judgment.
**Fix:** Add: "If the task spans two jobs, pick the one that produces the requester's final deliverable. Note any prerequisite jobs that must inform it."

### F-05 — Mission template misfit for decisions (P2, O3)
Mission sentence template "We need to ___ so that ___ within ___ constraints" assumes an action, not a decision. For compare-options jobs, you need "We need to DECIDE whether..." which is an awkward fit.
**Fix:** Add decision-variant template: "We need to decide [X vs Y] so that ___ within ___ constraints. The deliverable is a recommendation with trade-offs."

### F-06 — Whose success criteria unclear (P1, M5)
Step says capture "success criteria and failure signals" but does not say whose or how to handle when user hasn't provided quantified criteria. The task says "reliability complaints" but no SLA, no error rate, no p99 targets. The skill does not say whether to infer, ask, or flag as unknown.
**Fix:** Add "If the requester has not stated quantifiable success criteria, propose 2-3 measurable candidates (e.g. p99 latency, error rate, uptime %) and flag them as PROPOSED — to be confirmed."

### F-07 — Fact vs assumption boundary undefined (P2, M5)
The skill says "facts vs. assumptions" but does not define the boundary. Is a codebase observation (no caching layer) a fact? Is a user statement ("two engineers") a fact or unverified claim? No taxonomy provided.
**Fix:** Add: "Facts = directly observed or verified data. User statements = treat as facts unless contradicted by evidence. Inferences from code/data = label as observations."

### F-08 — 5W2H undefined and never introduced (P0, S4)
Step 2 says "3+ core 5W2H questions are unanswered" — this is the first and only mention of 5W2H. It is never defined in the skill file or referenced in any reference file. The skill assumes the reader knows Who/What/Where/When/Why/How/How-much. An orphaned reference to an unexplained framework.
**Fix:** Either define 5W2H inline ("5W2H: Who, What, Where, When, Why, How, How much — the core framing questions") or add it to references/01-intake-and-framing.md and cross-reference.

### F-09 — Owner concept breaks in AI-agent context (P1, O3)
The skill says "critical unknowns have no owner or resolve-by date." In an AI-agent context executing the skill, there is no team of people to assign ownership to. The skill was written for human-to-human planning. No guidance for AI execution.
**Fix:** Add: "In AI-assisted planning, assign unknowns to the requester with a suggested resolve-by date. If the requester is unavailable, flag the unknown and proceed with bounded assumptions."

### F-10 — Decision-maker identification heuristic missing (P2, M5)
Step 2 blocker: "the decision-maker is unknown." The user said "I need to decide" so they are the decision-maker, but the skill does not provide a heuristic for when the asker ≠ the decision-maker. In practice PM asks architect who advises CTO.
**Fix:** Add: "Unless stated otherwise, treat the requester as the decision-maker. If the request implies another approver (e.g. CTO, board), note the approval chain."

### F-11 — Scope definition ambiguous for decision jobs (P1, M6)
Step says "scope: in / out / unknown" but does not define what scope means for a compare-options job. Is it the scope of the decision? The scope of possible implementations? The scope of the analysis?
**Fix:** Add per-job-type scope guidance: "For compare-options: scope = which options are on the table, which constraints are fixed, and what aspects of each option will be evaluated."

### F-12 — Two options vs "several" ambiguity (P1, M1)
Step 3 table says "Several measurable options → Decision matrix." Task has TWO options (monolith, microservices). Is 2 "several"? Reference 03 says "minimum 3 including do nothing." Step 3 does not say to generate additional options — that is only in the reference file.
**Fix:** Add to Step 3: "If you have fewer than 3 options, generate a minimal/status-quo option and at least one hybrid before proceeding with a decision matrix."

### F-13 — Reference use-case bundles contradict step minimalism (P1, S2)
Step 3 says "one primary method, add one companion only if it closes a clear gap." Reference 03 use-case bundles say "Irreversible infrastructure choice → Type 1 process + Full decision matrix + ADR + Sensitivity check" (4 things). These contradict.
**Fix:** Add: "Reference file use-case bundles are suggestions for thoroughness, not requirements. Follow the step rule: one primary, one companion max, unless the reference explicitly marks methods as REQUIRED for the decision type."

### F-14 — Method-rule timing is wrong (P2, S3)
Step 3 says "if the first method already makes the choice clear, stop." But this is the METHOD SELECTION step — I have not APPLIED the method yet. This rule belongs in Step 5.
**Fix:** Move the method rule to Step 5 or reword: "After applying the method in Step 5, if the choice is clear, do not add another method."

### F-15 — "Clear gap" undefined for companion method (P2, M6)
Step says "Add one companion only if it closes a clear gap." No threshold given.
**Fix:** Add: "A clear gap exists when the primary method cannot answer a critical question needed for the decision — e.g., the matrix scores are tied and you need a tiebreaker, or long-term consequences are not captured by the criteria."

### F-16 — User claims without artifacts (P1, O3)
Step 4 lists "local context (artifacts, prior attempts, observed behavior)" as first evidence source. The task says "reliability complaints during peak usage" but the codebase has no logs, metrics, or monitoring. The skill does not say how to handle user-stated problems that have no supporting artifacts.
**Fix:** Add: "If the requester reports a problem but no supporting artifacts exist (logs, metrics, error reports), flag this as an UNVERIFIED CLAIM and note it in Assumptions. Recommend instrumenting as a prerequisite."

### F-17 — Direct signals inaccessible to code review (P1, M5)
Step 4 says "direct signals (current outcomes, constraints, failure signatures)." An AI agent reading source code cannot observe runtime behavior, error rates, or load characteristics. The skill assumes access to runtime data.
**Fix:** Add: "If you only have source code (no runtime data), focus on architectural risk indicators: missing caching, no connection pooling, synchronous coupling, absence of health checks, single-process design."

### F-18 — "Understand system behavior" — no method given (P1, M6)
Step 4 says "understand current system behavior before recommending structural change" but provides no method for doing so.
**Fix:** Add: "To understand current behavior: 1) Map the request flow from entry to database, 2) Identify coupling points between domains, 3) Check for scaling bottlenecks (single process, shared state, synchronous calls), 4) Note missing infrastructure (caching, queuing, health checks)."

### F-19 — Type 1/2 classification never triggered in workflow (P1, S3)
Step 4 depth rules reference "Type 1 / Type 2" decisions. This classification exists in reference 03 but is never explicitly scheduled in the workflow Steps 1-6.
**Fix:** Add to Step 1 or Step 3: "Classify the decision as Type 1 (irreversible) or Type 2 (reversible) using the criteria in references/03. This classification determines analysis depth in Step 4."

### F-20 — Option generation never scheduled (P0, S1)
Step 4 depth rules say "require 2-4 viable options" for Type 1 decisions. Reference 03 says "minimum 3 including do nothing." But the 6-step workflow NEVER explicitly says to generate options. Step 3 is about METHOD selection. Step 4 is about EVIDENCE. Option generation falls between the cracks.
**Fix:** Add explicit Step 3.5 or add to Step 4: "Before evaluating, ensure you have 2-4 viable options. If starting with fewer, generate additional options including a minimal/status-quo option and at least one hybrid."

### F-21 — No analytical process in Step 5 (P1, M4)
Step 5 says "Apply the output shape that matches the job" for Decision: "include the selected option, why it wins, and why the others do not." But does not describe HOW to apply the decision matrix. Must go back to reference 03 for the template and scoring approach.
**Fix:** Add to Step 5: "For Decision jobs, apply the method chosen in Step 3. For a decision matrix: score each option 1-5 against each criterion, multiply by weight, sum for totals. The highest score wins unless a sensitivity check changes the outcome."

### F-22 — Minimal option vs fallback conflated (P1, M6)
Step 5 says "Always include a minimal or fallback option" AFTER the decision instruction. Two different concepts conflated: (1) a minimal/status-quo CANDIDATE vs (2) a FALLBACK if the chosen option fails.
**Fix:** Separate: "Include a minimal/status-quo option as a candidate in your comparison. After deciding, also define a fallback plan: the option you switch to if the chosen option fails, and the trigger for switching."

### F-23 — Step 5 execution planning overlaps Step 6 (P2, S2)
Step 5 execution planning says "define phases, dependencies, owners, checkpoints, verification, and pivot triggers." Step 6 says nearly identical things. Unclear what belongs where.
**Fix:** Clarify: "Step 5 produces the decision/recommendation with high-level phasing. Step 6 packages it with full execution detail including owners, verification, and review cadence."

### F-24 — Most relevant reference buried in secondary file (P1, S3)
Reference 06 has a "Do I need event-driven architecture?" quick guide DIRECTLY relevant to this task. But the reference router says to start with 03. The most useful content was in a file the skill didn't tell me to load first.
**Fix:** Add cross-references in reference router: "For architecture comparison decisions, also check references/06 section on event-driven architecture quick guide."

### F-25 — Scoring methodology not guided (P1, M4)
Reference 03 provides a decision matrix template with 1-5 scoring but gives no guidance on HOW to score. What differentiates a 2 from a 3? Is 1 highest risk or lowest?
**Fix:** Add to reference 03: "Score 1 = poor fit/high risk, 5 = excellent fit/low risk. If unsure, use: 1=unacceptable, 2=poor, 3=adequate, 4=good, 5=excellent. Document one sentence of rationale per score."

### F-26 — Two-layer structure vs 9-item output contract (P0, S2)
Step 6 says deliver "two layers" (decision brief + execution detail). Output Contract says respond in 9 sections. Both claim to be the default. These are contradictory formats.
**Fix:** Reconcile: "The Output Contract defines the sections. The two-layer rule defines the packaging: Layer 1 (items 1-6 = Decision Brief) and Layer 2 (items 7-9 = Execution Detail). Deliver both unless the user requests only one."

### F-27 — Audience detection unguided (P2, M5)
Step 6 says "Lead with recommendation for decision-makers" or "sequence for executors." Does not say how to determine which audience. The task user is both.
**Fix:** Add: "If the requester is both decision-maker and executor, lead with the recommendation (decision-maker framing) and include execution detail immediately after."

### F-28 — "Decision frame" undefined (P2, M6)
Output contract item 4 says "Root Cause, Decision Frame, or Priority Logic." For compare-options, this is "Decision Frame" — but the term is never defined anywhere in the skill.
**Fix:** Add: "Decision Frame = the question being decided, the criteria used to evaluate, the reversibility classification, and any constraints that narrow the option space."

### F-29 — Cannot assign owners as AI agent (P1, O3)
Step 6 execution detail says include "owners." As an AI agent, I cannot assign people to tasks. Team described only as "two engineers."
**Fix:** Add: "If team members are not identified by name, assign to roles (e.g., Tech Lead, Engineer A, Engineer B) and note that the requester should assign specific people."

### F-30 — Quality gate thresholds undefined (P2, M1)
Quality gate checks are binary yes/no but items like "Are facts, assumptions, and unknowns CLEARLY separated?" have no threshold for what constitutes "clear."
**Fix:** Add pass criteria: "Facts, assumptions, and unknowns are separated when each item is explicitly labeled as [FACT], [ASSUMPTION], or [UNKNOWN] with a confidence level or resolve-by date for unknowns."

### F-31 — Failed gate recovery undefined (P1, M4)
Quality gate says "If any answer is no, revise before finalizing." Does not say which step to return to or what "revise" means operationally.
**Fix:** Add per-item recovery: "If item N fails, return to Step [X] to address it. For missing verification/checkpoints, add them to the execution detail."

### F-32 — Checkpoints not scheduled for Decision jobs (P1, O3)
Quality gate item 6 checks for "verification, checkpoints, and pivot triggers" but the workflow only creates these in Step 5 for execution planning jobs. For Decision jobs, their creation is never explicitly scheduled.
**Fix:** Add to Step 5 Decision output: "For all decision types, include: (1) how to verify the decision worked, (2) when to revisit, (3) what signals would trigger switching to the fallback option."

### F-33 — Done conditions vs quality gate overlap (P2, S2)
The skill has both "Done conditions" and "Final quality gate" sections. They overlap substantially but are presented as separate. Unclear if both must be checked.
**Fix:** Merge or clarify: "The quality gate IS the done condition check. All 7 gate items must pass before the plan is finalized."

---

## Part 3: Metrics Table

| Metric | Count |
|---|---|
| Total steps attempted | 7 |
| Clean passes | 0 |
| **P0 (blocks progress)** | **3** |
| **P1 (causes confusion)** | **19** |
| **P2 (minor annoyance)** | **11** |
| **Total friction points** | **33** |
| Derailments (could not determine next action) | 15 |
| Implicit knowledge used (executed but only because I "knew") | 18 |

### Root Cause Distribution

| Code | Meaning | Count |
|---|---|---|
| O3 | Edge case unhandled | 7 |
| M6 | Vague verb | 5 |
| M5 | Assumed knowledge | 5 |
| S3 | Scattered information | 4 |
| S2 | Contradictory paths | 4 |
| M4 | Missing execution method | 3 |
| M1 | Ambiguous threshold | 2 |
| S4 | Orphaned reference | 1 |
| S1 | Missing prerequisite | 1 |
| M2 | Unstated location | 1 |

---

## Part 4: What Worked Well

1. **The 6-step sequence is sound.** The flow from classify → frame → method → evidence → decide → package is a correct cognitive sequence. The steps are in the right ORDER even when individual step content is incomplete.

2. **The reference router is a good idea.** Directing users to one file at a time prevents information overload. The "Add only if" column is a genuinely useful constraint.

3. **Step 4's evidence priority order is excellent.** "Local context → direct signals → external research only when it can change the decision" is a powerful heuristic that prevents research rabbit holes.

4. **The anti-derail guardrails table is valuable.** "Start with one reference file and one method" and "Switch to a simpler method when a framework adds no clarity" are practical and actionable.

5. **The recovery paths section handles real failure modes.** The "if options remain tied, use reversibility as tiebreaker" is exactly the right guidance.

6. **Reference 03 is comprehensive and well-structured.** The decision matrix template, ADR template, pros/cons framework, and reversibility classification are all production-quality content.

7. **Reference 06's "Do I need event-driven architecture?" quick guide is gold.** Direct, specific, and immediately actionable — though it's buried in a secondary reference.

8. **The output contract provides clear structure.** The 9-item list gives a concrete format to follow, even if it conflicts with Step 6's two-layer packaging.

---

## Part 5: Derailment Density Map

```
Step 1: Classify           ████░░░░░░  4 friction points (1 P1, 2 P1, 1 P2)
Step 2: Frame              ███████░░░  7 friction points (1 P0, 4 P1, 2 P2)  ← HIGHEST
Step 3: Choose method      ████░░░░░░  4 friction points (2 P1, 2 P2)
Step 4: Build evidence     █████░░░░░  5 friction points (1 P0, 3 P1, 1 P1)  ← 2nd highest
Step 5: Decide             █████░░░░░  5 friction points (4 P1, 1 P2)
Step 6: Package            ████░░░░░░  4 friction points (1 P0, 1 P1, 2 P2)
Step 7: Quality gate       ████░░░░░░  4 friction points (2 P1, 2 P2)

P0 hotspots: Step 2 (5W2H), Step 4 (option generation), Step 6 (output format)
```

### Phase Analysis

**Framing phase (Steps 1-2)** had the most friction (11 points, 33% of total). This is concerning because framing is where the skill provides the most value — if you frame wrong, everything downstream is wrong. The main issues:
- The classification system doesn't handle prerequisite jobs
- 5W2H is referenced but never defined
- Key concepts (scope, success criteria, fact/assumption boundary) lack operational definitions

**Evidence phase (Step 4)** had the second-highest density (5 points). The main gap: the workflow never tells you to generate options, classify reversibility, or how to understand system behavior — all of which are required by the step's own depth rules.

**Decision phase (Step 5)** was surprisingly smooth in overall flow — but only because the reference files did the heavy lifting. The step itself is thin on analytical process and relies on the practitioner already knowing how to execute a decision matrix.

**Packaging phase (Steps 6-7)** has a structural contradiction: two competing output formats (two-layer vs 9-item) that are never reconciled. The quality gate catches omissions but doesn't tell you how to fix them.

---

## Summary Assessment

The `plan-work` skill has a **correct high-level architecture** but suffers from **incomplete step-level instructions**. The 6-step workflow is the right sequence, and the reference files are excellent — but the steps themselves are too thin to execute without domain expertise.

**Top 5 fixes that would eliminate the most friction:**

1. **Define 5W2H** (F-08, P0) — add a one-line definition where it's first used
2. **Add option generation step** (F-20, P0) — insert explicit "generate 2-4 options" before evaluation
3. **Reconcile output formats** (F-26, P0) — map the two-layer model onto the 9-item contract
4. **Add reversibility classification to workflow** (F-19, P1) — make Type 1/2 explicit in Step 1 or 3
5. **Cross-reference steps to reference content** (F-03, F-21, F-24, all P1) — tell practitioners WHEN to consult references and what to look for

The skill's **strength** is its reference library and guardrails. Its **weakness** is the gap between what the steps say to do and the knowledge needed to do it. An experienced planning practitioner can fill these gaps unconsciously; a literal executor (AI or junior) cannot.
