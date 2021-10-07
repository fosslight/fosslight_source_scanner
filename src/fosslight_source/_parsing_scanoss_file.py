#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

#import os
import logging
import re
import fosslight_util.constant as constant
#from ._license_matched import MatchedLicense
from ._scan_item import ScanItem
from ._scan_item import is_exclude_dir
from ._scan_item import is_exclude_file

logger = logging.getLogger(constant.LOGGER_NAME)

def parsing_scanResult(scanoss_report, need_matched_license=False):
    rc = True
    scanoss_file_item = []
    license_list = {}  # Key :[license]+[matched_text], value: MatchedLicense()
    msg = "TOTAL FILE COUNT: " + str(len(scanoss_report)) + "\n"

    prev_dir = ""
    prev_dir_value = False
    regex = re.compile(r'licenseref-(\S)+')

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
        copyright_detected = []
        if 'licenses' in findings[0]:
            for license in findings[0]['licenses']:
                license_detected.append(license['name'].lower())
            if len(license_detected) > 0:
                result_item.set_licenses(license_detected)
        if 'copyrights' in findings[0]:
            for copyright in findings[0]['copyrights']:
                copyright_detected.append(copyright['name'])
            if len(copyright_detected) > 0:
                result_item.set_copyright(copyright_detected)

        if is_exclude_file(file_path):
            result_item.set_exclude(True)

        comment = ""
        comment += "Match Type : " + findings[0]['id'] + ", "
        if 'vendor' in findings[0]:
            comment += "Vendor : " + findings[0]['vendor'] + ", "
        if 'file_url' in findings[0]:
            comment += "File URL : " + findings[0]['file_url'] + ", "
        if 'matched' in findings[0]:
            comment += "Matched : " + findings[0]['matched'] + ", "
        if 'lines' in findings[0]:
            comment += "Lines : " + findings[0]['lines']
        result_item.set_comment(comment)

        scanoss_file_item.append(result_item)

    return rc, scanoss_file_item
