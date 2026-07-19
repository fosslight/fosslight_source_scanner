#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import importlib_metadata
import warnings
import logging
import json
from typing import Tuple
import fosslight_util.constant as constant
from ._parsing_scanoss_file import parsing_scan_result  # scanoss
from ._parsing_scanoss_file import parsing_extra_info  # scanoss
from scanoss.scanner import Scanner, ScanType
from scanoss.scanoss_settings import ScanossSettings
import io
import contextlib

logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_PKG_NAME = "fosslight_source"
SCANOSS_RESULT_FILE = "scanner_output.wfp"
SCANOSS_OUTPUT_FILE = "scanoss_raw_result.json"


def get_scanoss_extra_info(scanned_result: dict) -> list:
    return parsing_extra_info(scanned_result)


def run_scanoss_py(path_to_scan: str, output_path: str = "", format: list = [],
                   called_by_cli: bool = False, num_threads: int = -1,
                   path_to_exclude: list = [], excluded_files: set = None,
                   write_json_file: bool = False, hide_progress: bool = False,
                   timeout: int = 120) -> Tuple[list, bool]:
    """
    Run scanoss.py for the given path.

    :param path_to_scan: path of sourcecode to scan.
    :param output_file_name: file name for the output.
    :param format: Output file format (not being used except when calling check_output_format).
    :param called_by_cli: if not called by cli, initialize logger.
    :param write_json_file: if requested, keep the raw files.
    :param timeout: timeout in seconds for SCANOSS API request.
    :return scanoss_file_list: list of ScanItem (scanned result by files).
    """

    scanoss_file_list = []
    scanoss_skipped = False
    try:
        importlib_metadata.distribution("scanoss")
    except Exception as error:
        logger.warning(f"{error}. Skipping scan with scanoss.")
        logger.warning("Please install scanoss and dataclasses before run fosslight_source with scanoss option.")
        return scanoss_file_list, scanoss_skipped

    output_json_file = os.path.join(output_path, SCANOSS_OUTPUT_FILE)
    output_wfp_file = os.path.join(output_path, SCANOSS_RESULT_FILE)
    if os.path.exists(output_json_file):
        os.remove(output_json_file)

    output_buffer = io.StringIO()
    try:
        logger.debug(f"|---Running SCANOSS on {path_to_scan}")
        scanoss_settings = ScanossSettings()
        scanner = Scanner(
            ignore_cert_errors=True,
            skip_folders=list(path_to_exclude) if path_to_exclude else [],
            scan_output=output_json_file,
            scan_options=ScanType.SCAN_SNIPPETS.value,
            nb_threads=num_threads if num_threads > 0 else 10,
            scanoss_settings=scanoss_settings,
            timeout=timeout,
            retry=0
        )

        # Check API connectivity & API Limit using dummy WFP POST
        try:
            logger.debug(f"|---Checking SCANOSS API connectivity to {scanner.scanoss_api.url}")
            dummy_wfp = "file=72214db4e1e543018d1bafe86ea3b444,21,dummy.txt\nfh2=b200cd2eff5d535886e598b3a833aab5\n"
            ping_response = scanner.scanoss_api.session.post(
                scanner.scanoss_api.url,
                files={'file': ('dummy.wfp', dummy_wfp)},
                headers=scanner.scanoss_api.headers,
                timeout=5
            )
            if ping_response.status_code != 200:
                response_text = ping_response.text.lower()
                is_limit = ping_response.status_code in [429, 503]
                is_limit = is_limit or "rate limit" in response_text
                is_limit = is_limit or "limits being exceeded" in response_text
                if is_limit:
                    logger.debug(f"[SCANOSS] API Limit Exceeded: HTTP {ping_response.status_code}")
                elif ping_response.status_code in [401, 403]:
                    logger.debug(f"[SCANOSS] Authentication Failed: HTTP {ping_response.status_code}")
                else:
                    logger.debug(f"[SCANOSS] API is not ready: HTTP {ping_response.status_code}")
                scanoss_skipped = True
                return scanoss_file_list, scanoss_skipped
        except Exception as ping_error:
            logger.debug(f"[SCANOSS] Connection failed to {scanner.scanoss_api.url}: {ping_error}")
            scanoss_skipped = True
            return scanoss_file_list, scanoss_skipped

        with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
            scanner.scan_folder_with_options(scan_dir=path_to_scan)
    except Exception as error:
        logger.debug(f"SCANOSS execution failed: {error}")

    captured_output = output_buffer.getvalue()
    if captured_output:
        for line in captured_output.splitlines():
            line_strip = line.strip()
            if line_strip.startswith("ERROR:") or "rejected" in line_strip:
                logger.debug(f"[SCANOSS] {line_strip}")

        api_limit_patterns = [
            "due to service limits being exceeded",
            "service limits/rate limit being exceeded",
            "Rate limit exceeded",
            "HTTP 429"
        ]
        timeout_patterns = [
            "The SCANOSS API request timed out",
            "Service unavailable (HTTP 503)",
            "The SCANOSS API is currently unavailable",
            "ConnectionError communicating with",
            "The SCANOSS API request failed",
            "Connection aborted",
            "RemoteDisconnected"
        ]
        api_limit_exceed = any(p in captured_output for p in api_limit_patterns)
        timeout_occurred = any(p in captured_output for p in timeout_patterns)
        if timeout_occurred or api_limit_exceed:
            scanoss_skipped = True
            if api_limit_exceed:
                logger.debug("SCANOSS skipped (API Limit Exceeded)")
            elif timeout_occurred:
                logger.debug("SCANOSS skipped (Timeout)")

    if os.path.isfile(output_json_file):
        try:
            logger.debug("|---SCANOSS Parsing")
            with open(output_json_file, "r") as st_json:
                st_python = json.load(st_json)
                for key_to_exclude in excluded_files:
                    if key_to_exclude in st_python:
                        del st_python[key_to_exclude]
            with open(output_json_file, 'w') as st_json:
                json.dump(st_python, st_json, indent=4)
            with open(output_json_file, "r") as st_json:
                st_python = json.load(st_json)
                scanoss_file_list = parsing_scan_result(st_python, excluded_files)
        except Exception as error:
            logger.debug(f"SCANOSS Parsing {path_to_scan}: {error}")

    if not write_json_file:
        if os.path.isfile(output_json_file):
            os.remove(output_json_file)
        if os.path.isfile(output_wfp_file):
            os.remove(output_wfp_file)

    logger.info(f"|---Number of files detected with SCANOSS: {(len(scanoss_file_list))}")

    return scanoss_file_list, scanoss_skipped
