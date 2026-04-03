# Mission Prompt Templates

How to write researcher agent prompts that produce world-class output. These templates encode the orchestrator philosophy into concrete prompt structures.

## The Mission Brief Structure

Every researcher agent gets a prompt with these sections, in this order:

```
## Context

{Dense prose: why this research exists, what the project needs, what the
researcher should know about the architecture/domain/privacy posture/
existing decisions. 200-500 words of rich, purposeful context.}

## Mission

{One paragraph: the observable end-state. Not "research X" but
"produce implementation-ready documentation covering Y that a developer
can follow without consulting any other source."}

{Then the research domains, each as a bold header with specific
subtopics listed underneath. These are understanding goals, not
search queries.}

## Research Guidance

{Source hints: specific URLs to fetch, search angles to explore,
extraction fields to target. Set ceilings with release valves.}

IMPORTANT: Use WebFetch to directly fetch these URLs:
- {url1}
- {url2}

Also use WebSearch for {angle descriptions}. Cast up to {N} search
angles if needed — you may find what you need in far fewer.

If MCP tools fail, fall back to WebFetch/WebSearch built-in tools.
If those fail, use Bash with curl. Do NOT stop — exhaust all
available approaches.

## Definition of Done

- [ ] {BSV criterion 1}
- [ ] {BSV criterion 2}
- [ ] {BSV criterion 3}

You must achieve 100% of every criterion before reporting completion.
Partial = incomplete.

## Handback Format

Return your research as a single comprehensive document organized
by the sections above. Include source attribution throughout.
```

## Context Block Patterns

### For SDK/Library Research

```
## Context

{ProjectName} is a {description} ({tech stack details}). The team is
integrating {library/SDK} for {purpose}. The {platform} app has:
- {architectural detail relevant to integration}
- {existing related infrastructure}
- {privacy/security posture}
- {specific constraints}

The app handles {sensitive data types}. {Privacy stance — what must
never reach the SDK}.

{What research already exists and what gaps remain.}
```

### For Architecture/Decision Research

```
## Context

{ProjectName} needs to decide {decision}. Current architecture:
- {how things work today}
- {what's driving the change}
- {constraints and non-negotiables}

The decision affects {blast radius}. Reversibility: {high/medium/low}.
The team has {experience level} with {domain}.
```

### For Community Feedback Research

```
## Context

{ProjectName} is about to {action}. Before implementing, the team
wants unvarnished developer community feedback — not documentation,
but what developers say in forums, Reddit, blog posts, and GitHub issues.

The {platform} app currently uses {current tool}. The {other platform}
app has {status}.

{Specific aspects to investigate: migration stories, performance,
pricing, gotchas, platform-specific issues.}
```

## Research Guidance Patterns

### For Official Documentation Research

```
## Research Guidance

Fetch these official documentation pages:
- {url1} — {what to find there}
- {url2} — {what to find there}

Use WebSearch for deeper context. Up to {60-80} search angles if
needed. Search for:
- "{SDK} {platform} {feature} {year}"
- "{SDK} {feature} configuration options"
- "{SDK} {platform}-specific limitations"
- "{SDK} {feature} breaking changes"

When extracting from pages: **{extraction fields joined by | }**
```

### For Community/Forum Research

```
## Research Guidance

This mission is ENTIRELY about community voices. Search across:

**Reddit:** Search r/{sub1}, r/{sub2} for "{topic}"
**GitHub:** Search {repo} issues for "{labels/keywords}"
**Forums:** {specific forums}

Cast up to 100 search angles — you may need far fewer, but community
sources warrant a high ceiling.

When extracting: **direct quotes with source attribution | upvote
counts | dates | specific version numbers | concrete numbers |
alternative tools mentioned**
```

## Definition of Done Patterns

### For Feature Documentation

```
- [ ] Every configuration option documented with type, default, and purpose
- [ ] Platform-specific limitations explicitly called out (not generic info)
- [ ] Swift code examples included for key APIs
- [ ] Feature availability matrix (platform × feature → supported/unsupported)
```

### For Community Feedback

```
- [ ] At least {10-15} distinct community sources cited
- [ ] Each finding attributed with source and date
- [ ] Both positive and negative sentiment captured
- [ ] Performance impact claims backed by specific numbers where available
- [ ] "Top N Things to Know" summary at end
```

### For Migration Research

```
- [ ] Feature parity comparison table (old vs new)
- [ ] API mapping (old calls → new calls)
- [ ] Step-by-step migration path
- [ ] Community migration experience documented
- [ ] Known gotchas and deal-breakers listed
```

## Anti-Patterns

| Do This | Not This |
|---------|----------|
| "Understand the complete request lifecycle" | "Search for 'request lifecycle' on Google" |
| "Up to 80 search angles if needed" | "Search at least 20 angles" |
| "Every option documented with type and default" | "Configuration is well-documented" |
| Rich context prose (200+ words) | Skeleton bullet points |
| "Use WebFetch/WebSearch; if denied, use curl" | "Use the web-search MCP tool" (may be denied) |
| Observable end-state | Procedural step list |

## The Fallback Chain

Always include this in every mission brief:

```
If MCP tools (web-search, scrape-links) are denied, fall back to
WebFetch/WebSearch built-in tools. If those fail, use Bash with
curl to fetch raw content from URLs. Do NOT stop working — use
whatever tools are available.
```

This prevents the #1 failure mode: agents stopping because one tool was denied.
