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
import re
import urllib.request
import urllib.error
import tempfile
import zipfile
import defusedxml.ElementTree as ET
import xml.etree.ElementTree as xmlET
from datetime import datetime
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from ._help import print_version, print_help_msg_source_scanner
from ._license_matched import get_license_list_to_print
from fosslight_util.output_format import check_output_formats_v2, write_output_file
from fosslight_util.correct import correct_with_yaml
from fosslight_util.parsing_yaml import SUPPORT_OSS_INFO_FILES
from .run_scancode import run_scan
from fosslight_util.exclude import get_excluded_paths
from .run_scanoss import run_scanoss_py
from .run_scanoss import get_scanoss_extra_info
import yaml
import tqdm
import argparse
import copy
from collections import Counter
from .run_spdx_extractor import get_spdx_downloads
from .run_manifest_extractor import get_manifest_licenses
from ._scan_item import SourceItem, resolve_kb_config, is_notice_file
from ._kb_client import fetch_origin_urls_via_scan_job
from fosslight_util.oss_item import ScannerItem
from typing import Optional, Tuple
from ._scan_item import is_manifest_file
import shutil


SRC_SHEET_NAME = 'SRC_FL_Source'
PRE_MERGE_SHEET_NAME = 'SRC_FL_Source_before_merge'
SCANOSS_HEADER = {SRC_SHEET_NAME: ['ID', 'Source Path', 'OSS Name',
                                   'OSS Version', 'License', 'Download Location',
                                   'Homepage', 'Copyright Text', 'Exclude', 'Comment']}
MERGED_HEADER = {SRC_SHEET_NAME: ['ID', 'Source Path', 'OSS Name',
                                  'OSS Version', 'License', 'Download Location',
                                  'Homepage', 'Copyright Text', 'Exclude', 'Comment', 'license_reference']}
KB_REFERENCE_HEADER = ['ID', 'Source Path', 'KB Origin URL', 'Evidence']
ALL_MODE = 'all'
SCANNER_TYPE = ['kb', 'scancode', 'scanoss', ALL_MODE]
OSS_INFO_CORRECTION_COMMENT = "Excluded because it's OSS info correction file"


logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
PKG_NAME = "fosslight_source"
RESULT_KEY = "Scan Result"


def _get_source_rows_to_print(source_items: list) -> list:
    source_rows = []
    for source_item in source_items:
        source_rows.extend(source_item.get_print_array())
    return source_rows


def _add_pre_merge_sheet(scan_item: 'ScannerItem') -> None:
    external_sheets = getattr(scan_item, "external_sheets", {}) or {}
    external_sheets[PRE_MERGE_SHEET_NAME] = [
        MERGED_HEADER[SRC_SHEET_NAME],
        *_get_source_rows_to_print(scan_item.file_items.get(PKG_NAME, [])),
    ]
    scan_item.external_sheets = external_sheets


