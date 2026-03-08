# 06 - Modern Practices

Engineering practices that address the realities of modern software delivery: cloud infrastructure, distributed systems, continuous deployment, and the need for security, reliability, and observability at scale. These practices reflect hard-won lessons from organizations operating at the frontier of software engineering.

---

## Practices Index

| # | Practice | File | Core Idea |
|---|---|---|---|
| 1 | Infrastructure as Code | [infrastructure-as-code.md](./infrastructure-as-code.md) | Treat infrastructure as version-controlled, tested, reviewable software |
| 2 | Security by Design | [security-by-design.md](./security-by-design.md) | Least privilege, defense in depth, zero trust from day one |
| 3 | Observability | [observability.md](./observability.md) | Logs, metrics, traces -- understand why your system behaves as it does |
| 4 | Progressive Delivery | [progressive-delivery.md](./progressive-delivery.md) | Feature flags, canaries, blue-green -- decouple deploy from release |
| 5 | DevOps Culture | [devops-culture.md](./devops-culture.md) | Shared ownership, blameless postmortems, error budgets |
| 6 | Shift-Left Everything | [shift-left-everything.md](./shift-left-everything.md) | Move quality checks earlier: testing, security, performance, accessibility |

---

## How These Practices Relate

These six practices form an interconnected system for modern software delivery:

- **Infrastructure as Code** provides the foundation: reproducible, auditable environments that everything else depends on.
- **Security by Design** ensures that the infrastructure and application are secure from the architecture level, not patched afterward.
- **Observability** gives you the visibility to understand what is happening in production -- essential for all other practices.
- **Progressive Delivery** uses observability data to safely roll out changes, feature flags to control exposure, and canary analysis to detect problems early.
- **DevOps Culture** provides the organizational structure (shared ownership, blameless postmortems, error budgets) that makes the technical practices sustainable.
- **Shift-Left Everything** moves the quality checks that these practices depend on (security scans, performance tests, accessibility audits) earlier in the development cycle, where they are cheapest and fastest.

---

## Recommended Reading Order

1. Start with **DevOps Culture** for the organizational foundation
2. Read **Infrastructure as Code** for the technical foundation
3. Study **Observability** to understand production visibility
4. Learn **Security by Design** to build secure systems from the start
5. Adopt **Progressive Delivery** for safe, controlled releases
6. Apply **Shift-Left Everything** to move quality checks earlier across all disciplines

---

## Key Metrics (DORA)

The DevOps Research and Assessment (DORA) team identified four key metrics that distinguish high-performing teams:

| Metric | Elite Performance | Low Performance |
|---|---|---|
| **Deployment frequency** | On-demand (multiple times per day) | Between once per month and every 6 months |
| **Lead time for changes** | Less than one hour | Between one month and six months |
| **Change failure rate** | 0-15% | 46-60% |
| **Time to restore service** | Less than one hour | Between one month and six months |

The practices in this section directly improve all four metrics.
