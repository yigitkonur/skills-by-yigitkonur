#!/usr/bin/env python3
"""Comprehensive test suite for audit-rewrite.py.

Verifies:
1. Valid vs invalid Active Ledger schemas (Markdown tables, sections, JSON).
2. Cadence & Rhythm metrics (burstiness, variance, std dev, monotony detection).
3. Linguistic structure heuristics (gerund cascades, nominalizations, passives).
4. CLI execution, JSON reporting, and deterministic exit codes.
5. Absolute zero dogmatic word/token blacklists.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# Prevent bytecode caching
sys.dont_write_bytecode = True

SCRIPT_PATH = Path(__file__).with_name("audit-rewrite.py")
SPEC = importlib.util.spec_from_file_location("audit_rewrite", SCRIPT_PATH)
assert SPEC and SPEC.loader
AUDIT_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT_MODULE
SPEC.loader.exec_module(AUDIT_MODULE)


class ActiveLedgerSchemaTests(unittest.TestCase):
    """Tests for Active Ledger schema validation and integrity checks."""

    def setUp(self) -> None:
        self.validator = AUDIT_MODULE.LedgerValidator()

    def test_valid_markdown_table_ledger(self) -> None:
        table = """# Active Audit Ledger

| Context | Original / Synthetic Sentence | Flaw / Category | Natural Alternative |
|:---|:---|:---|:---|
| SaaS Landing Page | Çözümümüz işletmeler tarafından sevilerek kullanılmaktadır. | Tarafından-pasifi ve kopula yığılması | İşletmeler çözümümüzü severek kullanıyor. |
| Pitch Deck | Büyüme oranlarımızın artışı gerçekleştirilmiştir. | Eylemsi enflasyonu ve sahte fiilimsi | Büyümemiz hızla arttı. |
"""
        report = self.validator.validate(table)
        self.assertTrue(report.is_valid, f"Expected valid ledger, got errors: {report.errors}")
        self.assertEqual(2, report.total_findings)
        self.assertEqual("markdown_table", report.schema_detected)
        self.assertEqual("SaaS Landing Page", report.findings[0].context)
        self.assertEqual("İşletmeler çözümümüzü severek kullanıyor.", report.findings[0].alternative)

    def test_valid_turkish_headers(self) -> None:
        table = """
| Bağlam | Orijinal Cümle | Kusur / Kategori | Doğal Alternatif |
|---|---|---|---|
| E-ticaret | Ürün tarafımızca kargolanacaktır. | Tarafından-pasifi | Ürünü bugün kargoya veriyoruz. |
"""
        report = self.validator.validate(table)
        self.assertTrue(report.is_valid, report.errors)
        self.assertEqual(1, report.total_findings)
        self.assertEqual("Ürün tarafımızca kargolanacaktır.", report.findings[0].original)

    def test_invalid_ledger_missing_columns(self) -> None:
        table_missing_alt = """
| Context | Original / Synthetic Sentence | Flaw / Category |
|---|---|---|
| Docs | System was configured. | Passive voice |
"""
        report = self.validator.validate(table_missing_alt)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("alternative" in err.lower() for err in report.errors))

    def test_invalid_ledger_empty_cells(self) -> None:
        table_empty_alt = """
| Context | Original / Synthetic Sentence | Flaw / Category | Natural Alternative |
|---|---|---|---|
| Blog | Some sentence. | Some flaw |   |
"""
        report = self.validator.validate(table_empty_alt)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("empty" in err.lower() for err in report.errors))

    def test_invalid_ledger_below_min_findings(self) -> None:
        empty_table = """
