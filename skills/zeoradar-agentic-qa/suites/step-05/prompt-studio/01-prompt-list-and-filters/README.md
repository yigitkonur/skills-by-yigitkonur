# Test Suite Specification: Prompt Studio — Prompt List, Taxonomy Filters & On-Demand Execution

## 1. Module Overview & Scope

The **Prompt Studio (List & Filters)** subsystem governs the centralized catalog, multi-dimensional taxonomy filters, quota tracking, and authoritative on-demand measurement runs in Zeo Geo-Radar. It spans three core interfaces:
1. **Prompt Designer Workbench (`/#/:slug/designer`, `tab=designer`)**: Master administrative table with active/paused lifecycle segmentation, category/topic sidebar, SVG capacity ring, and atomic bulk actions.
2. **Prompts & Citations Studio (`/#/:slug/aei?workspace=studio`)**: Forensic split-view linking queries to multi-engine win/loss micro-dots, search volume fallback hierarchies, and intent chips.
3. **Measurement Runs Cockpit (`/#/:slug/overview`, `assets/run-now.js`)**: Authoritative run trigger modal executing pre-flight credit gating, cell calculation (1 credit = 1 cell), same-day replacement confirmation, staged publication states, and polling timeout recovery.

This directory provides modular, code-grounded Gherkin test cases designed for execution via Ego Browser on physical macOS nodes with headless and interactive verification pipelines.

---

## 2. Vocabulary & Placeholders Dictionary

To ensure deterministic evaluation across multi-tenant environments and locales, all test cases employ standard placeholders:

| Placeholder | Context / Semantics | Example Concrete Value |
|---|---|---|
| `[SLUG]` | Target project workspace slug | `daikin` |
| `[COUNTRY]` | Target market ISO-2 country code | `US`, `TR`, `GB`, `DE` |
| `[LANGUAGE]` | Canonical BCP-47 / ISO language code | `en`, `tr`, `de`, `fr` |
| `[PROMPT_TEXT]` | Generative query text under test | `"En iyi inverter klima modelleri hangileridir?"` |
| `[TOPIC_NAME]` | Category / cluster taxonomy label | `"Klimalar"`, `"Isı Pompaları"` |
| `[INTENT_TYPE]` | Query search intent classification | `info` (Informational), `comm` (Commercial), `trans` (Transactional), `nav` (Navigational) |
| `[CREDIT_BALANCE]` | Available workspace execution credits | `0` (Depleted), `500` (Sufficient), `10000000` |
| `[RUN_ID]` | UUID identifier of measurement run | `[RUN_ID]` |
| `[CAPACITY_COUNT]` | Total active prompt count for workspace | `48`, `99`, `100`, `101` |
| `[STROKE_DASHARRAY]` | Computed SVG capacity circle stroke | `"19.296 40.2"`, `"40.2 40.2"` |
| `[REPLACEMENT_TOKEN]` | Server-issued confirmation token | `rn_conf_tok_9b2e8a1f4c7d` |

---

## 3. Architecture & Target Component Reference

### 3.1 Component & Source Code Map
- **`assets/designer-wizards.js`**: `window.renderDesignerWorkbench`, `dgRenderLive`, `dgVisiblePrompts`, `handleDesignerAction`, `dgBulkRowDraft`, `dgRunBulkRows`, `dgStartBulk`
- **`assets/designer.css`**: Layout grids (`.dg-tbl`, `.dg-row`, `.dg-check`, `.dg-side`, `.dg-search-box`, `.count-pill`, `.ring`, `.dg-bulk-panel`, `.zr-bulkbar`, `.dg-save-chip`, `.dg-dot-mod`)
- **`assets/aei.js`**: `window.renderAeiWorkspaceStudio`, `renderStudioPipelineDetail`, `studioIntentFilter`, `studioSearchQuery`, `studioActiveEngine`, `computePromptStatus`
- **`assets/run-now.js`**: `window.ZeoRunNow`, `rnOpen`, `rnCallRunNow`, `rnPreviewBodyHTML`, `rnConfirmBodyHTML`, `rnStartedBodyHTML`, `rnResumeTracking`

