# Sources and synthesis decisions

This page is provenance, not a runtime reading requirement. The skill's operational
instructions are package-local and require no separately installed source skill.
Source content was compared during design; the resulting workflow is adapted to
this repository's role, evidence, isolation, and delivery contracts.

## Comparison

| Source | Focus and strength | Gap for this campaign | Inherit / avoid |
|---|---|---|---|
| [Matt Pocock: to-tickets](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/to-tickets/SKILL.md) | Bounded vertical slices, real blocking edges, immediately ready frontier | Tracker setup and interactive approval are assumed; tickets are not independently reviewed E2E evidence | Inherit bounded handoffs and true DAG edges; avoid mandatory setup-skill/user-review dependencies |
| [Matt Pocock: implement](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/implement/SKILL.md) | Scoped implementation, developer checks, final review and commit | Does not separate implementer from campaign executor/verifier or model runtime generations | Inherit focused implementation/checks; add independent retest and serial integration locally |
| [Repository tunnel skill](https://github.com/yigitkonur/skills-by-yigitkonur/tree/main/skills/use-cloudflare-tunnel) | Origin/public/client reachability and process tracking | Helper removes shared credentials and uses global process cleanup; static proxy does not preserve every dev transport | Inherit separate readiness layers; avoid copying cleanup/proxy scripts and fixed DNS timing assumptions |
| [Repository browser skill](https://github.com/yigitkonur/skills-by-yigitkonur/tree/main/skills/run-agent-browser) | Real browser interaction and awareness of shared provider sessions | Host/provider-specific commands and setup do not generalize to every harness | Inherit actual-client evidence and explicit session ownership; bind tools during Wave 0 |
| [yq duplicate-key test](https://github.com/mikefarah/yq/blob/338eca45467f7d1159dd2ce10f894dd9cceef637/pkg/yqlib/operator_traverse_path_test.go#L630) | Convenient structured queries; source test shows duplicate-key traversal yielding the later value | Successful query cannot establish strict record validity | Keep yq optional; validate with the bundled strict YAML/parser/schema path |
| [YAML parser documentation](https://eemeli.org/yaml/) and [Ajv documentation](https://ajv.js.org/guide/getting-started.html) | Parsing and schema validation as separate mechanical responsibilities | Neither judges whether a screenshot semantically satisfies an expectation | Use strict machine checks plus independent artifact inspection; accepted submission is not PASS |

Skill discovery used `skill-dl` where available and a `npx skills find` fallback
when its macOS Bash compatibility prevented discovery. These research tools are
not required to execute the distributed skill. Sources were distilled, not
copied as another package under a new name.

## Material external constraints

- [GitHub issue-closing syntax](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue): closing keywords also accept qualified repository references and colons. Avoid automatic closure in PR descriptions and commit messages until independent retest proves resolution.
- [Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/): random URLs, 200 concurrent in-flight requests, HTTP 429 at the limit, no SSE support, and no uptime/SLA guarantee. Select based on actual protocol needs.
- [Cloudflare firewall requirements](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/tunnel-with-firewall/): outbound QUIC uses UDP 7844 and HTTP/2 uses TCP 7844.
- [Cloudflare routing](https://developers.cloudflare.com/tunnel/concepts/routing/): replicas on the same tunnel UUID share an endpoint; independent addressing needs different routing identities.
- [MCP transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports) and [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http): stdio attaches a client-launched subprocess; HTTP replies may use JSON or SSE. Inspect the actual server transport rather than assuming Quick Tunnel supports every MCP server.

These constraints were checked during the September 2026 design. During runtime
setup, verify installed CLI syntax and any material service behavior that has
changed. Fixed DNS propagation/negative-cache timings and universal process
detachment recipes are deliberately not part of the contract.
