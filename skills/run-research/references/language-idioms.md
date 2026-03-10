# Language Features & Idioms Research Guide

## Quick Reference: Which Tools For Which Language Problem

| Use Case | Primary Tool | Secondary Tool | Why This Combination |
|---|---|---|---|
| 01. Async & Concurrency | `deep_research` | `search_reddit` | Cross-language comparison + deadlock/cancellation war stories |
| 02. Type System Corner Cases | `deep_research` | `search_google` + `scrape_pages` | Formal type reasoning + RFC/compiler blog extraction |
| 03. Compiler Behavior | `search_google` + `scrape_pages` | `search_reddit` | Compiler blog discovery + optimization pass explanations |
| 04. Lifetime & Borrow Puzzles | `search_reddit` + `fetch_reddit` | `deep_research` | r/rust expert explanations + NLL limitation catalog |
| 05. Generics & Traits | `deep_research` | `search_reddit` | Library design guidance + orphan rule workaround stories |
| 06. Macro & Metaprogramming | `search_google` | `search_reddit` | Tutorial/crate discovery + debugging war stories |
| 07. FFI & Interop | `deep_research` | `scrape_pages` | Boundary design + type mapping table extraction |
| 08. Unsafe Code Review | `deep_research` + `fetch_reddit` | `scrape_pages` | Audit checklist + expert safety threads + UCG extraction |
| 09. Error Handling Strategy | `search_reddit` | `deep_research` | Decision stories + integrated error flow architecture |
| 10. Iterator & Functional | `search_google` | `search_reddit` | Performance benchmarks + readability debate perspectives |

---

## 01. Async & Concurrency Patterns

**deep_research** -- cross-language synthesis:
```
WHAT I NEED: Comparison of structured concurrency across Rust (Tokio), JavaScript, and Python.
SPECIFIC QUESTIONS:
1) How does cancellation differ between Tokio task abort, AbortController, Python TaskGroup?
2) What happens to child tasks when a parent scope exits in each language?
3) Which patterns prevent resource leaks on partial failure?
```

**search_reddit**: `["Tokio select! deadlock debugging", "async cancellation safety footgun", "Promise.all error handling best practice", "Python asyncio TaskGroup vs gather"]`

**Best Practices**: Search for "footgun", "deadlock", "leak" on Reddit. Include version-specific terms ("Python 3.12 TaskGroup"). For scrape_pages, extract "cancellation semantics | error propagation | cleanup patterns."

---

## 02. Type System Corner Cases

**deep_research** -- comparative type system:
```
WHAT I NEED: Understanding variance in Rust lifetimes vs TypeScript generics vs Java wildcards.
SPECIFIC QUESTIONS:
1) When does Rust infer covariance vs invariance for lifetime parameters?
2) How does TypeScript structural typing affect variance vs Rust nominal approach?
```

**search_google**: `["TypeScript conditional types distributive behavior unexpected", "Rust lifetime variance covariant contravariant examples", "higher-kinded types emulation TypeScript Rust workaround"]`

**Best Practices**: Use precise terminology ("covariant", "distributive", "HRTB"). Search for error messages verbatim. Target compiler repos with `site:github.com/rust-lang/rust`. On Reddit, search for confusion, not concepts.

---

## 03. Compiler Behavior Investigation

**deep_research** -- attach code, ask about the pipeline:
```
WHAT I NEED: Why LLVM fails to auto-vectorize certain loop patterns and how to fix them.
SPECIFIC QUESTIONS:
1) Top 10 reasons LLVM loop vectorizer bails out?
2) How to read LLVM optimization remarks to diagnose failure?
3) When to use std::simd instead of auto-vectorization?
```

**search_google**: `["LLVM auto-vectorization failure why loop not vectorized", "V8 TurboFan JIT deoptimization reasons hidden classes", "GCC vs Clang optimization difference same code"]`

**Best Practices**: Attach actual code via file_attachments. Ask "how to diagnose" not just "how to fix." On Reddit, search for "Godbolt" to find threads with interactive demonstrations.

---

## 04. Lifetime & Borrow Puzzles

**search_reddit** -- emotional signal finds the best explanations:
```
queries: ["r/rust borrow checker confusing error lifetime", "r/rust NLL limitation workaround",
          "r/rust HRTB for<'a> when to use explained", "r/rust self-referential struct solution"]
```

**deep_research**: Ask for categorized NLL limitation catalog: "What categories of safe code does NLL reject? For each, what is the standard workaround? Which will Polonius fix?"

**Best Practices**: Always `fetch_comments=True` with `use_llm=False` -- lifetime annotations like `'a` must be preserved exactly. Search "frustrated" and "finally understood" for eureka explanations. Look for corrections in replies -- first answers on lifetime threads are often incomplete.

---

## 05. Generics & Trait Constraints

**deep_research** -- reference real crate patterns:
```
WHAT I NEED: Rust trait system constraints and workaround patterns for library design.
SPECIFIC QUESTIONS:
1) What trait designs cause orphan rule problems for downstream users?
2) How do serde, tower, axum design their trait hierarchies?
3) When to use associated types vs generic type parameters?
4) Complete object safety rules?
```

