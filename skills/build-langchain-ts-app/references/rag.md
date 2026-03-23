# RAG — Retrieval-Augmented Generation

> Verified against langchain@1.2.35, @langchain/core@1.1.34, @langchain/openai@1.3.0, @langchain/textsplitters@1.0.1 — March 2026
> All code TypeScript. Import paths exact.

---

## RAG Architecture: Which Pattern to Choose

| Architecture | Control | Latency | Best For |
|---|---|---|---|
| **2-Step RAG** (`createRetrievalChain`) | Fixed order, predictable | Fast | FAQ bots, docs search |
| **Agentic RAG** (retriever as tool) | Agent decides when/whether to retrieve | Variable | Research assistants, multi-tool |
| **Hybrid RAG** (ensemble + query enhancement) | Medium | Variable | Domain Q&A with quality gates |

**Decision tree:**
```
Corpus < 100k tokens?  → Stuff full text into context window. No RAG needed.
Every query needs retrieval + latency matters?  → 2-Step RAG (createRetrievalChain)
Queries unpredictable, multiple sources?  → Agentic RAG (tool-based)
Need keyword + semantic coverage?  → Hybrid with EnsembleRetriever
```

Core pipeline: `Loaders → Splitters → Embeddings → VectorStore → Retriever → LLM`

---

## 1. Document Loaders

All loaders produce `Document[]` with `pageContent: string` and `metadata: Record<string, any>`.

### File Loaders (15 types)

| Loader | Import Path | Required Package | Key Option |
|--------|------------|-----------------|------------|
| `PDFLoader` | `@langchain/community/document_loaders/fs/pdf` | `pdf-parse` | `splitPages: true` |
| `CSVLoader` | `@langchain/community/document_loaders/fs/csv` | `d3-dsv@2` | `column:` for single column |
| `JSONLoader` | `@langchain/classic/document_loaders/fs/json` | `langchain` | JSON pointer array |
| `JSONLinesLoader` | `@langchain/classic/document_loaders/fs/json` | `langchain` | pointer per line |
| `TextLoader` | `@langchain/classic/document_loaders/fs/text` | `langchain` | — |
| `DocxLoader` | `@langchain/community/document_loaders/fs/docx` | `mammoth` | `type: "doc"` for legacy |
| `EPubLoader` | `@langchain/community/document_loaders/fs/epub` | `epub2`, `html-to-text` | `splitChapters: true` |
| `PPTXLoader` | `@langchain/community/document_loaders/fs/pptx` | `officeparser` | — |
| `SRTLoader` | `@langchain/community/document_loaders/fs/srt` | `@langchain/community` | — |
| `DirectoryLoader` | `@langchain/classic/document_loaders/fs/directory` | `langchain` | extension→loader map |
| `UnstructuredLoader` | `@langchain/community/document_loaders/fs/unstructured` | `@langchain/community` | `apiKey` or `unstructuredAPIURL` |
| `UnstructuredDirectoryLoader` | `@langchain/community/document_loaders/fs/unstructured` | `@langchain/community` | same |
| `OpenAIWhisperAudio` | `@langchain/community/document_loaders/fs/openai_whisper_audio` | `openai` | `transcriptionCreateParams` |
| `ChatGPTLoader` | `@langchain/community/document_loaders/fs/chatgpt` | `@langchain/community` | — |
| `NotionLoader` (Markdown) | `@langchain/community/document_loaders/fs/notion` | `@langchain/community` | directory path |

```typescript
import { PDFLoader } from "@langchain/community/document_loaders/fs/pdf";
import { DirectoryLoader } from "@langchain/classic/document_loaders/fs/directory";
import { TextLoader } from "@langchain/classic/document_loaders/fs/text";
import { CSVLoader } from "@langchain/community/document_loaders/fs/csv";

// PDF — one Document per page
const pdf = new PDFLoader("./report.pdf");
const pdfDocs = await pdf.load();
// metadata: { source, pdf: { totalPages }, loc: { pageNumber } }

// Mixed directory
const dir = new DirectoryLoader("./data/", {
  ".txt": (path) => new TextLoader(path),
  ".csv": (path) => new CSVLoader(path),
  ".pdf": (path) => new PDFLoader(path),
});
const allDocs = await dir.load();
```

### Web Loaders (25+ types)

| Loader | JS Execution | Auth | Best For |
|--------|-------------|------|----------|
| `CheerioWebBaseLoader` | No | None | Static HTML, docs sites |
| `PuppeteerWebBaseLoader` | Yes (Chrome) | None | SPAs, JS-rendered pages |
| `PlaywrightWebBaseLoader` | Yes (multi-browser) | None | SPAs, parallel scraping |
| `RecursiveUrlLoader` | No | None | Crawl a doc site up to N levels deep |
| `SitemapLoader` | No | None | Full site from sitemap.xml |
| `GithubRepoLoader` | No | GitHub token | Source code repositories |
| `NotionAPILoader` | No | Notion token | Notion pages and databases |
| `ConfluencePagesLoader` | No | Confluence token | Confluence spaces |
| `YoutubeLoader` | No | None | Video transcripts (captions) |
| `S3Loader` | No | AWS credentials | Files from S3 via Unstructured |
| `FireCrawlLoader` | Yes (cloud) | FireCrawl key | JS-rendered, managed crawl |
| `JiraProjectLoader` | No | Jira token | Jira project issues |
| `AirtableLoader` | No | Airtable token | Airtable base rows |
| `BrowserbaseLoader` | Yes (cloud) | Browserbase key | Cloud browser rendering |

