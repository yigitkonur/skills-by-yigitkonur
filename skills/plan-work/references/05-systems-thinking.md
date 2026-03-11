# Systems Thinking

## Read this if
- Local fixes create side effects.
- Outcomes emerge from cross-team/tool interactions.
- Problems keep returning in different forms.
- You suspect a "quick fix" is making the real problem worse.
- You need to explain systemic risk to stakeholders who think linearly.

## Planning vision for this stage
Think in relationships and loops, not isolated parts.

## System mapping flow

1. Define system boundary.
2. Identify key elements and links.
3. Mark delays and constraints.
4. Identify feedback loops.
5. Choose leverage points.

---

## Causal loop diagrams

Causal loop diagrams (CLDs) show how variables in a system influence each other. They are the primary tool for making feedback loops visible.

### Notation

| Symbol | Meaning | Example |
|--------|---------|---------|
| `──(+)──>` | Same direction: if A increases, B increases (and vice versa) | More developers → more code output |
| `──(-)──>` | Opposite direction: if A increases, B decreases (and vice versa) | More automation → fewer manual errors |
| `R` | Reinforcing loop — amplifies change (virtuous or vicious cycle) | Growth flywheel |
| `B` | Balancing loop — resists change, seeks equilibrium | Thermostat, on-call burnout recovery |
| `──||──>` | Delay — effect is not immediate | Hiring → productivity (onboarding delay) |

### How to draw a CLD

1. **Pick the problem symptom** — start with what you observe (e.g., "deploys are slow").
2. **Ask "what causes this?"** — write that variable and draw an arrow to the symptom.
3. **Ask "what does this cause?"** — follow each variable forward.
4. **Label each arrow** with (+) or (-).
5. **Trace loops** — when a chain returns to an earlier variable, you found a feedback loop.
6. **Classify each loop** — odd number of (-) arrows = Balancing; even (or zero) = Reinforcing.

### Worked example: Technical debt loop

```
          more features requested
                |
                | (+)
                v
        pressure to ship fast
                |
                | (+)
                v
          shortcuts taken ──────(+)──────> technical debt
                ^                              |
                |                              | (+)
                |                              v
                |                      slower development
                |                              |
                |              (+)             |
                └──────────────────────────────┘

Loop type: REINFORCING (vicious cycle)
All arrows are (+) → even number of (-) = Reinforcing
```

**Reading this diagram:** More feature requests → more pressure → more shortcuts → more debt → slower development → even more pressure to take shortcuts. Without intervention, this loop accelerates.

**Leverage points in this loop:**
- Reduce feature pressure (change the input)
- Allocate explicit debt paydown time (break the shortcut→debt link)
- Make debt visible with metrics (add a balancing loop)

---

## Stock and flow models

Stocks are accumulations — things you can count at a point in time. Flows are rates — things that change stocks over time.

### Structure

```
                  inflow                          outflow
  [source] ════════╗          ┌─────────┐          ╔════════ [sink]
                   ╚══════>   │  STOCK  │   ═════> ╝
                              └─────────┘
                             (accumulation)
```

### Software engineering examples

**Bug stock:**

```
  bugs introduced ═══>  [ Known Bugs ]  ═══> bugs fixed
   (inflow rate)        (stock: count)        (outflow rate)
```

If inflow > outflow, the bug count grows. Metrics to track: inflow rate per sprint, outflow rate per sprint, net stock trend.

**Feature stock:**

```
  features shipped ═══>  [ Active Features ]  ═══> features deprecated
    (inflow rate)         (stock: count)             (outflow rate)
```

If you never deprecate, the maintenance burden (a second stock fed by Active Features) grows without bound.

**Team knowledge stock:**

```
  learning + hiring ═══>  [ Team Knowledge ]  ═══> attrition + forgetting
    (inflow rate)          (stock: expertise)        (outflow rate)
```

Key insight: knowledge has a **delay** on inflow (onboarding takes months) but can have sudden outflow (key person leaves).

### When to use stock-and-flow vs. CLDs

| Use stock-and-flow when… | Use CLDs when… |
|--------------------------|----------------|
| You need to quantify accumulations | You need to show influence relationships |
| You want to model rates and capacity | You want to find feedback loops |
| The problem involves resource pools | The problem involves behavioral dynamics |

