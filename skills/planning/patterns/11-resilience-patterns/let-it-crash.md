# Let It Crash

**Instead of defensive error handling at every level, let processes fail and rely on supervisors to restart them cleanly.**

---

## Origin / History

The "let it crash" philosophy originates from Erlang and the Open Telecom Platform (OTP), designed by Joe Armstrong at Ericsson in the 1980s for building telephone switches that required 99.9999999% uptime (nine nines — less than 31 milliseconds of downtime per year). Armstrong's key insight was counter-intuitive: instead of writing complex error-recovery code in every function, isolate each unit of work in a lightweight process and let a supervisor decide what to do when it fails. Erlang's BEAM virtual machine proved this approach at massive scale in telecom, and the philosophy has since influenced Akka (Scala/Java), Elixir/Phoenix, and modern actor-based systems.

## The Problem It Solves

Defensive programming creates three problems. First, error-handling code proliferates throughout the system, making the happy path hard to read and the error paths hard to test. Second, developers cannot anticipate every failure mode — the try/catch blocks they write handle known errors but silently corrupt state on unknown errors. Third, recovering from an error in-place often leaves the process in an inconsistent state: half-initialized data structures, leaked resources, corrupted caches. The process "recovered" from the error but is now running with garbage state.

## The Principle Explained

The let-it-crash philosophy separates the code that does work from the code that handles failure. Worker processes focus entirely on the happy path. They do not catch exceptions they cannot meaningfully handle. When something goes wrong — unexpected state, corrupted data, resource exhaustion — the process crashes. A clean crash releases all resources and destroys the corrupted state.

A **supervisor** monitors the worker. When the worker crashes, the supervisor decides what to do based on a **restart strategy**:

- **One-for-one:** Only restart the failed process. Other processes are unaffected. Use this when processes are independent.
- **One-for-all:** Restart all child processes when any one fails. Use this when processes have shared state and cannot function independently.
- **Rest-for-one:** Restart the failed process and all processes started after it. Use this when processes have a dependency ordering (B depends on A, so if A crashes, B must also restart).

The supervisor also tracks restart frequency. If a child crashes too often (e.g., 5 times in 60 seconds), the supervisor itself crashes, escalating to its parent supervisor. This creates a **supervision tree** — a hierarchy of supervisors that propagates failures upward until they reach a level that can handle them.

## Code Examples

### GOOD: Supervisor pattern adapted for TypeScript/Node.js

```typescript
type RestartStrategy = "one-for-one" | "one-for-all" | "rest-for-one";

interface ChildSpec {
  id: string;
  start: () => Promise<ManagedProcess>;
  restartable: boolean;
}

interface ManagedProcess {
  run(): Promise<void>;
  shutdown(): Promise<void>;
}

interface SupervisorOptions {
  strategy: RestartStrategy;
  maxRestarts: number;
  maxRestartWindowMs: number;
}

class Supervisor {
  private children: Map<string, { spec: ChildSpec; process: ManagedProcess | null }> = new Map();
  private restartTimestamps: number[] = [];
  private running = false;

  constructor(
    private readonly name: string,
    private readonly options: SupervisorOptions
  ) {}

  async startChildren(specs: ChildSpec[]): Promise<void> {
    this.running = true;
    for (const spec of specs) {
      const process = await spec.start();
      this.children.set(spec.id, { spec, process });
      this.monitor(spec.id, process);
    }
  }

  private monitor(childId: string, process: ManagedProcess): void {
    process.run().catch(async (error) => {
      if (!this.running) return;

      console.error(`[${this.name}] Child "${childId}" crashed:`, error.message);

      const child = this.children.get(childId);
      if (!child || !child.spec.restartable) {
        console.log(`[${this.name}] Child "${childId}" will not be restarted`);
        return;
      }

      if (!this.canRestart()) {
        console.error(
          `[${this.name}] Max restart intensity reached (${this.options.maxRestarts} in ${this.options.maxRestartWindowMs}ms). Supervisor shutting down.`
        );
        await this.shutdown();
        throw new SupervisorExhaustedError(this.name);
      }

      await this.applyStrategy(childId);
    });
  }

  private async applyStrategy(failedChildId: string): Promise<void> {
    switch (this.options.strategy) {
      case "one-for-one":
        await this.restartChild(failedChildId);
        break;

      case "one-for-all":
        await this.restartAllChildren();
        break;

      case "rest-for-one":
        await this.restartFromChild(failedChildId);
        break;
    }
  }

  private async restartChild(childId: string): Promise<void> {
    const child = this.children.get(childId);
    if (!child) return;

    this.restartTimestamps.push(Date.now());
    console.log(`[${this.name}] Restarting child "${childId}"`);

    try {
      if (child.process) await child.process.shutdown().catch(() => {});
    } catch { /* already crashed */ }

    const newProcess = await child.spec.start();
    child.process = newProcess;
    this.monitor(childId, newProcess);
  }

  private async restartAllChildren(): Promise<void> {
    for (const [id, child] of this.children) {
      try {
        if (child.process) await child.process.shutdown().catch(() => {});
      } catch { /* already crashed */ }
    }
    for (const [id, child] of this.children) {
      const newProcess = await child.spec.start();
      child.process = newProcess;
      this.monitor(id, newProcess);
    }
  }

  private async restartFromChild(failedId: string): Promise<void> {
    let found = false;
    for (const [id, child] of this.children) {
      if (id === failedId) found = true;
      if (found) await this.restartChild(id);
    }
  }

  private canRestart(): boolean {
    const now = Date.now();
    const windowStart = now - this.options.maxRestartWindowMs;
    this.restartTimestamps = this.restartTimestamps.filter((t) => t > windowStart);
    return this.restartTimestamps.length < this.options.maxRestarts;
  }

  async shutdown(): Promise<void> {
    this.running = false;
    for (const [, child] of this.children) {
      try {
        if (child.process) await child.process.shutdown();
      } catch { /* best effort */ }
    }
  }
}

class SupervisorExhaustedError extends Error {
  constructor(supervisorName: string) {
    super(`Supervisor "${supervisorName}" exceeded max restart intensity`);
    this.name = "SupervisorExhaustedError";
  }
}

// Usage: message queue consumer with supervisor
const workerSupervisor = new Supervisor("queue-workers", {
  strategy: "one-for-one",
  maxRestarts: 5,
  maxRestartWindowMs: 60_000,
});

await workerSupervisor.startChildren([
  {
    id: "order-consumer",
    start: async () => new OrderQueueConsumer(orderQueue),
    restartable: true,
  },
  {
    id: "notification-consumer",
    start: async () => new NotificationQueueConsumer(notificationQueue),
    restartable: true,
  },
]);
```