```typescript
import { CheerioWebBaseLoader } from "@langchain/community/document_loaders/web/cheerio";
import { RecursiveUrlLoader } from "@langchain/community/document_loaders/web/recursive_url";
import { compile } from "html-to-text";

// Static page with CSS selector
const page = new CheerioWebBaseLoader("https://docs.example.com", { selector: "p" });
const docs = await page.load();

// Recursive crawl (2 levels deep)
const crawler = new RecursiveUrlLoader("https://docs.example.com/", {
  extractor: compile({ wordwrap: 130 }),
  maxDepth: 2,
  excludeDirs: ["/api/", "/changelog/"],
  preventOutside: true,
});
const crawled = await crawler.load();
```

---

## 2. Text Splitters

All splitters from `@langchain/textsplitters`. Install: `npm install @langchain/textsplitters`.

### 8 Splitter Types

| Splitter | Size Control | Semantic | Cost | Best For |
|----------|------------|----------|------|----------|
| `RecursiveCharacterTextSplitter` | Characters | Partial (separator order) | Free | **Default for 80% of use cases** |
| `CharacterTextSplitter` | Characters | No | Free | Uniform text with known delimiter |
| `TokenTextSplitter` | Tokens (tiktoken) | No | Free | Strict token budget adherence |
| `RecursiveCharacterTextSplitter.fromLanguage()` | Characters | Yes (syntax) | Free | Source code repositories |
| `MarkdownHeaderTextSplitter` | Header boundaries | Yes (structure) | Free | Markdown docs, wikis |
| `HTMLHeaderTextSplitter` | Header boundaries | Yes (structure) | Free | HTML pages with `h1`–`h6` |
| `RecursiveJsonSplitter` | JSON string size | Yes (structure) | Free | Large JSON API responses |
| `SemanticChunker` | Semantic similarity | Yes (embeddings) | API cost | Dense unstructured text |

```typescript
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";
import { TokenTextSplitter } from "@langchain/textsplitters";
import { MarkdownHeaderTextSplitter } from "@langchain/textsplitters";
import { SemanticChunker } from "@langchain/textsplitters";
import { OpenAIEmbeddings } from "@langchain/openai";

// Default choice — respects paragraph, sentence, word boundaries in order
const recursive = new RecursiveCharacterTextSplitter({
  chunkSize: 1000,
  chunkOverlap: 200,
});
const chunks = await recursive.splitDocuments(docs);

// Token-accurate — guarantees within model token limits
const tokens = new TokenTextSplitter({
  encodingName: "cl100k_base",  // GPT-4 / text-embedding-3-*
  chunkSize: 512,
  chunkOverlap: 50,
});

// Language-aware — splits on function/class boundaries
const ts = RecursiveCharacterTextSplitter.fromLanguage("typescript", {
  chunkSize: 500,
  chunkOverlap: 0,
});
// Also: "python", "javascript", "java", "go", "rust", "markdown", "html", ...

// Markdown — headers become metadata, not pageContent
const md = new MarkdownHeaderTextSplitter({
  headersToSplitOn: [
    { level: 1, source: "#", metadataKey: "header1" },
    { level: 2, source: "##", metadataKey: "header2" },
  ],
});
const mdDocs = await md.splitText(markdownText);
// docs[0].metadata => { header1: "Introduction", header2: "Overview" }

// Semantic — uses embedding similarity to find topic breakpoints
const semantic = new SemanticChunker(new OpenAIEmbeddings(), {
  breakpointThresholdType: "percentile",  // "percentile" | "standard_deviation" | "interquartile"
  breakpointThresholdAmount: 90,
});
```

### Chunking Strategy Guide

| Query Type | Chunk Size | Overlap | Strategy |
|-----------|-----------|---------|----------|
| Factoid / short answer | 256–512 tokens | 50 tokens | RecursiveCharacter |
| Analytical / multi-part | 1024+ tokens | 10% | RecursiveCharacter |
| Mixed workload (default) | 400–512 tokens | 100 chars | RecursiveCharacter |
| Source code | 100–200 chars | 0 | fromLanguage() |
| Markdown docs | 500 tokens | 50 | MarkdownHeaderTextSplitter |
| Dense research text | Variable | None | SemanticChunker |
| Long docs needing context | child 200 / parent 2000 | 0 on child | ParentDocumentRetriever |

**Overlap rules**: Start at 10–20% of chunk size. Benefits diminish beyond 20%. Zero overlap on child chunks in parent-child patterns.

---

## 3. Embeddings

### Provider Overview (13 key providers)

| Provider | Class | Package | Default Model | Dims |
|---|---|---|---|---|
| OpenAI | `OpenAIEmbeddings` | `@langchain/openai` | `text-embedding-3-large` | 3072 |
| Azure OpenAI | `AzureOpenAIEmbeddings` | `@langchain/openai` | deployment name | varies |
| Google GenAI | `GoogleGenerativeAIEmbeddings` | `@langchain/google-genai` | `gemini-embedding-001` | 768 |
| Google Vertex | `VertexAIEmbeddings` | `@langchain/google-vertexai` | `gemini-embedding-001` | 768 |
| AWS Bedrock | `BedrockEmbeddings` | `@langchain/aws` | `amazon.titan-embed-text-v1` | 1536 |
| Cohere | `CohereEmbeddings` | `@langchain/cohere` | `embed-english-v3.0` | 1024 |
| Ollama (local) | `OllamaEmbeddings` | `@langchain/ollama` | `mxbai-embed-large` | 1024 |
| HuggingFace | `HuggingFaceInferenceEmbeddings` | `@langchain/community` | `BAAI/bge-base-en-v1.5` | 768 |
| MistralAI | `MistralAIEmbeddings` | `@langchain/mistralai` | `mistral-embed` | 1024 |
| Voyage AI | `VoyageEmbeddings` | `@langchain/community` | `voyage-2` | 1024 |
| Nomic | `NomicEmbeddings` | `@langchain/nomic` | `nomic-embed-text-v1.5` | 768 |
| Fireworks | `FireworksEmbeddings` | `@langchain/community` | `nomic-ai/nomic-embed-text-v1.5` | 768 |
| HuggingFace Transformers | `HuggingFaceTransformersEmbeddings` | `@langchain/community` | `all-MiniLM-L6-v2` | 384 |