---

## Donella Meadows' 12 leverage points

Ranked from **least** to **most** effective. Intervene at the highest level you can influence.

| # | Leverage point | Effectiveness | Software engineering example |
|---|---------------|---------------|------------------------------|
| 12 | Constants, parameters, numbers | Weakest | Changing a timeout from 30s to 60s |
| 11 | Buffer sizes | Low | Increasing queue depth, adding more disk |
| 10 | Structure of material stocks and flows | Low | Redesigning the CI pipeline topology |
| 9 | Delays | Moderate | Shortening feedback loops (faster tests, quicker PR reviews) |
| 8 | Negative (balancing) feedback loops | Moderate | Adding alerting, circuit breakers, error budgets |
| 7 | Positive (reinforcing) feedback loops | Moderate-high | Creating an inner-source contribution flywheel |
| 6 | Information flows | High | Making deploy frequency, DORA metrics, or cost data visible to teams |
| 5 | Rules of the system | High | Changing the code review policy, SLA definitions, on-call rotation rules |
| 4 | Self-organization | High | Enabling teams to choose their own tools, architectures, and processes |
| 3 | Goals of the system | Very high | Shifting from "ship features" to "deliver customer outcomes" |
| 2 | Paradigm / mindset | Strongest | Moving from "testing is QA's job" to "quality is everyone's responsibility" |
| 1 | Transcending paradigms | Beyond | Recognizing that all mental models are incomplete and staying adaptive |

**Practical rule of thumb:** Most engineers instinctively reach for levels 12–10 (tweak a parameter, add capacity). The highest-impact changes happen at levels 6–2 (change what information people see, change the rules, change the goals).

---

## System boundary definition template

Before mapping any system, define its boundary. Use these questions:

### Scope questions

| Question | Purpose | Example answer |
|----------|---------|----------------|
| What observable problem are we investigating? | Anchors the analysis | "Production deploys take 3 hours" |
| What is inside this system? | Defines elements to map | CI/CD pipeline, approval gates, test suites, deploy tooling |
| What is outside (treated as external input/output)? | Prevents scope creep | Customer requests, third-party SaaS uptime, budget decisions |
| Where are the interfaces between inside and outside? | Identifies boundary interactions | PR merged (input), production traffic served (output) |
| What are the significant delays? | Highlights hidden dynamics | Test suite runtime, approval wait time, environment provisioning |
| Who are the actors? | Identifies human feedback loops | Developers, reviewers, SRE on-call, release manager |
| What resources are shared across boundaries? | Finds contention points | Staging environment, shared CI runners, DBA review queue |

### Boundary checklist

- [ ] Boundary is small enough to analyze in one session
- [ ] All key feedback loops are inside the boundary
- [ ] External factors are listed but explicitly excluded from the model
- [ ] At least one measurable outcome is inside the boundary
- [ ] Delays longer than 1 hour are identified and marked

---

## System archetypes in software

Archetypes are recurring system structures. Recognizing them accelerates diagnosis.

### Fixes that Fail

**Pattern:** A quick fix solves the symptom but creates a delayed side effect that worsens the original problem.

```
  Problem ──(quick fix)──> Symptom reduced
     ^                          |
     |        (delay)           |
     └──── side effect ────────┘
```

**Software example:** A memory leak is "fixed" by adding a cron job that restarts the service every 4 hours. The real leak is never investigated. The restart causes brief outages, connection pool corruption, and lost in-flight requests — eventually causing more incidents than the original leak.

**Diagnostic question:** "Is our fix addressing the symptom or the cause?"

### Shifting the Burden

**Pattern:** A workaround reduces pressure to implement the real solution. Over time, the workaround becomes entrenched and the capability to implement the real fix atrophies.

**Software example:** Instead of fixing the flaky test, the team adds a retry-and-ignore wrapper. Over months, more tests become flaky. The team's ability to write reliable tests atrophies. Eventually, the test suite provides no signal.

**Diagnostic question:** "Is this workaround reducing our motivation to solve the root cause?"

### Limits to Growth

