# Library & Dependency Research Guide

## Quick Reference: Which Tools For Which Research Need

| # | Research Need | Primary Tools | Why These Tools |
|---|-------------|--------------|-----------------|
| 01 | Choosing Between Competing Libraries | all 5 tools | Multi-dimensional comparison needs benchmarks (scrape), sentiment (Reddit), synthesis (deep_research) |
| 02 | Checking for Known Issues Before Adoption | search_google -> scrape_pages -> search_reddit -> fetch_reddit | GitHub issues are the source of truth; Reddit surfaces bugs not yet in issue trackers |
| 03 | Finding Correct Configuration | search_google -> scrape_pages -> search_reddit -> deep_research | Official docs have the syntax; scrape extracts config snippets; Reddit has battle-tested configs |
| 04 | Version Upgrade Impact Assessment | search_google -> scrape_pages -> search_reddit -> fetch_reddit -> deep_research | Changelogs document changes; Reddit has real upgrade stories; deep_research plans upgrade strategy |
| 05 | Understanding Internal Behavior | search_google -> scrape_pages -> deep_research -> search_reddit | Source code explanations live in blog posts; deep_research synthesizes architecture docs |
| 06 | Debugging a Library's Unexpected Behavior | search_google -> search_reddit -> fetch_reddit -> scrape_pages -> deep_research | Exact errors are highly searchable; Reddit has "same issue" threads; scrape confirms expected vs actual behavior |
| 07 | Security Audit of Dependencies | search_google -> scrape_pages -> search_reddit -> deep_research | CVE databases are scrapeable; Snyk/GitHub advisories have structured data; deep_research does risk assessment |
| 08 | Finding Alternatives to Abandoned Packages | search_reddit -> fetch_reddit -> search_google -> scrape_pages -> deep_research | Reddit is the #1 source for "what should I use instead"; search_google finds curated alternative lists |
| 09 | Understanding Breaking Changes | search_google -> scrape_pages -> search_reddit -> fetch_reddit -> deep_research | Changelogs are the source; scrape extracts version-specific changes; Reddit has fix sequences |
| 10 | Evaluating Library Maturity | search_google -> scrape_pages -> search_reddit -> fetch_reddit -> deep_research | Metrics live on npm/GitHub; Reddit has production experience reports; deep_research does risk-calibrated assessment |

---

## 01. Choosing Between Competing Libraries

### Recommended Tools: all 5
### Query Templates:
**deep_research** -- The primary tool. Structure the question with exact constraints:
```
"WHAT I NEED: A comprehensive comparison of Prisma, Drizzle, and Kysely for a TypeScript/PostgreSQL project.
WHY: Starting a new production API and need to choose an ORM that will scale.
WHAT I KNOW: Prisma has the largest community but reportedly slow cold starts. Drizzle is newer but claims better performance.
SPECIFIC QUESTIONS: 1) Cold-start times in serverless? 2) Type-safety for complex queries? 3) Migration tooling maturity? 4) Learning curve from raw SQL? 5) Maintenance activity?"
```
**search_google** -- Search for benchmark comparisons, feature matrices, and "X vs Y" articles:
```
keywords = ["Prisma vs Drizzle vs Kysely benchmark comparison 2025", "TypeScript ORM comparison production experience", "site:npmtrends.com prisma drizzle"]
```
**scrape_pages** -- Extract from benchmark articles, npmtrends, and official comparison pages:
```
what_to_extract = "benchmark results|bundle size|type safety features|migration tools|community size|release frequency"
```
**search_reddit** -- Search for "switched from X to Y" threads:
```
queries = ["Prisma vs Drizzle production experience", "switched from Prisma to Drizzle why", "r/typescript ORM recommendation 2025"]
```
**fetch_reddit** -- Fetch full comparison threads (fetch_comments=True). Comments contain benchmark numbers and migration stories.
### Best Practices:
- State exact project constraints in deep_research (team size, DB type, deployment model, performance requirements)
- Use 5-10 search_reddit queries covering both "X vs Y" and "recommend me an X" angles
- Scrape both library READMEs for feature claims; scrape npm for adoption metrics
- Reddit comments have the most honest take on DX issues that docs never mention
- Run deep_research AFTER gathering search_google and Reddit data for the most informed synthesis

## 02. Checking for Known Issues Before Adoption