**Model selection guide:**
- Best quality (production): `text-embedding-3-large` (3072d) — supports Matryoshka dimension reduction
- Cost/quality balance: `text-embedding-3-small` (1536d, 5× cheaper than large)
- Free / local: Ollama `mxbai-embed-large` or HF `all-MiniLM-L6-v2`
- Multilingual: Cohere `embed-multilingual-v3.0` (100+ languages)
- Code search: Voyage `voyage-code-2`

```typescript
import { OpenAIEmbeddings } from "@langchain/openai";

const embeddings = new OpenAIEmbeddings({
  model: "text-embedding-3-large",
  batchSize: 512,       // docs per API call (max 2048)
  dimensions: 1536,     // Matryoshka reduction (text-embedding-3-* only)
  maxRetries: 6,
  stripNewLines: true,
});

const queryVec: number[] = await embeddings.embedQuery("What is RAG?");
const docVecs: number[][] = await embeddings.embedDocuments(["Doc A", "Doc B"]);
```

**Critical rule**: Use the SAME embedding model for indexing and querying. Mixing models produces meaningless similarity scores.

### CacheBackedEmbeddings

Avoids re-embedding documents by caching vectors to a key-value store. Critical for production cost reduction.

```typescript
import { CacheBackedEmbeddings } from "@langchain/classic/embeddings/cache_backed";
import { InMemoryStore } from "@langchain/core/stores";
import { OpenAIEmbeddings } from "@langchain/openai";

const underlying = new OpenAIEmbeddings({ model: "text-embedding-3-small" });
const store = new InMemoryStore<number[]>();

const cached = CacheBackedEmbeddings.fromBytesStore(underlying, store, {
  namespace: underlying.model,  // prevents key collision when switching models
});

// First run: calls OpenAI API and caches
// Second run: served from cache instantly
const vectorStore = await MemoryVectorStore.fromDocuments(docs, cached);

// Production: persistent Redis cache
import { RedisByteStore } from "@langchain/community/storage/ioredis";
import Redis from "ioredis";
const redis = new Redis({ host: "localhost", port: 6379 });
const persistentStore = new RedisByteStore({ client: redis });
const prodCached = CacheBackedEmbeddings.fromBytesStore(underlying, persistentStore, {
  namespace: "v1_text-embedding-3-small",
});
```

---

## 4. Vector Stores

### Comparison Matrix (17 stores)

| Store | Package | Hosting | MMR | Filter | Namespace | Delete by IDs | Hybrid Search |
|-------|---------|---------|-----|--------|-----------|---------------|---------------|
| `InMemoryVectorStore` | `@langchain/core` | In-process | ✓ | ✓ | ✗ | ✓ | ✗ |
| `MemoryVectorStore` (legacy) | `@langchain/classic` | In-process | ✗ | ✓ | ✗ | ✗ | ✗ |
| `FAISS` | `@langchain/community` | Local disk | ✓ | ✗ | ✗ | ✓ | ✗ |
| `Chroma` | `@langchain/community` | Local/Cloud | ✗ | ✓ | via collection | ✓ | ✗ |
| `Pinecone` | `@langchain/pinecone` | Cloud | ✗ | ✓ | ✓ | ✓ | ✗ |
| `Qdrant` | `@langchain/qdrant` | Self/Cloud | ✗ | ✓ | via collection | ✗ | ✓ |
| `PGVector` | `@langchain/community` | Self/Cloud | ✓ | ✓ | via tableName | ✓ | ✗ |
| `Supabase` | `@langchain/community` | Cloud | ✗ | ✓ | ✗ | ✓ | ✗ |
| `Weaviate` | `@langchain/weaviate` | Self/Cloud | ✗ | ✓ | via indexName | ✓ | ✓ |
| `Redis` | `@langchain/redis` | Self/Cloud | ✓ | ✓ | via indexName | ✓ | ✗ |
| `MongoDB Atlas` | `@langchain/mongodb` | Cloud | ✗ | ✓ | ✗ | ✓ | ✓ |
| `Upstash` | `@langchain/community` | Cloud serverless | ✗ | ✓ | ✓ | ✓ | ✗ |
| `LanceDB` | `@langchain/community` | Local disk | ✗ | ✗ | ✗ | ✓ | ✗ |
| `Turbopuffer` | `@langchain/community` | Cloud serverless | ✗ | ✓ | ✓ | ✓ | ✓ |
| `Cloudflare Vectorize` | `@langchain/cloudflare` | Edge/Cloud | ✗ | ✓ | ✗ | ✓ | ✗ |
| `Milvus` | `@langchain/classic` | Self/Cloud | ✓ | ✓ | via collection | ✓ | ✓ |
| `Azure AI Search` | `@langchain/community` | Cloud | ✗ | ✓ | ✗ | ✓ | ✓ |