**Pattern:** A reinforcing loop drives initial success, but eventually hits a constraint that slows or stops growth.

**Software example:** A microservices migration increases team autonomy and velocity (reinforcing loop). But as service count grows, the shared Kubernetes cluster runs out of capacity, service-to-service latency increases, and debugging distributed failures becomes exponentially harder (limiting constraint).

**Diagnostic question:** "What constraint will we hit if this trend continues for 6 more months?"

### Tragedy of the Commons

**Pattern:** Multiple actors share a resource. Each actor's rational self-interest depletes the resource, harming everyone.

**Software example:** All teams share a single staging environment. Each team extends their usage window "just a little." Staging becomes permanently contested. No team can get a clean test window. Everyone's release quality drops.

**Diagnostic question:** "Is each team's rational behavior degrading a shared resource?"

---

## Worked example: "Why does deploying to production take 3 hours?"

### Step 1 — Define the boundary

- **Inside:** Code merge → production traffic serving
- **Outside:** Feature planning, customer feedback, infrastructure procurement
- **Actors:** Developer, CI system, reviewer/approver, deploy tooling, SRE on-call

### Step 2 — Map the elements and delays

```
  PR merged
      │
      ▼
  CI pipeline (25 min) ──delay──> flaky test retries (10 min avg)
      │
      ▼
  Security scan (15 min)
      │
      ▼
  Approval gate ──delay──> waiting for approver (0–90 min)
      │
      ▼
  Staging deploy (10 min)
      │
      ▼
  Manual smoke test ──delay──> tester availability (0–45 min)
      │
      ▼
  Production deploy (canary: 20 min, full rollout: 15 min)
      │
      ▼
  Monitoring bake time (30 min)
```

**Total wall clock:** ~25 + 10 + 15 + 45 + 10 + 22 + 20 + 15 + 30 ≈ **3 hours**
**Actual compute work:** ~115 min. **Waiting/delays:** ~65 min.

### Step 3 — Identify feedback loops

**B1 (Balancing — Risk aversion):** Past production incidents → more approval gates → longer deploy time → larger batches → riskier deploys → more incidents.

**R1 (Reinforcing — Flaky tests):** Flaky tests → retries added → less pressure to fix → more flaky tests → more retries.

**B2 (Balancing — Manual testing):** Automated tests lack coverage → manual smoke tests added → less incentive to automate → coverage stays low.

### Step 4 — Identify archetypes

- **Fixes that Fail:** Adding approval gates to reduce incidents actually increases batch size and risk.
- **Shifting the Burden:** Manual smoke tests prevent investment in automated integration tests.

### Step 5 — Choose leverage points

| Intervention | Meadows level | Expected impact |
|-------------|---------------|-----------------|
| Increase CI runner count | 11 (buffers) | Low — saves minutes, not the bottleneck |
| Fix flaky tests | 9 (delays) | Moderate — removes 10 min + retry noise |
| Auto-approve low-risk changes | 5 (rules) | High — removes 0–90 min wait for most deploys |
| Make deploy frequency visible per team | 6 (information) | High — creates social pressure + reveals bottlenecks |
| Shift to continuous deployment culture | 2 (paradigm) | Highest — but requires org-wide buy-in |

**Recommended sequence:** Fix flaky tests (quick win) → auto-approve low-risk changes (high impact) → make metrics visible (sustain improvement).

---

## Method steering

### Connection circles
Best for revealing influence paths.
- Thinking posture: "What affects what, and in which direction?"

### Concept map
Best for shared understanding across stakeholders.
- Thinking posture: "Build a common mental model before planning interventions."

### Balancing feedback loop
Best for understanding resistance to change.
- Thinking posture: "What pushes the system back to status quo?"

### Reinforcing feedback loop
Best for identifying accelerators.
- Thinking posture: "What amplifies growth or decline over time?"

### Iceberg Model
Best for linking visible events to hidden structures.
- Thinking posture: "Treat recurring events as system output, not isolated mistakes."

| Layer | Question | Example |
|-------|----------|---------|
| Events | What happened? | "Deploy failed at 2 AM" |
| Patterns | What trends repeat? | "Deploys fail more on Fridays" |
| Structure | What system produces this pattern? | "Friday deploys batch a week of changes" |
| Mental models | What beliefs sustain this structure? | "We can't deploy more than once a week" |

