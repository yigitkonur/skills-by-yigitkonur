# Memory: Long-Term Stores & Caching Reference

Complete reference for LangGraph BaseStore (long-term cross-thread memory), LLM response caching (all 8 cache classes), `CacheBackedEmbeddings`, GDPR compliance, and legacy migration. All APIs verified against `@langchain/langgraph@1.x`, `@langchain/core@1.x`, `langchain@1.x` — March 2026. TypeScript only.

---

## Quick Reference — Imports

```typescript
// Long-term stores (LangGraph)
import { InMemoryStore } from "@langchain/langgraph";
import { PostgresStore } from "@langchain/langgraph-checkpoint-postgres/store";

// LangChain key-value stores (for CacheBackedEmbeddings, ParentDocumentRetriever)
import { InMemoryStore } from "@langchain/core/stores";
import { LocalFileStore } from "@langchain/community/storage/file_system";
import { RedisStore } from "@langchain/community/storage/ioredis";
import { UpstashRedisStore } from "@langchain/community/storage/upstash_redis";
import { VercelKVStore } from "@langchain/community/storage/vercel_kv";

// LLM Caching
import { InMemoryCache, setLLMCache } from "@langchain/core/caches";
import { RedisCache } from "@langchain/community/caches/ioredis";
import { UpstashRedisCache } from "@langchain/community/caches/upstash_redis";
import { CloudflareKVCache } from "@langchain/cloudflare";
import { SQLiteCache } from "@langchain/community/caches/sqlite";
import { MomentoCache } from "@langchain/community/caches/momento";
import { RedisSemanticCache } from "langchain-redis";
import { CassandraSemanticCache } from "@langchain/community/caches/cassandra";

// Embeddings cache
import { CacheBackedEmbeddings } from "langchain/embeddings/cache_backed";
```

---

## Two BaseStore Interfaces — Critical Distinction

There are **two different `BaseStore` interfaces** in LangChain.js. They are NOT interchangeable:

| Aspect | LangChain BaseStore (`@langchain/core/stores`) | LangGraph BaseStore (`@langchain/langgraph`) |
|--------|-----------------------------------------------|---------------------------------------------|
| Key structure | Single flat string | `namespace[]` array + `key` string |
| Value type | Generic `V` | `Record<string, any>` JSON document |
| Batch API | `mget/mset/mdelete` | `batch(ops[])` |
| Key iteration | `yieldKeys(prefix?)` | `listNamespaces()` |
| Vector search | Not supported | `search(namespace, query?)` |
| Used by | `CacheBackedEmbeddings`, `ParentDocumentRetriever` | LangGraph agents (long-term memory) |

---

## LangGraph BaseStore Full API

```typescript
// From @langchain/langgraph
interface BaseStore {
  // Write a JSON document under namespace + key
  put(
    namespace: string[],
    key: string,
    value: object,
    options?: { index?: string[] | false }
  ): Promise<void>;

  // Retrieve a single document
  get(
    namespace: string[],
    key: string
  ): Promise<{
    value: object;
    key: string;
    namespace: string[];
    createdAt: string;
    updatedAt: string;
  } | undefined>;

  // Semantic similarity search + optional content filter
  search(
    namespace: string[],
    opts?: {
      query?: string;               // natural-language → vector similarity
      filter?: Record<string, any>; // exact field match
      limit?: number;               // default: 10
    }
  ): Promise<Array<{
    key: string;
    value: object;
    namespace: string[];
    createdAt: string;
    updatedAt: string;
    score?: number;                 // relevance score (0–1) when query supplied
  }>>;

  // Delete a single document
  delete(namespace: string[], key: string): Promise<void>;

  // List all namespaces (with optional prefix/suffix/depth filtering)
  listNamespaces(opts?: {
    prefix?: string[];
    suffix?: string[];
    maxDepth?: number;
    limit?: number;
    offset?: number;
  }): Promise<string[][]>;

  // Batch multiple operations efficiently
  batch(ops: Operation[]): Promise<OperationResults<Op>>;

  start(): Promise<void>;
  stop(): Promise<void>;
}
```

---

## InMemoryStore (Dev/Test)

**Package:** `@langchain/langgraph`

```typescript
import { InMemoryStore } from "@langchain/langgraph";
import { OpenAIEmbeddings } from "@langchain/openai";

// Without semantic search
const store = new InMemoryStore();

// With semantic search (vector indexing via HNSW)
const store = new InMemoryStore({
  index: {
    embeddings: new OpenAIEmbeddings({ model: "text-embedding-3-small" }),
    dims: 1536,
    fields: ["$"],    // "$" = index entire document; or ["field1", "field2"]
    metric: "cosine", // default; also "euclidean" | "dot_product"
  },
});

await store.put(["user_123", "memories"], "pref1", { text: "Prefers dark mode" });
await store.put(["user_123", "memories"], "pref2", { text: "Expert TypeScript developer" });

// Semantic search
const results = await store.search(["user_123", "memories"], {
  query: "UI preferences",
  limit: 3,
});
// results[0].score — similarity score (0–1)
```

