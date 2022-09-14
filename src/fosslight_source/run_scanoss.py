#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import pkg_resources
import warnings
import logging
import json
from datetime import datetime
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from fosslight_util.output_format import check_output_format  # , write_output_file
from ._parsing_scanoss_file import parsing_scanResult  # scanoss
from ._parsing_scanoss_file import parsing_extraInfo  # scanoss
import shutil
from pathlib import Path

logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_PKG_NAME = "fosslight_source"
SCANOSS_RESULT_FILE = "scanner_output.wfp"
SCANOSS_OUTPUT_FILE = "scanoss_raw_result.json"
SCANOSS_COMMAND_PREFIX = "scanoss-py scan -o "


def get_scanoss_extra_info(scanned_result):
    return parsing_extraInfo(scanned_result)


def run_scanoss_py(path_to_scan, output_file_name="", format="", called_by_cli=False, write_json_file=False, num_threads=-1):
    """
    Run scanoss.py for the given path.

    :param path_to_scan: path of sourcecode to scan.
    :param output_file_name: file name for the output.
    :param format: Output file format (not being used except when calling check_output_format).
    :param called_by_cli: if not called by cli, initialize logger.
    :param write_json_file: if requested, keep the raw files.
    :return scanoss_file_list: list of ScanItem (scanned result by files).
    """
    success, msg, output_path, output_file, output_extension = check_output_format(output_file_name, format)

    if not called_by_cli:
        global logger
        _start_time = datetime.now().strftime('%y%m%d_%H%M')
        logger, _result_log = init_log(os.path.join(output_path, f"fosslight_log_{_start_time}.txt"),
                                       True, logging.INFO, logging.DEBUG, _PKG_NAME, path_to_scan)

    scanoss_file_list = []
    try:
        pkg_resources.get_distribution("scanoss")
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

    scan_command = f"{SCANOSS_COMMAND_PREFIX} {output_json_file} {path_to_scan}"
    if num_threads > 0:
        scan_command += " -T " + str(num_threads)
    else:
        scan_command += " -T " + "30"

    try:
        os.system(scan_command)
        if os.path.isfile(output_json_file):
            with open(output_json_file, "r") as st_json:
                st_python = json.load(st_json)
                scanoss_file_list = parsing_scanResult(st_python)
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

    return scanoss_file_list
