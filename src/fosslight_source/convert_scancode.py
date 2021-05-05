#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import getopt
import os
import sys
import json
import platform
from datetime import datetime
import logging
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from fosslight_util.set_log import init_log_item
import yaml
from ._parsing_scancode_file_item import parsing_file_item
from fosslight_util.write_excel import write_excel_and_csv

logger = logging.getLogger(constant.LOGGER_NAME)
_PKG_NAME = "fosslight_source"
_ERROR_PREFIX = "* Error : "


def convert_json_to_excel(scancode_json, excel_name):
    file_list = []
    _result_log = init_log_item(_PKG_NAME)
    msg = ""
    success = True

    try:
        sheet_list = {}
        if os.path.isfile(scancode_json):
            file_list = get_detected_licenses_from_scancode(
                scancode_json)
            if len(file_list) > 0:
                file_list = sorted(
                                file_list, key=lambda row: (''.join(row.licenses)))
                sheet_list["SRC"] = [scan_item.get_row_to_print() for scan_item in file_list]
        elif os.path.isdir(scancode_json):
            for root, dirs, files in os.walk(scancode_json):
                for file in files:
                    if file.endswith(".json"):
                        try:
                            result_file = os.path.join(root, file)
                            file_list = get_detected_licenses_from_scancode(
                                result_file)
                            if len(file_list) > 0:
                                file_name = os.path.basename(file)
                                file_list = sorted(
                                    file_list, key=lambda row: (''.join(row.licenses)))
                                sheet_list["SRC_" + file_name] = [scan_item.get_row_to_print() for scan_item in file_list]
                        except Exception as ex:
                            pass

        success_to_write, writing_msg = write_excel_and_csv(excel_name, sheet_list)
        logger.warn("* Writing excel :"+str(success_to_write)+ " "+writing_msg)
        if success_to_write:
            _result_log["OSS Report"] = excel_name+".xlsx"

    except Exception as ex:
        success = False
        msg = _ERROR_PREFIX+str(ex)

    scan_result_msg = str(success)+" "+msg
    _result_log["Scan Result"] = scan_result_msg.strip()

    try:
        _str_final_result_log = yaml.safe_dump(_result_log, allow_unicode=True, sort_keys=True)
        logger.warn("\n"+_str_final_result_log)
    except Exception as ex:
        logger.warn(_ERROR_PREFIX+"Failed to print result log. "+ str(ex))

    return file_list


def get_detected_licenses_from_scancode(scancode_json_file):
    file_list = []
    try:
        logger.warn("Start parsing " + scancode_json_file)
        with open(scancode_json_file, "r") as st_json:
            st_python = json.load(st_json)
            rc, file_list, msg= parsing_file_item(st_python["files"])
            logger.warn("|---"+msg)
    except Exception as error:
        logger.warn(_ERROR_PREFIX+"Parsing -"+str(error))
    logger.warn("|---Number of files detected: " + str(len(file_list)))
    return file_list


def print_help_msg():
    print("* Required :\n -p path_of_scancode_json_result")
    sys.exit()


def main():
    global logger

    argv = sys.argv[1:]
    path_to_find_bin = os.getcwd()
    start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_file_name = ""

    try:
        opts, args = getopt.getopt(argv, 'hp:o:')
        for opt, arg in opts:
            if opt == "-h":
                print_help_msg()
            elif opt == "-p":
                path_to_find_bin = arg
            elif opt == "-o":
                output_file_name = arg
    except Exception as error:
        pass

    if output_file_name == "":
        output_dir = os.getcwd()
        oss_report_name = "OSS-Report_" + start_time
    else:
        oss_report_name = output_file_name
        output_dir = os.path.dirname(os.path.abspath(output_file_name))

    logger = init_log(os.path.join(output_dir, "fosslight_src_log_"+start_time+".txt"))

    convert_json_to_excel(path_to_find_bin, oss_report_name)


if __name__ == '__main__':
    main()
