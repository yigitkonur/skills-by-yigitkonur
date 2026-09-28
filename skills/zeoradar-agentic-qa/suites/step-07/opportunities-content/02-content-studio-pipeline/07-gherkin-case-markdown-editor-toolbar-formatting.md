# Test Case: TC-CS-07 - AEO Editor Sticky Toolbar Formatting & Caret Behaviors

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-07`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #46 (Content Studio Pipeline, Facts Grounding & AI Streaming)
- **Traceability:** Maps to Source Scenarios `TC-CS-06` (Markdown Live Editor Formatting) and `TC-CS-16` (Markdown Editor Formatting Shortcuts with Collapsed Selection)
- **Purpose:** Test the AEO Rich Text Editor sticky toolbar (`.ed-toolbar`), verifying that formatting commands (Bold, Italic, Link, H1, H2, Blockquote) apply correctly to highlighted text, that clicking block formatting buttons (H1, H2) with a collapsed caret selection automatically wraps the active paragraph enclosing the caret without requiring text highlighting, and that clicking AI Rewrite with a collapsed selection triggers a defensive guidance toast without modifying document state.

---

## 2. Tester Brief
The tester will verify the formatting engine inside `#edContentBody`:
1. The sticky toolbar `.ed-toolbar` houses formatting buttons: `Bold`, `Italic`, `Link`, `H1`, `H2`, `Blockquote`, and `AI Rewrite`.
2. **Highlighted Selection Formatting:** Selecting a phrase and clicking `Bold` wraps text in `<b>` or applies `font-weight: bold`.
3. **Caret Behavior with Collapsed Selection (`sel.isCollapsed === true`):**
   - Placing the caret inside a normal paragraph `<p>` and clicking `H2` converts the entire paragraph into `<h2>`.
   - Structural statistics in the sidebar (`stats.headings`) update immediately.
4. **AI Rewrite Guard on Collapsed Selection:**
   - Placing the caret with no text selected and clicking `button.ed-ai-btn` triggers a defensive toast: `"Select text in the draft to rewrite"` / `"Yeniden yazmak için taslakta metin seçin"`.
   - No destructive edits or accidental full-document overwrites occur.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Matching Result Directory:** `07-gherkin-result-case-markdown-editor-toolbar-formatting/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: AEO Live Markdown Editor Toolbar Formatting and Collapsed Caret Protections

  Background:
    Given the user is in an active Content Studio article editor
    And the canvas "#edContentBody" contains formatted paragraphs and text
    And the sticky toolbar ".ed-toolbar" is visible

  Scenario Outline: Applying Formatting to Highlighted Text Selection
    Given the user selects the text "<TargetText>" inside "#edContentBody"
    When the user clicks the toolbar button "<ButtonSelector>"
    Then the selected text should be wrapped in "<ExpectedTag>"
    And the document dirty state should update and persist

    Examples:
      | TargetText    | ButtonSelector                    | ExpectedTag |
      | artisan truff | .ed-tb-btn[title*='Bold']         | <b>         |
      | premier cacao | .ed-tb-btn[title*='Italic']       | <i>         |
      | Key Finding   | .ed-tb-btn[title*='Heading 2']    | <h2>        |

  Scenario: Block Formatting with Collapsed Caret Selection
    Given the user places the typing caret inside a normal paragraph with no text selected
    And notes the initial heading count in the sidebar stats as "H_count"
    When the user clicks the "Heading 2" button in the sticky toolbar
    Then the active paragraph enclosing the caret should be converted to an "<h2>" element
    And the headings counter in the sidebar stats should increment to "H_count + 1"

  Scenario: Defensive Toast Guard on AI Rewrite with Collapsed Selection
    Given the user has a collapsed caret selection with zero text highlighted
    When the user clicks the "AI Rewrite" button "button.ed-ai-btn" in the toolbar
    Then a protective guidance toast should appear
    And the toast message should contain "Select text in the draft to rewrite"
    And the editor canvas HTML content should remain completely unmodified
```

---

## 5. Visual Checks
1. **Sticky Toolbar Position:** `.ed-toolbar` remains pinned at `top: 68px` when the user scrolls the document.
2. **Active State Indication:** Buttons show visual depressed or active states when formatting is active.
3. **Canvas Focus Ring:** `#edContentBody` displays subtle focus indication when typing.

---

## 6. Data and Network Checks
1. **Canvas DOM Structure:**
   ```js
   const edBody = document.getElementById('edContentBody');
   console.assert(edBody.getAttribute('contenteditable') === 'true', "Canvas is not contenteditable");
   ```
2. **Autosave Persistence:**
   - Verify `ContentStudio.persistEditor()` executes on change.
   - Inspect active project `draft` property in `ContentStudioState.projects`.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `07-gherkin-result-case-markdown-editor-toolbar-formatting/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `toolbar_bold_applied.png` showing bold tag wrapper.
  2. Capture `caret_h2_applied.png` showing block paragraph converted to H2.
  3. Capture `ai_rewrite_collapsed_toast.png` showing protective guidance toast.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/editor-formatting/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/07-gherkin-result-case-markdown-editor-toolbar-formatting/
     ```
  5. Include verification metrics in `result.md`.

### Pass/Fail Criteria
- [ ] Toolbar formatting applies corresponding HTML tags to selected text.
- [ ] H2 block command formats active paragraph when caret is collapsed.
- [ ] AI Rewrite safely displays guidance toast when no text is selected.
- [ ] Document changes persist cleanly to storage without HTML corruption.
