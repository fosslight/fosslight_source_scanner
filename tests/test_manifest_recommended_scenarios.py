# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Recommended verification scenarios for Android.bp manifest handling."""

from fosslight_source._scan_item import SourceItem
from fosslight_source.cli import merge_results


def test_scenario1_android_bp_keeps_scancode_licenses():
    """Android.bp with ScanCode licenses: is_manifest_file=True, licenses preserved."""
    scancode_item = SourceItem("Android.bp")
    scancode_item.licenses = ["Apache-2.0", "unknown-license-reference", "BSD", "MIT", "OFL"]

    merged, _, _, _ = merge_results(
        scancode_result=[scancode_item],
        manifest_licenses={"Android.bp": []},
    )

    assert len(merged) == 1
    assert merged[0].is_manifest_file is True
    assert merged[0].licenses == ["Apache-2.0", "unknown-license-reference", "BSD", "MIT", "OFL"]


def test_scenario2_package_json_manifest_fail_keeps_scancode_licenses():
    """package.json manifest extraction fails but ScanCode row exists: manifest flag only."""
    scancode_item = SourceItem("app/package.json")
    scancode_item.licenses = ["Apache-2.0"]

    merged, _, _, _ = merge_results(
        scancode_result=[scancode_item],
        manifest_licenses={"app/package.json": []},
    )

    assert len(merged) == 1
    assert merged[0].is_manifest_file is True
    assert merged[0].licenses == ["Apache-2.0"]


def test_scenario3_android_bp_from_spdx_marks_manifest_without_new_row():
    """Android.bp added by spdx merge: manifest flag on existing item, no duplicate row."""
    spdx_item = SourceItem("module/Android.bp")
    spdx_item.download_location = ["https://example.com/repo"]

    merged, _, _, _ = merge_results(
        scancode_result=[spdx_item],
        manifest_licenses={"module/Android.bp": []},
    )

    assert len(merged) == 1
    assert merged[0].is_manifest_file is True
    assert merged[0].download_location == ["https://example.com/repo"]
    assert merged[0].licenses == []


def test_scenario3_android_bp_not_in_result_no_row_non_ui():
    """Android.bp absent from merge result: no row in non-UI mode."""
    merged_non_ui, _, _, _ = merge_results(
        scancode_result=[],
        manifest_licenses={"module/Android.bp": []},
        ui_mode=False,
    )
    assert merged_non_ui == []


def test_scenario3_android_bp_not_in_result_ui_keeps_empty_row():
    """Android.bp absent from merge result: UI mode still creates manifest row."""
    merged_ui, _, _, _ = merge_results(
        scancode_result=[],
        manifest_licenses={"module/Android.bp": []},
        ui_mode=True,
    )

    assert len(merged_ui) == 1
    assert merged_ui[0].source_name_or_path == "module/Android.bp"
    assert merged_ui[0].is_manifest_file is True
    assert merged_ui[0].licenses == []
