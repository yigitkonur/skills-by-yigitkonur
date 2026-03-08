# Deep Modules

**One-line summary:** A well-designed module provides powerful functionality behind a simple interface -- it is "deep," hiding complexity rather than exposing it.

---

## Origin

John Ousterhout introduced the deep module concept in *A Philosophy of Software Design* (2018, Yaknyam Press). Ousterhout, a Stanford professor and creator of the Tcl scripting language and the Raft consensus algorithm, argued that the software industry's obsession with small classes and thin interfaces has produced "shallow modules" that push complexity onto their callers rather than absorbing it. The book emerged from his CS 190 course at Stanford, where he observed students consistently struggling with unnecessary complexity caused by poor abstraction boundaries.

---

## The Problem It Solves

Shallow modules create what Ousterhout calls "complexity leakage." When a module's interface is nearly as complex as its implementation, callers gain almost nothing from the abstraction. They still need to understand the internals to use the module correctly. This manifests as: dozens of tiny classes that each do trivially little, forcing developers to navigate a maze of indirection; interfaces that require the caller to pass implementation details (configuration objects with 15 fields); and "pass-through methods" that add a layer of code without adding a layer of meaning. The cognitive load of the system increases with every shallow module added.

---

## The Principle Explained

A **deep module** has a simple interface relative to the functionality it provides. Think of the Unix file I/O system: five basic calls (`open`, `read`, `write`, `lseek`, `close`) hide an enormous amount of complexity -- file systems, disk drivers, caching, permissions, buffering. The interface is narrow; the implementation is deep. Callers do not need to know whether the file lives on SSD, spinning disk, or a network mount.

A **shallow module** is the opposite: its interface is complicated relative to what it does. A class with 10 methods that each wrap a single line of logic is shallow. It forces callers to learn 10 method signatures to accomplish what could have been expressed in 10 lines of inline code. The module exists as an abstraction boundary, but it does not actually abstract anything away.

**Information hiding** is the mechanism that makes modules deep. Each module should encapsulate design decisions that are likely to change -- data formats, algorithms, hardware details, business rules. When these decisions are hidden behind a stable interface, changes to them do not propagate through the system. Information leakage (the opposite) occurs when the same knowledge must exist in multiple places, creating coupling that makes the system rigid.

---

## Code Examples

### BAD: Shallow Module (complexity leakage)

```typescript
// Shallow: interface is as complex as the implementation
// Callers must understand internal details to use it correctly

class EmailConfig {
  smtpHost: string = "";
  smtpPort: number = 587;
  useTls: boolean = true;
  authMethod: "plain" | "login" | "oauth2" = "plain";
  connectionTimeout: number = 5000;
  retryCount: number = 3;
  retryBackoffMs: number = 1000;
}

class EmailConnectionManager {
  connect(config: EmailConfig): SmtpConnection { /* ... */ return {} as SmtpConnection; }
  disconnect(conn: SmtpConnection): void { /* ... */ }
}

class EmailBodyFormatter {
  formatPlainText(text: string): string { return text; }
  formatHtml(html: string): string { return html; }
  addAttachment(body: FormattedBody, file: Buffer, name: string): FormattedBody {
    return {} as FormattedBody;
  }
}

class EmailHeaderBuilder {
  setFrom(address: string): void { /* ... */ }
  setTo(addresses: string[]): void { /* ... */ }
  setSubject(subject: string): void { /* ... */ }
  setReplyTo(address: string): void { /* ... */ }
  build(): EmailHeaders { return {} as EmailHeaders; }
}

class EmailSender {
  send(conn: SmtpConnection, headers: EmailHeaders, body: FormattedBody): SendResult {
    return {} as SendResult;
  }
}

// Caller must orchestrate 5 classes and understand SMTP internals
// to send a single email. The abstraction hides nothing.
```

### GOOD: Deep Module (complexity absorbed)

