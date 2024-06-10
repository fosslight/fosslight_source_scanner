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
from fosslight_util.cover import CoverItem

SRC_SHEET_NAME = 'SRC_FL_Source'
SCANOSS_HEADER = {SRC_SHEET_NAME: ['ID', 'Source Path', 'OSS Name',
                                   'OSS Version', 'License', 'Download Location',
                                   'Homepage', 'Copyright Text', 'Exclude', 'Comment']}
MERGED_HEADER = {SRC_SHEET_NAME: ['ID', 'Source Path', 'OSS Name',
                                  'OSS Version', 'License', 'Download Location',
                                  'Homepage', 'Copyright Text', 'Exclude', 'Comment', 'license_reference']}
SCANNER_TYPE = ['scancode', 'scanoss', 'all', '']

logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_PKG_NAME = "fosslight_source"
RESULT_KEY = "Scan Result"


def main():
    global logger
    _result_log = {}

    path_to_scan = os.getcwd()
    path_to_exclude = []
    write_json_file = False
    output_file_name = ""
    print_matched_text = False
    format = ""
    selected_scanner = ""
    correct_mode = True

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
    parser.add_argument('-e', '--exclude', nargs='*', required=False, default=[])
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
    if args.exclude:
        path_to_exclude = args.exclude
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

    if os.path.isdir(path_to_scan):
        result = []
        result = run_scanners(path_to_scan, output_file_name, write_json_file, core, True,
                              print_matched_text, format, time_out, correct_mode, correct_filepath,
                              selected_scanner, path_to_exclude)
        _result_log["Scan Result"] = result[1]

        try:
            logger.info(yaml.safe_dump(_result_log, allow_unicode=True, sort_keys=True))
        except Exception as ex:
            logger.debug(f"Failed to print log.: {ex}")
    else:
        logger.error(f"Check the path to scan. : {path_to_scan}")
        sys.exit(1)


def count_files(path_to_scan, path_to_exclude):
    total_files = 0
    excluded_files = 0
    abs_path_to_exclude = [os.path.abspath(os.path.join(path_to_scan, path)) for path in path_to_exclude]

    for root, _, files in os.walk(path_to_scan):
        for file in files:
            file_path = os.path.join(root, file)
            abs_file_path = os.path.abspath(file_path)
            if any(os.path.commonpath([abs_file_path, exclude_path]) == exclude_path
                   for exclude_path in abs_path_to_exclude):
                excluded_files += 1
            total_files += 1

    return total_files, excluded_files


def create_report_file(_start_time, merged_result, license_list, scanoss_result, selected_scanner, need_license=False,
                       output_path="", output_file="", output_extension="", correct_mode=True, correct_filepath="",
                       path_to_scan="", path_to_exclude=[]):
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

    cover = CoverItem(tool_name=_PKG_NAME,
                      start_time=_start_time,
                      input_path=path_to_scan,
                      exclude_path=path_to_exclude)
    files_count, removed_files_count = count_files(path_to_scan, path_to_exclude)
    cover.comment = f"Total number of files / removed files: {files_count} / {removed_files_count}"
    if len(merged_result) == 0:
        if files_count < 1:
            cover.comment += "(No file detected.)"
        else:
            cover.comment += "(No OSS detected.)"

    sheet_list[SRC_SHEET_NAME] = []
    if merged_result:
        for scan_item in merged_result:
            for row in scan_item.get_row_to_print():
                sheet_list[SRC_SHEET_NAME].append(row)

        if selected_scanner == 'scanoss':
            extended_header = SCANOSS_HEADER
        else:
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
                                                                   sheet_list, extended_header, "", cover)
    if success_to_write:
        if result_file:
            logger.info(f"Output file:{result_file}")
            logger.info(f'{cover.comment}')
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


def run_scanners(path_to_scan, output_file_name="", write_json_file=False, num_cores=-1, called_by_cli=True,
                 print_matched_text=False, format="", time_out=120, correct_mode=True, correct_filepath="",
                 selected_scanner='all', path_to_exclude=[]):
    """
    Run Scancode and scanoss.py for the given path.

    :param path_to_scan: path of sourcecode to scan.
    :param output_file_name: path or file name (with path) for the output.
    :param write_json_file: if requested, keep the raw files.
    :param num_cores: number of cores used for scancode scanning.
    :param called_by_cli: if not called by cli, initialize logger.
    :param print_matched_text: if requested, output matched text (only for scancode).
    :param format: output format (excel, csv, opossum).
    :return success: success or failure of scancode.
    :return result_log["Scan Result"]:
    :return merged_result: merged scan result of scancode and scanoss.
    :return license_list: matched text.(only for scancode)
    """
    global logger

    start_time = datetime.now().strftime('%y%m%d_%H%M')
    scancode_result = []
    scanoss_result = []
    merged_result = []
    license_list = []
    spdx_downloads = {}
    result_log = {}

    success, msg, output_path, output_file, output_extension = check_output_format(output_file_name, format)
    logger, result_log = init_log(os.path.join(output_path, f"fosslight_log_src_{start_time}.txt"),
                                  True, logging.INFO, logging.DEBUG, _PKG_NAME, path_to_scan, path_to_exclude)
    if output_extension != '.xlsx' and output_extension and print_matched_text:
        logger.warning("-m option is only available for excel.")
        print_matched_text = False
    if success:
        if selected_scanner == 'scancode' or selected_scanner == 'all' or selected_scanner == '':
            success, result_log[RESULT_KEY], scancode_result, license_list = run_scan(path_to_scan, output_file_name,
                                                                                      write_json_file, num_cores, True,
                                                                                      print_matched_text, format, called_by_cli,
                                                                                      time_out, correct_mode, correct_filepath,
                                                                                      path_to_exclude)
        if selected_scanner == 'scanoss' or selected_scanner == 'all' or selected_scanner == '':
            scanoss_result = run_scanoss_py(path_to_scan, output_file_name, format, True,
                                            write_json_file, num_cores, path_to_exclude)
        if selected_scanner in SCANNER_TYPE:
            spdx_downloads = get_spdx_downloads(path_to_scan, path_to_exclude)
            merged_result = merge_results(scancode_result, scanoss_result, spdx_downloads)
            create_report_file(start_time, merged_result, license_list, scanoss_result, selected_scanner,
                               print_matched_text, output_path, output_file, output_extension, correct_mode,
                               correct_filepath, path_to_scan, path_to_exclude)
        else:
            print_help_msg_source_scanner()
            result_log[RESULT_KEY] = "Unsupported scanner"
            success = False
    else:
        result_log[RESULT_KEY] = f"Format error. {msg}"
        success = False

    return success, result_log.get(RESULT_KEY, ""), merged_result, license_list, scanoss_result


if __name__ == '__main__':
    main()
