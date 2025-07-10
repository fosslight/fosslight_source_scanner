#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import fosslight_util.constant as constant
from ._scan_item import SourceItem
from ._scan_item import is_exclude_file
from ._scan_item import replace_word
from typing import Tuple

logger = logging.getLogger(constant.LOGGER_NAME)
SCANOSS_INFO_HEADER = ['No', 'Source Path', 'Component Declared', 'SPDX Tag',
                       'File Header', 'License File', 'Scancode',
                       'Matched Rate (line number)', 'scanoss_fileURL']


def parsing_extraInfo(scanned_result: dict) -> list:
    scanoss_extra_info = []
    for scan_item in scanned_result:
        license_w_source = scan_item.scanoss_reference
        if scan_item.matched_lines:
            if license_w_source:
                extra_item = [scan_item.source_name_or_path, ','.join(license_w_source['component_declared']),
                              ','.join(license_w_source['file_spdx_tag']),
                              ','.join(license_w_source['file_header']),
                              ','.join(license_w_source['license_file']),
                              ','.join(license_w_source['scancode']),
                              scan_item.matched_lines, scan_item.fileURL]
            else:
                extra_item = [scan_item.source_name_or_path, '', '', '', '', '', scan_item.matched_lines, scan_item.fileURL]
            scanoss_extra_info.append(extra_item)
    scanoss_extra_info.insert(0, SCANOSS_INFO_HEADER)
    return scanoss_extra_info


def parsing_scanResult(scanoss_report: dict, path_to_scan: str = "", path_to_exclude: list = []) -> Tuple[bool, list]:
    scanoss_file_item = []
    abs_path_to_exclude = [os.path.abspath(os.path.join(path_to_scan, path)) for path in path_to_exclude]

    for file_path, findings in scanoss_report.items():
        abs_file_path = os.path.abspath(os.path.join(path_to_scan, file_path))
        if any(os.path.commonpath([abs_file_path, exclude_path]) == exclude_path for exclude_path in abs_path_to_exclude):
            continue
        result_item = SourceItem(file_path)

        if 'id' in findings[0]:
            if "none" == findings[0]['id']:
                continue

        if 'component' in findings[0]:
            result_item.oss_name = findings[0]['component']
        if 'version' in findings[0]:
            result_item.oss_version = findings[0]['version']
        if 'url' in findings[0]:
            result_item.download_location = list([findings[0]['url']])

        license_detected = []
        license_w_source = {"component_declared": [], "file_spdx_tag": [],
                            "file_header": [], "license_file": [], "scancode": []}
        if 'licenses' in findings[0]:
            for license in findings[0]['licenses']:

                license_lower = license['name'].lower()
                if license_lower.endswith('.'):
                    license_lower = license_lower[:-1]
                for word in replace_word:
                    if word in license_lower:
                        license_lower = license_lower.replace(word, "")
                license_detected.append(license_lower)

                if license['source'] not in license_w_source:
                    license_w_source[license['source']] = []
                license_w_source[license['source']].append(license['name'])
            if len(license_detected) > 0:
                result_item.licenses = license_detected
                result_item.scanoss_reference = license_w_source

        if is_exclude_file(file_path):
            result_item.exclude = True

        if 'file_url' in findings[0]:
            result_item.fileURL = findings[0]['file_url']
        if 'matched' in findings[0]:
            if 'lines' in findings[0]:
                result_item.matched_lines = f"{findings[0]['matched']} ({findings[0]['lines']})"
            else:
                result_item.matched_lines = f"{findings[0]['matched']}"
        elif 'lines' in findings[0]:
            result_item.matched_lines = f"({findings[0]['lines']})"

        scanoss_file_item.append(result_item)

    return scanoss_file_item
