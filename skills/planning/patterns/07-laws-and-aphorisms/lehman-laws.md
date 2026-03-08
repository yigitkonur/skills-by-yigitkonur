# Lehman's Laws of Software Evolution

## Origin

Meir M. "Manny" Lehman, from 1974 onward, refined through decades of empirical study at Imperial College London. Initially three laws, expanded to eight by 1996. Based on observations of IBM OS/360 and other long-lived systems.

## Explanation

Lehman's laws describe the inevitable forces acting on software systems that operate in the real world ("E-type" programs — embedded in and dependent on the real world). These are not guidelines — they are empirical observations about what happens to all long-lived software whether you want it to or not.

## The Eight Laws

### 1. Continuing Change (1974)

An E-type system must be continually adapted or it becomes progressively less satisfactory.

```typescript
// A payment gateway integration written in 2020
// that hasn't been updated:

// 2020: Works perfectly with Stripe API v2020-08-27
const charge = await stripe.charges.create({ amount, currency });

// 2022: Stripe deprecates Charges API, pushes PaymentIntents
// The code still works, but new features are unavailable

// 2024: Stripe drops support for old API version
// The system breaks. Not because the code changed, but because
// the world around it changed.
```

### 2. Increasing Complexity (1974)

As a system evolves, its complexity increases unless work is done to maintain or reduce it.

```typescript
// Version 1: Clean, simple
export function getPrice(item: Item): number {
  return item.basePrice;
}

// Version 5: After two years of "quick fixes"
export function getPrice(
  item: Item,
  user?: User,
  coupon?: Coupon,
  isBlackFriday?: boolean,
  legacyPricingMode?: boolean,    // Nobody knows what this does
  overrideRegion?: string,         // Added for "that one client"
  includeVat?: boolean,            // Default changed three times
): number {
  // 200 lines of nested conditionals
  // Complexity grew with every feature; nobody refactored
}
```

### 3. Self-Regulation (1974)

E-type system evolution processes are self-regulating. Growth metrics tend toward normal distributions.

### 4. Conservation of Organizational Stability (1978)

The average effective global activity rate in an evolving system is invariant over the product lifetime. Teams produce at a roughly constant rate regardless of resources.

### 5. Conservation of Familiarity (1978)

As a system evolves, all associated with it must maintain mastery of its content and behavior. Excessive growth rate degrades that mastery.

```typescript
// Adding 50 microservices in one quarter.
// No one understands the full system anymore.
// Incident response becomes guesswork.

// The law says: there is a natural limit to how fast
// you can evolve a system before the team loses comprehension.
```

### 6. Continuing Growth (1991)

The functional content of an E-type system must be continually increased to maintain user satisfaction.

### 7. Declining Quality (1996)

The quality of an E-type system will appear to be declining unless it is rigorously maintained and adapted.

### 8. Feedback System (1996)

E-type evolution processes are multi-level, multi-loop, multi-agent feedback systems and must be treated as such.

## TypeScript Code Examples

### Bad: Ignoring Increasing Complexity (Law 2)

```typescript
// auth.ts — evolved over 3 years without refactoring
export async function authenticate(req: Request): Promise<AuthResult> {
  // Legacy API key auth (2021)
  if (req.headers["x-api-key"]) {
    const key = req.headers["x-api-key"] as string;
    if (key.startsWith("legacy_")) {
      return legacyKeyAuth(key);
    }
    return modernKeyAuth(key);
  }
  // JWT auth (2022)
  if (req.headers.authorization?.startsWith("Bearer ")) {
    const token = req.headers.authorization.slice(7);
    if (token.includes(".")) { // JWT has dots
      return jwtAuth(token);
    }
    // Opaque token (2023)
    return opaqueTokenAuth(token);
  }
  // OAuth2 (2023)
  if (req.query.code) {
    return oauthAuth(req.query.code as string);
  }
  // mTLS (2024)
  if (req.socket && "getPeerCertificate" in req.socket) {
    return mtlsAuth(req);
  }
  // Each addition made the function worse. No one refactored.
  return { authenticated: false, error: "NO_AUTH_METHOD" };
}
```

### Good: Actively Managing Complexity Growth

```typescript
// Strategy pattern — each auth method is isolated, complexity is managed

interface AuthStrategy {
  readonly name: string;
  canHandle(req: Request): boolean;
  authenticate(req: Request): Promise<AuthResult>;
}

const strategies: ReadonlyArray<AuthStrategy> = [
  new MtlsAuthStrategy(),
  new JwtAuthStrategy(),
  new OpaqueTokenAuthStrategy(),
  new ApiKeyAuthStrategy(),
  new OAuthAuthStrategy(),
];

export async function authenticate(req: Request): Promise<AuthResult> {
  const strategy = strategies.find((s) => s.canHandle(req));
  if (!strategy) {
    return { authenticated: false, error: "NO_AUTH_METHOD" };
  }
  return strategy.authenticate(req);
}

// Adding a new auth method: implement AuthStrategy, add to array.
// Complexity grows linearly, not exponentially.
```

## Alternatives and Mitigations

- **Continuous refactoring:** Directly combats Law 2 (increasing complexity).
- **Deprecation policies:** Combat Law 1 (continuing change) by explicitly retiring old behaviors.
- **Architecture fitness functions:** Automated tests that detect complexity growth.
- **Evolutionary architecture:** Design systems that expect and accommodate change.

## When NOT to Apply

- **Short-lived systems:** Throwaway scripts and prototypes will not live long enough for Lehman's Laws to matter.
- **S-type programs (specification-driven):** Mathematical computations and algorithmic libraries are less subject to these laws because their requirements do not shift with the real world.
- **Static content:** A configuration file or a lookup table does not "evolve" in Lehman's sense.

## Trade-offs

| Response to Lehman's Laws | Benefit | Cost |
|---|---|---|
| Continuous refactoring | Manages complexity | Slows feature delivery in the short term |
| Planned obsolescence | Forces rewrites before decay | Throws away working code |
| Feature freezes for cleanup | Dedicated complexity reduction | Stakeholder impatience |
| Automated complexity metrics | Early warning system | Metrics can be gamed (Goodhart's Law) |

## Real-World Consequences

- **Windows Vista:** Increasing complexity (Law 2) made the OS unmaintainable; Microsoft eventually had to reset with Windows 7.
- **Firefox:** Declining quality perception (Law 7) as Chrome gained ground; required the Quantum rewrite to recover.
- **Linux kernel:** Actively managed under Lehman's Laws — continuous change, active complexity management, strict code review to maintain familiarity.
- **Every legacy system:** The codebase nobody wants to touch exists because Laws 1 and 2 were ignored.

## Further Reading

- Lehman, M. (1980). "Programs, Life Cycles, and Laws of Software Evolution"
- Lehman, M. & Ramil, J. (2001). "Rules and Tools for Software Evolution Planning and Management"
- Lehman, M. & Belady, L. (1985). *Program Evolution: Processes of Software Change*
- Herraiz, I. et al. (2013). "The Evolution of the Laws of Software Evolution"
- Ford, N. et al. (2017). *Building Evolutionary Architectures*
