#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import copy
import logging
import zipfile
import tempfile
import shutil
import defusedxml.ElementTree as ET
import xml.etree.ElementTree as xmlET
from collections import Counter

import fosslight_util.constant as constant
from ._scan_item import SourceItem
from fosslight_util.oss_item import ScannerItem

logger = logging.getLogger(constant.LOGGER_NAME)

PKG_NAME = "fosslight_source"
SRC_SHEET_NAME = 'SRC_FL_Source'
PRE_MERGE_SHEET_NAME = '.SRC_FL_Source_no_merge'

MERGED_HEADER = {SRC_SHEET_NAME: ['ID', 'Source Path', 'OSS Name',
                                  'OSS Version', 'License', 'Download Location',
                                  'Homepage', 'Copyright Text', 'Exclude', 'Comment', 'license_reference']}


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

            original_mode = None
            if os.path.exists(xlsx_path):
                try:
                    original_mode = os.stat(xlsx_path).st_mode
                except Exception as ex:
                    logger.debug(f"Failed to capture original permissions of {xlsx_path}: {ex}")

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

                if original_mode is not None:
                    try:
                        os.chmod(xlsx_path, original_mode)
                    except Exception as ex:
                        logger.debug(f"Failed to restore original permissions of {xlsx_path}: {ex}")
            except Exception:
                if os.path.exists(temp_xlsx_path):
                    os.remove(temp_xlsx_path)
                raise
    except Exception as ex:
        logger.debug(f"Failed to hide sheet {sheet_name}: {ex}")


def _normalize_merge_text(value: str) -> str:
    return value.strip() if value else ""


def _get_merge_licenses(scan_item: SourceItem) -> tuple:
    return tuple(sorted([lic.strip() for lic in scan_item.licenses if lic and lic.strip()]))


def _get_merge_download_locations(scan_item: SourceItem) -> tuple:
    downloads = scan_item.download_location
    if not downloads:
        return ()
    if isinstance(downloads, str):
        downloads = [downloads]
    return tuple(sorted([dl.strip() for dl in downloads if dl and dl.strip()]))


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
        and _is_merge_field_compatible(scan_items, lambda item: _normalize_merge_text(item.oss_name))
        and _is_merge_field_compatible(scan_items, lambda item: _normalize_merge_text(item.oss_version))
        and _is_merge_field_compatible(scan_items, _get_merge_licenses)
        and _is_merge_field_compatible(scan_items, _get_merge_download_locations)
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
    merged_downloads = _get_merge_field_value(scan_items, _get_merge_download_locations)
    merged_item.download_location = list(merged_downloads) if merged_downloads else []
    merged_copyrights = _get_top_merge_values(scan_items, lambda item: item.copyright)
    merged_item.copyright = merged_copyrights if merged_copyrights else []
    merged_item.set_oss_item()
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
        excluded_items = [item for item in merge_node_item["items"] if item.exclude]
        eligible_items = [item for item in merge_node_item["items"] if not item.exclude]

        # Keep at least one path depth in the report; root-level ". (N)" is too broad.
        if depth > 0 and _can_merge_folder(eligible_items):
            merged_items = [_create_merged_item(eligible_items, merge_path)] + excluded_items
        else:
            merged_items = list(merge_node_item["items"])

        for folder_name, child_node in merge_node_item["children"].items():
            child_path = f"{merge_path}/{folder_name}" if merge_path else folder_name
            merged_items.extend(merge_node(child_node, child_path, depth + 1))
        return merged_items

    return merge_node(merge_tree)
