# Graceful Degradation

**When a component fails, deliver reduced functionality instead of a complete outage.**

---

## Origin / History

Graceful degradation originated in hardware engineering and fault-tolerant computing, where systems like the Space Shuttle's flight computers were designed to continue operating with reduced capability after component failures. In web engineering, the concept gained prominence through Netflix's approach to resilience in the early 2010s. Their Hystrix library included fallback mechanisms as a first-class concept: when a service call failed, the system could return a cached response, a default value, or a simplified version of the feature. The philosophy was simple — a Netflix homepage with stale recommendations is infinitely better than an error page.

## The Problem It Solves

Modern applications are composed of many services and features. A product page might depend on the product catalog, pricing service, recommendation engine, review aggregator, inventory checker, and image CDN. If any single dependency is required for the page to load, the system's availability is the product of all dependency availabilities. Six services at 99.9% each yield 99.4% overall — nearly 5 hours of downtime per year from "reliable" services.

## The Principle Explained

Graceful degradation inverts the default. Instead of requiring all dependencies to serve a page, you classify each feature by criticality. The product name and price are essential. Recommendations, reviews, and "customers also bought" are nice-to-have. When a non-essential service fails, you hide that section, show cached data, or display a static placeholder. The user gets a slightly diminished experience but never an error page.

This requires a deliberate architectural choice: every feature rendered on a page must have a defined fallback behavior. This fallback might be a cached response (serve the last known good data), a static default (show a generic "popular products" section), a simplified alternative (show just product names instead of full cards with images), or simply hiding the section entirely.

The Netflix philosophy takes this further: they test degradation continuously. Chaos engineering (see `chaos-engineering.md`) deliberately kills services in production to verify that fallbacks work. If a fallback has never been triggered, you cannot trust it to work when you need it.

## Code Examples

### GOOD: Feature-level fallbacks with criticality classification

```typescript
type FeatureCriticality = "critical" | "important" | "optional";

interface FeatureResult<T> {
  data: T | null;
  source: "live" | "cache" | "fallback" | "hidden";
  degraded: boolean;
}

async function withDegradation<T>(
  featureName: string,
  criticality: FeatureCriticality,
  primary: () => Promise<T>,
  fallbacks: {
    cached?: () => Promise<T | null>;
    static?: () => T;
  }
): Promise<FeatureResult<T>> {
  // Try primary source
  try {
    const data = await primary();
    return { data, source: "live", degraded: false };
  } catch (primaryError) {
    metrics.increment(`feature.${featureName}.primary_failed`);

    // Try cache fallback
    if (fallbacks.cached) {
      try {
        const cached = await fallbacks.cached();
        if (cached !== null) {
          metrics.increment(`feature.${featureName}.served_from_cache`);
          return { data: cached, source: "cache", degraded: true };
        }
      } catch {
        // Cache itself failed — continue to next fallback
      }
    }

    // Try static fallback
    if (fallbacks.static) {
      metrics.increment(`feature.${featureName}.served_static`);
      return { data: fallbacks.static(), source: "fallback", degraded: true };
    }

    // No fallback available
    if (criticality === "critical") {
      throw primaryError; // Critical features MUST succeed
    }

    metrics.increment(`feature.${featureName}.hidden`);
    return { data: null, source: "hidden", degraded: true };
  }
}

// Building a product page with graceful degradation
async function buildProductPage(productId: string): Promise<ProductPage> {
  const [product, recommendations, reviews, inventory] = await Promise.all([
    // CRITICAL: must succeed or the page cannot render
    withDegradation("product-details", "critical",
      () => productService.getProduct(productId),
      { cached: () => productCache.get(productId) }
    ),

    // OPTIONAL: show fallback or hide entirely
    withDegradation("recommendations", "optional",
      () => recService.getForProduct(productId),
      {
        cached: () => recCache.get(productId),
        static: () => getPopularProducts(),
      }
    ),

    // IMPORTANT: degrade to summary if full reviews unavailable
    withDegradation("reviews", "important",
      () => reviewService.getReviews(productId),
      {
        cached: () => reviewCache.get(productId),
        static: () => ({ averageRating: null, count: 0, reviews: [] }),
      }
    ),

    // OPTIONAL: hide stock info rather than fail
    withDegradation("inventory", "optional",
      () => inventoryService.checkStock(productId),
      { static: () => ({ available: true, message: "Check availability at checkout" }) }
    ),
  ]);

  if (!product.data) {
    throw new ProductNotFoundError(productId); // Critical failure — no fallback
  }

  return {
    product: product.data,
    recommendations: recommendations.data ?? [],
    reviews: reviews.data ?? { averageRating: null, count: 0, reviews: [] },
    inventory: inventory.data,
    degraded: [product, recommendations, reviews, inventory].some((r) => r.degraded),
  };
}
```