**Characteristics:** Volatile (lost on restart), no TTL, supports namespace + vector search when `index` config provided. Use for dev/test only.

---

## PostgresStore (Production)

**Package:** `@langchain/langgraph-checkpoint-postgres`

```typescript
import { PostgresStore } from "@langchain/langgraph-checkpoint-postgres/store";
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
import { OpenAIEmbeddings } from "@langchain/openai";

const DB_URI = process.env.DATABASE_URL!;

// Long-term store for cross-thread memory
const store = PostgresStore.fromConnString(DB_URI, {
  index: {
    embeddings: new OpenAIEmbeddings({ model: "text-embedding-3-small" }),
    dims: 1536,
    fields: ["content", "summary"],  // index specific fields for vector search
  },
});
await store.setup(); // Creates required tables — MUST be called once

// Short-term checkpointer (can share the same PostgreSQL database)
const checkpointer = PostgresSaver.fromConnString(DB_URI);
await checkpointer.setup();
```

**PostgresStore method reference:**

| Method | Return Type | Description |
|--------|-------------|-------------|
| `setup()` | `Promise<void>` | Creates tables and runs migrations. Call once before use. |
| `put(namespace, key, value)` | `Promise<void>` | Upsert a document |
| `get(namespace, key)` | `Promise<Item \| undefined>` | Retrieve a document |
| `delete(namespace, key)` | `Promise<void>` | Delete a document |
| `search(namespace, opts?)` | `Promise<SearchItem[]>` | Text or vector search |
| `listNamespaces(opts?)` | `Promise<string[][]>` | List available namespaces |
| `batch(ops)` | `Promise<OperationResults>` | Execute multiple ops atomically |
| `sweepExpiredItems()` | `Promise<number>` | Remove expired items |
| `start()` | `Promise<void>` | Start (calls setup if `ensureTables=true`) |
| `stop()` | `Promise<void>` | Close DB connections |

---

## Namespace Patterns

Namespaces are `string[]` arrays acting as hierarchical paths. They define isolation boundaries.

```typescript
// Standard patterns
const userNs = ["user", userId];                                  // single user scope
const userAppNs = ["user", userId, "chitchat"];                   // user + context
const orgUserNs = ["org", orgId, "user", userId];                 // multi-tenant
const prefsNs = ["user", userId, "preferences"];                  // typed memories
const episodeNs = ["user", userId, "episodes", sessionId];        // per-session episodic
const instrNs = ["agent_instructions"];                           // procedural memory
```

**Multi-tenant isolation wrapper:**

```typescript
import { BaseStore } from "@langchain/langgraph";

function getUserStore(store: BaseStore, tenantId: string, userId: string) {
  const ns = ["tenant", tenantId, "user", userId];
  return {
    async put(key: string, value: object) { return store.put(ns, key, value); },
    async get(key: string) { return store.get(ns, key); },
    async search(query: string, filter?: Record<string, any>) {
      return store.search(ns, { query, filter });
    },
    async delete(key: string) { return store.delete(ns, key); },
    async deleteAll() {
      const namespaces = await store.listNamespaces({ prefix: ns });
      for (const namespace of namespaces) {
        const items = await store.search(namespace);
        await Promise.all(items.map((item) => store.delete(namespace, item.key)));
      }
    },
  };
}
```

---

## IndexConfig — Semantic Search Configuration

```typescript
interface IndexConfig {
  embeddings: Embeddings;      // LangChain Embeddings instance
  dims: number;                // vector dimensions (MUST match model output)
  fields?: string[];           // JSON paths to embed; default ["$"] = entire doc
  metric?: "cosine" | "euclidean" | "dot_product"; // default: "cosine"
}
```

**Common dimension values:**

| Model | Dims |
|---|---|
| `text-embedding-3-small` | 1536 |
| `text-embedding-3-large` | 3072 |
| `text-embedding-ada-002` | 1536 |
| `cohere embed-english-v3` | 1024 |

**LangGraph Platform config (`langgraph.json`):**

```json
{
  "store": {
    "index": {
      "embed": "openai:text-embedding-3-small",
      "dims": 1536,
      "fields": ["text", "summary"]
    }
  }
}
```

