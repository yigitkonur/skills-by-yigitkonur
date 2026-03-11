# Execution Risk and Learning Loops

## Read this if
- Delivery conditions are changing.
- The plan includes high uncertainty.
- You need controlled adaptation instead of rigid execution.
- You want structured templates for risk management, retrospectives, and incident response.

## Planning vision for this stage
Think like a navigator: keep direction stable, adjust route continuously.

## Execution control loop

1. Define early warning indicators.
2. Set checkpoint cadence.
3. Predefine pivot triggers.
4. Capture lessons and update plan.

## Method steering

### OODA loop
Best for rapid adaptation.
- Thinking posture: "Observe reality fast, re-orient before each decision."

### Confidence determines speed vs. quality
Best for pacing work under uncertainty.
- Thinking posture: "Match delivery speed to confidence and risk."

### Second-order thinking
Best for avoiding harmful chain reactions during execution.
- Thinking posture: "What new risks does this action introduce?"

### Balancing feedback loop
Best for identifying natural resistance in change execution.
- Thinking posture: "What system force neutralizes this intervention?"

### Reinforcing feedback loop
Best for scaling wins and controlling runaway failures.
- Thinking posture: "What is amplifying and how do we shape it?"

### Inversion (pre-mortem layer)
Best for contingency readiness.
- Thinking posture: "What would make this rollout fail, and what safeguards prevent it?"

## Use-case bundles

- High-volatility delivery -> OODA + confidence-speed-quality
- Rollout with cascading dependencies -> second-order + feedback loops
- Critical launch -> inversion pre-mortem + contingency planning

---

## Risk register template

Track every identified risk in a single source of truth. Review weekly; update scores as conditions change.

| Risk ID | Description | Category | Likelihood (1-5) | Impact (1-5) | Risk Score | Early Indicators | Mitigation | Contingency | Owner | Status |
|---------|-------------|----------|:-----------------:|:------------:|:----------:|------------------|------------|-------------|-------|--------|
| R-001 | Key person dependency — single engineer owns critical auth module | People | 4 | 5 | 20 | No code reviews from others on auth PRs; knowledge silo growing | Pair programming rotation; document architecture decisions; cross-train second engineer | Engage external contractor with auth expertise; freeze auth changes until coverage restored | Tech Lead | Active |
| R-002 | Third-party payment API instability — provider has had 3 outages in 60 days | Technical | 3 | 5 | 15 | Increased error rates in payment logs; provider status page warnings; latency spikes > 2s | Implement circuit breaker pattern; add retry with exponential backoff; cache idempotency keys | Switch to backup payment provider (pre-integrated); queue failed transactions for manual retry | Backend Lead | Active |
| R-003 | Scope creep — stakeholder requests expanding beyond agreed MVP | Process | 4 | 4 | 16 | Backlog growing > 15% per sprint; sprint goals missed due to added items; unclear acceptance criteria | Strict change request process; weekly scope review with product owner; freeze scope 2 days before sprint | Defer all new requests to v2 backlog; re-baseline timeline with stakeholders; escalate to sponsor | Product Owner | Watching |
| R-004 | Data migration failure — legacy DB schema incompatible with new model | Technical | 3 | 4 | 12 | Test migration errors > 5%; unmapped fields discovered; migration script runtime exceeds 4-hour window | Run migration dry-runs weekly; build field mapping validation suite; incremental migration strategy | Roll back to legacy system; run dual-write mode; extend migration window to off-peak weekend | Data Engineer | Active |
| R-005 | Performance regression — response times degrade after new feature deployment | Quality | 2 | 4 | 8 | p95 latency trending upward in staging; load test failures; memory usage climbing across deploys | Performance budget in CI pipeline; automated load tests on staging; profile critical paths weekly | Feature-flag rollback; scale horizontally while investigating; revert to last known good deployment | SRE Lead | Watching |

**Scoring guide:** Risk Score = Likelihood × Impact. Scores 1-6 = Low (monitor), 7-14 = Medium (mitigate), 15-25 = Critical (act immediately).

**Review cadence:** Re-score all active risks at each checkpoint. Retire risks that no longer apply. Promote "Watching" to "Active" when early indicators fire.

