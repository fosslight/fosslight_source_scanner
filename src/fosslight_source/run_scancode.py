#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import multiprocessing
import warnings
import logging
from scancode import cli
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from fosslight_util.time import current_timestamp_utc, timestamp_for_filename
from ._parsing_scancode_file_item import parsing_file_item
from ._parsing_scancode_file_item import get_error_from_header
from fosslight_util.output_format import check_output_formats_v2
from fosslight_binary.binary_analysis import check_binary
from fosslight_util.exclude import (
    EXCLUDE_DIRECTORY,
    EXCLUDE_FILE_EXTENSION,
    EXCLUDE_FILENAME,
    PACKAGE_DIRECTORY,
)
from commoncode.fileset import is_included
from typing import Tuple, Iterable

logger = logging.getLogger(constant.LOGGER_NAME)
warnings.filterwarnings("ignore", category=FutureWarning)
_PKG_NAME = "fosslight_source"

try:
    from click.core import UNSET as _CLICK_UNSET  # Click >= 8.3
    _HAS_CLICK_UNSET = True
except ImportError:  # pragma: no cover
    _CLICK_UNSET = None
    _HAS_CLICK_UNSET = False


def _apply_scancode_unset_workaround(kwargs: dict) -> None:
    """
    Click 8.3+ uses UNSET for optional multi-value plugin defaults. Those values
    are truthy, so plugins like --facet run with UNSET and crash (not iterable).
    Replace UNSET defaults with () or None before cli.run_scan().
    """
    try:
        for opt in cli.plugin_options:
            if opt.name in kwargs:
                continue
            default = getattr(opt, "default", None)
            unset = (_HAS_CLICK_UNSET and default is _CLICK_UNSET) or (
                getattr(default, "__class__", type(None)).__name__ == "Sentinel"
            )
            if not unset:
                continue
            if getattr(opt, "multiple", False):
                kwargs[opt.name] = ()
            elif getattr(opt, "is_flag", None):
                kwargs[opt.name] = False
            else:
                kwargs[opt.name] = None
    except Exception as ex:  # pragma: no cover
        logger.debug("scancode UNSET workaround skipped: %s", ex)


_WILDCARD_EXTENSIONS = {
    "png", "mp3", "ogg", "comp", "bin", "o", "db", "tflite",
    "ttf", "pyc", "exe", "dll", "jpg", "gif"
}


def _normalize_custom_pattern(pattern: str, abs_path_to_scan: str) -> set:
    pat = pattern.replace('\\', '/').strip()
    if not pat:
        return set()

    patterns_to_add = {pat}

    if pat.endswith("/**"):
        base = pat[:-3].rstrip("/")
        if base:
            patterns_to_add.add(base)
    elif pat.endswith("/*"):
        base = pat[:-2].rstrip("/")
        if base:
            patterns_to_add.add(base)
            patterns_to_add.add(f"{base}/**")
    elif pat.endswith("/"):
        base = pat.rstrip("/")
        if base:
            patterns_to_add.add(base)
            patterns_to_add.add(f"{base}/**")
            patterns_to_add.add(f"{base}/*")
    else:
        full_path = os.path.join(abs_path_to_scan, pat)
        if os.path.isdir(full_path):
            patterns_to_add.add(f"{pat}/**")
            patterns_to_add.add(f"{pat}/*")

    return patterns_to_add


def _directory_ignore_pattern(dir_name: str) -> str:
    """Path-based glob for a directory name (avoids matching the scan root itself)."""
    normalized = dir_name.strip().strip("/").replace("\\", "/")
    if not normalized:
        return dir_name
    return f"**/{normalized}/**"


def _default_scancode_coarse_ignore_patterns(
    path_to_exclude: list = [],
    abs_path_to_scan: str = ""
) -> frozenset:
    """
    Coarse ignore patterns aligned with fosslight_util.get_excluded_paths() rules.
    Directory names use path-based globs (e.g. **/tests/**) so they do not match
    the scan root directory name itself.
    """
    patterns = {".*"}
    for name in PACKAGE_DIRECTORY + EXCLUDE_DIRECTORY:
        patterns.add(_directory_ignore_pattern(name))
    for ext in EXCLUDE_FILE_EXTENSION:
        patterns.add(f"*.{ext}")
    for name in EXCLUDE_FILENAME:
        patterns.add(name)

    for pattern in path_to_exclude or []:
        patterns.update(_normalize_custom_pattern(pattern, abs_path_to_scan))

    return frozenset(patterns)


def _is_covered_by_coarse_ignore(rel_path: str, coarse_patterns: Iterable[str]) -> bool:
    excludes = {pattern: "exclude" for pattern in coarse_patterns}
    return not is_included(rel_path, includes={}, excludes=excludes)


def _add_path_to_exclude_pattern(
    patterns: set,
    exclude_path: str,
    abs_path_to_scan: str,
    coarse_patterns: frozenset,
) -> None:
    exclude_path_normalized = os.path.normpath(exclude_path).replace("\\", "/")

    if exclude_path_normalized.endswith("/**"):
        base_dir = exclude_path_normalized[:-3].rstrip("/")
        if base_dir:
            full_exclude_path = os.path.join(abs_path_to_scan, base_dir)
            if os.path.isdir(full_exclude_path):
                patterns.add(base_dir)
                patterns.add(exclude_path_normalized)
            else:
                patterns.add(exclude_path_normalized)
        else:
            patterns.add(exclude_path_normalized)
        return

    has_glob_chars = any(char in exclude_path_normalized for char in ['*', '?', '['])
    if has_glob_chars:
        patterns.add(exclude_path_normalized)
        return

    full_exclude_path = os.path.join(abs_path_to_scan, exclude_path_normalized)
    if os.path.isdir(full_exclude_path):
        base_path = exclude_path_normalized.rstrip("/")
        if base_path:
            patterns.add(base_path)
            patterns.add(f"{base_path}/**")
        else:
            patterns.add(exclude_path_normalized)
    elif os.path.isfile(full_exclude_path):
        ext = os.path.splitext(exclude_path_normalized)[1].lstrip('.').lower()
        if ext in _WILDCARD_EXTENSIONS:
            patterns.add(f"*.{ext}")
        elif not _is_covered_by_coarse_ignore(exclude_path_normalized, coarse_patterns):
            patterns.add(f"**/{exclude_path_normalized}")
    else:
        ext = os.path.splitext(exclude_path_normalized)[1].lstrip('.').lower()
        if ext in _WILDCARD_EXTENSIONS:
            patterns.add(f"*.{ext}")
        else:
            patterns.add(exclude_path_normalized)


