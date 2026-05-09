# Prompt gates — human-in-the-loop before destructive or sensitive ops

Some operations should never run on the agent's word alone. A user must approve them, in-line, before the side effect happens. This file is the prompt-gate pattern: tool returns "approval required," agent surfaces the question to the user, user replies, tool re-runs with proof of approval. Cross-link `auth-identity.md` for OAuth step-up consent, `agentic-patterns.md` for how gates fit into multi-step workflows, and `client-compatibility.md` for which clients support which approval mechanism.

The tradeoff is latency vs trust. A gate adds at least one extra turn — the user must read, decide, and reply. Use it only where the cost of a wrong action exceeds the cost of a delayed action. For everything else, structured errors and idempotency keys are cheaper.

---

## Use cases — where prompt gates earn their keep

**Financial transactions.** Wire transfers, refunds over a threshold, posting invoices to customers, charging cards. The cost of a hallucinated $10,000 transfer is unbounded; the cost of a 30-second delay is annoyance. Always gate.

**Data deletion.** `DROP TABLE`, `delete_environment`, `remove_user`, `purge_logs`. Deletion is rarely reversible at the speed an agent operates. The gate buys the user a chance to read the SQL, confirm the environment ID, notice the typo. Always gate destructive ops on production scope.

**Sending external messages.** Email blasts, Slack DMs to non-team users, Twitter posts, customer-facing chat replies. Once it leaves the system, it cannot be unsent. Even when an agent is correct, the user often wants a final read-pass for tone. Gate by default; the user can opt out for personal/private channels.

**Escalating privileges.** Granting admin role, opening a port to public, disabling MFA, rotating keys, adding OAuth scopes. The agent may need elevated access mid-session for one tool call; gate the elevation, not every subsequent call. Pair with OAuth step-up consent — see `auth-identity.md`.

Other common gate targets: `git push --force` to protected branches, schema migrations on production, deploys outside business hours, anything tagged `irreversible: true` in your tool annotations.

**Source:** [Anthropic — Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents); spec 2025-11-25 elicitation guidance at [modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-11-25/server/elicitation).

---

## The basic shape — `requires_approval` flag in the response

The lowest-coupling implementation: the tool inspects the call, decides "this needs approval," and returns a structured response that the agent must surface to the user. The agent re-calls with an approval token after the user agrees. No protocol features beyond `isError`. Works on every client.

```typescript
interface ApprovalChallenge {
  requires_approval: true;
  approval_token: string;       // signed by server; opaque to agent
  summary: string;              // shown verbatim to the user
  side_effects: string[];       // what will happen if approved
  expires_at: string;           // ISO 8601; gate expires after N minutes
}

server.tool("delete_environment", "Delete an environment. Requires approval.", {
  environment_id: z.string(),
  approval_token: z.string().optional(),
}, async ({ environment_id, approval_token }) => {
  if (!approval_token) {
    const challenge: ApprovalChallenge = {
      requires_approval: true,
      approval_token: signApproval({ tool: "delete_environment", environment_id, ts: Date.now() }),
      summary: `Permanently delete environment "${environment_id}".`,
      side_effects: [
        `Removes ${countResources(environment_id)} resources.`,
        `Cancels ${countActiveDeployments(environment_id)} active deployments.`,
        `Purges ${countLogs(environment_id, "30d")} log entries.`,
      ],
      expires_at: new Date(Date.now() + 5 * 60_000).toISOString(),
    };
    return {
      content: [{ type: "text", text: JSON.stringify(challenge, null, 2) }],
      structuredContent: challenge,
    };
  }
  const claim = verifyApproval(approval_token);
  if (!claim || claim.tool !== "delete_environment" || claim.environment_id !== environment_id) {
    return { content: [{ type: "text", text: "Invalid or expired approval_token. Request approval again." }], isError: true };
  }
  await deleteEnvironment(environment_id);
  return { content: [{ type: "text", text: `Environment ${environment_id} deleted.` }] };
});
```

The agent reads `requires_approval: true`, surfaces `summary` and `side_effects` to the user, waits for "yes," and re-calls with the token. The server enforces the binding — token tied to tool name, parameters, and timestamp. Replay across tools, parameter substitution, and stale-token attacks all fail at `verifyApproval`.

---

## Variant — gate via elicitation (form mode)

When the client supports `elicitation/create` (VS Code 1.102+, Cursor late 2025, Codex CLI, Goose), the server can pop a form. Cleaner UX than reading a JSON challenge from chat. Capability-check first; fall back to the `requires_approval` shape when missing. Cross-link `client-compatibility.md` Pattern 13 for the matrix; cross-link `advanced-protocol.md` for the full elicitation flow.

