#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import re
import fosslight_util.constant as constant
from ._license_matched import MatchedLicense
from ._scan_item import SourceItem
from ._scan_item import is_exclude_dir
from ._scan_item import is_exclude_file
from ._scan_item import replace_word
from ._scan_item import is_notice_file
from ._scan_item import is_manifest_file
from typing import Tuple

logger = logging.getLogger(constant.LOGGER_NAME)
_exclude_directory = ["test", "tests", "doc", "docs"]
_exclude_directory = [os.path.sep + dir_name +
                      os.path.sep for dir_name in _exclude_directory]
_exclude_directory.append("/.")
REMOVE_LICENSE = ["warranty-disclaimer"]
regex = re.compile(r'licenseref-(\S+)', re.IGNORECASE)
find_word = re.compile(rb"SPDX-PackageDownloadLocation\s*:\s*(\S+)", re.IGNORECASE)
KEYWORD_SPDX_ID = r'SPDX-License-Identifier\s*[\S]+'
KEYWORD_DOWNLOAD_LOC = r'DownloadLocation\s*[\S]+'
KEYWORD_SCANCODE_UNKNOWN = "unknown-spdx"
SPDX_REPLACE_WORDS = ["(", ")"]
KEY_AND = r"(?<=\s)and(?=\s)"
KEY_OR = r"(?<=\s)or(?=\s)"


def get_error_from_header(header_item: list) -> Tuple[bool, str]:
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
        logger.debug(f"Error_parsing_header: {ex}")
    return has_error, str_error


def parsing_scancode_32_earlier(scancode_file_list: list, has_error: bool = False) -> Tuple[bool, list, list, dict]:
    rc = True
    msg = []
    scancode_file_item = []
    license_list = {}  # Key :[license]+[matched_text], value: MatchedLicense()
    prev_dir = ""
    prev_dir_value = False

    if scancode_file_list:
        for file in scancode_file_list:
            try:
                is_dir = False
                file_path = file.get("path", "")
                if not file_path:
                    continue
                is_binary = file.get("is_binary", False)
                if "type" in file:
                    is_dir = file["type"] == "directory"
                    if is_dir:
                        prev_dir_value = is_exclude_dir(file_path)
                        prev_dir = file_path

                if not is_binary and not is_dir:
                    licenses = file.get("licenses", [])
                    copyright_list = file.get("copyrights", [])

                    result_item = SourceItem(file_path)

                    if has_error and "scan_errors" in file:
                        error_msg = file.get("scan_errors", [])
                        if len(error_msg) > 0:
                            result_item.comment = ",".join(error_msg)
                            scancode_file_item.append(result_item)
                            continue
                    copyright_value_list = []
                    for x in copyright_list:
                        latest_key_data = x.get("copyright", "")
                        if latest_key_data:
                            copyright_data = latest_key_data
                        else:
                            copyright_data = x.get("value", "")
                        if copyright_data:
                            try:
                                copyright_data = re.sub(KEYWORD_SPDX_ID, '', copyright_data, flags=re.I)
                                copyright_data = re.sub(KEYWORD_DOWNLOAD_LOC, '', copyright_data, flags=re.I).strip()
                            except Exception:
                                pass
                            copyright_value_list.append(copyright_data)

                    result_item.copyright = copyright_value_list

                    # Set the license value
                    license_detected = []
                    if licenses is None or licenses == "":
                        continue

                    license_expression_list = file.get("license_expressions", {})
                    if len(license_expression_list) > 0:
                        license_expression_list = [
                            x.lower() for x in license_expression_list
                            if x is not None]

                    for lic_item in licenses:
                        license_value = ""
                        key = lic_item.get("key", "")
                        if key in REMOVE_LICENSE:
                            if key in license_expression_list:
                                license_expression_list.remove(key)
                            continue
                        spdx = lic_item.get("spdx_license_key", "")
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
                            if key == KEYWORD_SCANCODE_UNKNOWN:
                                try:
                                    matched_txt = lic_item.get("matched_text", "").lower()
                                    matched = regex.search(matched_txt)
                                    if matched:
                                        license_value = str(matched.group())
                                except Exception:
                                    pass

                            for word in replace_word:
                                if word in license_value:
                                    license_value = license_value.replace(word, "")
                            license_detected.append(license_value)

                            # Add matched licenses
                            if "category" in lic_item:
                                lic_category = lic_item["category"]
                                if "matched_text" in lic_item:
                                    lic_matched_text = lic_item["matched_text"]
                                    lic_matched_key = license_value + lic_matched_text
                                    if lic_matched_key in license_list:
                                        license_list[lic_matched_key].set_files(file_path)
                                    else:
                                        lic_info = MatchedLicense(license_value, lic_category, lic_matched_text, file_path)
                                        license_list[lic_matched_key] = lic_info

                        matched_rule = lic_item.get("matched_rule", {})
                        result_item.is_license_text = matched_rule.get("is_license_text", False)

                    if len(license_detected) > 0:
                        result_item.licenses = license_detected

                        if len(license_expression_list) > 0:
                            license_expression_list = list(
                                set(license_expression_list))
                            result_item.comment = ','.join(license_expression_list)

                        if is_manifest_file(file_path):
                            result_item.is_license_text = True

                        if is_exclude_file(file_path, prev_dir, prev_dir_value):
                            result_item.exclude = True
                        scancode_file_item.append(result_item)
            except Exception as ex:
                msg.append(f"Error Parsing item: {ex}")
                rc = False
    msg = list(set(msg))
    return rc, scancode_file_item, msg, license_list


