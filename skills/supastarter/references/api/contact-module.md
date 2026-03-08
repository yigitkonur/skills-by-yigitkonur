# Contact Module

> End-to-end example of a small public API module: shared Zod validation, locale-aware middleware, and a side effect through the mail package. Consult this when creating a public endpoint or when you want the cleanest example of Supastarter's oRPC module pattern.

## Key files

- `packages/api/modules/contact/router.ts`
- `packages/api/modules/contact/procedures/submit-contact-form.ts`
- `packages/api/modules/contact/types.ts`

## Router and procedure

```ts
// packages/api/modules/contact/router.ts
export const contactRouter = {
  submit: submitContactForm,
};
```

```ts
// packages/api/modules/contact/procedures/submit-contact-form.ts
export const submitContactForm = publicProcedure
  .route({
    method: "POST",
    path: "/contact",
    tags: ["Contact"],
    summary: "Submit contact form",
  })
  .input(contactFormSchema)
  .use(localeMiddleware)
  .handler(async ({ input: { email, name, message }, context: { locale } }) => {
    try {
      await sendEmail({
        to: config.contactFormTo,
        locale,
        subject: "Contact Form Submission",
        text: `Name: ${name}\n\nEmail: ${email}\n\nMessage: ${message}`,
      });
    } catch (error) {
      logger.error(error);
      throw new ORPCError("INTERNAL_SERVER_ERROR");
    }
  });
```

## Shared validation schema

```ts
// packages/api/modules/contact/types.ts
export const contactFormSchema = z.object({
  email: z.string().email(),
  name: z.string().min(3),
  message: z.string().min(10),
});
```

## Flow

1. The procedure is mounted under the `contact` key in the root router.
2. `publicProcedure` means no session is required.
3. `localeMiddleware` resolves locale before the handler runs.
4. Validated input is passed to `sendEmail(...)`.
5. Failures are logged and normalized to `INTERNAL_SERVER_ERROR`.

## Actual route surface

- RPC namespace: `orpc.contact.submit`
- OpenAPI/REST path: `POST /api/contact`
- OpenAPI tag: `Contact`

---

**Related references:**
- `references/api/procedure-tiers.md` — Why this endpoint starts from `publicProcedure`
- `references/api/root-router.md` — Where the module is mounted
- `references/mail/send-email.md` — How `sendEmail(...)` dispatches the email
- `references/auth/better-auth-config.md` — Contrast with authenticated modules that use `protectedProcedure`
