# Error Response Design

## Origin

Early web APIs returned errors inconsistently — some used HTTP status codes, others returned 200 with error details in the body, and many mixed formats across endpoints. RFC 7807 (Problem Details for HTTP APIs), published in 2016 and updated as RFC 9457 in 2023, standardized a machine-readable error format. Companies like Stripe and Twilio established practical patterns that influenced the broader industry.

## Explanation

### Principles of Good Error Responses

1. **Use correct HTTP status codes**: 4xx for client errors, 5xx for server errors. Never return 200 with an error body.
2. **Machine-readable error codes**: A stable string like `"INSUFFICIENT_FUNDS"` that clients can switch on. Never change these.
3. **Human-readable messages**: A description for developers. These can be improved over time.
4. **Structured details**: Validation errors should identify which fields failed and why.
5. **Request correlation**: Include a request ID or trace ID for debugging.

### RFC 9457 (Problem Details) Format

```json
{
  "type": "https://api.example.com/errors/insufficient-funds",
  "title": "Insufficient Funds",
  "status": 422,
  "detail": "Account balance is $10.00 but the charge requires $25.00",
  "instance": "/charges/ch_abc123"
}
```

### Status Code Categories

| Range | Meaning | Examples |
|-------|---------|---------|
| 200-299 | Success | 200 OK, 201 Created, 204 No Content |
| 400 | Bad request / validation | Malformed JSON, missing fields |
| 401 | Authentication failed | Invalid/missing API key |
| 403 | Authorization failed | Valid key, insufficient permissions |
| 404 | Not found | Resource does not exist |
| 409 | Conflict | Duplicate resource, version conflict |
| 422 | Unprocessable entity | Valid syntax but semantic errors |
| 429 | Rate limited | Too many requests |
| 500 | Internal server error | Unhandled exception |
| 502/503 | Upstream failure | Dependency down, overloaded |

## TypeScript Code Examples

### Bad: Inconsistent Error Responses

```typescript
// BAD: Mix of formats, wrong status codes, no structure
app.post("/orders", async (req, res) => {
  if (!req.body.items) {
    // Returns 200 for an error — clients cannot distinguish success from failure
    return res.json({ success: false, message: "Items required" });
  }

  try {
    const order = await createOrder(req.body);
    res.json(order);
  } catch (err) {
    // Raw error message may leak stack traces or internal details
    res.status(500).json({ error: err.message });
  }
});
```

### Good: Structured Error Response System

```typescript
// GOOD: Consistent error envelope with machine-readable codes
interface ApiError {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  errors?: FieldError[];
  requestId: string;
}

interface FieldError {
  field: string;
  code: string;
  message: string;
}

class AppError extends Error {
  constructor(
    public readonly type: string,
    public readonly title: string,
    public readonly status: number,
    public readonly detail: string,
    public readonly fieldErrors?: FieldError[]
  ) {
    super(detail);
  }
}

// Domain-specific error factories
const Errors = {
  validation(fields: FieldError[]): AppError {
    return new AppError(
      "https://api.example.com/errors/validation",
      "Validation Error",
      422,
      `${fields.length} field(s) failed validation`,
      fields
    );
  },

  notFound(resource: string, id: string): AppError {
    return new AppError(
      "https://api.example.com/errors/not-found",
      "Resource Not Found",
      404,
      `${resource} with id '${id}' does not exist`
    );
  },

  insufficientFunds(required: number, available: number): AppError {
    return new AppError(
      "https://api.example.com/errors/insufficient-funds",
      "Insufficient Funds",
      422,
      `Account balance is $${(available / 100).toFixed(2)} but the charge requires $${(required / 100).toFixed(2)}`
    );
  },

  conflict(detail: string): AppError {
    return new AppError(
      "https://api.example.com/errors/conflict",
      "Conflict",
      409,
      detail
    );
  },
};
```

### Good: Global Error Handler Middleware

