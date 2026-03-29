# Full-Text Search With Reactive Results

## Use This When
- Adding search functionality backed by Convex search indexes.
- Building a search UI with debounced input and live-updating results.
- Understanding search index constraints before designing the schema.

## How It Works

Convex full-text search is powered by Tantivy (a Rust search engine library). Search queries run as regular Convex queries, which means they participate in the reactive subscription system. When indexed documents change, subscriptions to search queries automatically update — no polling needed.

## Server-Side: Define Search Index

```typescript
// convex/schema.ts
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  articles: defineTable({
    title: v.string(),
    body: v.string(),
    authorId: v.string(),
    category: v.string(),
    publishedAt: v.number(),
  })
    .searchIndex("search_articles", {
      searchField: "body",           // ONE search field only
      filterFields: ["authorId", "category"],  // Up to 16 filter fields
    }),
});
```

## Server-Side: Search Query

```typescript
// convex/articles.ts
import { userQuery } from "./functions";
import { v } from "convex/values";

export const search = userQuery({
  args: {
    searchText: v.string(),
    category: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    let results = ctx.db
      .query("articles")
      .withSearchIndex("search_articles", (q) => {
        let search = q.search("body", args.searchText);
        if (args.category) {
          search = search.eq("category", args.category);
        }
        return search;
      });

    // .collect() is needed — as of March 2026, search results cannot use .take()
    // Maximum 1024 results returned. Verify against current Convex docs if this has changed.
    return await results.collect();
  },
});
```

## Swift-Side: Reactive Search ViewModel

```swift
import Combine
import ConvexMobile

class SearchViewModel: ObservableObject {
    @Published var query: String = ""
    @Published var results: [Article] = []
    @Published var isSearching = false
    @Published var error: String?

    private var searchCancellable: AnyCancellable?
    private var cancellables = Set<AnyCancellable>()

    init() {
        $query
            .debounce(for: .milliseconds(300), scheduler: DispatchQueue.main)
            .removeDuplicates()
            .sink { [weak self] newQuery in
                self?.executeSearch(query: newQuery)
            }
            .store(in: &cancellables)
    }

    private func executeSearch(query: String) {
        // Cancel previous subscription
        searchCancellable?.cancel()

        guard !query.isEmpty else {
            results = []
            isSearching = false
            return
        }

        isSearching = true

        searchCancellable = client.subscribe(
            to: "articles:search",
            with: ["searchText": query],
            yielding: [Article].self
        )
        .receive(on: DispatchQueue.main)
        .removeDuplicates()
        .sink(
            receiveCompletion: { [weak self] completion in
                if case .failure(let error) = completion {
                    self?.error = error.localizedDescription
                    self?.isSearching = false
                }
            },
            receiveValue: { [weak self] articles in
                self?.results = articles
                self?.isSearching = false
            }
        )
    }
}
```

Key design points:
- **Debounce at 300ms** — prevents a subscription per keystroke.
- **Cancel previous subscription** before starting a new one — each search term creates a new reactive subscription.
- **`.removeDuplicates()`** — prevents re-renders when the WebSocket reconnects with identical results.

## View: Search Interface

```swift
struct ArticleSearchView: View {
    @StateObject private var viewModel = SearchViewModel()

    var body: some View {
        VStack {
            TextField("Search articles...", text: $viewModel.query)
                .textFieldStyle(.roundedBorder)
                .padding()

            if viewModel.isSearching {
                ProgressView("Searching...")
            }

            List(viewModel.results) { article in
                VStack(alignment: .leading) {
                    Text(article.title)
                        .font(.headline)
                    Text(article.body)
                        .font(.body)
                        .lineLimit(2)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }
}
```

## Reactive Behavior

Because search queries are regular Convex queries:
1. User types "machine learning".
2. Swift subscribes to `articles:search` with that search text.
3. Server returns matching articles; client renders them.
4. Another user publishes a new article containing "machine learning".
5. Server detects the search index changed, re-runs the query, and pushes updated results.
6. Swift subscription fires with new results including the new article.

No polling needed. Search results update in real-time.

## Search Index Limits

| Limit | Value |
|-------|-------|
| Search fields per index | **1** |
| Filter fields per index | **16** |
| Max results per query | **1024** |
| Result ordering | **Relevance only** (cannot sort by date) |
| Search indexes per table | Multiple allowed |
| Index rebuild time | Seconds (background, automatic) |

## Important Constraints

- **One search field per index** — cannot search across both `title` and `body` in a single index. Workaround: create a computed `searchText` field that concatenates both, and index that.
- **Relevance order only** — results are ordered by search relevance. Sort by date or other fields client-side (limited to 1024 results).
- **Filter fields are equality only** — `.eq()` only, not range queries. For range filtering, filter client-side after search.

## Avoid
- Creating a new subscription on every keystroke without debouncing — each subscription is a server-side resource.
- Using `.replaceError(with:)` on the search subscription — it emits the fallback then **completes** permanently, killing reactive updates.
- Expecting search results to be sortable by anything other than relevance — that is a client-side responsibility.
- Assuming `.take(n)` works on search results — it does not. Use `.collect()` and limit client-side if needed.

## Read Next
- [01-pagination-live-tail-and-history.md](01-pagination-live-tail-and-history.md)
- [05-image-upload-photospicker-asyncimage.md](05-image-upload-photospicker-asyncimage.md)
- [07-subscription-deduplication-and-fan-out.md](07-subscription-deduplication-and-fan-out.md)
