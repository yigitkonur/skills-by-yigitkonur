#!/usr/bin/env python3
"""Audit deterministic token and structure preservation across a rewrite.

This is deliberately not a semantic equivalence checker. It inventories exact
content that editorial rewrites commonly damage and reports newly introduced
production residue. Use the consuming project's parser and a human semantic
review in addition to this audit.
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
MARKDOWN_DEST_RE = re.compile(
    r"!?\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s)]+))(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
FENCE_OPEN_RE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})([^\r\n]*)")
INLINE_CODE_RE = re.compile(r"(?s)(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
DATE_RES = (
    re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)"),
    re.compile(r"(?<!\d)\d{1,2}[./-]\d{1,2}[./-]\d{2,4}(?!\d)"),
    re.compile(
        r"(?i)\b(?:\d{1,2}\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+(?:\d{1,2},?\s+)?\d{4}\b"
    ),
)
NUMBER_RE = re.compile(
    r"(?i)(?<![\w])(?:[$€£¥₹]\s*)?[+-]?\d+(?:[.,]\d+)*(?:\s?(?:%|percent|percentage points?|"
    r"USD|EUR|GBP|JPY|TRY|CAD|AUD|CHF|INR|ms|s|sec(?:onds?)?|min(?:utes?)?|h(?:ours?)?|"
    r"B|KB|MB|GB|TB|KiB|MiB|GiB|mm|cm|m|km|in|ft|yd|mi|mg|g|kg|lb|oz|°[CF]|kWh|W|kW))?(?![\w])"
)
TAG_RE = re.compile(r"(?s)<\s*(/?)\s*([A-Za-z][\w.:-]*)(\s[^<>]*?)?\s*(/?)>")
ATTR_RE = re.compile(
    r"([:@A-Za-z_][\w:.-]*)(?:\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|\{([^{}]*)\}|([^\s\"'=<>`]+)))?"
)
FRONTMATTER_LINE_RE = re.compile(r"^(\s*)([A-Za-z_][\w.-]*):(?:\s*(.*))?$")
PROTECTED_FRONTMATTER_KEY_RE = re.compile(
    r"(?i)(?:^|[-_.])(slug|id|uuid|date|time|locale|lang|url|uri|canonical|path|route|redirect|href|src|"
    r"draft|published|status|template|layout|component|version)(?:$|[-_.])"
)
SCALAR_RE = re.compile(r"(?i)^(?:true|false|null|~|[-+]?\d+(?:\.\d+)?)$")
COPY_ATTRIBUTES = {"alt", "title", "placeholder", "aria-label", "aria-description"}

ARTIFACT_PATTERNS = {
    "placeholder": re.compile(
        r"(?im)(?:\b(?:TODO|TBD|FIXME)\b|\[(?:insert|add|replace|source needed)[^\]\n]*\]|"
        r"\{\{\s*(?:company|name|title|value|placeholder)[^}\n]*\}\}|\blorem ipsum\b)"
    ),
    "assistant-chatter": re.compile(
        r"(?im)^\s*(?:certainly|of course|here(?:'s| is) (?:the|a|your) (?:revised|rewritten|polished|humanized) (?:version|text|copy)|"
        r"i hope this helps)[.!:]?\s*$"
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


def extract_frontmatter(text: str) -> tuple[str, list[str], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text, [], []
    closing = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if closing is None:
        return text, ["<unclosed-frontmatter>"], ["<unclosed-frontmatter>"]

    keys: list[str] = []
    protected_values: list[str] = []
    stack: list[tuple[int, str]] = []
    for line in lines[1:closing]:
        match = FRONTMATTER_LINE_RE.match(line)
        if not match:
            continue
        indent = len(match.group(1).replace("\t", "    "))
        key = match.group(2)
        raw_value = (match.group(3) or "").strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        path = ".".join([item[1] for item in stack] + [key])
        keys.append(path)
        if raw_value:
            value = raw_value.strip('"\'')
            if PROTECTED_FRONTMATTER_KEY_RE.search(path) or SCALAR_RE.match(value) or URL_RE.search(value):
                protected_values.append(f"{path}={raw_value}")
        else:
            stack.append((indent, key))
    body = "\n".join(lines[closing + 1 :])
    return body, keys, protected_values


def extract_code(text: str) -> tuple[list[str], list[str], str]:
    fences: list[str] = []
    lines = text.splitlines(keepends=True)
    masked_lines = list(lines)
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
            index += 1
            continue
        fences.append("".join(lines[index : end + 1]))
        for masked_index in range(index, end + 1):
            line = lines[masked_index]
            newline = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
            masked_lines[masked_index] = " " * (len(line) - len(newline)) + newline
        index = end + 1
    without_fences = "".join(masked_lines)
    inline: list[str] = []

    def mask_inline(match: re.Match[str]) -> str:
        inline.append(match.group(0))
        return " " * len(match.group(0))

    prose = INLINE_CODE_RE.sub(mask_inline, without_fences)
    return fences, inline, prose


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


def extract_artifacts(text: str) -> list[str]:
    artifacts: list[str] = []
    for name, pattern in ARTIFACT_PATTERNS.items():
        artifacts.extend(f"{name}:{match.group(0).strip()}" for match in pattern.finditer(text))
    return artifacts


def inventory(text: str) -> dict[str, list[str]]:
    body, frontmatter_keys, frontmatter_values = extract_frontmatter(text)
    fences, inline_code, prose = extract_code(body)
    tags, attributes, attribute_values = extract_markup(prose)
    markdown_destinations = [match.group(1) or match.group(2) for match in MARKDOWN_DEST_RE.finditer(prose)]
    dates = [match.group(0) for pattern in DATE_RES for match in pattern.finditer(prose)]
    return {
        "urls": [match.group(0) for match in URL_RE.finditer(prose)],
        "emails": [match.group(0) for match in EMAIL_RE.finditer(prose)],
        "markdown-destinations": markdown_destinations,
        "numbers-dates-currency-units": [match.group(0) for match in NUMBER_RE.finditer(prose)] + dates,
        "fenced-code": fences,
        "inline-code": inline_code,
        "frontmatter-keys": frontmatter_keys,
        "frontmatter-protected-values": frontmatter_values,
        "markup-tags": tags,
        "markup-attribute-names": attributes,
        "markup-protected-values": attribute_values,
        "artifacts": extract_artifacts(prose),
    }


def audit(original_text: str, revised_text: str) -> dict[str, object]:
    before = inventory(original_text)
    after = inventory(revised_text)
    differences: list[Difference] = []
    for category in before:
        if category == "artifacts":
            continue
        difference = compare(category, before[category], after[category])
        if difference:
            differences.append(difference)

    before_artifacts = counter(before["artifacts"])
    after_artifacts = counter(after["artifacts"])
    added_artifacts = expanded(after_artifacts - before_artifacts)
    existing_artifacts = expanded(after_artifacts & before_artifacts)
    return {
        "pass": not differences and not added_artifacts,
        "differences": [asdict(item) for item in differences],
        "artifacts": {"added": added_artifacts, "existing": existing_artifacts},
        "limitations": [
            "A pass does not prove semantic equivalence or factual truth.",
            "A pass does not prove style quality, native fluency, publication fitness, or authorship.",
            "Run the consuming parser, build, or renderer for structured files.",
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit deterministic protected-content drift between an original and revised text file."
    )
    parser.add_argument("--json", action="store_true", help="emit a machine-readable JSON report")
    parser.add_argument("original", type=Path, help="path to the original .txt, .md, .mdx, or .html file")
    parser.add_argument("revised", type=Path, help="path to the revised file")
    return parser.parse_args(argv)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise RuntimeError(f"cannot read {path}: {error}") from error


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
    lines.append("\nLimits:")
    lines.extend(f"- {line}" for line in report["limitations"])  # type: ignore[union-attr]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = audit(read_text(args.original), read_text(args.revised))
    except RuntimeError as error:
        print(f"audit error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
