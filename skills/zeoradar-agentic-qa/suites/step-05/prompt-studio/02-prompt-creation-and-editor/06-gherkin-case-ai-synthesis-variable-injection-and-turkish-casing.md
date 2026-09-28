# Test Case 06: Template Variable Substitution, Syntax Resilience & Turkish Locale Invariance

## 1. Case ID and Purpose
- **Case ID**: `TC-PCREAT-06-SYNTHESIS-VARIABLES`
- **Purpose**: Verify that the prompt generation pipeline evaluates template variables (`{brand}`, `{category}`, `{location}`) correctly, treats malformed or unclosed variable tokens (e.g. `{brand`) as literal query strings without syntax exceptions, adheres to the closed-enum type constraint (`promptTypeOf`), and maintains strict Turkish locale casing and diacritic normalization invariance (`İ` / `ı` to `i`) in `normalizeText`.

---

## 2. Tester Brief
The tester will:
1. Examine seed input templates containing variables: `{brand}`, `{category}`, and `{location}`.
2. Verify that variable injection in `backend/workers/suggest-base.ts` produces valid localized search queries respecting the 30-40% brand to 60-70% non-brand ratio.
3. Inject an unclosed variable token `{brand` into editorial instructions or custom topics and confirm the synthesizer evaluates it literally without throwing unhandled parsing exceptions.
4. Test the Turkish diacritic normalization algorithm in `assets/prompt-designer.js` (`normalizeText`):
   - Assert uppercase dotted `"İ"` and lowercase `"i"` both resolve to `'i'`.
   - Assert uppercase dotless `"I"` and lowercase `"ı"` both resolve to `'i'`.
   - Verify that deduplication keys for `"İpek"` and `"ipek"` produce identical keys, preventing duplicate insertion.
5. Verify that `promptTypeOf` strictly enforces closed enum (`brand` vs `non_brand`), rejecting hallucinated types with `suggestion_reply_item_invalid_enum`.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Locale Under Test**: `tr` (Turkish) and `en` (English)
- **Seed Templates**:
  - Valid: `"Where can I find {brand} assortments in {location}?"`
  - Unclosed Token: `"Compare {brand air conditioner with heat pump"`
  - Turkish Casing: `"İklimlendirme ve Isı Pompası Çözümleri"` vs `"iklimlendirme ve isi pompasi cozumleri"`

---

## 4. Gherkin Scenario

```gherkin
Feature: Template Variable Synthesis, Syntax Resilience & Turkish Normalization

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And the AI synthesis engine is initialized for project "[SLUG]"

  @synthesis @variables
  Scenario Outline: Synthesize prompts with template variable replacement and strategic balance
    Given the generator receives seed with template variable "<VariableToken>"
    When the synthesis task "suggest-project-prompts" executes
    Then the synthesized output query should contain the concrete value "<SubstitutedValue>"
    And the strategic ratio should maintain between 30% and 40% brand-type queries

    Examples:
      | VariableToken | SubstitutedValue |
      | {brand}       | Daikin           |
      | {category}    | heat pump        |
      | {location}    | Istanbul         |

  @syntax @resilience
  Scenario: Malformed and unclosed variable tokens are evaluated as literal text
    Given an editorial instruction contains the unclosed variable token "{brand"
    When the synthesis worker processes the seed prompt
    Then the worker must complete successfully without syntax errors
    And the resulting prompt query should contain the literal string "{brand"

  @turkish @i18n @deduplication
  Scenario Outline: Turkish dotted and dotless diacritics resolve invariantly in deduplication
    When the normalization function "normalizeText" processes input "<InputText>"
    Then the normalized output string should equal "<NormalizedResult>"
    And the deduplication key should match between uppercase and lowercase variants

    Examples:
      | InputText                | NormalizedResult         |
      | İpek Yolu                | ipek yolu                |
      | ipek yolu                | ipek yolu                |
      | Işık Dağı                | isik dagi                |
      | ışık dağı                | isik dagi                |
      | Isıtma ve Soğutma        | isitma ve sogutma        |

  @worker @type-safety
  Scenario: Closed enum guard rejects unlisted prompt type values
    When the synthesizer reply contains an item with type "sponsored"
    Then the validator "promptTypeOf" should throw "suggestion_reply_item_invalid_enum"
    And the worker should reject silent fallback to non_brand
```

---

## 5. Visual Checks
1. **Rendered Prompt Review**: Synthesized prompts in Step 3 display clean substituted text without dangling curly braces unless unclosed syntax was intentionally passed.
2. **Type Badges**: Prompt type buttons in the review table display either `"Brand"` or `"Non-brand"` based strictly on the closed enum value.

---

## 6. Data and Network Checks
1. **Normalization Function Unit Check**:
   ```javascript
   function normalizeText(value) {
     return String(value == null ? '' : value)
       .replace(/^\s+|\s+$/g, '')
       .replace(/\s+/g, ' ')
       .toLowerCase()
       .replace(/[ç]/g, 'c')
       .replace(/[ğ]/g, 'g')
       .replace(/[ı]/g, 'i')
       .replace(/[ö]/g, 'o')
       .replace(/[ş]/g, 's')
       .replace(/[ü]/g, 'u');
   }

   const keyUpper = normalizeText("İKLİMLENDİRME VE ISI POMPASI") + "::TR::tr";
   const keyLower = normalizeText("iklimlendirme ve isi pompasi") + "::TR::tr";
   assert.strictEqual(keyUpper, keyLower, "Turkish diacritics must resolve to identical deduplication keys");
   ```
2. **Worker Enum Guard**:
   - Inspect `backend/workers/suggest-base.ts`: verify `promptTypeOf` checks `value === "brand" || value === "non_brand"`.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-ai-synthesis-variable-injection-and-turkish-casing/`
- **Execution Model Notice**: Automated tests run via Ego Browser and Node.js harnesses on macOS. Normalization tests output results to `/tmp/shots/synthesis-normalization-[LOCALE].json` and are retrieved via SCP.
- **Report Contents**:
  - `status.json`: Test execution log and assertion state.
  - `normalization-matrix.json`: Table of tested Turkish characters and their normalized outcomes.
  - `screenshot-synthesized-prompts.png`: Review table displaying substituted prompt queries.
