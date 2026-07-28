"""Static contract checks for the Avrea 0.1.6 reference split.

These tests do not execute `avr`; they verify that the committed docs stay
aligned with the pinned release manifest and do not drift into unreleased or
invented command surfaces.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[1]
FIXTURE = TESTS_DIR / "fixtures" / "avr-0.1.6-command-manifest.json"
AVREA_DIR = REPO_ROOT / "skills" / "ci-cd-optimize" / "references" / "avrea"
SKILL = REPO_ROOT / "skills" / "ci-cd-optimize" / "SKILL.md"


def slug(command: str) -> str:
    return command.replace(" ", " ").strip()


class AvrReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(FIXTURE.read_text())
        cls.core = (AVREA_DIR / "cli-core-reference.md").read_text()
        cls.admin = (AVREA_DIR / "cli-admin-reference.md").read_text()
        cls.auth = (AVREA_DIR / "cli-auth-and-portability.md").read_text()
        cls.evidence = (AVREA_DIR / "cli-evidence.md").read_text()
        cls.skill = SKILL.read_text()
        cls.all_text = "\n".join([cls.core, cls.admin, cls.auth, cls.evidence])

    def test_release_identity_is_consistent(self):
        m = self.manifest
        for text in (self.core, self.admin, self.auth):
            self.assertIn(m["package"], text)
            self.assertIn(m["executable"], text)
            self.assertIn(m["version"], text)
            self.assertIn(m["release_tag"], text)
            self.assertIn(m["release_sha"], text)

    def test_skill_routes_all_avrea_references(self):
        for name in [
            "references/avrea/cli-evidence.md",
            "references/avrea/cli-core-reference.md",
            "references/avrea/cli-admin-reference.md",
            "references/avrea/cli-auth-and-portability.md",
            "references/avrea/platform-and-runners.md",
            "references/avrea/caching.md",
        ]:
            self.assertIn(name, self.skill)

    def test_every_released_top_level_command_is_documented(self):
        commands = self.manifest["commands"].keys()
        missing = [cmd for cmd in commands if f"avr {cmd}" not in self.all_text]
        self.assertEqual(missing, [], f"missing released top-level commands: {missing}")

    def test_every_released_subcommand_is_documented(self):
        missing = []
        for cmd, info in self.manifest["commands"].items():
            subcommands = info.get("subcommands", {})
            if isinstance(subcommands, list):
                continue
            for sub in subcommands:
                needle = f"avr {cmd} {sub}"
                if needle not in self.all_text:
                    missing.append(f"{cmd} {sub}")
        self.assertEqual(missing, [], f"missing released subcommands: {missing}")

    def test_unreleased_commands_are_quarantined(self):
        for cmd in self.manifest["unreleased_commands"]:
            self.assertIn(cmd, self.core + self.admin + self.auth,
                          f"unreleased command {cmd} should be named in the quarantine section")
        runnable_examples = re.findall(r"```(?:bash)?\n(.*?)```", self.all_text, re.S)
        for block in runnable_examples:
            for cmd in self.manifest["unreleased_commands"]:
                self.assertNotIn(f"avr {cmd}", block,
                                 f"unreleased command {cmd} leaked into runnable example")

    def test_absent_capabilities_are_stated(self):
        for capability in self.manifest["known_absent_capabilities"]:
            self.assertIn(capability, self.all_text)

    def test_no_invented_artifact_or_cost_commands(self):
        forbidden = [
            "avr artifact", "avr artifacts", "avr cost", "avr costs",
            "avr workflow artifacts", "avr run artifacts"
        ]
        for token in forbidden:
            self.assertNotIn(token, self.all_text)

    def test_mutation_classes_cover_mutating_commands(self):
        for cmd, info in self.manifest["commands"].items():
            subcommands = info.get("subcommands", {})
            if isinstance(subcommands, list):
                continue
            for sub, meta in subcommands.items():
                if meta["class"] in {
                    "remote-repo-mutation", "remote-org-mutation", "remote-scope-mutation",
                    "financial-mutation", "live-runner-access", "local-config-write"
                }:
                    needle = f"avr {cmd} {sub}"
                    self.assertIn(needle, self.all_text,
                                  f"mutating command {needle} must be documented")

    def test_show_token_is_flagged_as_sensitive(self):
        self.assertIn("--show-token", self.admin)
        self.assertIn("never use `--show-token`", self.admin.lower())

    def test_auth_env_precedence_is_documented(self):
        for token in ["AVR_HOST", "AVR_TOKEN", "AVR_ORG", "AVR_REPO", "AVR_CONFIG_DIR"]:
            self.assertIn(token, self.auth)
        self.assertIn("Only a remote named `origin` is auto-detected", self.auth)

    def test_evidence_file_stays_workflow_oriented(self):
        self.assertIn("## Step 1 — orient before measuring", self.evidence)
        self.assertIn("Keep syntax and command-surface questions out of this file", self.evidence)
        self.assertIn("Prefer the exact-SHA watcher", self.evidence)

    def test_core_reference_covers_exit_codes(self):
        for code in ["0", "1", "2", "4"]:
            self.assertRegex(self.core, rf"\| `{code}`?\s*\|".replace("`?", "`"))

    def test_released_firewall_vm_flag_not_job_flag(self):
        self.assertIn("--vm", self.admin)
        # --job for flow-summaries is unreleased; it may appear only as quarantine text.
        combined = self.core + self.admin
        self.assertIn("firewall flow-summaries --job", combined)
        for block in re.findall(r"```(?:bash)?\n(.*?)```", combined, re.S):
            self.assertNotIn("flow-summaries --job", block)


if __name__ == "__main__":
    unittest.main()
