#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import importlib_metadata
import warnings
import logging
import json
from datetime import datetime
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from fosslight_util.output_format import check_output_formats_v2  # , write_output_file
from ._parsing_scanoss_file import parsing_scanResult  # scanoss
from ._parsing_scanoss_file import parsing_extraInfo  # scanoss
import shutil
from pathlib import Path
from scanoss.scanner import Scanner, ScanType
import io
import contextlib

logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_PKG_NAME = "fosslight_source"
SCANOSS_RESULT_FILE = "scanner_output.wfp"
SCANOSS_OUTPUT_FILE = "scanoss_raw_result.json"


def get_scanoss_extra_info(scanned_result: dict) -> list:
    return parsing_extraInfo(scanned_result)


def run_scanoss_py(path_to_scan: str, output_file_name: str = "", format: list = [], called_by_cli: bool = False,
                   write_json_file: bool = False, num_threads: int = -1, path_to_exclude: list = []) -> list:
    """
    Run scanoss.py for the given path.

    :param path_to_scan: path of sourcecode to scan.
    :param output_file_name: file name for the output.
    :param format: Output file format (not being used except when calling check_output_format).
    :param called_by_cli: if not called by cli, initialize logger.
    :param write_json_file: if requested, keep the raw files.
    :return scanoss_file_list: list of ScanItem (scanned result by files).
    """
    success, msg, output_path, output_files, output_extensions, formats = check_output_formats_v2(output_file_name, format)

    if not called_by_cli:
        global logger
        _start_time = datetime.now().strftime('%y%m%d_%H%M')
        logger, _result_log = init_log(os.path.join(output_path, f"fosslight_log_src_{_start_time}.txt"),
                                       True, logging.INFO, logging.DEBUG, _PKG_NAME, path_to_scan, path_to_exclude)

    scanoss_file_list = []
    try:
        importlib_metadata.distribution("scanoss")
    except Exception as error:
        logger.warning(f"{error}. Skipping scan with scanoss.")
        logger.warning("Please install scanoss and dataclasses before run fosslight_source with scanoss option.")
        return scanoss_file_list

    if output_path == "":  # if json output with _write_json_file not used, output_path won't be needed.
        output_path = os.getcwd()
    else:
        output_path = os.path.abspath(output_path)
        if not os.path.isdir(output_path):
            Path(output_path).mkdir(parents=True, exist_ok=True)
    output_json_file = os.path.join(output_path, SCANOSS_OUTPUT_FILE)
    if os.path.exists(output_json_file):  # remove scanner_output.wfp file if exist
        os.remove(output_json_file)

    try:
        scanner = Scanner(
            ignore_cert_errors=True,
            skip_folders=path_to_exclude,
            scan_output=output_json_file,
            scan_options=ScanType.SCAN_SNIPPETS.value,
            nb_threads=num_threads if num_threads > 0 else 10
        )

        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
            scanner.scan_folder_with_options(scan_dir=path_to_scan)
        captured_output = output_buffer.getvalue()
        api_limit_exceed = "due to service limits being exceeded" in captured_output
        logger.debug(f"{captured_output}")

        if os.path.isfile(output_json_file):
            total_files_to_excluded = []
            if path_to_exclude:
                for path in path_to_exclude:
                    path = os.path.join(path_to_scan, os.path.relpath(path, os.path.abspath(path_to_scan))) \
                           if not os.path.isabs(path_to_scan) and os.path.isabs(path) else os.path.join(path_to_scan, path)
                    if os.path.isdir(path):
                        for root, _, files in os.walk(path):
                            root = root[len(path_to_scan) + 1:]
                            total_files_to_excluded.extend([os.path.normpath(os.path.join(root, file)).replace('\\', '/')
                                                            for file in files])
                    elif os.path.isfile(path):
                        path = path[len(path_to_scan) + 1:]
                        total_files_to_excluded.append(os.path.normpath(path).replace('\\', '/'))

            with open(output_json_file, "r") as st_json:
                st_python = json.load(st_json)
                for key_to_exclude in total_files_to_excluded:
                    if key_to_exclude in st_python:
                        del st_python[key_to_exclude]
            with open(output_json_file, 'w') as st_json:
                json.dump(st_python, st_json, indent=4)
            with open(output_json_file, "r") as st_json:
                st_python = json.load(st_json)
                scanoss_file_list = parsing_scanResult(st_python, path_to_scan, path_to_exclude)

    except Exception as error:
        logger.debug(f"SCANOSS Parsing {path_to_scan}: {error}")

    logger.info(f"|---Number of files detected with SCANOSS: {(len(scanoss_file_list))}")

    try:
        if write_json_file:
            shutil.move(SCANOSS_RESULT_FILE, output_path)
        else:
            os.remove(output_json_file)
            os.remove(SCANOSS_RESULT_FILE)
    except Exception as error:
        logger.debug(f"Moving scanoss raw files failed.: {error}")

    return scanoss_file_list, api_limit_exceed