### Recommended Tools: search_google -> scrape_pages -> search_reddit -> fetch_reddit
### Query Templates:
**search_google** -- Target GitHub issues and known bugs:
```
keywords = ["site:github.com/[org]/[lib]/issues label:bug", "[library] known issues gotchas production", "[library] memory leak OR crash OR data loss"]
```
**scrape_pages** -- Extract from GitHub issue list and Snyk advisor page:
```
what_to_extract = "open bugs|critical issues|issue count|response time|known limitations|breaking bugs|severity"
```
**search_reddit** -- Search for complaints and warnings:
```
queries = ["[library] problems issues bugs production", "[library] regret used in production", "r/[language] [library] issues gotchas"]
```
**fetch_reddit** -- Fetch "anyone else experiencing X" threads. Comments reveal scale-dependent issues.
### Best Practices:
- Check open issues on GitHub filtered by label:bug for severity assessment
- Scrape the Snyk advisor page (snyk.io/advisor/npm-package/[lib]) for a health score
- Reddit surfaces issues that maintainers may not have acknowledged yet
- Look for recurring complaints -- if 5 people report the same issue in different threads, it is real

## 03. Finding Correct Configuration

### Recommended Tools: search_google -> scrape_pages -> search_reddit -> deep_research
### Query Templates:
**search_google** -- Search for the exact config directive or option:
```
keywords = ["[library] configuration options reference complete list", "[library] [specific-option] example usage", "\"[library].config\" TypeScript correct setup"]
```
**scrape_pages** -- Extract config syntax directly from docs:
```
what_to_extract = "configuration options|required fields|default values|example configs|TypeScript types|deprecated options"
```
**search_reddit** -- Search for validated working configs:
```
queries = ["[library] config example working production", "[library] configuration issue resolved", "r/[language] [library] config help"]
```
**deep_research** -- Attach ALL configuration files. Ask for a validated, consistent set.
### Best Practices:
- Official docs have the syntax, but scrape_pages extracts it cleanly without surrounding prose
- Reddit has battle-tested configurations that combine multiple options correctly
- deep_research is essential for multi-file configuration (tsconfig + bundler + linter) -- it checks consistency across files
- Search for "example" and "working config" rather than "documentation" for practical results

## 04. Version Upgrade Impact Assessment

