#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import sys
import os
import warnings
import getopt
import logging
import copy
from datetime import datetime
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from fosslight_util.timer_thread import TimerThread
from ._help import print_help_msg_source, print_version
from ._license_matched import get_license_list_to_print
from fosslight_util.output_format import check_output_format, write_output_file
from .run_scancode import run_scan
from .run_scanoss import run_scanoss_py

SCANOSS_SHEET_NAME = 'SRC_FL_Source'
SCANOSS_HEADER = {SCANOSS_SHEET_NAME: ['ID', 'Source Name or Path', 'OSS Name',
                                       'OSS Version', 'License', 'Download Location',
                                       'Homepage', 'Copyright Text', 'Exclude',
                                       'Comment', 'scanoss_matched_lines',
                                       'scanoss_fileURL', 'scanoss_vendor']}

logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_PKG_NAME = "fosslight_source"


def main():
    global logger
    success = True
    _result_log = {}

    argv = sys.argv[1:]
    path_to_scan = ""
    write_json_file = False
    output_file_name = ""
    print_matched_text = False
    format = ""
    selected_scanner = ""

    scanned_result = []
    license_list = []

    try:
        opts, args = getopt.getopt(argv, 'hvmjs:p:o:f:')
        for opt, arg in opts:
            if opt == "-h":
                print_help_msg_source()
            elif opt == "-v":
                print_version(_PKG_NAME)
            elif opt == "-p":
                path_to_scan = arg
            elif opt == "-j":
                write_json_file = True
            elif opt == "-o":
                output_file_name = arg
            elif opt == "-m":
                print_matched_text = True
            elif opt == "-f":
                format = arg
            elif opt == "-s":
                selected_scanner = arg.lower()
    except Exception:
        print_help_msg_source()

    timer = TimerThread()
    timer.setDaemon(True)
    timer.start()

    start_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    success, msg, output_path, output_file, output_extension = check_output_format(output_file_name, format)
    logger, _result_log = init_log(os.path.join(output_path, "fosslight_src_log_"+start_time+".txt"),
                                   True, logging.INFO, logging.DEBUG, _PKG_NAME, path_to_scan)

    if selected_scanner == 'scancode':
        success, _result_log["Scan Result"], scanned_result, license_list = run_scan(path_to_scan, output_file_name,
                                                                                     write_json_file, -1, True,
                                                                                     print_matched_text, format, True)
    elif selected_scanner == 'scanoss':
        scanned_result = run_scanoss_py(path_to_scan, output_file_name, format, True, write_json_file)
    elif selected_scanner == 'all' or selected_scanner == '':
        success, _result_log["Scan Result"], scanned_result, license_list = run_all_scanners(path_to_scan, output_file_name,
                                                                                             write_json_file, -1,
                                                                                             print_matched_text, format, True)
    else:
        print_help_msg_source()
        sys.exit(1)
    create_report_file(start_time, scanned_result, license_list, selected_scanner, print_matched_text,
                       output_path, output_file, output_extension)


def create_report_file(start_time, scanned_result, license_list, selected_scanner, need_license=False,
                       output_path="", output_file="", output_extension=""):
    """
    Create report files for given scanned result.

    :param start_time: start time of scanning.
    :param scanned_result: scanned result.
    :param license_list: matched text (only for scancode).
    :param need_license: if requested, output matched text (only for scancode).
    """
    extended_header = {}
    _result_log = {}
    sheet_list = {}
    _json_ext = ".json"

    if output_path == "":
        output_path = os.getcwd()
    else:
        output_path = os.path.abspath(output_path)

    if output_file == "":
        if output_extension == _json_ext:
            output_file = "Opossum_input_" + start_time
        else:
            output_file = "FOSSLight-Report_" + start_time

    scanned_result = sorted(scanned_result, key=lambda row: (''.join(row.licenses)))

    if selected_scanner == 'scancode' or output_extension == _json_ext:
        sheet_list[SCANOSS_SHEET_NAME] = [scan_item.get_row_to_print() for scan_item in scanned_result]

    else:
        sheet_list[SCANOSS_SHEET_NAME] = [scan_item.get_row_to_print_for_scanoss() for scan_item in scanned_result]
        extended_header = SCANOSS_HEADER

    if need_license:
        sheet_list["matched_text"] = get_license_list_to_print(license_list)

    output_file_without_ext = os.path.join(output_path, output_file)
    success_to_write, writing_msg = write_output_file(output_file_without_ext, output_extension, sheet_list, extended_header)
    logger.info("Writing Output file(" + output_file + output_extension + "):"
                + str(success_to_write) + " " + writing_msg)
    if success_to_write:
        _result_log["Output file"] = output_file_without_ext + output_extension


def run_all_scanners(path_to_scan, output_file_name="", _write_json_file=False, num_cores=-1,
                     need_license=False, format="", called_by_cli=False):
    """
    Run Scancode and scanoss.py for the given path.

    :param path_to_scan: path of sourcecode to scan.
    :param output_file_name: path or file name (with path) for the output.
    :param _write_json_file: if requested, keep the raw files.
    :param num_cores: number of cores used for scancode scanning.
    :param need_license: if requested, output matched text (only for scancode).
    :param format: output format (excel, csv, opossum).
    :param called_by_cli: if not called by cli, initialize logger.
    :return success: success or failure of scancode.
    :return _result_log["Scan Result"]:
    :return merged_result: merged scan result of scancode and scanoss.
    :return license_list: matched text.(only for scancode)
    """
    scancode_result = []
    scanoss_result = []
    merged_result = []
    _result_log = {}
    success = True

    success, _result_log["Scan Result"], scancode_result, license_list = run_scan(path_to_scan, output_file_name,
                                                                                  _write_json_file, num_cores,
                                                                                  True, need_license,
                                                                                  format, called_by_cli)
    scanoss_result = run_scanoss_py(path_to_scan, output_file_name, format, called_by_cli, _write_json_file)

    for file_in_scancode_result in scancode_result:
        per_file_result = copy.deepcopy(file_in_scancode_result)
        if per_file_result in scanoss_result:
            per_file_result.merge_scan_item(scanoss_result.pop(scanoss_result.index(file_in_scancode_result)))
        merged_result.append(per_file_result)
    if scanoss_result:
        for file_left_in_scanoss_result in scanoss_result:
            merged_result.append(file_left_in_scanoss_result)

    return success, _result_log["Scan Result"], merged_result, license_list


if __name__ == '__main__':
    main()