**Selection guide:**
- Dev/testing → `InMemoryVectorStore` (modern) or `MemoryVectorStore` (legacy)
- Existing PostgreSQL → `PGVectorStore`
- Serverless scale → `Pinecone` (namespaces, managed)
- Self-hosted + rich filtering → `Qdrant` (Rust, low memory)
- Hybrid BM25+vector → `EnsembleRetriever` or `SupabaseHybridSearch`
- Low-latency with TTL → `Redis`

```typescript
import { InMemoryVectorStore } from "@langchain/core/vectorstores";
import { FaissStore } from "@langchain/community/vectorstores/faiss";
import { PineconeStore } from "@langchain/pinecone";
import { PGVectorStore } from "@langchain/community/vectorstores/pgvector";
import { QdrantVectorStore } from "@langchain/qdrant";
import { OpenAIEmbeddings } from "@langchain/openai";

const emb = new OpenAIEmbeddings({ model: "text-embedding-3-small" });

// In-memory (dev)
const mem = await InMemoryVectorStore.fromDocuments(docs, emb);

// FAISS (local production — Node.js only, no filter support)
const faiss = await FaissStore.fromDocuments(docs, emb);
await faiss.save("./faiss_index");
const loaded = await FaissStore.load("./faiss_index", emb);

// Pinecone (managed cloud)
import { Pinecone } from "@pinecone-database/pinecone";
const pc = new Pinecone();  // reads PINECONE_API_KEY
const pinecone = await PineconeStore.fromExistingIndex(emb, {
  pineconeIndex: pc.Index(process.env.PINECONE_INDEX!),
  namespace: "prod-v1",
  maxConcurrency: 5,
});

// PGVector (existing Postgres)
const pg = await PGVectorStore.initialize(emb, {
  postgresConnectionOptions: { connectionString: process.env.DATABASE_URL! },
  tableName: "langchain_vectors",
  distanceStrategy: "cosine",
});
await pg.createHnswIndex({ dimensions: 1536, m: 16, efConstruction: 64 });
```

### Metadata Filtering by Store

```typescript
// Chroma: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin, $and, $or
store.asRetriever({ filter: { $and: [{ source: { $eq: "docs" } }, { year: { $gte: 2023 } }] } });

// Pinecone: exact match + $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
store.asRetriever({ filter: { category: { $in: ["technical", "api"] }, version: "v2" } });

// Qdrant: native DSL (must prefix with "metadata.")
store.asRetriever({ filter: { must: [{ key: "metadata.source", match: { value: "docs" } }] } });

// PGVector: plain object equality
store.asRetriever({ filter: { source: "docs", language: "en" } });

// MongoDB Atlas: MQL operators
store.asRetriever({ filter: { "metadata.source": { $regex: "^docs" } } });
```

---

## 5. Retriever Types (11)

All retrievers implement `BaseRetriever` with `invoke(query: string): Promise<Document[]>`.

### VectorStoreRetriever (default)

```typescript
const retriever = vectorStore.asRetriever({
  k: 4,                          // results to return (default 4)
  searchType: "similarity",      // "similarity" | "mmr"
  filter: { source: "docs" },    // optional store-specific filter
  searchKwargs: { fetchK: 20, lambda: 0.5 },  // MMR params
});
```

### BM25Retriever (keyword search)

```typescript
import { BM25Retriever } from "@langchain/community/retrievers/bm25";
// npm install okapibm25

const bm25 = BM25Retriever.fromDocuments(docs);
bm25.k = 4;
bm25.includeScore = true;
const results = await bm25.invoke("keyword query");
```

### MultiQueryRetriever (LLM query expansion)

Generates N query variants, retrieves for each, deduplicates. Overcomes single-query phrasing limits.

```typescript
import { MultiQueryRetriever } from "langchain/retrievers/multi_query";
import { ChatOpenAI } from "@langchain/openai";

const mq = MultiQueryRetriever.fromLLM({
  llm: new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 }),
  retriever: vectorStore.asRetriever({ k: 3 }),
  k: 3,                        // number of query variants to generate
  includeOriginalQuery: false,
});
const results = await mq.invoke("tell me about AI agents");
```

### SelfQueryRetriever (LLM-generated metadata filters)

Parses natural language into semantic query + structured metadata filter automatically.

```typescript
import { SelfQueryRetriever } from "langchain/retrievers/self_query";
import { ChromaTranslator } from "@langchain/community/structured_query/chroma";
import type { AttributeInfo } from "langchain/chains/query_constructor";

const attributeInfo: AttributeInfo[] = [
  { name: "genre", description: "Movie genre", type: "string" },
  { name: "year", description: "Release year", type: "integer" },
  { name: "rating", description: "1-10 rating", type: "float" },
];

const selfQuery = new SelfQueryRetriever({
  llm: new ChatOpenAI({ model: "gpt-4o", temperature: 0 }),
  vectorStore: chromaStore,
  documentContents: "Brief movie summary",
  attributeInfo,
  structuredQueryTranslator: new ChromaTranslator(),
});
// "action movies from after 2010 with rating above 8"
// → vectorQuery="action movies" + filter={genre:"action", year:{$gt:2010}, rating:{$gt:8}}

// Supported translators: ChromaTranslator, PineconeTranslator, WeaviateTranslator,
// SupabaseTranslator, PGVectorTranslator
```

### ContextualCompressionRetriever (reranking)

