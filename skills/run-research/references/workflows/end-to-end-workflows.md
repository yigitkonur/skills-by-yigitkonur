# End-to-End Research Workflows

## Overview

This reference provides complete, step-by-step research workflows for the most common coding research scenarios. Each workflow specifies exact tool calls, query templates, and decision points. Follow these workflows as written; deviate only when the intermediate results suggest a different path.

## Workflow 1: "I Hit an Error I Don't Recognize"

**Trigger:** Unknown error message, stack trace, or unexpected behavior.
**Expected tool calls:** 3-4
**Expected time:** 2-3 minutes

### Step-by-Step

```
1. EXTRACT the distinctive part of the error message
   - Remove project-specific paths, line numbers, and timestamps
   - Keep the error type, error code, and key description
   - Example: "/Users/me/app/src/server.ts:47 TypeError: Cannot read properties of undefined (reading 'id')"
     → Extract: "TypeError: Cannot read properties of undefined"

2. search_google (5 keywords)
   keywords = [
       '"TypeError: Cannot read properties of undefined" [framework]',
       '"Cannot read properties of undefined" [framework] [version] fix',
       'site:stackoverflow.com "Cannot read properties of undefined" [context]',
       '[framework] undefined error [specific context] solution',
       '[framework] [function/hook where error occurs] undefined fix [year]',
   ]

3. REVIEW results — pick top 3-5 URLs
   Priority: Stack Overflow > GitHub Issues > Official docs > Blog posts

4. scrape_pages (3-5 URLs)
   what_to_extract = "root cause | fix code | environment conditions | version affected | workarounds"

5. EVALUATE — is the fix clear?
   YES → Apply fix, done
   NO → Continue to step 6

6. search_reddit (3 queries)
   queries = [
       '"[error message]" r/[language]',
       '[library] [symptom] fix workaround',
       '[library] [version] issue [year]',
   ]

7. EVALUATE — found a fix?
   YES → Apply fix, done
   NO → Continue to step 8

8. deep_research (1 question, maximum depth)
   Attach the failing code file.
   Include full stack trace.
   Ask for systematic diagnosis.
```

### Decision Points

- If search_google returns 0 relevant results → the error is likely from your own code, not a known issue. Focus on code review.
- If the error is from a recent library update → check GitHub releases/changelog with scrape_pages.
- If multiple fixes are suggested → try the one from the most recent source first.

## Workflow 2: "Should I Use Library A or Library B?"

**Trigger:** Need to choose between competing libraries for a specific task.
**Expected tool calls:** 5-6
**Expected time:** 5-8 minutes

### Step-by-Step

```
1. DEFINE requirements before researching
   Write down: deployment model, performance needs, team size,
   risk tolerance, maintenance horizon

2. search_google (6 keywords)
   keywords = [
       '[lib A] vs [lib B] [year]',
       '[lib A] vs [lib B] benchmark performance',
       'best [category] [language] library [year]',
       '[lib A] alternatives [year]',
       'site:npmtrends.com [lib A] [lib B]',
       '[lib A] [lib B] migration guide',
   ]

3. scrape_pages (3-5 URLs from step 2)
   what_to_extract = "features | bundle size | performance | limitations | maintenance activity | community size"

4. search_reddit (7 queries — cover both positive and negative)
   queries = [
       '[lib A] vs [lib B] experience',
       '[lib A] production experience',
       '[lib B] production experience',
       'switched from [lib A] to [lib B]',
       '[lib A] problems issues',
       '[lib B] problems issues',
       'r/[language] [category] recommendation [year]',
   ]

5. fetch_reddit (5-7 highest-signal threads from step 4)
   fetch_comments = true
   use_llm = false  # Preserve exact opinions, code, and version numbers

6. deep_research (1-2 questions)
   Include your requirements from step 1.
   Attach your code showing how the library will be used.
   Ask:
   - Which library fits MY constraints?
   - What are the migration costs if I need to switch later?
   - What are the specific risks for MY use case?

7. BUILD decision matrix
   | Criterion | Lib A | Lib B | Source |
   |-----------|-------|-------|--------|
   | Performance | [data] | [data] | scrape_pages |
   | Community | [data] | [data] | search_reddit |
   | Team fit | [assessment] | [assessment] | Your knowledge |
   | Risk | [assessment] | [assessment] | deep_research |
```

