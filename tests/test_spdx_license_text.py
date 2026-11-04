#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import pytest
from spdx_tools.spdx.parser.parse_anything import parse_file
from spdx_tools.spdx.validation.document_validator import validate_full_spdx_document

from fosslight_source import cli as source_cli
from fosslight_source._license_matched import MatchedLicense
from fosslight_source._scan_item import SourceItem


@pytest.mark.parametrize("matched_text, expected_text", [
    ('    license="BSD",', '    license="BSD",'),
    ("", "BSD"),
])
def test_spdx_uses_scancode_matched_text_without_reference_sheet(
    tmp_path, monkeypatch, matched_text, expected_text
):
    project = tmp_path / "project"
    project.mkdir()
    (project / "setup.py").write_text('license="BSD"\n', encoding="utf-8")
    output = tmp_path / "reports"
    source_item = SourceItem("setup.py")
    source_item.checksum = "a" * 40
    source_item.licenses = ["BSD-3-Clause"]
    matched_license = MatchedLicense("BSD-3-Clause", "", matched_text, "setup.py")
    license_list = {matched_license.license + matched_license.matched_text: matched_license}
    received_need_matched_text = []

    def run_scancode(*args, **kwargs):
        received_need_matched_text.append(args[5])
        return True, "True", [source_item], license_list

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(source_cli, "run_scan", run_scancode)

    success, message, scan_item, _licenses, _scanoss_result = source_cli.run_scanners(
        str(project), str(output), selected_scanner="scancode", formats=["spdx-json"],
        print_matched_text=False, correct_mode=False, all_exclude_mode=([], [], set(), 1),
        hide_progress=True,
    )

    assert success, message
    assert received_need_matched_text == [True]
    assert "scancode_reference" not in scan_item.external_sheets
    assert scan_item.file_items[source_cli.PKG_NAME][0].oss_items[0].license == ["BSD"]
    document = parse_file(str(next(output.glob("*.json"))))
    assert validate_full_spdx_document(document) == []
    assert document.extracted_licensing_info[0].license_name == "BSD"
    assert document.extracted_licensing_info[0].extracted_text == expected_text
    assert {str(value) for value in document.files[0].license_info_in_file} == {"LicenseRef-BSD"}