Wraps any retriever; compressor filters/reranks results post-retrieval.

```typescript
import { ContextualCompressionRetriever } from "langchain/retrievers/contextual_compression";
import { CohereRerank } from "@langchain/cohere";

// Cohere Rerank (recommended for production)
const reranker = new CohereRerank({
  apiKey: process.env.COHERE_API_KEY,
  topN: 3,
  model: "rerank-english-v3.0",
});

const compressed = new ContextualCompressionRetriever({
  baseCompressor: reranker,
  baseRetriever: vectorStore.asRetriever({ k: 20 }),  // fetch 20, rerank to top 3
});
// Available compressors: LLMChainExtractor, LLMChainFilter, EmbeddingsFilter, CohereRerank, DocumentCompressorPipeline
```

### ParentDocumentRetriever (small chunks → large context)

Indexes small child chunks (precise retrieval), returns larger parent docs (full context for LLM).

```typescript
import { ParentDocumentRetriever } from "langchain/retrievers/parent_document";
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";
import { InMemoryStore } from "langchain/storage/in_memory";

const retriever = new ParentDocumentRetriever({
  vectorstore: new InMemoryVectorStore(emb),
  docstore: new InMemoryStore(),
  childSplitter: new RecursiveCharacterTextSplitter({ chunkSize: 200, chunkOverlap: 0 }),
  parentSplitter: new RecursiveCharacterTextSplitter({ chunkSize: 2000, chunkOverlap: 200 }),
});
await retriever.addDocuments(docs);
const parentDocs = await retriever.invoke("query");  // returns parent-sized chunks
```

### MultiVectorRetriever (summary-based retrieval)

Embeds multiple representations per document (summaries, hypothetical questions) and links back to full docs.

```typescript
import { MultiVectorRetriever } from "langchain/retrievers/multi_vector";
import { InMemoryStore } from "langchain/storage/in_memory";
import { v4 as uuidv4 } from "uuid";
import { Document } from "@langchain/core/documents";

const ids = docs.map(() => uuidv4());
const retriever = new MultiVectorRetriever({
  vectorstore: new InMemoryVectorStore(emb),
  docstore: new InMemoryStore(),
  idKey: "doc_id",
});
const summaries = await Promise.all(docs.map(async (doc, i) => {
  const summary = await llm.invoke(`Summarize in 100 words: ${doc.pageContent}`);
  return new Document({ pageContent: summary.content as string, metadata: { doc_id: ids[i] } });
}));
await retriever.vectorstore.addDocuments(summaries);
await retriever.docstore.mset(ids.map((id, i) => [id, docs[i]]));
// Searches summaries, returns full original docs
```

### EnsembleRetriever (Hybrid BM25 + Vector)

Combines multiple retrievers using Reciprocal Rank Fusion (RRF).

```typescript
import { EnsembleRetriever } from "langchain/retrievers/ensemble";

const bm25 = BM25Retriever.fromDocuments(docs);
bm25.k = 4;
const vector = vectorStore.asRetriever({ k: 4 });

const ensemble = new EnsembleRetriever({
  retrievers: [bm25, vector],
  weights: [0.5, 0.5],   // must sum to 1.0
  c: 60,                  // RRF constant — higher = gentler reranking
});
// RRF score = Σ(weight / (rank + c)) — docs in multiple lists get boosted
```

### TimeWeightedVectorStoreRetriever

Weights scores by recency. Score = vector_score × (1 − decay)^(seconds_since_access).

```typescript
import { TimeWeightedVectorStoreRetriever } from "langchain/retrievers/time_weighted";

const twRetriever = new TimeWeightedVectorStoreRetriever({
  vectorStore,
  k: 10,
  decayRate: 0.01,       // per second; lower = documents stay "fresh" longer
  memoryStream: [],
});
await twRetriever.addDocuments([
  new Document({ pageContent: "...", metadata: { last_accessed_at: new Date() } }),
]);
```

### ScoreThresholdRetriever

Returns only documents above a minimum similarity score.

```typescript
import { ScoreThresholdRetriever } from "langchain/retrievers/score_threshold";

const threshold = ScoreThresholdRetriever.fromVectorStore(vectorStore, {
  minSimilarityScore: 0.8,
  maxK: 10,
  kIncrement: 2,
});
```

### HyDE Retriever (Hypothetical Document Embeddings)

LLM generates a hypothetical answer, embeds that answer instead of the query, retrieves real docs matching the hypothetical.

```typescript
import { HydeRetriever } from "@langchain/classic/retrievers/hyde";
import { OpenAI } from "@langchain/openai";

const hyde = new HydeRetriever({
  vectorStore,
  llm: new OpenAI({ temperature: 0 }),
  k: 2,
});
// Bridges query-document embedding gap for question-to-passage retrieval
```

---

## 6. RAG Chain Construction

### Two-Step RAG (createRetrievalChain)

```typescript
import { createRetrievalChain } from "langchain/chains/retrieval";
import { createStuffDocumentsChain } from "langchain/chains/combine_documents";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { ChatOpenAI } from "@langchain/openai";

const llm = new ChatOpenAI({ model: "gpt-4o-mini" });

const prompt = ChatPromptTemplate.fromMessages([
  ["system", "Answer based only on the context:\n\n{context}"],
  ["human", "{input}"],
]);

const docChain = await createStuffDocumentsChain({ llm, prompt });
const ragChain = await createRetrievalChain({ retriever, combineDocsChain: docChain });

const result = await ragChain.invoke({ input: "What is LangChain?" });
// result.answer — LLM response
// result.context — retrieved Document[]
// result.input — original question
```

