# Strangler Fig Pattern

**Incrementally replace a legacy system by gradually routing traffic from old components to new ones.**

---

## Origin

The Strangler Fig pattern was named by Martin Fowler in his 2004 article *"StranglerFigApplication,"* inspired by the strangler fig trees he observed in Australia. These trees grow around a host tree, gradually replacing it until the original tree dies and the fig stands on its own. Fowler applied this metaphor to software migration: instead of replacing a legacy system all at once, you build new functionality alongside it and gradually redirect traffic until the old system can be decommissioned. The pattern has since become the standard approach for legacy modernization at scale, popularized by companies like Amazon, Netflix, and Shopify.

---

## The Problem It Solves

Legacy systems accumulate years of business logic, edge cases, and institutional knowledge. A "big bang" rewrite — building a complete replacement and switching over — is one of the most dangerous projects in software engineering. The new system must replicate every feature of the old one (including undocumented behaviors), the team must maintain both systems during development, and the cutover is a single, high-risk moment. History is littered with failed rewrites: Netscape's rewrite (lost the browser wars), the FBI's Virtual Case File ($170M failure), and countless enterprise projects that were abandoned after years of effort.

---

## The Principle Explained

The Strangler Fig pattern avoids the big bang by taking an incremental approach. You identify a seam in the legacy system — a feature, a page, an API endpoint — and build a new implementation for that specific piece. A routing layer (reverse proxy, API gateway, load balancer) sits in front of both systems and directs traffic: old feature goes to the legacy system, new feature goes to the replacement.

Over time, you migrate more features. Each migration is small, testable, and reversible. If the new implementation has a bug, you route traffic back to the legacy system. The legacy system is never in a half-migrated state that does not work — at every point, the system as a whole is functional because unchanged features still hit the old code.

The pattern has three phases: **Transform** (build the new component), **Coexist** (run old and new side by side, routing selectively), and **Eliminate** (remove the old component once all traffic is routed to the new one). The "coexist" phase can last months or years — and that is fine. The goal is risk reduction, not speed.

---

## Code Examples

### BAD: Big bang rewrite — all-or-nothing cutover

```typescript
// The dangerous approach: rewrite everything, then switch

// Step 1: Spend 18 months building the new system
// Meanwhile, the old system keeps getting bug fixes and features
// The new system is always "almost done" but never catches up

// Step 2: The cutover night
async function cutover(): Promise<void> {
  // Pray that every feature works in the new system
  await dnsSwitch("app.example.com", "new-system.example.com");
  // If anything is wrong, you have two options:
  // 1. Roll back DNS (but the new system may have written data)
  // 2. Fix forward under extreme pressure at 2am
}

// Common outcome: "We discovered 47 undocumented business rules
// in the legacy system that the new system does not handle."
// Result: emergency rollback, 6 more months of development, morale collapse.
```

### GOOD: Strangler Fig — incremental migration with routing

```typescript
// ============================================
// ROUTING LAYER — the "strangler" facade
// ============================================

interface RouteConfig {
  path: string;
  target: "legacy" | "modern";
  percentage?: number; // For canary routing
}

// This can be an API gateway config, nginx rules, or application code
const routingTable: RouteConfig[] = [
  // Phase 1: User profile migrated to new system
  { path: "/api/users/profile*", target: "modern" },

  // Phase 2: Search migrated (canary at 20%)
  { path: "/api/search*", target: "modern", percentage: 20 },

  // Not yet migrated: everything else goes to legacy
  { path: "/api/*", target: "legacy" },
];

class StranglerProxy {
  constructor(
    private readonly routes: RouteConfig[],
    private readonly legacyUrl: string,
    private readonly modernUrl: string
  ) {}

  async handleRequest(req: IncomingRequest): Promise<Response> {
    const route = this.findMatchingRoute(req.path);
    const target = this.resolveTarget(route);

    if (target === "modern") {
      return this.proxyToModern(req);
    }
    return this.proxyToLegacy(req);
  }

  private resolveTarget(route: RouteConfig): "legacy" | "modern" {
    if (route.target === "legacy") return "legacy";

    // Canary routing: gradually increase traffic to modern
    if (route.percentage !== undefined) {
      return Math.random() * 100 < route.percentage ? "modern" : "legacy";
    }

    return "modern";
  }

  private findMatchingRoute(path: string): RouteConfig {
    return this.routes.find((r) => pathMatches(path, r.path))
      ?? { path: "*", target: "legacy" };
  }

  private async proxyToModern(req: IncomingRequest): Promise<Response> {
    try {
      return await fetch(`${this.modernUrl}${req.path}`, {
        method: req.method,
        headers: req.headers,
        body: req.body,
      });
    } catch (error) {
      // Fallback to legacy if modern fails — safety net
      console.error("Modern service failed, falling back to legacy", error);
      return this.proxyToLegacy(req);
    }
  }

  private async proxyToLegacy(req: IncomingRequest): Promise<Response> {
    return fetch(`${this.legacyUrl}${req.path}`, {
      method: req.method,
      headers: req.headers,
      body: req.body,
    });
  }
}

// ============================================
// MIGRATION STRATEGY — feature-by-feature
// ============================================

// Anti-corruption layer: translates between legacy and modern data models
class UserAntiCorruptionLayer {
  // Legacy system returns XML with different field names
  translateFromLegacy(legacyUser: LegacyUserXml): ModernUser {
    return {
      id: legacyUser.usr_id,
      email: legacyUser.email_addr,
      fullName: `${legacyUser.first_nm} ${legacyUser.last_nm}`,
      createdAt: new Date(legacyUser.create_dt),
      status: this.mapStatus(legacyUser.status_cd),
    };
  }

  private mapStatus(legacyStatus: string): UserStatus {
    const mapping: Record<string, UserStatus> = {
      "A": "active",
      "I": "inactive",
      "S": "suspended",
      "D": "deleted",
    };
    return mapping[legacyStatus] ?? "unknown";
  }
}

// Data synchronization during coexistence
class DataSyncService {
  constructor(
    private readonly legacyDb: LegacyDatabase,
    private readonly modernDb: ModernDatabase
  ) {}

  // During migration, write to both systems
  async syncUserUpdate(userId: string, changes: Partial<ModernUser>): Promise<void> {
    // Write to modern system (source of truth for migrated features)
    await this.modernDb.users.update(userId, changes);

    // Write to legacy system (for features not yet migrated)
    const legacyChanges = this.toLegacyFormat(changes);
    await this.legacyDb.updateUser(userId, legacyChanges);
  }

  private toLegacyFormat(changes: Partial<ModernUser>): Record<string, unknown> {
    const mapping: Record<string, string> = {
      email: "email_addr",
      fullName: "display_name",
    };
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(changes)) {
      result[mapping[key] ?? key] = value;
    }
    return result;
  }
}

// ============================================
// VERIFICATION — compare old and new systems
// ============================================

// Shadow traffic: send requests to both and compare responses
class ShadowVerifier {
  async verify(req: IncomingRequest): Promise<VerificationResult> {
    const [legacyResponse, modernResponse] = await Promise.all([
      this.callLegacy(req),
      this.callModern(req),
    ]);

    const differences = this.compareResponses(legacyResponse, modernResponse);

    if (differences.length > 0) {
      await this.reportDifferences(req, differences);
    }

    // Always return the legacy response — modern is just for verification
    return {
      response: legacyResponse,
      isConsistent: differences.length === 0,
      differences,
    };
  }
}
```