---

## Pre-mortem template

A pre-mortem assumes the project has already failed and works backward to find causes. Run this at project kickoff and before each major phase.

### How to run a pre-mortem

1. **Set the scene** — "It is [deadline date]. The project has failed. What went wrong?"
2. **Individual brainstorm** (5-10 min) — Each team member writes exactly 3 failure scenarios independently. No discussion yet.
3. **Share and group** — Read all scenarios aloud. Cluster duplicates and related items.
4. **Score** — Each participant votes: Likelihood (1-5) × Impact (1-5) for each cluster.
5. **Rank** — Sort by combined score descending. Take the top 5.
6. **Create prevention actions** — For each top-5 failure, define a concrete prevention action, an owner, and a detection signal.
7. **Feed into risk register** — Add the top failures as entries in the risk register above.

### Worked example — E-commerce checkout rebuild

**Scene:** "It is March 15. The checkout rebuild launched but we had to roll back within 48 hours."

| Rank | Failure Scenario | Likelihood | Impact | Score | Prevention Action | Owner |
|:----:|-----------------|:----------:|:------:|:-----:|-------------------|-------|
| 1 | Payment edge cases not tested — gift cards, split payments, and multi-currency failed silently | 4 | 5 | 20 | Build payment scenario matrix; run each combination in staging with real provider sandbox | QA Lead |
| 2 | Legacy order service contract changed without notice — new checkout sends incompatible payloads | 3 | 5 | 15 | Add contract tests in CI; set up breaking-change alerts on legacy service repo | Backend Lead |
| 3 | Mobile performance killed conversion — new checkout loads 4s on 3G connections | 3 | 4 | 12 | Performance budget: < 2s on simulated 3G; block merge if budget exceeded | Frontend Lead |
| 4 | Team velocity dropped 40% in final sprint due to holiday absences and context switching | 4 | 3 | 12 | Freeze scope 2 sprints before launch; no new feature requests after code freeze date | PM |
| 5 | Rollback plan untested — when we tried to revert, database migrations had no down path | 2 | 5 | 10 | Require reversible migrations; test full rollback in staging before each release | DevOps Lead |

---

## Retrospective formats

Choose the format based on team maturity and the type of reflection needed.

### Start / Stop / Continue

**Best for:** Teams new to retros, or when you need quick actionable changes.

| Start (we should begin doing) | Stop (we should quit doing) | Continue (keep doing, it works) |
|-------------------------------|-----------------------------|---------------------------------|
| Daily 10-min design syncs | Skipping code review for "small" PRs | Weekly demo to stakeholders |
| Writing ADRs for architecture decisions | Late-night deploys on Fridays | Pair programming on complex modules |

### 4Ls: Liked, Learned, Lacked, Longed for

**Best for:** Mid-project check-ins where you want emotional and practical feedback.

| Liked | Learned | Lacked | Longed for |
|-------|---------|--------|------------|
| Team collaboration on the migration sprint | Circuit breakers prevent cascading failures | Clear ownership of shared services | Dedicated time for tech debt reduction |
| Stakeholder transparency during delays | Feature flags reduce deploy risk | Staging environment parity with prod | Better onboarding docs for new joiners |

### Sailboat

**Best for:** Visual thinkers; teams that want a metaphor to structure discussion.

| Wind (what helps us) | Anchor (what holds us back) | Rocks (risks ahead) | Island (our goal) |
|-----------------------|-----------------------------|----------------------|-------------------|
| Strong CI/CD pipeline | Manual QA bottleneck | Third-party API deprecation in Q3 | Ship v2 with 99.9% uptime |
| Experienced team lead | Unclear priority between features | Key engineer leaving in 6 weeks | Zero-downtime migration complete |

### Mad / Sad / Glad

**Best for:** Teams experiencing friction or morale issues; surfaces emotional undercurrents.

| Mad (frustrated by) | Sad (disappointed about) | Glad (happy about) |
|----------------------|--------------------------|---------------------|
| Changing requirements mid-sprint | Missed the launch date by 2 weeks | Team pulled together during the outage |
| Blocked by unresponsive external team | Lost a team member to another project | Customer feedback on beta was positive |

### When to use which format

