# RAG Patterns — Retrieval-Augmented Generation

> Verified against langchain@1.2.35, @langchain/core@1.1.34, @langchain/openai@1.3.0, @langchain/textsplitters@1.0.1, @langchain/langgraph@1.2.5 — March 2026
> All code TypeScript. Import paths exact.

---

## RAG Decision Tree: Do You Even Need RAG?

Before building a RAG pipeline, check whether a simpler approach works:

```
Start
 │
 ├─ Corpus < 100k tokens?
 │   └─ YES → Stuff it into the context window. Done.
 │       Use ChatPromptTemplate with the full text as context.
 │       Cheaper, faster, more accurate than RAG.
 │
 ├─ Corpus < 1M tokens AND queries need reasoning over multiple docs?
 │   └─ YES → Try agentic RAG (retriever as a tool).
 │       The agent decides when/whether to search.
 │       Better for exploratory or multi-step queries.
 │
 └─ Corpus > 1M tokens OR latency-sensitive with large corpus?
     └─ YES → Traditional RAG pipeline.
         Pre-index, retrieve top-K, inject into prompt.
```

**Principle: Start simple, measure quality, add complexity only when needed.**

- Context window first → no indexing, no retrieval errors, perfect recall
- Agentic RAG → agent controls retrieval, better for unpredictable query patterns
- Traditional RAG → mandatory for large corpora, requires tuning

---

## 1. Document Loading

Documents are the raw input to a RAG pipeline. LangChain uses `Document` objects with `pageContent` and `metadata`.

### Document Object

```typescript
import { Document } from "@langchain/core/documents";

const doc = new Document({
  pageContent: "LangChain is a framework for LLM applications.",
  metadata: { source: "docs", page: 1, category: "framework" },
});
// doc.pageContent → string
// doc.metadata → Record<string, any> (defaults to {} if omitted)
```

### Text Files

```typescript
import { TextLoader } from "@langchain/community/document_loaders/fs/text";

const loader = new TextLoader("./data/article.txt");
const docs = await loader.load();
// docs[0].metadata.source → "./data/article.txt"
```

### PDF Files

```typescript
import { PDFLoader } from "@langchain/community/document_loaders/fs/pdf";

const loader = new PDFLoader("./data/report.pdf");
const docs = await loader.load();
// One Document per page. metadata includes { source, pdf: { totalPages }, loc: { pageNumber } }
```

### Web Pages

```typescript
import { CheerioWebBaseLoader } from "@langchain/community/document_loaders/web/cheerio";

const loader = new CheerioWebBaseLoader("https://example.com/article");
const docs = await loader.load();
```

### CSV Files

```typescript
import { CSVLoader } from "@langchain/community/document_loaders/fs/csv";

const loader = new CSVLoader("./data/records.csv");
const docs = await loader.load();
// One Document per row. Each column becomes a metadata field.
```

**Key point**: All loaders return `Document[]`. Metadata is automatically populated with `source` and format-specific fields.

---

## 2. Text Splitting

Raw documents are typically too large for a single embedding or context window slot. Split them into chunks.

### RecursiveCharacterTextSplitter (Default Choice)

```typescript
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";

const splitter = new RecursiveCharacterTextSplitter({
  chunkSize: 1000,    // max characters per chunk
  chunkOverlap: 200,  // overlap between consecutive chunks
});

// Split raw text into string chunks
const chunks: string[] = await splitter.splitText(longText);

// Split into Document objects (preserves + extends metadata)
const docs = await splitter.createDocuments(
  [longText],
  [{ source: "article.md", author: "Alice" }]
);
// docs[0].metadata → { source: "article.md", author: "Alice", loc: { lines: { from: 1, to: 12 } } }
```

### Language-Aware Splitting

```typescript
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";

// Markdown-aware: splits on headers, code blocks, paragraphs before characters
const mdSplitter = RecursiveCharacterTextSplitter.fromLanguage("markdown", {
  chunkSize: 1000,
  chunkOverlap: 100,
});
const mdChunks = await mdSplitter.splitText(markdownContent);

// JavaScript-aware: splits on functions, classes, statements
const jsSplitter = RecursiveCharacterTextSplitter.fromLanguage("js", {
  chunkSize: 1500,
  chunkOverlap: 200,
});

// Available languages:
// "markdown", "js", "python", "html", "latex", "go", "rust", "ruby",
// "cpp", "java", "php", "swift", "scala", "sol"
```

