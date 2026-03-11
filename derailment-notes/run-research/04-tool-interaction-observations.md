# Tool Interaction Observations: run-research

## Tool output patterns that affect skill execution

### search_google output behavior
- Returns aggregated results with consensus scoring
- Generates "Next Steps (DO NOT SKIP)" banners with tool-call templates
- Provides 10 results per keyword, grouped by query
- Friction: The tool's next-step suggestions conflict with the skill's own step sequence

### scrape_pages output behavior
- Returns structured tables when use_llm=true with tabular extraction targets
- Extracts "Not found in SOURCE" for missing data (honest gaps)
- Quality depends heavily on `what_to_extract` specificity
- Observation: Pipe-separated extraction targets produce better tables than prose descriptions
- Token budget: ~6,400 per URL with 5 URLs

### search_reddit output behavior
- Returns aggregated results with consensus scoring (≥2 appearances)
- 10 results per query, up to 50 queries
- Generates CTR-ranked full results list
- Observation: 8 queries produced 68 unique posts — the diversity was good
- Friction: No guidance on how many queries to use for different task types

### fetch_reddit output behavior
- Returns full post content + top comments
- Comment budget: 1000 total distributed across posts (125 per post for 8 posts)
- use_llm=false gives raw comments (better for authenticity)
- use_llm=true gives synthesized insights (better for volume)
- Observation: Raw comments from experienced devs (e.g., Ably co-founder) provided unique insights not in any docs

### deep_research output behavior
- Returns structured sections: CURRENT STATE, KEY INSIGHTS, TRADE-OFFS, PRACTICAL IMPLICATIONS, WHAT'S CHANGING
- Uses 32K token budget per question
- File attachments dramatically improve answer relevance
- GOAL/WHY/KNOWN/APPLY format produces much better results than bare questions
- Observation: deep_research already synthesizes — step 5 "synthesize" is redundant when deep_research was used
- Friction: deep_research generates its own "Next Steps" banner, creating authority conflict with the skill

## Tool sequencing observations

### Library research (Pattern C): search_google → scrape_pages → search_reddit → fetch_reddit → deep_research
- Each tool added unique value:
  - search_google: found formal docs and comparison articles
  - scrape_pages: extracted structured comparison tables from articles
  - search_reddit: found developer experience reports and opinions
  - fetch_reddit: got specific recommendations and warnings from real users
  - deep_research: synthesized everything + added pricing/latency data
- The sequence order matters: search_google first gives formal baseline, Reddit adds real-world validation

### Bug fix research (Pattern A): search_google → scrape_pages → deep_research (with code)
- Simpler sequence was sufficient
- deep_research with attached code was the highest-value tool call
- Reddit was helpful but not essential for technical bugs (code patterns > opinions)
- Error message as literal search query was the most effective query strategy

## Recommendations for SKILL.md

1. Add tool-to-step mapping explicitly (Step 2 → search_google, Step 3 → scrape_pages, etc.)
2. Define when deep_research should be called (after completing minimum sequence)
3. Add guidance: "Follow the skill's steps, not tool-generated next-step suggestions"
4. Add output templates for common task types (library comparison table, bug fix pattern)
5. Add thread/URL selection counts per tool
6. Define validation sufficiency criteria (2+ independent sources confirming key claims)
