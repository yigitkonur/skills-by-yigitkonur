# Multi-Round and Request State

*Read this when building flows across multiple elicitation rounds or needing state integrity across re-entry.*

Elicitation flows can span multiple rounds. Each round re-runs your handler with accumulated client responses in `ctx.inputResponses`. Use `requestState` to safely carry trusted data across rounds.

## Two-round flow pattern

```typescript
export const deployConfirm = server.tool(
  {
    name: "deploy-with-confirm",
    description: "Deploy after two confirmations.",
    inputSchema: z.object({ service: z.string() }),
  },
  async (params, ctx) => {
    // Round 1: No inputResponses yet
    if (!ctx.inputResponses) {
      return inputRequired.elicit("deploy-env", {
        schema: z.object({
          environment: z.enum(["staging", "production"]).describe("Target"),
        }),
      }).result;
    }

    // Round 2: First response received, ask for confirmation
    const { environment } = ctx.inputResponses;
    if (ctx.inputResponses.confirmDeployment === undefined) {
      return inputRequired.elicit("deploy-confirm", {
        schema: z.object({
          confirmDeployment: z.boolean().describe(`Deploy to ${environment}?`),
        }),
      }).result;
    }

    // Round 3: Both confirmations received
    if (!ctx.inputResponses.confirmDeployment) {
      return { content: [{ type: "text", text: "Deployment cancelled." }] };
    }

    // Perform the deployment
    await deploy(params.service, environment);
    return {
      content: [{ type: "text", text: `Deployed ${params.service} to ${environment}.` }],
      structuredContent: { success: true, environment },
    };
  }
);
```

## Carrying state forward

Embed prior-round data in the prompt or schema description:

```typescript
const previousInput = ctx.inputResponses?.name || "guest";
return inputRequired.elicit("preferences", {
  schema: z.object({
    theme: z.enum(["light", "dark"]).describe(`Theme for ${previousInput}?`),
  }),
}).result;
```

Do **not** store intermediate state in module-level variables — the module is shared across sessions. Keep state in:
- The handler closure (local variables)
- `requestState` codec for round-trip validation (see below)
- Backend database keyed by user identity

## Request state for integrity

Use `createRequestStateCodec` to sign/verify data across re-entry rounds:

```typescript
import { createRequestStateCodec } from "mcp-use";

const stateCodec = createRequestStateCodec({
  secret: "your-secret-key", // use env var; see 02-setup/08-env-vars.md
  maxAge: 3600, // 1 hour
});

const server = new MCPServer({
  name: "secure-server",
  version: "1.0.0",
  requestState: stateCodec.verify, // enables state validation
});
```

Then encode state and pass it in the elicitation result:

```typescript
export const secureTool = server.tool(
  { name: "secure-op", ... },
  async (params, ctx) => {
    if (!ctx.inputResponses) {
      const state = stateCodec.encode({ userId: ctx.auth.user.id, requestId: generateId() });
      return inputRequired.elicit("verify", {
        schema: z.object({ otp: z.string() }),
        state, // encoded state travels back to client and re-enters via ctx.requestState
      }).result;
    }

    // Re-entry: state is validated by the codec
    const decoded = ctx.requestState.parse(); // throws if validation fails or max age exceeded
    if (decoded.userId !== ctx.auth.user.id) {
      return { isError: true, content: [...] };
    }

    // Now safe to proceed
    return { content: [...] };
  }
);
```

> Documented but not shipped in 2.0.0-beta.66 — verify against your installed version.

## Multi-round rules

1. **Guard re-entry:** Check `if (!ctx.inputResponses)` to detect the first call.
2. **Sequential prompts:** Ask one form or URL per round; don't batch multiple fields into one.
3. **Exit early on cancel:** After each round, check status and return early if not `accept`.
4. **Embed prior answers:** Reference earlier responses in prompts so context is clear.
5. **Validate at SDK level:** Zod schemas automatically validate client input; don't re-validate manually.
6. **Use requestState for trusted data:** Anything that affects authorization or policy must be signed/verified.
7. **Cap rounds:** Keep flows to 2-3 rounds for good completion rates.

## Onboarding example

```typescript
export const onboard = server.tool(
  { name: "onboard", inputSchema: z.object({}) },
  async (_params, ctx) => {
    if (!ctx.inputResponses) {
      // Round 1: Basics
      return inputRequired.elicit("basics", {
        schema: z.object({
          name: z.string().min(2).describe("Full name"),
          email: z.string().email().describe("Email"),
        }),
      }).result;
    }

    const { name, email } = ctx.inputResponses;
    if (ctx.inputResponses.role === undefined) {
      // Round 2: Preferences
      return inputRequired.elicit("prefs", {
        schema: z.object({
          role: z.enum(["dev", "designer", "manager"]).describe("Your role"),
          newsletter: z.boolean().default(true).describe("Weekly updates?"),
        }),
      }).result;
    }

    // Round 3: Complete
    const { role, newsletter } = ctx.inputResponses;
    await createUser({ name, email, role, newsletter });
    return {
      content: [{ type: "text", text: `Welcome, ${name}!` }],
      structuredContent: { userId: email, role },
    };
  }
);
```

## Related

- Form mode schema design: `02-form-mode.md`
- URL mode for browser flows: `03-url-mode.md`
- Anti-patterns: `05-anti-patterns.md`
- Production state patterns: `../10-sessions/03-state-patterns-without-sessions.md`