def _hide_xlsx_sheet(xlsx_path: str, sheet_name: str) -> None:
    workbook_xml_path = "xl/workbook.xml"
    namespace_uri = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    relationship_uri = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    xmlET.register_namespace("", namespace_uri)
    xmlET.register_namespace("r", relationship_uri)

    try:
        with zipfile.ZipFile(xlsx_path, "r") as workbook:
            try:
                workbook_xml = workbook.read(workbook_xml_path)
            except KeyError:
                logger.debug(f"Failed to hide sheet. workbook.xml not found: {xlsx_path}")
                return

            root = ET.fromstring(workbook_xml)
            target_sheet = None
            for sheet in root.findall(f".//{{{namespace_uri}}}sheet"):
                if sheet.attrib.get("name") == sheet_name:
                    target_sheet = sheet
                    break

            if target_sheet is None:
                logger.debug(f"Failed to hide sheet. sheet not found: {sheet_name}")
                return

            target_sheet.set("state", "hidden")
            updated_workbook_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

            output_dir = os.path.dirname(xlsx_path) or "."
            with tempfile.NamedTemporaryFile(delete=False, dir=output_dir, suffix=".xlsx") as temp_file:
                temp_xlsx_path = temp_file.name

            try:
                with zipfile.ZipFile(temp_xlsx_path, "w") as updated_workbook:
                    for item in workbook.infolist():
                        if item.filename == workbook_xml_path:
                            content = updated_workbook_xml
                        else:
                            content = workbook.read(item.filename)
                        updated_workbook.writestr(item, content)
                shutil.move(temp_xlsx_path, xlsx_path)
            except Exception:
                if os.path.exists(temp_xlsx_path):
                    os.remove(temp_xlsx_path)
                raise
    except Exception as ex:
        logger.debug(f"Failed to hide sheet {sheet_name}: {ex}")


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
    parser.add_argument('--kb_url', type=str, required=False, default="")
    parser.add_argument('--kb_token', type=str, required=False, default="")
    parser.add_argument('--no_merge', action='store_true', required=False)

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
    kb_url = args.kb_url
    kb_token = args.kb_token
    merge_by_folder = not args.no_merge

    time_out = args.timeout
    core = args.cores

    if os.path.isdir(path_to_scan):
        result = []
        result = run_scanners(path_to_scan, output_file_name, write_json_file, core, True,
                              print_matched_text, formats, time_out, correct_mode, correct_filepath,
                              selected_scanner, path_to_exclude, hide_progress=hide_progress,
                              kb_url=kb_url, kb_token=kb_token,
                              merge_by_folder=merge_by_folder)

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
    run_kb_msg: str = "", merge_by_folder: bool = False, kb_reference_result: Optional[list] = None
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
                kb_ref = get_kb_reference_to_print(kb_reference_result or merged_result)
                sheet_list["kb_reference"] = kb_ref
            else:
                sheet_list["scancode_reference"] = get_license_list_to_print(license_list)
                sheet_list["scanoss_reference"] = get_scanoss_extra_info(scanoss_result)
                kb_ref = get_kb_reference_to_print(kb_reference_result or merged_result)
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

    if merged_result and merge_by_folder:
        _add_pre_merge_sheet(scan_item)
        scan_item.file_items[PKG_NAME] = merge_results_by_folder(scan_item.file_items[PKG_NAME])

    combined_paths_and_files = [os.path.join(output_path, file) for file in output_files]
    results = []
    has_pre_merge_sheet = PRE_MERGE_SHEET_NAME in getattr(scan_item, "external_sheets", {})
    for combined_path_and_file, output_extension, output_format in zip(combined_paths_and_files, output_extensions, formats):
        # if need_license and output_extension == _json_ext and "scanoss_reference" in sheet_list:
        #     del sheet_list["scanoss_reference"]
        result = write_output_file(
            combined_path_and_file, output_extension, scan_item, extended_header, "", output_format
        )
        success, _, result_file = result
        if success and has_pre_merge_sheet and result_file.endswith(".xlsx"):
            _hide_xlsx_sheet(result_file, PRE_MERGE_SHEET_NAME)
        results.append(result)
    for success, msg, result_file in results:
        final_result_file = result_file.replace(output_path, final_output_path)
        if success:
            logger.info(f"Output file: {final_result_file}")
            for row in scan_item.get_cover_comment():
                logger.info(row)
        else:
            logger.error(f"Fail to generate result file {final_result_file}. msg:({msg})")
    return scan_item


def check_kb_server_reachable(kb_url: str, kb_token: str = "") -> bool:
    for attempt in range(3):
        try:
            request = urllib.request.Request(f"{kb_url}health", method='GET')
            if kb_token:
                request.add_header('Authorization', f'Bearer {kb_token}')
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


def mark_oss_info_correction_files_as_excluded(scan_results: list) -> None:
    for item in scan_results:
        file_name = os.path.basename(item.source_name_or_path).lower()
        if any(re.search(pattern, file_name, re.IGNORECASE) for pattern in SUPPORT_OSS_INFO_FILES):
            item.exclude = True
            item.comment = OSS_INFO_CORRECTION_COMMENT


