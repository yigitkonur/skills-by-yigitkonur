#!/usr/bin/env python3
"""Regression tests for audit-rewrite.py."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
SCRIPT = Path(__file__).with_name("audit-rewrite.py")
SPEC = importlib.util.spec_from_file_location("audit_rewrite", SCRIPT)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


class AuditRewriteTests(unittest.TestCase):
    def assert_passes(self, original: str, revised: str) -> None:
        report = AUDIT.audit(original, revised)
        self.assertTrue(report["pass"], report)

    def assert_fails_in(self, category: str, original: str, revised: str) -> None:
        report = AUDIT.audit(original, revised)
        self.assertFalse(report["pass"], report)
        categories = {item["category"] for item in report["differences"]}
        self.assertIn(category, categories, report)

    def test_plain_prose_can_change(self) -> None:
        self.assert_passes("This generic sentence is long.", "This sentence is clearer.")

    def test_urls_and_emails_are_protected(self) -> None:
        original = "Visit https://example.com/a and email team@example.com."
        revised = "Email team@example.org or visit https://example.com/b."
        report = AUDIT.audit(original, revised)
        categories = {item["category"] for item in report["differences"]}
        self.assertTrue({"urls", "emails"}.issubset(categories), report)

    def test_markdown_label_can_change_but_destination_cannot(self) -> None:
        self.assert_passes("Read [the complete guide](https://example.com/docs).", "See [the guide](https://example.com/docs).")
        self.assert_fails_in(
            "markdown-destinations",
            "Read [the guide](https://example.com/docs).",
            "Read [the guide](https://example.com/start).",
        )

    def test_reference_definitions_and_relative_destinations_are_protected(self) -> None:
        original = "Read [the guide][docs].\n\n[docs]: <../guides/start_(here).md> \"Start\"\n"
        revised = "See [our guide][docs].\n\n[docs]: <../guides/finish_(here).md> \"Start\"\n"
        self.assert_fails_in("markdown-references", original, revised)

    def test_reference_identifier_can_remain_while_visible_label_changes(self) -> None:
        original = "Read [the old label][docs].\n\n[docs]: /guide\n"
        revised = "See [the clearer label][docs].\n\n[docs]: /guide\n"
        self.assert_passes(original, revised)

    def test_reference_titles_are_copy_but_shortcuts_and_footnote_ids_are_protected(self) -> None:
        original = 'Read [docs] and note [^scope].\n\n[docs]: ../guide.md "Old title"\n[^scope]: Old note.\n'
        title_and_note_rewrite = (
            'See [docs] and note [^scope].\n\n[docs]: ../guide.md "Clear title"\n[^scope]: Clear note.\n'
        )
        changed_footnote = title_and_note_rewrite.replace("[^scope]", "[^limits]")
        self.assert_passes(original, title_and_note_rewrite)
        self.assert_fails_in("markdown-references", original, changed_footnote)

    def test_nested_markdown_destination_is_protected_but_title_is_copy(self) -> None:
        original = 'Read [the guide](../guides/start_(here).md "Old title").'
        title_change = 'See [our guide](../guides/start_(here).md "Clear title").'
        destination_change = 'See [our guide](../guides/finish_(here).md "Clear title").'
        self.assert_passes(original, title_change)
        self.assert_fails_in("markdown-destinations", original, destination_change)

    def test_numbers_dates_currency_and_units_are_protected(self) -> None:
        original = "On 2026-07-26, 12.5% paid €49 for 10 GB."
        revised = "On 2026-07-27, 12% paid €59 for 20 GB."
        self.assert_fails_in("numbers-dates-currency-units", original, revised)

    def test_inline_and_fenced_code_are_protected(self) -> None:
        original = "Run `pnpm verify`.\n\n```bash\npnpm verify --filter site\n```\n"
        changed_inline = original.replace("`pnpm verify`", "`pnpm test`")
        changed_fence = original.replace("--filter site", "--filter app")
        self.assert_fails_in("inline-code", original, changed_inline)
        self.assert_fails_in("fenced-code", original, changed_fence)

    def test_longer_closing_fence_and_multibacktick_span_are_protected(self) -> None:
        original = "Use ``code with ` inside``.\n\n```txt\nexact prose-like code\n````\n"
        changed_span = original.replace("code with ` inside", "different ` code")
        changed_fence = original.replace("exact prose-like code", "changed prose-like code")
        self.assert_fails_in("inline-code", original, changed_span)
        self.assert_fails_in("fenced-code", original, changed_fence)

    def test_code_like_numbers_do_not_leak_into_prose_inventory(self) -> None:
        original = "Use this command:\n\n```bash\nretry --count 3\n```\n"
        revised = "Run the command:\n\n```bash\nretry --count 3\n```\n"
        self.assert_passes(original, revised)

    def test_indented_code_is_protected(self) -> None:
        original = "Run this command:\n\n    deploy --environment staging\n    verify --sha 123\n"
        revised = "Use these commands:\n\n    deploy --environment production\n    verify --sha 123\n"
        self.assert_fails_in("indented-code", original, revised)

    def test_frontmatter_keys_and_protected_values(self) -> None:
        original = '---\ntitle: "Old title"\nslug: keep-me\ndraft: false\n---\nOld copy.\n'
        title_change = '---\ntitle: "Better title"\nslug: keep-me\ndraft: false\n---\nNew copy.\n'
        slug_change = title_change.replace("keep-me", "changed")
        removed_key = title_change.replace('title: "Better title"\n', "")
        self.assert_passes(original, title_change)
        self.assert_fails_in("frontmatter-protected-values", original, slug_change)
        self.assert_fails_in("frontmatter-keys", original, removed_key)

    def test_frontmatter_sequences_and_noncopy_scalars_are_protected(self) -> None:
        original = '---\ntitle: "Old"\nauthor: Ada\ntags:\n  - stable\n  - public\n---\nOld copy.\n'
        revised = '---\ntitle: "Better"\nauthor: Grace\ntags:\n  - changed\n  - public\n---\nNew copy.\n'
        self.assert_fails_in("frontmatter-protected-values", original, revised)

    def test_nested_frontmatter_copy_fields_can_change_but_object_ids_cannot(self) -> None:
        original = (
            "---\nseo:\n  title: Old title\n  description: Old description\nauthors:\n"
            "  - name: Ada\n    id: author-1\n---\nOld body.\n"
        )
        copy_change = (
            "---\nseo:\n  title: Clear title\n  description: Clear description\nauthors:\n"
            "  - name: Ada\n    id: author-1\n---\nClear body.\n"
        )
        id_change = copy_change.replace("author-1", "author-2")
        self.assert_passes(original, copy_change)
        self.assert_fails_in("frontmatter-protected-values", original, id_change)

    def test_frontmatter_copy_block_may_change_without_losing_shape(self) -> None:
        original = "---\ndescription: >\n  Old generic copy.\nslug: stable\n---\nBody.\n"
        revised = "---\ndescription: >\n  Clear useful copy.\nslug: stable\n---\nRevised body.\n"
        self.assert_passes(original, revised)

    def test_html_text_and_copy_attributes_may_change(self) -> None:
        original = '<p class="lead"><img src="hero.png" alt="Generic image">Old copy.</p>'
        revised = '<p class="lead"><img src="hero.png" alt="Team reviewing a report">Clear copy.</p>'
        self.assert_passes(original, revised)

    def test_html_and_jsx_structure_is_protected(self) -> None:
        original = '<Callout tone="warning" id="renewal">Old copy.</Callout>'
        changed_attr = '<Callout tone="info" id="renewal">New copy.</Callout>'
        changed_name = '<Notice tone="warning" id="renewal">New copy.</Notice>'
        self.assert_fails_in("markup-protected-values", original, changed_attr)
        self.assert_fails_in("markup-tags", original, changed_name)

    def test_language_and_direction_values_are_protected(self) -> None:
        original = '<p lang="tr" dir="ltr">Metin.</p>'
        revised = '<p lang="en" dir="rtl">Text.</p>'
        self.assert_fails_in("markup-protected-values", original, revised)

    def test_html_comments_entities_and_raw_text_are_protected(self) -> None:
        original = '<!-- cms:keep --><p>A&nbsp;B</p><script type="application/ld+json">{"name":"Old"}</script>'
        changed_comment = original.replace("cms:keep", "cms:drop")
        changed_entity = original.replace("&nbsp;", "&thinsp;")
        changed_script = original.replace('"Old"', '"New"')
        self.assert_fails_in("html-comments", original, changed_comment)
        self.assert_fails_in("html-entities", original, changed_entity)
        self.assert_fails_in("html-raw-text", original, changed_script)

    def test_raw_text_isolated_from_mdx_expressions_and_unclosed_comments_are_artifacts(self) -> None:
        original = '<style>.card { color: red; }</style><p>Old copy.</p>'
        revised = '<style>.card { color: blue; }</style><p>Clear copy.</p>'
        report = AUDIT.audit(original, revised)
        categories = {item["category"] for item in report["differences"]}
        self.assertIn("html-raw-text", categories, report)
        self.assertNotIn("brace-expressions", categories, report)

        malformed = AUDIT.audit("<p>Copy.</p>", "<!-- unfinished\n<p>Copy.</p>")
        self.assertFalse(malformed["pass"], malformed)
        self.assertTrue(any("unclosed-html-comment" in item for item in malformed["artifacts"]["added"]), malformed)

    def test_mdx_expressions_esm_and_template_directives_are_protected(self) -> None:
        expression_original = '<Price value={{monthly: prices[locale]}}>{format(price)}</Price>'
        expression_revised = '<Price value={{annual: prices[locale]}}>{format(total)}</Price>'
        expression_report = AUDIT.audit(expression_original, expression_revised)
        expression_categories = {item["category"] for item in expression_report["differences"]}
        self.assertIn("brace-expressions", expression_categories, expression_report)

        esm_original = 'export const plan = "starter"\n\n# Old\n'
        esm_revised = 'export const plan = "enterprise"\n\n# New\n'
        self.assert_fails_in("mdx-esm", esm_original, esm_revised)

        template_original = "Hello {{ customer.name }}. {% if active %}${plan}{% endif %}"
        template_revised = "Hello {{ account.name }}. {% if trial %}${tier}{% endif %}"
        self.assert_fails_in("template-directives", template_original, template_revised)

    def test_localized_currency_suffix_and_spacing_are_protected(self) -> None:
        original = "Plan A: 100\u00a0zł; Plan B: ₺1.250,50; Plan C: ١٢٫٥ د.إ"
        revised = "Plan A: 100\u00a0kr; Plan B: ₺1.250,50; Plan C: ١٢٫٥ ر.س"
        self.assert_fails_in("numbers-dates-currency-units", original, revised)

    def test_user_protected_literals_cover_legal_terms_and_names(self) -> None:
        original = "Offer is void where prohibited. Contact Acme & Co."
        revised = "Offer is unavailable where prohibited. Contact Acme and Company."
        report = AUDIT.audit(
            original,
            revised,
            protected_literals=["Offer is void where prohibited.", "Acme & Co."],
        )
        self.assertFalse(report["pass"], report)
        categories = {item["category"] for item in report["differences"]}
        self.assertIn("user-protected-literals", categories, report)

    def test_user_protected_literal_must_exist_in_original(self) -> None:
        with self.assertRaisesRegex(ValueError, "not present in original"):
            AUDIT.audit("Original copy.", "Revised copy.", protected_literals=["Missing invariant"])

    def test_user_protected_literal_preserves_occurrence_count_and_deduplicates_inputs(self) -> None:
        report = AUDIT.audit("Exact / Exact", "Exact", protected_literals=["Exact", "Exact"])
        self.assertFalse(report["pass"], report)
        difference = next(item for item in report["differences"] if item["category"] == "user-protected-literals")
        self.assertEqual(["Exact"], difference["missing"], report)

    def test_low_signal_and_large_delta_warnings_do_not_claim_failure(self) -> None:
        low_signal = AUDIT.audit("Plain original prose.", "Clear revised prose.")
        self.assertTrue(low_signal["pass"], low_signal)
        self.assertIn("no-deterministic-protections", {item["code"] for item in low_signal["warnings"]})

        empty = AUDIT.audit("", "New prose without protected tokens.")
        self.assertTrue(empty["pass"], empty)
        self.assertIn("original-empty", {item["code"] for item in empty["warnings"]})

        large_delta = AUDIT.audit("Keep 2026. Short.", "Keep 2026. " + "Expanded prose. " * 20)
        self.assertTrue(large_delta["pass"], large_delta)
        self.assertIn("large-size-delta", {item["code"] for item in large_delta["warnings"]})

    def test_multilingual_assistant_and_prompt_residue_fail(self) -> None:
        revised = (
            "İşte yeniden yazılmış sürüm:\n\nMetin.\n\n"
            "Como modelo de lenguaje de IA, no tengo opiniones personales."
        )
        report = AUDIT.audit("Metin.", revised)
        self.assertFalse(report["pass"], report)
        self.assertGreaterEqual(len(report["artifacts"]["added"]), 2, report)

    def test_new_unclosed_fence_is_an_artifact(self) -> None:
        original = "Text.\n\n```txt\nclosed\n```\n"
        revised = "Text.\n\n```txt\nunclosed\n"
        report = AUDIT.audit(original, revised)
        self.assertFalse(report["pass"], report)
        self.assertTrue(any("unclosed-fence" in item for item in report["artifacts"]["added"]), report)

    def test_new_artifact_fails_but_existing_artifact_is_reported(self) -> None:
        added = AUDIT.audit("Ready copy.", "Ready copy. [insert source]")
        self.assertFalse(added["pass"])
        self.assertTrue(added["artifacts"]["added"])

        existing = AUDIT.audit("TODO: add source", "TODO: add source")
        self.assertTrue(existing["pass"], existing)
        self.assertTrue(existing["artifacts"]["existing"])
        self.assertFalse(existing["artifacts"]["added"])

    def test_assistant_chatter_and_citation_residue_fail(self) -> None:
        report = AUDIT.audit("Article text.", "Here is the revised version:\n\nArticle text. citeturn0search1")
        self.assertFalse(report["pass"])
        self.assertEqual(2, len(report["artifacts"]["added"]), report)

    def test_cli_json_and_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.md"
            revised = root / "revised.md"
            original.write_text("Price: €49.", encoding="utf-8")
            revised.write_text("The price is €49.", encoding="utf-8")
            passed = subprocess.run(
                [sys.executable, str(SCRIPT), "--json", str(original), str(revised)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, passed.returncode, passed.stderr)
            payload = json.loads(passed.stdout)
            self.assertTrue(payload["pass"])
            self.assertIn("does not prove semantic equivalence", payload["limitations"][0])

            revised.write_text("The price is €59.", encoding="utf-8")
            failed = subprocess.run(
                [sys.executable, str(SCRIPT), str(original), str(revised)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, failed.returncode)
            self.assertTrue(failed.stdout.startswith("FAIL"), failed.stdout)

    def test_cli_protect_and_protect_from(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.md"
            revised = root / "revised.md"
            protected = root / "protected.txt"
            original.write_text("Keep Exact Product Name and Legal phrase.", encoding="utf-8")
            revised.write_text("Keep Product Name and revised phrase.", encoding="utf-8")
            protected.write_text("# exact literals\nExact Product Name\nLegal phrase\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--json",
                    "--protect",
                    "Exact Product Name",
                    "--protect-from",
                    str(protected),
                    str(original),
                    str(revised),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("user-protected-literals", {item["category"] for item in payload["differences"]})

    def test_cli_rejects_missing_protected_literal_and_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.md"
            revised = root / "revised.md"
            original.write_text("Original.", encoding="utf-8")
            revised.write_text("Revised.", encoding="utf-8")
            missing_literal = subprocess.run(
                [sys.executable, str(SCRIPT), "--protect", "Absent", str(original), str(revised)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, missing_literal.returncode)
            self.assertIn("not present in original", missing_literal.stderr)

            missing_file = subprocess.run(
                [sys.executable, str(SCRIPT), "--protect-from", str(root / "missing.txt"), str(original), str(revised)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, missing_file.returncode)
            self.assertIn("cannot read", missing_file.stderr)

    def test_cli_rejects_blank_literal_and_empty_protection_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.md"
            revised = root / "revised.md"
            empty = root / "empty.txt"
            original.write_text("Original.", encoding="utf-8")
            revised.write_text("Revised.", encoding="utf-8")
            empty.write_text("# comments only\n\n", encoding="utf-8")

            blank = subprocess.run(
                [sys.executable, str(SCRIPT), "--protect", "  ", str(original), str(revised)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, blank.returncode)
            self.assertIn("must not be blank", blank.stderr)

            empty_file = subprocess.run(
                [sys.executable, str(SCRIPT), "--protect-from", str(empty), str(original), str(revised)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, empty_file.returncode)
            self.assertIn("contains no protected literals", empty_file.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
