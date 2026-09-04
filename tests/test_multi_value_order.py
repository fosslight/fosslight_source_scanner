# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Stable order for multi-value License / Copyright cells."""

from fosslight_source._merge import _get_top_merge_values
from fosslight_source._scan_item import SourceItem


def test_licenses_are_stored_sorted():
    item = SourceItem("dummy.c")
    item.licenses = ["zlib", "mit", "apache-2.0"]
    assert item.licenses == ["apache-2.0", "mit", "zlib"]


def test_top_merge_copyrights_break_count_ties_alphabetically():
    items = []
    for text in ["Copyright Z", "Copyright A", "Copyright Z", "Copyright M"]:
        item = SourceItem("dummy.c")
        item.copyright = [text]
        items.append(item)

    assert _get_top_merge_values(items, lambda i: i.copyright) == [
        "Copyright Z",
        "Copyright A",
        "Copyright M",
    ]