### 3.2 DOM Selectors & Key Elements
- **Workbench Container**: `.designer-grid`, `.designer-head h1`, `.designer-top`
- **Tabs & Quota**: `.tab[data-action="dg-tab"][data-t="active"]`, `.tab[data-t="inactive"]`, `.count-pill`, `svg.ring circle:nth-child(2)`
- **Taxonomy Sidebar**: `.dg-side .t-row[data-action="dg-topic"]`, `button.btn.small.addt[data-action="dg-open-add-topic"]`
- **Search & Actions**: `input[data-action-input="dg-search"]`, `button[data-action="dg-open-add-prompt"]`, `button[data-action="dg-open-ai-discover"]`
- **Master Table**: `table.tbl.dg-tbl`, `tr.dg-row`, `th.dg-checkcol .dg-check`, `td.dg-checkcol .dg-check`, `tr.dg-addrow`
- **Bulk Action Bar**: `.zr-bulkbar.bulk-action-bar-floating`, `.bulk-count`, `button[data-action="bulk-disable"]`, `button[data-action="bulk-delete"]`, `button[data-action="bulk-clear"]`
- **AEI Studio**: `.aei-studio-workspace`, `input#aeiStudioSearchInput`, `.aei-intent-chip[data-action="aei-studio-filter-intent"]`, `.aei-master-item`, `.aei-m-dots`, `.aei-empty-state`
- **Run Now Modal**: `#modalHolder .modal.rn-modal`, `button[data-action="rn-open"]`, `button[data-action="rn-start"]`, `button[data-action="rn-confirm"]`, `button[data-action="rn-confirm-cancel"]`, `button[data-action="rn-resume-tracking"]`

---

## 4. Authoritative Business & State Machine Rules

1. **Capacity Ring Saturation & 100-Cap Formula**:
   $$\text{ringPct} = \frac{\min(\text{totalN}, 100)}{100}$$
   $$\text{dashValue} = 40.2 \times \text{ringPct}$$
   - When `totalN = 48`: `stroke-dasharray="19.296 40.2"`
   - When `totalN = 100`: `stroke-dasharray="40.2 40.2"` (saturated circle)
   - When `totalN = 101`: `stroke-dasharray` remains `"40.2 40.2"`; `.count-pill` reads `101 / 100 prompts`. Server blocks new prompt additions with plan quota limits.
   - Deleting or archiving a prompt immediately decrements `totalN` and contracts `dashValue`.

2. **Bulk Toggle Inversion Logic**:
   - If a mixed or active set is toggled via `data-action="bulk-disable"`, all selected rows transition to `paused`.
   - If **all** selected rows are already `paused` (homogeneous inactive set in Inactive tab), `dgBulkRowDraft` computes:
     `base.status = row.status === 'paused' ? 'active' : 'paused';`
     inverting their status back to `active` and migrating them back to the Active tab upon reload.

3. **Search Substring Sanitization**:
   - All filter searches use case-insensitive substring matching (`text.indexOf(query) !== -1`).
   - All input rendered in the DOM is escaped via `esc()`. Hostile injection vectors (e.g. `<script>`, `' OR 1=1 --`) are treated as literal query strings, matching 0 rows and rendering `.dg-empty-row` with zero XSS execution.

4. **AEI Search Volume Fallback Hierarchy**:
   - Priority 1: AI Search Volume (`pr.aiv` > 0) -> displays plain formatted number (e.g. `1,250`).
   - Priority 2: Google Traditional Volume (`pr.gv` > 0) -> displays `"GV: "` + formatted number (e.g. `"GV: 450"`).
   - Priority 3: Zero volume available -> displays `–` with tooltip `"Volume unmeasured"`.

