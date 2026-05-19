#!/usr/bin/env python3
"""Cluster normalized review feedback without assigning verdicts."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

BOT_MARKERS = (
    "[bot]",
    "bot",
    "coderabbit",
    "copilot",
    "cubic",
    "devin",
    "greptile",
    "bito",
)

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "here",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cluster normalized review feedback JSONL into stable review items."
    )
    parser.add_argument("--input", required=True, help="Input normalized JSONL file")
    parser.add_argument("--output", required=True, help="Output clusters JSON file")
    return parser.parse_args()


def classify_source_type(source: str, existing: str | None) -> str:
    if existing in {"human", "bot", "self-review", "markdown doc"}:
        return existing
    lowered = (source or "").lower()
    if any(marker in lowered for marker in BOT_MARKERS):
        return "bot"
    return "human"


def normalize_severity(body: str, source: str) -> str:
    text = f"{source or ''} {body or ''}".lower()
    if any(term in text for term in ("critical", "blocker", "blocking", "security", "data loss", "high severity")):
        return "critical"
    if any(term in text for term in ("nitpick", "nit:", "typo", "minor", "style", "low severity")):
        return "minor"
    if any(term in text for term in ("warning", "potential issue", "bug", "important", "medium severity", "yellow")):
        return "important"
    if "\U0001f534" in body:
        return "critical"
    if "\U0001f7e1" in body or "\u26a0" in body:
        return "important"
    return "unknown"


def clean_text(body: str) -> str:
    text = re.sub(r"```.*?```", " ", body or "", flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    return text.lower()


def fingerprint(body: str) -> str:
    words = re.findall(r"[a-z0-9_]+", clean_text(body))
    useful = [word for word in words if word not in STOPWORDS and len(word) > 2]
    if useful:
        return "-".join(useful[:12])
    fallback = re.sub(r"\s+", " ", (body or "").strip().lower())
    return fallback[:80] or "empty"


def concern_slug(body: str) -> str:
    words = re.findall(r"[a-z0-9_]+", clean_text(body))
    useful = [word for word in words if word not in STOPWORDS and len(word) > 2]
    return "-".join(useful[:4]) if useful else "general"


def coerce_line(item: dict) -> int | None:
    for key in ("line", "original_line"):
        value = item.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def load_items(path: Path) -> list[dict]:
    items = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid JSONL at line {line_no}: {exc}") from exc
            item["source_type"] = classify_source_type(item.get("source", ""), item.get("source_type"))
            item["severity_hint"] = normalize_severity(item.get("body", ""), item.get("source", ""))
            item["_line_for_cluster"] = coerce_line(item)
            item["_fingerprint"] = fingerprint(item.get("body", ""))
            item["_concern"] = concern_slug(item.get("body", ""))
            items.append(item)
    return items


def sort_key(item: dict) -> tuple:
    path = item.get("path") or ""
    line = item.get("_line_for_cluster")
    return (path, line if line is not None else -1, item.get("_fingerprint", ""))


def cluster_items(items: list[dict]) -> list[list[dict]]:
    path_groups: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        path_groups[item.get("path") or "__general__"].append(item)

    clusters: list[list[dict]] = []
    for path in sorted(path_groups):
        group = sorted(path_groups[path], key=sort_key)
        if path == "__general__":
            by_fingerprint: dict[str, list[dict]] = defaultdict(list)
            for item in group:
                by_fingerprint[item["_fingerprint"]].append(item)
            clusters.extend(by_fingerprint[key] for key in sorted(by_fingerprint))
            continue

        current: list[dict] = []
        current_end: int | None = None
        for item in group:
            line = item.get("_line_for_cluster")
            if line is None:
                clusters.append([item])
                continue
            if not current:
                current = [item]
                current_end = line
                continue
            if current_end is not None and abs(line - current_end) <= 5:
                current.append(item)
                current_end = max(current_end, line)
            else:
                clusters.append(current)
                current = [item]
                current_end = line
        if current:
            clusters.append(current)
    return clusters


def public_item(item: dict, item_id: str) -> dict:
    return {
        "id": item_id,
        "channel": item.get("channel"),
        "comment_id": item.get("id"),
        "source": item.get("source"),
        "source_type": item.get("source_type"),
        "path": item.get("path"),
        "line": item.get("line"),
        "original_line": item.get("original_line"),
        "commit_id": item.get("commit_id"),
        "severity_hint": item.get("severity_hint"),
        "dedupe_key": item.get("_fingerprint"),
        "body": item.get("body"),
    }


def build_output(input_path: Path, items: list[dict]) -> dict:
    clusters = []
    for cluster_index, cluster in enumerate(cluster_items(items), start=1):
        cluster_id = f"CR-{cluster_index:03d}"
        lines = [item["_line_for_cluster"] for item in cluster if item.get("_line_for_cluster") is not None]
        paths = sorted({item.get("path") for item in cluster if item.get("path")})
        dedupe_groups: dict[str, list[str]] = defaultdict(list)
        public_items = []
        for item_index, item in enumerate(cluster, start=1):
            item_id = f"{cluster_id}-{item_index:02d}"
            public_items.append(public_item(item, item_id))
            dedupe_groups[item["_fingerprint"]].append(item_id)

        clusters.append(
            {
                "id": cluster_id,
                "location": {
                    "path": paths[0] if len(paths) == 1 else None,
                    "paths": paths,
                    "start_line": min(lines) if lines else None,
                    "end_line": max(lines) if lines else None,
                },
                "concern": cluster[0].get("_concern", "general"),
                "source_types": sorted({item.get("source_type", "human") for item in cluster}),
                "sources": [
                    {
                        "source": item.get("source"),
                        "source_type": item.get("source_type"),
                        "channel": item.get("channel"),
                        "comment_id": item.get("id"),
                    }
                    for item in cluster
                ],
                "severity_hints": sorted({item.get("severity_hint", "unknown") for item in cluster}),
                "dedupe_groups": [
                    {"dedupe_key": key, "item_ids": ids}
                    for key, ids in sorted(dedupe_groups.items())
                ],
                "items": public_items,
                "final_verdict": None,
            }
        )

    return {
        "generated_by": "cluster-feedback.py",
        "input": str(input_path),
        "cluster_rule": "same path and line within +/-5; pathless comments grouped by content fingerprint",
        "verdict_policy": "no final verdicts assigned; verify clusters against code before ACCEPT/PUSHBACK/CLARIFY/DEFER/DISMISS",
        "clusters": clusters,
    }


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    items = load_items(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output = build_output(input_path, items)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {output_path} ({len(output['clusters'])} clusters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
