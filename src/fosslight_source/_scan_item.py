#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import re
import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)
replace_word = ["-only", "-old-style", "-or-later", "licenseref-scancode-", "licenseref-"]
_notice_filename = ['licen[cs]e[s]?', 'notice[s]?', 'legal', 'copyright[s]?', 'copying*', 'patent[s]?', 'unlicen[cs]e', 'eula',
                    '[a,l]?gpl[-]?[1-3]?[.,-,_]?[0-1]?', 'mit', 'bsd[-]?[0-4]?', 'bsd[-]?[0-4][-]?clause[s]?',
                    'apache[-,_]?[1-2]?[.,-,_]?[0-2]?']
_exclude_filename = ["changelog", "config.guess", "config.sub", "changes", "ltmain.sh",
                     "configure", "configure.ac", "depcomp", "compile", "missing", "makefile"]
_exclude_extension = [".m4", ".in", ".po"]
_exclude_directory = ["test", "tests", "doc", "docs"]
_exclude_directory = [os.path.sep + dir_name +
                      os.path.sep for dir_name in _exclude_directory]
_exclude_directory.append("/.")
MAX_LICENSE_LENGTH = 200
MAX_LICENSE_TOTAL_LENGTH = 600
SUBSTRING_LICENSE_COMMENT = "Maximum character limit (License)"


class ScanItem:
    file = ""
    scanoss_reference = {}
    exclude = False
    is_license_text = False
    oss_name = ""
    oss_version = ""
    download_location = []
    matched_lines = ""  # Only for SCANOSS results
    fileURL = ""  # Only for SCANOSS results
    license_reference = ""

    def __init__(self, value):
        self.file = value
        self._copyright = []
        self._licenses = []
        self.download_location = []
        self.comment = ""
        self.exclude = False
        self.is_license_text = False

    def __del__(self):
        pass

    def __hash__(self):
        return hash(self.file)

    @property
    def copyright(self):
        return self._copyright

    @copyright.setter
    def copyright(self, value):
        self._copyright.extend(value)
        if len(self._copyright) > 0:
            self._copyright = list(set(self._copyright))

    @property
    def licenses(self):
        return self._licenses

    @licenses.setter
    def licenses(self, value):
        self._licenses.extend(value)
        if len(self._licenses) > 0:
            self._licenses = list(set(self._licenses))

    def get_file(self):
        return self.file

    def get_row_to_print(self):
        print_rows = []
        licenses = []
        max_length_exceed = False
        for lic in self.licenses:
            if len(lic) > MAX_LICENSE_LENGTH:
                lic = lic[:MAX_LICENSE_LENGTH]
                max_length_exceed = True
            licenses.append(lic)
        str_license = ",".join(licenses)
        if len(str_license) > MAX_LICENSE_TOTAL_LENGTH:
            max_length_exceed = True
            str_license = str_license[:MAX_LICENSE_TOTAL_LENGTH]

        if max_length_exceed:
            self.comment = f"{self.comment}/ {SUBSTRING_LICENSE_COMMENT}" if self.comment else SUBSTRING_LICENSE_COMMENT

        if not self.download_location:
            print_rows.append([self.file, self.oss_name, self.oss_version, str_license, "", "",
                               "\n".join(self.copyright), "Exclude" if self.exclude else "", self.comment,
                               self.license_reference])
        else:
            for url in self.download_location:
                print_rows.append([self.file, self.oss_name, self.oss_version, str_license, url, "",
                                   "\n".join(self.copyright), "Exclude" if self.exclude else "", self.comment,
                                   self.license_reference])
        return print_rows

    def __eq__(self, other):
        if type(other) == str:
            return self.file == other
        else:
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
    if os.path.splitext(filename)[1] in _exclude_extension:
        return True
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


def is_notice_file(file_path):
    pattern = r"({})(?<!w)".format("|".join(_notice_filename))
    file_path = file_path.lower()
    filename = os.path.basename(file_path)
    return bool(re.match(pattern, filename))