### Chunk Size Tuning Guide

| Chunk Size | Best For | Trade-off |
|-----------|----------|-----------|
| 200–500 | FAQ, short answers, precise retrieval | May lose surrounding context |
| 500–1000 | General knowledge bases, articles | Good balance of precision and context |
| 1000–2000 | Technical docs, code, legal text | Better context, noisier retrieval |
| 2000+ | Long-form analysis, research papers | High context but low retrieval precision |

**Rules of thumb**:
- Start with `chunkSize: 1000, chunkOverlap: 200`
- If retrieval returns irrelevant chunks → decrease chunk size
- If answers lack context → increase chunk size or overlap
- Always test with representative queries before tuning

---

## 3. Chunking Strategy Matrix

| Strategy | Splitter | Best For | Parameters |
|----------|---------|----------|------------|
| **Recursive** (default) | `RecursiveCharacterTextSplitter` | General text, articles, docs | `chunkSize`, `chunkOverlap` |
| **Token-aware** | `RecursiveCharacterTextSplitter` with `lengthFunction` | Token-budget-sensitive apps | Custom `lengthFunction` counting tokens |
| **Format-specific** | `.fromLanguage("markdown"\|"js"\|...)` | Code, Markdown, HTML | Language + `chunkSize` |
| **Semantic** | Custom (embed → cluster → split) | Research papers, heterogeneous docs | Embedding model + similarity threshold |

**Decision guide**:
- Plain text or mixed content → **Recursive**
- Code or structured markup → **Format-specific** with the matching language
- Need exact token control (billing, context window) → **Token-aware**
- Documents with varying topic density → **Semantic** (most complex, highest quality)

---

## 4. Embeddings

Embeddings convert text chunks into vectors for similarity search. **OpenRouter does NOT support embeddings** — you must use OpenAI (or another embedding provider) directly.

### OpenAI Embeddings

```typescript
import { OpenAIEmbeddings } from "@langchain/openai";

// Production: use OpenAI directly for embeddings (not OpenRouter)
const embeddings = new OpenAIEmbeddings({
  model: "text-embedding-3-small", // or "text-embedding-3-large"
  openAIApiKey: process.env.OPENAI_API_KEY!,
});

// Embed a single query
const queryVector = await embeddings.embedQuery("What is LangChain?");
// queryVector → number[] (1536 dimensions for text-embedding-3-small)

// Embed multiple documents
const docVectors = await embeddings.embedDocuments([
  "LangChain is a framework.",
  "LangGraph adds stateful agents.",
]);
// docVectors → number[][] (one vector per document)
```

### Embedding Model Comparison

| Model | Dimensions | Max Tokens | Cost (per 1M tokens) | Best For |
|-------|-----------|------------|----------------------|----------|
| `text-embedding-3-small` | 1536 | 8191 | $0.02 | Default choice, good quality/cost ratio |
| `text-embedding-3-large` | 3072 | 8191 | $0.13 | Higher accuracy, large-scale retrieval |
| `text-embedding-ada-002` | 1536 | 8191 | $0.10 | Legacy — use `3-small` instead |

**Critical rule**: Use the SAME embedding model for indexing and querying. Mixing models produces meaningless similarity scores.

### Fake Embeddings (Testing Only)

```typescript
import { FakeEmbeddings } from "@langchain/core/utils/testing";

// For unit tests — returns random vectors, not useful for real retrieval
const fakeEmbeddings = new FakeEmbeddings();
```

---

## 5. Vector Stores

Vector stores index embeddings for fast similarity search.

### MemoryVectorStore (Development)

