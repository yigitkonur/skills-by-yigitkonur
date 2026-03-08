# Progressive Delivery

**One-line summary:** Progressive delivery decouples deployment from release by gradually exposing changes to increasing subsets of users, using feature flags, canary releases, and blue-green deployments to reduce the blast radius of failures.

---

## Origin

The term "progressive delivery" was coined by James Governor of RedMonk (2018), building on continuous delivery practices. Feature flags trace back to Flickr's "flippers" system (2009). Martin Fowler described feature toggles in his bliki (2010). Netflix pioneered canary analysis at scale with their Spinnaker deployment platform (2015). The core insight: deploying code to production and releasing features to users are two separate decisions, and conflating them is the root cause of release anxiety.

---

## The Problem It Solves

Traditional "big bang" releases deploy all changes to all users simultaneously. If something breaks, 100% of users are affected. Rollback is an emergency operation that may involve database migrations, cache invalidation, and downstream coordination. Teams ship less frequently because each release is a high-risk event, which paradoxically makes each release riskier (more changes bundled together). Progressive delivery breaks this cycle: deploy constantly, release gradually, and automatically roll back if metrics degrade.

---

## The Principle Explained

**Feature flags** (feature toggles) are runtime switches that control which code paths are active. A new feature can be deployed to production but hidden behind a flag, visible only to internal users, beta testers, or a percentage of traffic. This separates the "deploy" moment (code is in production) from the "release" moment (users can see it). Flags also enable A/B testing, kill switches for misbehaving features, and trunk-based development (everyone works on main, incomplete features are flagged off).

**Canary releases** route a small percentage of traffic (typically 1-5%) to the new version while the rest continues on the old version. Automated canary analysis compares the canary's metrics (error rate, latency, CPU) against the baseline. If the canary is healthy after a defined period, traffic gradually shifts. If metrics degrade, the canary is automatically rolled back. The blast radius of a bad deploy is limited to the canary percentage.

**Blue-green deployments** maintain two identical production environments. "Blue" runs the current version; "green" runs the new version. After deploying to green and verifying it works (smoke tests, health checks), traffic is switched from blue to green. If green fails, switch back to blue instantly. The drawback is resource cost (double the infrastructure) and complexity around stateful components (databases, queues).

---

## Code Examples

### BAD: Big Bang Release

```typescript
// All changes deployed to all users at once
// No way to partially release or roll back a single feature

app.get("/api/dashboard", async (req, res) => {
  const user = req.authenticatedUser;

  // New analytics widget -- untested in production, affects everyone
  const analytics = await computeExpensiveAnalytics(user.id);

  // New recommendation engine -- might be slow, affects everyone
  const recommendations = await getRecommendations(user.id);

  // Redesigned layout -- might have accessibility issues, affects everyone
  res.json({
    analytics,
    recommendations,
    layoutVersion: "v2", // No way to revert without a full rollback
  });
});

// Deployment is all-or-nothing: if recommendations are slow,
// the only option is to rollback everything, including the
// analytics fix that was working fine.
```

### GOOD: Feature Flags for Gradual Rollout

```typescript
// Feature flag service: runtime control over feature visibility
interface FeatureFlagService {
  isEnabled(flagName: string, context: FlagContext): Promise<boolean>;
  getVariant(flagName: string, context: FlagContext): Promise<string>;
  getPercentage(flagName: string): Promise<number>;
}

interface FlagContext {
  readonly userId: string;
  readonly userTier?: string;
  readonly region?: string;
  readonly deviceType?: string;
}

// Feature flags in practice: decouple deploy from release
app.get("/api/dashboard", async (req, res) => {
  const user = req.authenticatedUser;
  const flagContext: FlagContext = {
    userId: user.id,
    userTier: user.tier,
    region: user.region,
  };

  // New analytics: deployed to prod, released to 10% of users
  const analytics = await flags.isEnabled("new-analytics-widget", flagContext)
    ? await computeNewAnalytics(user.id)
    : await computeLegacyAnalytics(user.id);

  // Recommendations: deployed to prod, released to internal users only
  const recommendations = await flags.isEnabled("recommendation-engine", flagContext)
    ? await getRecommendations(user.id)
    : [];

  // Layout variant: A/B test between v1 and v2
  const layoutVersion = await flags.getVariant("dashboard-layout", flagContext);

  res.json({ analytics, recommendations, layoutVersion });
});
```

### GOOD: Canary Deployment with Automated Analysis

