#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import sys
import os
import warnings
import logging
from datetime import datetime
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from fosslight_util.timer_thread import TimerThread
from ._help import print_version, print_help_msg_source_scanner
from ._license_matched import get_license_list_to_print
from fosslight_util.output_format import check_output_format, write_output_file
from fosslight_util.correct import correct_with_yaml
from .run_scancode import run_scan
from .run_scanoss import run_scanoss_py
from .run_scanoss import get_scanoss_extra_info
import yaml
import argparse
from .run_spdx_extractor import get_spdx_downloads
from ._scan_item import ScanItem

SRC_SHEET_NAME = 'SRC_FL_Source'
SCANOSS_HEADER = {SRC_SHEET_NAME: ['ID', 'Source Name or Path', 'OSS Name',
                                   'OSS Version', 'License', 'Download Location',
                                   'Homepage', 'Copyright Text', 'Exclude', 'Comment']}
MERGED_HEADER = {SRC_SHEET_NAME: ['ID', 'Source Name or Path', 'OSS Name',
                                  'OSS Version', 'License', 'Download Location',
                                  'Homepage', 'Copyright Text', 'Exclude', 'Comment', 'license_reference']}
SCANNER_TYPE = ['scancode', 'scanoss', 'all', '']

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
    correct_mode = True

    license_list = []
    scanoss_result = []
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
    parser.add_argument('--no_correction', action='store_true', required=False)
    parser.add_argument('--correct_fpath', nargs=1, type=str, required=False)

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
    if args.no_correction:
        correct_mode = False
    correct_filepath = path_to_scan
    if args.correct_fpath:
        correct_filepath = ''.join(args.correct_fpath)

    time_out = args.timeout
    core = args.cores

    timer = TimerThread()
    timer.setDaemon(True)
    timer.start()

    _start_time = datetime.now().strftime('%y%m%d_%H%M')
    success, msg, output_path, output_file, output_extension = check_output_format(output_file_name, format)
    if output_extension != '.xlsx' and output_extension != "" and print_matched_text:
        logger.warning("-m option is only available for excel.")
        print_matched_text = False
    if not success:
        logger.error(f"Format error. {msg}")
        sys.exit(1)
    logger, _result_log = init_log(os.path.join(output_path, f"fosslight_log_src_{_start_time}.txt"),
                                   True, logging.INFO, logging.DEBUG, _PKG_NAME, path_to_scan)

    if os.path.isdir(path_to_scan):
        scancode_result = []
        scanoss_result = []
        merged_result = []
        spdx_downloads = {}
        success = True

        if selected_scanner == 'scancode' or selected_scanner == 'all' or selected_scanner == '':
            success, _result_log["Scan Result"], scancode_result, license_list = run_scan(path_to_scan, output_file_name,
                                                                                          write_json_file, core, True,
                                                                                          print_matched_text, format, True,
                                                                                          time_out, correct_mode,
                                                                                          correct_filepath)
        if selected_scanner == 'scanoss' or selected_scanner == 'all' or selected_scanner == '':
            scanoss_result = run_scanoss_py(path_to_scan, output_file_name, format, True, write_json_file)
        if selected_scanner not in SCANNER_TYPE:
            print_help_msg_source_scanner()
            sys.exit(1)
        spdx_downloads = get_spdx_downloads(path_to_scan)
        merged_result = merge_results(scancode_result, scanoss_result, spdx_downloads)
        create_report_file(_start_time, merged_result, license_list, scanoss_result, selected_scanner, print_matched_text,
                           output_path, output_file, output_extension, correct_mode, correct_filepath, path_to_scan)

        try:
            logger.info(yaml.safe_dump(_result_log, allow_unicode=True, sort_keys=True))
        except Exception as ex:
            logger.debug(f"Failed to print log.: {ex}")
    else:
        logger.error(f"Check the path to scan. : {path_to_scan}")
        sys.exit(1)


def create_report_file(_start_time, merged_result, license_list, scanoss_result, selected_scanner, need_license=False,
                       output_path="", output_file="", output_extension="", correct_mode=True, correct_filepath="",
                       path_to_scan=""):
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

    if not correct_filepath:
        correct_filepath = path_to_scan

    if output_file == "":
        if output_extension == _json_ext:
            output_file = f"fosslight_opossum_src_{_start_time}"
        else:
            output_file = f"fosslight_report_src_{_start_time}"

    if merged_result:
        if selected_scanner == 'scancode' or output_extension == _json_ext:
            sheet_list[SRC_SHEET_NAME] = []
            for scan_item in merged_result:
                for row in scan_item.get_row_to_print():
                    sheet_list[SRC_SHEET_NAME].append(row)

        elif selected_scanner == 'scanoss':
            sheet_list[SRC_SHEET_NAME] = []
            for scan_item in merged_result:
                for row in scan_item.get_row_to_print():
                    sheet_list[SRC_SHEET_NAME].append(row)
            extended_header = SCANOSS_HEADER

        else:
            sheet_list[SRC_SHEET_NAME] = []
            for scan_item in merged_result:
                for row in scan_item.get_row_to_print():
                    sheet_list[SRC_SHEET_NAME].append(row)
            extended_header = MERGED_HEADER

        if need_license:
            if selected_scanner == 'scancode' or output_extension == _json_ext:
                sheet_list["scancode_reference"] = get_license_list_to_print(license_list)
            elif selected_scanner == 'scanoss':
                sheet_list["scanoss_reference"] = get_scanoss_extra_info(scanoss_result)
            else:
                sheet_list["scancode_reference"] = get_license_list_to_print(license_list)
                sheet_list["scanoss_reference"] = get_scanoss_extra_info(scanoss_result)

    if correct_mode:
        success, msg_correct, correct_list = correct_with_yaml(correct_filepath, path_to_scan, sheet_list)
        if not success:
            logger.info(f"No correction with yaml: {msg_correct}")
        else:
            sheet_list = correct_list
            logger.info("Success to correct with yaml.")

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


def merge_results(scancode_result=[], scanoss_result=[], spdx_downloads={}):
    """
    Merge scanner results and spdx parsing result.
    :param scancode_result: list of scancode results in ScanItem.
    :param scanoss_result: list of scanoss results in ScanItem.
    :param spdx_downloads: dictionary of spdx parsed results.
    :return merged_result: list of merged result in ScanItem.
    """

    # If anything that is found at SCANOSS only exist, add it to result.
    scancode_result.extend([item for item in scanoss_result if item not in scancode_result])

    # If download loc. in SPDX form found, overwrite the scanner result.
    # If scanner result doesn't exist, create a new row.
    if spdx_downloads:
        for file_name, download_location in spdx_downloads.items():
            if file_name in scancode_result:
                merged_result_item = scancode_result[scancode_result.index(file_name)]
                merged_result_item.download_location = download_location
            else:
                new_result_item = ScanItem(file_name)
                new_result_item.download_location = download_location
                scancode_result.append(new_result_item)
    return scancode_result


if __name__ == '__main__':
    main()
