#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.
"""Inspect a CHARMM-GUI download by content without extracting it."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from datetime import datetime
from pathlib import Path, PurePosixPath


REQUIRED_EXTENSIONS = (".gro", ".top", ".itp", ".mdp")
PARTIAL_SUFFIXES = (".crdownload", ".part", ".partial", ".download")
ARCHIVE_SUFFIXES = (".tar", ".tgz", ".tar.gz", ".tbz", ".tbz2", ".txz")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compression_from_magic(prefix: bytes, tar_readable: bool) -> str:
    if prefix.startswith(b"\x1f\x8b"):
        return "gzip"
    if prefix.startswith(b"BZh"):
        return "bzip2"
    if prefix.startswith(b"\xfd7zXZ\x00"):
        return "xz"
    if tar_readable:
        return "uncompressed_tar"
    return "none"


def looks_like_html(prefix: bytes) -> bool:
    sample = prefix.lstrip().lower()
    markers = (b"<!doctype html", b"<html", b"<head", b"<title>charmm-gui")
    return any(sample.startswith(marker) for marker in markers) or (
        b"<html" in sample[:4096] and b"charmm-gui" in sample[:65536]
    )


def is_partial_name(path: Path) -> bool:
    lower = path.name.lower()
    return any(lower.endswith(suffix) for suffix in PARTIAL_SUFFIXES)


def has_archive_name(path: Path) -> bool:
    lower = path.name.lower()
    return any(lower.endswith(suffix) for suffix in ARCHIVE_SUFFIXES)


def unsafe_path(name: str) -> bool:
    path = PurePosixPath(name)
    return path.is_absolute() or ".." in path.parts


def unsafe_member_reasons(member: tarfile.TarInfo) -> list[str]:
    reasons: list[str] = []
    if unsafe_path(member.name):
        reasons.append("unsafe_member_path")
    if member.issym() or member.islnk():
        if unsafe_path(member.linkname):
            reasons.append("unsafe_link_target")
    if member.ischr() or member.isblk() or member.isfifo():
        reasons.append("unsafe_special_file")
    return reasons


def empty_counts() -> dict[str, int]:
    return {ext: 0 for ext in REQUIRED_EXTENSIONS}


def base_report(path: Path) -> dict[str, object]:
    return {
        "artifact": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "sensitive_content_recorded": False,
        "production_ready": False,
        "no_mdrun": True,
        "archive_member_count_definition": "all tar members including directories and links",
        "archive_regular_file_count_definition": "regular-file tar members only",
    }


def classify_non_archive(
    report: dict[str, object],
    *,
    classification: str,
    action: str,
) -> dict[str, object]:
    report.update(
        archive_member_count=0,
        archive_regular_file_count=0,
        archive_file_count=0,
        total_uncompressed_bytes=0,
        largest_member_bytes=0,
        extension_counts=empty_counts(),
        required_extension_counts=empty_counts(),
        required_gromacs_extensions_present=False,
        gromacs_entry_count=0,
        unsafe_member_count=0,
        unsafe_members=[],
        classification=classification,
        recommended_next_action=action,
    )
    return report


def inspect_artifact(path: Path) -> dict[str, object]:
    path = path.expanduser().resolve()
    report = base_report(path)
    if not path.exists() or not path.is_file():
        report.update(
            size_bytes=None,
            modified_time=None,
            sha256=None,
            html_like=False,
            partial_name=is_partial_name(path),
            tar_readable=False,
            compression="none",
        )
        return classify_non_archive(
            report,
            classification="missing",
            action="LOCATE_OR_REDOWNLOAD_FINAL_PACKAGE",
        )

    stat = path.stat()
    size = stat.st_size
    with path.open("rb") as handle:
        prefix = handle.read(65536)
    html_like = looks_like_html(prefix)
    partial_name = is_partial_name(path)
    tar_readable = False
    tar_error_type: str | None = None
    if size:
        try:
            tar_readable = tarfile.is_tarfile(path)
        except (OSError, tarfile.TarError) as exc:
            tar_error_type = type(exc).__name__
    compression = compression_from_magic(prefix, tar_readable)
    report.update(
        size_bytes=size,
        modified_time=datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(),
        sha256=sha256(path),
        html_like=html_like,
        partial_name=partial_name,
        tar_readable=tar_readable,
        compression=compression,
        tar_error_type=tar_error_type,
    )

    if partial_name:
        return classify_non_archive(
            report,
            classification="partial",
            action="RESUME_LATEST_BROWSER_DOWNLOAD_OR_WAIT",
        )
    if html_like:
        return classify_non_archive(
            report,
            classification="invalid_html",
            action="REDOWNLOAD_FROM_AUTHENTICATED_FINAL_PAGE",
        )
    if not tar_readable:
        archive_like = has_archive_name(path) or compression != "none"
        return classify_non_archive(
            report,
            classification="corrupt_archive" if archive_like else "invalid_non_archive",
            action="REDOWNLOAD_FROM_AUTHENTICATED_FINAL_PAGE",
        )

    try:
        with tarfile.open(path, "r:*") as archive:
            members = archive.getmembers()
    except (OSError, tarfile.TarError) as exc:
        report["tar_readable"] = False
        report["tar_error_type"] = type(exc).__name__
        return classify_non_archive(
            report,
            classification="corrupt_archive",
            action="REDOWNLOAD_FROM_AUTHENTICATED_FINAL_PAGE",
        )

    regular = [member for member in members if member.isfile()]
    names = [member.name for member in regular]
    extension_counts = {
        ext: sum(name.lower().endswith(ext) for name in names)
        for ext in REQUIRED_EXTENSIONS
    }
    gromacs_count = sum(
        "/gromacs/" in f"/{name.lower().lstrip('/')}" for name in names
    )
    unsafe_rows = []
    for member in members:
        reasons = unsafe_member_reasons(member)
        if reasons:
            unsafe_rows.append({"member": member.name, "reasons": reasons})
    has_required = all(extension_counts[ext] > 0 for ext in REQUIRED_EXTENSIONS)
    if unsafe_rows:
        classification = "unsafe_archive"
        action = "QUARANTINE_AND_DO_NOT_EXTRACT"
    elif has_required and gromacs_count > 0:
        classification = "valid_final_candidate"
        action = "VALIDATE_FINAL_PACKAGE"
    else:
        classification = "intermediate"
        action = "VERIFY_JOB_STAGE_OR_SELECTED_OUTPUT_ENGINE"
    report.update(
        archive_member_count=len(members),
        archive_regular_file_count=len(regular),
        archive_file_count=len(regular),
        total_uncompressed_bytes=sum(member.size for member in regular),
        largest_member_bytes=max((member.size for member in regular), default=0),
        extension_counts=extension_counts,
        required_extension_counts=extension_counts,
        required_gromacs_extensions_present=has_required,
        gromacs_entry_count=gromacs_count,
        unsafe_member_count=len(unsafe_rows),
        unsafe_members=unsafe_rows[:20],
        classification=classification,
        recommended_next_action=action,
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    report = inspect_artifact(args.artifact)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered)
        print(args.json_out)
    else:
        print(rendered, end="")

    return {
        "valid_final_candidate": 0,
        "intermediate": 3,
        "invalid_html": 4,
        "partial": 5,
        "unsafe_archive": 6,
        "corrupt_archive": 7,
    }.get(str(report["classification"]), 8)


if __name__ == "__main__":
    raise SystemExit(main())