### Document Combining Strategies

| Function | LLM Calls | Best For |
|---|---|---|
| `createStuffDocumentsChain` | 1 | ≤8 docs, simple Q&A |
| `createMapReduceDocumentsChain` | N+1 | 10–50 docs, cost-sensitive |
| `createRefineDocumentsChain` | N | Complex sequential reasoning |

```typescript
import { createMapReduceDocumentsChain } from "langchain/chains/combine_documents";

const mapReduceChain = await createMapReduceDocumentsChain({
  llm,
  combinePrompt: ChatPromptTemplate.fromMessages([
    ["system", "Combine these summaries: {context}"],
    ["human", "{input}"],
  ]),
});
const ragChain = await createRetrievalChain({
  retriever: vectorStore.asRetriever({ k: 20 }),
  combineDocsChain: mapReduceChain,
});
```

### Agentic RAG (retriever as tool)

```typescript
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { createReactAgent } from "@langchain/langgraph/prebuilt";

const retrieve = tool(
  async ({ query }: { query: string }) => {
    const results = await vectorStore.similaritySearch(query, 4);
    const content = results.map(d => `Source: ${d.metadata.source}\n${d.pageContent}`).join("\n\n---\n\n");
    return [content, results];
  },
  {
    name: "retrieve",
    description: "Search the knowledge base for relevant information.",
    schema: z.object({ query: z.string() }),
    responseFormat: "content_and_artifact",  // content for LLM + raw Document[] as artifact
  }
);

const agent = createReactAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  tools: [retrieve],
});
```

---

## 7. Conversational RAG

```typescript
import { createHistoryAwareRetriever } from "langchain/chains/history_aware_retriever";
import { createRetrievalChain } from "langchain/chains/retrieval";
import { createStuffDocumentsChain } from "langchain/chains/combine_documents";
import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";
import { RunnableWithMessageHistory } from "@langchain/core/runnables";
import { ChatMessageHistory } from "@langchain/core/chat_history";
import { ChatOpenAI } from "@langchain/openai";

const llm = new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 });

// 1. History-aware retriever: reformulates follow-up questions as standalone
const contextualizePrompt = ChatPromptTemplate.fromMessages([
  ["system", "Given chat history and latest question, formulate a standalone question. Return as-is if already standalone."],
  new MessagesPlaceholder("chat_history"),
  ["human", "{input}"],
]);
const historyAwareRetriever = await createHistoryAwareRetriever({
  llm,
  retriever: vectorStore.asRetriever({ k: 4 }),
  rephrasePrompt: contextualizePrompt,
});
// Behavior: empty chat_history → passes input directly; non-empty → LLM reformulates

// 2. QA chain with history in prompt
const qaPrompt = ChatPromptTemplate.fromMessages([
  ["system", "Answer using only the context:\n\n{context}\n\nIf not in context, say so."],
  new MessagesPlaceholder("chat_history"),
  ["human", "{input}"],
]);
const qaChain = await createStuffDocumentsChain({ llm, prompt: qaPrompt });

// 3. Full RAG chain
const ragChain = await createRetrievalChain({
  retriever: historyAwareRetriever,
  combineDocsChain: qaChain,
});

// 4. Wrap with automatic history management
const historyStore = new Map<string, ChatMessageHistory>();
const chainWithHistory = new RunnableWithMessageHistory({
  runnable: ragChain,
  getMessageHistory: async (sessionId: string) => {
    if (!historyStore.has(sessionId)) historyStore.set(sessionId, new ChatMessageHistory());
    return historyStore.get(sessionId)!;
  },
  inputMessagesKey: "input",
  historyMessagesKey: "chat_history",
  outputMessagesKey: "answer",
});

const config = { configurable: { sessionId: "user-abc" } };
const r1 = await chainWithHistory.invoke({ input: "What is LangChain?" }, config);
const r2 = await chainWithHistory.invoke({ input: "What are its key features?" }, config);
// "its" in r2 is resolved via chat_history

// Production history backends:
// Redis: new RedisChatMessageHistory({ sessionId, client: redisClient, ttl: 3600 })
// Upstash: new UpstashRedisChatMessageHistory({ sessionId, config: { url, token } })
```

---

## 8. Streaming RAG

```typescript
// Token streaming via .stream()
const stream = await ragChain.stream(
  { input: "Explain RAG in detail" },
  { configurable: { sessionId: "s1" } }
);
for await (const chunk of stream) {
  if (chunk.answer) process.stdout.write(chunk.answer);
}

// Granular event streaming — intercept retriever and model events separately
const events = ragChain.streamEvents({ input: "What is RAG?" }, { version: "v2" });
for await (const event of await events) {
  if (event.event === "on_chat_model_stream") {
    const content = event.data?.chunk?.content;
    if (content) process.stdout.write(content);
  }
  if (event.event === "on_retriever_end") {
    console.log("\nRetrieved:", event.data.output.length, "docs");
  }
}

// Next.js App Router SSE
// app/api/chat/route.ts
import { NextRequest } from "next/server";
import { StreamingTextResponse, LangChainStream } from "ai";  // Vercel AI SDK

export async function POST(req: NextRequest) {
  const { messages } = await req.json();
  const { stream, handlers } = LangChainStream();
  ragChain.invoke({ input: messages.at(-1).content }, { callbacks: [handlers] });
  return new StreamingTextResponse(stream);
}
```

---

## 9. Advanced RAG Patterns

