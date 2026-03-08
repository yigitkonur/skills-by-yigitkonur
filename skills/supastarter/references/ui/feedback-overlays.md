# Feedback and Overlays

> Covers the shared UI affordances used for loading, notifications, and overlays. Consult this when choosing between dialogs, toasts, skeletons, or spinners.

## Common primitives

- `Spinner` for in-button or inline loading states
- toast helpers for success/error feedback
- dialog/sheet components for overlays
- skeleton components for loading placeholders
- progress bar for wizard flows

## Grounded examples

- `packages/ui/components/button.tsx` prepends `Spinner` when `loading` is true
- `apps/web/modules/saas/onboarding/components/OnboardingForm.tsx` uses `Progress`
- settings and org forms use toast helpers for mutation feedback

## Practical rule

Choose the lightest-weight feedback primitive that matches the action:

- button spinner for immediate submission feedback
- toast for async mutation results
- dialog/sheet for blocking interaction or editing larger content

---

**Related references:**
- `references/ui/components.md` — Shared component inventory
- `references/onboarding/onboarding-flow.md` — Progress bar usage
- `references/settings/account-settings.md` — Toast-based form feedback
