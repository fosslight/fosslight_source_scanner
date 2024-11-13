#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import sys
import os
import platform
import warnings
import logging
from datetime import datetime
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from fosslight_util.timer_thread import TimerThread
from ._help import print_version, print_help_msg_source_scanner
from ._license_matched import get_license_list_to_print
from fosslight_util.output_format import check_output_formats_v2, write_output_file
from fosslight_util.correct import correct_with_yaml
from .run_scancode import run_scan
from .run_scanoss import run_scanoss_py
from .run_scanoss import get_scanoss_extra_info
import yaml
import argparse
from .run_spdx_extractor import get_spdx_downloads
from ._scan_item import SourceItem
from fosslight_util.oss_item import ScannerItem
from typing import Tuple

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
PKG_NAME = "fosslight_source"
RESULT_KEY = "Scan Result"


def main() -> None:
    global logger
    _result_log = {}

    path_to_scan = os.getcwd()
    path_to_exclude = []
    write_json_file = False
    output_file_name = ""
    print_matched_text = False
    formats = []
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
    parser.add_argument('-f', '--formats', nargs='*', type=str, required=False)
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
        print_version(PKG_NAME)
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
    if args.formats:
        formats = list(args.formats)
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
                              print_matched_text, formats, time_out, correct_mode, correct_filepath,
                              selected_scanner, path_to_exclude)

        _result_log["Scan Result"] = result[1]

        try:
            logger.info(yaml.safe_dump(_result_log, allow_unicode=True, sort_keys=True))
        except Exception as ex:
            logger.debug(f"Failed to print log.: {ex}")
    else:
        logger.error(f"(-p option) Input path({path_to_scan}) is not a directory. Please enter a valid path.")
        sys.exit(1)


def count_files(path_to_scan: str, path_to_exclude: list) -> Tuple[int, int]:
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


def create_report_file(
    _start_time: str, merged_result: list,
    license_list: list, scanoss_result: list,
    selected_scanner: str, need_license: bool = False,
    output_path: str = "", output_files: list = [],
    output_extensions: list = [], correct_mode: bool = True,
    correct_filepath: str = "", path_to_scan: str = "", path_to_exclude: list = [],
    formats: list = []
) -> 'ScannerItem':
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

    if not output_files:
        # If -o does not contains file name, set default name
        while len(output_files) < len(output_extensions):
            output_files.append(None)
        to_remove = []  # elements of spdx format on windows that should be removed
        for i, output_extension in enumerate(output_extensions):
            if output_files[i] is None or output_files[i] == "":
                if formats:
                    if formats[i].startswith('spdx'):
                        if platform.system() != 'Windows':
                            output_files[i] = f"fosslight_spdx_src_{_start_time}"
                        else:
                            logger.warning('spdx format is not supported on Windows. Please remove spdx from format.')
                            to_remove.append(i)
                    else:
                        if output_extension == _json_ext:
                            output_files[i] = f"fosslight_opossum_src_{_start_time}"
                        else:
                            output_files[i] = f"fosslight_report_src_{_start_time}"
                else:
                    if output_extension == _json_ext:
                        output_files[i] = f"fosslight_opossum_src_{_start_time}"
                    else:
                        output_files[i] = f"fosslight_report_src_{_start_time}"
        for index in sorted(to_remove, reverse=True):
            # remove elements of spdx format on windows
            del output_files[index]
            del output_extensions[index]
            del formats[index]
        if len(output_extensions) < 1:
            sys.exit(0)

    if not correct_filepath:
        correct_filepath = path_to_scan

    scan_item = ScannerItem(PKG_NAME, _start_time)
    scan_item.set_cover_pathinfo(path_to_scan, path_to_exclude)
    files_count, removed_files_count = count_files(path_to_scan, path_to_exclude)

    scan_item.set_cover_comment(f"Total number of files : {files_count}")
    scan_item.set_cover_comment(f"Removed files : {removed_files_count}")

    if not merged_result:
        if files_count < 1:
            scan_item.set_cover_comment("(No file detected.)")
        else:
            scan_item.set_cover_comment("(No OSS detected.)")

    if merged_result:
        sheet_list = {}
        scan_item.append_file_items(merged_result, PKG_NAME)

        if selected_scanner == 'scanoss':
            extended_header = SCANOSS_HEADER
        else:
            extended_header = MERGED_HEADER

        if need_license:
            if selected_scanner == 'scancode':
                sheet_list["scancode_reference"] = get_license_list_to_print(license_list)
            elif selected_scanner == 'scanoss':
                sheet_list["scanoss_reference"] = get_scanoss_extra_info(scanoss_result)
            else:
                sheet_list["scancode_reference"] = get_license_list_to_print(license_list)
                sheet_list["scanoss_reference"] = get_scanoss_extra_info(scanoss_result)
            if sheet_list:
                scan_item.external_sheets = sheet_list

    if correct_mode:
        success, msg_correct, correct_item = correct_with_yaml(correct_filepath, path_to_scan, scan_item)
        if not success:
            logger.info(f"No correction with yaml: {msg_correct}")
        else:
            scan_item = correct_item
            logger.info("Success to correct with yaml.")

    combined_paths_and_files = [os.path.join(output_path, file) for file in output_files]
    results = []
    for combined_path_and_file, output_extension, output_format in zip(combined_paths_and_files, output_extensions, formats):
        # if need_license and output_extension == _json_ext and "scanoss_reference" in sheet_list:
        #     del sheet_list["scanoss_reference"]
        results.append(write_output_file(combined_path_and_file, output_extension, scan_item, extended_header, "", output_format))
    for success, msg, result_file in results:
        if success:
            logger.info(f"Output file: {result_file}")
            for row in scan_item.get_cover_comment():
                logger.info(row)
        else:
            logger.error(f"Fail to generate result file {result_file}. msg:({msg})")
    return scan_item