**Selective field indexing (per-document override):**

```typescript
await store.put(["docs"], "doc1", { text: "Python tutorial" });                         // default (full doc)
await store.put(["docs"], "doc2", { other: "value" }, { index: ["other"] });            // index "other" only
await store.put(["docs"], "doc3", { text: "Private" }, { index: false });               // not indexed
```

**Custom async embedding function:**

```typescript
import OpenAI from "openai";

const openaiClient = new OpenAI();
const aembedTexts = async (texts: string[]): Promise<number[][]> => {
  const response = await openaiClient.embeddings.create({
    model: "text-embedding-3-small",
    input: texts,
  });
  return response.data.map((e) => e.embedding);
};

const store = new InMemoryStore({ index: { embed: aembedTexts, dims: 1536 } });
```

---

## Memory Storage Patterns

### Profile Pattern

Single JSON document per user. Read-modify-write on each update.

```typescript
import { tool } from "langchain";
import { type ToolRuntime } from "langchain";
import { z } from "zod";

const getUserInfo = tool(
  async (_, runtime: ToolRuntime) => {
    const info = await runtime.store.get(["users"], runtime.context.userId);
    return info?.value ? JSON.stringify(info.value) : "No profile found";
  },
  { name: "getUserInfo", description: "Look up user profile", schema: z.object({}) }
);

const saveUserInfo = tool(
  async (userInfo, runtime: ToolRuntime) => {
    const userId = runtime.context.userId;
    const existing = await runtime.store.get(["users"], userId);
    const merged = { ...(existing?.value ?? {}), ...userInfo };
    await runtime.store.put(["users"], userId, merged);
    return "Profile saved.";
  },
  {
    name: "saveUserInfo",
    description: "Save or update user profile",
    schema: z.object({
      name: z.string().optional(),
      language: z.string().optional(),
      timezone: z.string().optional(),
    }),
  }
);
```

**Trade-offs:** Simple mental model; no semantic search per individual fact; large profiles become unwieldy.

### Collection Pattern

Each memory is a separate document. Supports semantic search and per-fact operations. Preferred for granular recall.

```typescript
import { v4 as uuidv4 } from "uuid";

// Store individual memories
await runtime.store.put(
  ["user", userId, "memories"],
  uuidv4(),
  { content: "Prefers TypeScript", type: "preference", createdAt: new Date().toISOString() }
);

// Semantic search across collection
const results = await runtime.store.search(["user", userId, "memories"], {
  query: "programming language preferences",
  filter: { type: "preference" },
  limit: 10,
});
```

### Agent Instructions Pattern (Procedural Memory)

```typescript
import { StateGraph } from "@langchain/langgraph";
import { BaseStore } from "@langchain/langgraph";

const callModel = async (state: State, config: { store?: BaseStore }) => {
  const instrItem = await config.store?.get(["agent_instructions"], "agent_a");
  const instructions = instrItem?.value?.instructions as string ?? "You are a helpful assistant.";
  const response = await llm.invoke([
    { role: "system", content: instructions },
    ...state.messages,
  ]);
  return { messages: [response] };
};
```

---

## Accessing Store Inside Graph Nodes

```typescript
import { StateGraph, Annotation } from "@langchain/langgraph";
import { BaseStore } from "@langchain/langgraph";

const callModel = async (
  state: typeof StateAnnotation.State,
  config: { store?: BaseStore; configurable?: { userId?: string } }
) => {
  const userId = config.configurable?.userId ?? "anonymous";
  const profileItem = await config.store?.get(["user", userId], "profile");
  const profile = profileItem?.value;

  const response = await llm.invoke([
    { role: "system", content: `User profile: ${JSON.stringify(profile ?? {})}` },
    ...state.messages,
  ]);
  return { messages: [response] };
};

const graph = new StateGraph(StateAnnotation)
  .addNode("callModel", callModel)
  .addEdge("__start__", "callModel")
  .compile({ store });  // pass store here
```

---

## Production: Hybrid Short-Term + Long-Term

```typescript
import { createAgent } from "langchain";
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
import { PostgresStore } from "@langchain/langgraph-checkpoint-postgres/store";
import { summarizationMiddleware } from "langchain";
import { OpenAIEmbeddings } from "@langchain/openai";

const DB_URI = process.env.DATABASE_URL!;

const checkpointer = PostgresSaver.fromConnString(DB_URI);
await checkpointer.setup();

const store = PostgresStore.fromConnString(DB_URI, {
  index: {
    embeddings: new OpenAIEmbeddings({ model: "text-embedding-3-small" }),
    dims: 1536,
    fields: ["content", "summary"],
  },
});
await store.setup();

const agent = createAgent({
  model: "claude-sonnet-4-6",
  tools: [getUserInfo, saveUserInfo, searchMemories],
  checkpointer,  // short-term: per-thread graph state
  store,         // long-term: cross-session memories
  middleware: [
    summarizationMiddleware({
      model: "gpt-4o-mini",
      trigger: { tokens: 4000 },
      keep: { messages: 20 },
    }),
  ],
});
```