### BAD: Defensive programming that swallows errors and corrupts state

```typescript
// This function tries to handle every error locally.
// It catches exceptions, logs them, and continues with corrupted state.
class OrderProcessor {
  private orderCache: Map<string, Order> = new Map();
  private balance = 0;

  async processOrder(orderId: string): Promise<void> {
    try {
      const order = await fetchOrder(orderId);
      this.orderCache.set(orderId, order);

      try {
        await chargeCustomer(order);
        this.balance += order.total;
      } catch (paymentError) {
        // Swallow the error. The order is now in the cache but unpaid.
        // The balance is wrong. State is corrupted.
        console.error("Payment failed, continuing...", paymentError);
      }

      try {
        await sendConfirmation(order);
      } catch (emailError) {
        // Customer paid but got no confirmation. Nobody knows.
        console.error("Email failed, continuing...", emailError);
      }
    } catch (error) {
      // Catch-all: the process continues running with unknown state.
      // Is the order in the cache? Is the balance correct? Nobody knows.
      console.error("Something went wrong, but we'll keep going", error);
    }
  }
}
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Defensive programming** | When crashes are unacceptable (embedded systems, single-process desktop apps) |
| **Exception handling with recovery** | When you CAN meaningfully recover (e.g., retry a transient error) |
| **Circuit breaker** | When repeated failures should stop the operation entirely, not restart it |
| **Graceful degradation** | When you want to continue with reduced functionality rather than restart |

Let-it-crash and circuit breakers complement each other. The circuit breaker prevents a process from crashing repeatedly on the same external failure. The supervisor restarts the process for internal failures.

## When NOT to Apply

- **Stateful processes with expensive initialization:** If restarting means reloading gigabytes of data or rebuilding an index, crash-and-restart is too expensive. Checkpoint and recover instead.
- **User-facing request handlers in synchronous systems:** Crashing a web server process drops all in-flight requests, not just the failing one. Use exception handling to isolate request failures.
- **When "crash" means data loss:** If the process holds un-persisted state (in-memory queue, uncommitted transaction), crashing loses data. Persist state before crashing.
- **Single-threaded environments without process isolation:** In a Node.js server, an uncaught exception kills the entire process and all connections. Use domains, worker threads, or cluster mode for isolation.

## Tensions & Trade-offs

- **Process isolation is the prerequisite.** Let-it-crash only works when crashes are cheap and isolated. Erlang's lightweight processes (2KB each) make this natural. OS processes are expensive. Threads share state. Without true isolation, a crash cascades.
- **Restart loops:** A bug that triggers on every message will crash the process repeatedly until the supervisor gives up. The supervisor's max-restart-intensity prevents infinite loops but means the process eventually stays down.
- **State recovery:** After a restart, the process starts fresh. Any accumulated in-memory state is gone. Systems using let-it-crash typically store critical state externally (database, ETS tables, Redis).
- **Debugging difficulty:** Crashes that trigger restarts can be hard to debug because the evidence (stack trace, in-memory state) disappears with the process. Structured logging and crash dumps become essential.

## Real-World Consequences

WhatsApp handled 2 million concurrent connections per server using Erlang/OTP's let-it-crash philosophy. Individual connection-handling processes crashed and restarted without affecting other connections. A team of 35 engineers served 450 million users.

Discord uses Elixir (built on Erlang's BEAM VM) for their real-time messaging infrastructure. When a process handling a user's session encounters corrupted state, it crashes and restarts. The user experiences a momentary reconnection — a better outcome than receiving corrupted messages.

Akka, the Scala/Java actor framework inspired by Erlang, brought supervisor trees to the JVM. LinkedIn, PayPal, and Walmart have used Akka to build resilient distributed systems using the let-it-crash model.

## Further Reading

- Joe Armstrong's PhD thesis: [Making Reliable Distributed Systems in the Presence of Software Errors](https://erlang.org/download/armstrong_thesis_2003.pdf)
- [Erlang/OTP Supervision Principles](https://www.erlang.org/doc/design_principles/sup_princ.html)
- *Programming Elixir* by Dave Thomas — Chapters on OTP supervisors
- [Akka Documentation: Supervision](https://doc.akka.io/docs/akka/current/general/supervision.html)
