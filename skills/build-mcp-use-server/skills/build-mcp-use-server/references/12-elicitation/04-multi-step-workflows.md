# Multi-Step Elicitation Workflows

For longer flows, split the conversation into small validated checkpoints rather than presenting one giant form. Each step renders, validates, and exits early on non-accept.

## Two-step example

```typescript
const step1 = await ctx.elicit(
  "Step 1 of 2: Pick environment",
  z.object({ environment: z.enum(["staging", "production"]).describe("Target") })
);
if (step1.action !== "accept") return text("Cancelled at step 1.");

const step2 = await ctx.elicit(
  `Step 2 of 2: Confirm deployment to ${step1.data.environment}`,
  z.object({
    confirm: z.boolean().default(false).describe("I understand this is irreversible"),
  })
);
if (step2.action !== "accept" || !step2.data.confirm) {
  return text("Deployment not confirmed.");
}
return text(`Deploying to ${step1.data.environment}...`);
```

## Carrying state forward

Inline the prior step's data into the next prompt's message string. Do not store state in module-level variables — the same module is shared across sessions.

```typescript
const step2 = await ctx.elicit(
  `Welcome ${step1.data.name}! Step 2: Preferences`,
  z.object({ /* ... */ })
);
```

If you need to persist state across tool calls (not just steps within one call), use:

- A backend store keyed on `ctx.client.user()?.subject` (see `../16-client-introspection/05-extension-and-user.md`)
- The session metadata API (see `../10-sessions/`)

## Multi-step rules

1. Carry forward already-known values in the next prompt's message string.
2. Validate and exit early after each step (`if (step.action !== "accept") return ...`).
3. Keep step count low — two or three is usually enough.
4. Use URL mode for any step that needs a browser (auth, payment).
5. Make the final irreversible step gated by an explicit `confirm: z.boolean()` field.

## Combining elicitation with sampling

A powerful shape: elicit user intent first, then `ctx.sample()` with that structured input:

```typescript
server.tool(
  { name: "smart-report", schema: z.object({ data: z.string() }) },
  async (args, ctx) => {
    if (!ctx.client.can("elicitation") || !ctx.client.can("sampling")) {
      return error("Required capabilities missing.");
    }

    const prefs = await ctx.elicit("What kind of report?", z.object({
      format: z.enum(["summary", "detailed", "bullets"]).describe("Format"),
      focus: z.string().optional().describe("Specific focus area"),
    }));
    if (prefs.action !== "accept") return text("Report cancelled.");

    const prompt = `Generate a ${prefs.data.format} report` +
      (prefs.data.focus ? ` focused on ${prefs.data.focus}` : "") +
      `:\n\n${args.data}`;

    const report = await ctx.sample(prompt, { maxTokens: 1000, temperature: 0.4 });
    return text(report.content.text);
  }
);
```

See `../13-sampling/01-overview.md` for sampling details.

## Onboarding example

```typescript
server.tool(
  { name: "onboard-user", description: "Multi-step onboarding.", schema: z.object({}) },
  async (_args, ctx) => {
    if (!ctx.client.can("elicitation")) return error("Elicitation not supported.");

    const basics = await ctx.elicit("Step 1: Basic Information", z.object({
      name:  z.string().min(2).describe("Full name"),
      email: z.string().email().describe("Email address"),
    }));
    if (basics.action !== "accept") return text("Onboarding cancelled.");

    const prefs = await ctx.elicit(`Welcome ${basics.data.name}! Step 2: Preferences`, z.object({
      role:       z.enum(["developer", "designer", "manager"]).describe("Your role"),
      experience: z.number().min(0).max(50).describe("Years of experience"),
      newsletter: z.boolean().default(true).describe("Receive weekly updates"),
    }));
    if (prefs.action !== "accept") return text("Onboarding cancelled.");

    return text(
      `Onboarding complete! ${basics.data.name} (${basics.data.email}) — ` +
      `${prefs.data.role}, ${prefs.data.experience}y experience.`
    );
  }
);
```
