# Output Architecture

How to design the documentation tree before dispatching any researchers. The structure determines the quality — a well-designed tree forces each researcher to produce focused, non-overlapping, independently useful documentation.

## The Bracket-Path System

Use bracket notation (`[segment]`) for dynamic parts of the file tree that will be filled based on the specific research topic:

```
docs/research/[topic-name]/
├── 00-master-summary.md
├── [domain-a]/
│   ├── 01-[specific-topic].md
│   ├── 02-[specific-topic].md
│   └── 03-[specific-topic].md
├── [domain-b]/
│   └── 01-[specific-topic].md
├── [cross-cutting]/
│   └── 01-[concern].md
└── [context]/
    └── 01-[practitioner-feedback].md
```

**Why brackets work:** They force the orchestrator to think about taxonomy — what are the actual domains, what belongs where. The brackets signal "this will be filled with a descriptive name." They prevent generic names like `section1/` or `part-a/`.

**When brackets are resolved:** During Phase 2b, the orchestrator replaces every bracket with a concrete kebab-case name:

```
docs/research/sentry-implementation/
├── 00-master-summary.md
├── common/
│   ├── 01-sdk-overview-and-architecture.md
│   ├── 02-error-monitoring-fundamentals.md
│   └── 03-tracing-and-performance.md
├── platform-specific/
│   ├── ios/
│   │   ├── 01-ios-setup-and-initialization.md
│   │   └── 02-ios-error-monitoring.md
│   └── macos/
│       ├── 01-macos-setup-and-initialization.md
│       └── 02-macos-error-monitoring.md
└── context/
    ├── 01-community-feedback-and-gotchas.md
    └── 02-sentry-cocoa-skill-file-analysis.md
```

## Naming Rules

### Folders

- Kebab-case, descriptive: `platform-specific/`, `cross-cutting/`, `context/`
- Max 2 nesting levels: `[domain]/[subdomain]/` — no deeper
- Folder names describe the CATEGORY of content, not the topic being researched

### Files

- **Numbered prefix:** `01-`, `02-`, `03-` — ensures consistent ordering in file listings
- **Hyphenated topic:** Forces specificity. `01-ios-setup-and-initialization.md` not `01-setup.md`
- **Platform prefix when platform-specific:** `01-ios-...`, `01-macos-...` — makes platform clear at a glance
- **Special files:** `00-master-summary.md` always at root (00 sorts first)

### What Makes a Good File Name

| Good | Bad | Why |
|------|-----|-----|
| `01-ios-setup-and-initialization.md` | `01-setup.md` | Specificity — which platform? what kind of setup? |
| `07-fingerprinting-and-grouping.md` | `07-config.md` | Descriptive — what configuration exactly? |
| `01-community-feedback-and-gotchas.md` | `01-feedback.md` | Content signal — the reader knows what's inside |
| `06-ios-firebase-migration.md` | `06-migration.md` | From what? To what? Both should be in the name |

## Domain Design Patterns

### By Platform (when researching cross-platform tools)

```
[tool-name]-implementation/
├── common/           # Shared across platforms
├── platform-specific/
│   ├── ios/
│   └── macos/
└── context/          # Community feedback, integration maps
```

### By Feature Area (when researching a single platform)

```
[topic]-research/
├── core/             # Fundamental capabilities
├── advanced/         # Deep configuration, edge cases
├── integration/      # How it connects to other systems
└── context/          # Community, alternatives, trade-offs
```

### By Stakeholder (when researching for decision-making)

```
[decision]-analysis/
├── technical/        # Architecture, performance, compatibility
├── business/         # Pricing, licensing, vendor risk
├── operational/      # Maintenance, monitoring, incident response
└── context/          # Community experience, case studies
```

## File Independence Rule

Every documentation file must be independently useful. A developer should be able to read ONE file and act on it without reading the others.

This means each file should:
- State its scope at the top
- Include relevant code examples (not just "see other file")
- Cite its sources directly
- Be self-contained for its specific topic

Cross-references are fine for context ("see `common/03-tracing.md` for the full trace model") but the file should not REQUIRE reading another file to be actionable.

## Agent-to-Output Mapping

After designing the tree, map each researcher agent to specific output files:

```
Agent 1 (iOS SDK)        → platform-specific/ios/01 through ios/06
Agent 2 (macOS SDK)      → platform-specific/macos/01 through macos/05
Agent 3 (Configuration)  → common/07, common/09, common/10
Agent 4 (Enrichment)     → common/08, common/11
Agent 5 (Tracing)        → common/03, common/04, common/05
Agent 6 (Logs/Overview)  → common/01, common/02, common/06, context/02
Agent 7 (Community)      → context/01
```

This mapping is the contract between the orchestrator and each agent. The agent knows what docs it's responsible for producing evidence to fill.

## The 00-master-summary.md Structure

Always the LAST file written. Contains:

1. **Document index** — table linking to every file with a 1-line description
2. **Critical findings** — the 5-10 most important things the reader must know
3. **Cross-domain insights** — connections between domains that individual researchers couldn't see
4. **Action items** — prioritized list of what to do next
5. **Research coverage** — what this research covers and what it doesn't
6. **Source summary** — aggregate sources used across all docs
