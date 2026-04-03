# From Zero to Realtime Chat App

## Use This When
- Starting a new SwiftUI + Convex project from scratch.
- Need a concrete, end-to-end example of every layer (schema, backend, auth, Swift client, views).
- Onboarding a teammate who has never seen Convex before.

---

## Step 1: Initialize the Convex Backend

```bash
mkdir my-chat-app && cd my-chat-app
npm init -y
npm install convex convex-helpers
npx convex dev
```

Keep `npx convex dev` running. See `setup/`.

## Step 2: Define the Schema

```typescript
// convex/schema.ts
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
    channels: defineTable({
        name: v.string(),
        createdBy: v.string(),  // tokenIdentifier
    }),
    messages: defineTable({
        channelId: v.id("channels"),
        userId: v.string(),     // tokenIdentifier
        body: v.string(),
    }).index("by_channel", ["channelId"]),
});
```

See [../backend/01-schema-document-model-and-relationships.md](../backend/01-schema-document-model-and-relationships.md).

## Step 3: Create Auth-Gated Function Wrappers

```typescript
// convex/functions.ts
import { mutation, query, QueryCtx } from "./_generated/server";
import { customQuery, customCtx, customMutation } from "convex-helpers/server/customFunctions";

async function userCheck(ctx: QueryCtx) {
    const identity = await ctx.auth.getUserIdentity();
    if (identity === null) throw new Error("Unauthenticated");
    return { identity };
}

export const userQuery = customQuery(query, customCtx(async (ctx) => await userCheck(ctx)));
export const userMutation = customMutation(mutation, customCtx(async (ctx) => await userCheck(ctx)));
```

This is the primary pattern. `userQuery`/`userMutation` from `convex-helpers` centralizes the auth check and provides `ctx.identity` directly in every handler.

See [../backend/04-auth-rules-and-server-ownership.md](../backend/04-auth-rules-and-server-ownership.md).

## Step 4: Write Backend Functions

```typescript
// convex/messages.ts
import { v } from "convex/values";
import { userMutation, userQuery } from "./functions";

export const list = userQuery({
    args: { channelId: v.id("channels") },
    handler: async (ctx, args) => {
        return await ctx.db.query("messages")
            .withIndex("by_channel", q => q.eq("channelId", args.channelId))
            .order("desc").take(50);
    },
});

export const send = userMutation({
    args: { channelId: v.id("channels"), body: v.string() },
    handler: async (ctx, args) => {
        return await ctx.db.insert("messages", {
            channelId: args.channelId,
            userId: ctx.identity.tokenIdentifier,
            body: args.body.trim(),
        });
    },
});
```

## Step 5: Configure Clerk Auth

```typescript
// convex/auth.config.ts
export default {
    providers: [{
        domain: "YOUR_CLERK_FRONTEND_API_URL",
        applicationID: "convex",
    }],
};
```

Set up via Clerk Dashboard. See [../authentication/01-clerk-first-setup.md](../authentication/01-clerk-first-setup.md).

## Step 6: Add SPM Packages in Xcode

Add these three packages:
- `https://github.com/clerk/clerk-ios` -> `ClerkKit` + `ClerkKitUI`
- `https://github.com/clerk/clerk-convex-swift` -> `ClerkConvex`
- `https://github.com/get-convex/convex-swift` -> `ConvexMobile`

## Step 7: Create the App Entry Point

```swift
import ClerkConvex
import ClerkKit
import ClerkKitUI
import ConvexMobile
import SwiftUI

@MainActor
let client = ConvexClientWithAuth(
    deploymentUrl: "https://your-project.convex.cloud",
    authProvider: ClerkConvexAuthProvider()
)

@main
struct MyChatApp: App {
    init() {
        Clerk.configure(publishableKey: "pk_test_xxx")
    }
    var body: some Scene {
        WindowGroup {
            LandingPage()
                .prefetchClerkImages()
                .environment(Clerk.shared)
        }
    }
}
```

## Step 8: Build the Auth Gate + Main View

```swift
struct LandingPage: View {
    @State private var authState: AuthState<String> = .loading
    @State private var authViewIsPresented = false

    var body: some View {
        Group {
            switch authState {
            case .loading: ProgressView()
            case .unauthenticated:
                Button("Login") { authViewIsPresented = true }
            case .authenticated:
                ChannelView(channelId: "default")
            }
        }
        .sheet(isPresented: $authViewIsPresented) { AuthView() }
        .task {
            for await state in client.authState.values {
                authState = state
            }
        }
    }
}
```

## Step 9: Build the Chat ViewModel + View

```swift
struct Message: Decodable, Identifiable {
    let id: String
    let body: String
    let userId: String
    enum CodingKeys: String, CodingKey {
        case id = "_id"; case body; case userId
    }
}

class ChannelViewModel: ObservableObject {
    @Published var messages: [Message] = []
    let channelId: String

    init(channelId: String) {
        self.channelId = channelId
        client.subscribe(to: "messages:list", with: ["channelId": channelId],
                         yielding: [Message].self)
            .replaceError(with: []) // ⚠️ PROTOTYPE ONLY — kills pipeline after first error. See pitfalls/01.
            .receive(on: DispatchQueue.main)
            .assign(to: &$messages)
    }

    func send(body: String) {
        Task {
            try? await client.mutation("messages:send", with: [
                "channelId": channelId, "body": body
            ])
        }
    }
}
```

---

## Architecture Summary

```
MyChatApp (@main)
  |-- Clerk.configure() in init()
  |-- @MainActor let client = ConvexClientWithAuth(authProvider: ClerkConvexAuthProvider())
  +-- LandingPage
       |-- @State authState via .task { for await }
       |-- .unauthenticated -> AuthView() sheet
       +-- .authenticated -> ChannelView
            +-- @StateObject ChannelViewModel
                 |-- subscribes to "messages:list"
                 +-- mutation "messages:send"
```

## Avoid
- Using raw `query`/`mutation` for authenticated endpoints instead of `userQuery`/`userMutation`.
- Calling `loginFromCache()` or `login()` manually when using `ClerkConvexAuthProvider` -- `bind()` handles it.
- Naming the client variable `convex` -- use `client` to match the official examples.
- Accepting a client-passed `userId` instead of deriving it server-side from `ctx.identity.tokenIdentifier`.

## Read Next
- [02-complete-schema-and-backend-code.md](02-complete-schema-and-backend-code.md)
- [03-complete-swift-models-and-viewmodels.md](03-complete-swift-models-and-viewmodels.md)
- [04-complete-swiftui-views.md](04-complete-swiftui-views.md)
- [05-deployment-checklist.md](05-deployment-checklist.md)
