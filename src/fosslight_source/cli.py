#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import sys
import os
import platform
import time
import warnings
import logging
import urllib.request
import urllib.error
from datetime import datetime
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from ._help import print_version, print_help_msg_source_scanner
from ._license_matched import get_license_list_to_print
from fosslight_util.output_format import check_output_formats_v2, write_output_file
from fosslight_util.correct import correct_with_yaml
from .run_scancode import run_scan
from fosslight_util.exclude import get_excluded_paths
from .run_scanoss import run_scanoss_py
from .run_scanoss import get_scanoss_extra_info
import yaml
import argparse
from .run_spdx_extractor import get_spdx_downloads
from .run_manifest_extractor import get_manifest_licenses
from ._scan_item import SourceItem, KB_URL
from fosslight_util.oss_item import ScannerItem
from typing import Tuple
from ._scan_item import is_manifest_file
import shutil


SRC_SHEET_NAME = 'SRC_FL_Source'
SCANOSS_HEADER = {SRC_SHEET_NAME: ['ID', 'Source Path', 'OSS Name',
                                   'OSS Version', 'License', 'Download Location',
                                   'Homepage', 'Copyright Text', 'Exclude', 'Comment']}
MERGED_HEADER = {SRC_SHEET_NAME: ['ID', 'Source Path', 'OSS Name',
                                  'OSS Version', 'License', 'Download Location',
                                  'Homepage', 'Copyright Text', 'Exclude', 'Comment', 'license_reference']}
KB_REFERENCE_HEADER = ['ID', 'Source Path', 'KB Origin URL', 'Evidence']
ALL_MODE = 'all'
SCANNER_TYPE = ['kb', 'scancode', 'scanoss', ALL_MODE]


logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
PKG_NAME = "fosslight_source"
RESULT_KEY = "Scan Result"


def main() -> None:
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
    parser.add_argument('-s', '--scanner', nargs=1, type=str, required=False, default=ALL_MODE)
    parser.add_argument('-t', '--timeout', type=int, required=False, default=120)
    parser.add_argument('-c', '--cores', type=int, required=False, default=-1)
    parser.add_argument('-e', '--exclude', nargs='*', required=False, default=[])
    parser.add_argument('--no_correction', action='store_true', required=False)
    parser.add_argument('--correct_fpath', nargs=1, type=str, required=False)
    parser.add_argument('--hide_progress', action='store_true', required=False)

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
    hide_progress = args.hide_progress

    time_out = args.timeout
    core = args.cores

    if os.path.isdir(path_to_scan):
        result = []
        result = run_scanners(path_to_scan, output_file_name, write_json_file, core, True,
                              print_matched_text, formats, time_out, correct_mode, correct_filepath,
                              selected_scanner, path_to_exclude, hide_progress=hide_progress)

        _result_log["Scan Result"] = result[1]

        try:
            logger.info(yaml.safe_dump(_result_log, allow_unicode=True, sort_keys=True))
        except Exception as ex:
            logger.debug(f"Failed to print log.: {ex}")
    else:
        logger.error(f"(-p option) Input path({path_to_scan}) is not a directory. Please enter a valid path.")
        sys.exit(1)


