# Chaos Engineering

**Proactively inject failures into production systems to build confidence in their resilience.**

---

## Origin / History

Chaos engineering was born at Netflix in 2010 when they migrated from data centers to AWS. The engineering team created Chaos Monkey — a tool that randomly terminated production EC2 instances — to force engineers to build services that could survive instance failures. In 2012, Netflix expanded the concept into the "Simian Army" (Chaos Gorilla for availability zone failures, Latency Monkey for network delays, etc.). In 2014, Netflix formalized the discipline in their "Principles of Chaos Engineering" paper. Casey Rosenthal and Nora Jones later published *Chaos Engineering: System Resiliency in Practice* (2020), establishing it as a formal engineering discipline.

## The Problem It Solves

Traditional testing verifies that systems work correctly under expected conditions. But distributed systems fail in unexpected, emergent ways: a network partition isolates one replica, a clock skew causes cache invalidation, a DNS TTL expires during a deployment, a disk fills up silently. These failures are not bugs in any individual component — they are properties of the system as a whole. You cannot write a unit test for "what happens when the connection pool exhausts at the same time as a garbage collection pause." The only way to know how your system behaves under failure is to fail it, deliberately, in a controlled manner.

## The Principle Explained

Chaos engineering follows a scientific method adapted for distributed systems:

**1. Define a steady state.** Identify the measurable indicators that your system is working: request success rate, latency percentile, throughput, error rate. This is your baseline.

**2. Hypothesize that steady state continues during failure.** Before injecting failure, state what you believe will happen: "If we kill 1 of 3 database replicas, the success rate will remain above 99.9% and P99 latency will stay below 500ms."

**3. Introduce real-world events.** Inject failures that actually happen in production: server crashes, network latency, disk full, dependency timeouts, certificate expiration, DNS failures, clock skew.

**4. Look for differences.** Compare actual behavior against the steady-state hypothesis. If the system held, your confidence increases. If it did not, you found a weakness before your users did.

The key philosophical shift is that chaos engineering is not about breaking things. It is about building confidence through empirical evidence. Each experiment either confirms your resilience or reveals a gap. Both outcomes are valuable.

**Game Days** are organized team events where engineers deliberately inject failures and observe the system's response in real time. They serve dual purposes: testing resilience and training incident response. Amazon, Google, and Netflix all run regular Game Days.

## Code Examples

### GOOD: Structured chaos experiment with steady-state verification

```typescript
interface SteadyStateMetric {
  name: string;
  query: () => Promise<number>;
  threshold: { min?: number; max?: number };
}

interface ChaosExperiment {
  name: string;
  hypothesis: string;
  steadyState: SteadyStateMetric[];
  inject: () => Promise<ChaosHandle>;
  durationMs: number;
  rollback: (handle: ChaosHandle) => Promise<void>;
}

interface ChaosHandle {
  id: string;
  injectedAt: Date;
  metadata: Record<string, unknown>;
}

interface ExperimentResult {
  experiment: string;
  hypothesis: string;
  passed: boolean;
  steadyStateBefore: Record<string, number>;
  steadyStateDuring: Record<string, number>;
  steadyStateAfter: Record<string, number>;
  violations: string[];
  duration: number;
}

async function runExperiment(experiment: ChaosExperiment): Promise<ExperimentResult> {
  const violations: string[] = [];

  // 1. Measure steady state BEFORE injection
  const before = await measureSteadyState(experiment.steadyState);
  console.log(`[${experiment.name}] Baseline metrics:`, before);

  // 2. Verify baseline is actually steady
  for (const metric of experiment.steadyState) {
    const value = before[metric.name];
    if (!isWithinThreshold(value, metric.threshold)) {
      throw new Error(
        `Aborting: baseline metric "${metric.name}" is already outside threshold (${value})`
      );
    }
  }

  // 3. Inject failure
  console.log(`[${experiment.name}] Injecting failure...`);
  const handle = await experiment.inject();

  try {
    // 4. Wait for the experiment duration, sampling metrics
    await sleep(experiment.durationMs);
    const during = await measureSteadyState(experiment.steadyState);
    console.log(`[${experiment.name}] Metrics during failure:`, during);

    // 5. Check hypothesis
    for (const metric of experiment.steadyState) {
      if (!isWithinThreshold(during[metric.name], metric.threshold)) {
        violations.push(
          `"${metric.name}" violated: ${during[metric.name]} outside [${metric.threshold.min ?? "-inf"}, ${metric.threshold.max ?? "inf"}]`
        );
      }
    }

    return {
      experiment: experiment.name,
      hypothesis: experiment.hypothesis,
      passed: violations.length === 0,
      steadyStateBefore: before,
      steadyStateDuring: during,
      steadyStateAfter: {}, // filled after rollback
      violations,
      duration: experiment.durationMs,
    };
  } finally {
    // 6. ALWAYS roll back — even if measurement fails
    console.log(`[${experiment.name}] Rolling back...`);
    await experiment.rollback(handle);
  }
}

// Concrete experiment: kill a service replica
const replicaFailureExperiment: ChaosExperiment = {
  name: "payment-service-replica-failure",
  hypothesis:
    "Killing 1 of 3 payment service replicas maintains >99% success rate and <1s P99 latency",
  steadyState: [
    {
      name: "success-rate",
      query: () => prometheus.query("rate(http_requests_total{status=~'2..'}[1m]) / rate(http_requests_total[1m])"),
      threshold: { min: 0.99 },
    },
    {
      name: "p99-latency-ms",
      query: () => prometheus.query("histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[1m])) * 1000"),
      threshold: { max: 1000 },
    },
  ],
  inject: async () => {
    const instance = await kubernetes.getRandomPod("payment-service");
    await kubernetes.deletePod(instance.name);
    return {
      id: crypto.randomUUID(),
      injectedAt: new Date(),
      metadata: { killedPod: instance.name },
    };
  },
  durationMs: 120_000, // observe for 2 minutes
  rollback: async () => {
    // Kubernetes will auto-reschedule the pod; just verify it came back
    await kubernetes.waitForDesiredReplicas("payment-service", 3, 60_000);
  },
};
```

