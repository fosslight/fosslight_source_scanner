#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)
HEADER = ['No', 'Category', 'License',
          'Matched Text', 'File Count', 'Files']
LOW_PRIORITY = ['Permissive', 'Public Domain']


class MatchedLicense:
    license = ""
    files = []
    category = ""
    matched_text = ""
    priority = 0

    def __init__(self, lic, category, text, file):
        self.files = [file]
        self.license = lic
        self.matched_text = text
        self.set_category(category)

    def __del__(self):
        pass

    def set_license(self, value):
        self.license = value

    def set_files(self, value):
        if value not in self.files:
            self.files.append(value)

    def set_category(self, value):
        self.category = value
        if value in LOW_PRIORITY:
            self.priority = 1
        else:
            self.priority = 0

    def set_matched_text(self, value):
        self.matched_text = value

    def get_row_to_print(self):
        print_rows = [self.category, self.license, self.matched_text, str(len(self.files)), ','.join(self.files)]
        return print_rows


def get_license_list_to_print(license_list):
    license_items = license_list.values()
    license_items = sorted(license_items, key=lambda row: (row.priority, row.category, row.license))
    license_rows = [lic_item.get_row_to_print() for lic_item in license_items]
    license_rows.insert(0, HEADER)
    return license_rows
