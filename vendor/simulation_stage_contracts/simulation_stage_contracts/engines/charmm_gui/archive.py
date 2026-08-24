from __future__ import annotations

import tarfile
from datetime import datetime
from pathlib import Path, PurePosixPath

from ...canonicalization import sha256_file


REQUIRED_EXTENSIONS = (".gro", ".top", ".itp", ".mdp")
PARTIAL_SUFFIXES = (".crdownload", ".part", ".partial", ".download")
ARCHIVE_SUFFIXES = (".tar", ".tgz", ".tar.gz", ".tbz", ".tbz2", ".txz")


def _compression(prefix: bytes, tar_readable: bool) -> str:
    if prefix.startswith(b"\x1f\x8b"):
        return "gzip"
    if prefix.startswith(b"BZh"):
        return "bzip2"
    if prefix.startswith(b"\xfd7zXZ\x00"):
        return "xz"
    return "uncompressed_tar" if tar_readable else "none"


def _looks_like_html(prefix: bytes) -> bool:
    sample = prefix.lstrip().lower()
    return any(sample.startswith(marker) for marker in (b"<!doctype html", b"<html", b"<head")) or b"<html" in sample[:4096]


def _unsafe_path(value: str) -> bool:
    path = PurePosixPath(value)
    return path.is_absolute() or ".." in path.parts


def _unsafe_reasons(member: tarfile.TarInfo) -> list[str]:
    reasons: list[str] = []
    if _unsafe_path(member.name):
        reasons.append("unsafe_member_path")
    if (member.issym() or member.islnk()) and _unsafe_path(member.linkname):
        reasons.append("unsafe_link_target")
    if member.ischr() or member.isblk() or member.isfifo():
        reasons.append("unsafe_special_file")
    return reasons


def inspect_archive(path: Path) -> dict:
    path = path.expanduser().resolve()
    report = {
        "artifact": str(path),
        "exists": path.is_file(),
        "production_ready": False,
        "no_mdrun": True,
        "archive_member_count_definition": "all tar members including directories and links",
        "archive_regular_file_count_definition": "regular-file tar members only",
    }
    if not path.is_file():
        return {**report, "classification": "missing", "recommended_next_action": "LOCATE_OR_REDOWNLOAD_FINAL_PACKAGE"}

    stat = path.stat()
    prefix = path.read_bytes()[:65536]
    partial = any(path.name.lower().endswith(suffix) for suffix in PARTIAL_SUFFIXES)
    html = _looks_like_html(prefix)
    try:
        readable = bool(stat.st_size) and tarfile.is_tarfile(path)
    except (OSError, tarfile.TarError):
        readable = False
    compression = _compression(prefix, readable)
    report.update(
        size_bytes=stat.st_size,
        modified_time=datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(),
        sha256=sha256_file(path),
        html_like=html,
        partial_name=partial,
        tar_readable=readable,
        compression=compression,
    )
    if partial:
        return {**report, "classification": "partial", "recommended_next_action": "RESUME_LATEST_BROWSER_DOWNLOAD_OR_WAIT"}
    if html:
        return {**report, "classification": "invalid_html", "recommended_next_action": "REDOWNLOAD_FROM_AUTHENTICATED_FINAL_PAGE"}
    if not readable:
        archive_like = any(path.name.lower().endswith(suffix) for suffix in ARCHIVE_SUFFIXES) or compression != "none"
        return {**report, "classification": "corrupt_archive" if archive_like else "invalid_non_archive", "recommended_next_action": "REDOWNLOAD_FROM_AUTHENTICATED_FINAL_PAGE"}

    with tarfile.open(path, "r:*") as archive:
        members = archive.getmembers()
    regular = [member for member in members if member.isfile()]
    names = [member.name for member in regular]
    extension_counts = {ext: sum(name.lower().endswith(ext) for name in names) for ext in REQUIRED_EXTENSIONS}
    unsafe = [
        {"member": member.name, "reasons": reasons}
        for member in members
        if (reasons := _unsafe_reasons(member))
    ]
    gromacs_entries = sum("/gromacs/" in f"/{name.lower().lstrip('/')}" for name in names)
    has_required = all(extension_counts.values())
    if unsafe:
        classification, action = "unsafe_archive", "QUARANTINE_AND_DO_NOT_EXTRACT"
    elif has_required and gromacs_entries:
        classification, action = "valid_final_candidate", "VALIDATE_FINAL_PACKAGE"
    else:
        classification, action = "intermediate", "VERIFY_JOB_STAGE_OR_SELECTED_OUTPUT_ENGINE"
    return {
        **report,
        "archive_member_count": len(members),
        "archive_regular_file_count": len(regular),
        "total_uncompressed_bytes": sum(member.size for member in regular),
        "largest_member_bytes": max((member.size for member in regular), default=0),
        "required_extension_counts": extension_counts,
        "required_gromacs_extensions_present": has_required,
        "gromacs_entry_count": gromacs_entries,
        "unsafe_member_count": len(unsafe),
        "unsafe_members": unsafe[:20],
        "classification": classification,
        "recommended_next_action": action,
    }


def read_text_member(path: Path, suffix: str, max_bytes: int = 250_000_000) -> tuple[str | None, str]:
    with tarfile.open(path, "r:*") as archive:
        matches = sorted(
            (member for member in archive.getmembers() if member.isfile() and member.name.endswith(suffix)),
            key=lambda member: member.name,
        )
        if not matches:
            return None, ""
        member = matches[0]
        if member.size > max_bytes:
            return member.name, ""
        handle = archive.extractfile(member)
        return (member.name, handle.read().decode("utf-8", errors="replace")) if handle else (member.name, "")