```typescript
// Deep: simple interface, powerful functionality
// All SMTP, retry, formatting complexity is hidden

interface EmailMessage {
  readonly to: string | readonly string[];
  readonly subject: string;
  readonly body: string;
  readonly html?: string;
  readonly attachments?: readonly { name: string; content: Buffer }[];
  readonly replyTo?: string;
}

interface SendResult {
  readonly success: boolean;
  readonly messageId: string;
  readonly timestamp: Date;
}

class EmailService {
  // Simple constructor -- sensible defaults, override only what you need
  constructor(private readonly smtpUrl: string) {}

  // One method does everything: connects, formats, retries, sends, cleans up
  async send(message: EmailMessage): Promise<SendResult> {
    const connection = await this.connectWithRetry();
    try {
      const formatted = this.formatMessage(message);
      return await this.transmit(connection, formatted);
    } finally {
      await this.disconnect(connection);
    }
  }

  // All complexity is private -- callers never see it
  private async connectWithRetry(): Promise<InternalConnection> {
    // Handles TLS negotiation, auth method detection, retries with backoff
    // ... 80 lines of connection logic hidden from callers
    return {} as InternalConnection;
  }

  private formatMessage(message: EmailMessage): InternalMessage {
    // Handles MIME encoding, attachment encoding, header construction
    // ... 60 lines of formatting logic hidden from callers
    return {} as InternalMessage;
  }

  private async transmit(
    conn: InternalConnection,
    msg: InternalMessage
  ): Promise<SendResult> {
    // Handles send, retry on transient failure, result parsing
    return { success: true, messageId: "abc-123", timestamp: new Date() };
  }

  private async disconnect(conn: InternalConnection): Promise<void> {
    // Graceful disconnect with timeout
  }
}

// Caller code is trivial:
const email = new EmailService("smtps://user:pass@smtp.example.com:465");
await email.send({
  to: "recipient@example.com",
  subject: "Deep modules are powerful",
  body: "Simple interface, complex implementation.",
});
```

---

## Alternatives & Related Approaches

| Approach | Philosophy | Relationship to Deep Modules |
|---|---|---|
| **Microservices** | Many small services with network boundaries | Risk of shallow services that just proxy calls |
| **Unix pipes** | Small composable tools connected via text streams | Deep at the individual tool level (e.g., `grep` is deep) |
| **Clean Architecture layers** | Separate concerns into concentric rings | Complementary; each ring should be a deep module |
| **Facade pattern** | Wrap a complex subsystem with a simpler interface | Direct implementation of the deep module idea |
| **Thin wrapper libraries** | Minimal abstraction over a dependency | Deliberately shallow; useful only for decoupling, not simplification |

---

## When NOT to Apply

- **When the domain is inherently complex and callers need control.** A graphics rendering pipeline legitimately needs many knobs. Hiding them all behind a single `render()` call would cripple advanced users.
- **When building libraries for experts.** A cryptography library should expose algorithm choices rather than hiding them behind "just encrypt this." Security-sensitive defaults must be visible and auditable.
- **When composability matters more than encapsulation.** The Unix pipe philosophy thrives on shallow, composable tools. Depth is achieved by composition, not by individual module size.
- **When a module is genuinely simple.** Not everything needs to be deep. A `clamp(value, min, max)` function is shallow by nature, and that is fine.

---

## Tensions & Trade-offs

- **Deep modules vs. testability:** Very deep modules can be hard to unit test because they hide internal behavior. Use dependency injection to make internal collaborators swappable without exposing them in the public interface.
- **Deep modules vs. Clean Code's small classes:** Martin advocates many small classes; Ousterhout advocates fewer, deeper ones. The resolution is that "small" should mean "small interface," not "small implementation."
- **Information hiding vs. debuggability:** When a deep module fails, its callers may struggle to diagnose the problem. Good error messages and observability (logging, metrics) mitigate this.
- **Depth vs. flexibility:** A very deep module makes assumptions about what callers need. If those assumptions are wrong, the module becomes a straitjacket. Design escape hatches for power users.

---

## Real-World Consequences

- The **Java I/O library** is a classic example of shallow modules. To read a line from a file, you must compose `FileInputStream`, `InputStreamReader`, and `BufferedReader` -- three layers that each do trivially little on their own.
- The **Go `net/http` package** is a deep module. `http.ListenAndServe(":8080", handler)` hides TCP socket management, HTTP parsing, connection pooling, and keep-alive handling behind a single function call.
- **AWS S3's API** is deep: `putObject` and `getObject` hide distributed storage, replication, consistency, and fault tolerance behind a key-value interface.

---

## Key Quotes

> "The best modules are those whose interfaces are much simpler than their implementations." -- John Ousterhout

> "Shallow modules don't help much in the battle against complexity, because the benefit they provide (not having to learn about how they work internally) is negated by the cost of learning and using their interfaces." -- John Ousterhout

> "The most important technique for achieving deep modules is information hiding." -- John Ousterhout

> "If a system has simple abstractions and deep implementations, then it is probably well-designed." -- John Ousterhout

---

## Further Reading

- *A Philosophy of Software Design* by John Ousterhout (2018, 2nd edition 2021)
- "On the Criteria To Be Used in Decomposing Systems into Modules" by David Parnas (1972) -- the foundational paper on information hiding
- *Design Patterns* by Gamma, Helm, Johnson, Vlissides (1994) -- Facade pattern as a deep module technique
- John Ousterhout's Stanford CS 190 lecture videos (available on YouTube)
