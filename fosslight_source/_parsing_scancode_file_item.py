#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: LicenseRef-LGE-Proprietary

import os
import logging

logger = logging.getLogger(__name__)
_replace_word = ["-only", "-old-style", "-or-later", "licenseref-scancode-"]
_exclude_filename = ["changelog", "config.guess", "config.sub", "config.h.in", "changes", "ltmain.sh", "aclocal.m4", "configure", "configure.ac", "depcomp", "compile", "missing", "libtool.m4"]
_exclude_directory = ["test", "tests", "doc", "docs"]


class ScanCodeItem:
    file = ""
    licenses = []
    copyright = ""
    exclude = False

    def __init__(self, value):
        self.file = value
        self.copyright = []
        self.licenses = []
        self.comment = ""
        self.exclude = False

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

    def set_exclude(self, value):
        self.exclude = value

    def get_row_to_print(self):
        print_rows = [self.file, "", "", ','.join(self.licenses), "", "", ','.join(self.copyright), "", "Exclude" if self.exclude else "",
                      self.comment]
        return print_rows


def check_file_path_to_exclude(file_path, result_item):
    file_path = file_path.lower()

    filename = os.path.basename(file_path)

    if filename in _exclude_filename:
        result_item.set_exclude(True)
        return

    directory = file_path.split(os.path.sep)
    
    for dir_value in directory:
        if dir_value in _exclude_directory:
            result_item.set_exclude(True)
            break

    return


def parsing_file_item(scancode_file_list):
    rc = True
    scancode_file_item = []
    logger.debug("FILE COUNT:"+str(len(scancode_file_list)))
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
                
                check_file_path_to_exclude(file_path, result_item)

                copyright_value_list = [x["value"] for x in copyright_list]
                result_item.set_copyright(copyright_value_list)

                license_expression_list = file["license_expressions"]
                if len(license_expression_list) > 0 :
                    license_expression_list = [x.lower() for x in license_expression_list if x is not None]

                license_detected = []
                if licenses is None or licenses == "":
                    continue
                for lic_item in licenses:
                    license_value = ""
                    key = lic_item["key"]
                    spdx = lic_item["spdx_license_key"]
                    #logger.debug("LICENSE_KEY:"+str(key)+",SPDX:"+str(spdx))
                    if spdx is not None and spdx != "":
                        spdx = spdx.lower()
                    if key is not None and key != "":
                        key = key.lower()
                    if key in license_expression_list:
                        license_expression_list.remove(key)
                    if spdx != "":
                        license_value = spdx
                    else:
                        license_value = key

                    if license_value is not None and license_value != "":
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
            logger.warn("Error Parsing item-"+str(ex))
            rc = False

    return rc, scancode_file_item
