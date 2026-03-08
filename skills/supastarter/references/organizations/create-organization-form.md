# Create Organization Form

> Documents the standalone form used on `/new-organization` to create an org, set it active, and redirect into the new dashboard. Consult this when changing org creation UX or tracing how slug generation and post-create navigation work.

## Key files

- `apps/web/modules/saas/organizations/components/CreateOrganizationForm.tsx`
- `apps/web/modules/saas/organizations/lib/api.ts`

## Representative code

```ts
const onSubmit = form.handleSubmit(async ({ name }) => {
  const newOrganization = await createOrganizationMutation.mutateAsync({ name });
  await setActiveOrganization(newOrganization.slug);
  await queryClient.invalidateQueries({ queryKey: organizationListQueryKey });
  router.replace(`/app/${newOrganization.slug}`);
});
```

## Implementation notes

- The form validates only the name locally; slug generation happens through the organizations API flow.
- After creation, the new org is immediately set active and the organization list cache is invalidated.
- This form is used by the standalone `/new-organization` gate page and can also accept a prefilled default name.

---

**Related references:**
- `references/api/payments-organizations-modules.md` — Slug and logo-upload API utilities consumed by org flows
- `references/organizations/active-organization-context.md` — Active-org switching after creation
- `references/ui/forms.md` — Shared form pattern used by this component
