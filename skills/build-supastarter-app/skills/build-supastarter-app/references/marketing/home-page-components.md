# Home Page Components

> Documents the major building blocks of the marketing landing page. Consult this when customizing the public homepage or matching existing marketing section patterns.

## Key files

- `apps/web/modules/marketing/home/components/Hero.tsx`
- `apps/web/modules/marketing/home/components/Features.tsx`
- `apps/web/modules/marketing/home/components/PricingSection.tsx`
- `apps/web/modules/marketing/home/components/ContactForm.tsx`
- `apps/web/modules/marketing/home/components/FaqSection.tsx`
- `apps/web/modules/marketing/home/components/Newsletter.tsx`

## Grounded notes

- **Hero** contains the main marketing headline and CTA cluster
- **Features** is a client component driven by a `featureTabs` configuration array
- **PricingSection** wraps pricing UI driven by the payments config

`apps/web/tests/home.spec.ts` asserts the home page hero heading when marketing is enabled, so homepage copy/layout changes should keep tests in mind.

---

**Related references:**
- `references/marketing/pages.md` — Marketing layout and shared chrome
- `references/marketing/content-collections.md` — MDX-backed public content
- `references/payments/plans-config.md` — Pricing data source
- `references/ui/components.md` — Shared UI component library
