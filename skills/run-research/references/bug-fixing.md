# Bug Fixing Research Guide

## Quick Reference: Which Tools For Which Bug Type

| # | Bug Type | Primary Tools | Why These Tools |
|---|----------|--------------|-----------------|
| 01 | Runtime Error Diagnosis | search_google -> scrape_pages -> search_reddit | Error messages are highly googlable; scrape extracts fixes from SO/GitHub; Reddit has "same error" stories |
| 02 | Compiler Error Decoding | search_google -> scrape_pages -> deep_research | Error codes are unique identifiers; scrape pulls before/after code; deep_research explains compound type errors |
| 03 | Dependency Bug Triage | search_google -> scrape_pages -> search_reddit -> fetch_reddit | Changelogs confirm if it is your code or the dependency; Reddit provides early community consensus |
| 04 | Regression Hunting | search_google -> search_reddit -> deep_research | Bisect techniques live online; Reddit has war stories; deep_research builds investigation plans |
| 05 | Memory Leak Investigation | deep_research -> search_google -> search_reddit | Leaks need tailored investigation; search_google finds profiling tools; Reddit has debugging narratives |
| 06 | Race Condition Debugging | deep_research -> search_google -> search_reddit | Races span multiple layers; search_google finds race detectors; Reddit has timing-specific stories |
| 07 | Platform-Specific Bugs | search_google -> scrape_pages -> search_reddit | Error + platform name is very searchable; scrape extracts CI runner specs; Reddit catalogs cross-platform gotchas |
| 08 | CSS Layout Bugs | search_google -> scrape_pages -> search_reddit | CSS symptoms are describable; MDN/CanIUse have precise browser data; Reddit has visual debugging help |
| 09 | API Breaking Change Recovery | search_google -> scrape_pages -> search_reddit | Changelogs document what changed; scrape extracts migration steps; Reddit has real-time workarounds |
| 10 | Silent Data Corruption | deep_research -> search_google -> search_reddit | Pipeline analysis needs holistic view; search_google finds known corruption patterns |
| 11 | Performance Regression Root Cause | deep_research -> search_google -> scrape_pages | Architecture-aware analysis needed; search_google finds profiling tools; scrape extracts guides |
| 12 | Flaky Test Investigation | deep_research -> search_google -> search_reddit | Root cause analysis needs test code context; search_google finds flaky test taxonomies |
| 13 | Build Failure Resolution | search_google -> scrape_pages -> search_reddit | Build errors produce specific googlable strings; scrape extracts config syntax |
| 14 | Security Vulnerability Patching | search_google -> scrape_pages -> search_reddit | CVE numbers are precise identifiers; scrape extracts severity/versions from NVD |
| 15 | Encoding/Charset Bugs | deep_research -> search_google -> scrape_pages | Full-stack encoding audit needs synthesis; search_google finds mojibake diagnosis tables |

---

## 01. Runtime Error Diagnosis
### Tools: search_google -> scrape_pages -> search_reddit -> deep_research
### Query Templates:
**search_google**: `['"TypeError: Cannot read properties of undefined" react hooks', '"unhandled promise rejection" node.js async await']`
**scrape_pages**: `what_to_extract = "root cause|fix code|environment conditions|version affected|workarounds"`
**search_reddit**: `['"Cannot read properties of undefined" react useEffect', 'r/rust panic index out of bounds vector']`
**deep_research**: Attach the failing code file. Include the full stack trace.
### Best Practices:
- Always quote the distinctive part of the error in search_google
- Vary specificity: full error, error type only, error + framework name
- Follow up search_google with scrape_pages -- the fix is in the page content, not the URL

## 02. Compiler Error Decoding
### Tools: search_google -> scrape_pages -> deep_research
### Query Templates:
**search_google**: `['rust E0597 lifetime error struct reference solution', 'TS2322 conditional type inference error']`
**scrape_pages**: `what_to_extract = "error explanation|fix code before and after|common mistakes|compiler version differences"`
**deep_research**: Use for compound errors involving multiple language features. Attach the failing code.
### Best Practices:
- Error codes (E0597, TS2322) are the most specific search identifiers
- Include one query targeting the official error index: `site:doc.rust-lang.org E0597`
- Use 2 deep_research questions: one for understanding, one for the concrete fix pattern