```typescript
import { z } from "zod";

const ConfirmDelete = z.object({
  confirmed: z.boolean().describe("Confirm permanent deletion of the environment"),
  reason: z.string().optional().describe("Reason for deletion (optional, for audit log)"),
});

server.tool("delete_environment", "Delete an environment. Requires confirmation.", {
  environment_id: z.string(),
}, async ({ environment_id }, ctx) => {
  if ("elicitation" in (ctx.client_capabilities ?? {})) {
    const answer = await ctx.session.elicit({
      message: `Permanently delete environment "${environment_id}"?`,
      schema: ConfirmDelete,
    });
    if (!answer?.confirmed) {
      return { content: [{ type: "text", text: "Deletion cancelled." }] };
    }
    await deleteEnvironment(environment_id, { reason: answer.reason });
    return { content: [{ type: "text", text: `Environment ${environment_id} deleted.` }] };
  }
  // Fall back to in-band approval when elicitation unavailable.
  return {
    content: [{
      type: "text",
      text: "Confirmation required. Re-call with confirm=true in the next request to proceed.",
    }],
  };
});
```

Two non-negotiable rules from the spec: elicitation `schema` MUST be flat (no nesting), and elicitation MUST NOT be used for passwords, SSNs, credentials, or anything sensitive. Use `elicitation/create` for **confirmation**, never for **secrets**. For secrets, use the URL-mode escape hatch (server hands the client a URL the user opens in their browser; client never sees the secret) — supported only on VS Code Insiders as of 2025-12.

