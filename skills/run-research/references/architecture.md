# Architecture & Design Research Guide

## Quick Reference: Which Tools For Which Decision

| # | Architecture Decision | Primary Tools | Why These Tools |
|---|----------------------|--------------|-----------------|
| 01 | Design Pattern Selection | deep_research -> search_google -> scrape_pages -> search_reddit -> fetch_reddit | Patterns involve nuanced trade-offs needing synthesis; canonical sources provide frameworks; Reddit has survivorship-bias-free signal |
| 02 | State Management Approach | deep_research -> search_google -> scrape_pages -> search_reddit -> fetch_reddit | Rapidly changing landscape needs current synthesis; benchmarks require extraction; Reddit has migration stories |
| 03 | API Style Decision | deep_research -> search_google -> scrape_pages -> search_reddit -> fetch_reddit | Multi-boundary problem needs holistic analysis; engineering blogs document real decisions; Reddit has operational metrics |
| 04 | Database Selection | deep_research -> search_google -> scrape_pages -> search_reddit -> fetch_reddit | Total cost of ownership requires multi-dimensional synthesis; benchmarks need extraction; Reddit has cost surprises |
| 05 | Caching Strategy Design | deep_research -> search_google -> scrape_pages -> search_reddit -> fetch_reddit | Multi-data-type strategy needs holistic design; vendor guides have decision trees; Reddit has failure mode stories |
| 06 | Authentication Architecture | deep_research -> search_google -> scrape_pages -> search_reddit -> fetch_reddit | Security decisions cascade; OWASP sets the baseline; Reddit has security reviews in comment form |
| 07 | Microservices vs Monolith | deep_research -> search_google -> scrape_pages -> search_reddit -> fetch_reddit | Most context-dependent decision (team size, org structure); Reddit has the microservices backlash data |
| 08 | Real-Time Architecture | deep_research -> search_google -> scrape_pages -> search_reddit -> fetch_reddit | Transport and application protocol are tightly coupled; pricing models are complex; Reddit has scaling numbers |
| 09 | Event-Driven Design | deep_research -> search_google -> scrape_pages -> search_reddit -> fetch_reddit | Broker selection involves subtle delivery semantic differences; schema evolution needs synthesis |
| 10 | Deployment Strategy | deep_research -> search_google -> scrape_pages -> search_reddit -> fetch_reddit | Cost trajectory analysis needs multi-source modeling; Reddit has billing shock stories |

---

## 01. Design Pattern Selection
### Tools: all 5 (deep_research primary)
### Query Templates:
**deep_research**: `"WHAT I NEED: Determine whether CQRS with Event Sourcing or Repository Pattern for an order system (~5K orders/day). SPECIFIC QUESTIONS: 1) Scale threshold for CQRS+ES? 2) Event schema evolution? 3) Operational costs? 4) CQRS without ES? 5) Failure modes?"`
**search_google**: `["CQRS vs repository pattern trade-offs", "event sourcing production lessons 2024 2025", "site:martinfowler.com repository pattern event sourcing", "over-engineering design patterns CRUD"]`
**scrape_pages**: `what_to_extract = "decision criteria|trade-offs|scale thresholds|when NOT to use|team size recommendations"`
**search_reddit**: `["CQRS regret complexity not worth it", "event sourcing production experience", "r/ExperiencedDevs design pattern over-engineering"]`
**fetch_reddit**: 5-10 threads with high comment counts from r/ExperiencedDevs, r/softwarearchitecture.
### Best Practices:
- Attach your current code so deep_research analyzes your actual complexity
- Ask about failure modes explicitly -- pattern articles rarely cover what goes wrong
- Reddit includes those who rolled back; blog posts only come from those who succeeded
- Search for "when NOT to use" -- more useful than "when to use"