| Context | Original / Synthetic Sentence | Flaw / Category | Natural Alternative |
|---|---|---|---|
"""
        validator = AUDIT_MODULE.LedgerValidator(min_findings=1)
        report = validator.validate(empty_table)
        self.assertFalse(report.is_valid)
        self.assertEqual(0, report.total_findings)

    def test_valid_json_ledger(self) -> None:
        json_data = json.dumps([
            {
                "context": "Support",
                "original": "Talebiniz alınmıştır.",
                "flaw": "Edilgen",
                "alternative": "Talebinizi aldık."
            }
        ])
        report = self.validator.validate(json_data)
        self.assertTrue(report.is_valid, report.errors)
        self.assertEqual(1, report.total_findings)
        self.assertEqual("json", report.schema_detected)

    def test_invalid_json_ledger_missing_required_fields(self) -> None:
        json_data = json.dumps([
            {
                "context": "Support",
                "original": "Talebiniz alınmıştır."
                # missing flaw and alternative
            }
        ])
        report = self.validator.validate(json_data)
        self.assertFalse(report.is_valid)
        self.assertTrue(len(report.errors) > 0)

    def test_valid_structured_markdown_sections(self) -> None:
        content = """### Finding 1
- **Context**: Mobile App
- **Original**: Butona basılarak işlem onaylanmalıdır.
- **Flaw**: Sahte fiilimsi ve zorunluluk kipi
- **Alternative**: İşlemi onaylamak için butona dokunun.
"""
        report = self.validator.validate(content)
        self.assertTrue(report.is_valid, report.errors)
        self.assertEqual(1, report.total_findings)
        self.assertEqual("markdown_sections", report.schema_detected)

    def test_empty_content_fails(self) -> None:
        report = self.validator.validate("   \n\n  ")
        self.assertFalse(report.is_valid)
        self.assertIn("empty", report.errors[0].lower())


class CadenceAndRhythmMetricTests(unittest.TestCase):
    """Tests for cadence, rhythm, burstiness, and sentence segmentation."""

    def setUp(self) -> None:
        self.analyzer = AUDIT_MODULE.CadenceAnalyzer()

    def test_empty_text(self) -> None:
        metrics = self.analyzer.analyze("")
        self.assertEqual(0, metrics.sentence_count)
        self.assertEqual(0, metrics.word_count)
        self.assertEqual(0.0, metrics.variance)

    def test_monotonous_ai_prose(self) -> None:
        # Uniform length sentences (~7 words each) typical of low-temperature robotic AI output
        monotonous_text = (
            "Sistem verimliliği artırmak amacıyla dikkatle yapılandırılmıştır. "
            "Kullanıcı deneyimi bu aşamada özenle optimize edilmektedir. "
            "Performans göstergeleri düzenli periyotlarla titizlikle izlenmektedir. "
            "Veri analitiği sonuçları haftalık toplantılarda doğrudan paylaşılmaktadır. "
            "Teknik altyapı ihtiyaçları zamanında eksiksiz olarak karşılanmaktadır."
        )
        metrics = self.analyzer.analyze(monotonous_text)
        self.assertEqual(5, metrics.sentence_count)
        # Sentence lengths should be virtually identical
        self.assertLess(metrics.standard_deviation, 2.5)
        self.assertLess(metrics.burstiness_score, -0.6)
        self.assertTrue(metrics.cadence_monotony, "Expected cadence monotony flag for robotic uniformity")

    def test_dynamic_human_prose(self) -> None:
        # Dynamic variation: 1-word punchy opening, long compound sentence (25+ words), medium, then short finish
        dynamic_text = (
            "Durduk. "
            "Salondaki sessizlik gittikçe ağırlaşırken dışarıdaki fırtınanın camlara vuran uğultusu herkesi tedirgin etmeye yetmişti; kimse ne yapacağını kestiremiyordu çünkü elektrikler de ansızın kesilmişti ve yardımın geleceği çok şüpheliydi. "
            "Birden kapı gürültüyle çalındı. "
            "Gelen oydu."
        )
        metrics = self.analyzer.analyze(dynamic_text)
        self.assertEqual(4, metrics.sentence_count)
        # High standard deviation and variance reflecting conversational breathing
        self.assertGreater(metrics.standard_deviation, 4.0)
        self.assertGreater(metrics.variance, 16.0)
        self.assertGreater(metrics.burstiness_score, -0.4)
        self.assertFalse(metrics.cadence_monotony, "Dynamic human prose should not be flagged as monotonous")
        self.assertGreater(metrics.short_sentences_count, 0)
        self.assertGreater(metrics.long_sentences_count, 0)

    def test_sentence_segmentation_with_abbreviations_and_numbers(self) -> None:
        text = (
            "Dr. Kaya ve Prof. Demir saat 14:00'te geldi. "
            "Veriler 3.14 kat artış gösterdi. "
            "Rapor vb. belgeleri masaya bıraktılar!"
        )
        sentences = AUDIT_MODULE.split_sentences(text)
        self.assertEqual(3, len(sentences), f"Expected 3 sentences, got: {sentences}")
        self.assertTrue(sentences[0].startswith("Dr. Kaya"))
        self.assertIn("3.14 kat", sentences[1])
        self.assertTrue(sentences[2].startswith("Rapor vb."))

    def test_short_to_long_ratio(self) -> None:
        text = (
            "Kısa cümle. "
            "Bir başka kısa cümle. "
            "Bu ise oldukça uzun, detaylı, akıcı, zengin ve yirmi beş kelimeden daha uzun bir yapıya sahip olan birleşik bir cümledir çünkü birden fazla yan cümlecikle ve bağlaçlarla bilerek uzatılmıştır."
        )
        metrics = self.analyzer.analyze(text)
        self.assertEqual(2, metrics.short_sentences_count)
        self.assertEqual(1, metrics.long_sentences_count)
        self.assertEqual(2.0, metrics.short_to_long_ratio)

    def test_burstiness_score_bounded(self) -> None:
        metrics = self.analyzer.analyze("Bir iki üç. Dört beş altı yedi sekiz dokuz on. On bir.")
        self.assertGreaterEqual(metrics.burstiness_score, -1.0)
        self.assertLessEqual(metrics.burstiness_score, 1.0)


class LinguisticStructureHeuristicsTests(unittest.TestCase):
    """Tests for non-dogmatic syntactic choking hazards detection."""

    def setUp(self) -> None:
        self.analyzer = AUDIT_MODULE.LinguisticStructureAnalyzer()

    def test_cascading_gerund_chains_detected(self) -> None:
        # 3 consecutive gerunds (toplayıp, inceleyerek, hazırlayarak)
        text = "Verileri toplayıp, modelleri inceleyerek ve raporu hazırlayarak sunum yaptı."
        issues = self.analyzer.analyze(text)
        categories = [i.category for i in issues]
        self.assertIn("cascading_gerund_chain", categories)
        gerund_issue = next(i for i in issues if i.category == "cascading_gerund_chain")
        self.assertGreaterEqual(len(gerund_issue.evidence), 3)

    def test_single_or_double_gerund_not_flagged(self) -> None:
        # Natural prose with 1 gerund should NOT be flagged (zero dogmatic word bans!)
        text = "Koşarak içeri girdi ve haber verdi."
        issues = self.analyzer.analyze(text)
        categories = [i.category for i in issues]
        self.assertNotIn("cascading_gerund_chain", categories)

    def test_excessive_nominalization_detected(self) -> None:
        # High concentration of nominalizations
        text = "Sistemin yapılandırılması, kullanımının yaygınlaştırılması ve sürecin gerçekleştirilmesi hedeflenmektedir."
        issues = self.analyzer.analyze(text)
        categories = [i.category for i in issues]
        self.assertIn("excessive_nominalization", categories)

    def test_periphrastic_passive_stacking_detected(self) -> None:
        # 'tarafından-pasifi'
        text = "Rapor yönetim kurulu tarafından onaylanarak sisteme girilmiştir."
        issues = self.analyzer.analyze(text)
        categories = [i.category for i in issues]
        self.assertIn("periphrastic_passive_stacking", categories)

    def test_active_voice_not_flagged(self) -> None:
        # Direct active human subject
        text = "Yönetim kurulu raporu onayladı ve sisteme girdi."
        issues = self.analyzer.analyze(text)
        categories = [i.category for i in issues]
        self.assertNotIn("periphrastic_passive_stacking", categories)

    def test_run_on_sentence_detected(self) -> None:
        # Extreme sentence with >45 words without breaks
        run_on = " ".join(["kelime"] * 50) + "."
        issues = self.analyzer.analyze(run_on)
        categories = [i.category for i in issues]
        self.assertIn("run_on_sentence", categories)


class CLIExecutionAndExitCodeTests(unittest.TestCase):
    """Functional tests running audit-rewrite.py via subprocess CLI."""

    def test_cli_valid_ledger_exits_0(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_file = Path(temp_dir) / "ledger.md"
            ledger_file.write_text(
                "| Context | Original / Synthetic Sentence | Flaw / Category | Natural Alternative |\n"
                "|:---|:---|:---|:---|\n"
                "| UI | İşlem yapılmıştır. | Edilgen | İşlemi tamamladık. |\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--ledger", str(ledger_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, f"stderr: {result.stderr}")
            self.assertIn("PASS", result.stdout)

    def test_cli_invalid_ledger_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_file = Path(temp_dir) / "invalid_ledger.md"
            ledger_file.write_text(
                "| Context | Original / Synthetic Sentence |\n"
                "|:---|:---|\n"
                "| UI | Eksik tablo |\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--ledger", str(ledger_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("FAIL", result.stdout)

    def test_cli_valid_text_exits_0(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            text_file = Path(temp_dir) / "prose.txt"
            text_file.write_text(
                "Geldik. Kapıyı açtık ve içeriye baktık. Her şey yerli yerindeydi.",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--text", str(text_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, f"stderr: {result.stderr}")
            self.assertIn("PASS", result.stdout)

    def test_cli_strict_mode_fails_on_monotony(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            text_file = Path(temp_dir) / "monotonous.txt"
            text_file.write_text(
                "Sistem verimliliği artırmak amacıyla yapılandırılmıştır. "
                "Kullanıcı deneyimi bu aşamada optimize edilmektedir. "
                "Performans göstergeleri düzenli olarak izlenmektedir. "
                "Veri analitiği sonuçları haftalık paylaşılmaktadır.",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--text", str(text_file), "--strict"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("FAIL", result.stdout)

    def test_cli_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_file = Path(temp_dir) / "ledger.md"
            ledger_file.write_text(
                "| Context | Original / Synthetic Sentence | Flaw / Category | Natural Alternative |\n"
                "|:---|:---|:---|:---|\n"
                "| SaaS | Yapay metin. | Kusur | Doğal alternatif. |\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--ledger", str(ledger_file), "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode)
            data = json.loads(result.stdout)
            self.assertTrue(data["pass"])
            self.assertIn("ledger", data)
            self.assertTrue(data["ledger"]["valid"])
            self.assertEqual(1, data["ledger"]["total_findings"])

    def test_cli_missing_file_exits_2(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--ledger", "non_existent_file.md"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(2, result.returncode)

    def test_cli_no_args_exits_2(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(2, result.returncode)

    def test_cli_positional_arguments_auto_detection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_file = Path(temp_dir) / "my_ledger.md"
            ledger_file.write_text(
                "| Context | Original / Synthetic Sentence | Flaw / Category | Natural Alternative |\n"
                "|:---|:---|:---|:---|\n"
                "| Landing | Yapay cümle örneği | Kopula | Doğal cümle örneği |\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), str(ledger_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, f"stderr: {result.stderr}")
            self.assertIn("PASS", result.stdout)


class ZeroDogmaticBlacklistIntegrityTests(unittest.TestCase):
    """Verifies that audit-rewrite.py strictly contains NO dogmatic token/word blacklists."""

    def test_no_dogmatic_word_blacklists_in_source(self) -> None:
        source_code = SCRIPT_PATH.read_text(encoding="utf-8")
        # Ensure old artifact patterns and banned token lists are completely purged
        banned_stems = [
            "ARTIFACT_PATTERNS",
            "assistant-chatter",
            "model-disclaimer",
            "certainly",
            "of course",
            "işte",
            "bir yapay zek",
        ]
        for stem in banned_stems:
            self.assertNotIn(
                stem.lower(),
                source_code.lower(),
                f"Found dogmatic blacklist residue '{stem}' in audit-rewrite.py",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
