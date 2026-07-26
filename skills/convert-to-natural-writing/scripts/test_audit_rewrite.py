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

    def test_frontmatter_keys_and_protected_values(self) -> None:
        original = '---\ntitle: "Old title"\nslug: keep-me\ndraft: false\n---\nOld copy.\n'
        title_change = '---\ntitle: "Better title"\nslug: keep-me\ndraft: false\n---\nNew copy.\n'
        slug_change = title_change.replace("keep-me", "changed")
        removed_key = title_change.replace('title: "Better title"\n', "")
        self.assert_passes(original, title_change)
        self.assert_fails_in("frontmatter-protected-values", original, slug_change)
        self.assert_fails_in("frontmatter-keys", original, removed_key)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