**Source:** [MCP spec — elicitation](https://modelcontextprotocol.io/specification/2025-11-25/server/elicitation); [github.blog — MCP elicitation in Copilot](https://github.blog/ai-and-ml/github-copilot/building-smarter-interactions-with-mcp-elicitation-and-vs-code-1-102/) (2025-09-04).

---

## Variant — gate via OAuth step-up consent

For "this user is logged in but the requested tool needs admin scope," return an OAuth step-up challenge. The client triggers a fresh consent screen, the user grants (or refuses) the elevated scope, the client retries with a token bearing the new scope. The server never sees the password. This is the right gate for privilege escalation and for mid-session scope expansion. Cross-link `auth-identity.md` for the full OAuth 2.1 + step-up flow.

```typescript
server.tool("rotate_production_key", "Rotate the production API key. Requires admin:write scope.", {
  service_id: z.string(),
}, async ({ service_id }, ctx) => {
  if (!ctx.principal.scopes.includes("admin:write")) {
    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          requires_step_up: true,
          required_scope: "admin:write",
          authorize_url: `${process.env.AS_URL}/authorize?response_type=code&client_id=${process.env.CLIENT_ID}&scope=admin:write&prompt=consent&redirect_uri=${encodeURIComponent(process.env.REDIRECT_URI!)}`,
          summary: `Rotating the production key for "${service_id}" requires the admin:write scope. Re-authenticate to grant it.`,
        }),
      }],
      isError: true,
    };
  }
  const newKey = await rotateKey(service_id);
  return { content: [{ type: "text", text: `Rotated ${service_id}. New key id: ${newKey.id}.` }] };
});
```

The client surfaces the URL, the user re-consents, the next call carries a token that includes `admin:write`. Server verifies on every call; nothing is cached client-side beyond the token's normal lifetime.

**Source:** [RFC 9396 — Rich Authorization Requests](https://datatracker.ietf.org/doc/rfc9396/); [Cloudflare workers-oauth-provider](https://github.com/cloudflare/workers-oauth-provider).

---

## Bad-vs-good gate implementations

### Bad — boolean param without server-side enforcement

```typescript
// Bad: agent sets confirm=true on its own. No human in the loop.
server.tool("delete_environment", "Delete environment. Set confirm=true to proceed.", {
  environment_id: z.string(),
  confirm: z.boolean(),
}, async ({ environment_id, confirm }) => {
  if (!confirm) {
    return { content: [{ type: "text", text: "Set confirm=true to proceed." }], isError: true };
  }
  await deleteEnvironment(environment_id);
  return { content: [{ type: "text", text: "Deleted." }] };
});
```

Agents will set `confirm: true` on their first call. The "gate" is a description string the model promptly ignores. No human ever sees the deletion until it's done. This is the prompt-gate pattern's most common anti-pattern.

### Good — gate enforced via signed token + side-effect summary

```typescript
// Good: server signs a challenge, surfaces side effects, requires the user to OK it.
server.tool("delete_environment", "Delete environment. Two-step approval required.", {
  environment_id: z.string(),
  approval_token: z.string().optional(),
}, async ({ environment_id, approval_token }) => {
  if (!approval_token) {
    return { content: [{ type: "text", text: JSON.stringify(buildChallenge(environment_id)) }] };
  }
  if (!verifyChallenge(approval_token, "delete_environment", { environment_id })) {
    return { content: [{ type: "text", text: "Approval token invalid or expired. Re-request." }], isError: true };
  }
  await deleteEnvironment(environment_id);
  return { content: [{ type: "text", text: `Deleted ${environment_id}.` }] };
});
```

The signed token is the proof of human consent; the agent cannot mint one. Side effects are listed verbatim in the challenge so the user can read what they're approving. The token is scoped to the exact tool call — replay against a different `environment_id` fails verification. Tokens expire so a 5-minute-old approval cannot be used for an action the user has since forgotten about.

### Bad — mixing the gate into the success path

```typescript
// Bad: server triggers the action, then asks for forgiveness.
server.tool("send_email_blast", "Send email to all customers.", {
  template_id: z.string(),
}, async ({ template_id }) => {
  await sendEmailBlast(template_id);          // already gone
  return { content: [{ type: "text", text: "Sent. Was that intentional?" }] };
});
```

Recall is impossible. The "gate" is post-hoc and useless.

### Good — challenge-then-execute, ordered correctly

```typescript
// Good: gate first, then execute, then confirm.
server.tool("send_email_blast", "Send email to all customers.", {
  template_id: z.string(),
  approval_token: z.string().optional(),
}, async ({ template_id, approval_token }) => {
  if (!approval_token) {
    return { content: [{ type: "text", text: JSON.stringify(challengeFor(template_id)) }] };
  }
  if (!verifyChallenge(approval_token, "send_email_blast", { template_id })) {
    return { content: [{ type: "text", text: "Invalid approval. Re-request." }], isError: true };
  }
  const sent = await sendEmailBlast(template_id);
  return { content: [{ type: "text", text: `Sent to ${sent.recipient_count} customers. Message ID: ${sent.id}.` }] };
});
```

The action only runs after the user has read the challenge and the agent has re-called with proof. Failure mode is "user said no" — the action never happens.

---

## Gate hygiene — non-negotiables

- **Sign approval tokens.** HMAC-SHA256 with a server-only secret, scoped to tool name and salient parameters. Plain UUIDs or sequence numbers are forgeable.
- **Bind tokens to parameters.** A token approved for `delete_environment(env="staging")` MUST NOT delete `production`. Verify the parameter set on every consume.
- **Set short expirations.** 5 minutes for destructive actions, 60 seconds for messages, 24 hours only for the rare "approve a backlog of pending actions" UX. Stale approvals are nearly indistinguishable from no approval.
- **Surface side effects in plain language.** "Deletes 47 resources, cancels 3 deployments, purges 12,400 log lines" beats "permanently deletes the environment." The user has to imagine the wrong outcome to refuse it.
- **Never gate read-only tools.** A gate on `list_invoices` is friction with no upside. Use gates only where the action mutates state, sends data outside the system, or grants access.
- **Log every approved and rejected challenge.** The audit log is what makes this defensible after the fact.
- **Combine with idempotency keys.** A gated tool that returns "approved, executed" once should return the same result on retry — not re-execute. See `../../common/idempotency-and-retries.md` for the cross-surface idempotency contract and `agentic-patterns.md` for combining gates with parameter-dependency chains.

---

## Cross-references

- `agentic-patterns.md` — workflow integration: gates as one node in a multi-step pipeline, parameter-dependency chains as the structural sibling.
- `auth-identity.md` — OAuth 2.1, step-up consent, RFC 9396 Rich Authorization Requests for scoped escalation.
- `advanced-protocol.md` — `elicitation/create` form mode and URL mode in detail.
- `client-compatibility.md` — which clients support elicitation, sampling, and the URL escape hatch as of 2026-02.
- `error-handling.md` — how to shape the `isError: true` envelope when an approval is missing or expired.
- `../../common/idempotency-and-retries.md` — pairing gates with idempotency keys so the action runs at most once.
- `../decision-trees/security-posture.md` — when to add a gate at all (the threat-model decision before this file's how-to).
