# Root Cause and Problem Solving

## Read this if
- The same issue keeps recurring.
- Teams disagree on causes.
- Symptoms are fixed repeatedly without durable improvement.
- You need a structured postmortem after a production incident.
- You want to move from "who broke it" to "what allowed it to break."

## Planning vision for this stage
Think in layers. Events are signals; structures create events. Your goal is never to assign blame — it is to find the mechanism that permitted failure and change that mechanism.

## Diagnosis sequence

1. Define symptom precisely (what, when, who is affected, severity).
2. Collect evidence by category (process, people, system, environment).
3. Build cause hypotheses.
4. Test hypotheses against counterevidence.
5. Select highest-confidence causes.
6. Propose fixes mapped to each confirmed cause.
7. Define verification signals that prove the fix works.

---

## Evidence collection checklist

Gather these **before** starting any analysis method. Incomplete evidence leads to wrong conclusions.

| Category | What to Collect | Where to Find It |
|---|---|---|
| **Logs** | Application logs, error traces, stack traces | Log aggregator (Datadog, Splunk, CloudWatch) |
| **Metrics** | CPU, memory, latency, error rate, throughput | Monitoring dashboards (Grafana, New Relic) |
| **Timeline** | Exact timestamps of first symptom, escalation, mitigation | Alerting system, on-call chat, status page |
| **Recent changes** | Deploys, config changes, infra changes, feature flags | CI/CD pipeline, deploy logs, change management |
| **Affected scope** | Which users, regions, services, endpoints | Traffic analytics, error grouping |
| **Dependencies** | Upstream/downstream service health during window | Service mesh dashboards, dependency maps |
| **Customer reports** | Support tickets, social media mentions | Support queue, Twitter/status page |
| **Previous incidents** | Similar past incidents and their resolutions | Postmortem archive, incident tracker |

### Evidence collection template

```
## Evidence Gathered
- **First alert fired:** [timestamp]
- **First customer report:** [timestamp]
- **Services affected:** [list]
- **Error signature:** [error message / code]
- **Recent deploys (last 48h):** [list with timestamps]
- **Config changes (last 48h):** [list with timestamps]
- **Relevant metrics anomalies:** [describe]
- **Blast radius:** [% users, regions, severity]
```

---

## Method steering

### 5 Whys Technique

Best for linear cause chains where one failure cascades into visible symptoms.
- Thinking posture: "Keep asking why until you reach a mechanism you can change."

**Rules:**
1. Stop at a **mechanism**, not a person. "Bob made a mistake" is never a root cause. "The system allowed the mistake to reach production" is.
2. Each "why" must be supported by evidence, not speculation.
3. Stop when you reach something you can **design away** (typically 3–7 levels deep).
4. If a "why" branches into multiple causes, follow each branch separately.
5. Validate: the root cause should explain all observed symptoms when you read the chain forward.

**Worked example — User login fails:**

| Level | Question | Answer | Evidence |
|---|---|---|---|
| Symptom | What happened? | Users cannot log in; login page returns HTTP 500 | Error rate spike on `/auth/login` at 14:32 UTC |
| Why 1 | Why does login fail? | Auth service returns 500 errors on token generation | Auth service logs show `ConnectionException` |
| Why 2 | Why does the auth service throw ConnectionException? | Redis connection pool is exhausted (0 available connections) | Redis client metrics: pool size 20, all in use, 340 waiting |
| Why 3 | Why is the connection pool exhausted? | Connections are leaking in the retry logic — acquired but never released on failure path | Code review: `finally` block missing in `RetryHandler.execute()` |
| Why 4 | Why does the retry logic leak connections? | Retry calls a non-idempotent session-create endpoint, each retry opens a new connection without closing the failed one | Retry config targets `POST /sessions` which creates server-side state |
| Why 5 | Why does retry target a non-idempotent endpoint without protection? | API design has no idempotency key; retry logic has no awareness of endpoint idempotency | API spec review: no `Idempotency-Key` header defined |
| **Root cause** | | **Missing idempotency key in API design + retry logic that doesn't distinguish idempotent from non-idempotent calls** | |

**Verification (read forward):** Missing idempotency key → retry logic fires unsafe retries → each retry leaks a Redis connection → pool exhausts → auth service can't generate tokens → users can't log in. ✓ Chain is coherent.

