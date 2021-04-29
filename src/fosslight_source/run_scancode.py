#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import sys
import os
import multiprocessing
import warnings
import platform
import getopt
import logging
import yaml
from scancode import cli
from datetime import datetime
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from fosslight_util.set_log import init_log_item
from fosslight_util.timer_thread import TimerThread
from ._write_oss_report_src import write_result_to_csv, write_result_to_excel
from ._parsing_scancode_file_item import parsing_file_item

logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_PKG_NAME = "fosslight_source"
_ERROR_PREFIX = "* Error : "

def print_help_msg():
    print("* Required : -p path_to_scan")
    print("* Optional : -j ")
    sys.exit()


def main():
    argv = sys.argv[1:]
    _path_to_scan = ""
    _write_json_file = False
    _output_file = ""

    try:
        opts, args = getopt.getopt(argv, 'hjp:o:')
        for opt, arg in opts:
            if opt == "-h":
                print_help_msg()
            elif opt == "-p":
                _path_to_scan = arg
            elif opt == "-j":
                _write_json_file = True
            elif opt == "-o":
                _output_file = arg

    except Exception:
        print_help_msg()

    timer = TimerThread()
    timer.setDaemon(True)
    timer.start()
    success, result_log = run_scan(_path_to_scan, _output_file, _write_json_file, -1)


def run_scan(path_to_scan, output_file_name="",
             _write_json_file=False, num_cores=-1):
    global logger

    success = True
    msg = ""
    _str_final_result_log = ""
    _result_log = {}

    _windows = platform.system() == "Windows"
    start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    if output_file_name == "":
        output_file = "OSS-Report_" + start_time
        output_csv_file = "result_" + start_time
        output_json_file = "scancode_" + start_time
        output_dir = os.getcwd()
    else:
        output_file = output_file_name
        output_csv_file = output_file_name
        output_json_file = output_file_name
        output_dir = os.path.dirname(os.path.abspath(output_file_name))

    logger = init_log(os.path.join(output_dir, "fosslight_src_log_"+start_time+".txt"))
    _result_log = init_log_item(_PKG_NAME, path_to_scan)

    if path_to_scan == "":
        if _windows:
            path_to_scan = os.getcwd()
        else:
            print_help_msg()

    num_cores = multiprocessing.cpu_count() - 1 if num_cores < 0 else num_cores

    sheet_list = {}
    if os.path.isdir(path_to_scan):
        try:
            output_json_file = output_json_file+".json" if _write_json_file\
                else ""

            rc, results = cli.run_scan(path_to_scan, max_depth=100,
                                       strip_root=True, license=True,
                                       copyright=True, return_results=True,
                                       processes=num_cores,
                                       output_json_pp=output_json_file,
                                       only_findings=True)

            if rc:
                for key, value in results.items():
                    if key == "files":
                        rc, result_list, parsing_msg = parsing_file_item(value)
                        _result_log["Parsing Log"] = parsing_msg
                        if rc:
                            if len(result_list) > 0:
                                sheet_list["SRC"] = result_list
                                write_result_to_excel(
                                    output_file + ".xlsx", sheet_list)
                                _result_log["OSS Report"] = output_file
                            else:
                                msg = "* There is no item"\
                                    " to print in OSS-Report."
                if not _windows:
                    write_result_to_csv(output_csv_file + ".csv", sheet_list)
            else:
                msg = _ERROR_PREFIX+"Source code analysis failed."
                success = False
        except Exception as ex:
            success = False
            msg = _ERROR_PREFIX + str(ex)
    else:
        success = False
        msg = _ERROR_PREFIX+"Check the path to scan. :" + path_to_scan

    scan_result_msg = str(success)+" "+msg
    _result_log["Scan Result"] = scan_result_msg.strip()
    _result_log["Output Directory"] = output_dir
    try:
        _str_final_result_log = yaml.safe_dump(_result_log, allow_unicode=True, sort_keys=True)
        logger.warn("\n"+_str_final_result_log)
    except Exception as ex:
        logger.warn(_ERROR_PREFIX+"Failed to print result log. "+ str(ex))
    return success, _str_final_result_log


if __name__ == '__main__':
    main()
