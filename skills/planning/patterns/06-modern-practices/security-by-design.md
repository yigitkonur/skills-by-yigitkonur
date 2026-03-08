# Security by Design

**One-line summary:** Build security into the architecture from day one rather than bolting it on after the fact -- least privilege, defense in depth, zero trust, and shift-left security practices.

---

## Origin

The concept of "security by design" traces to Saltzer and Schroeder's seminal paper "The Protection of Information in Computer Systems" (1975), which introduced principles like least privilege, fail-safe defaults, and complete mediation. The OWASP Foundation (2001) systematized web application security. Google's BeyondCorp paper (2014) formalized zero trust networking. The term "shift-left security" emerged from the DevSecOps movement (2016+), advocating that security checks move earlier in the development lifecycle. The 2020 SolarWinds attack made supply chain security a mainstream concern.

---

## The Problem It Solves

Security as an afterthought produces systems where vulnerabilities are architectural -- they cannot be patched without redesigning core components. When security is a final review gate, it discovers problems too late: the database schema already stores passwords in plaintext, the API already trusts client-side input, the microservices already communicate without authentication. Retrofitting security into a running system is orders of magnitude more expensive than building it in, and the patches are invariably incomplete. The 2017 Equifax breach (unpatched Apache Struts) and the 2021 Log4Shell vulnerability demonstrated that even known vulnerabilities go unaddressed when security is treated as someone else's problem.

---

## The Principle Explained

**Least privilege** means every component -- every user, service, process, and token -- should have the minimum permissions necessary to perform its function, and no more. A database connection for a read-only API endpoint should have read-only database credentials. A Lambda function that writes to S3 should not have permissions to delete from DynamoDB. When a component is compromised, least privilege limits the blast radius.

**Defense in depth** layers multiple security controls so that no single failure is catastrophic. Input validation happens at the API gateway AND in the application logic AND in the database constraints. Authentication happens at the edge AND at each service boundary. Encryption protects data in transit AND at rest. Each layer assumes the layers above it have failed.

**Zero trust** replaces the traditional perimeter model ("inside the network is trusted") with the assumption that every request is potentially malicious, regardless of its origin. Every service-to-service call is authenticated and authorized. Network location grants no implicit trust. This model is essential in cloud environments where the "perimeter" is a fiction -- your services run on shared infrastructure, your employees work from home, and your APIs are called from the public internet.

---

## Code Examples

### BAD: Security as Afterthought

```typescript
// No input validation -- trusts client data
app.post("/api/users", async (req, res) => {
  // SQL injection vulnerability: raw string interpolation
  const query = `INSERT INTO users (name, email) VALUES ('${req.body.name}', '${req.body.email}')`;
  await db.query(query);

  // Stores password in plaintext
  await db.query(`UPDATE users SET password = '${req.body.password}' WHERE email = '${req.body.email}'`);

  // Returns too much information
  const user = await db.query(`SELECT * FROM users WHERE email = '${req.body.email}'`);
  res.json(user); // Leaks internal IDs, timestamps, and password hash
});

// No authentication on sensitive endpoint
app.delete("/api/users/:id", async (req, res) => {
  await db.query(`DELETE FROM users WHERE id = ${req.params.id}`);
  res.json({ success: true });
});

// Secrets hardcoded in source
const STRIPE_KEY = "sk_live_abc123def456";
const DB_PASSWORD = "admin123";
```

### GOOD: Security by Design

```typescript
import { z } from "zod";
import bcrypt from "bcrypt";
import { randomUUID } from "crypto";

// Input validation with strict schemas (defense in depth: application layer)
const CreateUserSchema = z.object({
  name: z.string().min(1).max(100).trim(),
  email: z.string().email().max(255).toLowerCase(),
  password: z.string().min(12).max(128),
});

// Parameterized queries prevent SQL injection (defense in depth: data layer)
async function createUser(input: z.infer<typeof CreateUserSchema>): Promise<PublicUser> {
  const passwordHash = await bcrypt.hash(input.password, 12);
  const id = randomUUID();

  await db.query(
    `INSERT INTO users (id, name, email, password_hash) VALUES ($1, $2, $3, $4)`,
    [id, input.name, input.email, passwordHash]
  );

  // Return only public fields -- never leak internal data
  return { id, name: input.name, email: input.email };
}

// Middleware: authentication + authorization (zero trust: verify every request)
function requireAuth(requiredPermission: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const token = req.headers.authorization?.replace("Bearer ", "");
    if (!token) {
      return res.status(401).json({ error: "Authentication required" });
    }

    try {
      const claims = await verifyJwt(token); // Verify signature and expiration
      const hasPermission = await checkPermission(claims.sub, requiredPermission);

      if (!hasPermission) {
        // Log the attempt for security monitoring
        auditLog.warn("Unauthorized access attempt", {
          userId: claims.sub,
          requiredPermission,
          resource: req.path,
        });
        return res.status(403).json({ error: "Insufficient permissions" });
      }

      req.authenticatedUser = claims;
      next();
    } catch {
      return res.status(401).json({ error: "Invalid token" });
    }
  };
}

// Route with full security stack
app.post(
  "/api/users",
  requireAuth("users:create"),  // Authentication + authorization
  rateLimit({ windowMs: 60000, max: 10 }), // Rate limiting
  async (req, res) => {
    // Input validation
    const parsed = CreateUserSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ errors: parsed.error.issues });
    }

    const user = await createUser(parsed.data);
    res.status(201).json(user);
  }
);

// Least privilege: delete requires specific permission, logs the action
app.delete(
  "/api/users/:id",
  requireAuth("users:delete"),
  async (req, res) => {
    const targetUserId = z.string().uuid().parse(req.params.id);

    auditLog.info("User deletion", {
      deletedBy: req.authenticatedUser.sub,
      targetUser: targetUserId,
    });

    await softDeleteUser(targetUserId); // Soft delete, not hard delete
    res.status(204).send();
  }
);

// Secrets from environment, never in code
const config = {
  stripeKey: process.env.STRIPE_SECRET_KEY!, // Loaded from secrets manager
  dbUrl: process.env.DATABASE_URL!,           // Injected at deploy time
  jwtSecret: process.env.JWT_SECRET!,         // Rotated regularly
};
```