```typescript
import { MemoryVectorStore } from "langchain/vectorstores/memory";
import { OpenAIEmbeddings } from "@langchain/openai";

const embeddings = new OpenAIEmbeddings({
  model: "text-embedding-3-small",
  openAIApiKey: process.env.OPENAI_API_KEY!,
});

// Create from documents
const vectorStore = await MemoryVectorStore.fromDocuments(docs, embeddings);

// Similarity search
const results = await vectorStore.similaritySearch("What is LangChain?", 3);
// results → Document[] (top 3 most similar)

// Similarity search with scores
const resultsWithScores = await vectorStore.similaritySearchWithScore(
  "What is LangChain?",
  3
);
// resultsWithScores → [Document, number][] (doc + similarity score)

// Convert to retriever for use in chains
const retriever = vectorStore.asRetriever({ k: 3 });
```

**Use for**: Development, prototyping, tests, small datasets (<10k documents).
**Limitation**: All in memory — lost on restart, doesn't scale.

### Pinecone (Managed, Serverless)

```typescript
import { Pinecone } from "@pinecone-database/pinecone";
import { PineconeStore } from "@langchain/pinecone";
import { OpenAIEmbeddings } from "@langchain/openai";

const pinecone = new Pinecone({ apiKey: process.env.PINECONE_API_KEY! });
const index = pinecone.index("my-index");

const vectorStore = await PineconeStore.fromExistingIndex(embeddings, {
  pineconeIndex: index,
  namespace: "my-namespace",
});

// Add documents
await vectorStore.addDocuments(docs);

// Search with metadata filter
const results = await vectorStore.similaritySearch("query", 5, {
  source: "docs",
});
```

**Use for**: Production SaaS, serverless scaling, metadata filtering, multi-tenant apps.

### Chroma (Self-Hosted)

```typescript
import { Chroma } from "@langchain/community/vectorstores/chroma";
import { OpenAIEmbeddings } from "@langchain/openai";

const vectorStore = await Chroma.fromDocuments(docs, embeddings, {
  collectionName: "my-collection",
  url: "http://localhost:8000",
});

const results = await vectorStore.similaritySearch("query", 3);
```

**Use for**: Self-hosted, open-source, local development with persistence.

### PGVector (PostgreSQL Extension)

```typescript
import { PGVectorStore } from "@langchain/community/vectorstores/pgvector";
import { OpenAIEmbeddings } from "@langchain/openai";

const vectorStore = await PGVectorStore.initialize(embeddings, {
  postgresConnectionOptions: {
    connectionString: process.env.DATABASE_URL!,
  },
  tableName: "documents",
});

await vectorStore.addDocuments(docs);
const results = await vectorStore.similaritySearch("query", 5);
```

**Use for**: Already using PostgreSQL, want SQL + vector in one database, hybrid queries.

### Supabase (Hosted PGVector)

```typescript
import { SupabaseVectorStore } from "@langchain/community/vectorstores/supabase";
import { createClient } from "@supabase/supabase-js";
import { OpenAIEmbeddings } from "@langchain/openai";

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

const vectorStore = new SupabaseVectorStore(embeddings, {
  client: supabase,
  tableName: "documents",
  queryName: "match_documents",
});
```

**Use for**: Supabase stack, managed PostgreSQL with vector search, row-level security.

### Vector DB Decision Matrix

| Store | Hosting | Cost Model | Metadata Filtering | Best For |
|-------|---------|-----------|-------------------|----------|
| **MemoryVectorStore** | In-process | Free | No | Dev, testing, <10k docs |
| **Pinecone** | Managed SaaS | Pay per query + storage | Yes (rich) | Production SaaS, serverless |
| **Chroma** | Self-hosted | Infra cost only | Yes | Self-hosted, open-source |
| **PGVector** | Self-hosted (Postgres) | Infra cost only | Yes (SQL WHERE) | Already using Postgres |
| **Supabase** | Managed Postgres | Supabase pricing | Yes (SQL + RLS) | Supabase ecosystem |

**Decision guide**:
- Just prototyping? → **MemoryVectorStore**
- Need managed + serverless? → **Pinecone**
- Want self-hosted + open-source? → **Chroma**
- Already have PostgreSQL? → **PGVector**
- Using Supabase? → **Supabase**

---

## 6. RAG Chain with LCEL