## 02. State Management Approach
### Tools: all 5 (deep_research primary)
### Query Templates:
**deep_research**: `"WHAT I NEED: Select state management for React 19 dashboard (~200 components, 15 slices). SPECIFIC QUESTIONS: 1) Zustand vs Redux Toolkit after 12+ months? 2) Jotai for complex derived state? 3) Do we need an external library with React 19? 4) Migration paths from Redux?"`
**search_google**: `["zustand vs redux toolkit vs jotai benchmark 2025", "react state management decision tree", "state of react survey 2024 2025"]`
**scrape_pages**: `what_to_extract = "benchmark numbers|bundle sizes|re-render counts|satisfaction scores|migration steps"`
**search_reddit**: `["zustand vs redux toolkit 2024 2025 experience", "redux toolkit regret migrated to what", "react 19 do you still need state management"]`
**fetch_reddit**: Threads with "experience" or "after X months" in title. Look for library author comments.
### Best Practices:
- State management recommendations from 2022 may be obsolete -- always include current year
- Migration cost is often the deciding factor; ask about incremental migration paths
- Include server-side state (TanStack Query, SWR) if using React Server Components

## 03. API Style Decision
### Tools: all 5 (deep_research primary)
### Query Templates:
**deep_research**: `"WHAT I NEED: Choose between REST, GraphQL, gRPC, tRPC for SaaS with public consumers and internal service-to-service. SPECIFIC QUESTIONS: 1) Different styles at different boundaries? 2) REST vs gRPC latency? 3) GraphQL at >1M req/day? 4) Hidden GraphQL operational costs? 5) tRPC alongside REST?"`
**search_google**: `["REST vs GraphQL vs gRPC comparison 2024 2025", "netflix API gateway graphql engineering blog", "tRPC vs REST type safety"]`
**scrape_pages**: `what_to_extract = "architecture decisions|benchmarks|latency numbers|when NOT to use|versioning approach"`
**search_reddit**: `["graphql regret went back to REST", "gRPC vs REST microservices real experience", "graphql n+1 problem production"]`
### Best Practices:
- Describe all API boundaries -- each may warrant a different style
- Hybrid architectures (GraphQL for clients, gRPC for internal) are common and valid
- GraphQL's hidden costs (caching, N+1, query cost analysis) are routinely underestimated
- Extract concrete latency numbers from Reddit comments

## 04. Database Selection
### Tools: all 5 (deep_research primary)
### Query Templates:
**deep_research**: `"WHAT I NEED: Select database for multi-tenant SaaS with IoT data (~50K inserts/sec), time-series queries, relational metadata. SPECIFIC QUESTIONS: 1) PostgreSQL + TimescaleDB at 50K inserts/sec? 2) Polyglot persistence overhead? 3) DynamoDB costs? 4) Multi-tenancy isolation? 5) Failure modes at scale?"`
**search_google**: `["postgresql vs dynamodb vs mongodb benchmark 2024 2025", "jepsen postgresql mongodb consistency", "timescaledb vs influxdb benchmark", "total cost of ownership database"]`
**scrape_pages**: `what_to_extract = "benchmark results|query latency|throughput|pricing tiers|consistency guarantees|scaling limits"`
**search_reddit**: `["dynamodb cost surprise expensive bill", "postgresql 50000 writes per second tuning", "mongodb vs postgresql when to actually use mongodb"]`
**fetch_reddit**: Fetch AMA and "X years experience" threads for configuration tips and cost breakdowns.
### Best Practices:
- Total cost of ownership (including ops) matters more than raw benchmarks
- Search for Jepsen consistency tests -- they reveal guarantees (or violations) under failure
- DynamoDB costs are frequently surprising at scale; search for "DynamoDB expensive" explicitly

## 05. Caching Strategy Design
### Tools: all 5 (deep_research primary)
### Query Templates:
**deep_research**: `"WHAT I NEED: Design multi-layer caching for e-commerce (50K SKUs, sessions, search, dynamic pricing). SPECIFIC QUESTIONS: 1) Invalidation per data type? 2) Write-through vs cache-aside per type? 3) Redis Cluster vs single instance? 4) Stampede prevention? 5) When to add CDN?"`
**search_google**: `["caching patterns write-through cache-aside write-behind", "redis patterns site:redis.io", "cache stampede prevention production"]`
**scrape_pages**: `what_to_extract = "caching patterns|decision criteria|invalidation strategies|TTL recommendations|stampede prevention"`
**search_reddit**: `["cache invalidation nightmare production", "cache stampede thundering herd solution", "caching mistakes learned hard way"]`
### Best Practices:
- Different data types need different strategies, TTLs, and invalidation approaches
- Ask about failure modes: Redis down, cache stampede, cold cache after deploy
- Reddit has implementation recipes (Lua scripts, request coalescing patterns)

