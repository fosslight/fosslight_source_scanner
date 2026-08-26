# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for pyproject.toml manifest license extraction."""

from fosslight_source.run_manifest_extractor import get_licenses_from_pyproject_toml


def test_pep621_license_string(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(
        '[project]\nname = "demo"\nlicense = "MIT"\n',
        encoding="utf-8",
    )
    assert get_licenses_from_pyproject_toml(str(path)) == ["MIT"]


def test_pep621_license_text_table(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(
        '[project]\nname = "demo"\nlicense = {text = "MIT"}\n',
        encoding="utf-8",
    )
    assert get_licenses_from_pyproject_toml(str(path)) == ["MIT"]


def test_pep621_license_file_returns_empty(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(
        '[project]\nname = "demo"\nlicense = {file = "LICENSE"}\n',
        encoding="utf-8",
    )
    assert get_licenses_from_pyproject_toml(str(path)) == []


def test_legacy_poetry_license(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(
        '[tool.poetry]\nname = "demo"\nlicense = "Apache-2.0"\n',
        encoding="utf-8",
    )
    assert get_licenses_from_pyproject_toml(str(path)) == ["Apache-2.0"]


def test_project_license_file_does_not_fall_back_to_poetry(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(
        '[project]\nname = "demo"\nlicense = {file = "LICENSE"}\n\n'
        '[tool.poetry]\nname = "demo"\nlicense = "MIT"\n',
        encoding="utf-8",
    )
    assert get_licenses_from_pyproject_toml(str(path)) == []
