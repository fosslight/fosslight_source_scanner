#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: LicenseRef-LGE-Proprietary

import getopt
import os
import sys
import json
import platform
from datetime import datetime
from ._write_oss_report_src import write_result_to_csv, write_result_to_excel
from ._parsing_scancode_file_item import parsing_file_item

_replace_word = ["-only", "-old-style", "-or-later"]


def convert_json_to_excel(scancode_result_json):
    try:
        start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        sheet_list = {}
        if os.path.isfile(scancode_result_json):
            file_list = get_detected_licenses_from_scancode(scancode_result_json)
            if len(file_list) > 0:
                sheet_list["SRC"] = file_list
        elif os.path.isdir(scancode_result_json):
            for root, dirs, files in os.walk(scancode_result_json):
                for file in files:
                    if file.endswith(".json"):
                        try:
                            result_file = os.path.join(root, file)
                            file_list = get_detected_licenses_from_scancode(result_file)
                            if len(file_list) > 0:
                                file_name = os.path.basename(file)
                                sheet_list["SRC_" + file_name] = file_list
                        except:
                            pass

        if len(sheet_list) > 0:
            oss_report_name = "OSS-Report_" + start_time + ".xlsx"
            write_result_to_excel(oss_report_name, sheet_list)
            if platform.system() != "Windows":
                write_result_to_csv("result_" + start_time + ".csv", sheet_list)
        else:
            print("There is no item to print in OSS-Report.")

    except Exception as ex:
        print(str(ex))


def get_detected_licenses_from_scancode(scancode_json_file):
    file_list = []
    try:
        print("Start parsing " + scancode_json_file)
        with open(scancode_json_file, "r") as st_json:
            st_python = json.load(st_json)
            rc, file_list = parsing_file_item(st_python["files"])
    except:
        pass
    print("|---Number of files detected: " + str(len(file_list)))
    return file_list


def print_help_msg():
    print("* Required :\n -p path_of_scancode_json_result")
    sys.exit()


def main():
    argv = sys.argv[1:]
    path_to_find_bin = os.getcwd()
    try:
        opts, args = getopt.getopt(argv, 'hp:')
        for opt, arg in opts:
            if opt == "-h":
                print_help_msg()
            elif opt == "-p":
                path_to_find_bin = arg
    except:
        pass

    convert_json_to_excel(path_to_find_bin)


if __name__ == '__main__':
    main()