The core RAG pattern: retrieve context → inject into prompt → generate answer.

### Standard RAG Chain

```typescript
import { Document } from "@langchain/core/documents";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import {
  RunnablePassthrough,
  RunnableLambda,
  RunnableSequence,
} from "@langchain/core/runnables";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatOpenAI } from "@langchain/openai";
import { MemoryVectorStore } from "langchain/vectorstores/memory";
import { OpenAIEmbeddings } from "@langchain/openai";

// 1. Index documents
const embeddings = new OpenAIEmbeddings({
  model: "text-embedding-3-small",
  openAIApiKey: process.env.OPENAI_API_KEY!,
});
const vectorStore = await MemoryVectorStore.fromDocuments(docs, embeddings);
const retriever = vectorStore.asRetriever({ k: 3 });

// 2. Format retrieved documents
function formatDocs(docs: Document[]): string {
  return docs.map((doc, i) => `[${i + 1}] ${doc.pageContent}`).join("\n\n");
}

// 3. RAG prompt
const ragPrompt = ChatPromptTemplate.fromMessages([
  [
    "system",
    `Answer based ONLY on the following context. If the context doesn't contain the answer, say "I don't have that information."

Context:
{context}`,
  ],
  ["human", "{question}"],
]);

// 4. Build chain with LCEL
const model = new ChatOpenAI({ /* config */ });

const ragChain = RunnableSequence.from([
  RunnablePassthrough.assign({
    context: new RunnableLambda({
      func: async (input: { question: string }) => {
        const docs = await retriever.invoke(input.question);
        return formatDocs(docs);
      },
    }),
  }),
  ragPrompt,
  model,
  new StringOutputParser(),
]);

// 5. Use it
const answer = await ragChain.invoke({ question: "What is LangChain?" });
```

**How it works**:
1. `RunnablePassthrough.assign()` passes through `{ question }` and adds `{ context }` from the retriever
2. The prompt receives both `{question}` and `{context}`
3. The model generates an answer grounded in the context
4. `StringOutputParser` extracts the string response

### RAG Chain Without Real Embeddings (Mock Retriever)

For development/testing without an OpenAI API key for embeddings:

```typescript
import { Document } from "@langchain/core/documents";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import {
  RunnablePassthrough,
  RunnableLambda,
  RunnableSequence,
} from "@langchain/core/runnables";
import { StringOutputParser } from "@langchain/core/output_parsers";

// Knowledge base as Document objects
const knowledgeBase = [
  new Document({
    pageContent: "LCEL stands for LangChain Expression Language...",
    metadata: { source: "docs", topic: "lcel" },
  }),
  new Document({
    pageContent: "LangGraph is used for building stateful agents...",
    metadata: { source: "docs", topic: "langgraph" },
  }),
];

// Keyword-based mock retriever
function mockRetrieve(query: string): Document[] {
  const queryLower = query.toLowerCase();
  const scored = knowledgeBase.map((doc) => {
    const words = queryLower.split(/\s+/);
    const score = words.filter((w) =>
      doc.pageContent.toLowerCase().includes(w)
    ).length;
    return { doc, score };
  });
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, 2).map((s) => s.doc);
}

const ragChain = RunnableSequence.from([
  RunnablePassthrough.assign({
    context: new RunnableLambda({
      func: (input: { question: string }) => {
        const docs = mockRetrieve(input.question);
        return formatDocs(docs);
      },
    }),
  }),
  ragPrompt,
  model,
  new StringOutputParser(),
]);
```

### RAG with Streaming

```typescript
const stream = await ragChain.stream({ question: "What is LangChain?" });
for await (const chunk of stream) {
  process.stdout.write(chunk); // Stream answer tokens as they arrive
}
```

---

## 7. Retrieval Tuning

### Top-K Selection

```typescript
// Retrieve more or fewer documents
const retriever = vectorStore.asRetriever({ k: 5 }); // default is 4

// Higher k = more context but more noise
// Lower k = more precise but may miss relevant chunks
```

### Similarity Score Threshold

