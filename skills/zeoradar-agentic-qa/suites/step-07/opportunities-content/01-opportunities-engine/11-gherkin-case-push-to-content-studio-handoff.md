# Test Case: TC-OPP-11 - Opportunities to Content Studio Handoff Bridge

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-11`
- **Module:** Opportunities Engine (`assets/opportunities.js`) & Content Studio (`assets/content-studio.js`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage) & Issue #46 (Content Studio Pipeline)
- **Traceability:** Maps to Source Scenario `TC-OPP-13` (Push-to-Content-Studio Handoff)
- **Purpose:** Validate the execution bridge between the Opportunities Engine and the Content Studio. When the user clicks "Draft Brief" (`button.op-draft-btn[data-action="opp-draft-brief"]`) on an opportunity card or inside the detail view, the system must assemble a structured `briefSeed` object, dispatch it to `ContentStudio.createBriefFromOpportunity()`, switch the global SPA tab to `"workflows"`, and immediately mount the AEO Content Studio Editor with pre-populated Brand Hub facts, competitor gap targets, and outline headings.

---

## 2. Tester Brief
The tester will verify the cross-module handoff bridge:
1. Identifying an active opportunity card in `.opps-list` with `id: [OPPORTUNITY_ID]`.
2. Clicking "Draft Brief" (`button.op-draft-btn`):
   - Extracts `briefSeed` containing: `id`, `topic`, `targetPrompt`, `category`, `sourceUrls`, `outlineHeadings`, `impactScore`, `competitors`, and `rationale`.
   - Calls `ContentStudio.createBriefFromOpportunity(briefSeed)`.
   - Transitions global application tab: `window.state.tab = "workflows"`.
   - Transitions studio view: `window.ContentStudioState.view = "editor"`.
3. Verifies that the editor canvas (`#edContentBody`) mounts immediately with:
   - Topic headline and seeded draft structure.
   - Authoritative Brand Hub Facts compliance block (`.brief-fact-compliance-box`).
   - Authentic citation sources box (`.brief-citation-sources-box`).
   - Implementation checklist steps converted into H2 headings in the document outline.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Opportunity Under Test `[OPPORTUNITY_ID]`:** E.g. `op-content-1` or `op-reddit-1`
- **Matching Result Directory:** `11-gherkin-result-case-push-to-content-studio-handoff/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Opportunities to Content Studio Brief Handoff Bridge

  Background:
    Given the user is on the Opportunities page for "[DOMAIN]"
    And card "[OPPORTUNITY_ID]" is visible in the active backlog
    And the card contains a "Draft Brief" button "button.op-draft-btn"

  Scenario: Clicking Draft Brief Dispatches Seed and Transitions to Content Studio Editor
    When the user clicks the "Draft Brief" button on card "[OPPORTUNITY_ID]"
    Then the application should switch the active route to "/#/workflows"
    And global state "window.state.tab" should equal "workflows"
    And the Content Studio view "window.ContentStudioState.view" should equal "editor"
    And the AEO Editor container ".editor-view-container" should be mounted in the DOM
    And the document title in ".editor-doc-title" should match the opportunity title
    And the editor canvas "#edContentBody" should be visible and editable

  Scenario: Pre-population of Brand Hub Facts and Citation Sources
    Given the Content Studio editor has mounted from opportunity "[OPPORTUNITY_ID]"
    Then the editor canvas should contain an Authoritative Brand Hub Facts box ".brief-fact-compliance-box"
    And the compliance box should list verified facts from "window.getBrandHubFacts()"
    And the editor canvas should contain a Citation Sources box ".brief-citation-sources-box"
    And the document outline should contain H2 headings corresponding to the opportunity implementation steps
```

---

## 5. Visual Checks
1. **Transition Speed:** Clicking "Draft Brief" transitions seamlessly from Opportunities to Workflows without page reload or blank white screen.
2. **Editor Layout:**
   - Top Bar: Displays document title, back button, "Saved" status indicator.
   - Canvas (Left): Displays contenteditable `#edContentBody` with styled compliance cards.
   - Sidebar (Right): Displays Outline tab, AEO stats tab, and History tab.
3. **Compliance Box:** `.brief-fact-compliance-box` renders with shield icon (`🛡`), green verification checkmarks, and enterprise fact bullets.
4. **Citation Box:** `.brief-citation-sources-box` lists source URLs with outbound link indicators.

---

## 6. Data and Network Checks
1. **Brief Seed Payload Inspection:**
   ```js
   var seed = {
     id: targetOp.id,
     topic: targetOp.title,
     targetPrompt: targetOp.targetPrompt || targetOp.entityTag,
     category: targetOp.category,
     sourceUrls: (targetOp.references || []).map(r => r.url).filter(Boolean),
     outlineHeadings: (targetOp.implementationSteps || []).map(s => s.text),
     impactScore: targetOp.impactScore,
     competitors: targetOp.competitors || [],
     rationale: targetOp.rationale
   };
   console.assert(seed.id && seed.topic && Array.isArray(seed.outlineHeadings), "Invalid briefSeed format");
   ```
2. **Project Persistence:**
   - Check `ContentStudio.persistProject` creates a project entry in `ContentStudioState.projects`.
   - Verify project status is set to `"draft"`.
   - Check `localStorage` contains `zeo-content-studio-projects:*`.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `11-gherkin-result-case-push-to-content-studio-handoff/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `card_draft_btn_click.png` showing the clicked opportunity card.
  2. Capture `editor_view_mounted.png` showing transition to AEO Editor.
  3. Capture `facts_compliance_box.png` verifying Brand Hub fact injection.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-handoff/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/11-gherkin-result-case-push-to-content-studio-handoff/
     ```
  5. Include verification metrics in `result.md`.

### Pass/Fail Criteria
- [ ] Clicking "Draft Brief" switches route to `#/workflows` and view to `editor`.
- [ ] Document title matches the originating opportunity title.
- [ ] Brand Hub compliance box is rendered inside `#edContentBody` with verified claims.
- [ ] Outline headings match opportunity implementation steps.