def _collect_kb_file_hashes(
    scancode_result: list,
    path_to_scan: str,
    excluded_files: set,
    hide_progress: bool,
) -> tuple[list[str], list[tuple[SourceItem, str]]]:
    """Collect MD5 hashes from scancode results and walk targets, plus (extra_item, md5) candidates.

    Skips license/notice files and scancode_result items that already have download_location.
    ScanOSS/SPDX results are merged into scancode_result before this runs.
    """
    file_hashes: list[str] = []
    extra_candidates: list[tuple[SourceItem, str]] = []

    for item in scancode_result:
        if item.is_license_text or is_notice_file(item.source_name_or_path):
            continue
        if item.download_location:
            continue
        md5_hash, _wfp = item._get_hash(path_to_scan)
        if md5_hash:
            item._cached_kb_md5 = md5_hash
            file_hashes.append(md5_hash)

    abs_path_to_scan = os.path.abspath(path_to_scan)
    scancode_paths = {item.source_name_or_path for item in scancode_result}

    files_to_scan = []
    for root, _dirs, files in os.walk(path_to_scan):
        for file in files:
            files_to_scan.append(os.path.join(root, file))

    for file_path in tqdm.tqdm(files_to_scan, desc="KB Hashing", disable=hide_progress):
        rel_path = os.path.relpath(file_path, abs_path_to_scan).replace("\\", "/")
        if rel_path in scancode_paths or rel_path in excluded_files or is_notice_file(file_path):
            continue
        extra_item = SourceItem(rel_path)
        md5_hash, _wfp = extra_item._get_hash(path_to_scan)
        if md5_hash:
            extra_item._cached_kb_md5 = md5_hash
            file_hashes.append(md5_hash)
            extra_candidates.append((extra_item, md5_hash))

    return file_hashes, extra_candidates