def _build_scancode_ignore_patterns(
    path_to_exclude: list,
    abs_path_to_scan: str,
    binary_paths: list,
) -> tuple:
    coarse_patterns = _default_scancode_coarse_ignore_patterns(path_to_exclude, abs_path_to_scan)
    patterns = set(coarse_patterns)

    for path in path_to_exclude or []:
        if os.path.isabs(path):
            exclude_path = os.path.relpath(path, abs_path_to_scan)
        else:
            exclude_path = path
        _add_path_to_exclude_pattern(patterns, exclude_path, abs_path_to_scan, coarse_patterns)

    for rel_path in binary_paths:
        ext = os.path.splitext(rel_path)[1].lstrip('.').lower()
        if ext in _WILDCARD_EXTENSIONS:
            patterns.add(f"*.{ext}")
        else:
            patterns.add(f"**/{rel_path}")

    return tuple(sorted(patterns))


def run_scan(
    path_to_scan: str, output_file_name: str = "",
    _write_json_file: bool = False, num_cores: int = -1,
    return_results: bool = False, need_license: bool = False,
    formats: list = [], called_by_cli: bool = False,
    time_out: int = 120, correct_mode: bool = True,
    correct_filepath: str = "", path_to_exclude: list = [],
    excluded_files: list = [], hide_progress: bool = False
) -> Tuple[bool, str, list, list]:
    if not called_by_cli:
        global logger

    success = True
    msg = ""
    _result_log = {}
    result_list = []
    license_list = []
    _json_ext = ".json"
    _start_time = current_timestamp_utc()
    _file_time = timestamp_for_filename(_start_time)

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
                        output_files[i] = f"fosslight_opossum_src_{_file_time}"
                    else:
                        output_files[i] = f"fosslight_report_src_{_file_time}"

        if _write_json_file:
            output_json_file = os.path.join(output_path, "scancode_raw_result.json")
        else:
            output_json_file = ""

        if not called_by_cli:
            log_file_path = os.path.join(
                output_path, f"fosslight_log_src_{_file_time}.txt"
            )
            logger, _result_log = init_log(
                log_file_path, True, logging.INFO, logging.DEBUG,
                _PKG_NAME, path_to_scan, path_to_exclude
            )

            logger.info(f"Tool Info : {_result_log['Tool Info']}")

        num_cores = multiprocessing.cpu_count() - 1 if num_cores < 0 else num_cores

        if os.path.isdir(path_to_scan):
            try:
                time_out = float(time_out)
                pretty_params = {}
                pretty_params["path_to_scan"] = path_to_scan
                pretty_params["path_to_exclude"] = path_to_exclude
                pretty_params["output_file"] = output_file_name
                abs_path_to_scan = os.path.abspath(path_to_scan)
                binary_paths = []
                coarse_patterns = _default_scancode_coarse_ignore_patterns(path_to_exclude, abs_path_to_scan)

                for root, dirs, files in os.walk(path_to_scan):
                    dirs[:] = [
                        d for d in dirs
                        if not d.startswith('.') and not _is_covered_by_coarse_ignore(
                            os.path.relpath(os.path.join(root, d), abs_path_to_scan).replace("\\", "/") + "/a",
                            coarse_patterns
                        )
                    ]
                    for name in files:
                        if name.startswith('.'):
                            continue
                        full_path = os.path.join(root, name)
                        rel_path = os.path.relpath(full_path, abs_path_to_scan).replace("\\", "/")
                        if _is_covered_by_coarse_ignore(rel_path, coarse_patterns):
                            continue
                        try:
                            if not check_binary(full_path, True):
                                continue
                        except Exception:
                            continue
                        binary_paths.append(rel_path)
                        logger.debug(f"Excluded binary from scancode: {rel_path}")

                ignore_tuple = _build_scancode_ignore_patterns(
                    path_to_exclude, abs_path_to_scan, binary_paths
                )
                logger.debug(f"Scancode ignore patterns: {len(ignore_tuple)}")

                kwargs = {
                    "max_depth": 100,
                    "strip_root": True,
                    "license": True,
                    "copyright": True,
                    "return_results": True,
                    "processes": num_cores,
                    "pretty_params": pretty_params,
                    "output_json_pp": output_json_file,
                    "only_findings": True,
                    "license_text": True,
                    "url": True,
                    "timeout": time_out,
                    "include": (),
                    "ignore": ignore_tuple,
                    "quiet": hide_progress
                }
                _apply_scancode_unset_workaround(kwargs)
                rc, results = cli.run_scan(path_to_scan, **kwargs)
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
                                if os.path.isdir(scan_item.source_name_or_path):
                                    continue
                                if check_binary(os.path.join(path_to_scan, scan_item.source_name_or_path), True):
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

    if not success:
        logger.error(f"Failed to run: {scan_result_msg}")
    return success, _result_log["Scan Result"], result_list, license_list
