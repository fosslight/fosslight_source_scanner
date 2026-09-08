# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for setup.cfg manifest license extraction."""

from fosslight_source._scan_item import SourceItem
from fosslight_source.cli import merge_results
from fosslight_source.run_manifest_extractor import get_licenses_from_setup_cfg


def test_setup_cfg_spdx_license(tmp_path):
    path = tmp_path / "setup.cfg"
    path.write_text("[metadata]\nname = demo\nlicense = MIT\n", encoding="utf-8")
    assert get_licenses_from_setup_cfg(str(path)) == ["MIT"]


def test_setup_cfg_license_filename_returns_empty(tmp_path):
    path = tmp_path / "setup.cfg"
    path.write_text("[metadata]\nname = demo\nlicense = LICENSE\n", encoding="utf-8")
    assert get_licenses_from_setup_cfg(str(path)) == []


def test_setup_cfg_license_filename_case_insensitive(tmp_path):
    path = tmp_path / "setup.cfg"
    path.write_text("[metadata]\nname = demo\nlicense = License\n", encoding="utf-8")
    assert get_licenses_from_setup_cfg(str(path)) == []


def test_setup_cfg_license_filename_keeps_scancode_licenses(tmp_path):
    path = tmp_path / "setup.cfg"
    path.write_text("[metadata]\nname = demo\nlicense = LICENSE\n", encoding="utf-8")
    assert get_licenses_from_setup_cfg(str(path)) == []

    scancode_item = SourceItem("pkg/setup.cfg")
    scancode_item.licenses = ["Apache-2.0"]
    merged, _, _, _ = merge_results(
        scancode_result=[scancode_item],
        manifest_licenses={"pkg/setup.cfg": []},
    )
    assert merged[0].is_manifest_file is True
    assert merged[0].licenses == ["Apache-2.0"]
