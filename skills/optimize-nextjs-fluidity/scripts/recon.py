#!/usr/bin/env python3
"""Repo profiler for optimize-nextjs-fluidity — Phase 1 recon.

Produces the facts every later phase cites: versions, project shape, config
inventory, feature counts, and library-vs-custom detection. Strictly read-only:
no writes, no installs, no builds, no git mutation. Secret VALUES are never
printed — only .env file names.

Counting discipline (see references/workflow/false-positives.md):
  * comment-only matches are excluded
  * tests/stories/mocks are excluded
  * RSS/feed route handlers and ImageResponse/Satori routes are excluded from
    JSX image rules

Usage:
    recon.py <repo-root>           # markdown for nextjs-enhancement/00-recon.md
    recon.py <repo-root> --json    # machine-readable
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SRC_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs"}
SKIP_DIRS = {
    "node_modules", ".next", ".git", "dist", "build", "out", ".vercel",
    "coverage", ".turbo", "__pycache__", ".cache",
    # git worktrees and agent scratch dirs hold full copies of the repo — counting
    # them multiplies every metric by the number of checkouts present
    ".claude", ".worktrees", ".yarn", ".pnpm-store", "storybook-static",
}
# built/vendored asset bundles that are not source
SKIP_PATH_PARTS = ("/public/", "/static/", "/vendor/", "/.output/", "/scripts/qa/")
TEST_MARKERS = (".test.", ".spec.", "__tests__", "__mocks__", "/e2e/", ".stories.", "/.storybook/")
CONFIG_FILES = ("next.config.ts", "next.config.js", "next.config.mjs", "next.config.cjs")

LIB_SIGNALS = {
    "next-themes": "theming",
    "next-intl": "i18n",
    "next-i18next": "i18n",
    "tailwindcss": "styling",
    "swr": "data",
    "@tanstack/react-query": "data",
    "@vercel/speed-insights": "measurement",
    "@vercel/analytics": "measurement",
    "web-vitals": "measurement",
    "@sentry/nextjs": "monitoring",
}


def is_test(path: str) -> bool:
    p = path.replace("\\", "/")
    return any(m in p for m in TEST_MARKERS)


def is_image_exempt(path: str) -> bool:
    """RSS/feed/OG routes legitimately use raw <img> or produce non-HTML."""
    p = path.replace("\\", "/")
    return ("/api/rss" in p or "/feed" in p or "/api/og" in p
            or p.endswith("opengraph-image.tsx") or p.endswith("twitter-image.tsx"))


def strip_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"(?m)^\s*(?://|\*|/\*).*$", "", src)


def walk(root: Path):
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in SRC_EXT:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        rel = "/" + str(p.relative_to(root)).replace("\\", "/")
        if any(part in rel for part in SKIP_PATH_PARTS):
            continue
        yield p


def load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def installed(root: Path, pkg: str) -> str | None:
    return (load_json(root / "node_modules" / pkg / "package.json") or {}).get("version")


def detect_router(root: Path) -> dict:
    for base in ("app", "src/app"):
        if (root / base).is_dir():
            return {"router": "app", "dir": base, "src_prefixed": base.startswith("src/")}
    for base in ("pages", "src/pages"):
        if (root / base).is_dir():
            return {"router": "pages", "dir": base, "src_prefixed": base.startswith("src/")}
    return {"router": "unknown", "dir": None, "src_prefixed": False}


def config_keys(root: Path) -> tuple[str | None, list[str]]:
    for name in CONFIG_FILES:
        p = root / name
        if not p.is_file():
            continue
        src = strip_comments(p.read_text(encoding="utf-8", errors="replace"))
        keys = sorted(set(re.findall(r"^\s{2,6}([A-Za-z_][A-Za-z0-9_]*)\s*:", src, re.M)))
        noise = {"protocol", "hostname", "pathname", "port", "search", "source",
                 "destination", "key", "value", "permanent", "has", "type"}
        return name, [k for k in keys if k not in noise]
    return None, []


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-only Next.js repo profiler.")
    ap.add_argument("repo_root")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = Path(args.repo_root).expanduser().resolve()
    if not (root / "package.json").is_file():
        print(f"error: no package.json at {root}", file=sys.stderr)
        return 2

    pkg = load_json(root / "package.json")
    deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}

    counts: dict[str, int] = {}
    samples: dict[str, list[str]] = {}

    def hit(key: str, path: Path, cap: int = 4) -> None:
        counts[key] = counts.get(key, 0) + 1
        samples.setdefault(key, [])
        if len(samples[key]) < cap:
            samples[key].append(str(path.relative_to(root)))

    total_src = 0
    for p in walk(root):
        rel = str(p.relative_to(root))
        raw = p.read_text(encoding="utf-8", errors="replace")
        if is_test(rel):
            continue
        total_src += 1
        src = strip_comments(raw)

        if re.search(r"^\s*['\"]use client['\"]", src, re.M):
            hit("use_client", p)
        if re.search(r"^\s*['\"]use server['\"]", src, re.M):
            hit("use_server", p)
        if "use cache" in src:
            hit("use_cache", p)
        if re.search(r"from ['\"]next/image['\"]", src):
            hit("next_image", p)
        if re.search(r"<img[\s>]", src) and not is_image_exempt(rel):
            hit("raw_img", p)
        if re.search(r"from ['\"]next/font", src):
            hit("next_font", p)
        if re.search(r"fonts\.(googleapis|gstatic)\.com", src) and not rel.startswith("next.config"):
            hit("external_font", p)
        if re.search(r"from ['\"]next/dynamic['\"]|React\.lazy\(", src):
            hit("dynamic_import", p)
        if "<Suspense" in src:
            hit("suspense", p)
        if re.search(r"\buseEffect\b", src) and re.search(r"\bfetch\(", src):
            hit("client_fetch", p)
        if re.search(r"\bgenerateMetadata\b", src):
            hit("generate_metadata", p)
        if re.search(r"export const metadata\b", src):
            hit("static_metadata", p)
        if re.search(r"export const (revalidate|dynamic|fetchCache)\b", src):
            hit("legacy_segment_export", p)
        if "unstable_cache" in src:
            hit("unstable_cache", p)
        if re.search(r"runtime\s*=\s*['\"]edge['\"]", src):
            hit("edge_runtime", p)
        if re.search(r"preferredRegion", src):
            hit("preferred_region", p)
        if re.search(r"from ['\"]next/script['\"]", src):
            hit("next_script", p)
        if re.search(r"cacheLife\(|cacheTag\(", src):
            hit("cache_life_tag", p)
        if re.search(r"\bViewTransition\b", src):
            hit("view_transition", p)
        if p.name in ("loading.tsx", "loading.jsx", "loading.ts", "loading.js"):
            hit("loading_file", p)

    cfg_name, keys = config_keys(root)
    router = detect_router(root)
    libs = {name: LIB_SIGNALS[name] for name in LIB_SIGNALS if name in deps}

    res = {
        "repo_root": str(root),
        "versions": {
            "next_installed": installed(root, "next"),
            "next_declared": deps.get("next"),
            "react_installed": installed(root, "react"),
            "typescript": deps.get("typescript"),
            "node_engine": (pkg.get("engines") or {}).get("node"),
            "package_manager": pkg.get("packageManager"),
        },
        "shape": {
            **router,
            "proxy_ts": (root / "src/proxy.ts").is_file() or (root / "proxy.ts").is_file(),
            "middleware_ts": (root / "src/middleware.ts").is_file() or (root / "middleware.ts").is_file(),
            "vercel_json": (root / "vercel.json").is_file(),
            "vercel_linked": (root / ".vercel").is_dir(),
            "config_file": cfg_name,
        },
        "config_keys": keys,
        "counts": {**counts, "source_files_excl_tests": total_src},
        "samples": samples,
        "libraries": libs,
        "env_files": sorted(p.name for p in root.glob(".env*") if p.is_file()),
        "scripts": sorted((pkg.get("scripts") or {}).keys()),
    }

    if args.json:
        print(json.dumps(res, indent=2))
        return 0

    v, s, c = res["versions"], res["shape"], res["counts"]
    out = [f"# Recon — {root.name}\n", f"**Repo root:** `{root}`\n", "## Versions\n",
           "| What | Installed | Declared |", "|---|---|---|",
           f"| next | `{v['next_installed'] or 'not installed'}` | `{v['next_declared'] or 'n/a'}` |",
           f"| react | `{v['react_installed'] or 'not installed'}` | — |",
           f"| typescript | — | `{v['typescript'] or 'n/a'}` |",
           f"| node engine | — | `{v['node_engine'] or 'unspecified'}` |",
           f"| package manager | — | `{v['package_manager'] or 'unspecified'}` |\n",
           "## Project shape\n",
           f"- Router: **{s['router']}** (dir `{s['dir']}`, src-prefixed: {s['src_prefixed']})",
           f"- Network boundary: {'`proxy.ts`' if s['proxy_ts'] else ('`middleware.ts` (deprecated)' if s['middleware_ts'] else 'none')}",
           f"- Vercel: linked={s['vercel_linked']}, vercel.json={s['vercel_json']}",
           f"- Config file: `{s['config_file'] or 'NOT FOUND'}`",
           f"- `.env` files present (names only): {', '.join(res['env_files']) or 'none'}\n",
           "## Config keys found\n",
           (", ".join(f"`{k}`" for k in keys) if keys else "_none parsed_") + "\n",
           "## Feature inventory\n", "| Signal | Count | Sample paths |", "|---|---|---|"]

    labels = [
        ("source_files_excl_tests", "Source files (excl. tests)"),
        ("use_client", "`'use client'` files"),
        ("use_server", "Server Actions (`'use server'`)"),
        ("use_cache", "`use cache` files"),
        ("cache_life_tag", "`cacheLife`/`cacheTag` calls"),
        ("next_image", "`next/image` importers"),
        ("raw_img", "Raw `<img>` (excl. tests/RSS/OG)"),
        ("next_font", "`next/font` usage"),
        ("external_font", "External font requests"),
        ("dynamic_import", "`next/dynamic` / `React.lazy`"),
        ("suspense", "`<Suspense>` files"),
        ("loading_file", "`loading.*` files"),
        ("client_fetch", "`useEffect` + `fetch`"),
        ("generate_metadata", "`generateMetadata`"),
        ("static_metadata", "static `metadata` exports"),
        ("legacy_segment_export", "Legacy `revalidate|dynamic|fetchCache`"),
        ("unstable_cache", "`unstable_cache`"),
        ("edge_runtime", "`runtime = 'edge'`"),
        ("preferred_region", "`preferredRegion`"),
        ("next_script", "`next/script`"),
        ("view_transition", "`ViewTransition` usage"),
    ]
    for key, label in labels:
        n = c.get(key, 0)
        smp = ", ".join(f"`{x}`" for x in samples.get(key, [])) or "—"
        out.append(f"| {label} | {n} | {smp} |")

    out.append("\n## Libraries detected\n")
    out.append(", ".join(f"`{k}` ({v})" for k, v in libs.items()) if libs else "_none of the tracked libraries_")
    out.append("\n**Library-vs-custom:** theming = "
               f"{'next-themes' if 'next-themes' in libs else 'custom or none'}; i18n = "
               f"{'next-intl' if 'next-intl' in libs else 'custom or none'}. "
               "A custom implementation means verdict `APPLICABLE-CUSTOM` — compare the "
               "mechanism, never propose a library migration.\n")
    out.append("> Fill in archetype, baseline, existing-good-practice, and anomalies by hand — "
               "see `references/artifact/recon-report-template.md`.")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
