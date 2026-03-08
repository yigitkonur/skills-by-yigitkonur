# Not Invented Here (NIH)

## Origin

The phrase predates software engineering, appearing in business and manufacturing contexts from the mid-20th century. In software, it was formalized as an anti-pattern in the 1990s and discussed extensively by Joel Spolsky in "In Defense of Not-Invented-Here Syndrome" (2001), which unusually argues that NIH is sometimes correct.

## Explanation

Not Invented Here is the tendency to reject external solutions (libraries, frameworks, services, standards) in favor of building your own, motivated by:

1. **Distrust:** "Their code might have bugs" (yours does too)
2. **Pride:** "We can do it better" (maybe, but at what cost?)
3. **Control:** "We need to own it" (ownership has maintenance costs)
4. **Ignorance:** "I didn't know that existed" (not true NIH, but same result)
5. **Resume-driven development:** "Building our own X is more interesting"

The result: teams reinvent well-solved problems, diverting engineering effort from their core domain to infrastructure and plumbing.

## TypeScript Code Examples

### Bad: Reinventing a JSON Schema Validator

```typescript
// "We don't want to depend on an external validation library."
// Team builds their own validator from scratch.

type ValidationRule = {
  field: string;
  type: "string" | "number" | "boolean" | "array" | "object";
  required?: boolean;
  min?: number;
  max?: number;
  pattern?: string;
  // Missing: nested objects, unions, transforms, coercion, error messages,
  // custom validators, async validation, conditional rules...
};

function validate(data: unknown, rules: ValidationRule[]): string[] {
  const errors: string[] = [];
  if (typeof data !== "object" || data === null) {
    return ["Input must be an object"];
  }
  for (const rule of rules) {
    const value = (data as Record<string, unknown>)[rule.field];
    if (rule.required && (value === undefined || value === null)) {
      errors.push(`${rule.field} is required`);
      continue;
    }
    if (value !== undefined && typeof value !== rule.type) {
      errors.push(`${rule.field} must be ${rule.type}`);
    }
    // 200 more lines of half-implemented validation...
    // No edge cases handled. No tests. No documentation.
    // Took 3 weeks. Zod does this in 3 lines.
  }
  return errors;
}
```

### Good: Using an Established Library

```typescript
// Zod: zero dependencies, TypeScript-native, maintained by the community,
// tested by thousands of projects.

import { z } from "zod";

const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().min(13).max(150),
  role: z.enum(["admin", "user", "viewer"]),
  preferences: z.object({
    newsletter: z.boolean().default(false),
    theme: z.enum(["light", "dark"]).default("light"),
  }).optional(),
});

type CreateUserInput = z.infer<typeof CreateUserSchema>;

// Type-safe validation in 15 lines.
// Covers edge cases that would take months to handle manually.
// Battle-tested by 15,000+ projects on npm.
```

### When NIH IS Justified

```typescript
// Scenario: Your core business IS the thing you would otherwise outsource.

// If you are Stripe, you build your own payment processing.
// If you are Vercel, you build your own deployment infrastructure.
// If you are a logging company, you build your own log processing.

// Example: You are a real-time analytics company.
// Using a generic analytics library would be NIH-avoidance taken too far.

// Your custom analytics engine IS your product.
export class AnalyticsEngine {
  // Optimized for your specific access patterns
  // Handles your specific scale requirements
  // Contains your competitive advantage
  async ingest(events: ReadonlyArray<AnalyticsEvent>): Promise<void> {
    // Custom columnar storage format optimized for your query patterns
    // Custom indexing strategy for your data shape
    // Custom aggregation pipeline for your specific metrics
    // This is worth building because it IS the business.
  }
}

// But the REST framework, the database driver, the logging library,
// the JSON parser, the HTTP client — use existing solutions for those.
// They are not your competitive advantage.
```

## The Joel Spolsky Test

Joel Spolsky argued NIH is justified when the component is:
1. **Core to your business** — your competitive advantage
2. **Something you need deep control over** — performance, behavior, debugging
3. **Simple enough to maintain** — you can actually build and maintain it

If all three are true, building your own may be correct. If any is false, use an existing solution.

## Decision Matrix

| Factor | Use External | Build Your Own |
|---|---|---|
| Core business differentiator? | No | Yes |
| Well-maintained OSS exists? | Yes | No or poor quality |
| Team has domain expertise? | No | Yes |
| Long-term maintenance budget? | No | Yes |
| Need deep customization? | No | Yes |
| Time-to-market critical? | Yes | No |

## Alternatives and Related Concepts

- **Proudly Found Elsewhere (PFE):** The opposite attitude — actively seek and adopt external solutions.
- **Buy vs. Build analysis:** Formal decision framework for make/buy decisions.
- **Inner source:** Adopt open-source practices within the organization.
- **Thin wrappers:** Use external libraries but wrap them in a thin adapter for portability.

## When NOT to Apply (When NIH Accusation Is Wrong)

- **Core competency:** Amazon building their own cloud infrastructure is not NIH — it IS their business.
- **Unique requirements:** If no existing solution handles your specific constraints (real-time, embedded, extreme scale), building is justified.
- **Security-critical components:** Building your own auth layer when you are a security company is core competency, not NIH.
- **Vendor risk:** If the external solution is from a single vendor with lock-in risk, building may be strategic.
- **License incompatibility:** If the library's license conflicts with your business model, you must build your own.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Always use external | Fast development, proven solutions | Dependency risk, less control |
| Always build your own | Full control, deep understanding | Massive time investment, maintenance burden |
| Strategic NIH (build core, buy rest) | Best of both worlds | Requires honest assessment of "core" |
| Thin wrappers over external | Portability + speed | Wrapper maintenance overhead |

## Real-World Consequences

- **Google's NIH culture:** Google built their own version of almost everything: Borg (Kubernetes ancestor), Bigtable, Spanner, Angular, Go, Dart, Bazel. Justified by their scale and unique requirements — but also produced many abandoned projects.
- **Facebook's React:** Facebook needed a UI library that matched their specific needs. Existing options (jQuery, Backbone) did not fit. NIH was justified — React became an industry standard.
- **Not-justified NIH:** A startup building their own logging library instead of using Winston/Pino. Their competitive advantage is their product, not their log formatting.
- **npm ecosystem:** The opposite extreme — depending on hundreds of tiny packages (left-pad, is-odd) because building anything yourself is seen as NIH.

## The Pragmatic Middle Ground

```
1. Is this our core business?              → Build
2. Does a good external solution exist?    → Use it
3. Does the external solution fit 80%+?    → Use it, adapt the 20%
4. Does it fit less than 80%?              → Evaluate build cost vs. adaptation cost
5. Is the maintenance cost acceptable?     → Factor into both build and buy decisions
```

## Further Reading

- Spolsky, J. (2001). "In Defense of Not-Invented-Here Syndrome" — joelonsoftware.com
- Brown, W. et al. (1998). *AntiPatterns*
- Raymond, E.S. (2003). *The Art of Unix Programming* — on reuse and composition
- Wardley, S. (2016). "Wardley Mapping" — understanding what to build vs. buy based on evolution