### GOOD: Supply Chain Security

```typescript
// package.json: pin exact versions, audit regularly
{
  "dependencies": {
    "express": "4.18.2",       // Exact version, not "^4.18.2"
    "zod": "3.22.4",
    "bcrypt": "5.1.1"
  },
  "scripts": {
    "audit": "npm audit --audit-level=high",
    "check-deps": "npx depcheck",
    "lint:lockfile": "npx lockfile-lint --path package-lock.json --type npm --allowed-hosts npm"
  }
}

// CI pipeline step: fail on known vulnerabilities
// npm audit --audit-level=high || exit 1

// Use SBOM (Software Bill of Materials) generation
// npx @cyclonedx/cyclonedx-npm --output-file sbom.json
```

---

## Security Principles Reference

| Principle | Description | Example |
|---|---|---|
| **Least privilege** | Minimum permissions needed | Read-only DB creds for read endpoints |
| **Defense in depth** | Multiple layers of controls | Validation at API + app + DB levels |
| **Zero trust** | Never trust, always verify | mTLS between all services |
| **Fail-safe defaults** | Deny by default, allow explicitly | Default-deny firewall rules |
| **Complete mediation** | Check authorization on every access | Middleware on every route, not just some |
| **Open design** | Security not dependent on secrecy | Published algorithms, secret only in keys |
| **Separation of privilege** | Require multiple conditions for access | MFA, approval workflows |
| **Least common mechanism** | Minimize shared components | Separate DB per service |

---

## Alternatives & Related Approaches

| Approach | Philosophy | Risk |
|---|---|---|
| **Security as afterthought** | Build first, secure later | Architectural vulnerabilities, costly retrofitting |
| **Penetration testing only** | Find and fix vulnerabilities post-deployment | Catches symptoms, not root causes |
| **Compliance-driven security** | Meet regulatory checkboxes | Creates a false sense of security; compliance != security |
| **Bug bounty programs** | Crowdsource vulnerability discovery | Supplements but does not replace secure design |
| **WAF-only protection** | Rely on a Web Application Firewall | Bypassed by logic flaws; false sense of security |

---

## When NOT to Apply

- **Internal tools with no sensitive data.** A team dashboard showing build status does not need the same security rigor as a payment system. Apply proportional security.
- **Throwaway prototypes.** A hackathon demo should not spend hours on security hardening. But never deploy it to production without hardening first.
- **Over-securing public data.** A public API serving open-source package metadata does not need authentication. Rate limiting and input validation are sufficient.

---

## Tensions & Trade-offs

- **Security vs. developer experience:** Strict security policies (mandatory MFA, secrets rotation, strict CSP headers) create friction. Balance with tooling that makes the secure path the easy path.
- **Least privilege vs. operational agility:** Very fine-grained permissions slow down deployments and debugging. Start with reasonable defaults and tighten based on risk assessment.
- **Zero trust vs. performance:** Authenticating every service call adds latency. Use efficient mechanisms (mTLS, JWT with local validation) and cache authorization decisions where appropriate.
- **Supply chain security vs. velocity:** Pinning exact dependency versions prevents surprise updates but requires manual maintenance. Use automated tools like Dependabot or Renovate.

---

## Real-World Consequences

- **The Equifax breach (2017):** 147 million records exposed due to an unpatched Apache Struts vulnerability. Security was not integrated into the deployment pipeline.
- **SolarWinds (2020):** Supply chain attack that compromised 18,000 organizations. Attackers injected malicious code into the build pipeline.
- **Log4Shell (2021):** A critical vulnerability in Log4j affected millions of applications. Organizations with SBOM tracking could identify affected systems in hours; others took weeks.
- **Google's BeyondCorp:** Eliminated VPN-based access in favor of zero trust, enabling secure work-from-anywhere without a traditional network perimeter.

---

## Key Quotes

> "Security is a process, not a product." -- Bruce Schneier

> "The only truly secure system is one that is powered off, cast in a block of concrete, and sealed in a lead-lined room with armed guards." -- Gene Spafford

> "If you think technology can solve your security problems, then you don't understand the problems and you don't understand the technology." -- Bruce Schneier

> "Every program has at least one bug and can be shortened by at least one instruction -- from which, by induction, one can deduce that every program can be reduced to one instruction which doesn't work." -- Anonymous

---

## Further Reading

- "The Protection of Information in Computer Systems" by Saltzer and Schroeder (1975)
- OWASP Top 10 (owasp.org/www-project-top-ten/) -- updated regularly
- *The Web Application Hacker's Handbook* by Stuttard and Pinto (2011)
- Google BeyondCorp papers (research.google/pubs) -- zero trust architecture
- *Threat Modeling* by Adam Shostack (2014)
- *Building Secure and Reliable Systems* by Google SRE (O'Reilly, 2020)
