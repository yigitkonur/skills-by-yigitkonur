"""Routing and package contract tests for skills/ci-cd-optimize.

Stricter, skill-specific checks that must not be pushed into the shared
repository validator (which governs all skills). Each test maps to a defect
row in evals/requirements-matrix.json.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "ci-cd-optimize"
SKILL = SKILL_DIR / "SKILL.md"
README = SKILL_DIR / "README.md"
WATCHER = SKILL_DIR / "scripts" / "ci-watch.py"
REFERENCES = sorted((SKILL_DIR / "references").rglob("*.md"))

DESCRIPTION_PREFIXES = ("Use skill if you are ", "Use if ")


def frontmatter_description(text: str) -> str:
    match = re.search(r"^description:\s*(.+)$", text, re.M)
    assert match, "SKILL.md needs a description line"
    return match.group(1).strip().strip('"')


def content_words(text: str) -> set[str]:
    words = re.findall(r"[a-z][a-z\-]{5,}", text.lower())
    return {w.strip("-")[:6] for w in words}


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill_text = SKILL.read_text()
        cls.readme_text = README.read_text()
        cls.watcher_text = WATCHER.read_text()

    # d85-9 — description limits
    def test_description_prefix_and_word_budget(self):
        description = frontmatter_description(self.skill_text)
        self.assertTrue(description.startswith(DESCRIPTION_PREFIXES),
                        f"description must start with one of {DESCRIPTION_PREFIXES}")
        self.assertLessEqual(len(description.split()), 30,
                             "description exceeds the 30-word repository budget")

    # stricter than the shared validator's 1000-line cap
    def test_skill_md_stays_lean(self):
        lines = self.skill_text.count("\n") + 1
        self.assertLessEqual(lines, 500,
                             f"SKILL.md is {lines} lines; the rebuilt contract is <=500")

    # d85-11 — README derivation
    def test_readme_heading_and_category(self):
        self.assertTrue(self.readme_text.startswith("# ci-cd-optimize\n"))
        self.assertIn("**Category:** ops", self.readme_text)

    def test_readme_description_derives_from_frontmatter(self):
        description = frontmatter_description(self.skill_text)
        readme_first_para = self.readme_text.split("\n\n")[1]
        allowed = content_words(description)
        introduced = content_words(readme_first_para) - allowed
        self.assertEqual(introduced, set(),
                         f"README description introduces claims absent from frontmatter: {sorted(introduced)}")

    # routing integrity beyond the shared validator
    def test_every_reference_is_routed_from_skill_md(self):
        for ref in REFERENCES:
            rel = ref.relative_to(SKILL_DIR).as_posix()
            self.assertIn(rel, self.skill_text, f"{rel} not routed from SKILL.md")

    def test_watcher_script_is_routed_and_executable(self):
        self.assertIn("scripts/ci-watch.py", self.skill_text)
        mode = WATCHER.stat().st_mode
        self.assertTrue(mode & 0o111, "ci-watch.py must be executable")

    def test_no_legacy_feedback_document_names(self):
        legacy = [
            "agent-feedback-loop.md", "agent-ci-feedback.md",
            "ci-feedback-loop.md", "ci-watching.md", "watching-runs.md",
            "references/scripts/",
        ]
        existing = {p.name for p in REFERENCES}
        for name in legacy:
            self.assertNotIn(name, existing, f"legacy PR-era file {name} must not return")
            self.assertNotIn(name, self.skill_text)

    # d85-4 — documented flags must exist in the script
    def test_documented_watcher_flags_exist(self):
        parser_flags = set(re.findall(r'"(--[a-z][a-z\-]+)"', self.watcher_text))
        docs = self.skill_text + "\n".join(p.read_text() for p in REFERENCES)
        for block in re.findall(r"```(?:bash)?\n(.*?)```", docs, re.S):
            if "ci-watch.py" not in block:
                continue
            # Only flags on the watcher's own (possibly continued) command
            # lines count; other tools may appear in the same block.
            in_watcher_command = False
            for line in block.splitlines():
                stripped = line.strip()
                if "ci-watch.py" in stripped:
                    in_watcher_command = True
                elif in_watcher_command and not stripped.startswith("--"):
                    in_watcher_command = False
                if not in_watcher_command:
                    continue
                for flag in re.findall(r"(--[a-z][a-z\-]+)", stripped):
                    self.assertIn(flag, parser_flags,
                                  f"doc uses unknown ci-watch.py flag {flag}")

    # d85-5 — documented exit contract matches the implementation
    def test_documented_exit_contract_matches_script(self):
        feedback = (SKILL_DIR / "references" / "feedback-loops.md").read_text()
        for verdict, code in [("success", 0), ("failure", 1), ("cancelled", 1),
                              ("timeout", 2), ("no-run", 2), ("probe-dead", 2),
                              ("superseded", 3)]:
            self.assertRegex(feedback, rf"`{verdict}`\s*\|\s*{code}",
                             f"feedback-loops.md must document {verdict} -> exit {code}")
            self.assertRegex(self.watcher_text, rf'"{verdict}":\s*{code}')

    # d85-3 — examples define their variables
    def test_diff_examples_define_base_and_head(self):
        for path in REFERENCES + [SKILL]:
            text = path.read_text()
            for block in re.findall(r"```(?:yaml|bash)\n(.*?)```", text, re.S):
                if '"$BASE...$HEAD"' in block and "git diff" in block:
                    defined = ("BASE:" in block and "HEAD:" in block) or \
                              ("BASE=" in block and "HEAD=" in block)
                    is_anti_example = "without proving where" in text.split(block)[-1][:400] \
                        or "broken example" in text.split(block)[0][-400:].lower()
                    self.assertTrue(defined or is_anti_example,
                                    f"{path.name}: $BASE/$HEAD used undefined outside anti-example")

    # d85-10 — consistent action pins, no silent downgrades
    def test_checkout_versions_are_consistent(self):
        versions = set()
        for path in REFERENCES + [SKILL]:
            versions.update(re.findall(r"actions/checkout@(v\d+)", path.read_text()))
        self.assertLessEqual(len(versions), 1,
                             f"inconsistent actions/checkout pins: {sorted(versions)}")

    # authorization framing must survive edits
    def test_analysis_is_not_authorization_is_front_loaded(self):
        head = self.skill_text[:4000]
        self.assertIn("## Analysis is not authorization", head)
        for gate in ["cancelling or re-running", "deleting caches", "deployments"]:
            self.assertIn(gate, self.skill_text)

    def test_near_misses_are_stated(self):
        for phrase in ["one-line YAML", "runtime performance", "delete or bypass required tests"]:
            self.assertIn(phrase, self.skill_text)

    def test_no_banned_directories_in_skill(self):
        for banned in ("evals", "__pycache__"):
            self.assertEqual(list(SKILL_DIR.rglob(banned)), [],
                             f"{banned} must not exist inside the packaged skill")


if __name__ == "__main__":
    unittest.main()