```typescript
// Filter by minimum similarity
const results = await vectorStore.similaritySearchWithScore("query", 10);
const filtered = results.filter(([_doc, score]) => score > 0.7);
```

### Reranking Concepts

After initial retrieval, rerank results for better relevance:

1. **Cross-encoder reranking** — Use a separate model to score query–document pairs (e.g., Cohere Rerank)
2. **Reciprocal Rank Fusion (RRF)** — Combine results from multiple retrievers (keyword + vector)
3. **LLM-as-judge reranking** — Ask the LLM to rank retrieved documents by relevance

```typescript
// Conceptual reranking with LLM
async function rerankWithLLM(
  query: string,
  docs: Document[],
  model: ChatOpenAI
): Promise<Document[]> {
  const prompt = ChatPromptTemplate.fromMessages([
    [
      "system",
      `Given the query and documents, return the indices of the most relevant documents in order of relevance. Return only a JSON array of indices.`,
    ],
    [
      "human",
      `Query: {query}\n\nDocuments:\n{documents}`,
    ],
  ]);

  const formatted = docs
    .map((d, i) => `[${i}] ${d.pageContent.slice(0, 200)}`)
    .join("\n");

  const chain = prompt.pipe(model).pipe(new StringOutputParser());
  const result = await chain.invoke({ query, documents: formatted });
  const indices: number[] = JSON.parse(result);
  return indices.map((i) => docs[i]);
}
```

### Multi-Query Retrieval

Generate multiple query variations to improve recall:

```typescript
async function multiQueryRetrieve(
  query: string,
  retriever: any,
  model: ChatOpenAI
): Promise<Document[]> {
  // Generate query variations
  const variationPrompt = ChatPromptTemplate.fromMessages([
    [
      "system",
      "Generate 3 alternative versions of the given question to improve search retrieval. Return each on a new line.",
    ],
    ["human", "{question}"],
  ]);
  const chain = variationPrompt.pipe(model).pipe(new StringOutputParser());
  const variations = (await chain.invoke({ question: query })).split("\n").filter(Boolean);

  // Retrieve for each variation
  const allDocs: Document[] = [];
  for (const q of [query, ...variations]) {
    const docs = await retriever.invoke(q);
    allDocs.push(...docs);
  }

  // Deduplicate by content
  const seen = new Set<string>();
  return allDocs.filter((doc) => {
    if (seen.has(doc.pageContent)) return false;
    seen.add(doc.pageContent);
    return true;
  });
}
```

---

## 8. Agentic RAG: Retriever as a Tool

Instead of always retrieving, let the agent decide when to search:

```typescript
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { MemorySaver } from "@langchain/langgraph";

const searchKnowledgeBase = tool(
  async ({ query }: { query: string }) => {
    const results = await vectorStore.similaritySearch(query, 3);
    return results.map((doc) => doc.pageContent).join("\n\n---\n\n");
  },
  {
    name: "search_knowledge_base",
    description:
      "Search the internal knowledge base for information. Use this when the user asks about topics covered in our documentation.",
    schema: z.object({
      query: z.string().describe("The search query to find relevant documents"),
    }),
  }
);

const agent = createReactAgent({
  llm: model,
  tools: [searchKnowledgeBase],
  checkpointSaver: new MemorySaver(),
});

const result = await agent.invoke(
  { messages: [{ role: "user", content: "What does our docs say about LCEL?" }] },
  { configurable: { thread_id: "rag-session-1" } }
);
```

