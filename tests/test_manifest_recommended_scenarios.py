# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Recommended verification scenarios for Android.bp manifest handling."""

import json
from pathlib import Path

from fosslight_source._parsing_scancode_file_item import parsing_scancode
from fosslight_source._scan_item import SourceItem
from fosslight_source.cli import merge_results, metadata_collector

REPO_ROOT = Path(__file__).resolve().parents[1]
CARROIS_SCAN_ROOT = REPO_ROOT / "temp" / "carrois-gothic-sc"
CARROIS_SCANCODE_JSON = REPO_ROOT / "temp" / "scancode_raw_result.json"


def test_scenario1_carrois_android_bp_keeps_scancode_licenses():
    """carrois-gothic-sc/Android.bp: is_manifest_file=True, ScanCode licenses preserved."""
    assert CARROIS_SCAN_ROOT.is_dir(), f"missing fixture dir: {CARROIS_SCAN_ROOT}"
    assert CARROIS_SCANCODE_JSON.is_file(), f"missing fixture json: {CARROIS_SCANCODE_JSON}"

    scancode_files = json.loads(CARROIS_SCANCODE_JSON.read_text(encoding="utf-8"))["files"]
    success, scancode_result, _messages, _license_list = parsing_scancode(scancode_files)
    assert success is True

    android_bp = next(item for item in scancode_result if item.source_name_or_path.endswith("Android.bp"))
    scancode_licenses = list(android_bp.licenses)
    assert scancode_licenses, "expected ScanCode licenses on Android.bp"

    _, manifest_licenses = metadata_collector(str(CARROIS_SCAN_ROOT), set())
    assert "Android.bp" in manifest_licenses
    assert manifest_licenses["Android.bp"] == []

    merged, _, _, _ = merge_results(
        scancode_result=list(scancode_result),
        manifest_licenses=manifest_licenses,
    )
    merged_android_bp = next(item for item in merged if item.source_name_or_path.endswith("Android.bp"))

    assert merged_android_bp.is_manifest_file is True
    assert merged_android_bp.licenses == scancode_licenses


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


def test_scenario3_android_bp_not_in_scancode_no_row_non_ui():
    """Android.bp absent from ScanCode: no row in non-UI mode."""
    manifest = {"module/Android.bp": []}

    merged_non_ui, _, _, _ = merge_results(scancode_result=[], manifest_licenses=manifest, ui_mode=False)
    assert merged_non_ui == []


def test_scenario3_android_bp_not_in_scancode_ui_keeps_empty_row():
    """Android.bp absent from ScanCode: UI mode still creates manifest row."""
    manifest = {"module/Android.bp": []}

    merged_ui, _, _, _ = merge_results(scancode_result=[], manifest_licenses=manifest, ui_mode=True)

    assert len(merged_ui) == 1
    assert merged_ui[0].source_name_or_path == "module/Android.bp"
    assert merged_ui[0].is_manifest_file is True
    assert merged_ui[0].licenses == []
