#!/usr/bin/env python3
"""Capability probe — the gating primitive for optimize-nextjs-fluidity.

Answers one question per config key: does THIS install accept it? Reads the
installed package, never a version guess:

  node_modules/next/package.json          -> the authoritative installed version
  node_modules/next/dist/server/
      config-schema.js                    -> which next.config keys are accepted
  node_modules/react/package.json         -> gates React 19.2 APIs

Read-only. Touches nothing, installs nothing, runs no build.

Usage:
    probe-capabilities.py <repo-root>            # markdown table for 00-recon.md
    probe-capabilities.py <repo-root> --json     # machine-readable
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# key -> (owning domain, introduced version, note)
PROBE_KEYS: dict[str, tuple[str, str, str]] = {
    "cacheComponents": ("rendering-strategy-caching", "16.0.0", "gates partial prefetching + auto <Activity>"),
    "partialPrefetching": ("navigation-prefetching", "16.3.0", "also requires cacheComponents"),
    "staleTimes": ("navigation-prefetching", "14.2.0", "experimental, production-discouraged"),
    "viewTransition": ("page-transitions-view-transitions", "15.x", "recorded removed in 16 — probe before removing"),
    "cachedNavigations": ("navigation-prefetching", "16.2.0", "experimental"),
    "prefetchInlining": ("navigation-prefetching", "16.2.0", "experimental"),
    "useOffline": ("navigation-prefetching", "16.3.0", "experimental"),
    "inlineCss": ("bundle-code-splitting", "16.2.0", "CSS delivery"),
    "reactCompiler": ("bundle-code-splitting", "16.0.0", "stable opt-in; NOT a bundle-size reducer"),
    "turbopackRustReactCompiler": ("build-performance-turbopack", "16.3.0", "experimental; requires reactCompiler"),
    "optimizePackageImports": ("bundle-code-splitting", "pre-14.2", "formally experimental"),
    "turbopackFileSystemCacheForBuild": ("build-performance-turbopack", "16.0.0", "default-on by 16.3"),
    "turbopackFileSystemCacheForDev": ("build-performance-turbopack", "15.5.0", "default-on by 16.1"),
    "turbopackMemoryEviction": ("build-performance-turbopack", "16.3.0", "experimental, dev-only"),
    "htmlLimitedBots": ("seo-metadata", "15.2.0", "REPLACES the default bot list, does not extend"),
    "serverExternalPackages": ("bundle-code-splitting", "15.0.0", "renamed from serverComponentsExternalPackages"),
    "exposeTestingApiInProductionBuild": ("measurement-regression-guardrails", "16.3.0", "experimental; CI only"),
    "useTypeScriptCli": ("build-performance-turbopack", "16.3.0", "experimental; needs typescript@^7"),
    "instantInsights": ("measurement-regression-guardrails", "16.3.0", "requires cacheComponents"),
}

CONFIG_FILES = ("next.config.ts", "next.config.js", "next.config.mjs", "next.config.cjs")

SCHEMA_CANDIDATES = (
    "node_modules/next/dist/server/config-schema.js",
    "node_modules/next/dist/server/config-schema.mjs",
    "node_modules/next/dist/esm/server/config-schema.js",
)


def read_pkg_version(root: Path, pkg: str) -> str | None:
    """Installed version straight from node_modules, or None if absent."""
    p = root / "node_modules" / pkg / "package.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("version")
    except Exception:
        return None


def declared_version(root: Path, pkg: str) -> str | None:
    try:
        data = json.loads((root / "package.json").read_text(encoding="utf-8"))
    except Exception:
        return None
    for field in ("dependencies", "devDependencies"):
        got = (data.get(field) or {}).get(pkg)
        if got:
            return got
    return None


def find_schema(root: Path) -> Path | None:
    for rel in SCHEMA_CANDIDATES:
        p = root / rel
        if p.is_file():
            return p
    # pnpm strict layouts hide the real package behind a symlinked dir
    store = root / "node_modules" / ".pnpm"
    if store.is_dir():
        for cand in sorted(store.glob("next@*/node_modules/next/dist/server/config-schema.js")):
            return cand
    return None


def find_config(root: Path) -> Path | None:
    for name in CONFIG_FILES:
        p = root / name
        if p.is_file():
            return p
    return None


def strip_comments(src: str) -> str:
    """Drop // and /* */ comments so a key mentioned in prose isn't 'set'."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", "", src)