## 03. Dependency Bug Triage
### Tools: search_google -> scrape_pages -> search_reddit -> fetch_reddit
### Query Templates:
**search_google**: `['"axios" "1.6.0" breaking change behavior different', 'site:github.com/axios/axios issues "regression"']`
**scrape_pages**: Scrape CHANGELOG.md, release page, and related GitHub issues.
**search_reddit**: `['"[package] update broke"']` with `date_after` for recency.
**fetch_reddit**: fetch_comments=True -- workarounds are in reply chains.
### Best Practices:
- Search with the exact version number, not just the package name
- Reddit is where developers first report regressions, often before GitHub issues are filed

## 04. Regression Hunting
### Tools: search_google -> search_reddit -> deep_research
### Query Templates:
**search_google**: `['git bisect automated regression hunting best practices', '"git bisect run" script example']`
**search_reddit**: `['git bisect regression found tips', 'r/programming how I found a regression']`
**deep_research**: Describe behavior precisely (gradual vs cliff, deterministic vs intermittent).
### Best Practices:
- For complex regressions, deep_research builds structured investigation plans
- Ask for an investigation plan, not just "what caused it"

## 05. Memory Leak Investigation
### Tools: deep_research -> search_google -> scrape_pages -> search_reddit
### Query Templates:
**deep_research**: Attach suspected leaking code. Describe growth pattern (linear, exponential, step-function).
**search_google**: `['node.js memory leak event listener heap growing debugging', '"OOMKilled" kubernetes pod memory leak diagnosis']`
**scrape_pages**: `what_to_extract = "profiling commands|heap snapshot interpretation|common leak patterns"`
### Best Practices:
- Start with deep_research for a customized investigation plan for your stack
- State your memory limit and timeline ("grows from 256MB to 1GB in 6-8 hours") -- highly diagnostic

## 06. Race Condition Debugging
### Tools: deep_research -> search_google -> search_reddit
### Query Templates:
**deep_research**: Attach code from ALL layers. Describe timing ("1 in 200 requests").
**search_google**: `['ThreadSanitizer TSAN data race detection tutorial', 'react useState race condition stale closure fix']`
### Best Practices:
- Race conditions rarely have a single fix point -- deep_research identifies all fix points across layers
- Search for your runtime's race detector first (TSAN, `go test -race`, Helgrind)

## 07. Platform-Specific Bugs
### Tools: search_google -> scrape_pages -> search_reddit
### Query Templates:
**search_google**: `['"works on mac fails on linux" CI github actions', 'node.js native module linux alpine musl libc error']`
**scrape_pages**: Scrape CI runner specs and library cross-platform docs.
### Best Practices:
- Specify platforms precisely: "macOS 14 on Apple Silicon" and "ubuntu-22.04 on x86_64"
- deep_research traces the full dependency chain (your code -> library -> system lib)

## 08. CSS Layout Bugs
### Tools: search_google -> scrape_pages -> search_reddit
### Query Templates:
**search_google**: `['flexbox gap not working safari iOS fix', 'position sticky not working overflow parent']`
**scrape_pages**: Always scrape MDN and CanIUse: `what_to_extract = "browser support|known bugs|workarounds|specification behavior"`
### Best Practices:
- CSS bugs are often well-known gotchas (z-index stacking context, overflow + sticky)
- deep_research handles multi-property interactions that break differently across browsers

## 09. API Breaking Change Recovery
### Tools: search_google -> scrape_pages -> search_reddit
### Query Templates:
**search_google**: `['"Stripe API" breaking change v2024 deprecated endpoint', 'site:stripe.com/docs changelog']`
**scrape_pages**: `what_to_extract = "breaking changes|deprecated endpoints|migration code examples|sunset dates"`
**search_reddit**: `['"[API provider] broke changed deprecated"']` with date_after for recency.
### Best Practices:
- Speed matters -- your integration is broken in production
- Reddit threads appear within hours of breakages with community workarounds

