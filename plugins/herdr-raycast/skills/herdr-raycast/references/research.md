# research-mcp for decisions

Back to [SKILL.md](../SKILL.md). Measured on 2026-10-02 with the question "which
MCP framework for a TypeScript server?".

| tool | gives | seen |
| --- | --- | --- |
| `plan-research` (`objective`) | clusters, checkable evidence requirements, first-wave and reserve queries, budgets, stop rules | optional; plan plus the whole search wave took 96 s |
| `web-search` (`queries`, 1–50) | ranked, de-duplicated leads with snippets; leads, not evidence | 41 queries in 3 parallel calls; about 40–50k characters per call |
| `extract-evidence` (`urls` ≤ 20, `evidence_requirements` ≤ 20) | per requirement: status, verified quotations, line locators | 3 calls of 7–8 URLs hit their 180 s deadline with 10 of 22 pages pending; 6 calls of 1–3 URLs then fetched all 10 in about a minute; a 2971-line README came back as a few dozen quotes |

Using it as the conductor:

- One decision, one question. Write four to eight checkable requirements
  ("supports spec 2026-07-28", "minimum Node version", "latest release").
- When you know where the answer lives (official docs, the library's README),
  skip search and extract from those URLs directly.
- Search only to find URLs: about five queries per call, several calls in
  parallel. Never cite a snippet.
- Extract with one to three URLs per call, several calls in parallel. A pending
  URL may be retried once, as the reply says. A page that simply lacks the
  answer is a result, not a failure.
- `partial` is the normal status: the quotes are verified, the interpretation is
  yours. Decide from the quotes.
- Evidence beats popularity: the most-starred TypeScript "FastMCP" said in its
  own README that it does not support the current MCP spec, which neither its
  star count nor any search snippet showed.
- Put the decision and two or three source URLs into the agent's brief. When the
  answer depends on the code in front of the agent, brief the agent to find out
  instead.