---

## GDPR Compliance

### Right to Erasure (Article 17)

```typescript
import { BaseStore } from "@langchain/langgraph";

// Complete user data deletion across all namespaces
async function deleteUserData(store: BaseStore, userId: string): Promise<void> {
  const userNamespaces = await store.listNamespaces({ prefix: ["user", userId] });
  const orgNamespaces = await store.listNamespaces({ prefix: ["org"] });
  const orgUserNamespaces = orgNamespaces.filter((ns) => ns.includes(userId));

  for (const namespace of [...userNamespaces, ...orgUserNamespaces]) {
    const items = await store.search(namespace, { limit: 1000 });
    await Promise.all(items.map((item) => store.delete(namespace, item.key)));
  }
}

// Verify deletion
async function verifyDeletion(store: BaseStore, userId: string): Promise<boolean> {
  const remaining = await store.listNamespaces({ prefix: ["user", userId] });
  return remaining.length === 0;
}
```

### Data Subject Access Request (DSAR) Export

```typescript
async function exportUserData(store: BaseStore, userId: string) {
  const namespaces = await store.listNamespaces({ prefix: ["user", userId] });
  const export_: Record<string, any> = {};

  for (const namespace of namespaces) {
    const items = await store.search(namespace, { limit: 1000 });
    export_[namespace.join("/")] = items.map(({ key, value, createdAt, updatedAt }) => ({
      key, value, createdAt, updatedAt,
    }));
  }
  return export_;
}
```

### Data Retention with Metadata TTL

```typescript
async function putWithRetention(
  store: BaseStore, namespace: string[], key: string,
  value: object, retentionDays = 90
): Promise<void> {
  await store.put(namespace, key, {
    ...value,
    _meta: {
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + retentionDays * 24 * 60 * 60 * 1000).toISOString(),
    },
  });
}

// Client-side expiry filter (for stores without native TTL)
async function getFreshItems(store: BaseStore, namespace: string[]) {
  const all = await store.search(namespace, { limit: 1000 });
  return all.filter((item) => {
    const expiresAt = (item.value as any)._meta?.expiresAt;
    return !expiresAt || new Date(expiresAt) > new Date();
  });
}
```

### PII Filtering (Before Storage)

```typescript
// Strip PII before storage
function sanitizeForStorage(value: object): object {
  const json = JSON.stringify(value);
  return JSON.parse(
    json
      .replace(/\b[A-Z][a-z]+\s[A-Z][a-z]+\b/g, "[NAME]")       // names
      .replace(/\b\d{3}-\d{2}-\d{4}\b/g, "[SSN]")                // SSNs
      .replace(/\b[\w.-]+@[\w.-]+\.\w{2,}\b/g, "[EMAIL]")         // emails
  );
}

await store.put(namespace, key, sanitizeForStorage(rawData));
```

---

## LLM Caching

LLM caching avoids redundant API calls by returning stored responses. All caches implement `BaseCache`:

```typescript
import { BaseCache } from "@langchain/core/caches";
import { Generation } from "@langchain/core/outputs";

abstract class BaseCache {
  abstract lookup(prompt: string, llmKey: string): Promise<Generation[] | null>;
  abstract update(prompt: string, llmKey: string, value: Generation[]): Promise<void>;
  clear(): void;
  async aclear(): Promise<void>;
}
```

**How the cache is consulted:**
1. LLM call made → LangChain calls `cache.lookup(prompt, llmKey)` where `llmKey` is a deterministic string of model params
2. If `null` → call the actual LLM, then call `cache.update(...)`
3. If a value returned → use it directly, skipping the LLM API call

### Setting Cache

```typescript
import { setLLMCache, InMemoryCache } from "@langchain/core/caches";

// Global — applies to ALL LLM calls in the process
setLLMCache(new InMemoryCache());

// Per-model instance
import { ChatOpenAI } from "@langchain/openai";
import { RedisCache } from "@langchain/community/caches/ioredis";
import { Redis } from "ioredis";

const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  cache: new RedisCache(new Redis(), { ttl: 3600 }),
});

// Explicitly disable cache for a model
const dynamicModel = new ChatOpenAI({
  model: "gpt-4o-mini",
  cache: false,
});
```

---