### Recommended Tools: search_google -> scrape_pages -> search_reddit -> fetch_reddit -> deep_research
### Query Templates:
**search_google** -- Search changelog and migration guides:
```
keywords = ["[library] v[X] to v[Y] migration guide", "[library] v[Y] breaking changes changelog", "site:github.com/[org]/[lib]/releases tag/v[Y]"]
```
**scrape_pages** -- Extract from release notes and CHANGELOG.md:
```
what_to_extract = "breaking changes|removed APIs|renamed functions|changed defaults|new required configuration|migration steps|before and after code"
```
**search_reddit** -- Search for upgrade experience threads:
```
queries = ["[library] v[Y] upgrade issues", "[library] v[X] to v[Y] broke my app", "r/[framework] [library] upgrade experience"]
```
**fetch_reddit** -- Fetch full threads. The fix is in comment #47, after 3 failed attempts.
**deep_research** -- Attach your current code. Ask for: complete list of affected APIs, mechanical fix patterns, and third-party compatibility.
### Best Practices:
- Scrape the GitHub release page for curated breaking change summaries
- Scrape the specific PR that introduced a breaking change for full rationale
- Reddit threads contain verified fix sequences -- "tried X, didn't work; tried Y, fixed it"
- deep_research identifies ALL affected files (including the 5 that haven't crashed yet but will)
- Always ask about third-party dependency compatibility with the new version

## 05. Understanding Internal Behavior

### Recommended Tools: search_google -> scrape_pages -> deep_research -> search_reddit
### Query Templates:
**search_google** -- Target architecture explanations and deep dives:
```
keywords = ["[library] internals how it works architecture", "[library] source code walkthrough explained", "\"[library]\" virtual DOM reconciliation algorithm explained"]
```
**scrape_pages** -- Extract from architecture blog posts and documentation:
```
what_to_extract = "architecture overview|internal data structures|algorithm explanation|execution flow|performance characteristics"
```
**deep_research** -- Ask about the specific internal you need to understand. Include why you need to know.
**search_reddit** -- Search for ELI5 and "how does X actually work" threads.
### Best Practices:
- Understanding internals is usually needed to fix a subtle bug or optimize performance
- Blog posts by library authors contain the best explanations of design decisions
- deep_research synthesizes multiple source code explanations into a coherent mental model
- Reddit "how does X work" threads often get replies from maintainers

## 06. Debugging a Library's Unexpected Behavior

### Recommended Tools: search_google -> search_reddit -> fetch_reddit -> scrape_pages -> deep_research
### Query Templates:
**search_google** -- Include the exact unexpected behavior:
```
keywords = ["[library] [function] returns undefined instead of expected value", "[library] [function] behaves differently than documented"]
```
**search_reddit** -- Find "same issue" threads:
```
queries = ["[library] [function] unexpected behavior", "[library] [function] not working as documented"]
```
**fetch_reddit** -- Fetch full threads where others debug the same issue. Comments reveal parameter subtleties.
**scrape_pages** -- Scrape the official docs for the function's expected behavior:
```
what_to_extract = "function signature|parameters|return value|edge cases|caveats|version differences"
```
**deep_research** -- Attach your code and the library docs. Ask for a diagnosis.
### Best Practices:
- First confirm expected behavior by scraping the official docs for that specific function
- Reddit threads about unexpected behavior often reveal undocumented edge cases
- GitHub issues frequently contain maintainer explanations of "intended behavior vs bug"
- deep_research can compare your usage pattern against the documented API to find the mismatch

## 07. Security Audit of Dependencies

### Recommended Tools: search_google -> scrape_pages -> search_reddit -> deep_research
### Query Templates:
**search_google** -- Target security databases and audit tools:
```
keywords = ["site:nvd.nist.gov [library]", "site:github.com/advisories [library]", "[library] CVE vulnerability security", "[ecosystem] dependency audit tool comparison"]
```
**scrape_pages** -- Extract from CVE pages and security advisories:
```
what_to_extract = "CVE IDs|CVSS scores|affected versions|patched versions|exploit conditions|severity|mitigation"
```
**search_reddit** -- Search r/netsec for expert analysis. Search for "supply chain attack" + ecosystem.
**deep_research** -- Ask for a complete audit: known CVEs, transitive dependency risk, and security posture assessment.
### Best Practices:
- Search for audit tool comparisons to choose the right scanner for your ecosystem
- Include "false positive npm audit" to learn which warnings are actionable
- Scrape Snyk and NVD for structured vulnerability data
- deep_research synthesizes scan results with threat landscape into a prioritized patching plan

## 08. Finding Alternatives to Abandoned Packages

### Recommended Tools: search_reddit -> fetch_reddit -> search_google -> scrape_pages -> deep_research
### Query Templates:
**search_reddit** -- THE most valuable tool for this use case:
```
queries = [
    "[abandoned-library] abandoned what to use instead",
    "alternative to [abandoned-library] 2025",
    "switched from [abandoned-library] to what",
    "[abandoned-library] replacement drop-in compatible",
    "[abandoned-library] community fork active development"
]
```
**fetch_reddit** -- Fetch 10-15 "what should I use instead" threads:
```
urls = ["https://reddit.com/r/node/comments/.../request_library_deprecated_what_now/", ...]
fetch_comments = True  # Recommendations are in comments; exact library names, version numbers, and migration commands
```
**search_google** -- Find curated lists and comparison articles:
```
keywords = ["[abandoned-library] alternative replacement 2025", "[abandoned-library] fork actively maintained", "awesome [category] curated list github"]
```
**scrape_pages** -- Scrape replacement library READMEs, migration guides, and npm pages:
```
what_to_extract = "features|API examples|migration guide|weekly downloads|last release date|contributor count"
```
**deep_research** -- Evaluate top 2-4 candidates with your codebase context. Attach your current usage code. Ask about migration effort per call site.
### Best Practices:
- Reddit is the #1 source because "what should I use instead" threads generate dozens of recommendations with first-hand migration experiences
- Search for "switched from" and "migrated from" for real transitions, not hypothetical comparisons
- Search for "drop-in replacement" and "community fork" for lowest migration cost
- fetch_reddit with use_llm=False preserves exact library names and code snippets
- deep_research evaluates the shortlist with YOUR codebase constraints -- number of call sites, features used, deploy setup

## 09. Understanding Breaking Changes

### Recommended Tools: search_google -> scrape_pages -> search_reddit -> fetch_reddit -> deep_research
### Query Templates:
**search_google** -- Find changelogs, release notes, and migration guides:
```
keywords = ["[library] [version] breaking changes changelog", "[library] [version] migration guide codemod", "site:github.com [library] BREAKING CHANGE [version]"]
```
**scrape_pages** -- Extract from release page, CHANGELOG.md, and upgrade guide:
```
what_to_extract = "breaking changes|removed APIs|renamed functions|changed defaults|before and after code examples|migration steps"
```
**search_reddit** -- Find error-to-fix mappings from devs who already hit the breaking change:
```
queries = ["[library] [version] broke my app", "[exact error message from your build]", "[function-name] no longer works [library] update"]
```
**fetch_reddit** -- Fetch threads that match your exact error. Comments contain verified fix sequences.
**deep_research** -- Attach broken files. Ask for: complete list of affected APIs, codemod availability, third-party compatibility.
### Best Practices:
- Search for exact error messages in quotes -- the highest-signal query for breaking changes
- Scrape the specific PR that introduced the breaking change for full rationale
- Reddit threads contain trial-and-error sequences leading to the correct fix
- fetch_reddit captures "EDIT: solved" markers that confirm the fix
- deep_research identifies all 17 affected files, not just the 12 that are currently crashing

## 10. Evaluating Library Maturity

### Recommended Tools: search_google -> scrape_pages -> search_reddit -> fetch_reddit -> deep_research
### Query Templates:
**search_google** -- Find maturity indicators:
```
keywords = ["[library] production use case study", "[library] who uses companies adoption", "[library] npm weekly downloads trend 2025", "ThoughtWorks technology radar [library]"]
```
**scrape_pages** -- Extract quantitative metrics:
```
urls = ["https://www.npmjs.com/package/[library]", "https://github.com/[org]/[library]", "https://snyk.io/advisor/npm-package/[library]"]
what_to_extract = "weekly downloads|GitHub stars|open issues|closed issues ratio|contributors|last release date|dependent packages|Snyk health score"
```
**search_reddit** -- Find production experience reports:
```
queries = ["[library] production ready 2025", "[library] used in production experience", "[library] issues problems at scale"]
```
**fetch_reddit** -- Fetch "is X production ready" threads. Comments provide multi-dimensional maturity evidence:
- "8/10 say works great for CRUD" = mature for that use case
- "3/10 say docs have gaps" = moderate documentation maturity
**deep_research** -- State your risk tolerance ("fintech API" vs "internal tool"). Ask about bus factor, financial sustainability, and comparative maturity.
### Best Practices:
- Always scrape both npm and GitHub -- downloads measure adoption, GitHub metrics measure maintenance health
- Scrape npm-stat.com for download trend graphs -- declining trends signal trouble
- Snyk advisor provides a composite health score covering maintenance, community, security, and popularity
- Reddit provides qualitative maturity -- "100K downloads but 90% is one tutorial that includes it by default"
- deep_research produces risk-calibrated assessment for YOUR use case: a library mature for a blog engine may be immature for a financial system
- Ask about bus factor -- a library maintained by one person is high-risk regardless of other metrics

---

## Universal Library Research Workflow

1. **Define your requirements** before researching: deployment model, performance needs, team size, risk tolerance, and how long you need the dependency to be maintained.
2. **Start with search_google** (5-7 keywords) to discover candidates and comparison articles.
3. **Use scrape_pages** on comparison articles, npm/GitHub pages, and official docs to extract structured metrics and feature lists.
4. **Use search_reddit** (5-7 queries) to find real-world usage reports. Target language-specific subreddits. Search for "experience", "production", "switched from", and "regret" terms.
5. **Use fetch_reddit** (fetch_comments=True, use_llm=False) on the 5-10 most relevant threads for full migration stories, code examples, and warnings.
6. **Use deep_research** as the synthesis step, incorporating your specific constraints. Attach relevant code files. Ask 3-5 pointed questions.
7. **Iterate**: initial research narrows from many candidates to 2-3. Run a second pass focused on the finalists with more specific queries (migration effort, edge case handling, operational costs).
