# Test Case: TC-CS-01 - Opportunity Handoff & Brand Hub Fact Compliance

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-01`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #46 (Content Studio Pipeline, Facts Grounding & AI Streaming)
- **Traceability:** Maps to Source Scenario `TC-CS-01` (Opportunity Handoff & Fact Compliance)
- **Purpose:** Verify that when an opportunity brief is seeded into Content Studio via `createBriefFromOpportunity()`, the system ingests the seed metadata, resolves authoritative Brand Hub facts via `getBrandHubFacts()`, injects the compliant `.brief-fact-compliance-box` (`BMD-BSH-02`), generates competitor citation gap notices and authentic citation source cards, maps implementation steps to H2 outline headings, calculates initial baseline AEO readiness, persists the project, and automatically mounts the AEO Editor canvas.

---

## 2. Tester Brief
The tester will verify the ingestion contract of `ContentStudio.createBriefFromOpportunity(briefSeed)`:
1. `briefSeed` object contains: `id`, `topic`, `targetPrompt`, `category`, `sourceUrls`, `outlineHeadings`, `impactScore`, `competitors`, `rationale`.
2. The method queries `window.getBrandHubFacts(profile)`. If verified facts exist (e.g. SLA, Data Residency, Security), they must render inside `#edContentBody` enclosed in `.brief-fact-compliance-box` with green checkmarks.
3. If competitors are tracked, a competitor citation gap block is rendered warning against competitor domain authority.
4. Verified AI source URLs are rendered inside `.brief-citation-sources-box`.
5. The `outlineHeadings` array is converted into structured `<h2>` headings within the document.
6. The project is assigned an ID, persisted to storage, and `ContentStudioState.view` is set to `"editor"`.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Article Title `[ARTICLE_TITLE]`:** `"Position [BRAND] in Discussions Comparing [COMPETITOR_NAME] vs [BRAND]"`
- **Opportunity Seed `[OPPORTUNITY_ID]`:** `op-reddit-1`
- **Matching Result Directory:** `01-gherkin-result-case-opportunity-handoff-and-fact-compliance/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Content Studio Opportunity Brief Ingestion and Brand Hub Fact Compliance

  Background:
    Given the user is on the Workflows page for "[DOMAIN]"
    And verified Brand Hub facts exist for "[DOMAIN]" in the Truth Vault
    And an opportunity seed for "[OPPORTUNITY_ID]" is ready with title "[ARTICLE_TITLE]"

  Scenario: Brief Seed Ingestion and Editor Mounting
    When the system executes "ContentStudio.createBriefFromOpportunity(briefSeed)"
    Then the application view mode "ContentStudioState.view" should equal "editor"
    And the editor container ".editor-view-container" should be mounted
    And the document title ".editor-doc-title" should display "[ARTICLE_TITLE]"
    And the project status indicator should display "Draft"

  Scenario: Brand Hub Fact Compliance and Citation Sources Injection
    Given the Content Studio editor has mounted from the opportunity seed
    Then the editor canvas "#edContentBody" should contain the compliance box ".brief-fact-compliance-box"
    And the compliance box should display header "Authoritative Brand Hub Facts Compliance (BMD-BSH-02)"
    And the compliance box should list verified SLA and Data Residency facts with checkmark indicators
    And the canvas should contain citation sources container ".brief-citation-sources-box"
    And the canvas should contain H2 outline headings corresponding to the seed outline steps
    And the sidebar "Workflow" tab should list the outline steps in ".ed-outline-list"
```

---

## 5. Visual Checks
1. **Compliance Box Styling:** `.brief-fact-compliance-box` renders with green/emerald border tint, shield icon (`🛡`), and structured fact list items.
2. **Citation Sources Box:** `.brief-citation-sources-box` renders citation URL pills with external link indicators.
3. **Editor Layout:**
   - Left side: Full-width sticky formatting toolbar and `#edContentBody` canvas.
   - Right side: Inspector sidebar with tabs for Workflow, AEO Stats, and History.

---

## 6. Data and Network Checks
1. **Seed Ingestion Verification:**
   ```js
   const proj = window.ContentStudioState.projects.find(p => p.id === window.ContentStudioState.activeProjectId);
   console.assert(proj && proj.title === "[ARTICLE_TITLE]", "Project title mismatch");
   console.assert(proj.draft && proj.draft.includes("brief-fact-compliance-box"), "Compliance box missing in draft HTML");
   ```
2. **State Persistence:**
   - Check `localStorage.getItem("zeo-content-studio-projects:[wid]:[pid]")` contains the newly created project.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `01-gherkin-result-case-opportunity-handoff-and-fact-compliance/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `seed_ingested_editor_view.png` showing mounted editor.
  2. Capture `compliance_facts_box.png` verifying Brand Hub fact claims.
  3. Capture `outline_headings.png` showing generated outline structure.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/content-handoff/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/01-gherkin-result-case-opportunity-handoff-and-fact-compliance/
     ```
  5. Include verification checklist in `result.md`.

### Pass/Fail Criteria
- [ ] Seed ingestion smoothly transitions view to `editor`.
- [ ] Document title matches opportunity topic.
- [ ] `.brief-fact-compliance-box` renders with verified Brand Hub claims.
- [ ] Outline headings and citation links are injected without syntax errors.
