#!/usr/bin/env python3
"""Audit deterministic token and structure preservation across a rewrite.

This is deliberately not a parser or semantic equivalence checker. It inventories
exact content that editorial rewrites commonly damage and reports newly introduced
production residue. Use the consuming project's native parser, build, renderer, and
human review in addition to this audit.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


URL_RE = re.compile(r"(?i)\b(?:https?://|mailto:)[^\s<>\]\[\"']+[^\s<>\]\[\"'.,;:!?)]")
EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[a-z0-9.-]+\.[a-z]{2,}(?![\w.-])")
FENCE_OPEN_RE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})([^\r\n]*)")
INLINE_CODE_RE = re.compile(r"(?s)(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
REFERENCE_DEFINITION_RE = re.compile(
    r"^[ ]{0,3}\[([^\]\n]+)\]:[ \t]*(?:<([^>\n]*)>|([^\s]+))(?:[ \t]+.*)?$"
)
FOOTNOTE_DEFINITION_RE = re.compile(r"^[ ]{0,3}\[\^([^\]\n]+)\]:")
BRACKET_TOKEN_RE = re.compile(r"!?\[([^\]\n]+)\]")
FOOTNOTE_RE = re.compile(r"\[\^([^\]\n]+)\]")
INLINE_LINK_START_RE = re.compile(r"!?\[[^\]\n]*\]\(")
DATE_RES = (
    re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)"),
    re.compile(r"(?<!\d)\d{1,2}[./-]\d{1,2}[./-]\d{2,4}(?!\d)"),
    re.compile(
        r"(?i)\b(?:\d{1,2}\s+)?(?:January|February|March|April|May|June|July|August|September|October|"
        r"November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+"
        r"(?:\d{1,2},?\s+)?\d{4}\b"
    ),
)
CURRENCY_TOKEN = (
    r"(?:USD|EUR|GBP|JPY|CNY|RMB|TRY|CAD|AUD|NZD|CHF|INR|BRL|MXN|PLN|SEK|NOK|DKK|CZK|HUF|RON|"
    r"AED|SAR|QAR|KWD|BHD|OMR|JOD|EGP|MAD|ZAR|KRW|SGD|HKD|TWD|THB|IDR|MYR|PHP|VND|NGN|KES|"
    r"zł|kr|Kč|Ft|lei|лв|د\.إ|ر\.س|ر\.ق|د\.ك|د\.ب|ر\.ع|د\.ا|ج\.م|د\.م\.|"
    r"[$€£¥₹₺₽₩₪₫₴₦₱฿₲₵₡₭₮₨₸₼₾₿])"
)
UNIT_TOKEN = (
    r"(?:%|٪|percent|percentage[ \t]+points?|ms|sec(?:onds?)?|min(?:utes?)?|h(?:ours?)?|"
    r"B|KB|MB|GB|TB|KiB|MiB|GiB|mm|cm|m|km|in|ft|yd|mi|mg|g|kg|lb|oz|°[CF]|kWh|W|kW)"
)
NUMBER_RE = re.compile(
    rf"(?ix)(?<![\w])(?:{CURRENCY_TOKEN}[ \t\u00a0\u202f]*)?[+-]?\d+"
    rf"(?:[.,٬٫'’\u00a0\u202f]\d+)*(?:[ \t\u00a0\u202f]*(?:{CURRENCY_TOKEN}|{UNIT_TOKEN}))?(?![\w])"
)
TAG_RE = re.compile(r"(?s)<\s*(/?)\s*([A-Za-z][\w.:-]*)(\s[^<>]*?)?\s*(/?)>")
ATTR_RE = re.compile(
    r"(?s)([:@A-Za-z_][\w:.-]*)(?:\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|"
    r"(\{\{.*?\}\}|\{(?:[^{}]|\{[^{}]*\})*\})|([^\s\"'=<>`]+)))?"
)
HTML_ENTITY_RE = re.compile(r"&(?:#[xX][0-9A-Fa-f]+|#\d+|[A-Za-z][A-Za-z0-9]+);")
RAW_TEXT_OPEN_RE = re.compile(r"(?is)<(script|style|textarea)(?=[\s>])[^>]*>")
FRONTMATTER_MAPPING_RE = re.compile(
    r"^([ \t]*)(-\s+)?([A-Za-z_][\w.-]*):(?:[ \t]*(.*?))[ \t]*(?:\r?\n)?$"
)
BLOCK_SCALAR_RE = re.compile(r"^[>|](?:[+-]?\d?|\d?[+-]?)(?:\s+#.*)?$")
MDX_ESM_START_RE = re.compile(
    r"^[ ]{0,3}(?:import(?:\s|['\"])|export\s+(?:default\b|declare\b|const\b|let\b|var\b|"
    r"function\b|class\b|interface\b|type\b|enum\b|namespace\b|\{|\*))"
)
COPY_FRONTMATTER_FIELDS = {
    "title",
    "description",
    "summary",
    "excerpt",
    "seotitle",
    "seodescription",
    "metatitle",
    "metadescription",
    "ogtitle",
    "ogdescription",
}
COPY_ATTRIBUTES = {"alt", "title", "placeholder", "aria-label", "aria-description"}

ARTIFACT_PATTERNS = {
    "placeholder": re.compile(
        r"(?im)(?:\b(?:TODO|TBD|FIXME)\b|\[(?:insert|add|replace|source needed)[^\]\n]*\]|\blorem ipsum\b)"
    ),
    "assistant-chatter": re.compile(
        r"(?im)^\s*(?:certainly|of course|i hope this helps|"
        r"here(?:'s| is) (?:the|a|your) (?:revised|rewritten|polished|humanized) (?:version|text|copy)|"
        r"işte (?:yeniden yazılmış|düzenlenmiş|gözden geçirilmiş) (?:sürüm|metin)|"
        r"(?:aquí|acá) (?:tienes|está) (?:la|el) (?:versión|texto) (?:revisad[oa]|reescrit[oa])|"
        r"voici (?:la|le) (?:version|texte) (?:révisé[e]?|réécrit[e]?)|"
        r"hier ist (?:die|der) (?:überarbeitete|umgeschriebene) (?:fassung|text)|"
        r"aqui (?:está|tem) (?:a|o) (?:versão|texto) (?:revisad[oa]|reescrit[oa])|"
        r"ecco (?:la|il) (?:versione|testo) (?:rivist[oa]|riscritt[oa]))[.!:]?\s*$"
    ),
    "model-disclaimer": re.compile(
        r"(?i)(?:as an? (?:AI|artificial intelligence) language model|"
        r"bir yapay zek[âa] dil modeli olarak|como modelo de lenguaje (?:de IA|de inteligencia artificial)|"
        r"en tant que modèle de langage (?:d['’]IA|d['’]intelligence artificielle)|"
        r"als (?:KI|AI)[- ]Sprachmodell|como modelo de linguagem (?:de IA|de inteligência artificial)|"
        r"in quanto modello linguistico (?:di IA|di intelligenza artificiale)|"
        r"作为(?:一个)?人工智能语言模型|AI言語モデルとして|인공지능 언어 모델로서|بصفتي نموذج(?:ًا)? لغوي(?:ًا)? للذكاء الاصطناعي)"
    ),
    "prompt-residue": re.compile(
        r"(?im)(?:^\s*###?\s*(?:instruction|instructions|system prompt|prompt)\s*$|"
        r"\bignore (?:all )?(?:the )?previous instructions\b|<\/?system>|\[/?INST\])"
    ),
    "citation-residue": re.compile(r"(?:cite(?:turn\d+(?:search|view)\d+)+|【\d+(?:†[^】]+)?】)"),
}


@dataclass
class Difference:
    category: str
    missing: list[str]
    added: list[str]


def counter(values: Iterable[str]) -> collections.Counter[str]:
    return collections.Counter(value for value in values if value != "")


def expanded(counter_value: collections.Counter[str]) -> list[str]:
    result: list[str] = []
    for value in sorted(counter_value):
        result.extend([value] * counter_value[value])
    return result


def compare(category: str, original: Iterable[str], revised: Iterable[str]) -> Difference | None:
    before = counter(original)
    after = counter(revised)
    missing = before - after
    added = after - before
    if not missing and not added:
        return None
    return Difference(category, expanded(missing), expanded(added))


def indentation(value: str) -> int:
    prefix = value[: len(value) - len(value.lstrip(" \t"))]
    return len(prefix.expandtabs(4))


def mask_spans(text: str, spans: Iterable[tuple[int, int]]) -> str:
    characters = list(text)
    for start, end in spans:
        for index in range(max(0, start), min(len(characters), end)):
            if characters[index] not in "\r\n":
                characters[index] = " "
    return "".join(characters)


def extract_frontmatter(text: str) -> tuple[str, list[str], list[str], list[str]]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text, [], [], []
    closing = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if closing is None:
        return text, ["<unclosed-frontmatter>"], ["<unclosed-frontmatter>"], ["unclosed-frontmatter:---"]

    keys: list[str] = []
    protected_values: list[str] = []
    stack: list[tuple[int, str]] = []
    copy_block_indent: int | None = None
    for line in lines[1:closing]:
        stripped = line.strip()
        line_indent = indentation(line)
        if copy_block_indent is not None:
            if not stripped or line_indent > copy_block_indent:
                continue
            copy_block_indent = None

        match = FRONTMATTER_MAPPING_RE.match(line)
        if match:
            leading, list_marker, key, raw_value = match.groups()
            key_indent = indentation(leading) + (2 if list_marker else 0)
            while stack and stack[-1][0] >= key_indent:
                stack.pop()
            path = ".".join([item[1] for item in stack] + [key])
            keys.append(path)
            value = (raw_value or "").strip()
            copy_field = key.lower().replace("-", "").replace("_", "") in COPY_FRONTMATTER_FIELDS
            if not value:
                stack.append((key_indent, key))
            elif copy_field:
                if BLOCK_SCALAR_RE.match(value):
                    protected_values.append(f"{path}=<copy-block:{value.split()[0]}>")
                    copy_block_indent = key_indent
            else:
                protected_values.append(f"{path}={value}")
            continue

        if stripped and not stripped.startswith("#"):
            path = ".".join(item[1] for item in stack) or "<root>"
            protected_values.append(f"{path}::{stripped}")

    return "".join(lines[closing + 1 :]), keys, protected_values, []


def extract_code(text: str) -> tuple[list[str], list[str], list[str], str, list[str]]:
    fences: list[str] = []
    indented: list[str] = []
    artifacts: list[str] = []
    lines = text.splitlines(keepends=True)
    occupied = [False] * len(lines)

    index = 0
    while index < len(lines):
        opening = FENCE_OPEN_RE.match(lines[index])
        if not opening or (opening.group(1).startswith("`") and "`" in opening.group(2)):
            index += 1
            continue
        marker = opening.group(1)[0]
        minimum = len(opening.group(1))
        closing_re = re.compile(rf"^[ ]{{0,3}}{re.escape(marker)}{{{minimum},}}[ \t]*(?:\r?\n)?$")
        end = index + 1
        while end < len(lines) and not closing_re.match(lines[end]):
            end += 1
        if end == len(lines):
            fences.append("".join(lines[index:]))
            artifacts.append(f"unclosed-fence:{lines[index].strip()}")
            for occupied_index in range(index, len(lines)):
                occupied[occupied_index] = True
            break
        fences.append("".join(lines[index : end + 1]))
        for occupied_index in range(index, end + 1):
            occupied[occupied_index] = True
        index = end + 1

    index = 0
    while index < len(lines):
        if occupied[index] or not re.match(r"^(?: {4}|\t)", lines[index]):
            index += 1
            continue
        end = index + 1
        while end < len(lines) and not occupied[end] and (
            not lines[end].strip() or re.match(r"^(?: {4}|\t)", lines[end])
        ):
            end += 1
        while end > index and not lines[end - 1].strip():
            end -= 1
        indented.append("".join(lines[index:end]))
        for occupied_index in range(index, end):
            occupied[occupied_index] = True
        index = max(end, index + 1)

    masked_lines: list[str] = []
    for line, is_occupied in zip(lines, occupied):
        if not is_occupied:
            masked_lines.append(line)
            continue
        newline = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
        masked_lines.append(" " * (len(line) - len(newline)) + newline)
    without_blocks = "".join(masked_lines)
    inline: list[str] = []

    def mask_inline(match: re.Match[str]) -> str:
        inline.append(match.group(0))
        return " " * len(match.group(0))

    prose = INLINE_CODE_RE.sub(mask_inline, without_blocks)
    return fences, indented, inline, prose, artifacts


def extract_mdx_esm(text: str) -> tuple[list[str], str]:
    lines = text.splitlines(keepends=True)
    occupied = [False] * len(lines)
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        if not MDX_ESM_START_RE.match(lines[index]):
            index += 1
            continue
        end = index + 1
        while end < len(lines) and lines[end].strip():
            end += 1
        blocks.append("".join(lines[index:end]))
        for occupied_index in range(index, end):
            occupied[occupied_index] = True
        index = end
    spans: list[tuple[int, int]] = []
    offset = 0
    for line, is_occupied in zip(lines, occupied):
        if is_occupied:
            spans.append((offset, offset + len(line)))
        offset += len(line)
    return blocks, mask_spans(text, spans)


def extract_html_special(text: str) -> tuple[list[str], list[str], list[str], str, list[str]]:
    comments: list[str] = []
    raw_text: list[str] = []
    artifacts: list[str] = []
    spans: list[tuple[int, int]] = []
    comment_cursor = 0
    while True:
        comment_start = text.find("<!--", comment_cursor)
        if comment_start == -1:
            break
        comment_end = text.find("-->", comment_start + 4)
        if comment_end == -1:
            artifacts.append("unclosed-html-comment:<!--")
            spans.append((comment_start, len(text)))
            break
        comment_end += 3
        comments.append(text[comment_start:comment_end])
        spans.append((comment_start, comment_end))
        comment_cursor = comment_end

    comment_masked = mask_spans(text, spans)
    raw_cursor = 0
    while True:
        opening = RAW_TEXT_OPEN_RE.search(comment_masked, raw_cursor)
        if opening is None:
            break
        tag = opening.group(1).lower()
        closing_re = re.compile(rf"(?is)</{re.escape(tag)}\s*>")
        closing = closing_re.search(comment_masked, opening.end())
        if closing is None:
            body_end = len(text)
            artifacts.append(f"unclosed-html-raw-text:{tag}")
            raw_cursor = len(text)
        else:
            body_end = closing.start()
            raw_cursor = closing.end()
        raw_text.append(f"{tag}:{text[opening.end():body_end]}")
        spans.append((opening.end(), body_end))

    entities = [match.group(0) for match in HTML_ENTITY_RE.finditer(text)]
    return comments, entities, raw_text, mask_spans(text, spans), artifacts


def scan_balanced_braces(text: str, brace_index: int) -> int | None:
    depth = 0
    quote: str | None = None
    escaped = False
    index = brace_index
    while index < len(text):
        character = text[index]
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif character in "'\"`":
            quote = character
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return None


def extract_expressions(text: str) -> tuple[list[str], list[str], str, list[str]]:
    directives: list[str] = []
    brace_expressions: list[str] = []
    artifacts: list[str] = []
    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(text):
        if text.startswith("{{", index) or text.startswith("{%", index):
            opener = text[index : index + 2]
            closer = "}}" if opener == "{{" else "%}"
            end_marker = text.find(closer, index + 2)
            if end_marker == -1:
                artifacts.append(f"unclosed-template-directive:{opener}")
                spans.append((index, len(text)))
                break
            end = end_marker + 2
            directives.append(text[index:end])
            spans.append((index, end))
            index = end
            continue
        if text.startswith("${", index):
            end = scan_balanced_braces(text, index + 1)
            if end is None:
                artifacts.append("unclosed-template-directive:${")
                spans.append((index, len(text)))
                break
            directives.append(text[index:end])
            spans.append((index, end))
            index = end
            continue
        if text[index] == "{":
            end = scan_balanced_braces(text, index)
            if end is not None:
                brace_expressions.append(text[index:end])
                spans.append((index, end))
                index = end
                continue
        index += 1
    return directives, brace_expressions, mask_spans(text, spans), artifacts


def extract_markdown_destinations(text: str) -> list[str]:
    destinations: list[str] = []
    for match in INLINE_LINK_START_RE.finditer(text):
        index = match.end()
        while index < len(text) and text[index] in " \t\n":
            index += 1
        if index >= len(text):
            continue
        if text[index] == "<":
            end = index + 1
            escaped = False
            while end < len(text):
                if escaped:
                    escaped = False
                elif text[end] == "\\":
                    escaped = True
                elif text[end] == ">":
                    destinations.append(text[index + 1 : end])
                    break
                elif text[end] in "\r\n":
                    break
                end += 1
            continue
        start = index
        depth = 0
        escaped = False
        while index < len(text):
            character = text[index]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == "(":
                depth += 1
            elif character == ")":
                if depth == 0:
                    break
                depth -= 1
            elif character.isspace() and depth == 0:
                break
            index += 1
        if index > start:
            destinations.append(text[start:index])
    return destinations


def normalize_reference_id(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def extract_markdown_references(text: str) -> list[str]:
    references: list[str] = []
    definitions: dict[str, str] = {}
    definition_spans: set[tuple[int, int]] = set()
    offset = 0
    for line in text.splitlines(keepends=True):
        footnote = FOOTNOTE_DEFINITION_RE.match(line.rstrip("\r\n"))
        if footnote:
            references.append(f"footnote-definition:{footnote.group(1)}")
        else:
            definition = REFERENCE_DEFINITION_RE.match(line.rstrip("\r\n"))
            if definition:
                identifier = definition.group(1)
                destination = definition.group(2) if definition.group(2) is not None else definition.group(3)
                definitions[normalize_reference_id(identifier)] = identifier
                references.append(f"definition:{identifier}->{destination}")
                bracket_end = line.find("]") + 1
                definition_spans.add((offset, offset + bracket_end))
        offset += len(line)

    references.extend(f"footnote-id:{match.group(1)}" for match in FOOTNOTE_RE.finditer(text))
    for match in BRACKET_TOKEN_RE.finditer(text):
        span = match.span()
        label = match.group(1)
        if label.startswith("^") or span in definition_spans:
            continue
        after = text[match.end() :]
        if after.startswith("("):
            continue
        explicit = re.match(r"^\[([^\]\n]*)\]", after)
        if explicit:
            identifier = explicit.group(1) or label
            references.append(f"reference-use:{identifier}")
            continue
        if normalize_reference_id(label) in definitions:
            references.append(f"reference-use:{label}")
    return references


def extract_markup(text: str) -> tuple[list[str], list[str], list[str]]:
    tags: list[str] = []
    attributes: list[str] = []
    protected_values: list[str] = []
    for match in TAG_RE.finditer(text):
        closing, tag, raw_attributes, self_closing = match.groups()
        kind = "close" if closing else "self" if self_closing else "open"
        tags.append(f"{kind}:{tag}")
        if closing or not raw_attributes:
            continue
        for attr_match in ATTR_RE.finditer(raw_attributes):
            name = attr_match.group(1)
            values = attr_match.groups()[1:]
            value = next((item for item in values if item is not None), None)
            attributes.append(f"{tag}:{name}")
            if value is not None and name.lower() not in COPY_ATTRIBUTES:
                protected_values.append(f"{tag}:{name}={value}")
    return tags, attributes, protected_values


def extract_artifacts(text: str, structural: Iterable[str]) -> list[str]:
    artifacts = list(structural)
    for name, pattern in ARTIFACT_PATTERNS.items():
        artifacts.extend(f"{name}:{match.group(0).strip()}" for match in pattern.finditer(text))
    return artifacts


def inventory(text: str) -> dict[str, list[str]]:
    body, frontmatter_keys, frontmatter_values, frontmatter_artifacts = extract_frontmatter(text)
    fences, indented, inline_code, prose, code_artifacts = extract_code(body)
    mdx_esm, without_esm = extract_mdx_esm(prose)
    comments, entities, raw_text, html_visible, html_artifacts = extract_html_special(without_esm)
    directives, brace_expressions, visible_copy, expression_artifacts = extract_expressions(html_visible)
    tags, attributes, attribute_values = extract_markup(html_visible)
    dates = [match.group(0) for pattern in DATE_RES for match in pattern.finditer(visible_copy)]
    structural_artifacts = frontmatter_artifacts + code_artifacts + html_artifacts + expression_artifacts
    return {
        "urls": [match.group(0) for match in URL_RE.finditer(visible_copy)],
        "emails": [match.group(0) for match in EMAIL_RE.finditer(visible_copy)],
        "markdown-destinations": extract_markdown_destinations(visible_copy),
        "markdown-references": extract_markdown_references(visible_copy),
        "numbers-dates-currency-units": [match.group(0) for match in NUMBER_RE.finditer(visible_copy)] + dates,
        "fenced-code": fences,
        "indented-code": indented,
        "inline-code": inline_code,
        "frontmatter-keys": frontmatter_keys,
        "frontmatter-protected-values": frontmatter_values,
        "html-comments": comments,
        "html-entities": entities,
        "html-raw-text": raw_text,
        "mdx-esm": mdx_esm,
        "template-directives": directives,
        "brace-expressions": brace_expressions,
        "markup-tags": tags,
        "markup-attribute-names": attributes,
        "markup-protected-values": attribute_values,
        "artifacts": extract_artifacts(visible_copy, structural_artifacts),
    }


def unique_protected_literals(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value.strip():
            raise ValueError("protected literal must not be blank")
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


def literal_inventory(text: str, literals: Iterable[str]) -> list[str]:
    values: list[str] = []
    for literal in literals:
        values.extend([literal] * text.count(literal))
    return values


def build_warnings(
    original_text: str, revised_text: str, before: dict[str, list[str]], protected_literals: list[str]
) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    if not original_text.strip():
        warnings.append({"code": "original-empty", "message": "The original is empty or whitespace-only."})
    if not revised_text.strip():
        warnings.append({"code": "revised-empty", "message": "The revised text is empty or whitespace-only."})
    deterministic_count = sum(len(values) for key, values in before.items() if key != "artifacts")
    if deterministic_count == 0 and not protected_literals:
        warnings.append(
            {
                "code": "no-deterministic-protections",
                "message": "No deterministic protected items were found; rely on semantic and editorial review.",
            }
        )
    original_length = len(original_text)
    revised_length = len(revised_text)
    if original_length:
        delta = abs(revised_length - original_length)
        ratio = revised_length / original_length
        if (delta >= 200 and (ratio >= 1.8 or ratio <= 0.55)) or (
            original_length >= 500 and delta / original_length >= 0.5
        ):
            warnings.append(
                {
                    "code": "large-size-delta",
                    "message": (
                        f"Character count changed from {original_length} to {revised_length}; "
                        "verify scope and completeness."
                    ),
                }
            )
    return warnings


def audit(
    original_text: str, revised_text: str, protected_literals: Iterable[str] | None = None
) -> dict[str, object]:
    literals = unique_protected_literals(protected_literals or [])
    for literal in literals:
        if literal not in original_text:
            raise ValueError(f"protected literal not present in original: {literal!r}")

    before = inventory(original_text)
    after = inventory(revised_text)
    differences: list[Difference] = []
    for category in before:
        if category == "artifacts":
            continue
        difference = compare(category, before[category], after[category])
        if difference:
            differences.append(difference)
    literal_difference = compare(
        "user-protected-literals",
        literal_inventory(original_text, literals),
        literal_inventory(revised_text, literals),
    )
    if literal_difference:
        differences.append(literal_difference)

    before_artifacts = counter(before["artifacts"])
    after_artifacts = counter(after["artifacts"])
    added_artifacts = expanded(after_artifacts - before_artifacts)
    existing_artifacts = expanded(after_artifacts & before_artifacts)
    return {
        "pass": not differences and not added_artifacts,
        "differences": [asdict(item) for item in differences],
        "artifacts": {"added": added_artifacts, "existing": existing_artifacts},
        "warnings": build_warnings(original_text, revised_text, before, literals),
        "limitations": [
            "A pass does not prove semantic equivalence or factual truth.",
            "A pass does not prove style quality, native fluency, publication fitness, or authorship.",
            "This conservative inventory is not a complete Markdown, MDX, YAML, template, or HTML parser.",
            "Run the consuming parser, build, or renderer for structured files.",
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit deterministic protected-content drift between an original and revised text file."
    )
    parser.add_argument("--json", action="store_true", help="emit a machine-readable JSON report")
    parser.add_argument(
        "--protect",
        action="append",
        default=[],
        metavar="TEXT",
        help="protect an exact literal; repeat for additional invariants",
    )
    parser.add_argument(
        "--protect-from",
        action="append",
        default=[],
        type=Path,
        metavar="FILE",
        help="read newline-delimited literals, ignoring blank lines and lines beginning with #",
    )
    parser.add_argument("original", type=Path, help="path to the original .txt, .md, .mdx, or .html file")
    parser.add_argument("revised", type=Path, help="path to the revised file")
    return parser.parse_args(argv)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise RuntimeError(f"cannot read {path}: {error}") from error


def read_protected_files(paths: Iterable[Path]) -> list[str]:
    literals: list[str] = []
    for path in paths:
        values = [
            line
            for line in read_text(path).splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if not values:
            raise ValueError(f"protected-literal file contains no protected literals: {path}")
        literals.extend(values)
    return literals


def render_text(report: dict[str, object]) -> str:
    lines = ["PASS" if report["pass"] else "FAIL"]
    for item in report["differences"]:  # type: ignore[union-attr]
        lines.append(f"\n{item['category']}:")
        for value in item["missing"]:
            lines.append(f"  missing: {value}")
        for value in item["added"]:
            lines.append(f"  added: {value}")
    artifacts = report["artifacts"]  # type: ignore[assignment]
    for value in artifacts["added"]:
        lines.append(f"\nnew production artifact: {value}")
    for value in artifacts["existing"]:
        lines.append(f"\nexisting production artifact: {value}")
    for warning in report["warnings"]:  # type: ignore[union-attr]
        lines.append(f"\nwarning [{warning['code']}]: {warning['message']}")
    lines.append("\nLimits:")
    lines.extend(f"- {line}" for line in report["limitations"])  # type: ignore[union-attr]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        literals = list(args.protect) + read_protected_files(args.protect_from)
        report = audit(read_text(args.original), read_text(args.revised), protected_literals=literals)
    except (RuntimeError, ValueError) as error:
        print(f"audit error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
