#!/usr/bin/env python3
"""Active Ledger and Cadence/Rhythm Structural Validator.

A non-dogmatic validator for natural writing workflows complying with the
Audit-First Active Ledger architecture (agentskills.io).

Key capabilities:
1. Active Ledger Integrity: Validates that audit ledger files contain properly
   structured findings (Context, Original/Synthetic Sentence, Flaw/Category,
   Natural Alternative) with non-empty values and valid schema.
2. Cadence & Rhythm Metrics: Analyzes prose rhythm through sentence length variance,
   standard deviation, coefficient of variation, short-to-long ratios, and
   normalized burstiness to detect robotic monotony.
3. Linguistic Structure Heuristics: Detects syntactic choking hazards (such as
   cascading chains of 3+ consecutive gerunds like -erek/-arak/-ip, excessive
   nominalization clusters, or passive stacking) without dogmatic word blacklists.
4. Clean CLI & JSON outputs with deterministic exit codes.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class LedgerFinding:
    context: str
    original: str
    flaw: str
    alternative: str
    row_number: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LedgerReport:
    is_valid: bool
    total_findings: int
    findings: list[LedgerFinding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    schema_detected: str = "none"

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.is_valid,
            "total_findings": self.total_findings,
            "schema_detected": self.schema_detected,
            "errors": self.errors,
            "warnings": self.warnings,
            "findings": [asdict(f) for f in self.findings],
        }


@dataclass
class CadenceMetrics:
    sentence_count: int
    word_count: int
    mean_sentence_length: float
    variance: float
    standard_deviation: float
    coefficient_of_variation: float
    burstiness_score: float
    short_sentences_count: int      # <= 8 words
    medium_sentences_count: int     # 9 - 24 words
    long_sentences_count: int       # >= 25 words
    short_to_long_ratio: float
    cadence_monotony: bool
    sentence_lengths: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sentence_count": self.sentence_count,
            "word_count": self.word_count,
            "mean_sentence_length": round(self.mean_sentence_length, 2),
            "variance": round(self.variance, 2),
            "standard_deviation": round(self.standard_deviation, 2),
            "coefficient_of_variation": round(self.coefficient_of_variation, 2),
            "burstiness_score": round(self.burstiness_score, 3),
            "short_sentences_count": self.short_sentences_count,
            "medium_sentences_count": self.medium_sentences_count,
            "long_sentences_count": self.long_sentences_count,
            "short_to_long_ratio": round(self.short_to_long_ratio, 2),
            "cadence_monotony": self.cadence_monotony,
            "sentence_lengths": self.sentence_lengths,
        }


@dataclass
class StructuralIssue:
    category: str
    description: str
    sentence_index: int
    sentence_preview: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "description": self.description,
            "sentence_index": self.sentence_index,
            "sentence_preview": self.sentence_preview,
            "evidence": self.evidence,
        }


@dataclass
class TextAnalysisReport:
    is_valid: bool
    metrics: CadenceMetrics
    issues: list[StructuralIssue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.is_valid,
            "metrics": self.metrics.to_dict(),
            "issues": [i.to_dict() for i in self.issues],
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Tokenization & Sentence Segmentation Helpers
# ---------------------------------------------------------------------------

ABBREVIATIONS = {
    "dr", "prof", "doç", "yrd", "av", "müh", "örn", "vb", "vs", "bkz", "sf", "no",
    "mr", "mrs", "ms", "jr", "sr", "gen", "rep", "sen", "st", "inc", "ltd", "corp",
    "co", "e.g", "i.e", "etc", "vs", "al", "approx", "dept", "est", "min", "max"
}


def split_sentences(text: str) -> list[str]:
    """Segment text into sentences while respecting common abbreviations, numbers, and quotes."""
    if not text or not text.strip():
        return []

    # Clean markdown fences and code blocks from text to avoid false sentence breaks
    clean = re.sub(r"```[\s\S]*?```", " ", text)
    clean = re.sub(r"`[^`\n]+`", " ", clean)

    # Protect common periods in numbers (e.g. 3.14 or 10.000)
    clean = re.sub(r"(?<=\d)\.(?=\d)", "<NUM_DOT>", clean)

    # Protect periods in common abbreviations
    for abbr in ABBREVIATIONS:
        pattern = re.compile(rf"\b({abbr})\.", re.IGNORECASE)
        clean = pattern.sub(r"\1<ABBR_DOT>", clean)

    # Protect ellipsis
    clean = re.sub(r"\.{3}|…", "<ELLIPSIS>", clean)

    # Split on sentence boundaries: punctuation followed by space or end-of-string
    raw_sentences = re.split(r"(?<=[.!?])[\s\r\n]+", clean)

    sentences: list[str] = []
    for s in raw_sentences:
        restored = s.replace("<NUM_DOT>", ".").replace("<ABBR_DOT>", ".").replace("<ELLIPSIS>", "...")
        stripped = restored.strip()
        # Filter out markdown headings, table dividers, or blank fragments
        stripped = re.sub(r"^#+\s*", "", stripped).strip()
        stripped = re.sub(r"^[-*+]\s*", "", stripped).strip()
        if stripped and len(stripped) > 1 and not re.match(r"^\|[-:\s|]+\|$", stripped):
            sentences.append(stripped)

    return sentences


def extract_words(sentence: str) -> list[str]:
    """Extract word tokens from a sentence, stripping formatting and punctuation."""
    # Find all alphanumeric tokens including Turkish diacritics and intra-word apostrophes/hyphens
    tokens = re.findall(r"\b[A-Za-zÇĞİÖŞÜçğıöşü0-9]+(?:[-'][A-Za-zÇĞİÖŞÜçğıöşü0-9]+)*\b", sentence)
    return tokens


# ---------------------------------------------------------------------------
# 1. Active Ledger Integrity Validator
# ---------------------------------------------------------------------------

class LedgerValidator:
    """Validates schema and integrity of Active Ledger audit reports."""

    HEADER_MAP = {
        "context": ("context", "bağlam", "location", "section", "genre", "scope", "konum"),
        "original": (
            "original / synthetic sentence",
            "synthetic / ai sentence",
            "synthetic sentence",
            "original sentence",
            "ai sentence",
            "original / synthetic",
            "original",
            "synthetic",
            "source sentence",
            "source",
            "orijinal cümle",
            "yapay cümle",
            "orijinal / yapay cümle",
            "orijinal",
            "yapay",
        ),
        "flaw": (
            "flaw / category",
            "linguistic flaw / smell",
            "flaw",
            "smell",
            "category",
            "linguistic flaw",
            "defect",
            "kusur",
            "hata",
            "kategori",
            "kusur / kategori",
            "dilbilgisel kusur",
        ),
        "alternative": (
            "natural human alternative",
            "natural alternative",
            "human alternative",
            "proposed alternative",
            "natural rewrite",
            "alternative",
            "rewrite",
            "doğal alternatif",
            "doğal insan alternatifi",
            "alternatif",
            "önerilen alternatif",
        ),
    }

    def __init__(self, min_findings: int = 1):
        self.min_findings = min_findings

    def validate(self, content: str) -> LedgerReport:
        if not content or not content.strip():
            return LedgerReport(
                is_valid=False,
                total_findings=0,
                errors=["Ledger content is empty."],
                schema_detected="none",
            )

        # Check if content is JSON
        content_stripped = content.strip()
        if content_stripped.startswith("{") or content_stripped.startswith("["):
            try:
                data = json.loads(content_stripped)
                return self._validate_json(data)
            except json.JSONDecodeError:
                pass  # Fall back to markdown parser

        # Parse markdown tables or sections
        return self._validate_markdown(content)

    def _validate_json(self, data: Any) -> LedgerReport:
        items = data if isinstance(data, list) else data.get("findings", [])
        if not isinstance(items, list):
            return LedgerReport(
                is_valid=False,
                total_findings=0,
                errors=["JSON ledger root or 'findings' key must be a list."],
                schema_detected="json",
            )

        findings: list[LedgerFinding] = []
        errors: list[str] = []
        warnings: list[str] = []

        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                errors.append(f"Item #{idx} is not a valid dictionary/object.")
                continue

            # Case-insensitive key lookup
            normalized = {k.lower().strip(): v for k, v in item.items()}

            ctx = self._lookup_field(normalized, "context")
            orig = self._lookup_field(normalized, "original")
            flaw = self._lookup_field(normalized, "flaw")
            alt = self._lookup_field(normalized, "alternative")

            if not orig:
                errors.append(f"Item #{idx}: Missing or empty 'original/synthetic sentence'.")
            if not flaw:
                errors.append(f"Item #{idx}: Missing or empty 'flaw/category'.")
            if not alt:
                errors.append(f"Item #{idx}: Missing or empty 'natural alternative'.")

            findings.append(
                LedgerFinding(
                    context=str(ctx or "General").strip(),
                    original=str(orig or "").strip(),
                    flaw=str(flaw or "").strip(),
                    alternative=str(alt or "").strip(),
                    row_number=idx,
                )
            )

        if len(findings) < self.min_findings:
            errors.append(
                f"Ledger contains {len(findings)} findings, but at least {self.min_findings} is required."
            )

        is_valid = len(errors) == 0 and len(findings) >= self.min_findings
        return LedgerReport(
            is_valid=is_valid,
            total_findings=len(findings),
            findings=findings,
            errors=errors,
            warnings=warnings,
            schema_detected="json",
        )

    def _validate_markdown(self, content: str) -> LedgerReport:
        lines = content.splitlines()
        findings: list[LedgerFinding] = []
        errors: list[str] = []
        warnings: list[str] = []

        # Look for markdown tables
        table_rows: list[tuple[int, list[str]]] = []
        header_index: int | None = None
        col_mapping: dict[str, int] = {}

        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line.startswith("|") or not line.endswith("|"):
                continue

            # Split cells
            cells = [c.strip() for c in line.strip("|").split("|")]
            # Ignore markdown separator line e.g. |---|:---|
            if all(re.match(r"^:?-+:?$", cell) for cell in cells if cell):
                continue

            # Detect header
            if not col_mapping:
                mapping = self._detect_columns(cells)
                if mapping and len(mapping) >= 3:  # Found at least original, flaw, alt
                    col_mapping = mapping
                    header_index = line_no
                    continue

            if col_mapping:
                table_rows.append((line_no, cells))

        if col_mapping:
            # Table schema detected
            missing_cols = []
            for req in ("original", "flaw", "alternative"):
                if req not in col_mapping:
                    missing_cols.append(req)

            if missing_cols:
                errors.append(
                    f"Markdown table at line {header_index} is missing required columns: {', '.join(missing_cols)}."
                )

            for row_no, cells in table_rows:
                def get_cell(col_name: str) -> str:
                    idx = col_mapping.get(col_name)
                    if idx is not None and idx < len(cells):
                        return cells[idx].strip()
                    return ""

                ctx = get_cell("context") or "General"
                orig = get_cell("original")
                flaw = get_cell("flaw")
                alt = get_cell("alternative")

                # Check if whole row is empty
                if not any([orig, flaw, alt]):
                    continue

                if not orig:
                    errors.append(f"Row {row_no}: Original/synthetic sentence cell is empty.")
                if not flaw:
                    errors.append(f"Row {row_no}: Flaw/category cell is empty.")
                if not alt:
                    errors.append(f"Row {row_no}: Natural alternative cell is empty.")

                findings.append(
                    LedgerFinding(
                        context=ctx,
                        original=orig,
                        flaw=flaw,
                        alternative=alt,
                        row_number=row_no,
                    )
                )

            if len(findings) < self.min_findings:
                errors.append(
                    f"Ledger contains {len(findings)} findings, but at least {self.min_findings} is required."
                )

            is_valid = len(errors) == 0 and len(findings) >= self.min_findings
            return LedgerReport(
                is_valid=is_valid,
                total_findings=len(findings),
                findings=findings,
                errors=errors,
                warnings=warnings,
                schema_detected="markdown_table",
            )

        # Fallback: Check for bulleted/section structured format
        structured_findings = self._parse_structured_markdown_sections(lines)
        if structured_findings:
            if len(structured_findings) < self.min_findings:
                errors.append(
                    f"Ledger contains {len(structured_findings)} structured findings, but at least {self.min_findings} is required."
                )
            is_valid = len(errors) == 0 and len(structured_findings) >= self.min_findings
            return LedgerReport(
                is_valid=is_valid,
                total_findings=len(structured_findings),
                findings=structured_findings,
                errors=errors,
                warnings=warnings,
                schema_detected="markdown_sections",
            )

        # Neither found
        return LedgerReport(
            is_valid=False,
            total_findings=0,
            errors=[
                "No valid Active Ledger structure detected. Must contain a Markdown table with columns "
                "(Context, Original / Synthetic Sentence, Flaw / Category, Natural Alternative) or structured entries."
            ],
            schema_detected="none",
        )

    def _detect_columns(self, cells: list[str]) -> dict[str, int]:
        mapping: dict[str, int] = {}
        for idx, cell in enumerate(cells):
            cleaned = re.sub(r"[*_`]", "", cell).strip().lower()
            for field_name, aliases in self.HEADER_MAP.items():
                if field_name not in mapping and any(cleaned == a or cleaned.startswith(a) for a in aliases):
                    mapping[field_name] = idx
                    break
        return mapping

    def _lookup_field(self, data: dict[str, Any], field_name: str) -> Any:
        aliases = self.HEADER_MAP.get(field_name, ())
        for key in data:
            cleaned = key.lower().strip()
            if any(cleaned == a or cleaned.startswith(a) for a in aliases):
                return data[key]
        return None

    def _parse_structured_markdown_sections(self, lines: list[str]) -> list[LedgerFinding]:
        findings: list[LedgerFinding] = []
        current: dict[str, str] = {}
        row_no = 0

        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            # Match patterns like: - **Context**: SaaS Hero or - Original: ...
            match = re.match(r"^[-*+]?\s*\**([A-Za-zÇĞİÖŞÜçğıöşü\s/]+)\**\s*:\s*(.+)$", line)
            if match:
                key, val = match.group(1).lower().strip(), match.group(2).strip()
                for target_field, aliases in self.HEADER_MAP.items():
                    if any(key == a or key.startswith(a) for a in aliases):
                        current[target_field] = val
                        break

            # If we accumulated all required fields, save finding
            if "original" in current and "flaw" in current and "alternative" in current:
                findings.append(
                    LedgerFinding(
                        context=current.get("context", "General"),
                        original=current["original"],
                        flaw=current["flaw"],
                        alternative=current["alternative"],
                        row_number=line_no,
                    )
                )
                current = {}

        return findings


# ---------------------------------------------------------------------------
# 2. Cadence & Rhythm Metrics Analyzer
# ---------------------------------------------------------------------------

class CadenceAnalyzer:
    """Computes prose rhythm, sentence length variance, and burstiness metrics."""

    def __init__(self, monotony_threshold_stddev: float = 2.5, burstiness_floor: float = -0.75):
        self.monotony_threshold_stddev = monotony_threshold_stddev
        self.burstiness_floor = burstiness_floor

    def analyze(self, text: str) -> CadenceMetrics:
        sentences = split_sentences(text)
        if not sentences:
            return CadenceMetrics(
                sentence_count=0,
                word_count=0,
                mean_sentence_length=0.0,
                variance=0.0,
                standard_deviation=0.0,
                coefficient_of_variation=0.0,
                burstiness_score=0.0,
                short_sentences_count=0,
                medium_sentences_count=0,
                long_sentences_count=0,
                short_to_long_ratio=0.0,
                cadence_monotony=False,
                sentence_lengths=[],
            )

        lengths: list[int] = []
        short_count = 0
        medium_count = 0
        long_count = 0

        for s in sentences:
            w_count = len(extract_words(s))
            lengths.append(w_count)
            if w_count <= 8:
                short_count += 1
            elif w_count <= 24:
                medium_count += 1
            else:
                long_count += 1

        total_sentences = len(lengths)
        total_words = sum(lengths)
        mean_length = total_words / total_sentences if total_sentences > 0 else 0.0

        # Population variance
        if total_sentences > 1:
            variance = sum((l - mean_length) ** 2 for l in lengths) / total_sentences
            std_dev = math.sqrt(variance)
        else:
            variance = 0.0
            std_dev = 0.0

        cv = (std_dev / mean_length) if mean_length > 0 else 0.0

        # Goh-Barabási normalized burstiness parameter: B = (sigma - mu) / (sigma + mu)
        # Ranging from -1 (periodic/monotonous) to +1 (extremely bursty)
        denominator = std_dev + mean_length
        if denominator > 0:
            burstiness = (std_dev - mean_length) / denominator
        else:
            burstiness = 0.0

        ratio = (short_count / long_count) if long_count > 0 else float(short_count)

        # Monotony detection:
        # If there are at least 4 sentences and either:
        # - std_dev is extremely low (< monotony_threshold_stddev)
        # - burstiness is deeply negative (< burstiness_floor)
        # - or 4+ consecutive sentences have length difference <= 2
        consecutive_monotony = False
        consecutive_count = 1
        for i in range(1, len(lengths)):
            if abs(lengths[i] - lengths[i - 1]) <= 2:
                consecutive_count += 1
                if consecutive_count >= 4:
                    consecutive_monotony = True
                    break
            else:
                consecutive_count = 1

        is_monotonous = False
        if total_sentences >= 4:
            if (std_dev < self.monotony_threshold_stddev and cv < 0.22) or (
                burstiness < self.burstiness_floor and consecutive_monotony
            ):
                is_monotonous = True

        return CadenceMetrics(
            sentence_count=total_sentences,
            word_count=total_words,
            mean_sentence_length=mean_length,
            variance=variance,
            standard_deviation=std_dev,
            coefficient_of_variation=cv,
            burstiness_score=burstiness,
            short_sentences_count=short_count,
            medium_sentences_count=medium_count,
            long_sentences_count=long_count,
            short_to_long_ratio=ratio,
            cadence_monotony=is_monotonous,
            sentence_lengths=lengths,
        )


# ---------------------------------------------------------------------------
# 3. Linguistic Structure & Syntactic Choking Hazard Analyzer
# ---------------------------------------------------------------------------

class LinguisticStructureAnalyzer:
    """Analyzes non-dogmatic syntactic choking hazards:
    - Cascading gerund chains (ulaç yığılması: 3+ consecutive gerunds like -erek/-arak/-ip)
    - Excessive Latinate or Turkish nominalization density
    - Passive voice stacking with periphrastic agents ('tarafından-pasifi')
    - Run-on sentences lacking conversational breathing
    """

    # Turkish verbal adverb / gerund suffix patterns
    TURKISH_GERUND_RE = re.compile(
        r"\b\w{3,}(?:erek|arak|ip|ıp|up|üp|ince|ınca|ünce|unce|dıkça|dikçe|dukça|dükçe|tıkça|tikçe|tukça|tükçe|meksizin|maksızın)\b",
        re.IGNORECASE,
    )

    # Exclude common non-gerund false positives ending in similar letters
    GERUND_EXCLUSIONS = {
        "takip", "nasip", "rakip", "sahip", "katip", "tahrip", "tertip", "çorap",
        "klip", "grip", "hasip", "habip", "mucip", "talip", "tezkip"
    }

    # Nominalization suffixes (Turkish: -ma/-me, -mak/-mek, -ış/-iş/-uş/-üş, -ım/-im/-um/-üm, -laştırma/-leştirme)
    # and English: -tion, -sion, -ment, -ance, -ence, -ity
    NOMINALIZATION_RE = re.compile(
        r"\b\w{3,}(?:(?:ma|me|mak|mek|ış|iş|uş|üş|ım|im|um|üm|laştırma|leştirme|landırılma|lendirilme)(?:lar|ler)?(?:[sny]?[aıieouü])*(?:n[ıiuü]n|d[ae]|d[ae]n)?|(?:tion|sion|ment|ance|ence|ity)(?:s|al|ally)?)\b",
        re.IGNORECASE,
    )

    # Passive agent markers in Turkish that lead to translationese
    PERIPHRASTIC_AGENT_RE = re.compile(
        r"\b(?:tarafından|vasıtasıyla|aracılığıyla|marifetiyle)\b",
        re.IGNORECASE,
    )

    # Passive verb endings in Turkish (-ıl/-il/-ul/-ül, -ın/-in/-un/-ün, -n)
    TURKISH_PASSIVE_VERB_RE = re.compile(
        r"\b\w{3,}(?:ıl|il|ul|ül|ın|in|un|ün|n)(?:mış|miş|muş|müş|mektedir|maktadır|dı|di|du|dü|acak|ecek|ır|ir|ur|ür)(?:tir|dir|dur|dür|ler|lar)?\b",
        re.IGNORECASE,
    )

    def analyze(self, text: str) -> list[StructuralIssue]:
        sentences = split_sentences(text)
        issues: list[StructuralIssue] = []

        for idx, sentence in enumerate(sentences, start=1):
            words = extract_words(sentence)
            w_count = len(words)

            # 1. Cascading gerund chains (3+ gerunds in a single sentence)
            gerund_matches = [
                m.group(0) for m in self.TURKISH_GERUND_RE.finditer(sentence)
                if m.group(0).lower() not in self.GERUND_EXCLUSIONS
            ]
            if len(gerund_matches) >= 3:
                issues.append(
                    StructuralIssue(
                        category="cascading_gerund_chain",
                        description=(
                            f"Cascading chain of {len(gerund_matches)} consecutive gerunds (ulaç yığılması) "
                            f"creates a syntactic choking hazard. Break into independent clauses with finite verbs."
                        ),
                        sentence_index=idx,
                        sentence_preview=sentence[:80] + ("..." if len(sentence) > 80 else ""),
                        evidence=gerund_matches,
                    )
                )

            # 2. Excessive nominalization density (>= 4 nominalizations in a single sentence)
            nominal_matches = [m.group(0) for m in self.NOMINALIZATION_RE.finditer(sentence)]
            if len(nominal_matches) >= 4 and (len(nominal_matches) / max(1, w_count)) >= 0.25:
                issues.append(
                    StructuralIssue(
                        category="excessive_nominalization",
                        description=(
                            f"High nominalization density ({len(nominal_matches)} abstract nouns) "
                            f"leads to bureaucratic opacity. Replace noun clusters with active verbs."
                        ),
                        sentence_index=idx,
                        sentence_preview=sentence[:80] + ("..." if len(sentence) > 80 else ""),
                        evidence=nominal_matches,
                    )
                )

            # 3. Passive stacking with periphrastic agents (tarafından-pasifleri)
            agent_matches = [m.group(0) for m in self.PERIPHRASTIC_AGENT_RE.finditer(sentence)]
            passive_matches = [m.group(0) for m in self.TURKISH_PASSIVE_VERB_RE.finditer(sentence)]
            if agent_matches and passive_matches:
                issues.append(
                    StructuralIssue(
                        category="periphrastic_passive_stacking",
                        description=(
                            "Passive construction coupled with periphrastic agent ('tarafından-pasifi') "
                            "signals translationese. Reconstruct with active voice and explicit human subject."
                        ),
                        sentence_index=idx,
                        sentence_preview=sentence[:80] + ("..." if len(sentence) > 80 else ""),
                        evidence=agent_matches + passive_matches,
                    )
                )

            # 4. Severe run-on sentence without syntactic relief (> 45 words)
            if w_count >= 45 and ";" not in sentence and ":" not in sentence:
                issues.append(
                    StructuralIssue(
                        category="run_on_sentence",
                        description=(
                            f"Extreme sentence length ({w_count} words) without structural pause or semicolon. "
                            f"Split into varied, breathable sentences."
                        ),
                        sentence_index=idx,
                        sentence_preview=sentence[:80] + ("..." if len(sentence) > 80 else ""),
                        evidence=[f"{w_count} words"],
                    )
                )

        return issues


# ---------------------------------------------------------------------------
# High-Level Audit Pipeline
# ---------------------------------------------------------------------------

def audit(
    ledger_text: str | None = None,
    prose_text: str | None = None,
    min_findings: int = 1,
    strict: bool = False,
) -> dict[str, Any]:
    """Execute end-to-end audit across active ledger and/or text cadence."""
    results: dict[str, Any] = {
        "pass": True,
        "ledger": None,
        "text_analysis": None,
        "summary": [],
    }

    # Validate ledger if provided
    if ledger_text is not None:
        validator = LedgerValidator(min_findings=min_findings)
        ledger_report = validator.validate(ledger_text)
        results["ledger"] = ledger_report.to_dict()
        if not ledger_report.is_valid:
            results["pass"] = False
            results["summary"].append(f"Ledger validation failed: {'; '.join(ledger_report.errors)}")
        else:
            results["summary"].append(
                f"Ledger valid: {ledger_report.total_findings} structured findings verified."
            )

    # Analyze prose text if provided
    if prose_text is not None:
        cadence_analyzer = CadenceAnalyzer()
        structure_analyzer = LinguisticStructureAnalyzer()

        metrics = cadence_analyzer.analyze(prose_text)
        issues = structure_analyzer.analyze(prose_text)

        text_valid = True
        warnings: list[str] = []

        if metrics.cadence_monotony:
            msg = (
                f"Cadence monotony detected (std_dev={round(metrics.standard_deviation, 2)}, "
                f"burstiness={round(metrics.burstiness_score, 2)}). Text exhibits robotic sentence length uniformity."
            )
            warnings.append(msg)
            if strict:
                text_valid = False

        if any(i.category == "cascading_gerund_chain" for i in issues):
            warnings.append("Cascading gerund chains detected (ulaç yığılması).")
            if strict:
                text_valid = False

        if strict and issues:
            text_valid = False

        text_report = TextAnalysisReport(
            is_valid=text_valid,
            metrics=metrics,
            issues=issues,
            warnings=warnings,
        )
        results["text_analysis"] = text_report.to_dict()

        if not text_valid:
            results["pass"] = False
            results["summary"].append("Prose rhythm / structural heuristic validation failed.")
        else:
            results["summary"].append(
                f"Prose analysis passed: {metrics.sentence_count} sentences, "
                f"burstiness={round(metrics.burstiness_score, 2)}, {len(issues)} structural suggestions."
            )

    return results


# ---------------------------------------------------------------------------
# CLI Interface & Formatting
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="audit-rewrite.py",
        description="Active Ledger and Text Cadence/Rhythm Structural Validator",
    )
    parser.add_argument(
        "--ledger", "-l",
        type=Path,
        metavar="PATH",
        help="Path to markdown or JSON active ledger file to validate",
    )
    parser.add_argument(
        "--text", "-t",
        type=Path,
        metavar="PATH",
        help="Path to prose text file to analyze for cadence, burstiness, and syntactic hazards",
    )
    parser.add_argument(
        "--min-findings",
        type=int,
        default=1,
        help="Minimum required findings in active ledger (default: 1)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: fail on cadence monotony or structural choking hazards",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Emit structured JSON output",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed findings and sentence-by-sentence metrics",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        metavar="FILE",
        help="Positional file path(s) to ledger or text file(s)",
    )
    return parser.parse_args(argv)


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as err:
        raise RuntimeError(f"Cannot read '{path}': {err}") from err


def render_human_report(report: dict[str, Any], verbose: bool = False) -> str:
    lines: list[str] = []
    overall_pass = report.get("pass", False)
    status_header = "PASS: Audit-First Validation Successful" if overall_pass else "FAIL: Validation Violations Detected"
    lines.append(f"=== {status_header} ===\n")

    for summary_item in report.get("summary", []):
        lines.append(f"• {summary_item}")
    lines.append("")

    # Ledger Section
    ledger = report.get("ledger")
    if ledger:
        lines.append("--- Active Ledger Report ---")
        lines.append(f"Status: {'VALID' if ledger['valid'] else 'INVALID'}")
        lines.append(f"Schema Detected: {ledger['schema_detected']}")
        lines.append(f"Total Findings: {ledger['total_findings']}")
        if ledger.get("errors"):
            lines.append("Errors:")
            for err in ledger["errors"]:
                lines.append(f"  ✖ {err}")
        if ledger.get("warnings"):
            lines.append("Warnings:")
            for warn in ledger["warnings"]:
                lines.append(f"  ⚠ {warn}")

        if verbose and ledger.get("findings"):
            lines.append("\nSample Findings:")
            for f in ledger["findings"][:5]:
                lines.append(f"  - [{f.get('context', 'General')}] {f.get('original')[:60]}...")
                lines.append(f"    Flaw: {f.get('flaw')}")
                lines.append(f"    Alternative: {f.get('alternative')[:60]}...")
        lines.append("")

    # Text Analysis Section
    text_data = report.get("text_analysis")
    if text_data:
        m = text_data.get("metrics", {})
        lines.append("--- Cadence & Rhythm Metrics ---")
        lines.append(f"Sentences: {m.get('sentence_count')}, Words: {m.get('word_count')}")
        lines.append(f"Mean Sentence Length: {m.get('mean_sentence_length')} words")
        lines.append(f"Std Deviation: {m.get('standard_deviation')}, Variance: {m.get('variance')}")
        lines.append(f"Burstiness Score: {m.get('burstiness_score')} (range: -1.0 to +1.0)")
        lines.append(f"Sentence Distribution: Short={m.get('short_sentences_count')}, "
                     f"Medium={m.get('medium_sentences_count')}, Long={m.get('long_sentences_count')}")
        lines.append(f"Cadence Monotony: {'YES (Robotic uniformity)' if m.get('cadence_monotony') else 'NO (Dynamic human rhythm)'}")

        issues = text_data.get("issues", [])
        if issues:
            lines.append(f"\nSyntactic Choking Hazards & Heuristics ({len(issues)} detected):")
            for issue in issues:
                lines.append(f"  ⚠ [{issue.get('category')}] Sentence #{issue.get('sentence_index')}: {issue.get('description')}")
                if verbose and issue.get("evidence"):
                    lines.append(f"    Evidence: {', '.join(issue['evidence'])}")
                    lines.append(f"    Preview: \"{issue.get('sentence_preview')}\"")

        if verbose and m.get("sentence_lengths"):
            lines.append(f"\nSentence Lengths Sequence: {m.get('sentence_lengths')}")
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    ledger_path = args.ledger
    text_path = args.text

    # Handle positional paths if flags were omitted
    if not ledger_path and not text_path and args.paths:
        first_path = args.paths[0]
        try:
            content = read_file(first_path)
            # Auto-detect whether first file is a ledger or text
            if ("|" in content and ("original" in content.lower() or "flaw" in content.lower() or "bağlam" in content.lower())) or (
                content.strip().startswith("{") and "findings" in content
            ):
                ledger_path = first_path
                if len(args.paths) > 1:
                    text_path = args.paths[1]
            else:
                text_path = first_path
                if len(args.paths) > 1:
                    ledger_path = args.paths[1]
        except RuntimeError as err:
            print(f"Error: {err}", file=sys.stderr)
            return 2

    if not ledger_path and not text_path:
        print("Error: Must specify at least one file to validate via --ledger or --text (or positional arguments).", file=sys.stderr)
        return 2

    ledger_content = None
    text_content = None

    try:
        if ledger_path:
            ledger_content = read_file(ledger_path)
        if text_path:
            text_content = read_file(text_path)
    except RuntimeError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2

    report = audit(
        ledger_text=ledger_content,
        prose_text=text_content,
        min_findings=args.min_findings,
        strict=args.strict,
    )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_human_report(report, verbose=args.verbose))

    return 0 if report.get("pass", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
