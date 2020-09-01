#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: LicenseRef-LGE-Proprietary

_replace_word = ["-only", "-old-style", "-or-later"]


class ScanCodeItem:
    file = ""
    licenses = []
    copyright = ""

    def __init__(self, value):
        self.file = value
        self.copyright = []
        self.licenses = []
        self.comment = ""

    def __del__(self):
        pass

    def set_comment(self, value):
        self.comment = value

    def set_file(self, value):
        self.file = value

    def set_copyright(self, value):
        self.copyright.extend(value)
        if len(self.copyright) > 0:
            self.copyright = list(set(self.copyright))

    def set_licenses(self, value):
        self.licenses.extend(value)
        if len(self.licenses) > 0:
            self.licenses = list(set(self.licenses))

    def get_row_to_print(self):
        print_rows = [self.file, "", "", ','.join(self.licenses), "", "", ','.join(self.copyright), "", "",
                      self.comment]
        return print_rows


def parsing_file_item(scancode_file_list):
    rc = True
    scancode_file_item = []

    for file in scancode_file_list:
        try:
            is_binary = False
            is_dir = False
            if "is_binary" in file:
                is_binary = file["is_binary"]
            if "type" in file:
                is_dir = file["type"] == "directory"
            if not is_binary and not is_dir:
                file_path = file["path"]
                licenses = file["licenses"]
                copyright_list = file["copyrights"]

                result_item = ScanCodeItem(file_path)
                copyright_value_list = [x["value"] for x in copyright_list]
                result_item.set_copyright(copyright_value_list)

                license_expression_list = file["license_expressions"]
                license_expression_list = [x.lower() for x in license_expression_list]

                license_detected = []
                for lic_item in licenses:
                    license_value = ""
                    key = lic_item["key"].lower()
                    spdx = lic_item["spdx_license_key"].lower()
                    if key in license_expression_list:
                        license_expression_list.remove(key)
                    if spdx != "":
                        license_value = spdx
                    else:
                        license_value = key
                    if license_value != "":
                        for word in _replace_word:
                            if word in license_value:
                                license_value = license_value.replace(word, "")
                        license_detected.append(license_value)
                if len(license_detected) > 0:
                    result_item.set_licenses(license_detected)

                    if len(license_expression_list) > 0:
                        license_expression_list = list(set(license_expression_list))
                        result_item.set_comment(','.join(license_expression_list))
                    scancode_file_item.append(result_item)
        except Exception as ex:
            print(str(ex))
            rc = False

    return rc, scancode_file_item
