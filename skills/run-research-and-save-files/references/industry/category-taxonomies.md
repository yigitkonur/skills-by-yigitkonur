# Category Taxonomies

How to choose context-specific folder names and comparison criteria for different industry research verticals.

## Selection Rule

Pick the taxonomy that matches the buyer or researcher decision. Then rename folders so each path says what the file answers in that vertical.

Good:

```text
_cross-product/01-pricing-unit-economics/
_cross-ecosystem/05-license-governance-security/
_cross-provider/03-data-coverage-quality/
```

Weak:

```text
_cross-product/01-context/
_cross-product/05-security/
_cross-product/07-other/
```

## SaaS Or Product Category

Use for vendor landscapes, B2B SaaS, infrastructure products, API products, marketplaces, or buying decisions.

Entity contexts:

```text
00-overview/
01-pricing-unit-economics/
02-product-capabilities/
03-integrations-ecosystem/
04-operations-reliability-support/
05-security-compliance-legal/
06-audience-reviews-reddit/
07-benchmarks-performance-tests/
08-buyer-fit-alternatives/
09-sources-claims-gaps/
```

Cross contexts:

```text
00-category-map-and-rankings/
01-pricing-unit-economics/
02-capability-matrix/
03-integrations-ecosystem/
04-operations-reliability-support/
05-security-compliance-legal/
06-audience-market-signal/
07-benchmarks-performance-tests/
08-buyer-scenarios-shortlists/
09-sources-claims-gaps/
```

Required emphasis:

- native pricing units, overages, gated enterprise terms, unit economics
- product layer and control surface
- integrations and switching cost
- status pages, incident history, SLA, support, changelog
- security, privacy, compliance, acceptable use, legal risk
- reviews, Reddit, HN, forums, migration stories, pricing complaints
- benchmark claims and buyer-run test plan

## Open-Source Technology Ecosystem

Use for frameworks, libraries, developer tools, model runtimes, infrastructure components, or open-source alternatives.

Entity contexts:

```text
00-overview/
01-project-health-maintenance/
02-installation-api-devex/
03-architecture-extension-model/
04-ecosystem-integrations/
05-license-governance-security/
06-community-github-reddit/
07-benchmarks-performance-reproducibility/
08-adoption-fit-alternatives/
09-sources-claims-gaps/
```

Cross contexts:

```text
00-ecosystem-map-and-rankings/
01-project-health-maintenance/
02-api-devex-and-documentation/
03-architecture-extension-model/
04-ecosystem-integrations/
05-license-governance-security/
06-community-maintainer-signal/
07-benchmarks-performance-reproducibility/
08-adoption-scenarios-alternatives/
09-sources-claims-gaps/
```

Required emphasis:

- release cadence, maintainer bus factor, issue velocity, abandoned forks
- license compatibility and governance
- install path, API stability, docs quality, examples, migration friction
- benchmarks and reproducibility, not only README claims
- GitHub issues, discussions, Reddit, HN, Stack Overflow, Discord/forum evidence

## Developer Infrastructure Or Cloud Platform

Use for hosting, databases, observability, auth, serverless, orchestration, or cloud runtime categories.

Suggested contexts:

```text
00-platform-map-and-rankings/
01-pricing-capacity-unit-economics/
02-runtime-architecture-control-plane/
03-deployment-integrations-devex/
04-reliability-scaling-observability/
05-security-compliance-data-boundaries/
06-practitioner-incidents-migrations/
07-performance-benchmarks-load-tests/
08-workload-fit-exit-paths/
09-sources-claims-gaps/
```

Required emphasis:

- pricing under realistic capacity and traffic
- data plane vs control plane
- regions, scaling, quotas, cold starts, failover, backup/restore
- lock-in and exit path
- incident history and migration stories

## Data, API, Or Content Provider Market

Use for search APIs, data vendors, scraping APIs, enrichment providers, vector data, or content/license markets.

Suggested contexts:

```text
00-provider-map-and-rankings/
01-pricing-usage-unit-economics/
02-data-coverage-quality-freshness/
03-api-contracts-integrations/
04-operations-rate-limits-support/
05-data-rights-compliance-privacy/
06-audience-accuracy-complaints/
07-benchmarks-evaluation-methods/
08-use-case-fit-vendor-risk/
09-sources-claims-gaps/
```

Required emphasis:

- coverage, freshness, accuracy, deduplication, data provenance
- rate limits, SLAs, quota behavior, retries
- contractual rights, redistribution, privacy, retention
- evaluation datasets and test queries

## Regulated Or Compliance-Heavy Industry

Use for healthcare, finance, insurance, legal, education, government, or security markets.

Suggested contexts:

```text
00-industry-map-and-regulatory-frame/
01-market-structure-and-economics/
02-product-capabilities-and-workflows/
03-integrations-and-data-exchange/
04-operations-risk-and-service-model/
05-regulatory-compliance-legal/
06-stakeholder-voice-and-adoption/
07-outcomes-evidence-and-benchmarks/
08-procurement-fit-and-risk/
09-sources-claims-gaps/
```

Required emphasis:

- regulations, certifications, audit requirements, legal restrictions
- stakeholder groups and procurement barriers
- risk controls, data handling, retention, explainability
- outcomes evidence and clinical/financial/legal proof where applicable

## Consumer Apps, Hardware, Or Media Ecosystem

Use for consumer products, apps, devices, creator tools, marketplaces, entertainment, or prosumer categories.

Suggested contexts:

```text
00-market-map-and-positioning/
01-pricing-packaging-monetization/
02-product-experience-features/
03-platform-ecosystem-integrations/
04-operations-availability-support/
05-privacy-safety-policy-risk/
06-audience-reviews-social-signal/
07-performance-quality-tests/
08-user-fit-alternatives/
09-sources-claims-gaps/
```

Required emphasis:

- onboarding, UX, retention, subscriptions, app-store reviews
- social signal, influencer bias, support complaints
- privacy, safety, content moderation, policy issues
- real user scenarios and alternatives

## Naming Rules

1. Preserve numeric order for scanability.
2. Prefer 2-4 domain words after the prefix.
3. Use the buyer's language, not internal architecture.
4. Include the risk domain in the folder name when it matters: `compliance`, `license`, `data-rights`, `regulatory`, `governance`.
5. Use `sources-claims-gaps` for final verification folders across all archetypes.
6. Do not create a category just because a template has it; create it because evidence and decisions need it.

## Category Completeness Check

Ask these questions before dispatch:

- Does every category answer a distinct decision question?
- Are pricing/economics separated from capability claims?
- Is practitioner evidence separated from official documentation?
- Is source verification separate from synthesis?
- Are category names specific enough that another agent can infer what belongs there?
- If this were an open-source corpus, would SaaS-only names still make sense? If not, rename them.
