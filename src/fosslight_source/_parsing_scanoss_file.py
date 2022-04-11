#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import fosslight_util.constant as constant
from ._scan_item import ScanItem
from ._scan_item import is_exclude_file

logger = logging.getLogger(constant.LOGGER_NAME)
SCANOSS_INFO_HEADER = ['No', 'Source Name or Path', 'Component Declared', 'SPDX Tag',
                       'File Header', 'License File', 'Scancode',
                       'scanoss_matched_lines', 'scanoss_fileURL']


def parsing_extraInfo(scanned_result):
    scanoss_extra_info = []
    for scan_item in scanned_result:
        extra_item = scan_item.get_extra_info_row_for_scanoss()
        scanoss_extra_info.append(extra_item)
    scanoss_extra_info.insert(0, SCANOSS_INFO_HEADER)
    return scanoss_extra_info


def parsing_scanResult(scanoss_report):
    scanoss_file_item = []

    for file_path, findings in scanoss_report.items():
        result_item = ScanItem(file_path)
        if 'id' in findings[0]:
            if "none" == findings[0]['id']:
                continue

        if 'component' in findings[0]:
            result_item.set_oss_name(findings[0]['component'])
        if 'version' in findings[0]:
            result_item.set_oss_version(findings[0]['version'])
        if 'url' in findings[0]:
            result_item.set_download_location(findings[0]['url'])

        license_detected = []
        license_w_source = {}
        copyright_detected = []
        if 'licenses' in findings[0]:
            for license in findings[0]['licenses']:
                license_detected.append(license['name'].lower())
                if license['source'] not in license_w_source:
                    license_w_source[license['source']] = []
                license_w_source[license['source']].append(license['name'])
            if len(license_detected) > 0:
                result_item.set_licenses(license_detected)
                result_item.set_license_w_source(license_w_source)
        if 'copyrights' in findings[0]:
            for copyright in findings[0]['copyrights']:
                copyright_detected.append(copyright['name'])
            if len(copyright_detected) > 0:
                result_item.set_copyright(copyright_detected)

        if is_exclude_file(file_path):
            result_item.set_exclude(True)

        if 'vendor' in findings[0]:
            result_item.set_vendor(findings[0]['vendor'])
        if 'file_url' in findings[0]:
            result_item.set_fileURL(findings[0]['file_url'])
        if 'matched' in findings[0]:
            if 'lines' in findings[0]:
                result_item.set_matched_lines(f"{findings[0]['matched']} ({findings[0]['lines']})")
            else:
                result_item.set_matched_lines(f"{findings[0]['matched']}")
        elif 'lines' in findings[0]:
            result_item.set_matched_lines(f"({findings[0]['lines']})")

        scanoss_file_item.append(result_item)

    return scanoss_file_item
