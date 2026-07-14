// Cloudflare Worker fronting Email Service (send_email binding) for
// contextplusplus transactional email. The Railway backend cannot hold a
// Cloudflare API token (token creation is dashboard-gated), but a Worker
// gets the EMAIL binding ambiently — so the backend calls this Worker over
// HTTPS with a shared secret instead. One route: POST /send.
export interface Env {
  readonly EMAIL: EmailSenderBinding;
  // Shared secret the backend must present as `Authorization: Bearer <token>`.
  readonly AUTH_TOKEN: string;
}

// Minimal contract of the Email Service binding (workers-types does not ship
// it yet while the product is in beta). NOTE: unlike the REST API's
// {address, name}, the binding's EmailAddress shape is {email, name}.
interface EmailSenderBinding {
  send(message: {
    readonly from: { readonly email: string; readonly name?: string } | string;
    readonly to: string;
    readonly subject: string;
    readonly html?: string;
    readonly text?: string;
  }): Promise<{ readonly messageId: string }>;
}

interface SendRequest {
  readonly from: { readonly address: string; readonly name?: string } | string;
  readonly to: string;
  readonly subject: string;
  readonly html?: string;
  readonly text?: string;
}

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function isSendRequest(value: unknown): value is SendRequest {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const body = value as Record<string, unknown>;
  const fromOk =
    typeof body.from === "string" ||
    (typeof body.from === "object" &&
      body.from !== null &&
      typeof (body.from as Record<string, unknown>).address === "string");
  return (
    fromOk &&
    typeof body.to === "string" &&
    typeof body.subject === "string" &&
    (typeof body.html === "string" || typeof body.text === "string")
  );
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (request.method !== "POST" || url.pathname !== "/send") {
      return json(404, { error: "not_found" });
    }
    const auth = request.headers.get("authorization") ?? "";
    // AUTH_TOKEN is a required deploy-time secret; refuse everything when the
    // deployment is misconfigured rather than becoming an open relay.
    if (env.AUTH_TOKEN === undefined || env.AUTH_TOKEN.length < 16) {
      return json(503, { error: "sender_not_configured" });
    }
    if (auth !== `Bearer ${env.AUTH_TOKEN}`) {
      return json(401, { error: "unauthorized" });
    }
    let body: unknown;
    try {
      body = await request.json();
    } catch {
      return json(400, { error: "invalid_json" });
    }
    if (!isSendRequest(body)) {
      return json(400, { error: "invalid_request", detail: "from,to,subject,html|text required" });
    }
    try {
      const from =
        typeof body.from === "string"
          ? body.from
          : {
              email: body.from.address,
              ...(body.from.name !== undefined ? { name: body.from.name } : {}),
            };
      const result = await env.EMAIL.send({
        from,
        to: body.to,
        subject: body.subject,
        ...(body.html !== undefined ? { html: body.html } : {}),
        ...(body.text !== undefined ? { text: body.text } : {}),
      });
      return json(200, { message_id: result.messageId });
    } catch (cause) {
      // Binding failures surface as coded strings (E_SENDER_NOT_VERIFIED,
      // E_RATE_LIMIT_EXCEEDED, ...). 502 tells the backend the provider — not
      // the request — failed, which maps to its EmailDeliveryError.
      const message = cause instanceof Error ? cause.message : String(cause);
      return json(502, { error: "send_failed", detail: message });
    }
  },
};
