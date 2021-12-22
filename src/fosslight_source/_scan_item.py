#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)
replace_word = ["-only", "-old-style", "-or-later", "licenseref-scancode-"]
_exclude_filename = ["changelog", "config.guess", "config.sub",
                     "config.h.in", "changes", "ltmain.sh",
                     "aclocal.m4", "configure", "configure.ac",
                     "depcomp", "compile", "missing", "libtool.m4",
                     "makefile"]
_exclude_directory = ["test", "tests", "doc", "docs"]
_exclude_directory = [os.path.sep + dir_name +
                      os.path.sep for dir_name in _exclude_directory]
_exclude_directory.append("/.")


class ScanItem:
    file = ""
    licenses = []
    copyright = ""
    exclude = False
    is_license_text = False
    oss_name = ""
    oss_version = ""
    download_location = ""
    matched_lines = ""
    fileURL = ""
    vendor = ""

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

    def set_oss_name(self, value):
        self.oss_name = value

    def set_oss_version(self, value):
        self.oss_version = value

    def set_download_location(self, value):
        self.download_location = value

    def set_matched_lines(self, value):
        self.matched_lines = value

    def set_fileURL(self, value):
        self.fileURL = value

    def set_vendor(self, value):
        self.vendor = value

    def get_row_to_print(self):
        print_rows = [self.file, self.oss_name, self.oss_version, ','.join(self.licenses), self.download_location, "",
                      ','.join(self.copyright),
                      "Exclude" if self.exclude else "",
                      self.comment]
        return print_rows

    def get_row_to_print_for_scanoss(self):
        print_rows = [self.file, self.oss_name, self.oss_version, ','.join(self.licenses), self.download_location, "",
                      ','.join(self.copyright),
                      "Exclude" if self.exclude else "",
                      self.comment, self.matched_lines, self.fileURL, self.vendor]
        return print_rows

    def merge_scan_item(self, other):
        """
        Merge two ScanItem instance into one.

        TODO: define how to merge comments and implement.
        """
        self.licenses = list(set(self.licenses + other.licenses))

        if len(self.copyright) > 0:
            self.copyright = list(set(self.copyright))

        if self.exclude and other.exclude:
            self.exclude = True
        else:
            self.exclude = False

        if not self.oss_name:
            self.oss_name = other.oss_name
        if not self.oss_version:
            self.oss_version = other.oss_version
        if not self.download_location:
            self.download_location = other.download_location
        if not self.matched_lines:
            self.matched_lines = other.matched_lines
        if not self.fileURL:
            self.fileURL = other.fileURL
        if not self.vendor:
            self.vendor = other.vendor

    def __eq__(self, other):
        return self.file == other.file


def is_exclude_dir(dir_path):
    if dir_path != "":
        dir_path = dir_path.lower()
        dir_path = dir_path if dir_path.endswith(
            os.path.sep) else dir_path + os.path.sep
        dir_path = dir_path if dir_path.startswith(
            os.path.sep) else os.path.sep + dir_path
        return any(dir_name in dir_path for dir_name in _exclude_directory)
    return False


def is_exclude_file(file_path, prev_dir=None, prev_dir_exclude_value=None):
    file_path = file_path.lower()
    filename = os.path.basename(file_path)
    if filename in _exclude_filename:
        return True

    dir_path = os.path.dirname(file_path)
    if prev_dir is not None:  # running ScanCode
        if dir_path == prev_dir:
            return prev_dir_exclude_value
        else:
            # There will be no execution of this else statement.
            # Because scancode json output results are sorted by path,
            # most of them will match the previous if statement.
            return is_exclude_dir(dir_path)
    else:  # running SCANOSS
        return is_exclude_dir(dir_path)
    return False