```typescript
// GOOD: Central error handler produces consistent responses
function errorHandler(err: Error, req: Request, res: Response, _next: NextFunction) {
  const requestId = req.headers["x-request-id"] as string ?? generateRequestId();

  if (err instanceof AppError) {
    const response: ApiError = {
      type: err.type,
      title: err.title,
      status: err.status,
      detail: err.detail,
      instance: req.originalUrl,
      requestId,
    };

    if (err.fieldErrors) {
      response.errors = err.fieldErrors;
    }

    return res
      .status(err.status)
      .type("application/problem+json")
      .json(response);
  }

  // Unhandled errors — log full details, return safe message
  console.error("Unhandled error:", {
    requestId,
    error: err.message,
    stack: err.stack,
    url: req.originalUrl,
    method: req.method,
  });

  res.status(500).type("application/problem+json").json({
    type: "https://api.example.com/errors/internal",
    title: "Internal Server Error",
    status: 500,
    detail: "An unexpected error occurred. Please contact support with the request ID.",
    requestId,
  });
}

app.use(errorHandler);
```

### Good: Validation Error with Field Details

```typescript
// GOOD: Validation errors identify exactly which fields failed
app.post("/orders", async (req, res, next) => {
  const fieldErrors: FieldError[] = [];

  if (!req.body.items || !Array.isArray(req.body.items)) {
    fieldErrors.push({
      field: "items",
      code: "REQUIRED",
      message: "Items array is required",
    });
  } else if (req.body.items.length === 0) {
    fieldErrors.push({
      field: "items",
      code: "MIN_LENGTH",
      message: "At least one item is required",
    });
  }

  if (!req.body.currency || !["USD", "EUR", "GBP"].includes(req.body.currency)) {
    fieldErrors.push({
      field: "currency",
      code: "INVALID_VALUE",
      message: "Currency must be one of: USD, EUR, GBP",
    });
  }

  if (fieldErrors.length > 0) {
    return next(Errors.validation(fieldErrors));
  }

  const order = await createOrder(req.body);
  res.status(201).json({ data: order });
});

// Response:
// {
//   "type": "https://api.example.com/errors/validation",
//   "title": "Validation Error",
//   "status": 422,
//   "detail": "2 field(s) failed validation",
//   "instance": "/orders",
//   "errors": [
//     { "field": "items", "code": "REQUIRED", "message": "Items array is required" },
//     { "field": "currency", "code": "INVALID_VALUE", "message": "Currency must be one of: USD, EUR, GBP" }
//   ],
//   "requestId": "req_abc123"
// }
```

## Alternatives

| Approach | Pros | Cons |
|----------|------|------|
| **RFC 9457 (Problem Details)** | Standard, extensible, content-type support | Verbose for simple cases |
| **Stripe-style** (`{ error: { type, code, message } }`) | Simple, well-proven | Non-standard |
| **GraphQL errors** (top-level `errors` array) | Part of GraphQL spec | Different paradigm, mixed with data |
| **gRPC status codes** | Protocol-level, strongly typed | Limited to gRPC ecosystem |
| **JSON:API errors** | Full specification | Heavy for most use cases |

## When NOT to Apply

- **Internal microservices with gRPC**: gRPC has its own status code system and error details mechanism. Mapping to RFC 9457 adds a translation layer with no benefit.
- **Webhook payloads**: Webhooks are fire-and-forget from the sender's perspective. Error details in webhook event payloads are a different concern than API error responses.
- **Simple scripts or prototypes**: Over-engineering error responses for a weekend project is wasted effort. Start with status codes and plain messages.

## Trade-offs

- **Error granularity**: Too specific and you create a coupling — clients depend on exact error codes. Too vague and clients cannot react programmatically. Aim for a stable set of codes that map to client actions.
- **Security vs. debuggability**: Detailed errors help developers but can leak information to attackers. Never expose stack traces, SQL queries, or internal paths in production responses.
- **Localization**: Human-readable messages may need translation. Keep machine-readable codes as the stable API; treat messages as hints, not contracts.
- **Error documentation**: Every error code you expose becomes part of your API contract. Document them, version them, and do not remove them without a deprecation period.

## Further Reading

- [RFC 9457 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)
- [Stripe API — Error Handling](https://stripe.com/docs/api/errors)
- [Microsoft REST API Guidelines — Error Responses](https://github.com/microsoft/api-guidelines/blob/vNext/Guidelines.md#7102-error-condition-responses)
- [Google Cloud API Design — Errors](https://cloud.google.com/apis/design/errors)