### BAD: All-or-nothing rendering — one failure kills the page

```typescript
// If ANY service call fails, the entire page returns 500.
// The recommendation engine being slow means users cannot even
// see the product they want to buy.
async function buildProductPage(productId: string): Promise<ProductPage> {
  const product = await productService.getProduct(productId);
  const recommendations = await recService.getForProduct(productId);
  const reviews = await reviewService.getReviews(productId);
  const inventory = await inventoryService.checkStock(productId);

  return {
    product,
    recommendations,
    reviews,
    inventory,
    degraded: false,
  };
}
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Fail fast** | When partial results are dangerous or misleading (financial calculations, safety-critical systems) |
| **Let it crash (Erlang-style)** | When a supervisor can restart the failed component quickly enough that users do not notice |
| **Static fallback pages** | When the entire application is down, serve a static HTML page from a CDN (zero-dependency fallback) |
| **Feature flags** | Proactively disable features before they fail, rather than reacting to failures |

Graceful degradation and feature flags are natural partners. A feature flag can disable a feature manually (planned degradation), while the degradation framework handles automatic fallback during unplanned failures.

## When NOT to Apply

- **Financial transactions:** A payment page that hides the "total amount" because the pricing service is down is worse than an error page. Users should know exactly what they are paying.
- **Safety-critical systems:** An autopilot that "degrades gracefully" by ignoring altitude data is catastrophic. Fail loudly.
- **Data integrity operations:** Silently writing incomplete records because one data source is unavailable creates data quality nightmares.
- **When the fallback is misleading:** Showing stale inventory ("In Stock") when the inventory service is down can lead to overselling. Sometimes "unavailable" is the honest and correct response.

## Tensions & Trade-offs

- **Fallback maintenance cost:** Every fallback path is code that must be written, tested, and maintained. Untested fallbacks are the most dangerous code in the system — they only run during emergencies, exactly when reliability matters most.
- **Stale data risks:** Cached fallbacks can serve data that is minutes, hours, or days old. Users might make decisions based on outdated information.
- **Complexity creep:** A system with 20 features, each with 3 fallback layers, has 60 code paths. Testing all combinations is impractical.
- **Silent failures:** If degradation is too seamless, operators may not notice that a service has been down for hours. Monitoring must distinguish between live and degraded responses.

## Real-World Consequences

Netflix builds every UI component with a fallback. When their personalization service goes down, the homepage shows generic content ("Popular on Netflix") instead of personalized rows. Users may not even notice. This philosophy — combined with chaos engineering to test fallbacks regularly — is why Netflix maintains 99.99%+ perceived availability despite running hundreds of microservices.

Amazon's retail site is famous for loading product pages in fragments. If the review widget fails, the rest of the page renders normally. The review section shows a "Reviews temporarily unavailable" placeholder. This is graceful degradation at the UI component level.

## Further Reading

- [Netflix TechBlog: Making the Netflix API More Resilient](https://netflixtechblog.com/making-the-netflix-api-more-resilient-a8ec62159c2d)
- [Microsoft: Compensating Transactions](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction)
- *Release It!* by Michael Nygard — Chapter 4: Stability Anti-patterns
- [Google SRE Book: Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)