## Exact Match Caches

Returns a cached response only if the prompt string matches **exactly**.

### 1. InMemoryCache

**Package:** `@langchain/core/caches`

```typescript
import { InMemoryCache, setLLMCache } from "@langchain/core/caches";

setLLMCache(new InMemoryCache());

// Or use the process-level singleton
const globalCache = InMemoryCache.global();
```

- In-process only; data lost on restart
- No TTL
- Fastest possible lookup (Map-based)
- **Known conflict:** Do NOT use with `MemorySaver` — they conflict internally

### 2. RedisCache (ioredis)

**Package:** `@langchain/community/caches/ioredis`

```typescript
import { RedisCache } from "@langchain/community/caches/ioredis";
import { Redis } from "ioredis";

const redisClient = new Redis({ host: "localhost", port: 6379 });

const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  cache: new RedisCache(redisClient, { ttl: 3600 }),
});
```

Constructor: `new RedisCache(redisClient: Redis, options?: { ttl?: number; keyEncoder?: Fn })`
- Works with Redis Cluster via pre-configured ioredis cluster client. Do NOT use `redis_url` with Cluster.

### 3. UpstashRedisCache

**Package:** `@langchain/community/caches/upstash_redis`

```typescript
import { UpstashRedisCache } from "@langchain/community/caches/upstash_redis";

const cache = new UpstashRedisCache({
  config: {
    url: process.env.UPSTASH_REDIS_REST_URL!,
    token: process.env.UPSTASH_REDIS_REST_TOKEN!,
  },
  ttl: 3600,
});
```

- Serverless Redis via HTTP REST; edge-compatible (Cloudflare Workers, Vercel Edge)
- No persistent TCP connection

### 4. CloudflareKVCache

**Package:** `@langchain/cloudflare`

```typescript
import { CloudflareKVCache } from "@langchain/cloudflare";
import { ChatAnthropic } from "@langchain/anthropic";

// Inside Cloudflare Worker
export default {
  async fetch(request: Request, env: Env) {
    const cache = new CloudflareKVCache(env.KV_NAMESPACE);
    const model = new ChatAnthropic({ cache });
    const response = await model.invoke("How are you today?");
    return new Response(JSON.stringify(response), {
      headers: { "content-type": "application/json" },
    });
  },
};
```

- Only works inside Cloudflare Workers
- No explicit TTL in the wrapper (use Workers KV native TTL separately)
- Eventually consistent (global Workers KV distribution)

### 5. SQLiteCache

**Package:** `@langchain/community/caches/sqlite`

```typescript
import { SQLiteCache } from "@langchain/community/caches/sqlite";
import { setLLMCache } from "@langchain/core/caches";

setLLMCache(new SQLiteCache("./llm_cache.db"));
```

- Local file-based persistence
- No TTL support
- Good for local development and single-node production

### 6. MomentoCache

**Package:** `@langchain/community/caches/momento`

```typescript
import { MomentoCache } from "@langchain/community/caches/momento";
import { CacheClient, Configurations, CredentialProvider } from "@gomomento/sdk";

const client = await CacheClient.create({
  configuration: Configurations.Laptop.v1(),
  credentialProvider: CredentialProvider.fromEnvironmentVariable({
    environmentVariableName: "MOMENTO_API_KEY",
  }),
  defaultTtlSeconds: 3600,
});

const cache = await MomentoCache.fromProps({
  client,
  cacheName: "langchain",
  ttlSeconds: 300,
});

const model = new ChatOpenAI({ cache });
```

- Managed serverless cache service
- TTL support per entry

---

## Semantic Caches

Semantic caches match responses by **embedding similarity** rather than exact string matching. A new query hits the cache if a semantically similar query was previously answered.

### 7. RedisSemanticCache

**Package:** `langchain-redis`

```typescript
import { RedisSemanticCache } from "langchain-redis";
import { OpenAIEmbeddings } from "@langchain/openai";
import { setLLMCache } from "@langchain/core/caches";

setLLMCache(new RedisSemanticCache({
  redisUrl: "redis://localhost:6379",
  embedding: new OpenAIEmbeddings(),
  scoreThreshold: 0.85,  // cosine similarity (0–1)
}));
```

**How semantic lookup works:**
1. Incoming prompt is embedded via the configured `embedding` model
2. Vector similarity search on cached embeddings using cosine distance
3. If similarity score ≥ `scoreThreshold` → return cached response
4. If no match → call the LLM, cache the embedding + response pair

**Threshold tuning:**

