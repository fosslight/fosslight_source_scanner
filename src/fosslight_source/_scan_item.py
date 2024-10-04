#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import re
import fosslight_util.constant as constant
from fosslight_util.oss_item import FileItem, OssItem, get_checksum_sha1

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


class SourceItem(FileItem):

    def __init__(self, value: str) -> None:
        super().__init__("")
        self.source_name_or_path = value
        self.is_license_text = False
        self.license_reference = ""
        self.scanoss_reference = {}
        self.matched_lines = ""  # Only for SCANOSS results
        self.fileURL = ""  # Only for SCANOSS results
        self.download_location = []
        self.copyright = []
        self._licenses = []
        self.oss_name = ""
        self.oss_version = ""

        self.checksum = get_checksum_sha1(value)

    def __del__(self) -> None:
        pass

    def __hash__(self) -> int:
        return hash(self.file)

    @property
    def licenses(self) -> list:
        return self._licenses

    @licenses.setter
    def licenses(self, value: list) -> None:
        if value:
            max_length_exceed = False
            for new_lic in value:
                if new_lic:
                    if len(new_lic) > MAX_LICENSE_LENGTH:
                        new_lic = new_lic[:MAX_LICENSE_LENGTH]
                        max_length_exceed = True
                    if new_lic not in self._licenses:
                        self._licenses.append(new_lic)
                        if len(",".join(self._licenses)) > MAX_LICENSE_TOTAL_LENGTH:
                            self._licenses.remove(new_lic)
                            max_length_exceed = True
                            break
            if max_length_exceed and (SUBSTRING_LICENSE_COMMENT not in self.comment):
                self.comment = f"{self.comment}/ {SUBSTRING_LICENSE_COMMENT}" if self.comment else SUBSTRING_LICENSE_COMMENT

    def set_oss_item(self) -> None:
        self.oss_items = []
        if self.download_location:
            for url in self.download_location:
                item = OssItem(self.oss_name, self.oss_version, self.licenses, url)
                item.copyright = "\n".join(self.copyright)
                item.comment = self.comment
                self.oss_items.append(item)
        else:
            item = OssItem(self.oss_name, self.oss_version, self.licenses)
            item.copyright = "\n".join(self.copyright)
            item.comment = self.comment
            self.oss_items.append(item)

    def get_print_array(self) -> list:
        print_rows = []
        for item in self.oss_items:
            print_rows.append([self.source_name_or_path, item.name, item.version, ",".join(item.license),
                               item.download_location, "",
                               item.copyright, "Exclude" if self.exclude else "", item.comment,
                               self.license_reference])
        return print_rows

    def __eq__(self, other: object) -> bool:
        if type(other) == str:
            return self.source_name_or_path == other
        else:
            return self.source_name_or_path == other.source_name_or_path


def is_exclude_dir(dir_path: str) -> bool:
    if dir_path != "":
        dir_path = dir_path.lower()
        dir_path = dir_path if dir_path.endswith(
            os.path.sep) else dir_path + os.path.sep
        dir_path = dir_path if dir_path.startswith(
            os.path.sep) else os.path.sep + dir_path
        return any(dir_name in dir_path for dir_name in _exclude_directory)
    return False


def is_exclude_file(file_path: str, prev_dir: str = None, prev_dir_exclude_value: bool = None) -> bool:
    file_path = file_path.lower()
    filename = os.path.basename(file_path)
    if os.path.splitext(filename)[1] in _exclude_extension:
        return True
    if filename.startswith('.') or filename in _exclude_filename:
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


def is_notice_file(file_path: str) -> bool:
    pattern = r"({})(?<!w)".format("|".join(_notice_filename))
    file_path = file_path.lower()
    filename = os.path.basename(file_path)
    return bool(re.match(pattern, filename))
