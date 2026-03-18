# Question Bank

Standard brainstorming questions for the planning phase. Select 3-5 questions based on context. Users answer in compact form: `1b,2d,3g,4a,5c`.

## Question selection

| Context | Use questions |
|---|---|
| Greenfield project | Q1, Q2, Q3, Q4, Q5 |
| New feature in existing project | Q1, Q2, Q4, Q6, Q7 |
| Refactor or migration | Q1, Q3, Q4, Q7, Q8 |
| Bug fix campaign | Q1, Q4, Q5, Q9 |
| Infrastructure or DevOps | Q1, Q2, Q3, Q5, Q10 |

## Questions

### Q1: What are you building?

```
a) Greenfield project from scratch
b) Major new feature for an existing project
c) Multiple related features (feature bundle)
d) Refactor or rewrite of existing functionality
e) Bug fix campaign (multiple related bugs)
f) Infrastructure or DevOps setup
g) API or integration development
h) Migration (framework, database, cloud)
i) Documentation overhaul
j) Testing infrastructure and coverage
k) Performance optimization
l) Security hardening
m) UI/UX redesign
n) Data pipeline or ETL system
o) Monitoring and observability
p) CI/CD pipeline improvement
q) Internationalization or localization
r) Accessibility compliance
s) Third-party integration bundle
t) Other (describe in follow-up)
```

### Q2: How deep should decomposition go?

```
a) Light — Epics → Tasks (2 levels, well-understood work)
b) Standard — Epics → Features → Tasks (3 levels, recommended)
c) Deep — Epics → Features → Tasks → Subtasks (4 levels, complex projects)
d) Maximum — 5+ levels (enterprise, compliance-heavy)
e) Adaptive — 3 levels default, deeper where complexity warrants
```

### Q3: How many execution waves?

```
a) 1 wave — everything in parallel
b) 2 waves — foundation → features
c) 3 waves — foundation → core → polish
d) 4 waves — foundation → core → advanced → release
e) 5 waves — foundation → core → integrations → advanced → hardening
f) 6+ waves — complex multi-phase (describe in follow-up)
g) Manual — I will specify the wave structure
```

### Q4: What does done look like?

```
a) All tests pass with coverage above threshold
b) Feature works end-to-end with QA sign-off
c) Deployed to production with zero downtime
d) Documentation written and reviewed
e) Performance benchmarks met
f) Security audit passed
g) Accessibility standards met (WCAG 2.1 AA)
h) API contract verified against spec
i) Migration complete with data integrity verified
j) Monitoring and alerting operational
k) Multiple of the above (specify in follow-up)
l) Custom criteria (describe in follow-up)
```

### Q5: How should agents execute?

```
a) Maximum parallelism — all ready issues at once
b) Controlled — max 3 agents concurrently
c) Conservative — max 2 agents concurrently
d) Sequential — one issue at a time
e) Mixed — parallel within waves, confirm between waves
f) Manual — approve each dispatch individually
```

### Q6: Integration surface?

```
a) Standalone — no external dependencies
b) Internal APIs — other team services
c) Third-party APIs — vendor integrations
d) Database changes — schema migrations
e) Message queues — async patterns
f) File systems — storage and retrieval
g) Multiple of the above
```

### Q7: Existing patterns?

```
a) Follow codebase conventions strictly
b) Introduce new patterns where they improve design
c) Major refactor — establish new conventions
d) Mix — follow existing for most, improve where critical
e) I will specify in follow-up
```

### Q8: Migration strategy?

```
a) Big bang — switch everything at once
b) Strangler fig — gradually replace
c) Parallel run — old and new side by side
d) Feature flags — toggle old/new
e) Blue/green deployment
f) Canary rollout
```

### Q9: Bug priority grouping?

```
a) By severity — critical first
b) By component — group by module
c) By root cause — fix shared causes first
d) By user impact — most-affected first
e) By complexity — quick wins first
```

### Q10: Infrastructure scope?

```
a) Local development environment
b) CI/CD pipeline
c) Staging environment
d) Production infrastructure
e) Monitoring and observability
f) Security and compliance
g) Full stack (all above)
h) Specific components (specify in follow-up)
```

## Formatting

Present only the selected questions (3-5). Number them sequentially. End with:

```
**Answer format:** `1b,2c,3d,4a,5e` (one letter per question)
```
