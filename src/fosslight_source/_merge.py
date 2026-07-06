#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import copy
from collections import Counter

from fosslight_util.constant import COMMENT_DELIMITER

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


def _get_item_oss_name(item: SourceItem) -> str:
    if item.oss_items:
        return item.oss_items[0].name
    return item.oss_name


def _get_item_oss_version(item: SourceItem) -> str:
    if item.oss_items:
        return item.oss_items[0].version
    return item.oss_version


def _get_merge_licenses(scan_item: SourceItem) -> tuple:
    if scan_item.oss_items:
        return tuple(sorted([lic.strip() for lic in scan_item.oss_items[0].license if lic and lic.strip()]))
    return tuple(sorted([lic.strip() for lic in scan_item.licenses if lic and lic.strip()]))


def _get_merge_download_locations(scan_item: SourceItem) -> tuple:
    if scan_item.oss_items:
        downloads = scan_item.oss_items[0].download_location
    else:
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
    if len(scan_items) <= 1:
        return False
    # If any file has multiple OSS components, do not merge this folder
    for item in scan_items:
        if len(item.oss_items) > 1:
            return False
    return (
        _is_merge_field_compatible(scan_items, lambda item: _normalize_merge_text(_get_item_oss_name(item)))
        and _is_merge_field_compatible(scan_items, lambda item: _normalize_merge_text(_get_item_oss_version(item)))
        and _is_merge_field_compatible(scan_items, _get_merge_licenses)
        and _is_merge_field_compatible(scan_items, _get_merge_download_locations)
    )


def _get_merged_comments(scan_items: list) -> str:
    comments = []
    for item in scan_items:
        val = item.comment
        if val:
            parts = [p.strip() for p in val.split(COMMENT_DELIMITER) if p.strip()]
            for p in parts:
                if p not in comments:
                    comments.append(p)
    if not comments:
        return ""

    return COMMENT_DELIMITER.join(comments)


def _create_merged_item(scan_items: list, merge_path: str) -> SourceItem:
    representative_item = scan_items[0]
    merged_item = copy.copy(representative_item)
    merged_item.source_name_or_path = f"{merge_path} ({len(scan_items)})"
    merged_item.oss_name = _get_merge_field_value(scan_items, lambda item: _normalize_merge_text(_get_item_oss_name(item)))
    merged_item.oss_version = _get_merge_field_value(scan_items, lambda item: _normalize_merge_text(_get_item_oss_version(item)))
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
    Merge output rows within the same folder when OSS name, OSS version, license,
    and download location are compatible.

    A field is compatible when non-empty values across rows differ by at most one
    (empty values are ignored). All eligible rows in the folder must be compatible
    together; rows are not grouped by key subsets.
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

    def get_all_eligible_items(node: dict) -> list:
        items = [item for item in node["items"] if not item.exclude]
        for child_node in node["children"].values():
            items.extend(get_all_eligible_items(child_node))
        return items

    def merge_node(merge_node_item: dict, merge_path: str = "", depth: int = 0) -> tuple:
        child_finalized = []
        child_unfinalized = []
        for folder_name, child_node in merge_node_item["children"].items():
            child_path = f"{merge_path}/{folder_name}" if merge_path else folder_name
            fin, unfin = merge_node(child_node, child_path, depth + 1)
            child_finalized.extend(fin)
            child_unfinalized.extend(unfin)

        local_excluded = [item for item in merge_node_item["items"] if item.exclude]
        local_eligible = [item for item in merge_node_item["items"] if not item.exclude]

        all_eligible_candidates = list(local_eligible)
        for _, g_items in child_unfinalized:
            all_eligible_candidates.extend(g_items)

        # We can merge under the current node if depth > 0 and we are combining multiple sources:
        # e.g., local files + child groups, or multiple child groups, or multiple local files.
        can_merge_here = (depth > 0) and (len(local_eligible) + len(child_unfinalized) > 1)

        if can_merge_here:
            all_subtree_eligible = get_all_eligible_items(merge_node_item)
            if _can_merge_folder(all_subtree_eligible):
                new_finalized = child_finalized + local_excluded
                new_unfinalized = [(merge_path, all_eligible_candidates)]
                return new_finalized, new_unfinalized
            else:
                # Compatibility broke at this level. We must finalize the subtrees.
                finalized_child_groups = []
                for c_path, c_items in child_unfinalized:
                    if len(c_items) > 1 and _can_merge_folder(c_items):
                        finalized_child_groups.append(_create_merged_item(c_items, c_path))
                    else:
                        finalized_child_groups.extend(c_items)

                finalized_local = []
                if len(local_eligible) > 1 and _can_merge_folder(local_eligible):
                    finalized_local.append(_create_merged_item(local_eligible, merge_path))
                else:
                    finalized_local.extend(local_eligible)

                new_finalized = child_finalized + local_excluded + finalized_child_groups + finalized_local
                new_unfinalized = []
                return new_finalized, new_unfinalized
        else:
            # We cannot merge or don't need to merge at this level (e.g. depth == 0 or only 1 source).
            # We propagate everything up as unfinalized.
            new_finalized = child_finalized + local_excluded
            new_unfinalized = list(child_unfinalized)
            if local_eligible:
                new_unfinalized.append((merge_path, local_eligible))
            return new_finalized, new_unfinalized

    fin, unfin = merge_node(merge_tree)
    finalized_results = list(fin)
    for path, items in unfin:
        if path and len(items) > 1 and _can_merge_folder(items):
            finalized_results.append(_create_merged_item(items, path))
        else:
            finalized_results.extend(items)

    return finalized_results
