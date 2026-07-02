#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import copy
from collections import Counter

from ._scan_item import SourceItem


def _get_source_rows_to_print(source_items: list) -> list:
    source_rows = []
    for source_item in source_items:
        source_rows.extend(source_item.get_print_array())
    return source_rows


def _add_pre_merge_sheet(scan_item, pre_merge_sheet_name: str, header_row: list, pkg_name: str) -> None:
    external_sheets = getattr(scan_item, "external_sheets", {}) or {}
    external_sheets[pre_merge_sheet_name] = [
        header_row,
        *_get_source_rows_to_print(scan_item.file_items.get(pkg_name, [])),
    ]
    scan_item.external_sheets = external_sheets


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


def _get_merged_comments(scan_items: list) -> str:
    comments = []
    for item in scan_items:
        val = item.comment
        if val:
            parts = [p.strip() for p in val.split(" / ") if p.strip()]
            for p in parts:
                if p not in comments:
                    comments.append(p)
    if not comments:
        return ""

    delimiter = " / "
    merged = delimiter.join(comments)
    max_len = 32767
    if len(merged) > max_len:
        merged = merged[:max_len - 3] + "..."
    return merged


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
    merged_item._comment = _get_merged_comments(scan_items)
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