def probe(root: Path) -> dict:
    schema = find_schema(root)
    schema_src = schema.read_text(encoding="utf-8", errors="replace") if schema else ""

    cfg_path = find_config(root)
    cfg_src = strip_comments(cfg_path.read_text(encoding="utf-8", errors="replace")) if cfg_path else ""

    rows = []
    for key, (domain, introduced, note) in PROBE_KEYS.items():
        if not schema:
            verdict = "unresolved"
        elif re.search(rf"\b{re.escape(key)}\b", schema_src):
            verdict = "present"
        else:
            verdict = "absent"
        # "set in repo" means an assignment, not a mention
        set_in_repo = bool(cfg_src) and bool(
            re.search(rf"\b{re.escape(key)}\b\s*:", cfg_src)
        )
        rows.append(
            {
                "key": key,
                "domain": domain,
                "introduced": introduced,
                "probe": verdict,
                "set_in_repo": set_in_repo,
                "note": note,
            }
        )

    return {
        "repo_root": str(root),
        "next_installed": read_pkg_version(root, "next"),
        "next_declared": declared_version(root, "next"),
        "react_installed": read_pkg_version(root, "react"),
        "schema_path": str(schema.relative_to(root)) if schema else None,
        "config_path": str(cfg_path.relative_to(root)) if cfg_path else None,
        "confidence": "probe-verified" if schema else "version-inferred",
        "keys": rows,
    }


def consequence(row: dict) -> str:
    if row["probe"] == "absent":
        return "**NOT APPLICABLE** — never recommend on this install"
    if row["probe"] == "unresolved":
        return "unresolved — fall back to version comparison, mark findings `version-inferred`"
    if row["set_in_repo"]:
        return "present and set — do not blind-remove; judge by stability tier"
    return "available — adopt only if the priority matrix justifies it"


def render_markdown(res: dict) -> str:
    out: list[str] = []
    out.append("### Capability probe\n")
    out.append(f"- Installed next: `{res['next_installed'] or 'not installed'}`")
    out.append(f"- Declared next: `{res['next_declared'] or 'n/a'}`")
    out.append(f"- Installed react: `{res['react_installed'] or 'not installed'}`")
    out.append(f"- Schema: `{res['schema_path'] or 'NOT FOUND'}`")
    out.append(f"- Config: `{res['config_path'] or 'NOT FOUND'}`")
    out.append(f"- Confidence: **{res['confidence']}**\n")

    if res["next_installed"] and res["next_declared"]:
        dec = res["next_declared"].lstrip("^~>=< ")
        if dec and not res["next_installed"].startswith(dec.split()[0]):
            out.append(
                f"> **Mismatch:** declared `{res['next_declared']}` vs installed "
                f"`{res['next_installed']}`. Installed wins; note it as a finding.\n"
            )

    if res["confidence"] == "version-inferred":
        out.append(
            "> **No config schema found.** `node_modules` is missing or laid out "
            "unusually. Every downstream finding must be stamped "
            "`confidence: version-inferred`.\n"
        )

    out.append("| Config key | Domain | Introduced | Probe | Set in repo | Consequence |")
    out.append("|---|---|---|---|---|---|")
    for r in sorted(res["keys"], key=lambda x: (x["probe"] != "absent", x["key"])):
        out.append(
            f"| `{r['key']}` | {r['domain']} | {r['introduced']} | **{r['probe']}** | "
            f"{'yes' if r['set_in_repo'] else 'no'} | {consequence(r)} |"
        )

    absent = [r["key"] for r in res["keys"] if r["probe"] == "absent"]
    if absent:
        out.append("\n**Withhold list** (absent from this install — emit no task proposing these):")
        out.append(", ".join(f"`{k}`" for k in sorted(absent)))
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Probe an installed Next.js for config-key availability (read-only)."
    )
    ap.add_argument("repo_root", help="path to the target Next.js repo")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    args = ap.parse_args()

    root = Path(args.repo_root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    if not (root / "package.json").is_file():
        print(f"error: no package.json at {root} — not a JS project", file=sys.stderr)
        return 2

    res = probe(root)
    print(json.dumps(res, indent=2) if args.json else render_markdown(res), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