---

## Alternatives & Related Principles

| Approach | Relationship |
|---|---|
| **Big Bang Rewrite** | Replace everything at once. Highest risk, highest reward if it works. History suggests it usually does not work for large systems. |
| **Branch by Abstraction** | Introduce an abstraction layer within the codebase to allow old and new implementations to coexist. Works within a single deployment, while Strangler Fig works across deployments. |
| **Parallel Run** | Run both old and new systems simultaneously, compare outputs, and only switch when they match. More conservative than Strangler Fig — both systems process every request. |
| **Feature Flags** | Toggle between old and new implementations at runtime. Often used alongside Strangler Fig for the routing decisions. |
| **Anti-Corruption Layer (DDD)** | A translation layer between two bounded contexts. Essential in Strangler Fig migrations to prevent the new system from being polluted by legacy data models. |

---

## When NOT to Apply

- **The legacy system is small enough to rewrite quickly**: If the entire system can be rewritten in a sprint, the overhead of a proxy layer and dual maintenance is not worth it.
- **The legacy system has no clear seams**: If the monolith is so entangled that you cannot isolate a single feature, you may need to do internal refactoring (Branch by Abstraction) before you can strangle externally.
- **Data model incompatibility**: If the legacy and modern systems have fundamentally different data models that cannot coexist, the dual-write synchronization becomes the hardest part of the migration.
- **Regulatory constraints**: Some regulated environments require full system validation. Running two systems simultaneously may require certifying both.

---

## Tensions & Trade-offs

- **Dual maintenance**: During the coexistence phase, bugs and features may need to be implemented in both systems. This is a real cost.
- **Data consistency**: When both systems write to their own databases, keeping data in sync is challenging. Events, CDC, or dual-writes all have trade-offs.
- **Extended timeline**: Strangler Fig migrations can take years for large systems. Organizational patience is required.
- **Routing complexity**: The proxy/gateway layer becomes critical infrastructure. Its failure modes and performance characteristics matter.
- **Feature parity verification**: How do you know the new implementation matches the old one's behavior? Shadow traffic and comparison testing are essential but imperfect.

---

## Real-World Consequences

**Adherence example**: Shopify migrated their storefront rendering from a Ruby monolith to a distributed system over several years using the Strangler Fig pattern. Each storefront section (product pages, collections, checkout) was migrated independently. At no point was the platform unavailable or degraded. The migration enabled them to scale to handle Flash Sales and Black Friday traffic.

**Failure example**: The UK's Universal Credit system attempted a big bang replacement of the legacy benefits system. After several years and hundreds of millions of pounds, the project was partially rolled back and restarted with an incremental migration approach. The big bang rewrite had failed to account for thousands of edge cases in the 30-year-old legacy system.

---

## Key Quotes

> "The most important reason to consider a strangler fig application over a cut-over rewrite is reduced risk. A strangler fig can give value early and regularly, while a rewrite gives value only at the end." — Martin Fowler

> "Rewriting from scratch is the single worst strategic mistake that any software company can make." — Joel Spolsky (on the Netscape rewrite)

> "The strangler fig pattern succeeds because it turns a single high-risk decision into many low-risk decisions." — common paraphrase

---

## Further Reading

- Fowler, M. — [StranglerFigApplication](https://martinfowler.com/bliki/StranglerFigApplication.html) (2004)
- Newman, S. — *Monolith to Microservices* (2019), Chapter 3: "Splitting the Monolith"
- Spolsky, J. — [Things You Should Never Do, Part I](https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/) (2000)
- Fowler, M. — [BranchByAbstraction](https://martinfowler.com/bliki/BranchByAbstraction.html)
- Hodgson, P. — [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html) (companion pattern for routing decisions)