## Workflow 3: "How Should I Design This System?"

**Trigger:** Architecture decision, system design, technology selection.
**Expected tool calls:** 5-7
**Expected time:** 8-15 minutes

### Step-by-Step

```
1. FRAME the decision precisely
   Write down: current state, constraints, scale targets,
   team composition, risk tolerance, timeline

2. deep_research (2-3 structured questions)
   Use the full template (WHAT I NEED / WHY I'M RESEARCHING THIS / WHAT I ALREADY KNOW / HOW I PLAN TO USE THIS / SPECIFIC QUESTIONS).
   Attach relevant code showing current architecture.
   Ask about:
   - Trade-offs between options
   - Failure modes and scaling limits
   - Migration path and reversibility

3. EVALUATE deep_research output
   Identify: key claims to verify, areas of uncertainty,
   contradictions with your experience

4. search_reddit (5-7 queries — focus on real-world experience)
   queries = [
       '[option A] vs [option B] production',
       '[option A] regret switched from',
       '[option B] regret switched from',
       'r/ExperiencedDevs [decision category]',
       '[option A] [scale target] experience',
       'best [category] for [your constraints]',
       '[option A] failure mode production',
   ]

5. fetch_reddit (5-7 best threads)
   fetch_comments = true
   use_llm = false
   Focus on: dissenting comments, experience-based warnings,
   specific metrics (cost, latency, team size thresholds)

6. search_google (3-5 queries for official sources)
   keywords = [
       'site:[official-docs] [option A] architecture guide',
       '[option A] benchmark [specific metric]',
       '[option A] vs [option B] case study',
       '[option A] migration guide from [current]',
   ]

7. scrape_pages (3-5 authoritative URLs from step 6)
   what_to_extract = "features | limitations | pricing | compatibility | migration path | scaling limits"

8. SYNTHESIZE
   Build decision matrix with data from all sources.
   Weight: deep_research analysis + Reddit experience + official docs.
   Present recommendation with confidence level and conditions.
```

## Workflow 4: "Is This Information Still Current?"

**Trigger:** Need to verify if advice, documentation, or a claim is still valid.
**Expected tool calls:** 2-3
**Expected time:** 1-2 minutes

### Step-by-Step

```
1. search_google (3 keywords)
   keywords = [
       '[topic] [year] changes updates',
       'site:[official-docs] [topic] changelog',
       '[topic] deprecated OR removed OR changed [year]',
   ]

2. scrape_pages (2-3 most relevant URLs)
   what_to_extract = "current status | version | changes | deprecations | migration notes"

3. EVALUATE
   If current → the information is valid
   If changed → note what changed and when
   If deprecated → find the replacement
```

## Workflow 5: "I Need to Fix a Production Issue Fast"

**Trigger:** Production incident requiring immediate resolution.
**Expected tool calls:** 2-3 (speed is critical)
**Expected time:** 1-2 minutes

### Step-by-Step

```
1. search_google (3 keywords — fast and focused)
   keywords = [
       '"[exact error]" [stack] fix',
       '[service] [symptom] production fix',
       'site:stackoverflow.com "[error code]" [framework]',
   ]

2. scrape_pages (top 2-3 URLs — fastest extraction)
   what_to_extract = "fix steps | workaround | root cause"

3. APPLY the most relevant fix

4. If fix doesn't work:
   search_reddit (3 queries, recent)
   queries = [
       '"[error]" [framework] fix [year]',
       '[framework] [symptom] workaround',
       'r/[language] [error type] recent',
   ]
   date_after = "[30 days ago]"
```

### Speed Optimization

- Use fewer, more targeted keywords (3 instead of 7)
- Scrape fewer URLs (2-3 instead of 5)
- Skip deep_research unless initial searches fail
- Skip fetch_reddit unless search_reddit reveals a promising thread
- Apply the first plausible fix and iterate

## Workflow 6: "I Need to Stay Current on a Technology"

**Trigger:** Periodic check on a technology you use or are considering.
**Expected tool calls:** 4
**Expected time:** 3-5 minutes

### Step-by-Step

