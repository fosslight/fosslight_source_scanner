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
# from ._help import print_help_msg_source

logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_PKG_NAME = "fosslight_source"


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
    if not called_by_cli:
        global logger

    scanoss_file_list = []
    try:
        pkg_resources.get_distribution("scanoss")
    except Exception as error:
        logger.warning(str(error) + ". Skipping scan with scanoss.")
        return scanoss_file_list
    scan_command = "scanoss-py scan -o "

    start_time = datetime.now().strftime('%Y%m%d_%H%M%S')

    success, msg, output_path, output_file, output_extension = check_output_format(output_file_name, format)
    if not called_by_cli:
        logger, _result_log = init_log(os.path.join(output_path, "fosslight_src_log_"+start_time+".txt"),
                                       True, logging.INFO, logging.DEBUG, _PKG_NAME, path_to_scan)

    if output_path == "":  # if json output with _write_json_file not used, output_path won't be needed.
        output_path = os.getcwd()
    else:
        output_path = os.path.abspath(output_path)

    output_file = "scanoss_raw_result.json"

    output_json_file = os.path.join(output_path, output_file)

    scan_command += output_json_file + " " + path_to_scan

    if num_threads > 0:
        scan_command += " -T " + str(num_threads)
    else:
        scan_command += " -T " + "30"

    try:
        os.system(scan_command)
        st_json = open(output_json_file, "r")
        logger.info("SCANOSS Start parsing " + path_to_scan)
        with open(output_json_file, "r") as st_json:
            st_python = json.load(st_json)
            scanoss_file_list = parsing_scanResult(st_python)
    except Exception as error:
        logger.warning("Parsing " + path_to_scan + ":" + str(error))
    logger.info("|---Number of files detected with SCANOSS: " + str(len(scanoss_file_list)))

    if not write_json_file:
        try:
            os.system("rm " + output_json_file)
            os.system("rm scanner_output.wfp")
        except Exception as error:
            logger.debug("Deleting scanoss result failed.:" + str(error))
    else:
        try:
            os.system("mv scanner_output.wfp " + output_path + "/scanoss_fingerprint.wfp")
        except Exception as error:
            logger.debug("Moving scanoss fingerprint file failed.:" + str(error))

    return scanoss_file_list
