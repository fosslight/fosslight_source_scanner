#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: LicenseRef-LGE-Proprietary

import sys
import os
import multiprocessing

import warnings
warnings.filterwarnings("ignore",category=FutureWarning)
from scancode import cli
import platform
import getopt
from datetime import datetime
from ._write_oss_report_src import write_result_to_csv, write_result_to_excel
from ._parsing_scancode_file_item import parsing_file_item



def print_help_msg():
    print("* Required : -p path_to_scan")
    print("* Optional : -j ")
    sys.exit()


def main():
    argv = sys.argv[1:]
    path_to_scan = ""
    _write_json_file = False
    _windows = platform.system() == "Windows"
    start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_file = "OSS-Report_" + start_time
    output_csv_file = "result_" + start_time
    output_json_file = "scancode_" + start_time

    try:
        opts, args = getopt.getopt(argv, 'hjp:o:')
        for opt, arg in opts:
            if opt == "-h":
                print_help_msg()
            elif opt == "-p":
                path_to_scan = arg
            elif opt == "-j":
                _write_json_file = True
            elif opt == "-o":
                output_file = arg
                output_csv_file = arg
                output_json_file = arg

    except Exception as ex:
        print_help_msg()

    if path_to_scan == "":
        if _windows:
            path_to_scan = os.getcwd()
        else:
            print_help_msg()

    num_cores = multiprocessing.cpu_count() - 1
    if num_cores < 1:
        num_cores = 1

    sheet_list = {}
    if os.path.isdir(path_to_scan):
        try:
            rc, results = cli.run_scan(path_to_scan, max_depth=100, strip_root=True, license=True, copyright=True,
                                       return_results=True, processes=num_cores)
            if rc:
                for key, value in results.items():
                    if key == "files":
                        rc, result_list = parsing_file_item(value)
                        if rc:
                            if len(result_list) > 0:
                                sheet_list["SRC"] = result_list
                                write_result_to_excel(output_file + ".xlsx", sheet_list)
                            else:
                                print("There is no item to print in OSS-Report.")
                if _write_json_file:
                    from formattedcode.output_json import write_json
                    write_json(results, output_json_file + ".json", pretty=True)
                if not _windows:
                    write_result_to_csv(output_csv_file + ".csv", sheet_list)
            else:
                print("* Source code analysis failed.")
        except Exception as ex:
            print('* Error :' + str(ex))
    else:
        print("* Check the path to scan. :" + path_to_scan)


if __name__ == '__main__':
    main()