5. **On-Demand Run Lifecycle & Same-Day Safeguards**:
   - **Cost Calculation**: Baseline active prompts $\times$ active engines $+$ incremental persona cells. Exactly 1 credit = 1 planned execution cell.
   - **Pre-flight Gating**: If balance < required credits, server rejects with `insufficient_credits`. UI renders red error message and disables start.
   - **Same-Day Replacement Negotiation**: If a published run already exists for the UTC day, server returns `replacement_confirmation_required` with `{ day, plannedCells, creditCost, existingRunLabel, replacesRunId, confirmationToken }`.
   - **Cancellation**: Operator clicking `rn-confirm-cancel` reverts to preview; published run remains current and intact.
   - **Staged In-Flight State**: During execution, status is `Running` and publication status is `Staged replacement — not current`. Published run remains active until the new run reaches `Sealed`.
   - **90-Second Polling Watchdog Recovery**: If client polling budget expires (`onStop('limit')`), UI displays `"Live tracking stopped"`. Clicking `rn-resume-tracking` resumes polling without re-triggering the backend job.

---

## 5. Test Case Inventory & Traceability Matrix

| Original Monolithic ID | Modular Case File | Case Title & Scope Summary |
|---|---|---|
| `TC-PLIST-01`, `TC-PLIST-14`, `TC-PLIST-15` | `01-gherkin-case-prompt-table-rendering-capacity-ring.md` | Master Table Rendering, SVG Capacity Formula & 100-Prompt Cap |
| `TC-PLIST-02` | `02-gherkin-case-taxonomy-topic-sidebar-filtering.md` | Category / Topic Taxonomy Sidebar Isolation & Badge Counters |
| `TC-PLIST-03`, `TC-PLIST-11` | `03-gherkin-case-search-filter-and-injection-sanitization.md` | Query Search Substring Filter & Hostile XSS Injection Sanitization |
| `TC-PLIST-04` | `04-gherkin-case-active-paused-tab-lifecycle.md` | Active vs Paused Tab Lifecycle & Offline Status Badges |
| `TC-PLIST-05`, `TC-PLIST-12` | `05-gherkin-case-bulk-selection-and-toggle-inversion.md` | Multi-Row Bulk Actions, Floating Bar & Paused Set Toggle Inversion |
| `TC-PLIST-06`, `TC-PLIST-13` (Zero-State) | `06-gherkin-case-aei-studio-intent-filtering-and-zero-state.md` | AEI Studio 5-Intent Taxonomy Chips & Zero-Match Empty State |
| `TC-PLIST-07`, `TC-PLIST-13` (Volume) | `07-gherkin-case-aei-studio-volume-fallback-and-engine-dots.md` | AEI Volume Fallback Hierarchy & 5-Engine Win/Loss Outcome Dots |
| `TC-PLIST-08`, `TC-PLIST-16` | `08-gherkin-case-on-demand-run-preview-and-credit-gating.md` | On-Demand Run Preview Calculation & Pre-flight Insufficient Credits Gating |
| `TC-PLIST-09`, `TC-PLIST-17` | `09-gherkin-case-same-day-replacement-modal-and-cancellation.md` | Same-Day Replacement Confirmation Audit & Cancellation Rollback |
| `TC-PLIST-10`, `TC-PLIST-18` | `10-gherkin-case-run-execution-staged-state-and-timeout-recovery.md` | In-Flight Staged Run Tracking, 90s Timeout Alert & Polling Resumption |

---

## 6. Execution Model & Quality Contract

- **Execution Engine**: All test cases are designed for automated or assisted execution via `ego-browser nodejs` on a macOS host.
- **Artifact Isolation**: Test runs capture browser viewport snapshots on the remote test runner (`/tmp/shots/`) and pull them via `scp` into local result directories.
- **Result Directory Pattern**: Each case specifies an exact result directory matching the pattern `01-gherkin-result-case-<short-slug>/`. *(Note: Result directories are created only during actual test execution, never pre-created empty).*
- **Failure Protocol**: If an assertion fails, the execution log must record the exact DOM state, console errors, network payload diff, and a high-resolution screenshot before halting.