def merge_results(scancode_result: list = [], scanoss_result: list = [], spdx_downloads: dict = {}) -> list:
    """
    Merge scanner results and spdx parsing result.
    :param scancode_result: list of scancode results in SourceItem.
    :param scanoss_result: list of scanoss results in SourceItem.
    :param spdx_downloads: dictionary of spdx parsed results.
    :return merged_result: list of merged result in SourceItem.
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
                new_result_item = SourceItem(file_name)
                new_result_item.download_location = download_location
                scancode_result.append(new_result_item)

    for item in scancode_result:
        item.set_oss_item()

    return scancode_result


def run_scanners(
    path_to_scan: str, output_file_name: str = "",
    write_json_file: bool = False, num_cores: int = -1,
    called_by_cli: bool = True, print_matched_text: bool = False,
    formats: list = [], time_out: int = 120,
    correct_mode: bool = True, correct_filepath: str = "",
    selected_scanner: str = 'all', path_to_exclude: list = []
) -> Tuple[bool, str, 'ScannerItem', list, list]:
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
    scan_item = []

    success, msg, output_path, output_files, output_extensions, formats = check_output_formats_v2(output_file_name, formats)

    logger, result_log = init_log(os.path.join(output_path, f"fosslight_log_src_{start_time}.txt"),
                                  True, logging.INFO, logging.DEBUG, PKG_NAME, path_to_scan, path_to_exclude)

    if '.xlsx' not in output_extensions and print_matched_text:
        logger.warning("-m option is only available for excel.")
        print_matched_text = False

    if success:
        if selected_scanner == 'scancode' or selected_scanner == 'all' or selected_scanner == '':
            success, result_log[RESULT_KEY], scancode_result, license_list = run_scan(path_to_scan, output_file_name,
                                                                                      write_json_file, num_cores, True,
                                                                                      print_matched_text, formats, called_by_cli,
                                                                                      time_out, correct_mode, correct_filepath)
        if selected_scanner == 'scanoss' or selected_scanner == 'all' or selected_scanner == '':
            scanoss_result = run_scanoss_py(path_to_scan, output_file_name, formats, True, write_json_file, num_cores,
                                            path_to_exclude)
        if selected_scanner in SCANNER_TYPE:
            spdx_downloads = get_spdx_downloads(path_to_scan, path_to_exclude)
            merged_result = merge_results(scancode_result, scanoss_result, spdx_downloads)
            scan_item = create_report_file(start_time, merged_result, license_list, scanoss_result, selected_scanner,
                                           print_matched_text, output_path, output_files, output_extensions, correct_mode,
                                           correct_filepath, path_to_scan, path_to_exclude, formats)
        else:
            print_help_msg_source_scanner()
            result_log[RESULT_KEY] = "Unsupported scanner"
            success = False
    else:
        result_log[RESULT_KEY] = f"Format error. {msg}"
        success = False
    return success, result_log.get(RESULT_KEY, ""), scan_item, license_list, scanoss_result


if __name__ == '__main__':
    main()
