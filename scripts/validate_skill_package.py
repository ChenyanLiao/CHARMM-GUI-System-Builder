#!/usr/bin/env python3
"""Validate the portable CHARMM-GUI System Builder skill package."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any


CANONICAL_NAME = "charmm-gui-system-builder"
EXPECTED_VERSION = "1.1.1"
ALLOWED_FIELDS = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
    "compatibility",
}
REQUIRED_METADATA = {
    "author": "Liao Chenyan",
    "version": EXPECTED_VERSION,
    "canonical_repository": (
        "https://github.com/ChenyanLiao/CHARMM-GUI-System-Builder"
    ),
    "origin_id": "io.github.ChenyanLiao.charmm-gui-system-builder",
}
REQUIRED_PATHS = (
    "adapters/codex.md",
    "adapters/claude-code.md",
    "adapters/openclaw.md",
    "adapters/hermes.md",
    "adapters/generic-agent-skills.md",
    "docs/INSTALL_CODEX.md",
    "docs/INSTALL_CLAUDE.md",
    "docs/INSTALL_OPENCLAW.md",
    "docs/INSTALL_HERMES.md",
    "docs/CAPABILITY_MATRIX.md",
    "docs/CROSS_AGENT_ARCHITECTURE.md",
    "metadata/compatibility.json",
)
REQUIRED_PLATFORMS = {
    "codex",
    "claude_code",
    "openclaw",
    "hermes",
    "generic_agent_skills",
}


def _scalar(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if value[0:1] in {"'", '"'}:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise ValueError(f"invalid quoted YAML scalar: {value}") from exc
        if not isinstance(parsed, str):
            raise ValueError(f"frontmatter scalar must be a string: {value}")
        return parsed
    return value


def parse_frontmatter(skill_md: Path) -> tuple[dict[str, Any], str]:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md must start with closed YAML frontmatter")

    data: dict[str, Any] = {}
    active_map: str | None = None
    for line_number, raw in enumerate(match.group(1).splitlines(), start=2):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw:
            raise ValueError(f"frontmatter line {line_number} contains a tab")
        if raw.startswith("  "):
            if active_map != "metadata":
                raise ValueError(
                    f"unsupported nested frontmatter at line {line_number}"
                )
            key, separator, value = raw.strip().partition(":")
            if not separator or not key or not value.strip():
                raise ValueError(f"invalid metadata entry at line {line_number}")
            data["metadata"][key] = _scalar(value)
            continue
        if raw.startswith(" "):
            raise ValueError(f"invalid indentation at frontmatter line {line_number}")

        key, separator, value = raw.partition(":")
        if not separator or not key.strip():
            raise ValueError(f"invalid frontmatter entry at line {line_number}")
        key = key.strip()
        if key in data:
            raise ValueError(f"duplicate frontmatter field: {key}")
        if key == "metadata":
            if value.strip():
                raise ValueError("metadata must be a one-level YAML mapping")
            data[key] = {}
            active_map = key
        else:
            data[key] = _scalar(value)
            active_map = None
    return data, text


def _local_markdown_links(text: str) -> list[str]:
    links: list[str] = []
    for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
        target = target.strip().strip("<>").split("#", 1)[0]
        if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            continue
        links.append(target)
    return links


def _read_optional_json(
    path: Path,
    label: str,
    errors: list[str],
) -> tuple[bool, Any]:
    if not path.is_file():
        return False, None
    try:
        return True, json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid {label}: {exc}")
        return False, None


def validate_skill(root: Path, strict_directory_name: bool = False) -> dict[str, Any]:
    root = root.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    skill_md = root / "SKILL.md"

    if not root.is_dir():
        errors.append(f"not a directory: {root}")
        return _report(root, strict_directory_name, errors, warnings)
    if not skill_md.is_file():
        errors.append("missing required file: SKILL.md")
        return _report(root, strict_directory_name, errors, warnings)

    try:
        frontmatter, skill_text = parse_frontmatter(skill_md)
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append(str(exc))
        return _report(root, strict_directory_name, errors, warnings)

    extra_fields = sorted(set(frontmatter) - ALLOWED_FIELDS)
    if extra_fields:
        errors.append(f"unexpected frontmatter fields: {', '.join(extra_fields)}")

    name = frontmatter.get("name")
    if name != CANONICAL_NAME:
        errors.append(f"name must be {CANONICAL_NAME!r}, got {name!r}")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        errors.append("name must contain lowercase letters, digits, and single hyphens")
    if isinstance(name, str) and len(name) > 64:
        errors.append("name exceeds the 64-character Agent Skills limit")

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("description must be a non-empty string")
    elif len(description) > 1024:
        errors.append("description exceeds the 1024-character Agent Skills limit")

    compatibility = frontmatter.get("compatibility")
    if not isinstance(compatibility, str):
        errors.append("compatibility must be a string")
    elif len(compatibility) > 500:
        errors.append("compatibility exceeds the 500-character Agent Skills limit")

    if frontmatter.get("license") != "AGPL-3.0-only":
        errors.append("license must be AGPL-3.0-only")

    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("metadata must be a mapping")
    else:
        for key, expected in REQUIRED_METADATA.items():
            if metadata.get(key) != expected:
                errors.append(
                    f"metadata.{key} must be {expected!r}, got {metadata.get(key)!r}"
                )

    if strict_directory_name and root.name != CANONICAL_NAME:
        errors.append(
            f"directory name {root.name!r} must match {CANONICAL_NAME!r}"
        )
    elif not strict_directory_name and root.name != CANONICAL_NAME:
        warnings.append(
            "directory-name check skipped for repository display name; installed "
            "copies must use charmm-gui-system-builder"
        )

    line_count = len(skill_text.splitlines())
    if line_count > 500:
        errors.append(f"SKILL.md has {line_count} lines; keep it at or below 500")

    for relative in REQUIRED_PATHS:
        if not (root / relative).is_file():
            errors.append(f"missing required cross-agent file: {relative}")

    for target in _local_markdown_links(skill_text):
        if not (root / target).exists():
            errors.append(f"broken local SKILL.md link: {target}")

    compatibility_loaded, compatibility_data = _read_optional_json(
        root / "metadata/compatibility.json",
        "metadata/compatibility.json",
        errors,
    )
    if compatibility_loaded:
        skill = compatibility_data.get("skill", {})
        if skill.get("name") != CANONICAL_NAME:
            errors.append("compatibility metadata skill name is inconsistent")
        if skill.get("version") != EXPECTED_VERSION:
            errors.append("compatibility metadata version is inconsistent")
        platforms = set(compatibility_data.get("platforms", {}))
        if platforms != REQUIRED_PLATFORMS:
            errors.append(
                "compatibility metadata platforms differ from the required set"
            )
        requirements = compatibility_data.get("core_requirements", {})
        if requirements.get("production_ready_default") is not False:
            errors.append("production_ready_default must remain false")
        if requirements.get("no_mdrun") is not True:
            errors.append("no_mdrun must remain true")

    provenance_loaded, provenance = _read_optional_json(
        root / "metadata/provenance.json",
        "metadata/provenance.json",
        errors,
    )
    if provenance_loaded and provenance.get("version") != EXPECTED_VERSION:
        errors.append("provenance version is inconsistent")

    cff_path = root / "CITATION.cff"
    if cff_path.is_file():
        cff_text = cff_path.read_text(encoding="utf-8")
        if f'version: "{EXPECTED_VERSION}"' not in cff_text:
            errors.append("CITATION.cff version is inconsistent")

    return _report(
        root,
        strict_directory_name,
        errors,
        warnings,
        line_count=line_count,
        frontmatter=frontmatter,
    )


def _report(
    root: Path,
    strict_directory_name: bool,
    errors: list[str],
    warnings: list[str],
    *,
    line_count: int | None = None,
    frontmatter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": "pass" if not errors else "fail",
        "agent_skills_spec_compatible": not errors,
        "skill_root": str(root),
        "canonical_name": CANONICAL_NAME,
        "version": (frontmatter or {}).get("metadata", {}).get("version"),
        "strict_directory_name": strict_directory_name,
        "directory_name_valid": root.name == CANONICAL_NAME,
        "skill_md_line_count": line_count,
        "errors": errors,
        "warnings": warnings,
        "production_ready": False,
        "no_mdrun": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--strict-directory-name", action="store_true")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    report = validate_skill(args.skill_root, args.strict_directory_name)
    rendered = json.dumps(report, indent=2, ensure_ascii=True)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
