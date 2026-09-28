# Test Case 02: Category / Topic Taxonomy Sidebar Isolation & Badge Counters

## 1. Case ID and Purpose
- **Case ID**: `TC-PLIST-02-TAXONOMY-FILTER`
- **Purpose**: Verify that the taxonomy sidebar in Prompt Designer organizes prompts by assigned category/topic clusters, displays live count badges per topic, and that selecting a topic row filters the master prompt table strictly to that cluster while synchronizing row counts with the badge indicator.

---

## 2. Tester Brief
The tester navigates to the Prompt Designer Workbench for `[DOMAIN]` and:
1. Inspects the left taxonomy sidebar `.dg-side`.
2. Verifies that the "All Topics" row (`data-k=""`) has class `.on` by default and shows the total prompt count.
3. Clicks a specific topic row (e.g. `[TOPIC_NAME]`) and verifies that:
   - The selected topic row gains class `.on` while "All Topics" loses class `.on`.
   - The master table `.dg-tbl` immediately updates to show only rows matching that `topicId`.
   - The number of visible table rows strictly equals the count `.n` shown on the topic pill.
4. Clicks "All Topics" to verify the table returns to displaying all active prompts.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Pre-existing Data**: At least 2 distinct topic clusters configured (e.g. `"Seasonal Collections"` and `"Corporate Gifts"`) with prompts assigned to each.
- **Dynamic Variables**:
  - `[TOPIC_NAME]`: Name of target cluster under test.
  - `[TOPIC_ID]`: Identifier for the topic row.
  - `[TOPIC_COUNT]`: Number of prompts assigned to `[TOPIC_NAME]`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Category / Topic Taxonomy Sidebar Isolation

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompt Designer Workbench at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"
    And the page has mounted with selector ".designer-grid"

  @smoke @ui @filter
  Scenario Outline: Filter prompt table by topic category and verify badge synchronicity
    Given the sidebar ".dg-side" displays the topic "<TopicName>" with badge count "<ExpectedCount>"
    When the tester clicks the sidebar topic row with label "<TopicName>"
    Then the clicked topic row should gain class ".on"
    And the "All Topics" row should lose class ".on"
    And the prompt table "table.tbl.dg-tbl tbody" should render exactly "<ExpectedCount>" rows
    And every visible row in the table should display the topic badge "<TopicName>"
    When the tester clicks the "All Topics" sidebar row
    Then the "All Topics" row should regain class ".on"
    And the prompt table should restore all active prompts

    Examples:
      | TopicName             | ExpectedCount |
      | Seasonal Collections  | 14            |
      | Corporate Gifts       | 8             |
      | [TOPIC_NAME]          | 19            |

  @edge @empty
  Scenario: Selecting an empty topic displays standard empty state
    Given a new topic "Brand New Cluster" has been created with 0 assigned prompts
    When the tester clicks the topic row "Brand New Cluster" in the sidebar
    Then the prompt table should render the empty notice "tr td.dg-empty-row"
    And the empty message should contain "No prompts match the current filters."
```

---

## 5. Visual Checks
1. **Sidebar Layout**: `.dg-side` is docked on the left grid column with header `.side-label.dg-side-label` displaying `"Topics (N) ⇅"`.
2. **Active State Highlight**: Selected `.t-row` receives background tint and font weight bold with `.on` class.
3. **Count Badges**: Each `.t-row` contains a `.n` pill on the right containing an integer count.
4. **Table Topic Cells**: Each row's `td.dg-topic-cell` displays the topic label with clean ellipsis overflow without wrapping.

---

## 6. Data and Network Checks
1. **Client Filter Assertion**:
   ```javascript
   const activeTopicRow = document.querySelector('.dg-side .t-row.on');
   const selectedTopicKey = activeTopicRow.getAttribute('data-k');
   const badgeCount = parseInt(activeTopicRow.querySelector('.n').textContent.trim(), 10);
   const visibleRows = document.querySelectorAll('.dg-tbl tbody tr.dg-row');

   assert.strictEqual(visibleRows.length, badgeCount, 'Visible table rows must match topic badge count');
   visibleRows.forEach(row => {
     assert.ok(row.textContent.includes(activeTopicRow.querySelector('span:first-child').textContent.trim()), 'Row must belong to selected topic');
   });
   ```
2. **Zero Unnecessary Network Requests**: Client-side filtering in workbench runs locally without re-fetching snapshot data unless reload is triggered.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-taxonomy-topic-sidebar-filtering/`
- **Execution Model Notice**: Remote execution runs via Ego Browser on macOS. Screenshots are saved to `/tmp/shots/topic-filter-[TOPIC].png` and transferred via SCP to the local report directory.
- **Report Contents**:
  - `status.json`: Test execution result and timing.
  - `screenshot-all-topics.png`: Initial view with "All Topics" selected.
  - `screenshot-filtered-topic.png`: Filtered view showing isolated topic cluster.