| Threshold | Effect |
|-----------|--------|
| `0.70` | High hit rate; risk of wrong answers for different-intent queries |
| `0.85` | Good balance for FAQ/support use cases (community-validated default) |
| `0.90` | Low false positives; lower hit rate |
| `0.95` | Near-exact matching; minimal benefit over exact cache |

**Production data (community-verified):**
- Exact string matching: ~12% cache hit rate in production
- Semantic caching at 0.85 threshold: 40–80% cost reduction reported
- Embedding cost: ~$8/month for hundreds of daily users (negligible vs LLM savings)

### 8. CassandraSemanticCache

**Package:** `@langchain/community/caches/cassandra`

```typescript
import { CassandraSemanticCache } from "@langchain/community/caches/cassandra";
import { OpenAIEmbeddings } from "@langchain/openai";

const cache = new CassandraSemanticCache({
  session: cassandraClient,
  table: "llm_cache",
  embedding: new OpenAIEmbeddings(),
  scoreThreshold: 0.85,
});

setLLMCache(cache);
```

- Cassandra or AstraDB (DataStax) backend
- `delete_by_document_id()` for targeted cache invalidation
- High-write distributed workloads

---

## Cache Comparison Table

| Cache | Package | Type | Persistence | TTL | Edge | Best For |
|-------|---------|------|-------------|-----|------|----------|
| `InMemoryCache` | `@langchain/core` | Exact | No | No | Yes | Testing |
| `SQLiteCache` | `@langchain/community` | Exact | SQLite | No | No | Local prod |
| `RedisCache` | `@langchain/community` | Exact | Redis | Yes | No | Production |
| `UpstashRedisCache` | `@langchain/community` | Exact | Upstash | Yes | Yes | Serverless |
| `CloudflareKVCache` | `@langchain/cloudflare` | Exact | Workers KV | No (native) | Yes | CF Workers |
| `MomentoCache` | `@langchain/community` | Exact | Momento | Yes | Yes | Managed serverless |
| `RedisSemanticCache` | `langchain-redis` | Semantic | Redis | Yes | No | FAQ / support |
| `CassandraSemanticCache` | `@langchain/community` | Semantic | Cassandra | Yes | No | Distributed |

---

## TTL Configuration Reference

| Cache | TTL Support | How to Set | Unit |
|-------|-------------|-----------|------|
| `InMemoryCache` | No | — | — |
| `RedisCache` (ioredis) | Yes | `new RedisCache(client, { ttl: 60 })` | Seconds |
| `UpstashRedisCache` | Yes | `new UpstashRedisCache({ config, ttl: 3600 })` | Seconds |
| `CloudflareKVCache` | No (native) | Via Workers KV API | — |
| `SQLiteCache` | No | — | — |
| `MomentoCache` | Yes | `fromProps({ ..., ttlSeconds: 300 })` | Seconds |
| `RedisSemanticCache` | Yes | Constructor `ttlSeconds` | Seconds |

**Production TTL recommendations:**
- Time-sensitive content (pricing, status): 60–300 seconds
- General FAQ responses: 3600–86400 seconds (1 hour to 1 day)
- Stable knowledge content: 604800 seconds (7 days)
- User-specific content: Short TTL or no cache

---

## Key Encoding

All LangChain caches use `HashKeyEncoder` from `@langchain/core/utils/hash`. The default encoder computes **SHA-256** of `prompt + llmKey`:

```typescript
// Fix deprecation warning about insecure key hashing
const cache = new RedisCache(redisClient);
cache.makeDefaultKeyEncoder(); // Re-initializes with secure SHA-256 encoder

// Custom key encoder
const myEncoder = (prompt: string, llmKey: string): string =>
  `custom:${sha256(prompt + llmKey)}`;
const cache = new RedisCache(redisClient, { keyEncoder: myEncoder });
```

---

## Production Cache Patterns

### Pattern 1: Global cache with TTL

```typescript
import { setLLMCache } from "@langchain/core/caches";
import { RedisCache } from "@langchain/community/caches/ioredis";
import { Redis } from "ioredis";

const redis = new Redis(process.env.REDIS_URL!);
setLLMCache(new RedisCache(redis, { ttl: 3600 }));
```

### Pattern 2: Per-model cache with different TTLs

```typescript
import { ChatOpenAI } from "@langchain/openai";

// Stable knowledge model — long TTL
const knowledgeModel = new ChatOpenAI({
  model: "gpt-4o-mini",
  cache: new RedisCache(redis, { ttl: 86400 }), // 24 hours
});

// Dynamic/user-specific model — no cache
const dynamicModel = new ChatOpenAI({
  model: "gpt-4o-mini",
  cache: false,
});
```

### Pattern 3: Semantic cache for FAQ workloads

