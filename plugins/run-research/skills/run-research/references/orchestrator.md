# Deep Single-Question Path

Use this reference only when one technical research question is too broad
for a single pass but still has one decision, one answer, and one final
markdown synthesis.

This is not corpus research. Do not create per-entity packs, product
profiles, comparison-template trees, buyer guides, category landscapes,
or reusable source-ledger corpora. Route those requests to
`run-deep-research`.

## When to Use

Use the deep path only when all are true:

- The request is one technical question, not a market/category landscape.
- The question spans 3+ distinct technical subdomains that need separate
  reading lenses.
- Independent evidence gathering would reduce context overload or
  source-class bias.
- The final deliverable can be one source-backed markdown answer.

Examples that fit:

- Decide whether to migrate a production API from library A to B, using
  maintainer docs, security advisories, benchmark data, and migration
  reports.
- Diagnose a cross-version production bug where runtime changes,
  framework changelogs, GitHub issues, and Reddit workarounds all matter.
- Choose an architecture pattern where official guidance, incident
  reports, performance evidence, and practitioner regret each need
  separate scrutiny.

Redirect instead:

- 5+ vendors/entities or products need comparison.
- The user asks for a market map, industry landscape, buyer comparison,
  evidence pack, or reusable corpus.
- The user asks to discover or compare GitHub repos. Use
  `run-github-scout`.
- The answer can be produced from one docs page or local codebase
  inspection.

## Subdomain Split

Split by evidence lens, not by product or entity.

Good splits:

| Lens | Source classes |
|---|---|
| Official behavior | docs, changelogs, release notes, API references |
| Maintainer intent | GitHub issues, PRs, RFCs, maintainer comments |
| Production experience | Reddit, HN, incident reports, migration posts |
| Security/performance | CVEs, advisories, benchmarks, postmortems |

Bad splits:

- one agent per vendor or entity
- one agent per section of a pre-decided report
- one agent per search keyword group with no distinct reading lens

## Brief Shape

Each researcher brief must include:

1. The single research question and user context.
2. The exact lens assigned to this researcher.
3. Source classes to prioritize and source classes to ignore.
4. Required extraction shape, including quotes for numeric, versioned,
   priced, API, CVE, or error-string claims.
5. A hard rule that search snippets and tool-provided synthesis are not
   citable evidence.
6. A compact source-notes output with URL, source type, author/date when
   available, research date, claim supported, and caveat.
7. A concise unresolved-gaps section.

Researchers gather evidence. The main agent writes the final answer.

## Output Discipline

Default to one in-chat markdown synthesis:

- recommendation or answer first
- evidence table or comparison table when useful
- conditions that would change the answer
- counter-arguments or contradictions
- source ledger or source notes
- unresolved gaps

Only create files when the user explicitly asks for persistent output.
If files are requested, use a small numbered folder:

```
research-question/
|-- 00-summary.md
|-- 01-official-behavior.md
|-- 02-maintainer-intent.md
|-- 03-production-experience.md
`-- 04-source-notes.md
```

Keep files lens-based and minimal. Do not create per-entity folders.

## Synthesis Gate

Before writing the final answer:

- Read every researcher output in full.
- Trace every non-trivial claim to scraped source content, not snippets.
- Resolve or surface contradictions.
- Mark inference separately from confirmed facts.
- Include unresolved gaps instead of smoothing them into confidence.
- Collapse duplicate sources; source volume is not source quality.

Stop when the original question is answered with enough evidence for the
stakes, or when remaining gaps are explicitly named and cannot be closed
with available sources.