### RAG Fusion (Multi-Query + RRF)

```typescript
// MultiQueryRetriever already applies RRF internally
const ragFusion = MultiQueryRetriever.fromLLM({
  llm: new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0.5 }),
  retriever: vectorStore.asRetriever({ k: 5 }),
  k: 5,  // generate 5 query variants, retrieve for each, deduplicate via RRF
});
```

### CRAG (Corrective RAG)

Grade retrieved docs and fall back to web search if quality is insufficient.

```typescript
import { RunnableLambda } from "@langchain/core/runnables";
import { TavilySearchAPIRetriever } from "@langchain/community/retrievers/tavily";

const cragChain = RunnableLambda.from(async ({ input }: { input: string }) => {
  const docs = await retriever.invoke(input);

  // Grade relevance
  const grader = ChatPromptTemplate.fromMessages([
    ["system", "Are these documents relevant to the question? Answer 'yes' or 'no'."],
    ["human", "Question: {q}\nDocs: {d}"],
  ]).pipe(llm);
  const grade = await grader.invoke({ q: input, d: docs.map(d => d.pageContent).join("\n") });

  let context = docs;
  if ((grade.content as string).toLowerCase().includes("no")) {
    // Fallback: web search
    const web = new TavilySearchAPIRetriever({ k: 3 });
    const rewritten = await llm.invoke(`Rewrite for web search: ${input}`);
    context = await web.invoke(rewritten.content as string);
  }
  return ragChain.invoke({ input, context });
});
```

### Self-RAG (Retrieval Decision + Critique)

Three steps: (1) LLM decides whether retrieval is needed (`needs external knowledge? yes/no`). (2) If yes: retrieve and generate. (3) Critique: if answer not grounded in context, retrieve more and refine. Use `RunnableLambda.from(async ({ input }) => { ... })` to compose the three steps. For production, implement as a LangGraph state machine to handle cycles cleanly.

### Query Routing

```typescript
import { z } from "zod";

const routerSchema = z.object({
  datasource: z.enum(["vectorstore", "web_search", "sql"]),
});
const router = ChatPromptTemplate.fromMessages([
  ["system", "Route to: vectorstore (docs), web_search (current events), sql (structured data)"],
  ["human", "{input}"],
]).pipe(llm.withStructuredOutput(routerSchema));

const routedRag = RunnableLambda.from(async ({ input }: { input: string }) => {
  const { datasource } = await router.invoke({ input });
  switch (datasource) {
    case "vectorstore": return ragChain.invoke({ input });
    case "web_search":  return webRagChain.invoke({ input });
    case "sql":         return sqlRagChain.invoke({ input });
  }
});
```

### Multi-Modal RAG

Use `MultiVectorRetriever` — store text summaries of images/tables in the vector store, link back to originals in docstore.

```typescript
const imgSummary = await llm.invoke(`Describe this image for retrieval: [base64 image]`);
await vectorStore.addDocuments([
  new Document({ pageContent: imgSummary.content as string, metadata: { type: "image", doc_id: imageId } }),
]);
await docstore.mset([[imageId, originalImageDocument]]);
// Query returns image summaries from vector search → original images from docstore
```

---

## 10. RAG Evaluation (RAGAS)

| Metric | Measures | Target | What it Detects |
|---|---|---|---|
| **Faithfulness** | Answer factually consistent with context | > 0.90 | Hallucinations |
| **Answer Relevancy** | Answer addresses the question | > 0.95 | Off-topic responses |
| **Context Recall** | Ground-truth info is in retrieved docs | > 0.90 | Missed retrieval |
| **Context Precision** | Retrieved context is relevant (no noise) | > 0.90 | Noisy retrieval |

RAGAS score = harmonic mean of all four.

```typescript
import { Client } from "langsmith";
import { evaluate } from "langsmith/evaluation";
import { z } from "zod";

// Enable tracing
process.env.LANGCHAIN_TRACING_V2 = "true";
process.env.LANGCHAIN_PROJECT = "rag-eval";

const client = new Client();
const dataset = await client.createDataset("RAG Eval v1");
await client.createExamples({
  inputs: [{ question: "What is RAG?" }],
  outputs: [{ answer: "RAG retrieves docs then generates answers grounded in them." }],
  datasetId: dataset.id,
});

// Faithfulness evaluator
const faithfulness = async ({ input, output, context }: { input: string; output: string; context: string }) => {
  const res = await llm.withStructuredOutput(
    z.object({ grounded: z.boolean(), explanation: z.string() })
  ).invoke(`Is this answer fully supported by context?\nQ: ${input}\nA: ${output}\nCtx: ${context}`);
  return { key: "faithfulness", score: res.grounded ? 1 : 0 };
};

const results = await evaluate(
  async (input) => {
    const out = await ragChain.invoke({ input: input.question });
    return { answer: out.answer, context: out.context.map((d: Document) => d.pageContent).join("\n") };
  },
  {
    data: "RAG Eval v1",
    evaluators: [faithfulness],
    experimentPrefix: "rag-v1",
    metadata: { model: "gpt-4o-mini" },
  }
);
```

**Four standard LangSmith evaluator types:**
- **Correctness** — `input + output + reference_output` → factual accuracy vs ground truth
- **Relevance** — `input + output` → answer addresses the question
- **Groundedness** — `input + output + context` → hallucination detection
- **Retrieval Relevance** — `input + context` → retrieved docs match query

---

## 11. Production Patterns

### Error Handling & Retries