### Second-order thinking (system ripple check)
Best for intervention impact forecasting.
- Thinking posture: "What downstream effects does this leverage point trigger?"

**Template for second-order analysis:**
1. First-order effect: What changes immediately?
2. Second-order effect: What changes because of that change?
3. Who adapts their behavior, and how?
4. What feedback loops are created or broken?

---

## When NOT to use systems thinking

Systems thinking is powerful but not always appropriate. Use simpler methods when:

| Situation | Why systems thinking is overkill | Better approach |
|-----------|----------------------------------|-----------------|
| Simple, linear problem with a clear single cause | No feedback loops to map | Standard root cause analysis (5 Whys) |
| Active incident requiring immediate response | Time spent mapping delays resolution | Incident response runbook, direct debugging |
| Well-understood problem with a known fix | System already mapped; just execute | Checklist or standard operating procedure |
| One-time task with no recurring pattern | No loops to identify or break | Just do the task |
| Politically sensitive situation where mapping creates blame | Diagrams can be weaponized | Private analysis, then frame solutions positively |

**Rule of thumb:** If you can explain the cause-and-effect chain in a single sentence with no "but then..." or "which causes...", you probably don't need systems thinking.

---

## Use-case bundles

- Multi-team reliability issue → Connection circles + Iceberg + feedback loops
- Organization-wide process redesign → Concept map + balancing loop analysis
- Adoption flywheel planning → Reinforcing loop + second-order checks
- Recurring incidents that resist fixes → Archetypes (Fixes that Fail, Shifting the Burden)
- Capacity planning → Stock and flow models + Limits to Growth archetype
- Cross-team resource contention → Tragedy of the Commons + boundary definition

## Output template
- System boundary (use the boundary definition template above)
- Key elements and relationships (CLD or concept map)
- Stocks and flows (if resource accumulation is relevant)
- Feedback loops identified (labeled R/B with narrative)
- Archetypes matched (with diagnostic question answers)
- Leverage points (ranked by Meadows' hierarchy)
- Recommended intervention sequence (quick wins first, paradigm shifts last)
- System-level risks and mitigations


## Steering experiences

### SE-01: Full systems map built for a local problem
**What happens:** Agent draws a complete causal loop diagram with 15 variables for a problem that involves 3 components. The map is accurate but the effort was disproportionate.
**Why it happens:** Systems thinking tools are powerful and engaging. Agents enjoy building comprehensive maps even when the problem is simple.
**Prevention:** Start with the smallest system boundary that contains the problem. If the causal chain has fewer than 4 nodes, a simple dependency list is enough -- skip the full CLD.

### SE-02: Feedback loops identified but not classified
**What happens:** Agent identifies 3 feedback loops in the system but does not label them as reinforcing (R) or balancing (B). Without classification, the leverage analysis is guesswork.
**Why it happens:** Identifying loops feels like the hard part. Classification feels like bookkeeping.
**Prevention:** Every loop must be labeled R (reinforcing -- amplifies change) or B (balancing -- resists change). The label determines whether intervention should amplify, dampen, or break the loop.

### SE-03: Interventions target low-leverage points
**What happens:** Agent recommends fixing a parameter (e.g., increase the timeout) instead of changing the feedback structure that causes the timeout to be insufficient.
**Why it happens:** Parameter changes are easy to implement and easy to recommend. Structural changes feel risky.
**Prevention:** Use Meadows leverage hierarchy: parameters < buffers < feedback loops < rules < goals < paradigms. If the recommended intervention is a parameter change, ask: "Is there a higher-leverage point that would make this parameter irrelevant?"

### SE-04: Overcomplexity -- the map becomes the deliverable
**What happens:** The systems map grows to 20+ nodes with detailed annotations. The agent spends most of the time maintaining the map rather than extracting actionable insights.
**Why it happens:** Map-building feels productive. There is no stopping rule in the template.
**Prevention:** The deliverable is the intervention recommendation, not the map. The map is a tool. If the map has more than 12 nodes, you are probably mapping more system than the problem requires. Prune to the boundary of influence.
