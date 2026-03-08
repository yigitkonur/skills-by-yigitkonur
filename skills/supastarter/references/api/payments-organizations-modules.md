# Payments and Organizations Modules

> Covers the two most operationally important API modules after auth: billing flows under `payments` and organization helpers under `organizations`. Consult this when adding checkout behavior, customer portal access, purchase listings, slug generation, or signed logo-upload flows.

## Payments module

### Key files

- `packages/api/modules/payments/router.ts`
- `packages/api/modules/payments/procedures/create-checkout-link.ts`
- `packages/api/modules/payments/procedures/create-customer-portal-link.ts`
- `packages/api/modules/payments/procedures/list-purchases.ts`

### Router surface

```ts
// packages/api/modules/payments/router.ts
export const paymentsRouter = {
  createCheckoutLink,
  createCustomerPortalLink,
  listPurchases,
};
```

### Checkout link procedure

```ts
// packages/api/modules/payments/procedures/create-checkout-link.ts
export const createCheckoutLink = protectedProcedure
  .use(localeMiddleware)
  .route({
    method: "POST",
    path: "/payments/create-checkout-link",
    tags: ["Payments"],
    summary: "Create checkout link",
  })
  .input(
    z.object({
      type: z.enum(["one-time", "subscription"]),
      productId: z.string(),
      redirectUrl: z.string().optional(),
      organizationId: z.string().optional(),
    }),
  )
  .handler(async ({ input: { productId, redirectUrl, type, organizationId }, context: { user } }) => {
    const customerId = await getCustomerIdFromEntity(
      organizationId ? { organizationId } : { userId: user.id },
    );

    const plan = Object.entries(config.plans).find(
      ([_planId, plan]) =>
        "prices" in plan &&
        plan.prices?.find((price) => price.productId === productId),
    );

    if (!plan) {
      throw new ORPCError("NOT_FOUND");
    }

    const [_, planDetails] = plan;

    const price =
      "prices" in planDetails &&
      planDetails.prices?.find((price) => price.productId === productId);

    const organization = organizationId
      ? await getOrganizationById(organizationId)
      : undefined;

    const seats =
      organization && price && "seatBased" in price && price.seatBased
        ? organization.members.length
        : undefined;

    const checkoutLink = await createCheckoutLinkFn({
      type,
      productId,
      email: user.email,
      name: user.name ?? "",
      redirectUrl,
      ...(organizationId ? { organizationId } : { userId: user.id }),
      seats,
      customerId: customerId ?? undefined,
    });

    return { checkoutLink };
  });
```

### Other payments endpoints

- `POST /api/payments/create-customer-portal-link`
  - protected endpoint
  - input: `purchaseId`, optional `redirectUrl`
  - verifies purchase ownership or org-owner access before creating the portal URL
- `GET /api/payments/purchases`
  - protected endpoint
  - optional `organizationId`
  - returns the purchases array directly from `getPurchasesByOrganizationId(...)` or `getPurchasesByUserId(...)`

## Organizations module

### Key files

- `packages/api/modules/organizations/router.ts`
- `packages/api/modules/organizations/procedures/generate-organization-slug.ts`
- `packages/api/modules/organizations/procedures/create-logo-upload-url.ts`

### Router surface

```ts
// packages/api/modules/organizations/router.ts
export const organizationsRouter = {
  generateSlug: generateOrganizationSlug,
  createLogoUploadUrl,
};
```

### Slug generation procedure

```ts
// packages/api/modules/organizations/procedures/generate-organization-slug.ts
export const generateOrganizationSlug = publicProcedure
  .route({
    method: "GET",
    path: "/organizations/generate-slug",
    tags: ["Organizations"],
    summary: "Generate organization slug",
  })
  .input(
    z.object({
      name: z.string(),
    }),
  )
  .handler(async ({ input: { name } }) => {
    const baseSlug = slugify(name, {
      lowercase: true,
    });

    let slug = baseSlug;
    let hasAvailableSlug = false;

    for (let i = 0; i < 3; i++) {
      const existing = await getOrganizationBySlug(slug);

      if (!existing) {
        hasAvailableSlug = true;
        break;
      }

      slug = `${baseSlug}-${nanoid(5)}`;
    }

    if (!hasAvailableSlug) {
      throw new ORPCError("INTERNAL_SERVER_ERROR");
    }

    return { slug };
  });
```

### Logo upload URL procedure

```ts
// packages/api/modules/organizations/procedures/create-logo-upload-url.ts
export const createLogoUploadUrl = protectedProcedure
  .route({
    method: "POST",
    path: "/organizations/logo-upload-url",
    tags: ["Organizations"],
    summary: "Create logo upload URL",
  })
  .input(z.object({ organizationId: z.string() }))
  .handler(async ({ context: { user }, input: { organizationId } }) => {
    const organization = await getOrganizationById(organizationId);
    if (!organization) {
      throw new ORPCError("BAD_REQUEST");
    }

    const membership = await verifyOrganizationMembership(organizationId, user.id);
    if (!membership) {
      throw new ORPCError("FORBIDDEN");
    }

    const path = `${organizationId}.png`;
    const signedUploadUrl = await getSignedUploadUrl(path, { bucket: "avatars" });

    return { signedUploadUrl, path };
  });
```

## Why these modules matter

- `payments` shows the standard pattern for protected business endpoints with database reads, provider delegation, and ownership checks.
- `organizations` shows the split between a public helper (`generateSlug`) and a protected storage-backed helper (`createLogoUploadUrl`).
- Both modules stay thin by delegating core work to shared packages: `@repo/payments`, `@repo/database`, and `@repo/storage`.

---

**Related references:**
- `references/api/procedure-tiers.md` — Why these procedures use `protectedProcedure` or `publicProcedure`
- `references/payments/plans-config.md` — Plan definitions consumed during checkout-link creation
- `references/payments/customer-ids.md` — Customer ID lookup/persistence used by payments flows
- `references/payments/stripe-provider.md` — Provider-side checkout and billing portal behavior
- `references/storage/signed-urls.md` — Presigned upload URL behavior used by organization logo uploads
- `references/organizations/create-organization-form.md` — UI flow that consumes slug generation and logo upload support
