# Test Suite Specification: Prompt Studio — Prompt Creation, Inline Editor, AI Discovery & Ingestion

## 1. Module Overview & Scope

The **Prompt Studio (Creation, Editor, AI Discovery & Ingestion)** subsystem governs the generation, editing, curation, and bulk ingestion of generative AI search queries in Zeo Geo-Radar. It encompasses three primary data ingestion and editing vectors:
1. **Single Prompt & Topic Modals (`assets/designer-wizards.js`)**: Atomic creation and inline editing modals (`add-prompt`, `edit-prompt`, `add-topic`), strict input validation (whitespace trimming, required topic bindings), optimistic state projection (`tr.dg-row-pending`), and server error banners (`duplicate_prompt`).
2. **AI Cluster Generator & Discovery Pipeline (`assets/prompt-designer.js`, `backend/workers/suggest-base.ts`)**: 4-step wizard dispatching asynchronous Trigger.dev synthesis tasks (`suggest-project-prompts`), template variable evaluation (`{brand}`, `{category}`, `{location}`), Brand Hub Truth Vault grounding, closed-enum validation (`promptTypeOf`), 40-second polling timeout safeguards, client-side deduplication against database active prompts (`isExistingDuplicate`, `.dg-dup-row`), and selective PostgreSQL batch commit (`import-discovered-prompts`).
3. **Bulk CSV Ingestion Engine (`assets/designer-wizards.js`)**: Client-side delimiter parsing and header guessing, UTF-8 BOM stripping (`\uFEFF`), and server-side row-level pre-validation (`preview-prompts-csv`) with itemized defect tags (`duplicate_in_file`, `duplicate_existing`, `invalid`).

---

## 2. Vocabulary & Placeholders Dictionary

| Placeholder | Context / Semantics | Example Concrete Value |
|---|---|---|
| `[DOMAIN]` | Target brand domain | `daikin.com.tr` |
| `[SLUG]` | Target project workspace slug | `daikin` |
| `[COUNTRY]` | Target market ISO-2 country code | `US`, `TR`, `GB`, `DE` |
| `[LANGUAGE]` | Target locale BCP-47 identifier | `en`, `tr`, `de`, `fr` |
| `[PROMPT_TEXT]` | New or edited query string | `"Daikin Sensira vs Shira Plus klima farkı nedir?"` |
| `[TOPIC_NAME]` | Category / cluster taxonomy title | `"Klimalar"`, `"Isı Pompaları"` |
| `[INTENT_TYPE]` | Intent classification label | `info`, `comm`, `trans`, `nav` |
| `[DISCOVERY_TASK_ID]` | Trigger.dev asynchronous run ID | `[DISCOVERY_TASK_ID]` |
| `[VARIABLE_NAME]` | Injected template variable tag | `{brand}`, `{category}`, `{location}` |
| `[CSV_FILENAME]` | Local CSV file uploaded via wizard | `prompts-q3-export.csv` |

---

## 3. Architecture & Target Component Reference

### 3.1 Component & Source Code Map
- **`assets/prompt-designer.js`**: `window.ZEO_PROMPT_DESIGNER`, `initFromProject`, `dispatchDiscovery`, `startPollingBatch`, `processDiscoveredOutput`, `commitImport`, `renderConfigureStep`, `renderLoadingStep`, `renderReviewStep`, `renderErrorStep`, `normalizeText`
- **`assets/designer-wizards.js`**: Modals (`add-prompt`, `edit-prompt`, `add-topic`), CSV wizards (`open-csv-wizard`, `dgcsv-open`), parsers (`parseCSVText`, `guessMappings`, `buildParsedFromMappings`)
- **`backend/workers/suggest-base.ts`**: AI prompt synthesizer (`suggest-project-prompts`), variable substitution, brand balance ratio (30-40% brand, 60-70% non-brand), closed-enum validator `promptTypeOf`
- **`assets/designer.css`**: Modal styles (`.zr-wizard`, `.wizard-split`, `.wizard-side`, `.gen-pane`, `.csv-map-row`, `.csv-dropzone`, `.dgcsv-errlist`, `.dg-dup-row`)

### 3.2 Key DOM Selectors & Forms
- **Add Prompt Form**: `input#dgPromptText`, `select#dgPromptTopic`, `select#dgPromptType`, `select#dgPromptCountry`, `select#dgPromptLocale`, `input#dgPromptIntent`, `button[data-action="apply-bulk-modal"][data-type="add-prompt"]`
- **Edit Prompt Form**: `button[data-action="dg-edit-prompt"]`, `button[data-action="apply-bulk-modal"][data-type="edit-prompt"]`, `tr.dg-row-pending`, `span.dg-save-chip.saved`, `span.dg-save-chip.failed`
- **Topic Creation**: `input#newTopicInput`, `button[data-action="apply-bulk-modal"][data-type="add-topic"]`
- **AI Discovery Step 1 (Configure)**: `input[data-action-input="dg-discover-prompts-count"]`, `input[data-action-input="dg-discover-custom-topic"]`, `input[type="checkbox"][data-action="dg-discover-toggle-grounding"]`, `button[data-action="dg-discover-generate"]`
- **AI Discovery Step 2 (Synthesis)**: `.wizard-load-title`, `.wizard-stage`, `.wizard-progress-fill`
- **AI Discovery Step 3 (Review)**: `table.tbl.csv-rev-tbl`, `tr.dg-dup-row`, `input[data-action-input="dg-discover-edit-text"]`, `button[data-action="dg-discover-toggle-type"]`, `button[data-action="dg-discover-commit"]`
- **CSV Ingestion**: `.csv-dropzone`, `input#csvFileInput`, `select[data-dg-select="csv-map"]`, `.dgcsv-errlist`, `span.dgcsv-st.dup`, `button#dgcsvImportBtn`