## 06. Authentication Architecture
### Tools: all 5 (deep_research primary)
### Query Templates:
**deep_research**: `"WHAT I NEED: Auth architecture for B2B SaaS with SSO (SAML/OIDC), magic links, passkeys. SOC2 required. SPECIFIC QUESTIONS: 1) Auth0 vs Clerk vs WorkOS vs custom? 2) Unified session management? 3) JWT with refresh vs opaque sessions? 4) Passkey maturity for B2B? 5) SOC2 auth requirements?"`
**search_google**: `["OWASP authentication best practices 2024 2025", "passkeys WebAuthn guide", "auth0 vs clerk vs workos pricing 2025", "JWT security httponly cookie"]`
**scrape_pages**: `what_to_extract = "security requirements|recommended practices|prohibited practices|pricing tiers|session management rules"`
**search_reddit**: `["auth0 vs clerk vs workos production 2024 2025", "JWT vs session token debate", "built custom auth regret"]`
### Best Practices:
- OWASP cheat sheets are non-negotiable starting points -- extract as requirements document
- Reddit surfaces provider comparison experiences that vendor pages never provide honestly
- Session management is the hardest part of auth architecture; ask about it explicitly
- Auth is one area where buying (Auth0/Clerk) is often safer than building

## 07. Microservices vs Monolith
### Tools: all 5 (deep_research primary)
### Query Templates:
**deep_research**: `"WHAT I NEED: Decompose monolith into microservices, adopt modular monolith, or stay as-is. Team of 12, 2-hour CI, no K8s experience. SPECIFIC QUESTIONS: 1) Team size threshold? 2) Operational cost without K8s? 3) Is modular monolith a real stepping stone? 4) Which services to extract first? 5) Communication patterns?"`
**search_google**: `["microservices vs monolith decision framework team size 2024 2025", "monolith first martin fowler", "modular monolith guide", "amazon prime video monolith case study"]`
**scrape_pages**: `what_to_extract = "decision criteria|team size thresholds|migration steps|decomposition patterns|when NOT to use microservices"`
**search_reddit**: `["microservices regret went back to monolith", "modular monolith experience production", "microservices operational cost small team"]`
**fetch_reddit**: Fetch famous threads (Amazon Prime Video, Segment.io). Look for migration timelines and cost breakdowns.
### Best Practices:
- Conway's Law reasoning: the decision is about organizational structure, not just technology
- Modular monolith is a legitimate architecture -- ask about it as a middle ground
- Search for infrastructure costs: K8s, service mesh, distributed tracing are significant upfront investment

## 08. Real-Time Architecture
### Tools: all 5 (deep_research primary)
### Query Templates:
**deep_research**: `"WHAT I NEED: Real-time layer for collaborative editor (~10K concurrent users, <100ms latency). SPECIFIC QUESTIONS: 1) WebSocket vs WebRTC at 10K? 2) Scaling across server instances? 3) Managed vs self-hosted? 4) How do CRDT libs (Yjs, Automerge) interact with transport?"`
**search_google**: `["WebSocket vs SSE vs long polling comparison 2024 2025", "WebSocket scaling architecture horizontal Redis pub/sub", "real-time collaborative editing CRDT OT comparison"]`
**scrape_pages**: `what_to_extract = "protocol features|connection limits|pricing per connection|pricing per message|reconnection handling"`
**search_reddit**: `["websocket scaling 10000 connections production", "websocket timeout corporate proxy", "pusher vs ably cost comparison"]`
### Best Practices:
- Transport and application protocol (CRDTs, OT) are tightly coupled -- reason about both
- 100 vs 10K vs 1M concurrent connections require fundamentally different architectures
- Reddit has failure mode stories (connection drops behind proxies, reconnection storms)
- Managed services charge differently: per connection vs per message -- extract and compare

