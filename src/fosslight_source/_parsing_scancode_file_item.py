#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import re
import fosslight_util.constant as constant
from ._license_matched import MatchedLicense

logger = logging.getLogger(constant.LOGGER_NAME)
_replace_word = ["-only", "-old-style", "-or-later", "licenseref-scancode-"]
_exclude_filename = ["changelog", "config.guess", "config.sub",
                     "config.h.in", "changes", "ltmain.sh",
                     "aclocal.m4", "configure", "configure.ac",
                     "depcomp", "compile", "missing", "libtool.m4",
                     "makefile"]
_exclude_directory = ["test", "tests", "doc", "docs"]
_exclude_directory = [os.path.sep + dir_name +
                      os.path.sep for dir_name in _exclude_directory]
_exclude_directory.append("/.")


class ScanCodeItem:
    file = ""
    licenses = []
    copyright = ""
    exclude = False
    is_license_text = False

    def __init__(self, value):
        self.file = value
        self.copyright = []
        self.licenses = []
        self.comment = ""
        self.exclude = False
        self.is_license_text = False

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

    def set_is_license_text(self, value):
        self.is_license_text = value

    def get_row_to_print(self):
        print_rows = [self.file, "", "", ','.join(self.licenses), "", "",
                      ','.join(self.copyright),
                      "Exclude" if self.exclude else "",
                      self.comment]
        return print_rows


def is_exclude_dir(dir_path):
    if dir_path != "":
        dir_path = dir_path.lower()
        dir_path = dir_path if dir_path.endswith(
            os.path.sep) else dir_path + os.path.sep
        dir_path = dir_path if dir_path.startswith(
            os.path.sep) else os.path.sep + dir_path
        return any(dir_name in dir_path for dir_name in _exclude_directory)
    return False


def is_exclude_file(file_path, prev_dir, prev_dir_exclude_value):
    file_path = file_path.lower()
    filename = os.path.basename(file_path)
    if filename in _exclude_filename:
        return True

    dir_path = os.path.dirname(file_path)
    if dir_path == prev_dir:
        return prev_dir_exclude_value
    else:
        # There will be no execution of this else statement.
        # Because scancode json output results are sorted by path,
        # most of them will match the previous if statement.
        return is_exclude_dir(dir_path)
    return False


def get_error_from_header(header_item):
    has_error = False
    str_error = ""
    key_error = "errors"

    try:
        for header in header_item:
            if key_error in header:
                errors = header[key_error]
                error_cnt = len(errors)
                if error_cnt > 0:
                    has_error = True
                    str_error = '{}...({})'.format(errors[0], error_cnt)
                    break
    except Exception as ex:
        logger.debug("error_parsing_header:"+str(ex))
    return has_error, str_error


def parsing_file_item(scancode_file_list, has_error, need_matched_license=False):

    rc = True
    scancode_file_item = []
    license_list = {}  # Key :[license]+[matched_text], value: MatchedLicense()
    msg = "TOTAL FILE COUNT: " + str(len(scancode_file_list)) + "\n"

    prev_dir = ""
    prev_dir_value = False
    regex = re.compile(r'licenseref-(\S)+')

    for file in scancode_file_list:
        try:
            is_binary = False
            is_dir = False
            file_path = file["path"]

            if "is_binary" in file:
                is_binary = file["is_binary"]
            if "type" in file:
                is_dir = file["type"] == "directory"
                if is_dir:
                    prev_dir_value = is_exclude_dir(file_path)
                    prev_dir = file_path

            if not is_binary and not is_dir:
                licenses = file["licenses"]
                copyright_list = file["copyrights"]

                result_item = ScanCodeItem(file_path)

                if has_error and "scan_errors" in file:
                    error_msg = file["scan_errors"]
                    if len(error_msg) > 0:
                        logger.debug("test_msg" + file_path + ":" + str(error_msg))
                        result_item.set_comment(",".join(error_msg))
                        scancode_file_item.append(result_item)
                        continue

                copyright_value_list = [x["value"] for x in copyright_list]
                result_item.set_copyright(copyright_value_list)

                # Set the license value
                license_detected = []
                if licenses is None or licenses == "":
                    continue

                license_expression_list = file["license_expressions"]
                if len(license_expression_list) > 0:
                    license_expression_list = [
                        x.lower() for x in license_expression_list
                        if x is not None]

                for lic_item in licenses:
                    license_value = ""
                    key = lic_item["key"]
                    spdx = lic_item["spdx_license_key"]
                    # logger.debug("LICENSE_KEY:"+str(key)+",SPDX:"+str(spdx))

                    if key is not None and key != "":
                        key = key.lower()
                        license_value = key
                        if key in license_expression_list:
                            license_expression_list.remove(key)
                    if spdx is not None and spdx != "":
                        # Print SPDX instead of Key.
                        license_value = spdx.lower()

                    if license_value != "":
                        if key == "unknown-spdx":
                            try:
                                if "matched_text" in lic_item:
                                    matched_txt = lic_item["matched_text"].lower()
                                    matched = regex.search(matched_txt)
                                    if matched:
                                        license_value = str(matched.group())
                            except Exception:
                                pass

                        for word in _replace_word:
                            if word in license_value:
                                license_value = license_value.replace(word, "")
                        license_detected.append(license_value)

                        # Add matched licenses
                        if need_matched_license and "category" in lic_item:
                            lic_category = lic_item["category"]
                            if "matched_text" in lic_item:
                                lic_matched_text = lic_item["matched_text"]
                                lic_matched_key = license_value + lic_matched_text
                                if lic_matched_key in license_list:
                                    license_list[lic_matched_key].set_files(file_path)
                                else:
                                    lic_info = MatchedLicense(license_value, lic_category, lic_matched_text, file_path)
                                    license_list[lic_matched_key] = lic_info

                    matched_rule = lic_item["matched_rule"]
                    if matched_rule["is_license_text"]:
                        result_item.set_is_license_text(True)

                if len(license_detected) > 0:
                    result_item.set_licenses(license_detected)

                    if len(license_expression_list) > 0:
                        license_expression_list = list(
                            set(license_expression_list))
                        result_item.set_comment(
                            ','.join(license_expression_list))

                    if is_exclude_file(file_path, prev_dir, prev_dir_value):
                        result_item.set_exclude(True)
                    scancode_file_item.append(result_item)

        except Exception as ex:
            msg += "* Error Parsing item:"+str(ex)
            rc = False
            logger.debug(msg)

    return rc, scancode_file_item, msg.strip(), license_list
