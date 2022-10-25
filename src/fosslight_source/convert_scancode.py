#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import json
from datetime import datetime
import logging
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
import yaml
from ._parsing_scancode_file_item import parsing_file_item, get_error_from_header
from fosslight_util.output_format import check_output_format, write_output_file
from ._help import print_version, print_help_msg_source_scanner
from ._license_matched import get_license_list_to_print
import argparse

logger = logging.getLogger(constant.LOGGER_NAME)
_PKG_NAME = "fosslight_source"


def convert_json_to_output_report(scancode_json, output_file_name, need_license=False, format=""):
    global logger

    sheet_license_prefix = "matched_text"
    sheet_SRC_prefix = "SRC_FL_Source"
    file_list = []
    lic_list = {}
    msg = ""
    success = True
    start_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    _json_ext = ".json"

    success, msg, output_path, output_file, output_extension = check_output_format(output_file_name, format)
    if success:
        if output_path == "":
            output_path = os.getcwd()
        else:
            output_path = os.path.abspath(output_path)

        if output_file == "":
            if output_extension == _json_ext:
                output_file = "fosslight_opossum_" + start_time
            else:
                output_file = "fosslight_report_" + start_time
    else:
        output_path = os.getcwd()

    logger, result_log = init_log(os.path.join(output_path, "fosslight_log_" + start_time + ".txt"),
                                  True, logging.INFO, logging.DEBUG, _PKG_NAME)
    if not success:
        logger.error("Fail to convert scancode: " + msg)
        return []
    try:
        sheet_list = {}
        if os.path.isfile(scancode_json):
            file_list, lic_list = get_detected_licenses_from_scancode(
                scancode_json, need_license)
            if file_list and len(file_list) > 0:
                file_list = sorted(
                                file_list, key=lambda row: (''.join(row.licenses)))
                sheet_list[sheet_SRC_prefix] = [scan_item.get_row_to_print() for scan_item in file_list]
            if need_license:
                sheet_list[sheet_license_prefix] = get_license_list_to_print(lic_list)
        elif os.path.isdir(scancode_json):
            for root, dirs, files in os.walk(scancode_json):
                for file in files:
                    if file.endswith(".json"):
                        try:
                            result_file = os.path.join(root, file)
                            file_list, lic_list = get_detected_licenses_from_scancode(
                                result_file, need_license)
                            if file_list and len(file_list) > 0:
                                file_name = os.path.basename(file)
                                file_list = sorted(
                                    file_list, key=lambda row: (''.join(row.licenses)))
                                sheet_name = sheet_SRC_prefix + "_" + file_name
                                sheet_list[sheet_name] = [scan_item.get_row_to_print() for scan_item in file_list]
                                if need_license:
                                    lic_sheet_name = sheet_license_prefix + "_" + file_name
                                    sheet_list[lic_sheet_name] = get_license_list_to_print(lic_list)
                        except Exception as ex:
                            logger.warning(f"Error parsing {file}: {ex}")

        output_file_without_ext = os.path.join(output_path, output_file)
        success_to_write, writing_msg, result_file = write_output_file(output_file_without_ext, output_extension, sheet_list)

        if success_to_write:
            if result_file:
                result_log["Output file"] = result_file
            else:
                logger.warning("Nothing is detected to convert so output file is not generated.")
        else:
            logger.info(f"Failed to writing Output file :{writing_msg}")

    except Exception as ex:
        success = False
        logger.warning(f"Failed to parsing file:{ex}")

    scan_result_msg = str(success) if msg == "" else str(success) + "," + msg
    result_log["Scan Result"] = scan_result_msg

    try:
        _str_final_result_log = yaml.safe_dump(result_log, allow_unicode=True, sort_keys=True)
        logger.info(_str_final_result_log)
    except Exception as ex:
        logger.warning(f"Failed to print result log.: {ex}")

    return file_list


def get_detected_licenses_from_scancode(scancode_json_file, need_license):
    file_list = []
    license_list = {}
    try:
        logger.info(f"Start parsing :{scancode_json_file}")
        with open(scancode_json_file, "r") as st_json:
            st_python = json.load(st_json)
            has_error, str_error = get_error_from_header(st_python["headers"])
            rc, file_list, msg, license_list = parsing_file_item(st_python.get("files"), has_error, need_license)
            if has_error:
                logger.info(f"|---Scan error:{str_error}")
    except Exception as error:
        logger.warning(f"Parsing {scancode_json_file} error:{error}")
    cnt = len(file_list) if file_list else 0
    logger.info(f"|--- Number of files detected: {cnt}")
    return file_list, license_list


def main():
    path_to_find_json = os.getcwd()
    output_file_name = ""
    print_matched_text = False
    format = ""

    parser = argparse.ArgumentParser(description='FOSSLight Source Convert',
                                     prog='fosslight_source_convert', add_help=False)
    parser.add_argument('-h', '--help', action='store_true', required=False)
    parser.add_argument('-v', '--version', action='store_true', required=False)
    parser.add_argument('-p', '--path', nargs=1, type=str, required=False)
    parser.add_argument('-o', '--output', nargs=1, type=str, required=False, default="")
    parser.add_argument('-m', '--matched', action='store_true', required=False)
    parser.add_argument('-f', '--format', nargs=1, type=str, required=False)
    args = parser.parse_args()

    if args.help:
        print_help_msg_source_scanner()
    if args.version:
        print_version(_PKG_NAME)
    if not args.path:
        path_to_find_json = os.getcwd()
    else:
        path_to_find_json = ''.join(args.path)
    output_file_name = ''.join(args.output)
    if args.matched:
        print_matched_text = True
    if args.format:
        format = ''.join(args.format)

    if path_to_find_json == "":
        print_help_msg_source_scanner()

    convert_json_to_output_report(path_to_find_json, output_file_name, print_matched_text, format)


if __name__ == '__main__':
    main()
