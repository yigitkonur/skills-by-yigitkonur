# Respect Save-Data and Network Information Constraints

> **Context:** Performance & Prefetch | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Users on metered cellular data or slow 2G/3G connections incur financial cost and severe latency when websites prefetch speculatively. Astro's native prefetch engine detects `navigator.connection.saveData` and `navigator.connection.effectiveType`. Under constrained networks, Astro automatically throttles or downgrades prefetch strategies to `tap`, preserving user bandwidth.

## 2. How It Differs From Classic React / Next.js

Many custom React prefetch hooks bypass browser connection hints, downloading next-page JS bundles indiscriminately. Astro builds network condition checks directly into `astro:prefetch`. Overriding this with `{ ignoreSlowConnection: true }` should be reserved strictly for mission-critical conversion funnels.

## 3. Common Mistakes & Anti-Patterns

Bypassing connection safeguards with programmatic prefetching across arbitrary links.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/PromoModal.astro
---
<script>
  import { prefetch } from 'astro:prefetch';

  // Blindly forcing prefetch regardless of user's data-saver preference
  document.querySelectorAll('.promo-banner a').forEach((link) => {
    prefetch(link.getAttribute('href'), { ignoreSlowConnection: true });
  });
</script>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/PromoModal.astro
---
<script>
  import { prefetch } from 'astro:prefetch';

  // Respect user constraints; Astro defaults ignoreSlowConnection to false
  const checkoutBtn = document.getElementById('checkout-action');
  checkoutBtn?.addEventListener('pointerenter', () => {
    const target = checkoutBtn.dataset.href;
    if (target) {
      // Only bypass slow-connection checks for the single critical transaction step
      prefetch(target, { ignoreSlowConnection: false });
    }
  });
</script>
```

## 4. Verification & Audit

Verify your application code does not abuse `ignoreSlowConnection: true`:

```bash
grep -rn 'ignoreSlowConnection:\s*true' src/
```

In Chrome DevTools, open the **Network** tab, throttle throttling preset to "Slow 3G", toggle "Emulate Network Conditions -> Save-Data", and confirm that hovering over non-critical links does not initiate background transfers.
