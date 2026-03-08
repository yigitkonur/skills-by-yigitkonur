# Pattern: Form with Zod

> Reusable pattern for validated client forms. Consult this before writing a new settings, onboarding, or marketing form.

## Standard shape

1. Define a local Zod schema
2. Create a `useForm()` instance with `zodResolver()`
3. Bind fields through Shadcn `FormField`
4. Handle submit with an async callback
5. Surface loading and error/success feedback

## Real examples in this repo

- `ChangeEmailForm.tsx`
- `OnboardingStep1.tsx`
- `CreateOrganizationForm.tsx`

## Keep it simple

Small forms stay self-contained in the component file unless a shared API schema already exists.

---

**Related references:**
- `references/ui/forms.md` — Shared UI primitives used by the form layer
- `references/onboarding/onboarding-step-one.md` — Complete form example with avatar upload
- `references/organizations/create-organization-form.md` — Another production form pattern