## 10. Silent Data Corruption
### Tools: deep_research -> search_google -> search_reddit
### Query Templates:
**deep_research**: Attach code from every pipeline stage. Describe corruption pattern ("trailing zeros", "garbled text").
**search_google**: `['floating point precision loss data corruption database', 'ORM silently changing data types']`
### Best Practices:
- The corruption pattern is diagnostic: trailing zeros = numeric precision; garbled text = encoding mismatch
- Known patterns: JavaScript 64-bit ID truncation, JSON BigInt loss, MySQL silent truncation

## 11. Performance Regression Root Cause
### Tools: deep_research -> search_google -> scrape_pages
### Query Templates:
**deep_research**: Attach slow code and metrics. State before/after numbers.
**search_google**: `['node.js performance regression profiling production flamegraph', 'PostgreSQL query plan changed slow regression']`
**scrape_pages**: Extract profiling tool interpretation guides.
### Best Practices:
- First determine which layer is slow (database, application, network) before optimizing
- Ask deep_research for a prioritized fix list ordered by expected impact

## 12. Flaky Test Investigation
### Tools: deep_research -> search_google -> search_reddit
### Query Templates:
**deep_research**: Attach the flaky test code. Include failure rate and environment.
**search_google**: `['flaky test root causes classification debugging', 'jest test flaky timing async race condition fix']`
### Best Practices:
- "Fails 15% on CI, 0% locally" is critical diagnostic data -- always include it
- Google's taxonomy: async wait, ordering, shared state, concurrency, resource leak

## 13. Build Failure Resolution
### Tools: search_google -> scrape_pages -> search_reddit
### Query Templates:
**search_google**: `['"Cannot find module" typescript path alias tsconfig', 'docker build "npm ERR! ERESOLVE"']`
**scrape_pages**: `what_to_extract = "configuration syntax|working examples|common mistakes"`
**deep_research**: Attach ALL config files (package.json, tsconfig, bundler config) for consistency check.
### Best Practices:
- Build errors produce highly specific, googlable strings -- always quote them
- Build failures in monorepos are configuration consistency problems across multiple files

## 14. Security Vulnerability Patching
### Tools: search_google -> scrape_pages -> search_reddit
### Query Templates:
**search_google**: `['CVE-2024-XXXXX severity patch', 'site:nvd.nist.gov CVE-2024-XXXXX']`
**scrape_pages**: `what_to_extract = "CVSS score|attack vector|affected versions|patched version|mitigation steps"`
**search_reddit**: Search r/netsec first for expert analysis.
### Best Practices:
- Always scrape both NVD and Snyk -- NVD has official score, Snyk has better exploit analysis
- Extract "exploit conditions" to assess relevance to YOUR usage pattern

## 15. Encoding/Charset Bugs
### Tools: deep_research -> search_google -> scrape_pages
### Query Templates:
**deep_research**: Include exact garbled output. Attach database schema and connection string.
**search_google**: `['mojibake UTF-8 decoded as Latin-1 fix', 'MySQL utf8 vs utf8mb4 emoji truncation bug']`
### Best Practices:
- Specific mojibake patterns map to exact mis-conversions: `A` = UTF-8 decoded as Latin-1
- MySQL `utf8` is NOT full UTF-8; `utf8mb4` is required for emoji

---

## Universal Bug-Fixing Research Workflow

1. **Identify the bug class** from the table above to determine tool priority.
2. **Start with search_google** (for most types) using 5-7 diverse keyword angles. Quote the exact error message.
3. **Follow with scrape_pages** on top 3-5 URLs to extract fix code, config changes, or diagnostic steps.
4. **Use search_reddit** for human debugging narratives. Target language-specific subreddits.
5. **Use fetch_reddit** (fetch_comments=True, use_llm=False) on promising threads for full fix sequences.
6. **Use deep_research** for complex bugs involving multiple systems. Attach code files and describe what you tried.
7. **Iterate**: if research narrows but does not resolve, run a second pass with more specific queries.

## Steering notes

1. **Exact error in quotes is #1 query.** `"ERR_HTTP_HEADERS_SENT" fastify v5` -- always start here.
2. **Grep for error message** to find files to attach to `deep_research`.
3. **Cascading failures:** research each service independently, then search for interaction patterns.
4. **Timing bugs** (race conditions): search general pattern, not specific error.
5. **Log correlation:** `"[framework] structured logging" debug` for log-based diagnosis.