**5 Whys template:**

```
## 5 Whys Analysis
**Symptom:** [describe]
**Date/Time:** [when]

| Level | Question | Answer | Evidence |
|---|---|---|---|
| Symptom | What happened? | | |
| Why 1 | Why did [symptom] occur? | | |
| Why 2 | Why did [Why 1 answer] happen? | | |
| Why 3 | Why did [Why 2 answer] happen? | | |
| Why 4 | Why did [Why 3 answer] happen? | | |
| Why 5 | Why did [Why 4 answer] happen? | | |

**Root cause:** [mechanism, not a person]
**Forward-read validation:** [read from root cause to symptom — does it hold?]
```

### Ishikawa / Fishbone Diagram

Best for broad cause discovery when the failure has multiple contributing factors.
- Thinking posture: "Map all plausible causes before narrowing."

**Categories for software systems:**

```
                        Code              Infrastructure          Process
                         |                     |                    |
                         |                     |                    |
Symptom  ◄───────────────┼─────────────────────┼────────────────────┤
(effect)                 |                     |                    |
                         |                     |                    |
                        Data              External             People
```

**Fishbone template (markdown):**

```
## Fishbone Analysis: [Symptom]

### Code
- [ ] Recent code changes in affected path?
- [ ] Logic errors, race conditions, off-by-one?
- [ ] Missing error handling or validation?
- [ ] Dependency version change?

### Infrastructure
- [ ] Resource exhaustion (CPU, memory, disk, connections)?
- [ ] Network partition or latency spike?
- [ ] DNS, load balancer, or certificate issue?
- [ ] Cloud provider incident?

### Process
- [ ] Deployment procedure skipped a step?
- [ ] Missing or outdated runbook?
- [ ] Change deployed without review or staging test?
- [ ] Monitoring/alerting gap?

### People
- [ ] Knowledge gap (new team member, unfamiliar system)?
- [ ] Communication breakdown between teams?
- [ ] Alert fatigue leading to ignored warning?
- [ ] On-call handoff missed context?

### Data
- [ ] Corrupt or unexpected input data?
- [ ] Schema migration issue?
- [ ] Data volume spike beyond tested capacity?
- [ ] Stale cache or inconsistent state?

### External
- [ ] Third-party API degradation?
- [ ] Upstream dependency failure?
- [ ] Customer traffic pattern change?
- [ ] Regulatory or compliance change?
```

### Fault Tree Analysis

Best for complex incidents where multiple conditions must combine to cause failure (AND gates) or where any single failure is sufficient (OR gates).
- Thinking posture: "Model the Boolean logic of how failures compose."

**Gate types:**
- **OR gate:** Any single child event is sufficient to cause the parent. (Use for redundant failure paths.)
- **AND gate:** All child events must occur simultaneously to cause the parent. (Use for incidents requiring multiple coincidences.)

**Worked example — Production database outage:**

```
                    [Database Outage]
                          |
                       OR gate
                    ______|______
                   |             |
          [Primary DB down]  [Failover fails]
                |                    |
             OR gate              AND gate
           ____|____          ______|______
          |         |        |             |
    [Disk full] [OOM kill]  [Replica lag   [Health check
                             > 60s]        misconfigured]
```

**Reading the tree:** The database outage occurs if the primary DB goes down (from disk full OR OOM kill) OR if failover fails (which requires BOTH replica lag > 60s AND a misconfigured health check at the same time).

**Fault tree template:**

```
## Fault Tree: [Top-level failure event]

### Top Event
[Describe the failure visible to users]

### Gate Decomposition

| Parent Event | Gate Type | Child Events | Evidence |
|---|---|---|---|
| [Top event] | OR | [Event A], [Event B] | |
| [Event A] | AND | [Event A1], [Event A2] | |
| [Event B] | OR | [Event B1], [Event B2] | |

### Minimal Cut Sets
(Smallest combinations of base events that cause the top event)
1. [Event A1] + [Event A2]  (both required — AND gate)
2. [Event B1] alone          (sufficient — OR gate)
3. [Event B2] alone          (sufficient — OR gate)

### Prevention Priority
Fix the minimal cut set with the fewest events first — it has the fewest barriers to failure.
```

### Iceberg Model
Best for recurring failures.
- Thinking posture: "Move from event -> pattern -> structure -> mental model."