def split_spdx_expression(spdx_string: str) -> list:
    license = []
    for replace in SPDX_REPLACE_WORDS:
        spdx_string = spdx_string.replace(replace, "")
    license = re.split(KEY_AND + "|" + KEY_OR, spdx_string)
    return license


def parsing_scancode_32_later(
    scancode_file_list: list, has_error: bool = False
) -> Tuple[bool, list, list, dict]:
    rc = True
    msg = []
    scancode_file_item = []
    license_list = {}  # Key :[license]+[matched_text], value: MatchedLicense()

    if scancode_file_list:
        for file in scancode_file_list:
            try:
                file_path = file.get("path", "")
                is_binary = file.get("is_binary", False)
                is_dir = file.get("type", "") == "directory"
                if (not file_path) or is_binary or is_dir:
                    continue

                result_item = SourceItem(file_path)

                if has_error:
                    error_msg = file.get("scan_errors", [])
                    if error_msg:
                        result_item.comment = ",".join(error_msg)
                        scancode_file_item.append(result_item)
                        continue

                copyright_value_list = []
                for x in file.get("copyrights", []):
                    copyright_data = x.get("copyright", "")
                    if copyright_data:
                        try:
                            copyright_data = re.sub(KEYWORD_SPDX_ID, '', copyright_data, flags=re.I)
                            copyright_data = re.sub(KEYWORD_DOWNLOAD_LOC, '', copyright_data, flags=re.I).strip()
                        except Exception:
                            pass
                        copyright_value_list.append(copyright_data)
                result_item.copyright = copyright_value_list

                license_detected = []
                licenses = file.get("license_detections", [])
                if not licenses:
                    continue
                for lic in licenses:
                    matched_lic_list = lic.get("matches", [])
                    for matched_lic in matched_lic_list:
                        found_lic_list = matched_lic.get("license_expression", "")
                        matched_txt = matched_lic.get("matched_text", "")
                        if found_lic_list:
                            found_lic_list = found_lic_list.lower()
                            for found_lic in split_spdx_expression(found_lic_list):
                                if found_lic:
                                    found_lic = found_lic.strip()
                                    if found_lic in REMOVE_LICENSE:
                                        continue
                                    elif found_lic == KEYWORD_SCANCODE_UNKNOWN:
                                        try:
                                            matched = regex.search(matched_txt.lower())
                                            if matched:
                                                found_lic = str(matched.group())
                                        except Exception:
                                            pass
                                    for word in replace_word:
                                        found_lic = found_lic.replace(word, "")
                                    if matched_txt:
                                        lic_matched_key = found_lic + matched_txt
                                        if lic_matched_key in license_list:
                                            license_list[lic_matched_key].set_files(file_path)
                                        else:
                                            lic_info = MatchedLicense(found_lic, "", matched_txt, file_path)
                                            license_list[lic_matched_key] = lic_info
                                    license_detected.append(found_lic)
                result_item.licenses = license_detected
                if len(license_detected) > 1:
                    license_expression_spdx = file.get("detected_license_expression_spdx", "")
                    license_expression = file.get("detected_license_expression", "")
                    if license_expression_spdx:
                        license_expression = license_expression_spdx
                    if license_expression:
                        result_item.comment = license_expression

                result_item.exclude = is_exclude_file(file_path)
                result_item.is_license_text = file.get("percentage_of_license_text", 0) > 90 or is_notice_file(file_path)

                if is_manifest_file(file_path) and len(license_detected) > 0:
                    result_item.is_license_text = True

                scancode_file_item.append(result_item)
            except Exception as ex:
                msg.append(f"Error Parsing item: {ex}")
                rc = False

    return rc, scancode_file_item, msg, license_list


def parsing_file_item(
    scancode_file_list: list, has_error: bool, need_matched_license: bool = False
) -> Tuple[bool, list, list, dict]:

    rc = True
    msg = []

    first_item = next(iter(scancode_file_list or []), {})
    if "licenses" in first_item:
        rc, scancode_file_item, msg, license_list = parsing_scancode_32_earlier(scancode_file_list, has_error)
    else:
        rc, scancode_file_item, msg, license_list = parsing_scancode_32_later(scancode_file_list, has_error)
    if not need_matched_license:
        license_list = {}
    return rc, scancode_file_item, msg, license_list
