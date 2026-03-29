# Structured Errors: ConvexError

## Use This When
- Your Swift app needs to handle specific application-level error conditions from the backend.
- Branching UI behavior based on a known server-side error code.
- Returning rich error payloads (codes, minimum values, localized messages) beyond a plain string.

## Server Side

```typescript
import { ConvexError } from "convex/values";

export const bid = mutation({
  args: { itemId: v.id("items"), amount: v.number() },
  handler: async (ctx, args) => {
    const item = await ctx.db.get(args.itemId);
    if (!item) throw new Error("Item not found");  // generic error

    if (args.amount <= item.currentBid) {
      throw new ConvexError({                    // structured error
        code: "BID_TOO_LOW",
        minimumBid: item.currentBid + 1,
        message: `Minimum bid is ${item.currentBid + 1}`,
      });
    }
    await ctx.db.patch(args.itemId, { currentBid: args.amount });
  },
});
```

Use `ConvexError` when the client needs to inspect the error shape. Use plain `throw new Error(...)` for unexpected failures the client should not parse.

## Swift Side

```swift
do {
    try await client.mutation("auction:bid", with: [
        "itemId": itemId, "bidAmount": amount
    ])
} catch ClientError.ConvexError(let data) {
    // data is a raw JSON string of whatever you passed to ConvexError
    struct BidError: Decodable {
        let code: String
        let minimumBid: Int
        let message: String
    }
    if let error = try? JSONDecoder().decode(BidError.self, from: Data(data.utf8)) {
        showAlert(error.message)
    }
} catch ClientError.ServerError(let msg) {
    // Generic server error (e.g., "Item not found")
    showAlert("Server error: \(msg)")
} catch ClientError.InternalError(let msg) {
    // SDK internal error (network, decode failure)
    showAlert("Connection error: \(msg)")
} catch {
    // Other Swift errors (DecodingError, etc.)
    showAlert(error.localizedDescription)
}
```

## Error Type Summary

| Error | When | Associated Value |
|---|---|---|
| `ClientError.ConvexError(data:)` | Your TS function threw `new ConvexError(data)` | JSON string of the data |
| `ClientError.ServerError(msg:)` | Generic `throw new Error("...")` or schema validation failure | Error message |
| `ClientError.InternalError(msg:)` | SDK/network failure, JSON decode error | Description |

## Avoid
- Using `ConvexError` for unexpected crashes or internal logic bugs; use plain `Error` for those.
- Catching only `ConvexError` and ignoring `ServerError` or `InternalError` in Swift.
- Passing unstructured strings to `ConvexError` when the client needs to branch on a code; always pass an object with a `code` field.
- Forgetting to decode the `data` string on the Swift side; it arrives as raw JSON, not a typed object.

## Read Next
- [05-internal-functions-and-helpers.md](05-internal-functions-and-helpers.md)
- [06-intent-plus-schedule-pattern.md](06-intent-plus-schedule-pattern.md)
- [../client-sdk/04-pipeline-termination-and-recovery.md](../client-sdk/04-pipeline-termination-and-recovery.md)