```typescript
import { RedisSemanticCache } from "langchain-redis";
import { OpenAIEmbeddings } from "@langchain/openai";

setLLMCache(new RedisSemanticCache({
  redisUrl: process.env.REDIS_URL!,
  embedding: new OpenAIEmbeddings({ modelName: "text-embedding-3-small" }),
  scoreThreshold: 0.85,
  ttlSeconds: 86400,
}));
```

### Pattern 4: Redis as both LLM cache and LangGraph checkpointer

Redis serves both roles from a single instance. These are different packages:

```typescript
import { Redis } from "ioredis";
import { RedisCache } from "@langchain/community/caches/ioredis";
import { RedisSaver } from "@langchain/langgraph-checkpoint-redis";
import { setLLMCache } from "@langchain/core/caches";

const redis = new Redis(process.env.REDIS_URL!);

// LLM response caching (exact match, 1 hour TTL)
setLLMCache(new RedisCache(redis, { ttl: 3600 }));

// LangGraph checkpoint storage (7 day TTL)
const checkpointer = new RedisSaver({
  url: process.env.REDIS_URL!,
  ttlSeconds: 7 * 24 * 60 * 60,
});

// IMPORTANT: Do NOT use InMemoryCache + MemorySaver together — they conflict
```

---

## CacheBackedEmbeddings

Caches embedding computations to avoid redundant API calls. Uses the **LangChain BaseStore** (`@langchain/core/stores`) interface, not the LangGraph one.

```typescript
import { CacheBackedEmbeddings } from "langchain/embeddings/cache_backed";
import { OpenAIEmbeddings } from "@langchain/openai";
import { InMemoryStore } from "@langchain/core/stores";
import { LocalFileStore } from "@langchain/community/storage/file_system";

const underlyingEmbeddings = new OpenAIEmbeddings();

// In-memory (dev/test)
const cacheBackedEmbeddings = CacheBackedEmbeddings.fromBytesStore(
  underlyingEmbeddings,
  new InMemoryStore(),
  { namespace: underlyingEmbeddings.modelName }
);

// File-based (persisted across restarts)
const fileStore = await LocalFileStore.fromPath("./embeddings-cache");
const persistedEmbeddings = CacheBackedEmbeddings.fromBytesStore(
  underlyingEmbeddings,
  fileStore,
  { namespace: "text-embedding-3-small" }
);

// Redis-backed (production)
import { RedisStore } from "@langchain/community/storage/ioredis";
import { Redis } from "ioredis";

const redisStore = new RedisStore({ client: new Redis(), sessionTTL: 86400 });
const redisEmbeddings = CacheBackedEmbeddings.fromBytesStore(
  underlyingEmbeddings,
  redisStore,
  { namespace: "text-embedding-3-small" }
);
```

`CacheBackedEmbeddings.fromBytesStore` signature:

```typescript
CacheBackedEmbeddings.fromBytesStore(
  underlyingEmbeddings: Embeddings,
  documentEmbeddingStore: BaseStore<string, Uint8Array>,
  options?: {
    namespace?: string;        // prefix for cache keys — use model name to avoid collisions
    batchSize?: number;        // default: 512 — number of texts to embed per batch
  }
): CacheBackedEmbeddings
```

**Use with VectorStore:**

```typescript
import { FaissStore } from "@langchain/community/vectorstores/faiss";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";

const splitter = new RecursiveCharacterTextSplitter({ chunkSize: 1000 });
const docs = await splitter.createDocuments(["Your document text here..."]);

const vectorStore = await FaissStore.fromDocuments(docs, cacheBackedEmbeddings);
// First call: embeds all docs, writes to cache
// Subsequent calls with same docs: cache hit, no API calls
```

---

## LangChain BaseStore Implementations (for CacheBackedEmbeddings)

These implement the `BaseStore<string, Uint8Array>` interface — distinct from the LangGraph `BaseStore`.

### InMemoryStore (`@langchain/core/stores`)

```typescript
import { InMemoryStore } from "@langchain/core/stores";
import { BaseMessage } from "@langchain/core/messages";

const kvStore = new InMemoryStore<BaseMessage>();
await kvStore.mset([["key1", new HumanMessage("Hello")]]);
const values = await kvStore.mget(["key1"]);
await kvStore.mdelete(["key1"]);
for await (const key of kvStore.yieldKeys("prefix:")) { /* ... */ }
```

### LocalFileStore

```typescript
import { LocalFileStore } from "@langchain/community/storage/file_system";

const store = await LocalFileStore.fromPath("./local_file_store");
const encoder = new TextEncoder();
const decoder = new TextDecoder();

await store.mset([["key1", encoder.encode("value1")]]);
const values = await store.mget(["key1"]);
console.log(values.map(v => decoder.decode(v)));
```

