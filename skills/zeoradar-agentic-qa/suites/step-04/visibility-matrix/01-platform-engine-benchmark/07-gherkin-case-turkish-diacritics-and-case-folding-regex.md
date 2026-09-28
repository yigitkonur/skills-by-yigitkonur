# Test Case: TC-VIS-07 - Turkish Diacritics, Case-Folding Regex & Word Boundaries

## 1. Case ID and Purpose
- **Case ID:** `TC-VIS-07`
- **Module:** Answer Engine Insights (`assets/aei.js`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture, Turkish Localization Law)
- **Traceability:** Maps to Source Scenarios `VIS-10` and `VIS-23`
- **Purpose:** Verify that the brand mention detection engine (`textMentionsBrand`) and highlight builder (`highlightAnswerText`) utilize `buildTurkishRegexPattern` to correctly handle Turkish-specific case variations—specifically dotted `İ` / `i`, dotless `I` / `ı`, and diacritics (`ş`/`Ş`, `ç`/`Ç`, `ö`/`Ö`, `ü`/`Ü`, `ğ`/`Ğ`)—ensuring accurate mention identification and green `<mark class="aei-mention-brand">` wrapping without false substring collisions or case mismatch failures.

---

## 2. Tester Brief
The tester or automated agent verifies Turkish language casing robustness in Answer Engine text evaluation:
1. Standard JavaScript `.toLowerCase()` and `.toUpperCase()` corrupt Turkish dotted/dotless I conversions (e.g. `'İ'.toLowerCase()` produces `'i'`, but `'I'.toLowerCase()` produces `'i'` instead of `'ı'` in default English locales).
2. `buildTurkishRegexPattern(term)` explicitly substitutes characters with regex character classes:
   - `i` or `İ` becomes `[iİ]`
   - `ı` or `I` becomes `[ıI]`
   - `ş` or `Ş` becomes `[şŞ]`
   - `ç` or `Ç` becomes `[çÇ]`
   - `ö` or `Ö` becomes `[öÖ]`
   - `ü` or `Ü` becomes `[üÜ]`
   - `ğ` or `Ğ` becomes `[ğĞ]`
3. Word boundaries `(^|[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ_])` and `(?=[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ_]|$)` ensure brand terms do not match arbitrary substrings inside unrelated words.
4. Verify both unit-level regex behavior and visual UI `<mark class="aei-mention-brand">` rendering across varied Turkish brand representations.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=studio`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]` (`p.me = "[BRAND]"`)
- **UI Language `[LANGUAGE]`:** `tr`
- **Target Terms:** `İklimlendirme`, `iklimlendirme`, `İKLİMLENDİRME`, `Isıtma`, `ısıtma`, `ISITMA`
- **Matching Result Directory:** `07-gherkin-result-case-turkish-diacritics-and-case-folding-regex/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Turkish Diacritic Case-Folding and Boundary-Safe Brand Mention Detection

  Background:
    Given the application runs in a dual-locale environment supporting Turkish diacritics
    And the brand mention regex engine utilizes "buildTurkishRegexPattern"

  Scenario Outline: Turkish Dotted and Dotless I Case-Folding Resilience
    Given the monitored brand is "<BrandTerm>"
    When an AI synthesized answer contains the text "<AnswerExcerpt>"
    Then "textMentionsBrand" should evaluate to true
    And the rendered answer HTML should highlight "<MatchedTerm>" inside "<mark class='aei-mention-brand'>"

    Examples:
      | BrandTerm | AnswerExcerpt                                                    | MatchedTerm |
      | İklimlendirme | Türkiye'nin önde gelen iklimlendirme markalarından daikin son... | iklimlendirme |
      | İklimlendirme | Konut ve ticari alanlarda İklimlendirme çözümleri tercih ediliyor.| İklimlendirme |
      | İklimlendirme | Enerji tasarrufu ve verimlilikte İKLİMLENDİRME öne çıkmaktadır.   | İKLİMLENDİRME |
      | Isıtma        | Kış aylarında ısıtma sistemleri lider konumdadır.                 | ısıtma        |
      | Isıtma        | Yüksek verimli ISITMA ürünleri tavsiye edilmektedir.              | ISITMA        |
      | Isıtma        | İklimlendirme sektöründe Isıtma sistemleri yüksek güvenilirlik sunar.| Isıtma     |

  Scenario Outline: Word Boundary Isolation Against Substring False Positives
    Given the monitored brand is "<BrandTerm>"
    When an AI synthesized answer contains the text "<MisleadingWord>"
    Then "textMentionsBrand" should evaluate to false
    And the text "<MisleadingWord>" should not be wrapped in "<mark class='aei-mention-brand'>"

    Examples:
      | BrandTerm | MisleadingWord                         | Description                          |
      | Isıtma    | Isıtma borularında kısıtlamalar başladı | Contains substring 'sıtma'           |
      | Çam       | Şirket çalışanlarının tamamı katıldı   | Contains substring 'çam' inside word |
      | Ak        | Şirket bu yıl paketi açıkladı          | Contains substring 'ak' inside paket |
```

---

## 5. Visual Checks
1. **Highlight Tag Styling:** `<mark class="aei-mention-brand">` renders with crisp green background (`rgba(16, 185, 129, 0.15)`) and dark green text (`var(--green)`).
2. **Text Normalcy:** Neighboring characters, punctuation, and punctuation marks (commas, periods, quotes) remain outside the `<mark>` tag.
3. **No Duplicate Highlighting:** If a brand term occurs multiple times in a paragraph, each occurrence is wrapped individually without nested `<mark>` tags.

---

## 6. Data and Network Checks
1. **JavaScript Engine Verification:**
   ```js
   const sampleAnswers = [
     { text: "Yeni nesil iklimlendirme sistemleri çok verimli.", expected: true },
     { text: "Bu oda kısıtlı alana sahiptir.", expected: false }
   ];
   sampleAnswers.forEach(s => {
     assert(textMentionsBrand(s.text, "İklimlendirme") === s.expected, "Turkish mention mismatch");
   });
   ```
2. **Regex Compilation Inspection:**
   - Confirm compiled regex has flags `i` or `gi`.
   - Verify pattern handles both standard ASCII characters and Unicode block `\u00C0-\u024F`.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `07-gherkin-result-case-turkish-diacritics-and-case-folding-regex/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`turkish_dotted_i_highlight.png`, `turkish_dotless_i_highlight.png`, `boundary_safety_negative.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/visibility/tc-vis-07-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/01-platform-engine-benchmark/07-gherkin-result-case-turkish-diacritics-and-case-folding-regex/screenshots/
     ```
  4. Write execution report `result.md` verifying regex patterns, match evaluations, and DOM snapshots.

### Pass/Fail Criteria
- [ ] Dotted `İ` matches lowercase `i` and uppercase `İ`.
- [ ] Dotless `I` matches lowercase `ı` and uppercase `I`.
- [ ] Word boundaries block false positive substring matches.
- [ ] Rendered HTML wraps verified matches with `mark.aei-mention-brand`.
