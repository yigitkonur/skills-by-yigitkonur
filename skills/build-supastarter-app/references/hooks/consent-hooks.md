# Consent Hooks

> Documents the hook/context pair behind the cookie consent demo. Consult this when consuming consent state in client code.

## Source of truth

`ConsentProvider` owns the state and cookie writes. Components consume that state through the shared consent hook in `@shared/hooks/cookie-consent`.

## What consumers need

The consent layer exposes:

- whether the user has already consented
- an allow action
- a decline action

`ConsentBanner.tsx` is the canonical consumer.

---

**Related references:**
- `references/analytics/consent-flow.md` — End-to-end consent behavior
- `references/routing/providers-document.md` — Where the provider is mounted
- `references/ui/feedback-overlays.md` — Banner UI and action patterns
