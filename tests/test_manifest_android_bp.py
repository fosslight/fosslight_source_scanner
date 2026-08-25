# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for Android.bp manifest marker handling."""

from unittest.mock import patch

from fosslight_source._scan_item import (
    SourceItem,
    extracts_manifest_license,
    is_manifest_file,
    is_manifest_marker_file,
)
from fosslight_source.cli import merge_results, metadata_collector


def test_is_manifest_marker_file_recognizes_android_bp():
    assert is_manifest_marker_file("/tmp/module/Android.bp") is True
    assert is_manifest_marker_file("/tmp/module/android.bp") is True
    assert is_manifest_marker_file("/tmp/module/package.json") is False


def test_is_manifest_file_includes_android_bp_marker():
    assert is_manifest_file("/tmp/module/Android.bp") is True
    assert extracts_manifest_license("/tmp/module/Android.bp") is False
    assert extracts_manifest_license("/tmp/module/package.json") is True


def test_metadata_collector_marks_android_bp_without_license_extraction(tmp_path):
    android_bp = tmp_path / "Android.bp"
    android_bp.write_text('license { name: "test_license" }', encoding="utf-8")
    package_json = tmp_path / "package.json"
    package_json.write_text('{"license": "MIT"}', encoding="utf-8")

    with patch("fosslight_source.cli.get_manifest_licenses", return_value=["MIT"]) as mock_get:
        spdx_downloads, manifest_licenses, manifest_markers = metadata_collector(str(tmp_path), set())

    assert spdx_downloads == {}
    assert manifest_licenses == {"package.json": ["MIT"]}
    assert manifest_markers == {"Android.bp"}
    mock_get.assert_called_once_with(str(package_json))


def test_merge_results_sets_manifest_flag_without_overwriting_scancode_licenses():
    scancode_item = SourceItem("carrois-gothic-sc/Android.bp")
    scancode_item.licenses = ["Apache-2.0", "MIT", "BSD"]

    merged, _, _, _ = merge_results(
        scancode_result=[scancode_item],
        manifest_markers={"carrois-gothic-sc/Android.bp"},
    )

    assert len(merged) == 1
    assert merged[0].is_manifest_file is True
    assert merged[0].licenses == ["Apache-2.0", "MIT", "BSD"]
