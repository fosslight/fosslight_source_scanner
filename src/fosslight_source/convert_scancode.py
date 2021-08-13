#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import getopt
import os
import sys
import json
from datetime import datetime
import logging
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
import yaml
from ._parsing_scancode_file_item import parsing_file_item, get_error_from_header
from fosslight_util.write_excel import write_excel_and_csv
from ._help import print_help_msg_convert
from ._license_matched import get_license_list_to_print

logger = logging.getLogger(constant.LOGGER_NAME)
_PKG_NAME = "fosslight_source"


def convert_json_to_excel(scancode_json, excel_name, result_log, need_license=False):
    sheet_license_prefix = "matched_text"
    sheet_SRC_prefix = "SRC"
    file_list = []
    lic_list = {}
    msg = ""
    success = True

    try:
        sheet_list = {}
        if os.path.isfile(scancode_json):
            file_list, lic_list = get_detected_licenses_from_scancode(
                scancode_json, need_license)
            if len(file_list) > 0:
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
                            if len(file_list) > 0:
                                file_name = os.path.basename(file)
                                file_list = sorted(
                                    file_list, key=lambda row: (''.join(row.licenses)))
                                sheet_name = sheet_SRC_prefix + "_" + file_name
                                sheet_list[sheet_name] = [scan_item.get_row_to_print() for scan_item in file_list]
                                if need_license:
                                    lic_sheet_name = sheet_license_prefix + "_" + file_name
                                    sheet_list[lic_sheet_name] = get_license_list_to_print(lic_list)
                        except Exception as ex:
                            logger.warning("Error parsing "+file+":" + str(ex))

        success_to_write, writing_msg = write_excel_and_csv(excel_name, sheet_list)
        logger.info("Writing excel :" + str(success_to_write) + " " + writing_msg)
        if success_to_write:
            result_log["FOSSLight Report"] = excel_name + ".xlsx"

    except Exception as ex:
        success = False
        logger.warning(str(ex))

    scan_result_msg = str(success) if msg == "" else str(success) + "," + msg
    result_log["Scan Result"] = scan_result_msg

    try:
        _str_final_result_log = yaml.safe_dump(result_log, allow_unicode=True, sort_keys=True)
        logger.info(_str_final_result_log)
    except Exception as ex:
        logger.warning("Failed to print result log.: " + str(ex))

    return file_list


def get_detected_licenses_from_scancode(scancode_json_file, need_license):
    file_list = []
    license_list = {}
    try:
        logger.info("Start parsing " + scancode_json_file)
        with open(scancode_json_file, "r") as st_json:
            st_python = json.load(st_json)
            has_error, str_error = get_error_from_header(st_python["headers"])
            rc, file_list, msg, license_list = parsing_file_item(st_python["files"], has_error, need_license)
            logger.info("|---"+msg)
            if has_error:
                logger.info("|---Scan error:"+str_error)
    except Exception as error:
        logger.warning("Parsing " + scancode_json_file + ":" + str(error))
    logger.info("|---Number of files detected: " + str(len(file_list)))
    return file_list, license_list


def main():
    global logger

    argv = sys.argv[1:]
    path_to_find_bin = os.getcwd()
    start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_file_name = ""
    print_matched_text = False

    try:
        opts, args = getopt.getopt(argv, 'hmp:o:')
        for opt, arg in opts:
            if opt == "-h":
                print_help_msg_convert()
            elif opt == "-p":
                path_to_find_bin = arg
            elif opt == "-o":
                output_file_name = arg
            elif opt == "-m":
                print_matched_text = True
    except Exception:
        print_help_msg_convert()

    if output_file_name == "":
        output_dir = os.getcwd()
        oss_report_name = "FOSSLight-Report_" + start_time
    else:
        oss_report_name = output_file_name
        output_dir = os.path.dirname(os.path.abspath(output_file_name))

    logger, _result_log = init_log(os.path.join(output_dir, "fosslight_src_log_" + start_time + ".txt"),
                                   True, logging.INFO, logging.DEBUG, _PKG_NAME)
    convert_json_to_excel(path_to_find_bin, oss_report_name, _result_log, print_matched_text)


if __name__ == '__main__':
    main()