## 09. Event-Driven Design
### Tools: all 5 (deep_research primary)
### Query Templates:
**deep_research**: `"WHAT I NEED: Event-driven architecture for e-commerce (orders, inventory, notifications, analytics). Choose Kafka, RabbitMQ, NATS, or Redis Streams at ~10K events/min. SPECIFIC QUESTIONS: 1) Is Kafka overkill? 2) Schema evolution (Avro/Protobuf/JSON Schema)? 3) Managed vs self-hosted cost? 4) Exactly-once in practice? 5) Saga patterns?"`
**search_google**: `["kafka vs rabbitmq vs nats comparison 2024 2025", "event-driven saga choreography orchestration", "schema registry evolution best practices"]`
**scrape_pages**: `what_to_extract = "delivery guarantees with conditions|ordering guarantees|retention|pricing|schema evolution support"`
**search_reddit**: `["kafka overkill small team alternative NATS redis streams", "event schema evolution production", "saga pattern production experience"]`
### Best Practices:
- Below 100K events/min, RabbitMQ or NATS may be simpler to operate than Kafka
- Schema evolution is the most underestimated challenge -- ask about it explicitly
- Delivery guarantees have conditions: Kafka exactly-once is transaction-scope-only; RabbitMQ ordering is queue-scoped
- NATS JetStream and Redis Streams have matured significantly -- ensure comparisons are current

## 10. Deployment Strategy
### Tools: all 5 (deep_research primary)
### Query Templates:
**deep_research**: `"WHAT I NEED: Deployment platform for full-stack SaaS (Next.js, Node.js, PostgreSQL, Redis). 2 devs, zero DevOps, budget $500-2000/month. SPECIFIC QUESTIONS: 1) When does Vercel become more expensive than AWS? 2) Is AWS ECS manageable for 2 people? 3) Serverless vs containers for sustained traffic? 4) Vendor lock-in risk? 5) Blue-green vs rolling vs canary?"`
**search_google**: `["vercel vs AWS vs cloudflare cost comparison 2024 2025", "railway render fly.io comparison 2025", "serverless vs containers decision framework"]`
**scrape_pages**: `what_to_extract = "pricing tiers|included limits|overage costs|compute pricing|bandwidth pricing|function limits"`
**search_reddit**: `["vercel expensive bill pricing shock production", "migrated from vercel to AWS why", "railway render fly.io production experience"]`
**fetch_reddit**: Fetch "hosting costs from 0 to X users" threads for itemized cost breakdowns.
### Best Practices:
- Cost at launch, 10x, and 100x reveals pricing curves that determine long-term viability
- Platform limits (connections, timeouts, deployment size) determine feasibility before cost matters
- Reddit has itemized cost breakdowns at specific traffic levels -- the best financial data available
- Consider staged approach: launch on PaaS for speed, migrate to AWS when spending exceeds threshold

---

## Universal Architecture Research Workflow

1. **Frame the decision** precisely: constraints, scale targets, team composition, risk tolerance.
2. **Start with deep_research** (unlike bug-fixing which starts with search_google). Architecture decisions benefit from synthesized analysis upfront.
3. **Use search_google** (5-7 keywords) for canonical sources, benchmarks, and decision frameworks. Use `site:` operators for high-quality sources.
4. **Use scrape_pages** on top 3-5 URLs to extract decision criteria, benchmark data, and pricing tables. Focus on "when to use" and "when NOT to use."
5. **Use search_reddit** (5-7 queries) for real-world experiences and regret stories. Search for "regret", "rolled back", "not worth it."
6. **Use fetch_reddit** (fetch_comments=True, use_llm=False) on 5-10 threads from r/ExperiencedDevs and r/softwarearchitecture.
7. **Synthesize with a second deep_research pass** if new questions arose. Feed Reddit and scrape_pages findings into a targeted follow-up.
8. **Build a decision matrix**: rows = criteria from authoritative sources, columns = options. Score using gathered data.

## Steering notes

1. **Start with `deep_research`**, not `search_google`. Architecture needs trade-off synthesis.
2. **Specific GOAL/WHY/KNOWN/APPLY.** "Should a 4-person team at 500 req/s migrate from Rails monolith?" not "should I use microservices?"
3. **Reddit reveals operational reality.** Search r/devops, r/microservices, r/softwarearchitecture.
4. **3-source verification strictly** -- architecture is expensive to reverse.
5. **Include cost forecasting** in queries.

### Modular monolith

Viable when: team <10, monolith with boundary issues, microservices overhead not justified. Queries: `"modular monolith" vs microservices [language]`.

### Migration sequencing

Strangler Fig (production, no downtime) vs Big Bang (greenfield, small) vs Branch by Abstraction (shared codebase, gradual).
