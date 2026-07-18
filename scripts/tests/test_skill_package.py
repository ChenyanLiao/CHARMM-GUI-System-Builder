import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_skill_package import (  # noqa: E402
    CANONICAL_NAME,
    EXPECTED_VERSION,
    REQUIRED_PLATFORMS,
    parse_frontmatter,
    validate_skill,
)


class CrossAgentSkillPackageTests(unittest.TestCase):
    def test_repository_content_validation_passes(self):
        report = validate_skill(ROOT)
        self.assertEqual(report["status"], "pass", report["errors"])
        self.assertTrue(report["agent_skills_spec_compatible"])
        self.assertFalse(report["production_ready"])
        self.assertTrue(report["no_mdrun"])

    def test_frontmatter_is_agent_skills_compatible(self):
        frontmatter, text = parse_frontmatter(ROOT / "SKILL.md")
        self.assertEqual(frontmatter["name"], CANONICAL_NAME)
        self.assertEqual(frontmatter["license"], "AGPL-3.0-only")
        self.assertEqual(frontmatter["metadata"]["version"], EXPECTED_VERSION)
        self.assertLessEqual(len(frontmatter["description"]), 1024)
        self.assertLessEqual(len(frontmatter["compatibility"]), 500)
        self.assertLessEqual(len(text.splitlines()), 500)

    def test_strict_validation_passes_in_canonical_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / CANONICAL_NAME
            shutil.copytree(
                ROOT,
                destination,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            report = validate_skill(destination, strict_directory_name=True)
        self.assertEqual(report["status"], "pass", report["errors"])
        self.assertTrue(report["directory_name_valid"])

    def test_all_platform_adapters_are_declared(self):
        data = json.loads((ROOT / "metadata/compatibility.json").read_text())
        self.assertEqual(set(data["platforms"]), REQUIRED_PLATFORMS)
        for platform in data["platforms"].values():
            self.assertTrue((ROOT / platform["adapter"]).is_file())

    def test_versions_are_consistent(self):
        provenance = json.loads((ROOT / "metadata/provenance.json").read_text())
        compatibility = json.loads(
            (ROOT / "metadata/compatibility.json").read_text()
        )
        self.assertEqual(provenance["version"], EXPECTED_VERSION)
        self.assertEqual(compatibility["skill"]["version"], EXPECTED_VERSION)
        self.assertIn(
            f'version: "{EXPECTED_VERSION}"',
            (ROOT / "CITATION.cff").read_text(),
        )

    def test_install_docs_use_lowercase_canonical_directory(self):
        for name in (
            "INSTALL_CODEX.md",
            "INSTALL_CLAUDE.md",
            "INSTALL_OPENCLAW.md",
            "INSTALL_HERMES.md",
        ):
            text = (ROOT / "docs" / name).read_text()
            self.assertIn(CANONICAL_NAME, text, name)

    def test_core_does_not_define_platform_specific_permission_fields(self):
        frontmatter, _ = parse_frontmatter(ROOT / "SKILL.md")
        self.assertNotIn("disable-model-invocation", frontmatter)
        self.assertNotIn("platforms", frontmatter)
        self.assertNotIn("allowed-tools", frontmatter)


if __name__ == "__main__":
    unittest.main()