def create_report_file(
    _start_time: str, merged_result: list,
    license_list: list, scanoss_result: list,
    selected_scanner: str, need_license: bool = False,
    output_path: str = "", output_files: list = [],
    output_extensions: list = [], correct_mode: bool = True,
    correct_filepath: str = "", path_to_scan: str = "", path_to_exclude: list = [],
    formats: list = [], api_limit_exceed: bool = False, files_count: int = 0, final_output_path: str = "",
    run_kb_msg: str = ""
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

    output_path = os.path.abspath(output_path)

    if not output_files:
        # If -o does not contains file name, set default name
        while len(output_files) < len(output_extensions):
            output_files.append(None)
        to_remove = []  # elements of spdx format on windows that should be removed
        for i, output_extension in enumerate(output_extensions):
            if output_files[i] is None or output_files[i] == "":
                if formats:
                    if formats[i].startswith('spdx') or formats[i].startswith('cyclonedx'):
                        if platform.system() == 'Windows':
                            logger.warning(f'{formats[i]} is not supported on Windows.Please remove {formats[i]} from format.')
                            to_remove.append(i)
                        else:
                            if formats[i].startswith('spdx'):
                                output_files[i] = f"fosslight_spdx_src_{_start_time}"
                            elif formats[i].startswith('cyclonedx'):
                                output_files[i] = f'fosslight_cyclonedx_src_{_start_time}'
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
    scan_item.set_cover_comment(f"Scanned files: {files_count}")

    if merged_result:
        scan_item.set_cover_comment(f"Detected source : {len(merged_result)}")
    else:
        if files_count < 1:
            scan_item.set_cover_comment("(No file detected.)")
        else:
            scan_item.set_cover_comment("(No OSS detected.)")

    if api_limit_exceed:
        scan_item.set_cover_comment("SCANOSS skipped (API limits)")

    if run_kb_msg:
        scan_item.set_cover_comment(run_kb_msg)
    display_mode = selected_scanner
    if selected_scanner == ALL_MODE:
        display_mode = ", ".join([s for s in SCANNER_TYPE if s != ALL_MODE])
    scan_item.set_cover_comment(f"Mode : {display_mode}")

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
            elif selected_scanner == 'kb':
                kb_ref = get_kb_reference_to_print(merged_result)
                sheet_list["kb_reference"] = kb_ref
            else:
                sheet_list["scancode_reference"] = get_license_list_to_print(license_list)
                sheet_list["scanoss_reference"] = get_scanoss_extra_info(scanoss_result)
                kb_ref = get_kb_reference_to_print(merged_result)
                sheet_list["kb_reference"] = kb_ref

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
        final_result_file = result_file.replace(output_path, final_output_path)
        if success:
            logger.info(f"Output file: {final_result_file}")
            for row in scan_item.get_cover_comment():
                logger.info(row)
        else:
            logger.error(f"Fail to generate result file {final_result_file}. msg:({msg})")
    return scan_item


def check_kb_server_reachable() -> bool:
    for attempt in range(3):
        try:
            request = urllib.request.Request(f"{KB_URL}health", method='GET')
            with urllib.request.urlopen(request, timeout=10) as response:
                logger.debug(f"KB server is reachable. Response status: {response.status}")
                return True
        except urllib.error.HTTPError:
            logger.debug("KB server responded (HTTP error), considered reachable")
            return True
        except urllib.error.URLError as e:
            logger.debug(f"KB server is unreachable (timeout or connection error): {e}")
            if attempt < 2:
                time.sleep(1)
            else:
                return False
        except Exception as e:
            logger.debug(f"Unexpected error checking KB server: {e}")
            if attempt < 2:
                time.sleep(1)
            else:
                return False
    return False


def get_kb_reference_to_print(merged_result: list) -> list:
    """
    Build kb_reference sheet rows: file path and URL from _get_origin_url_from_md5_hash.
    :param merged_result: list of SourceItem (merged scan result).
    :return: list of rows, first row is header, rest are [source_path, kb_origin_url].
    """
    rows = [item for item in merged_result if getattr(item, 'kb_origin_url', None)]
    if not rows:
        return [KB_REFERENCE_HEADER]
    rows.sort(key=lambda x: x.source_name_or_path)
    data = [
        [
            item.source_name_or_path,
            item.kb_origin_url,
            str(getattr(item, 'kb_evidence', '') or '')
        ]
        for item in rows
    ]
    data.insert(0, KB_REFERENCE_HEADER)
    return data


def merge_results(
    scancode_result: list = [], scanoss_result: list = [], spdx_downloads: dict = {},
    path_to_scan: str = "", run_kb: bool = False, manifest_licenses: dict = {},
    excluded_files: set = None, hide_progress: bool = False
) -> list:

    """
    Merge scanner results and spdx parsing result.
    :param scancode_result: list of scancode results in SourceItem.
    :param scanoss_result: list of scanoss results in SourceItem.
    :param spdx_downloads: dictionary of spdx parsed results.
    :param path_to_scan: path to the scanned directory for constructing absolute file paths.
    :param run_kb: if True, load kb result.
    :param excluded_files: set of relative paths to exclude from KB-only file discovery.
    :return merged_result: list of merged result in SourceItem.
    """
    if excluded_files is None:
        excluded_files = set()

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
    if manifest_licenses:
        for file_name, licenses in manifest_licenses.items():
            if file_name in scancode_result:
                merged_result_item = scancode_result[scancode_result.index(file_name)]
                # overwrite existing detected licenses with manifest-provided licenses
                merged_result_item.licenses = []  # clear existing licenses (setter clears when value falsy)
                merged_result_item.licenses = licenses
                merged_result_item.is_manifest_file = True
            else:
                new_result_item = SourceItem(file_name)
                new_result_item.licenses = licenses
                new_result_item.is_manifest_file = True
                scancode_result.append(new_result_item)

    for item in scancode_result:
        item.set_oss_item(path_to_scan, run_kb)

    # Add OSSItem for files in path_to_scan that are not in scancode_result
    # when KB returns an origin URL for their MD5 hash (skip excluded_files)
    if run_kb:
        import tqdm
        abs_path_to_scan = os.path.abspath(path_to_scan)
        scancode_paths = {item.source_name_or_path for item in scancode_result}

        files_to_scan = []
        for root, _dirs, files in os.walk(path_to_scan):
            for file in files:
                files_to_scan.append(os.path.join(root, file))

        for file_path in tqdm.tqdm(files_to_scan, desc="KB Scanning", disable=hide_progress):
            rel_path = os.path.relpath(file_path, abs_path_to_scan).replace("\\", "/")
            if rel_path in scancode_paths or rel_path in excluded_files:
                continue
            extra_item = SourceItem(rel_path)
            extra_item.set_oss_item(path_to_scan, run_kb)
            if extra_item.download_location:
                scancode_result.append(extra_item)
                scancode_paths.add(rel_path)

    return scancode_result


def run_scanners(
    path_to_scan: str, output_file_name: str = "",
    write_json_file: bool = False, num_cores: int = -1,
    called_by_cli: bool = True, print_matched_text: bool = False,
    formats: list = [], time_out: int = 120,
    correct_mode: bool = True, correct_filepath: str = "",
    selected_scanner: str = ALL_MODE, path_to_exclude: list = [],
    all_exclude_mode: tuple = (), hide_progress: bool = False
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
    api_limit_exceed = False

    success, msg, output_path, output_files, output_extensions, formats = check_output_formats_v2(output_file_name, formats)

    if output_path == "":
        output_path = os.getcwd()
    final_output_path = output_path
    output_path = os.path.join(os.path.dirname(output_path), f'.fosslight_temp_{start_time}')

    logger, result_log = init_log(os.path.join(output_path, f"fosslight_log_src_{start_time}.txt"),
                                  True, logging.INFO, logging.DEBUG, PKG_NAME, path_to_scan, path_to_exclude)

    if '.xlsx' not in output_extensions and print_matched_text:
        logger.warning("-m option is only available for excel.")
        print_matched_text = False

    if success:
        if all_exclude_mode and len(all_exclude_mode) == 4:
            (excluded_path_with_default_exclusion,
             excluded_path_without_dot,
             excluded_files,
             cnt_file_except_skipped) = all_exclude_mode
        else:
            path_to_exclude_with_filename = path_to_exclude
            (excluded_path_with_default_exclusion,
             excluded_path_without_dot,
             excluded_files,
             cnt_file_except_skipped) = get_excluded_paths(path_to_scan, path_to_exclude_with_filename)
            logger.debug(f"Skipped paths: {excluded_path_with_default_exclusion}")

        if not selected_scanner:
            selected_scanner = ALL_MODE
        if selected_scanner in ['scancode', ALL_MODE]:
            success, result_log[RESULT_KEY], scancode_result, license_list = run_scan(path_to_scan, output_file_name,
                                                                                      write_json_file, num_cores, True,
                                                                                      print_matched_text, formats, called_by_cli,
                                                                                      time_out, correct_mode, correct_filepath,
                                                                                      excluded_path_with_default_exclusion,
                                                                                      excluded_files, hide_progress)
        excluded_files = set(excluded_files) if excluded_files else set()
        if selected_scanner in ['scanoss', ALL_MODE]:
            scanoss_result, api_limit_exceed = run_scanoss_py(path_to_scan, output_path, formats, True, num_cores,
                                                              excluded_path_with_default_exclusion, excluded_files,
                                                              write_json_file, hide_progress)

        run_kb_msg = ""
        if selected_scanner in SCANNER_TYPE:
            run_kb = True if selected_scanner in ['kb', ALL_MODE] else False
            if run_kb:
                if not check_kb_server_reachable():
                    run_kb = False
                    run_kb_msg = "KB Unreachable"
                else:
                    run_kb_msg = "KB Enabled"

            spdx_downloads, manifest_licenses = metadata_collector(path_to_scan, excluded_files)
            merged_result = merge_results(scancode_result, scanoss_result, spdx_downloads,
                                          path_to_scan, run_kb, manifest_licenses, excluded_files, hide_progress)
            scan_item = create_report_file(start_time, merged_result, license_list, scanoss_result, selected_scanner,
                                           print_matched_text, output_path, output_files, output_extensions, correct_mode,
                                           correct_filepath, path_to_scan, excluded_path_without_dot, formats,
                                           api_limit_exceed, cnt_file_except_skipped, final_output_path, run_kb_msg)
        else:
            print_help_msg_source_scanner()
            result_log[RESULT_KEY] = "Unsupported scanner"
            success = False
    else:
        result_log[RESULT_KEY] = f"Format error. {msg}"
        success = False

    try:
        shutil.copytree(output_path, final_output_path, dirs_exist_ok=True)
        shutil.rmtree(output_path)
    except Exception as ex:
        logger.debug(f"Failed to move temp files: {ex}")

    return success, result_log.get(RESULT_KEY, ""), scan_item, license_list, scanoss_result


def metadata_collector(path_to_scan: str, excluded_files: set) -> dict:
    """
    Collect metadata for merging.

    - Traverse files with exclusions applied
    - spdx_downloads: {rel_path: [download_urls]}
    - manifest_licenses: {rel_path: [license_names]}

    :return: (spdx_downloads, manifest_licenses)
    """
    abs_path_to_scan = os.path.abspath(path_to_scan)
    spdx_downloads = {}
    manifest_licenses = {}

    for root, dirs, files in os.walk(path_to_scan):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path_file = os.path.relpath(file_path, abs_path_to_scan).replace('\\', '/')
            if rel_path_file in excluded_files:
                continue

            downloads = get_spdx_downloads(file_path)
            if downloads:
                spdx_downloads[rel_path_file] = downloads

            if is_manifest_file(file_path):
                licenses = get_manifest_licenses(file_path)
                if licenses:
                    manifest_licenses[rel_path_file] = licenses

    return spdx_downloads, manifest_licenses


if __name__ == '__main__':
    main()