| Situation | Recommended Format |
|-----------|--------------------|
| First retro with a new team | Start / Stop / Continue |
| Mid-project health check | 4Ls |
| Team feels stuck or directionless | Sailboat |
| After a stressful incident or missed deadline | Mad / Sad / Glad |
| Mature team wanting depth | 4Ls or Sailboat |

---

## Checkpoint design template

Define checkpoints at project start. Each checkpoint is a decision gate — not just a status update.

| Checkpoint | Date | Success Criteria | Decision Options | Owner |
|------------|------|------------------|------------------|-------|
| CP-1: Foundation complete | Week 4 | Core data model validated; CI/CD pipeline green; dev environment stable for all engineers | **Go:** proceed to feature build · **Adjust:** extend foundation by 1 week · **Stop:** revisit architecture if > 3 critical blockers | Tech Lead |
| CP-2: Feature-complete | Week 8 | All MVP user stories meet acceptance criteria; integration tests passing; no P0 bugs open | **Go:** enter hardening phase · **Adjust:** cut lowest-priority feature to meet timeline · **Stop:** re-scope MVP with stakeholders | Product Owner |
| CP-3: Launch-ready | Week 11 | Load tests pass at 2× expected traffic; rollback tested in staging; runbook reviewed by on-call team; stakeholder sign-off received | **Go:** deploy to production · **Adjust:** delay 1 week for specific gap · **Stop:** defer launch if P0 regression found | Engineering Manager |

**Checkpoint review protocol:**
1. Present evidence against each success criterion (dashboards, test results, demo).
2. Each reviewer independently selects a decision option.
3. Discuss disagreements. Escalate if no consensus within 30 minutes.
4. Document decision and rationale. Update risk register and timeline.

---

## Pivot triggers catalog

Define these thresholds at project start. When a trigger fires, it forces a structured reassessment — not panic.

### Velocity triggers
- **Sprint velocity drops below 60% of plan for 2 consecutive sprints** — Reassess scope, team capacity, or blocking issues.
- **Cycle time for standard tasks increases > 50%** — Investigate process bottlenecks, context switching, or unclear requirements.
- **Unplanned work exceeds 30% of sprint capacity** — Tighten intake process; revisit sprint planning accuracy.

### Quality triggers
- **Error rate exceeds threshold** — Production error rate > 1% of requests or > 2× baseline for 48 hours.
- **Bug escape rate rising** — More than 3 P1/P2 bugs found in production per release for 2 consecutive releases.
- **Test coverage drops below floor** — Coverage falls below agreed minimum (e.g., 70%) on changed files.

### Dependency triggers
- **External blocker unresolved for > 5 business days** — Escalate to skip-level; activate contingency plan; consider workaround or alternative provider.
- **Upstream API breaking change announced** — Assess impact within 24 hours; re-estimate affected work items.
- **Vendor SLA breach** — Provider misses SLA twice in 30 days; begin evaluating alternatives.

### Scope triggers
- **Requirements changed > 30% since last checkpoint** — Mandatory re-planning session; re-baseline estimates and timeline.
- **New regulatory or compliance requirement introduced** — Immediate impact assessment; may require architecture review.
- **Stakeholder priority inversion** — Top-3 priorities reordered; realign sprint backlog within 48 hours.

### Market and external triggers
- **Competitive landscape shift** — Competitor launches overlapping feature; reassess differentiation and timeline urgency.
- **Customer feedback invalidates assumptions** — Core hypothesis disproven by user research or beta feedback; pivot feature direction.
- **Budget or resource change** — Funding reduced or team size changes > 20%; re-scope deliverables to match capacity.

**Response protocol when a trigger fires:**
1. Verify the signal (not a data anomaly).
2. Convene decision-makers within 24 hours.
3. Choose: adjust plan, re-scope, escalate, or accept risk.
4. Document decision and update risk register.

---

## Progress tracking methods

### Burndown and burnup charts

**Burndown** shows remaining work over time. Line should trend toward zero by sprint end. Use when the scope is fixed and you want to track completion pace.

**Burnup** shows completed work and total scope on the same chart. Use when scope changes frequently — the widening or narrowing gap between the two lines reveals scope creep visually.