**search_google**: `["Rust orphan rule workaround newtype pattern alternatives", "E0119 conflicting implementations workaround", "Rust trait object safety rules dyn Trait"]`

**Best Practices**: Search "frustrating" and "workaround" on Reddit. Include the Rust Reference in scrape_pages batches. Look for playground links in Reddit comments.

---

## 06. Macro & Metaprogramming

**deep_research** -- decision framework:
```
SPECIFIC QUESTIONS:
1) Complexity thresholds where macro_rules! won't suffice?
2) Compile-time costs of proc macros vs build scripts?
3) How do serde, diesel, sqlx decide which approach to use?
```

**search_reddit**: `["r/rust proc macro debugging nightmare solution", "r/rust derive macro best practices 2025", "r/rust macro_rules limits when to switch proc macro"]`

**Best Practices**: Include specific crate names ("syn", "darling", "quote"). Search for "tutorial" or "workshop." On Reddit, look for threads by dtolnay for authoritative proc macro advice.

---

## 07. FFI & Interop Patterns

**deep_research** -- specify workload pattern:
```
WHAT I NEED: Decision guide for Rust-to-Python interop: PyO3 vs cpython vs raw FFI.
SPECIFIC QUESTIONS:
1) Performance overheads for different call patterns (high-frequency vs large data)?
2) How to handle Python objects crossing the FFI boundary efficiently?
3) Error handling across the boundary (Rust Result -> Python exception)?
```

**scrape_pages**: `what_to_extract: "type mapping table | memory ownership rules | safety requirements | zero-copy vs conversion types"`

**Best Practices**: Specify "high-frequency small calls" vs "infrequent large data transfers." Keep `use_llm=False` for fetch_reddit -- build scripts and linker flags must be exact. Include the Rustonomicon FFI chapter as baseline.

---

## 08. Unsafe Code Review

**deep_research** -- systematic audit:
```
SPECIFIC QUESTIONS:
1) Complete checklist of invariants each unsafe block must uphold?
2) How to write safety comments documenting the proof?
3) What does Miri catch vs what requires manual review?
4) Top 10 unsoundness patterns in real-world unsafe Rust?
```

**search_reddit**: `["r/rust is this unsafe code sound review", "r/rust Miri caught undefined behavior", "r/rust Stacked Borrows violation real code"]`

**Best Practices**: Attach your unsafe code for specific audit. Full Reddit threads preserve multi-expert safety analysis with corrections. For scrape_pages, extract "complete UB list | aliasing rules | valid pointer operations" from UCG reference. Include Ralf Jung's blog for aliasing rules.

---

## 09. Error Handling Strategy

**deep_research** -- project-level, not crate-level:
```
SPECIFIC QUESTIONS:
1) Library error type design (enum per module? thiserror patterns)?
2) How should API server convert library errors to HTTP responses?
3) How should CLI convert errors to user-friendly messages (miette)?
4) Error context conventions for a 5-developer team?
```

**search_reddit**: `["r/rust anyhow vs thiserror decision real project", "r/rust panic in library acceptable", "r/rust error context with_context pattern"]`

**Best Practices**: Read dissenting opinions -- they reveal trade-offs the majority glosses over. Extract "when to use | decision criteria" from anyhow + thiserror + miette docs in one scrape_pages batch. Search "regret" or "mistake" for hard-won lessons.

---

## 10. Iterator & Functional Patterns

**deep_research** -- implementation + performance:
```
SPECIFIC QUESTIONS:
1) Which optional Iterator methods to implement for performance (fold, nth, size_hint)?
2) How to implement DoubleEndedIterator and ExactSizeIterator correctly?
3) Patterns ensuring custom iterator chains optimize like slice iterators?
```

**search_google**: `["Rust iterator vs for loop performance benchmark 2025", "Rust itertools crate advanced patterns", "Rust fold vs try_fold pattern comparison"]`

**Best Practices**: Always implement `fold()` for custom tree iterators. Community guideline: chains for simple transforms, for-loop for early returns or 4+ chained operations. Extract top 20 most useful Iterator methods by purpose, not all 100+.

---

## Universal Language Research Workflow

1. **`search_google`** (5-7 keywords) -- discover documentation, blog posts, discussions
2. **`search_reddit`** (5-7 queries, emotional terms) -- practitioner war stories, in parallel with step 1
3. **`scrape_pages`** (3-5 URLs) -- extract patterns, rules, edge cases from best step-1 results
4. **`fetch_reddit`** (5-10 URLs, `fetch_comments=True`, `use_llm=False`) -- full debugging narratives and code
5. **`deep_research`** (2-3 questions) -- synthesize into a coherent answer, decision framework, or checklist

**Key principles:**
- Include "WHAT I KNOW" in deep_research to skip introductory content
- On Reddit, search for the confusion/failure, not the concept
- For scrape_pages, use pipe-separated targets: "rules | edge cases | limitations"
- Keep `use_llm=False` for fetch_reddit when code syntax matters (lifetimes, macros, types)
