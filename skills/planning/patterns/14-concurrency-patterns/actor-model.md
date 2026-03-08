# Actor Model

**Concurrency through isolated actors that communicate exclusively via asynchronous message passing. No shared state, no locks, no data races.**

---

## Origin / History

The Actor Model was formalized by Carl Hewitt, Peter Bishop, and Richard Steiger in 1973 at MIT. It was a response to the difficulty of reasoning about concurrent systems with shared mutable state. The model defines three primitives: an actor can (1) send messages to other actors, (2) create new actors, and (3) define how to handle the next message it receives.

Erlang (Joe Armstrong, 1986) built an entire programming language and runtime around the actor model, proving it could power telecom systems with 99.9999999% uptime (nine nines). The Akka framework (2009) brought actors to the JVM. Microsoft's Orleans (2015) introduced "virtual actors" — actors that are automatically activated and deactivated, simplifying distributed systems. In JavaScript, Web Workers and Node.js worker threads implement actor-like patterns, and libraries like Nact bring actor semantics to Node.js.

---

## The Problem It Solves

Shared mutable state with locks is the traditional approach to concurrency, and it is extraordinarily difficult to get right. Locks must be acquired in consistent order (or you get deadlocks), held for minimal duration (or you get contention), and never forgotten (or you get data races). As systems grow, the number of possible interleavings grows combinatorially, making testing inadequate and reasoning impossible.

The actor model eliminates shared state entirely. Each actor owns its state privately. Other actors cannot read or write it — they can only send messages. Because an actor processes one message at a time, its internal state transitions are sequential and deterministic. Concurrency exists between actors, but within each actor, the world is simple.

---

## The Principle Explained

An actor is a lightweight, isolated unit of computation with three capabilities: it maintains private state, it processes messages from its mailbox one at a time, and it can send messages to other actors (including creating new actors). The mailbox is a queue — messages arrive asynchronously and are processed in order.

The no-shared-state rule is absolute. If Actor A needs data from Actor B, it sends a request message. B processes the request and sends a response message. This message-passing discipline means actors can be distributed across machines transparently — the location of an actor does not affect how you communicate with it.

Supervision is the actor model's approach to fault tolerance. Instead of try/catch, actors are organized into supervision hierarchies. A parent actor supervises its children. When a child fails (throws an exception while processing a message), the supervisor decides the recovery strategy: restart the child, stop it, escalate the failure, or resume with the next message. This "let it crash" philosophy, pioneered by Erlang, turns error handling from a code-level concern into an architectural concern.

---

## Code Examples

### BAD: Shared mutable state with ad-hoc locking

```typescript
// Shared state — any code can read/write, races are inevitable
class BankAccount {
  private balance = 0;
  private locked = false;

  // Home-grown locking — fragile, error-prone
  private async acquireLock(): Promise<void> {
    while (this.locked) {
      await new Promise((resolve) => setTimeout(resolve, 10));
    }
    this.locked = true; // Race condition: two callers can both see locked=false
  }

  private releaseLock(): void {
    this.locked = false;
  }

  async transfer(amount: number, target: BankAccount): Promise<void> {
    await this.acquireLock();
    try {
      if (this.balance < amount) throw new Error("Insufficient funds");
      this.balance -= amount;
      // If this throws, balance is already decremented — inconsistent state!
      target.balance += amount;
    } finally {
      this.releaseLock();
    }
  }
}
```

### GOOD: Actor-based bank account — no shared state, message-driven

```typescript
// Message types — the actor's protocol
type AccountMessage =
  | { type: "DEPOSIT"; amount: number; replyTo: (result: DepositResult) => void }
  | { type: "WITHDRAW"; amount: number; replyTo: (result: WithdrawResult) => void }
  | { type: "GET_BALANCE"; replyTo: (balance: number) => void }
  | { type: "TRANSFER"; amount: number; targetActor: Actor<AccountMessage>;
      replyTo: (result: TransferResult) => void };

type DepositResult = { success: true; newBalance: number };
type WithdrawResult =
  | { success: true; newBalance: number }
  | { success: false; reason: "INSUFFICIENT_FUNDS" };
type TransferResult =
  | { success: true }
  | { success: false; reason: string };

// Minimal actor implementation
class Actor<T> {
  private mailbox: T[] = [];
  private processing = false;

  constructor(private handler: (message: T) => Promise<void> | void) {}

  send(message: T): void {
    this.mailbox.push(message);
    this.processNext();
  }

  private async processNext(): Promise<void> {
    if (this.processing || this.mailbox.length === 0) return;
    this.processing = true;
    const message = this.mailbox.shift()!;
    try {
      await this.handler(message);
    } catch (error) {
      console.error("Actor failed to process message:", error);
      // Supervision strategy would go here
    } finally {
      this.processing = false;
      this.processNext(); // Process next message in queue
    }
  }
}

// Account actor — private state, sequential message processing
function createAccountActor(initialBalance: number): Actor<AccountMessage> {
  let balance = initialBalance; // Private state — only this actor can access it

  return new Actor<AccountMessage>(async (message) => {
    switch (message.type) {
      case "DEPOSIT":
        balance += message.amount;
        message.replyTo({ success: true, newBalance: balance });
        break;

      case "WITHDRAW":
        if (balance < message.amount) {
          message.replyTo({ success: false, reason: "INSUFFICIENT_FUNDS" });
        } else {
          balance -= message.amount;
          message.replyTo({ success: true, newBalance: balance });
        }
        break;

      case "GET_BALANCE":
        message.replyTo(balance);
        break;

      case "TRANSFER":
        if (balance < message.amount) {
          message.replyTo({ success: false, reason: "Insufficient funds" });
        } else {
          balance -= message.amount;
          message.targetActor.send({
            type: "DEPOSIT",
            amount: message.amount,
            replyTo: () => {
              message.replyTo({ success: true });
            },
          });
        }
        break;
    }
  });
}
```