```
1. search_reddit (5 queries)
   queries = [
       '[technology] state of [year]',
       'what changed in [technology] recently',
       '[technology] new features [year]',
       'r/[language] [technology] updates',
       '[technology] vs alternatives [year]',
   ]

2. fetch_reddit (3-5 most active recent threads)
   fetch_comments = true
   use_llm = false

3. search_google (3 keywords)
   keywords = [
       '[technology] changelog [year]',
       '[technology] roadmap upcoming features',
       '[technology] release notes latest',
   ]

4. scrape_pages (2-3 URLs)
   what_to_extract = "new features | breaking changes | deprecations | roadmap | release dates"
```

## Workflow 7: "I Need to Audit or Repair a Skill / Runbook"

**Trigger:** Repo-local skill repair, workflow audit, command-path verification, or execution-contract cleanup.
**Expected tool calls:** 3-4
**Expected time:** 4-8 minutes

### Step-by-Step

```
1. FRAME the audit as an execution-contract question
   Write down:
   - runtime/tool surface being assumed
   - command paths or wrappers that must be exact
   - approval gates or stop conditions that must remain intact
   - source files that define the workflow

2. deep_research (1 focused question)
   Use the full template.
   Attach the source skill files or runbook sections under review.
   Ask:
   - which steps have hidden runtime assumptions?
   - which commands, tool names, or gates need source-of-truth verification?
   - what should the stop conditions and verification signals be?

3. search_google (3-5 keywords)
   keywords = [
       '[tool or CLI name] official docs [year]',
       'site:github.com/[org]/[repo] [command or subcommand]',
       '[tool name] wrapper name documentation',
       '[tool name] configuration syntax official',
   ]

4. scrape_pages (2-4 URLs)
   what_to_extract = "canonical command syntax | required prerequisites | verification signals | stop conditions | version-specific differences"

5. OPTIONAL Reddit branch
   Only if the topic has clear practitioner signal.
   If direct Reddit coverage is weak, search adjacent runtime/tooling topics once.
   If signal is still weak, stop the Reddit branch and record "community signal weak".

6. SYNTHESIZE
   Output:
   - execution-contract findings
   - source-of-truth repairs needed
   - verification signals
   - explicit stop conditions or fallback branches
```

## Workflow Selection Quick Reference

| Situation | Workflow | Key First Tool |
|-----------|----------|---------------|
| Unknown error message | Workflow 1 | search_google |
| Choosing between libraries | Workflow 2 | search_google |
| System design decision | Workflow 3 | deep_research |
| Verifying if info is current | Workflow 4 | search_google |
| Production incident | Workflow 5 | search_google |
| Technology landscape check | Workflow 6 | search_reddit |
| Skill / runbook audit | Workflow 7 | deep_research |

## Adapting Workflows

These workflows are starting points. Adapt based on intermediate results:

| Intermediate Result | Adaptation |
|-------------------|------------|
| search_google returns excellent results | Skip Reddit steps; go straight to scrape_pages |
| search_google returns nothing relevant | Try search_reddit; the topic may be too niche for Google |
| deep_research gives confident answer | Verify one key claim with scrape_pages, then stop |
| Reddit threads are all 3+ years old | Results may be outdated; verify with official docs |
| Contradictory information across sources | Add more sources until consensus emerges |
| All sources agree | High confidence; stop researching |

## Key Insight

The best researchers don't follow templates rigidly — they use templates as starting points and adapt based on what each tool call reveals. The workflow tells you where to start and what order to try. The intermediate results tell you when to deviate, when to dig deeper, and when to stop. The most common mistake is over-researching a question that was answered in step 2.

## Steering notes from production testing

### Conflicting evidence handling

1. Identify what specifically conflicts (pricing? performance? compatibility?)
2. Credibility hierarchy: scraped official docs > Reddit practitioners > deep_research synthesis > blog posts
3. If unclear: focused verification search targeting the specific conflicting claim

### deep_research placement

- Bug fix: ONLY after search->scrape->reddit, if fixes conflict or feel generic
- Library comparison: LAST, after all search/scrape/Reddit. Populate KNOWN.
- Architecture: FIRST (starts sequence). Verify with subsequent steps.
- Fact checks: Usually not needed.

### Tool "Next Steps" warning

All tools may suggest follow-up calls. Follow the Workflow Selector sequence, not tool suggestions.