| Chart Type | Best For | Watch For |
|------------|----------|-----------|
| Burndown | Fixed-scope sprints; daily standups | Flat lines (blocked work); sudden drops (batch closures, not real progress) |
| Burnup | Projects with changing scope; stakeholder reporting | Scope line rising faster than completion line (will miss deadline) |

### Milestone tracking

Track delivery against predefined milestones rather than individual tasks. Best for executive reporting and cross-team coordination.

| Milestone | Target Date | Actual Date | Status | Notes |
|-----------|-------------|-------------|--------|-------|
| Architecture approved | Week 2 | Week 2 | ✅ Done | — |
| API contracts finalized | Week 4 | Week 5 | ⚠️ Late | Delayed by auth provider decision |
| Integration testing complete | Week 8 | — | 🔵 In Progress | On track |
| Production deployment | Week 10 | — | ⬚ Not Started | — |

### Confidence-based reporting

Replace vague status updates with calibrated confidence assessments.

| Status | Criteria | Action Required |
|--------|----------|-----------------|
| 🟢 **On Track** | Milestones on schedule; no active P0 risks; velocity within 80-120% of plan | Continue; standard reporting |
| 🟡 **At Risk** | One milestone slipping; active P0 risk with mitigation in progress; velocity 60-80% of plan | Escalate to project sponsor; activate mitigation plans; consider scope trade-offs |
| 🔴 **Off Track** | Multiple milestones missed; unmitigated P0 risk; velocity below 60% of plan for 2+ sprints | Mandatory re-planning session; sponsor decision required on scope/timeline/resources |

Report confidence weekly. Pair the status color with one sentence explaining *why* and one sentence stating *what changes if anything*.

---

## Incident response planning

### Severity levels

| Severity | Definition | Response Time | Examples |
|:--------:|-----------|:-------------:|---------|
| **SEV-1** | Complete service outage or data loss affecting all users | < 15 min to acknowledge; all-hands until resolved | Production database down; payment processing halted; security breach confirmed |
| **SEV-2** | Major feature broken or significant performance degradation | < 30 min to acknowledge; dedicated responders | Checkout flow failing for 30% of users; API latency > 10× baseline; data sync halted |
| **SEV-3** | Minor feature broken; workaround available | < 2 hours to acknowledge; next business day fix | Export function fails for one file type; UI rendering issue on specific browser; non-critical job failing |
| **SEV-4** | Cosmetic issue or minor inconvenience | < 1 business day to acknowledge; scheduled fix | Typo in UI; minor styling inconsistency; log noise from deprecated endpoint |

### Escalation path

1. **Detect** — Monitoring alert fires or user report received.
2. **Triage** — On-call engineer assesses severity within response time window.
3. **Assemble** — SEV-1/2: page incident commander + relevant domain owners. SEV-3/4: assign to next sprint.
4. **Communicate** — Post to incident channel; update status page; notify affected stakeholders.
5. **Resolve** — Fix or mitigate. Document every action with timestamps.
6. **Review** — Blameless post-incident review within 48 hours for SEV-1/2.

### Communication templates

**Internal incident announcement:**
> 🔴 **[SEV-X] Incident: [short description]**
> **Impact:** [who is affected and how]
> **Status:** Investigating / Identified / Mitigating / Resolved
> **Incident Commander:** [name]
> **Next update:** [time]

**Stakeholder update (during incident):**
> **Update [N] — [timestamp]**
> **Current status:** [what we know now]
> **Actions taken:** [what we have done since last update]
> **Next steps:** [what we are doing next]
> **ETA to resolution:** [estimate or "under investigation"]

**Post-incident summary:**
> **Incident:** [title]
> **Duration:** [start time] – [end time] ([total duration])
> **Impact:** [users affected, revenue impact, SLA implications]
> **Root cause:** [concise technical explanation]
> **Resolution:** [what fixed it]
> **Action items:** [list with owners and due dates]

---

## Post-cycle review prompts

- What did we predict?
- What happened?
- Why was there a gap?
- What changes in next cycle?
- Which risks materialized that we did not anticipate?
- Which mitigation actions proved most effective?
- What should we add to the risk register for the next cycle?