### Inversion
Best for prevention planning.
- Thinking posture: "What would guarantee failure, and how do we block it?"

### Ladder of inference
Best for de-biasing diagnosis.
- Thinking posture: "Audit reasoning steps, not just conclusions."

### Productive Thinking Model
Best for turning diagnosis into actionable solutions.
- Thinking posture: "From current reality to feasible path."

### Conflict Resolution Diagram
Best when stakeholders have competing but valid goals.
- Thinking posture: "Find shared objective beneath opposing positions."

---

## Hypothesis-driven RCA

When you have multiple competing theories, use a structured hypothesis table to test each one systematically. This prevents anchoring on the first plausible cause.

**Process:**
1. List all plausible hypotheses (minimum 3).
2. For each, define a test plan and evidence threshold **before** investigating.
3. Execute tests. Record results honestly — including evidence that contradicts your favorite theory.
4. Converge on the hypothesis with the strongest supporting evidence.

**Worked example — API latency spike (p99 jumped from 200ms to 4s):**

| Hypothesis # | Description | Test Plan | Evidence Threshold | Result |
|---|---|---|---|---|
| H1 | Slow database queries due to missing index after schema migration | Check slow query log; compare query plans before/after migration | Query time > 1s on affected table; new sequential scan visible | ❌ **Rejected** — No schema migration in last 7 days; query plans unchanged |
| H2 | Upstream payment provider latency increase | Check payment provider status page; measure external call latency in traces | External call p99 > 2s during incident window | ❌ **Rejected** — Payment provider p99 stable at 180ms |
| H3 | Thread pool exhaustion from new async job running on same pool | Check thread pool metrics; correlate job schedule with latency spike | Thread pool utilization > 95% coinciding with spike; new job deployed recently | ✅ **Confirmed** — Batch export job (deployed 2h before) consumed 18/20 threads at spike time |
| H4 | GC pressure from memory leak in new feature | Check GC pause times and heap usage | GC pauses > 500ms; heap growing monotonically | ❌ **Rejected** — GC pauses normal (< 50ms); heap stable |

**Conclusion:** H3 confirmed. The batch export job shared the API thread pool and starved request handlers. Fix: move batch jobs to a dedicated thread pool.

**Hypothesis-driven RCA template:**

```
## Hypothesis-Driven Root Cause Analysis
**Incident:** [title]
**Date:** [date]
**Symptom:** [precise description]

| Hypothesis # | Description | Test Plan | Evidence Threshold | Result |
|---|---|---|---|---|
| H1 | | | | |
| H2 | | | | |
| H3 | | | | |

**Confirmed root cause:** [which hypothesis, with evidence summary]
**Contributing factors:** [other hypotheses that were partially true]
```

---

## Blameless postmortem template

Use this after any incident rated SEV-2 or higher. The goal is organizational learning, not punishment. Write it within 48 hours of resolution while memory is fresh.

