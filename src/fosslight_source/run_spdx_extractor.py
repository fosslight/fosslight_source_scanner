#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import re
import fosslight_util.constant as constant
import mmap

logger = logging.getLogger(constant.LOGGER_NAME)


def get_spdx_downloads(path_to_scan: str, path_to_exclude: set = None) -> dict:
    download_dict = {}
    find_word = re.compile(rb"SPDX-PackageDownloadLocation\s*:\s*(\S+)", re.IGNORECASE)
    abs_path_to_scan = os.path.abspath(path_to_scan)

    for root, dirs, files in os.walk(path_to_scan):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path_file = os.path.relpath(file_path, abs_path_to_scan).replace('\\', '/')
            if rel_path_file in path_to_exclude:
                continue
            try:
                if os.path.getsize(file_path) > 0:
                    with open(file_path, "r") as f:
                        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmap_obj:
                            for word in find_word.findall(mmap_obj):
                                if rel_path_file in download_dict:
                                    download_dict[rel_path_file].append(word.decode('utf-8'))
                                else:
                                    download_dict[rel_path_file] = [word.decode('utf-8')]
            except Exception as ex:
                logger.warning(f"Failed to extract SPDX download location. {rel_path_file}, {ex}")
    return download_dict
