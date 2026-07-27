# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for composer.json manifest license extraction."""

from fosslight_source._scan_item import is_manifest_file
from fosslight_source.run_manifest_extractor import (
    get_licenses_from_composer_json,
    get_manifest_licenses,
)


def test_is_manifest_file_recognizes_composer_json():
    assert is_manifest_file("/tmp/project/composer.json") is True
    assert is_manifest_file("/tmp/project/Composer.JSON") is True


def test_get_licenses_from_composer_json_string(tmp_path):
    path = tmp_path / "composer.json"
    path.write_text('{"name": "acme/demo", "license": "MIT"}', encoding="utf-8")
    assert get_licenses_from_composer_json(str(path)) == ["MIT"]


def test_get_licenses_from_composer_json_array(tmp_path):
    path = tmp_path / "composer.json"
    path.write_text(
        '{"name": "acme/demo", "license": ["LGPL-2.1-only", "GPL-3.0-or-later"]}',
        encoding="utf-8",
    )
    assert get_licenses_from_composer_json(str(path)) == [
        "LGPL-2.1-only",
        "GPL-3.0-or-later",
    ]


def test_get_licenses_from_composer_json_spdx_expression(tmp_path):
    path = tmp_path / "composer.json"
    path.write_text(
        '{"name": "acme/demo", "license": "(MIT OR Apache-2.0)"}',
        encoding="utf-8",
    )
    assert get_licenses_from_composer_json(str(path)) == ["MIT", "Apache-2.0"]


def test_get_manifest_licenses_dispatches_composer_json(tmp_path):
    path = tmp_path / "composer.json"
    path.write_text('{"license": "BSD-3-Clause"}', encoding="utf-8")
    assert get_manifest_licenses(str(path)) == ["BSD-3-Clause"]


def test_get_licenses_from_composer_json_missing_license(tmp_path):
    path = tmp_path / "composer.json"
    path.write_text('{"name": "acme/demo"}', encoding="utf-8")
    assert get_licenses_from_composer_json(str(path)) == []