### BAD: "Chaos" without scientific rigor

```typescript
// This is not chaos engineering. This is random destruction.
// No hypothesis, no steady-state measurement, no rollback plan.
async function doSomeChaos(): Promise<void> {
  // Randomly kill stuff in production on Friday at 4pm.
  // What could go wrong?
  const services = await kubernetes.listServices();
  const victim = services[Math.floor(Math.random() * services.length)];

  await kubernetes.scaleToZero(victim.name);

  console.log(`Killed ${victim.name}. Let's see what happens!`);

  // No measurement. No rollback. No hypothesis.
  // If something breaks, we'll find out from customer complaints on Monday.
}
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Traditional integration testing** | Early in development when the system is not yet in production |
| **Staging environment testing** | When you are not yet confident enough to run experiments in production |
| **Canary deployments** | For testing new code, not system resilience to infrastructure failures |
| **Load testing** | For capacity planning — how much traffic can the system handle? (Not the same as resilience testing) |
| **Game Days** | Structured team exercises that combine chaos experiments with incident response training |
| **Disaster recovery drills** | For validating backup/restore procedures and failover mechanisms |

Chaos engineering is complementary to all of these. It answers a question none of the others can: "Does our system survive unexpected failure in production?"

## When NOT to Apply

- **Systems without monitoring.** If you cannot measure steady state, you cannot run chaos experiments. Fix observability first.
- **Systems without resilience mechanisms.** If you know the system has no circuit breakers, no retries, no fallbacks — chaos experiments will just confirm what you already know. Build resilience first, then validate it.
- **Compliance-restricted environments** where injecting production failures violates regulatory requirements.
- **Single-instance systems** with no redundancy. Killing the only instance is an outage, not an experiment.
- **During active incidents.** Do not inject chaos when the system is already degraded.

## Tensions & Trade-offs

- **Blast radius control:** The entire value of chaos engineering depends on limiting the impact of experiments. Start small (one instance, one availability zone) and expand scope as confidence grows.
- **Production vs. staging:** Chaos engineering's value comes from testing real production conditions (real traffic, real data, real infrastructure). Staging environments miss emergent behaviors that only appear at scale. But production experiments require mature monitoring and rollback capabilities.
- **Cultural resistance:** "You want to break production on purpose?" is a common reaction. Chaos engineering requires organizational buy-in and a blameless culture.
- **Tool overhead:** Running chaos experiments requires infrastructure (experiment scheduler, metric collectors, rollback automation). For small teams, the overhead may outweigh the benefit.

## Real-World Consequences

Netflix's Chaos Monkey randomly terminates production instances during business hours. Engineers know this. As a result, every Netflix service is built to survive instance failures. This cultural forcing function is arguably more valuable than any individual experiment.

Amazon runs annual "Game Days" that simulate major infrastructure failures. During one famous Game Day, they simulated the loss of an entire AWS region. The exercise revealed that several internal services had hard-coded region-specific endpoints — a bug that could have caused a real outage.

Gremlin, a chaos engineering platform, reported that 60% of first-time chaos experiments reveal at least one unexpected system behavior. The median time to discover these issues through traditional testing or production incidents would be months.

## Further Reading

- [Principles of Chaos Engineering](https://principlesofchaos.org/)
- *Chaos Engineering* by Casey Rosenthal and Nora Jones (O'Reilly, 2020)
- [Netflix TechBlog: The Netflix Simian Army](https://netflixtechblog.com/the-netflix-simian-army-16e57fbab116)
- [Gremlin: Chaos Engineering Resources](https://www.gremlin.com/chaos-engineering/)
- [AWS GameDay](https://aws.amazon.com/gameday/)
