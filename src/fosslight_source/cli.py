#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import sys
import os
import warnings
import logging
import copy
from datetime import datetime
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from fosslight_util.timer_thread import TimerThread
from ._help import print_version, print_help_msg_source_scanner
from ._license_matched import get_license_list_to_print
from fosslight_util.output_format import check_output_format, write_output_file
from .run_scancode import run_scan
from .run_scanoss import run_scanoss_py
from .run_scanoss import get_scanoss_extra_info
import yaml
import argparse

SCANOSS_SHEET_NAME = 'SRC_FL_Source'
SCANOSS_HEADER = {SCANOSS_SHEET_NAME: ['ID', 'Source Name or Path', 'OSS Name',
                                       'OSS Version', 'License', 'Download Location',
                                       'Homepage', 'Copyright Text', 'Exclude',
                                       'Comment']}
MERGED_HEADER = {SCANOSS_SHEET_NAME: ['ID', 'Source Name or Path', 'OSS Name',
                                      'OSS Version', 'License', 'Download Location',
                                      'Homepage', 'Copyright Text', 'Exclude',
                                      'Comment', 'license_reference']}

logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_PKG_NAME = "fosslight_source"


def main():
    global logger
    success = True
    _result_log = {}

    path_to_scan = os.getcwd()
    write_json_file = False
    output_file_name = ""
    print_matched_text = False
    format = ""
    selected_scanner = ""

    scanned_result = []
    license_list = []
    time_out = 120
    core = -1

    parser = argparse.ArgumentParser(description='FOSSLight Source', prog='fosslight_source', add_help=False)
    parser.add_argument('-h', '--help', action='store_true', required=False)
    parser.add_argument('-v', '--version', action='store_true', required=False)
    parser.add_argument('-p', '--path', nargs=1, type=str, required=False)
    parser.add_argument('-j', '--json', action='store_true', required=False)
    parser.add_argument('-o', '--output', nargs=1, type=str, required=False, default="")
    parser.add_argument('-m', '--matched', action='store_true', required=False)
    parser.add_argument('-f', '--format', nargs=1, type=str, required=False)
    parser.add_argument('-s', '--scanner', nargs=1, type=str, required=False, default='all')
    parser.add_argument('-t', '--timeout', type=int, required=False, default=120)
    parser.add_argument('-c', '--cores', type=int, required=False, default=-1)

    args = parser.parse_args()

    if args.help:
        print_help_msg_source_scanner()
    if args.version:
        print_version(_PKG_NAME)
    if not args.path:
        path_to_scan = os.getcwd()
    else:
        path_to_scan = ''.join(args.path)
    if args.json:
        write_json_file = True
    output_file_name = ''.join(args.output)
    if args.matched:
        print_matched_text = True
    if args.format:
        format = ''.join(args.format)
    if args.scanner:
        selected_scanner = ''.join(args.scanner)

    time_out = args.timeout
    core = args.cores

    timer = TimerThread()
    timer.setDaemon(True)
    timer.start()

    _start_time = datetime.now().strftime('%y%m%d_%H%M')
    success, msg, output_path, output_file, output_extension = check_output_format(output_file_name, format)
    if output_extension != '.xlsx' and print_matched_text:
        logger.warning("-m option is only available for excel.")
        print_matched_text = False
    if not success:
        logger.error(f"Format error. {msg}")
        sys.exit(1)
    logger, _result_log = init_log(os.path.join(output_path, f"fosslight_log_{_start_time}.txt"),
                                   True, logging.INFO, logging.DEBUG, _PKG_NAME, path_to_scan)

    if os.path.isdir(path_to_scan):
        if selected_scanner == 'scancode':
            success, _result_log["Scan Result"], scanned_result, license_list = run_scan(path_to_scan, output_file_name,
                                                                                         write_json_file, core, True,
                                                                                         print_matched_text, format, True,
                                                                                         time_out)
        elif selected_scanner == 'scanoss':
            scanned_result = run_scanoss_py(path_to_scan, output_file_name, format, True, write_json_file)
        elif selected_scanner == 'all' or selected_scanner == '':
            success, _result_log["Scan Result"], scanned_result, license_list = run_all_scanners(path_to_scan, output_file_name,
                                                                                                 write_json_file, core,
                                                                                                 print_matched_text, format, True,
                                                                                                 time_out)
        else:
            print_help_msg_source_scanner()
            sys.exit(1)
        create_report_file(_start_time, scanned_result, license_list, selected_scanner, print_matched_text,
                           output_path, output_file, output_extension)
        try:
            logger.info(yaml.safe_dump(_result_log, allow_unicode=True, sort_keys=True))
        except Exception as ex:
            logger.debug(f"Failed to print log.: {ex}")
    else:
        logger.error(f"Check the path to scan. : {path_to_scan}")
        sys.exit(1)


def create_report_file(_start_time, scanned_result, license_list, selected_scanner, need_license=False,
                       output_path="", output_file="", output_extension=""):
    """
    Create report files for given scanned result.

    :param start_time: start time of scanning.
    :param scanned_result: scanned result.
    :param license_list: matched text (only for scancode).
    :param need_license: if requested, output matched text (only for scancode).
    """
    extended_header = {}
    sheet_list = {}
    _json_ext = ".json"

    if output_path == "":
        output_path = os.getcwd()
    else:
        output_path = os.path.abspath(output_path)

    if output_file == "":
        if output_extension == _json_ext:
            output_file = f"fosslight_opossum_{_start_time}"
        else:
            output_file = f"fosslight_report_{_start_time}"

    if scanned_result:
        scanned_result = sorted(scanned_result, key=lambda row: (''.join(row.licenses)))

        if selected_scanner == 'scancode' or output_extension == _json_ext:
            sheet_list[SCANOSS_SHEET_NAME] = [scan_item.get_row_to_print() for scan_item in scanned_result]

        elif selected_scanner == 'scanoss':
            sheet_list[SCANOSS_SHEET_NAME] = [scan_item.get_row_to_print_for_scanoss() for scan_item in scanned_result]
            extended_header = SCANOSS_HEADER

        else:
            sheet_list[SCANOSS_SHEET_NAME] = [scan_item.get_row_to_print_for_all_scanner() for scan_item in scanned_result]
            extended_header = MERGED_HEADER

        if need_license:
            if selected_scanner == 'scancode' or output_extension == _json_ext:
                sheet_list["scancode_reference"] = get_license_list_to_print(license_list)
            elif selected_scanner == 'scanoss':
                sheet_list["scanoss_reference"] = get_scanoss_extra_info(scanned_result)
            else:
                sheet_list["scancode_reference"] = get_license_list_to_print(license_list)
                sheet_list["scanoss_reference"] = get_scanoss_extra_info(scanned_result)

    output_file_without_ext = os.path.join(output_path, output_file)
    success_to_write, writing_msg, result_file = write_output_file(output_file_without_ext, output_extension,
                                                                   sheet_list, extended_header)
    if success_to_write:
        if result_file:
            logger.info(f"Output file:{result_file}")
        else:
            logger.warning(f"{writing_msg}")
    else:
        logger.error(f"Fail to generate result file. msg:({writing_msg})")


def run_all_scanners(path_to_scan, output_file_name="", _write_json_file=False, num_cores=-1,
                     need_license=False, format="", called_by_cli=True, time_out=120):
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
                                                                                  format, called_by_cli, time_out)
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