---

## 4. Authoritative Business & State Machine Rules

1. **Input Validation & Trimming**:
   - Prompt text is trimmed: `value.replace(/^\s+|\s+$/g, '')`.
   - If empty or whitespace-only, submission halts immediately with toast: `"Enter the prompt text."` (Turkish: `"Prompt metnini girin."`).
   - If topic select is empty, submission halts with toast: `"Add a topic first."` (Turkish: `"Önce bir konu ekleyin."`). Zero mutations are dispatched to the server.

2. **Deduplication Key & Turkish Casing Invariance**:
   - Normalized deduplication key:
     $$\text{Key} = \text{normalizeText}(\text{text}) + \text{"::"} + \text{country} + \text{"::"} + \text{canonicalLocale}(\text{locale})$$
   - `normalizeText` strips whitespace, lowercases text, and applies custom transliteration:
     `ç -> c, ğ -> g, ı -> i, ö -> o, ş -> s, ü -> u`.
   - In Turkish locale, dotted `İ` and dotless `ı` (e.g. `"İpek"` vs `"ipek"`) both resolve to `"ipek"`, ensuring 100% duplicate detection fidelity.

3. **Template Variables & Synthesizer Robustness**:
   - Recognizes `{brand}`, `{category}`, `{location}` in seed inputs.
   - Malformed or unclosed variable tokens (e.g. `{brand` without closing brace) MUST NOT crash the parser and are treated as literal text.
   - Synthesizer enforces 30-40% brand queries and 60-70% non-brand queries.
   - Closed-enum validation in `promptTypeOf`: only `"brand"` and `"non_brand"` are accepted. Any unexpected value throws `suggestion_reply_item_invalid_enum`.

4. **AI Discovery Review Deduplication**:
   - Discovered candidate items are checked against `existingLookup[key]`.
   - Matching items set `isExistingDuplicate: true` and `selected: false` (deselected by default).
   - In the review table, duplicate rows gain class `tr.dg-dup-row` and display a red badge `"Duplicate (Existing)"`.

5. **AI Discovery Polling Timeout**:
   - Polling has a 40-second / 30-tick watchdog budget.
   - If the task does not reach ready status within the budget, `onStop('limit')` transitions the wizard to `state.step = 'error'` with code `dependency_unavailable`.

6. **CSV Bulk Upload Resilience**:
   - Strips leading UTF-8 BOM (`\uFEFF`).
   - Semicolon or tab-delimited files fail comma parsing; `guessMappings` flags missing prompt/topic columns, disabling import.
   - Server-side pre-flight `preview-prompts-csv` audits rows, generating itemized defect tags (`duplicate_in_file`, `duplicate_existing`, `invalid`) before allowing commit.

---

## 5. Test Case Inventory & Traceability Matrix

| Original Monolithic ID | Modular Case File | Case Title & Scope Summary |
|---|---|---|
| `TC-PCREAT-01` | `01-gherkin-case-single-prompt-creation-and-optimistic-save.md` | Single Prompt Modal Creation, Optimistic Row & Server Save Settle |
| `TC-PCREAT-02`, `TC-PCREAT-11`, `TC-PCREAT-12` | `02-gherkin-case-prompt-form-validation-and-whitespace-gating.md` | Input Validation Gating, Whitespace-Only String & Missing Topic Rejection |
| `TC-PCREAT-03`, `TC-PCREAT-13` | `03-gherkin-case-prompt-modal-editor-and-server-duplicate-conflict.md` | Inline & Modal Prompt Editor, Attribute Modification & Server Duplicate 409 |
| `TC-PCREAT-04` | `04-gherkin-case-topic-cluster-creation-and-sidebar-sync.md` | Taxonomy Topic Creation Modal & Sidebar Cluster Synchronization |
| `TC-PCREAT-05`, `TC-PCREAT-06` | `05-gherkin-case-ai-discovery-configuration-and-grounding.md` | AI Discovery Configuration, 1-50 Count Slider & Truth Vault Grounding |
| `TC-PCREAT-14` | `06-gherkin-case-ai-synthesis-variable-injection-and-turkish-casing.md` | Template Variable Substitution, Syntax Resilience & Turkish Locale Invariance |
| `TC-PCREAT-07`, `TC-PCREAT-15` | `07-gherkin-case-ai-discovery-polling-lifecycle-and-timeout.md` | Asynchronous AI Task Polling, Stage Animations & 40s Timeout Handling |
| `TC-PCREAT-08`, `TC-PCREAT-09`, `TC-PCREAT-16` | `08-gherkin-case-ai-review-deduplication-and-matrix-curation.md` | Discovered Prompt Review Matrix, Inline Editing & Duplicate Default Deselect |
| `TC-PCREAT-10` | `09-gherkin-case-ai-review-selective-commit-and-import.md` | Discovered Candidate Batch Commit, Counters & Table Synchronization |
| `TC-PCREAT-17` | `10-gherkin-case-csv-bulk-upload-delimiter-and-syntax-resilience.md` | CSV Dropzone Parser, BOM Stripping & Corrupted Delimiter Resilience |
| `TC-PCREAT-18` | `11-gherkin-case-csv-server-preview-validation-and-defect-chips.md` | Server-Side CSV Pre-flight Validation & Itemized Defect Badges |

---

## 6. Execution Model & Quality Contract

- **Automated Executor**: Runs via `ego-browser nodejs` on the physical macOS test workstation.
- **Visual Artifacts**: All modal, review matrix, and error states are screenshotted to `/tmp/shots/` on the remote runner and transferred via `scp` into case-specific result folders.
- **Result Directory Pattern**: Each case targets `01-gherkin-result-case-<short-slug>/`. *(Directories are populated solely upon actual execution).*