def merge_results(
    scancode_result: list = [], scanoss_result: list = [], spdx_downloads: dict = {},
    path_to_scan: str = "", run_kb: bool = False, manifest_licenses: dict = {},
    excluded_files: set = None, hide_progress: bool = False, kb_url: str = "", kb_token: str = ""
) -> tuple[list, Optional[str], int, int]:

    """
    Merge scanner results and spdx parsing result.
    :param scancode_result: list of scancode results in SourceItem.
    :param scanoss_result: list of scanoss results in SourceItem.
    :param spdx_downloads: dictionary of spdx parsed results.
    :param path_to_scan: path to the scanned directory for constructing absolute file paths.
    :param run_kb: if True, load kb result.
    :param excluded_files: set of relative paths to exclude from KB-only file discovery.
    :param kb_url: KB API base URL.
    :param kb_token: KB API bearer token.
    :return: (merged_result, kb failure message, requested file_hash count, returned match count).
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
            valid_licenses = [lic.strip() for lic in licenses if isinstance(lic, str) and lic.strip()]
            if not valid_licenses:
                continue
            if file_name in scancode_result:
                merged_result_item = scancode_result[scancode_result.index(file_name)]
                # overwrite existing detected licenses with manifest-provided licenses
                merged_result_item.licenses = []  # clear existing licenses (setter clears when value falsy)
                merged_result_item.licenses = valid_licenses
                merged_result_item.is_manifest_file = True
            else:
                new_result_item = SourceItem(file_name)
                new_result_item.licenses = valid_licenses
                new_result_item.is_manifest_file = True
                scancode_result.append(new_result_item)

    kb_origin_urls: dict[str, str] = {}
    kb_status_message: Optional[str] = None
    kb_requested_count = 0
    kb_returned_count = 0
    extra_candidates: list[tuple[SourceItem, str]] = []
    if run_kb:
        file_hashes, extra_candidates = _collect_kb_file_hashes(
            scancode_result, path_to_scan, excluded_files, hide_progress
        )
        if file_hashes:
            kb_result = fetch_origin_urls_via_scan_job(file_hashes, kb_url, kb_token)
            kb_origin_urls = kb_result.origin_urls
            kb_status_message = kb_result.failure_message
            kb_requested_count = kb_result.requested_count
            kb_returned_count = kb_result.returned_count

    for item in scancode_result:
        item.set_oss_item(path_to_scan, kb_origin_urls=kb_origin_urls)

    # Add OSSItem for files in path_to_scan that are not in scancode_result
    # when KB returns an origin URL for their MD5 hash (skip excluded_files)
    if run_kb:
        for extra_item, _md5_hash in extra_candidates:
            extra_item.set_oss_item(path_to_scan, kb_origin_urls=kb_origin_urls)
            if extra_item.download_location:
                scancode_result.append(extra_item)

    return scancode_result, kb_status_message, kb_requested_count, kb_returned_count


def _finalize_temp_output(
    temp_output_path: str,
    final_output_path: str,
    publish: bool,
    log: Optional[logging.Logger] = None,
) -> bool:
    """Copy scan artifacts from temp dir, then always remove the temp directory."""
    if not temp_output_path or not os.path.isdir(temp_output_path):
        return True
    publish_ok = True
    try:
        if publish:
            shutil.copytree(temp_output_path, final_output_path, dirs_exist_ok=True)
    except Exception as ex:
        publish_ok = False
        if log:
            log.error(f"Failed to publish scan artifacts: {ex}")
    finally:
        try:
            shutil.rmtree(temp_output_path)
        except Exception as ex:
            if log:
                log.debug(f"Failed to cleanup temp output directory: {ex}")
    return publish_ok


def _normalize_merge_text(value: str) -> str:
    return value.strip() if value else ""


def _get_merge_licenses(scan_item: SourceItem) -> tuple:
    return tuple(sorted([lic.strip() for lic in scan_item.licenses if lic and lic.strip()]))


def _get_merge_field_value(scan_items: list, value_getter) -> str:
    for scan_item in scan_items:
        value = value_getter(scan_item)
        if value:
            return value
    return ""


def _is_merge_field_compatible(scan_items: list, value_getter) -> bool:
    values = []
    for scan_item in scan_items:
        value = value_getter(scan_item)
        if value:
            values.append(value)
    return len(set(values)) <= 1


def _iter_merge_values(values) -> list:
    if not values:
        return []
    if isinstance(values, str):
        return [values]
    return values


def _get_top_merge_values(scan_items: list, value_getter) -> list:
    values = []
    for scan_item in scan_items:
        for value in _iter_merge_values(value_getter(scan_item)):
            normalized_value = _normalize_merge_text(value)
            if normalized_value:
                values.append(normalized_value)
    return [value for value, _ in Counter(values).most_common(3)]


def _can_merge_folder(scan_items: list) -> bool:
    return (
        len(scan_items) > 1
        and len({bool(item.exclude) for item in scan_items}) <= 1
        and _is_merge_field_compatible(scan_items, lambda item: _normalize_merge_text(item.oss_name))
        and _is_merge_field_compatible(scan_items, lambda item: _normalize_merge_text(item.oss_version))
        and _is_merge_field_compatible(scan_items, _get_merge_licenses)
    )


def _create_merged_item(scan_items: list, merge_path: str) -> SourceItem:
    # Reuse the shortest path item as the representative row, but keep original paths untouched.
    representative_item = min(scan_items, key=lambda item: (len(item.source_name_or_path), item.source_name_or_path))
    merged_item = copy.copy(representative_item)
    merged_item.source_name_or_path = f"{merge_path} ({len(scan_items)})"
    merged_item.oss_name = _get_merge_field_value(scan_items, lambda item: _normalize_merge_text(item.oss_name))
    merged_item.oss_version = _get_merge_field_value(scan_items, lambda item: _normalize_merge_text(item.oss_version))
    merged_item._licenses = []
    merged_item.licenses = list(_get_merge_field_value(scan_items, _get_merge_licenses))
    merged_downloads = _get_top_merge_values(scan_items, lambda item: item.download_location)
    merged_copyrights = _get_top_merge_values(scan_items, lambda item: item.copyright)
    merged_item.download_location = [", ".join(merged_downloads)] if merged_downloads else []
    merged_item.copyright = [", ".join(merged_copyrights)] if merged_copyrights else []
    merged_item.set_oss_item(run_kb=False)
    return merged_item


def merge_results_by_folder(scan_result: list) -> list:
    """
    Merge output rows within the same folder when OSS name, OSS version, and license are compatible.
    """
    # Build a folder tree first so merge never jumps straight to root ".".
    merge_tree = {"items": [], "children": {}}

    for scan_item in scan_result:
        normalized_path = os.path.normpath(scan_item.source_name_or_path).replace("\\", "/")
        path_parts = [part for part in normalized_path.split("/") if part and part != "."]
        current_node = merge_tree

        for folder_name in path_parts[:-1]:
            current_node = current_node["children"].setdefault(folder_name, {"items": [], "children": {}})
        current_node["items"].append(scan_item)

    def merge_node(merge_node_item: dict, merge_path: str = "", depth: int = 0) -> list:
        # Keep at least one path depth in the report; root-level ". (N)" is too broad.
        if depth > 0 and _can_merge_folder(merge_node_item["items"]):
            merged_items = [_create_merged_item(merge_node_item["items"], merge_path)]
        else:
            merged_items = list(merge_node_item["items"])

        for folder_name, child_node in merge_node_item["children"].items():
            child_path = f"{merge_path}/{folder_name}" if merge_path else folder_name
            merged_items.extend(merge_node(child_node, child_path, depth + 1))
        return merged_items

    return merge_node(merge_tree)


def run_scanners(
    path_to_scan: str, output_file_name: str = "",
    write_json_file: bool = False, num_cores: int = -1,
    called_by_cli: bool = True, print_matched_text: bool = False,
    formats: list = [], time_out: int = 120,
    correct_mode: bool = True, correct_filepath: str = "",
    selected_scanner: str = ALL_MODE, path_to_exclude: list = [],
    all_exclude_mode: tuple = (), hide_progress: bool = False,
    kb_url: str = "", kb_token: str = "", merge_by_folder: bool = True
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
    :param kb_url: KB API base URL. If empty, read KB_URL environment variable, then use default.
    :param kb_token: KB API bearer token. If empty, read KB_TOKEN environment variable.
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
    kb_url, kb_token = resolve_kb_config(kb_url, kb_token)

    success, msg, output_path, output_files, output_extensions, formats = check_output_formats_v2(output_file_name, formats)

    if output_path == "":
        output_path = os.getcwd()
    final_output_path = output_path
    output_path = os.path.join(os.path.dirname(output_path), f'.fosslight_temp_{start_time}')
    publish_temp_output = False
    logger = None
    publish_ok = True

    try:
        logger, result_log = init_log(os.path.join(output_path, f"fosslight_log_src_{start_time}.txt"),
                                      True, logging.INFO, logging.DEBUG, PKG_NAME, path_to_scan, path_to_exclude)

        logger.info(f"Tool Info : {result_log['Tool Info']}")

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
                success, result_log[RESULT_KEY], scancode_result, license_list = run_scan(
                    path_to_scan, output_file_name, write_json_file, num_cores, True,
                    print_matched_text, formats, called_by_cli, time_out, correct_mode,
                    correct_filepath, excluded_path_with_default_exclusion,
                    excluded_files, hide_progress,
                )
            excluded_files = set(excluded_files) if excluded_files else set()
            if selected_scanner in ['scanoss', ALL_MODE]:
                scanoss_result, api_limit_exceed = run_scanoss_py(path_to_scan, output_path, formats, True, num_cores,
                                                                  excluded_path_with_default_exclusion, excluded_files,
                                                                  write_json_file, hide_progress)

            run_kb_msg = ""
            if selected_scanner in SCANNER_TYPE:
                run_kb = True if selected_scanner in ['kb', ALL_MODE] else False
                if run_kb:
                    if not check_kb_server_reachable(kb_url, kb_token):
                        run_kb = False
                        run_kb_msg = f"KB({kb_url}) Unreachable"

                spdx_downloads, manifest_licenses = metadata_collector(path_to_scan, excluded_files)
                merged_result, kb_status_message, kb_requested_count, kb_returned_count = merge_results(
                    scancode_result, scanoss_result, spdx_downloads,
                    path_to_scan, run_kb, manifest_licenses, excluded_files,
                    hide_progress, kb_url, kb_token,
                )
                if kb_status_message:
                    run_kb_msg = f"KB({kb_url}) {kb_status_message}"
                elif run_kb and kb_requested_count > 0:
                    run_kb_msg = (
                        f"KB({kb_url}) response : {kb_returned_count}/"
                        f" requested: {kb_requested_count}"
                    )
                mark_oss_info_correction_files_as_excluded(merged_result)
                scan_item = create_report_file(start_time, merged_result, license_list, scanoss_result, selected_scanner,
                                               print_matched_text, output_path, output_files, output_extensions, correct_mode,
                                               correct_filepath, path_to_scan, excluded_path_without_dot, formats,
                                               api_limit_exceed, cnt_file_except_skipped, final_output_path, run_kb_msg,
                                               merge_by_folder, merged_result)
            else:
                print_help_msg_source_scanner()
                result_log[RESULT_KEY] = "Unsupported scanner"
                success = False
        else:
            result_log[RESULT_KEY] = f"Format error. {msg}"
            success = False

        publish_temp_output = True
    finally:
        publish_ok = _finalize_temp_output(output_path, final_output_path, publish_temp_output, logger)

    if publish_temp_output and not publish_ok:
        success = False
        prev_msg = result_log.get(RESULT_KEY, "")
        result_log[RESULT_KEY] = (
            f"{prev_msg}, Failed to publish scan artifacts" if prev_msg
            else "Failed to publish scan artifacts"
        )

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
