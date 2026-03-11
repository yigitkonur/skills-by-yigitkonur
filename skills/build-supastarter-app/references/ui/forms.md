# UI Forms

> Documents the shared form primitives in `packages/ui/components/form.tsx`. Consult this when building a new React Hook Form + Zod form in the web app.
>
> The pattern is deliberately standardized: `FormProvider` at the top, `FormField` for each controlled field, then `FormItem` / `FormLabel` / `FormControl` / `FormMessage` for accessible structure.

## Core Exports

```ts
const Form = FormProvider;
const FormField = (...) => <Controller {...props} />;
const FormItem = (...) => <div className="space-y-1.5" ... />;
const FormLabel = (...) => <Label htmlFor={formItemId} ... />;
const FormControl = (...) => <Slot id={formItemId} aria-invalid={!!error} ... />;
```

## Standard Usage Pattern

```tsx
<Form {...form}>
  <FormField
    control={form.control}
    name="email"
    render={({ field }) => (
      <FormItem>
        <FormLabel>Email</FormLabel>
        <FormControl><Input {...field} /></FormControl>
        <FormMessage />
      </FormItem>
    )}
  />
</Form>
```

## Why This Matters

The UI form primitives automatically connect:

- `htmlFor`
- generated element ids
- `aria-describedby`
- error styling
- validation-message rendering

That is why feature forms like login, signup, onboarding, and settings all follow the same structure.

---

**Related references:**
- `references/conventions/component-patterns.md` — Project-wide form usage pattern
- `references/ui/components.md` — Broader shared component library context
- `references/auth/login-flow.md` — Real auth form using these primitives
- `references/onboarding/onboarding-flow.md` — Multi-step form usage in onboarding
- `references/patterns/form-with-zod.md` — Form pattern reference
