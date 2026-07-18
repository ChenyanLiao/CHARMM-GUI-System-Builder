#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(SCRIPTS))

from fixture_factory import create_download_archive  # noqa: E402
from inspect_charmmgui_download import inspect_artifact  # noqa: E402


class DownloadInspectorTests(unittest.TestCase):
    def test_6034_byte_html_disguised_as_tgz_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "download.tgz"
            prefix = b"<html><head><title>CHARMM-GUI</title></head><body>error</body></html>"
            path.write_bytes(prefix + b" " * (6034 - len(prefix)))
            report = inspect_artifact(path)
        self.assertEqual(report["size_bytes"], 6034)
        self.assertEqual(report["classification"], "invalid_html")
        self.assertFalse(report["tar_readable"])
        self.assertFalse(report["sensitive_content_recorded"])

    def test_gzip_tgz_is_accepted_by_magic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = create_download_archive(Path(tmp) / "download.tgz", gzip=True)
            report = inspect_artifact(path)
        self.assertEqual(report["classification"], "valid_final_candidate")
        self.assertEqual(report["compression"], "gzip")

    def test_safari_uncompressed_tar_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = create_download_archive(Path(tmp) / "charmm-gui.tar")
            report = inspect_artifact(path)
        self.assertEqual(report["classification"], "valid_final_candidate")
        self.assertEqual(report["compression"], "uncompressed_tar")

    def test_tgz_suffix_with_uncompressed_tar_content_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = create_download_archive(Path(tmp) / "download.tgz")
            report = inspect_artifact(path)
        self.assertEqual(report["classification"], "valid_final_candidate")
        self.assertEqual(report["compression"], "uncompressed_tar")

    def test_corrupt_tar_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.tar"
            path.write_bytes(b"not a tar archive")
            report = inspect_artifact(path)
        self.assertEqual(report["classification"], "corrupt_archive")

    def test_crdownload_is_partial_even_if_named_like_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "download.tgz.crdownload"
            path.write_bytes(b"partial transfer")
            report = inspect_artifact(path)
        self.assertEqual(report["classification"], "partial")
        self.assertEqual(report["recommended_next_action"], "RESUME_LATEST_BROWSER_DOWNLOAD_OR_WAIT")

    def test_pdb_reader_archive_is_intermediate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = create_download_archive(
                Path(tmp) / "pdbreader.tgz", gzip=True, include_gromacs=False
            )
            report = inspect_artifact(path)
        self.assertEqual(report["classification"], "intermediate")
        self.assertFalse(report["required_gromacs_extensions_present"])

    def test_path_traversal_member_is_unsafe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = create_download_archive(
                Path(tmp) / "unsafe.tar", unsafe_name="../../escape.txt"
            )
            report = inspect_artifact(path)
        self.assertEqual(report["classification"], "unsafe_archive")
        self.assertEqual(report["unsafe_member_count"], 1)

    def test_member_count_semantics_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = create_download_archive(Path(tmp) / "download.tar")
            report = inspect_artifact(path)
        self.assertIn("all tar members", report["archive_member_count_definition"])
        self.assertIn("regular-file", report["archive_regular_file_count_definition"])
        self.assertEqual(report["archive_member_count"], report["archive_regular_file_count"])


if __name__ == "__main__":
    unittest.main()