```typescript
import { RunnableLambda } from "@langchain/core/runnables";

// Retry with exponential backoff + jitter
const robustChain = ragChain.withRetry({
  stopAfterAttempt: 3,
  waitExponentialJitter: true,
  onFailedAttempt: (error, attempt) => console.warn(`Attempt ${attempt} failed: ${error.message}`),
});

// Graceful fallback (answer without retrieval if RAG fails)
const withFallback = ragChain.withFallbacks([simpleLlmChain]);

// Rate limiting
const rateLimited = RunnableLambda.from(async (input) => {
  await rateLimiter.removeTokens(1);  // e.g., using bottleneck or p-limit
  return robustChain.invoke(input);
});
```

### Caching & Performance

```typescript
// 1. Cache embeddings (CacheBackedEmbeddings — see section 3)

// 2. Cache LLM responses for identical queries
import { InMemoryCache } from "@langchain/core/caches";
const llmWithCache = new ChatOpenAI({ model: "gpt-4o-mini", cache: new InMemoryCache() });

// 3. Tune k for latency vs quality
// k=2: fast, less context risk
// k=4: balanced default
// k=10: more context, slower, higher cost

// 4. Batch indexing (avoid API rate limits)
const BATCH = 100;
for (let i = 0; i < docs.length; i += BATCH) {
  await vectorStore.addDocuments(docs.slice(i, i + BATCH));
}
```

### Observability with LangSmith

```typescript
process.env.LANGCHAIN_TRACING_V2 = "true";
process.env.LANGCHAIN_PROJECT = "production-rag";

// Per-request metadata for filtering in LangSmith UI
const result = await ragChain.invoke(
  { input: query },
  { runName: "rag-qa", tags: ["prod", "v2"], metadata: { userId, sessionId } }
);

// User feedback
import { Client } from "langsmith";
const ls = new Client();
await ls.createFeedback(runId, "user-rating", { score: 1, comment: "Helpful!" });
```

**Key metrics to monitor:** P50/P95 latency by step, error rate (target < 1%), faithfulness trend, context precision trend, token usage per session.

### Common Failure Modes

| Failure | Symptoms | Fix |
|---|---|---|
| Hallucination | Faithfulness < 0.8 | Add grounding instruction; use ContextualCompressionRetriever |
| Irrelevant retrieval | Context precision < 0.7 | Smaller chunks (256–400t); semantic chunking; add metadata filters |
| Missing information | Context recall < 0.7 | Increase k; use ParentDocumentRetriever |
| Slow responses | P95 > 5s | Cache embeddings; reduce k; use faster retriever |
| Context overflow | LLM context length error | Reduce k; use MapReduce chain; add compression |
| Stale answers | Outdated info retrieved | Re-index pipeline; add `last_updated` metadata; TimeWeightedRetriever |
| Poor multilingual | Low scores non-English | Switch to Cohere `embed-multilingual-v3.0` or `multilingual-e5-large` |

**Debugging steps:** (1) `retriever.invoke(query)` — inspect returned docs before LLM sees them. (2) `vectorStore.similaritySearchWithScore(query, 4)` — scores below 0.7 indicate poor retrieval. (3) Set `verbose: true` on the retriever. (4) View full chain traces in LangSmith.

---

## Import Quick Reference

| What | Import |
|------|--------|
| `Document` | `@langchain/core/documents` |
| `InMemoryVectorStore` | `@langchain/core/vectorstores` |
| `RecursiveCharacterTextSplitter`, `TokenTextSplitter`, `MarkdownHeaderTextSplitter`, `SemanticChunker` | `@langchain/textsplitters` |
| `OpenAIEmbeddings` | `@langchain/openai` |
| `CacheBackedEmbeddings` | `@langchain/classic/embeddings/cache_backed` |
| `FaissStore` | `@langchain/community/vectorstores/faiss` |
| `Chroma` | `@langchain/community/vectorstores/chroma` |
| `PineconeStore` | `@langchain/pinecone` |
| `QdrantVectorStore` | `@langchain/qdrant` |
| `PGVectorStore` | `@langchain/community/vectorstores/pgvector` |
| `BM25Retriever` | `@langchain/community/retrievers/bm25` |
| `MultiQueryRetriever` | `langchain/retrievers/multi_query` |
| `SelfQueryRetriever` | `langchain/retrievers/self_query` |
| `ContextualCompressionRetriever` | `langchain/retrievers/contextual_compression` |
| `ParentDocumentRetriever` | `langchain/retrievers/parent_document` |
| `MultiVectorRetriever` | `langchain/retrievers/multi_vector` |
| `EnsembleRetriever` | `langchain/retrievers/ensemble` |
| `ScoreThresholdRetriever` | `langchain/retrievers/score_threshold` |
| `HydeRetriever` | `@langchain/classic/retrievers/hyde` |
| `TimeWeightedVectorStoreRetriever` | `langchain/retrievers/time_weighted` |
| `createRetrievalChain` | `langchain/chains/retrieval` |
| `createStuffDocumentsChain`, `createMapReduceDocumentsChain`, `createRefineDocumentsChain` | `langchain/chains/combine_documents` |
| `createHistoryAwareRetriever` | `langchain/chains/history_aware_retriever` |
| `RunnableWithMessageHistory` | `@langchain/core/runnables` |
| `CheerioWebBaseLoader` | `@langchain/community/document_loaders/web/cheerio` |
| `PDFLoader` | `@langchain/community/document_loaders/fs/pdf` |
| `DirectoryLoader` | `@langchain/classic/document_loaders/fs/directory` |