```
## Postmortem: [Incident Title]

### Summary
- **Date:** [YYYY-MM-DD]
- **Duration:** [start time] → [end time] ([X] hours [Y] minutes)
- **Severity:** [SEV-1 / SEV-2 / SEV-3]
- **Impact:** [e.g., "12% of users unable to complete checkout for 47 minutes"]
- **Authors:** [names]
- **Status:** [Draft / In Review / Final]

### Timeline (all times UTC)

| Time | Event |
|---|---|
| 14:32 | Monitoring alert fires: error rate > 5% on /api/checkout |
| 14:35 | On-call engineer acknowledges alert, begins investigation |
| 14:42 | Identifies failing dependency: payment-service returning 503 |
| 14:50 | Escalates to payment team; incident channel created |
| 15:01 | Payment team identifies exhausted connection pool to Stripe API |
| 15:08 | Mitigation applied: connection pool size increased from 10 to 50 |
| 15:12 | Error rate returns to baseline; users can check out |
| 15:30 | Monitoring confirms stable recovery; incident closed |

### Root Causes
1. **Primary:** Connection pool sized for average load, not peak.
   Pool configured with hard-coded value (10) set during initial launch
   when traffic was 20% of current volume.
2. **Contributing:** No alerting on connection pool utilization. The pool
   was at 95%+ for 3 days before exhaustion with no warning.
3. **Contributing:** Load test suite does not cover checkout flow under
   peak concurrency.

### What Went Well
- Alert fired within 2 minutes of impact.
- On-call engineer escalated appropriately and quickly.
- Mitigation was effective and applied within 36 minutes.

### What Went Poorly
- No connection pool metrics in dashboard — had to query manually.
- Runbook for payment-service was last updated 8 months ago.
- Initial investigation focused on application code rather than infra.

### Action Items

| ID | Action | Owner | Priority | Due Date | Status |
|---|---|---|---|---|---|
| AI-1 | Add connection pool utilization to payment-service dashboard | @backend-team | P1 | 2024-02-15 | TODO |
| AI-2 | Set alert on pool utilization > 80% | @sre-team | P1 | 2024-02-15 | TODO |
| AI-3 | Update payment-service runbook | @on-call-author | P2 | 2024-02-22 | TODO |
| AI-4 | Add peak-concurrency checkout scenario to load tests | @qa-team | P2 | 2024-03-01 | TODO |
| AI-5 | Implement dynamic connection pool sizing based on traffic | @backend-team | P3 | 2024-03-15 | TODO |

### Lessons Learned
1. Hard-coded resource limits become time bombs as traffic grows.
   Prefer dynamic sizing or at minimum alert on utilization ratios.
2. Dashboards should include all resource pool metrics by default —
   if a service uses a pool, the pool's health is part of the service's health.
3. Runbooks decay. Schedule quarterly review of all SEV-1-eligible runbooks.
```

---

## Use-case bundles

| Situation | Recommended Method Combination |
|---|---|
| Operational incident repeats weekly | Ishikawa + Iceberg + Inversion |
| Cross-team blame cycle | Ladder of inference + Conflict Resolution Diagram |
| Root cause known but fix unclear | Productive Thinking Model |
| Single cascading failure chain | 5 Whys |
| Multiple conditions combined to cause failure | Fault Tree Analysis |
| Several competing theories about cause | Hypothesis-driven RCA |
| Post-incident organizational learning | Blameless Postmortem + Evidence Checklist |
| New system with unknown failure modes | Fishbone Diagram + Inversion |

---

## Output template

```
## Root Cause Analysis: [Title]

### Symptom Summary
[What happened, when, who was affected, severity]

### Evidence Reviewed
- [List every data source consulted]

### Hypothesis List
| # | Hypothesis | Status |
|---|---|---|
| H1 | [description] | Confirmed / Rejected / Inconclusive |

### Most Likely Causes (with confidence)
1. [Cause] — Confidence: High/Medium/Low — Evidence: [summary]

### Fixes Mapped to Causes
| Cause | Fix | Owner | Timeline |
|---|---|---|---|
| [cause 1] | [fix] | [who] | [when] |

### Verification Signals
- [How will we know the fix worked?]
- [What metric/alert should change?]
- [When will we check?]
```

---

## Quality checks

### Analysis quality
- [ ] Is each action item tied to a specific root cause (not just the symptom)?
- [ ] Did we challenge favorite theories with counterevidence?
- [ ] Are human/process/system factors all considered?
- [ ] Did we collect evidence **before** forming hypotheses?
- [ ] Can we read the causal chain forward (root cause → symptom) and it holds?
- [ ] Did we identify contributing factors, not just the primary cause?
- [ ] Have we distinguished correlation from causation in our evidence?

### Completeness checks
- [ ] Is the timeline complete with no gaps > 5 minutes during active incident?
- [ ] Are all data sources listed (even ones that showed nothing)?
- [ ] Did we document what we ruled out and why?
- [ ] Are action items specific, owned, and time-bound (not "improve monitoring")?
- [ ] Is there a follow-up date to verify fixes are effective?

### Blamelessness checks
- [ ] Does the analysis focus on mechanisms, not individuals?
- [ ] Would the people involved feel safe reading this document?
- [ ] Does each "human error" finding trace back to a system that allowed the error?
- [ ] Are action items about changing systems, not changing people?

### Reuse checks
- [ ] Is this postmortem searchable by future teams with similar symptoms?
- [ ] Did we tag it with affected services, failure categories, and root cause type?
- [ ] Are templates and runbooks updated based on findings?
- [ ] Is there a link to this postmortem in the relevant service's documentation?