**When to use agentic RAG**:
- User queries are unpredictable (some need retrieval, some don't)
- Agent needs to decide *what* to search for (query reformulation)
- Multiple data sources — agent picks the right one
- Multi-step reasoning — retrieve, reason, retrieve again

**When to use traditional RAG**:
- Every query needs retrieval (e.g., Q&A over a fixed corpus)
- Latency matters (one retrieval call vs agent loop)
- Simple, predictable query patterns

---

## 9. RAG Quality Checklist

### Retrieval Quality
- [ ] Chunks are the right size for your query patterns (test with 5+ representative queries)
- [ ] Top-K returns relevant documents for >80% of test queries
- [ ] Metadata is preserved and usable for filtering
- [ ] Overlap prevents important context from being split across chunks
- [ ] Embedding model matches between indexing and querying

### Generation Quality
- [ ] Model follows "only use context" instruction (doesn't hallucinate beyond retrieved docs)
- [ ] Out-of-scope queries get "I don't know" responses
- [ ] Source attribution is accurate when required
- [ ] Answers are grounded — claims traceable to specific chunks

### Operational
- [ ] Embedding costs are acceptable (estimate: docs × avg tokens per doc × price per token)
- [ ] Retrieval latency is within budget (<500ms for interactive, <2s for batch)
- [ ] Vector store handles expected document count (MemoryVectorStore OK for <10k, use production store above)
- [ ] Re-indexing strategy exists for document updates
- [ ] Monitoring in place for retrieval quality drift

---

## 10. Common RAG Bugs

### Wrong Chunk Size

**Symptom**: Retrieved chunks are irrelevant or missing key context.
**Cause**: Chunk size too small (fragments ideas) or too large (dilutes relevance).
**Fix**: Test with representative queries. Start at 1000 chars, adjust based on retrieval quality.

### Missing Metadata

**Symptom**: Can't filter by source, date, or category during retrieval.
**Cause**: Metadata not passed during `createDocuments()` or lost during splitting.
**Fix**: Always pass metadata to `createDocuments()`. Verify with `docs[0].metadata` after splitting.

```typescript
// ✅ Correct: pass metadata array matching text array
const docs = await splitter.createDocuments(
  [text1, text2],
  [{ source: "file1.md" }, { source: "file2.md" }]
);
```

### Embedding Model Mismatch

**Symptom**: Similarity scores are near-random; relevant documents not in top-K.
**Cause**: Different embedding models used for indexing vs querying.
**Fix**: Use the SAME `OpenAIEmbeddings` instance (or same model name) for both `fromDocuments()` and `similaritySearch()`.

### Retriever Returns Empty or Low-Quality Results

**Symptom**: Retriever returns documents but they don't answer the question.
**Cause**: Query phrasing doesn't match document language; or top-K too low.
**Fix**: Try multi-query retrieval (generate query variations), increase K, or add reranking.

### Context Window Overflow

**Symptom**: API error about maximum context length.
**Cause**: Too many/large chunks retrieved, plus system prompt, exceeds model's context window.
**Fix**: Reduce K, reduce chunk size, or use `trimMessages` on the prompt before sending to model.

### Stale Index

**Symptom**: Answers are outdated; new documents not reflected.
**Cause**: Vector store not updated after document changes.
**Fix**: Implement re-indexing: detect changed documents → re-embed → upsert to vector store. Use document hashes for change detection.

---

## Import Quick Reference

| What | Import |
|------|--------|
| `Document` | `@langchain/core/documents` |
| `RecursiveCharacterTextSplitter` | `@langchain/textsplitters` |
| `OpenAIEmbeddings` | `@langchain/openai` |
| `MemoryVectorStore` | `langchain/vectorstores/memory` |
| `TextLoader` | `@langchain/community/document_loaders/fs/text` |
| `PDFLoader` | `@langchain/community/document_loaders/fs/pdf` |
| `CheerioWebBaseLoader` | `@langchain/community/document_loaders/web/cheerio` |
| `CSVLoader` | `@langchain/community/document_loaders/fs/csv` |
| `PineconeStore` | `@langchain/pinecone` |
| `Chroma` | `@langchain/community/vectorstores/chroma` |
| `PGVectorStore` | `@langchain/community/vectorstores/pgvector` |
| `SupabaseVectorStore` | `@langchain/community/vectorstores/supabase` |
| `ChatPromptTemplate` | `@langchain/core/prompts` |
| `RunnablePassthrough`, `RunnableLambda`, `RunnableSequence` | `@langchain/core/runnables` |
| `StringOutputParser` | `@langchain/core/output_parsers` |
| `FakeEmbeddings` | `@langchain/core/utils/testing` |
| `tool` | `@langchain/core/tools` |
| `createReactAgent` | `@langchain/langgraph/prebuilt` |
