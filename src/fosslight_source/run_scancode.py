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
from ._parsing_scancode_file_item import parsing_file_item
from ._parsing_scancode_file_item import get_error_from_header
from fosslight_util.write_excel import write_excel_and_csv
from ._help import print_help_msg_source

logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_PKG_NAME = "fosslight_source"


def main():
    argv = sys.argv[1:]
    _path_to_scan = ""
    _write_json_file = False
    _output_file = ""

    try:
        opts, args = getopt.getopt(argv, 'hjp:o:')
        for opt, arg in opts:
            if opt == "-h":
                print_help_msg_source()
            elif opt == "-p":
                _path_to_scan = arg
            elif opt == "-j":
                _write_json_file = True
            elif opt == "-o":
                _output_file = arg

    except Exception:
        print_help_msg_source()

    timer = TimerThread()
    timer.setDaemon(True)
    timer.start()
    run_scan(_path_to_scan, _output_file, _write_json_file, -1, False)


def run_scan(path_to_scan, output_file_name="",
             _write_json_file=False, num_cores=-1, return_results=False):
    global logger

    success = True
    msg = ""
    _str_final_result_log = ""
    _result_log = {}
    result_list = []

    _windows = platform.system() == "Windows"
    start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    if output_file_name == "":
        output_file = "OSS-Report_" + start_time
        output_json_file = "scancode_" + start_time
        output_dir = os.getcwd()
    else:
        output_file = output_file_name
        output_json_file = output_file_name
        output_dir = os.path.dirname(os.path.abspath(output_file_name))

    logger = init_log(os.path.join(output_dir, "fosslight_src_log_"+start_time+".txt"))
    _result_log = init_log_item(_PKG_NAME, path_to_scan)

    if path_to_scan == "":
        if _windows:
            path_to_scan = os.getcwd()
        else:
            print_help_msg_source()

    num_cores = multiprocessing.cpu_count() - 1 if num_cores < 0 else num_cores

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
            if not rc:
                msg = "Source code analysis failed."
                success = False
            if results:
                sheet_list = {}
                has_error = False
                if "headers" in results:
                    has_error, error_msg = get_error_from_header(results["headers"])
                    if has_error:
                        _result_log["Error_files"] = error_msg
                        msg = "Failed to analyze :"+ error_msg
                if "files" in results:
                    rc, result_list, parsing_msg = parsing_file_item(results["files"], has_error)
                    _result_log["Parsing Log"] = parsing_msg
                    if rc:
                        if not success:
                            success = True
                        result_list = sorted(
                            result_list, key=lambda row: (''.join(row.licenses)))
                        sheet_list["SRC"] = [scan_item.get_row_to_print() for scan_item in result_list]

                        success_to_write, writing_msg = write_excel_and_csv(
                            output_file, sheet_list)
                        logger.info("Writing excel :"+str(success_to_write)+ " "+writing_msg)
                        if success_to_write:
                            _result_log["OSS Report"] = output_file +".xlsx"
        except Exception as ex:
            success = False
            msg = str(ex)
            logger.error("Analyze "+path_to_scan+":"+msg)
    else:
        success = False
        msg = "Check the path to scan. :" + path_to_scan

    if not return_results:
        result_list = []

    scan_result_msg = str(success) if msg == "" else str(success) + "," + msg
    _result_log["Scan Result"] = scan_result_msg
    _result_log["Output Directory"] = output_dir
    try:
        _str_final_result_log = yaml.safe_dump(_result_log, allow_unicode=True, sort_keys=True)
        logger.info(_str_final_result_log)
    except Exception as ex:
        logger.warning("Failed to print result log. "+ str(ex))
    return success, _result_log["Scan Result"], result_list


if __name__ == '__main__':
    main()
