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

    def test_v21_capability_and_maturity_registries_are_declared(self):
        capabilities = json.loads(
            (ROOT / "rules/capabilities/official_api.json").read_text()
        )
        official = {
            item["capability_id"]
            for item in capabilities["capabilities"]
            if item["route"] == "official_api"
        }
        self.assertEqual(
            official,
            {
                "api.login",
                "api.check_status",
                "api.download",
                "api.quick_bilayer",
            },
        )
        maturity = json.loads(
            (ROOT / "community/MODULE_MATURITY_REGISTRY.json").read_text()
        )
        self.assertTrue(maturity["modules"])
        self.assertFalse(maturity["production_ready"])
        self.assertTrue(maturity["no_mdrun"])
        self.assertNotIn("Stable", {row["maturity"] for row in maturity["modules"]})

    def test_v21_and_legacy_state_templates_are_both_preserved(self):
        current = json.loads((ROOT / "templates/RUN_STATE_TEMPLATE.json").read_text())
        legacy = json.loads(
            (ROOT / "templates/legacy/RUN_STATE_V6_TEMPLATE.json").read_text()
        )
        self.assertEqual(current["schema_version"], "2.1")
        self.assertEqual(legacy["schema_version"], 6)
        self.assertFalse(current["production_ready"])
        self.assertTrue(current["no_mdrun"])

    def test_runtime_capability_manifest_covers_route_critical_tools(self):
        manifest = json.loads(
            (ROOT / "templates/RUNTIME_CAPABILITY_MANIFEST_TEMPLATE.json").read_text()
        )
        self.assertEqual(manifest["schema_version"], "2.1")
        required = {
            "file_read",
            "file_write_run_directory_only",
            "command_execution",
            "browser_control",
            "page_state_capture",
            "screenshots",
            "file_upload",
            "download_control",
            "native_dialog_control",
            "official_api_network",
            "os_credential_vault",
            "durable_wait_resume",
        }
        self.assertEqual(set(manifest["capabilities"]), required)
        self.assertFalse(manifest["production_ready"])
        self.assertTrue(manifest["no_mdrun"])

    def test_credential_policy_forbids_plaintext_and_persistent_tokens(self):
        data = json.loads((ROOT / "metadata/compatibility.json").read_text())
        requirements = data["core_requirements"]
        self.assertTrue(requirements["manual_authentication_default"])
        self.assertTrue(requirements["plaintext_credentials_forbidden"])
        self.assertEqual(requirements["api_token_persistence"], "memory_only")

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

    def test_invalid_optional_metadata_json_is_reported(self):
        for relative in (
            "metadata/compatibility.json",
            "metadata/provenance.json",
        ):
            with (
                self.subTest(relative=relative),
                tempfile.TemporaryDirectory() as temp,
            ):
                destination = Path(temp) / CANONICAL_NAME
                shutil.copytree(
                    ROOT,
                    destination,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
                )
                (destination / relative).write_text("{")
                report = validate_skill(destination)

            self.assertEqual(report["status"], "fail")
            self.assertTrue(
                any(error.startswith(f"invalid {relative}:") for error in report["errors"]),
                report["errors"],
            )

    def test_invalid_rule_risk_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / CANONICAL_NAME
            shutil.copytree(
                ROOT,
                destination,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            rule_path = destination / "rules/membrane_builder/v2.1.json"
            data = json.loads(rule_path.read_text())
            data["parameters"][0]["risk_level"] = "SilentDefault"
            rule_path.write_text(json.dumps(data))
            report = validate_skill(destination)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(
            any("invalid risk_level" in error for error in report["errors"]),
            report["errors"],
        )


if __name__ == "__main__":
    unittest.main()