```typescript
// Canary deployment configuration (Kubernetes-style)
interface CanaryDeployment {
  readonly name: string;
  readonly baseline: DeploymentRef;
  readonly canary: DeploymentRef;
  readonly analysis: CanaryAnalysis;
  readonly steps: readonly RolloutStep[];
}

interface CanaryAnalysis {
  readonly metrics: readonly CanaryMetric[];
  readonly evaluationInterval: string; // "5m"
  readonly failureThreshold: number;   // How many failed checks before rollback
}

interface CanaryMetric {
  readonly name: string;
  readonly query: string;              // Prometheus query
  readonly thresholdRange: { min: number; max: number };
}

type RolloutStep =
  | { readonly action: "setWeight"; readonly weight: number }
  | { readonly action: "pause"; readonly duration: string }
  | { readonly action: "analyze" };

// Example canary rollout definition
const orderServiceCanary: CanaryDeployment = {
  name: "order-service-v2.1.0",
  baseline: { deployment: "order-service", version: "v2.0.0" },
  canary: { deployment: "order-service-canary", version: "v2.1.0" },
  analysis: {
    metrics: [
      {
        name: "error-rate",
        query: 'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])',
        thresholdRange: { min: 0, max: 0.01 }, // Less than 1% errors
      },
      {
        name: "p99-latency",
        query: 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))',
        thresholdRange: { min: 0, max: 0.5 }, // Under 500ms p99
      },
      {
        name: "cpu-usage",
        query: 'rate(container_cpu_usage_seconds_total[5m])',
        thresholdRange: { min: 0, max: 0.8 }, // Under 80% CPU
      },
    ],
    evaluationInterval: "5m",
    failureThreshold: 3,
  },
  steps: [
    { action: "setWeight", weight: 5 },    // 5% to canary
    { action: "pause", duration: "10m" },   // Observe for 10 minutes
    { action: "analyze" },                   // Run metric analysis
    { action: "setWeight", weight: 25 },    // Scale to 25%
    { action: "pause", duration: "10m" },
    { action: "analyze" },
    { action: "setWeight", weight: 50 },    // Scale to 50%
    { action: "pause", duration: "15m" },
    { action: "analyze" },
    { action: "setWeight", weight: 100 },   // Full rollout
  ],
};

// Automated canary analysis function
async function evaluateCanary(
  config: CanaryDeployment
): Promise<"pass" | "fail"> {
  let failureCount = 0;

  for (const metric of config.analysis.metrics) {
    const canaryValue = await queryPrometheus(metric.query, "canary");
    const baselineValue = await queryPrometheus(metric.query, "baseline");

    const isWithinThreshold =
      canaryValue >= metric.thresholdRange.min &&
      canaryValue <= metric.thresholdRange.max;

    if (!isWithinThreshold) {
      logger.warn("Canary metric out of range", {
        metric: metric.name,
        canaryValue,
        baselineValue,
        threshold: metric.thresholdRange,
      });
      failureCount++;
    }
  }

  return failureCount >= config.analysis.failureThreshold ? "fail" : "pass";
}
```

---

## Progressive Delivery Techniques

| Technique | Mechanism | Best For |
|---|---|---|
| **Feature flags** | Code-level toggles | Partial features, A/B tests, kill switches |
| **Canary releases** | Traffic splitting by percentage | Backend changes, API updates |
| **Blue-green deployments** | Two parallel environments | Zero-downtime deployments |
| **Dark launches** | Run new code path, discard results | Performance validation without user impact |
| **Ring-based deployment** | Deploy to rings (internal -> beta -> GA) | Large organizations with varied risk tolerance |
| **A/B testing** | Statistical comparison of variants | UI changes, pricing experiments |

---

## Alternatives & Related Approaches

| Approach | Philosophy | Risk |
|---|---|---|
| **Big bang releases** | Deploy everything to everyone at once | Maximum blast radius |
| **Release trains** | Scheduled releases on a cadence | Batching increases risk per release |
| **Continuous deployment to all** | Every merge goes to all users immediately | No safety net for unexpected failures |
| **Branch-based development** | Long-lived feature branches merged at release time | Merge conflicts, integration pain |

---

## When NOT to Apply

- **Database schema migrations.** You cannot canary a schema change that affects all queries. Use expand-and-contract migrations instead.
- **Trivially small changes.** A typo fix does not need a canary analysis pipeline. Ship it directly.
- **When flag cleanup is not practiced.** Feature flags that are never removed become technical debt. Every flag should have an expiration date and an owner.
- **Stateful changes that require global consistency.** If all users must see the same data format, partial rollout creates inconsistency.

---

## Tensions & Trade-offs

- **Feature flag complexity:** Flags create combinatorial state. If you have 10 flags, you have 1,024 possible configurations. Not all are tested.
- **Testing burden:** Each flag variant needs testing. Long-lived flags multiply the test matrix.
- **Infrastructure cost:** Blue-green requires double the resources. Canary requires traffic splitting infrastructure.
- **Flag cleanup discipline:** Stale flags are technical debt. Build expiration into your flag management process.

---

## Real-World Consequences

- **Facebook** deploys code to production thousands of times per day using feature flags (Gatekeeper system), testing changes on employee accounts before any external user sees them.
- **GitHub** uses feature flags for all major features, enabling staff engineers to deploy incomplete features to production daily without affecting users.
- **Knight Capital (2012)** lost $440 million in 45 minutes due to a deployment that activated old code on some servers but not others. A proper canary deployment would have caught the anomalous trading behavior within minutes.

---

## Key Quotes

> "Progressive delivery is continuous delivery with fine-grained control over the blast radius." -- James Governor

> "Deployment is not the same as release. Deploy continuously. Release deliberately." -- Dave Farley

> "If it hurts, do it more frequently, and bring the pain forward." -- Jez Humble

> "A feature flag is a technique that allows you to disable some functionality of your application, through configuration, without deploying new code." -- Martin Fowler

---

## Further Reading

- *Continuous Delivery* by Jez Humble and David Farley (2010)
- *Release It!* by Michael Nygard (2018, 2nd edition)
- "Feature Toggles" by Martin Fowler (martinfowler.com, 2017)
- Flagger documentation (flagger.app) -- Kubernetes-native progressive delivery
- LaunchDarkly blog (launchdarkly.com/blog) -- Feature management patterns
