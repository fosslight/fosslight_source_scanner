#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)
HEADER = ['No', 'License', 'Matched Text',
          'File Count', 'Files']
LOW_PRIORITY = ['Permissive', 'Public Domain']


class MatchedLicense:
    license = ""
    files = []
    category = ""
    matched_text = ""
    priority = 0

    def __init__(self, lic: str, category: str, text: str, file: str) -> None:
        self.files = [file]
        self.license = lic
        self.matched_text = text
        self.set_category(category)

    def __del__(self) -> None:
        pass

    def set_license(self, value: str) -> None:
        self.license = value

    def set_files(self, value: str) -> None:
        if value not in self.files:
            self.files.append(value)

    def set_category(self, value: str) -> None:
        self.category = value
        if value in LOW_PRIORITY:
            self.priority = 1
        else:
            self.priority = 0

    def set_matched_text(self, value: str) -> None:
        self.matched_text = value

    def get_row_to_print(self) -> list:
        return [self.license, self.matched_text, str(len(self.files)), ','.join(self.files)]


def get_license_list_to_print(license_list: dict) -> list:
    license_items = sorted(
        license_list.values(),
        key=lambda row: (row.priority, row.category, row.license),
    )
    license_rows = [lic_item.get_row_to_print() for lic_item in license_items]
    license_rows.insert(0, HEADER)
    return license_rows
