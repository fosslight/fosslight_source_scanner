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
from fosslight_util.output_format import check_output_formats_v2
from fosslight_binary.binary_analysis import check_binary
from typing import Tuple

logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_PKG_NAME = "fosslight_source"


def run_scan(
    path_to_scan: str, output_file_name: str = "",
    _write_json_file: bool = False, num_cores: int = -1,
    return_results: bool = False, need_license: bool = False,
    formats: list = [], called_by_cli: bool = False,
    time_out: int = 120, correct_mode: bool = True,
    correct_filepath: str = "", path_to_exclude: list = []
) -> Tuple[bool, str, list, list]:
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

    success, msg, output_path, output_files, output_extensions, formats = check_output_formats_v2(output_file_name, formats)
    if success:
        if output_path == "":  # if json output with _write_json_file not used, output_path won't be needed.
            output_path = os.getcwd()
        else:
            output_path = os.path.abspath(output_path)
        if not called_by_cli:
            while len(output_files) < len(output_extensions):
                output_files.append(None)
            for i, output_extension in enumerate(output_extensions):
                if output_files[i] is None or output_files[i] == "":
                    if output_extension == _json_ext:
                        output_files[i] = f"fosslight_opossum_src_{_start_time}"
                    else:
                        output_files[i] = f"fosslight_report_src_{_start_time}"

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
                    target_path = os.path.basename(path_to_scan) if os.path.isabs(path_to_scan) else path_to_scan

                    for path in path_to_exclude:
                        exclude_path = path
                        isabs_exclude = os.path.isabs(path)
                        if isabs_exclude:
                            exclude_path = os.path.relpath(path, os.path.abspath(path_to_scan))

                        exclude_path = os.path.join(target_path, exclude_path)
                        if os.path.isdir(exclude_path):
                            for root, _, files in os.walk(exclude_path):
                                total_files_to_excluded.extend([os.path.normpath(os.path.join(root, file)).replace("\\", "/")
                                                                for file in files])
                        elif os.path.isfile(exclude_path):
                            total_files_to_excluded.append(os.path.normpath(exclude_path).replace("\\", "/"))

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
                                if check_binary(os.path.join(path_to_scan, scan_item.source_name_or_path)):
                                    scan_item.exclude = True
            except Exception as ex:
                success = False
                msg = str(ex)
                logger.error(f"Analyze {path_to_scan}: {msg}")
        else:
            success = False
            msg = f"(-p option) Check the path to scan: {path_to_scan}"

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