- Persists to filesystem as JSON files
- Values serialized as `Uint8Array`
- Not suitable for multi-process or distributed deployments

### RedisStore (ioredis)

```typescript
import { RedisStore } from "@langchain/community/storage/ioredis";
import { Redis } from "ioredis";

const store = new RedisStore({
  client: new Redis({ host: "localhost", port: 6379 }),
  sessionTTL: 86400,  // optional TTL in seconds
});

const encoder = new TextEncoder();
await store.mset([["key1", encoder.encode(JSON.stringify({ data: "value1" }))]]);
```

### UpstashRedisStore

```typescript
import { UpstashRedisStore } from "@langchain/community/storage/upstash_redis";

const store = new UpstashRedisStore({
  config: {
    url: process.env.UPSTASH_REDIS_REST_URL!,
    token: process.env.UPSTASH_REDIS_REST_TOKEN!,
  },
});
```

- Serverless Redis via HTTP REST; edge-compatible
- No native TTL on `mset` (manage via Upstash REST API)

### VercelKVStore

```typescript
import { createClient } from "@vercel/kv";
import { VercelKVStore } from "@langchain/community/storage/vercel_kv";

const store = new VercelKVStore({
  client: createClient({
    url: process.env.VERCEL_KV_API_URL!,
    token: process.env.VERCEL_KV_API_TOKEN!,
  }),
});
```

---

## Store Selection Guide

| Use Case | Recommended | Reason |
|----------|-------------|--------|
| Dev / unit tests (LangGraph) | `InMemoryStore` (@langchain/langgraph) | Zero setup, namespace + search API |
| Dev — embeddings caching | `InMemoryStore` (@langchain/core) | `mset`/`mget` API for `CacheBackedEmbeddings` |
| Local file persistence | `LocalFileStore` | Simple file-based; no external service |
| Production — relational queries | `PostgresStore` | Full persistence, pgvector, ACID |
| High-throughput production | `RedisStore` (ioredis) | Fast, TTL support |
| Serverless / edge (Vercel) | `VercelKVStore` | Native Vercel KV integration |
| Serverless / edge (general) | `UpstashRedisStore` | HTTP REST, works everywhere |
| LLM cache — local dev | `InMemoryCache` | Zero setup |
| LLM cache — production | `RedisCache` | TTL, persistence, battle-tested |
| LLM cache — edge/serverless | `UpstashRedisCache` | HTTP REST |
| LLM cache — FAQ-heavy | `RedisSemanticCache` | Semantic matching, 40–80% cost savings |
| Embeddings caching — prod | `CacheBackedEmbeddings` + `RedisStore` | Persistent, TTL-able |

---

## Known Pitfalls

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| LangGraph store vs LangChain store API mismatch | `mget`/`mset` vs `put`/`get` methods; calls fail at runtime | They are NOT interchangeable — use separate instances for each purpose |
| `InMemoryCache` + `MemorySaver` conflict | Cache stops working; internal state management conflict | Use `RedisCache` + `RedisSaver` or Postgres for both |
| `store.setup()` not called on `PostgresStore` | Tables don't exist; throws on first operation | Always call `await store.setup()` at app startup |
| Semantic cache false positives ("SF" vs "NY" weather) | Semantically similar phrasing, different constraint → wrong cached answer | Raise threshold to 0.90+ or add constraint extraction layer |
| Infinite namespace growth | `listNamespaces()` returns thousands of orphaned namespaces | Implement TTL retention metadata + periodic cleanup job |
| No namespace on `CacheBackedEmbeddings` | Collisions when switching embedding models | Always set `namespace: modelName` in `fromBytesStore` options |
| Redis Cluster via `redis_url` | `RedisCache` or `RedisStore` fails to connect | Use pre-configured ioredis `Cluster` client instance |
| Concurrent writes without versioning | Race conditions on shared namespace/key (e.g., profile updates) | Include `version` field and implement read-check-write pattern |
| GDPR deletion misses nested org namespaces | User data persists after deletion request | Query both `["user", userId]` and org namespaces; see GDPR section |
| `index: false` on sensitive documents forgotten | PII accidentally embedded and made searchable | Default policy: always set `index: false` for documents containing PII; opt in explicitly |
| `dims` mismatch in `IndexConfig` | Vector search fails or returns garbage scores | `dims` MUST match the embedding model's actual output dimensions |
| Score threshold too low in `RedisSemanticCache` | Semantically similar but different-intent queries return wrong cached answers | Start at 0.85; tune up if false positives observed in production logs |