### Usage — actors communicate only via messages

```typescript
// Create actors
const aliceAccount = createAccountActor(1000);
const bobAccount = createAccountActor(500);

// Request/reply pattern
function askBalance(actor: Actor<AccountMessage>): Promise<number> {
  return new Promise((resolve) => {
    actor.send({ type: "GET_BALANCE", replyTo: resolve });
  });
}

function requestTransfer(
  from: Actor<AccountMessage>,
  to: Actor<AccountMessage>,
  amount: number,
): Promise<TransferResult> {
  return new Promise((resolve) => {
    from.send({
      type: "TRANSFER",
      amount,
      targetActor: to,
      replyTo: resolve,
    });
  });
}

// No locks, no shared state, no data races
const result = await requestTransfer(aliceAccount, bobAccount, 200);
```

### Supervision — let it crash, then recover

```typescript
type SupervisionStrategy = "restart" | "stop" | "escalate" | "resume";

class SupervisedActor<T> {
  private child: Actor<T> | null = null;

  constructor(
    private createChild: () => Actor<T>,
    private strategy: SupervisionStrategy = "restart",
    private maxRestarts: number = 3,
  ) {
    this.child = this.createChild();
  }

  private restartCount = 0;

  handleChildFailure(error: unknown): void {
    switch (this.strategy) {
      case "restart":
        if (this.restartCount < this.maxRestarts) {
          this.restartCount++;
          console.log(`Restarting child (attempt ${this.restartCount})`);
          this.child = this.createChild();
        } else {
          console.error("Max restarts exceeded, stopping child");
          this.child = null;
        }
        break;
      case "stop":
        this.child = null;
        break;
      case "escalate":
        throw error; // Let the parent supervisor handle it
      case "resume":
        break; // Ignore the error, continue with next message
    }
  }
}
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **Shared memory + locks (Mutex, Semaphore)** | Direct and familiar. But deadlocks, priority inversion, and lock contention are constant risks. Does not scale to distributed systems. |
| **CSP — Communicating Sequential Processes (Go channels)** | Similar to actors but focuses on channels rather than entities. Channels are typed, synchronous or buffered. More structured than actors but less suitable for distributed systems. |
| **Software Transactional Memory (STM)** | Treat memory operations like database transactions — atomicity, isolation via optimistic concurrency. Elegant but limited library support outside Haskell and Clojure. |
| **Immutability (avoid the problem)** | If all state is immutable, sharing is always safe. Eliminates the need for actors or locks. But some state must change — the question is where. |
| **Event Sourcing** | Append-only event log. Related to actors — each aggregate is like an actor processing events. More focused on persistence than concurrency. |

---

## When NOT to Apply

- **Simple request/response services**: A stateless REST API does not need actors. The request itself is the unit of concurrency, and the database handles state.
- **Single-threaded applications**: In Node.js, the main thread is single-threaded. Actors add overhead when there is no actual concurrency to manage (unless you need the mailbox/backpressure semantics).
- **Low-latency requirements**: Message passing adds latency compared to direct function calls. In microsecond-sensitive paths, the indirection is too costly.
- **Small teams without actor model experience**: The actor model requires a different way of thinking about state and communication. Without team expertise, it introduces confusion rather than clarity.

---

## Tensions & Trade-offs

- **Isolation vs. Efficiency**: Message passing copies or serializes data between actors. Shared memory is faster but sacrifices isolation. The trade-off is latency vs. safety.
- **Asynchronous messaging vs. Synchronous reasoning**: Actors communicate asynchronously, which makes reasoning about ordering harder. Request/reply patterns add complexity.
- **Supervision vs. Error handling**: "Let it crash" is powerful but requires careful design of supervision trees. A poorly designed supervision hierarchy restarts actors in loops.
- **Location transparency vs. Debugging**: Actors can be local or remote, which is powerful for distribution but makes debugging harder — you cannot set a breakpoint in a remote actor.

---

## Real-World Consequences

**Erlang/OTP and telecoms**: Ericsson's AXD301 ATM switch, written in Erlang with the actor model, achieved 99.9999999% uptime — 31 milliseconds of downtime per year. The "let it crash" philosophy with supervision trees meant that individual failures were recovered automatically without human intervention.

**Akka in financial systems**: Major banks use Akka actors for real-time trading systems. Each order is processed by an actor, and the system handles millions of orders per second with strong ordering guarantees per instrument — all without locks.

**Orleans and cloud gaming**: Microsoft's Orleans (virtual actors) powers Halo's backend services. Virtual actors are automatically placed on available servers, activated on demand, and deactivated when idle. This model handles millions of concurrent players without manual scaling or state management.

---

## Further Reading

- [Carl Hewitt — A Universal Modular Actor Formalism (1973)](https://en.wikipedia.org/wiki/Actor_model)
- [Joe Armstrong — Making Reliable Distributed Systems in the Presence of Software Errors (PhD Thesis, 2003)](https://erlang.org/download/armstrong_thesis_2003.pdf)
- [Akka Documentation — Actor Model](https://doc.akka.io/docs/akka/current/typed/guide/actors-intro.html)
- [Microsoft Orleans Documentation](https://learn.microsoft.com/en-us/dotnet/orleans/)
- [Bryan Hunter — The Actor Model (NDC Conference Talk)](https://www.youtube.com/watch?v=7erJ1DV_Tlo)
