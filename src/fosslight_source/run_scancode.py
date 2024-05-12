#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import multiprocessing
import warnings
import logging
import yaml
from scancode import cli
from datetime import datetime
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from ._parsing_scancode_file_item import parsing_file_item
from ._parsing_scancode_file_item import get_error_from_header
from ._license_matched import get_license_list_to_print
from fosslight_util.output_format import check_output_format
from fosslight_binary.binary_analysis import check_binary

logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_PKG_NAME = "fosslight_source"


def run_scan(path_to_scan, output_file_name="",
             _write_json_file=False, num_cores=-1, return_results=False, need_license=False, format="",
             called_by_cli=False, time_out=120, correct_mode=True, correct_filepath="", path_to_exclude=[]):
    if not called_by_cli:
        global logger

    success = True
    msg = ""
    _str_final_result_log = ""
    _result_log = {}
    result_list = []
    license_list = []
    _json_ext = ".json"
    _start_time = datetime.now().strftime('%y%m%d_%H%M')

    if not correct_filepath:
        correct_filepath = path_to_scan

    success, msg, output_path, output_file, output_extension = check_output_format(output_file_name, format)
    if success:
        if output_path == "":  # if json output with _write_json_file not used, output_path won't be needed.
            output_path = os.getcwd()
        else:
            output_path = os.path.abspath(output_path)

        if not called_by_cli:
            if output_file == "":
                if output_extension == _json_ext:
                    output_file = f"fosslight_opossum_src_{_start_time}"
                else:
                    output_file = f"fosslight_report_src_{_start_time}"

        if _write_json_file:
            output_json_file = os.path.join(output_path, "scancode_raw_result.json")
        else:
            output_json_file = ""

        if not called_by_cli:
            logger, _result_log = init_log(os.path.join(output_path, f"fosslight_log_src_{_start_time}.txt"),
                                           True, logging.INFO, logging.DEBUG, _PKG_NAME, path_to_scan, path_to_exclude)

        num_cores = multiprocessing.cpu_count() - 1 if num_cores < 0 else num_cores

        if os.path.isdir(path_to_scan):
            try:
                time_out = float(time_out)
                pretty_params = {}
                pretty_params["path_to_scan"] = path_to_scan
                pretty_params["path_to_exclude"] = path_to_exclude
                pretty_params["output_file"] = output_file_name
                total_files_to_excluded = []
                if path_to_exclude:
                    for path in path_to_exclude:
                        path = os.path.join(path_to_scan, path)
                        if os.path.isdir(path):
                            for root, _, files in os.walk(path):
                                total_files_to_excluded.extend([os.path.normpath(os.path.join(root, file)).replace("\\", "/")
                                                                for file in files])
                        elif os.path.isfile(path):
                            total_files_to_excluded.append(os.path.normpath(path).replace("\\", "/"))

                rc, results = cli.run_scan(path_to_scan, max_depth=100,
                                           strip_root=True, license=True,
                                           copyright=True, return_results=True,
                                           processes=num_cores, pretty_params=pretty_params,
                                           output_json_pp=output_json_file, only_findings=True,
                                           license_text=True, url=True, timeout=time_out,
                                           include=(), ignore=tuple(total_files_to_excluded))

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
                            msg = "Failed to analyze :" + error_msg
                    if "files" in results:
                        rc, result_list, parsing_msg, license_list = parsing_file_item(results["files"],
                                                                                       has_error, need_license)
                        if parsing_msg:
                            _result_log["Parsing Log"] = parsing_msg
                        if rc:
                            if not success:
                                success = True
                            result_list = sorted(
                                result_list, key=lambda row: (''.join(row.licenses)))

                            for scan_item in result_list:
                                if check_binary(os.path.join(path_to_scan, scan_item.file)):
                                    scan_item.exclude = True

                            sheet_list["SRC_FL_Source"] = [scan_item.get_row_to_print() for scan_item in result_list]
                            if need_license:
                                sheet_list["matched_text"] = get_license_list_to_print(license_list)

            except Exception as ex:
                success = False
                msg = str(ex)
                logger.error(f"Analyze {path_to_scan}: {msg}")
        else:
            success = False
            msg = "Check the path to scan. :" + path_to_scan

        if not return_results:
            result_list = []

    scan_result_msg = str(success) if msg == "" else f"{success}, {msg}"
    _result_log["Scan Result"] = scan_result_msg
    _result_log["Output Directory"] = output_path
    try:
        _str_final_result_log = yaml.safe_dump(_result_log, allow_unicode=True, sort_keys=True)
        logger.info(_str_final_result_log)
    except Exception as ex:
        logger.warning(f"Failed to print result log. {ex}")

    if not success:
        logger.error(f"Failed to run: {scan_result_msg}")
    return success, _result_log["Scan Result"], result_list, license_list
