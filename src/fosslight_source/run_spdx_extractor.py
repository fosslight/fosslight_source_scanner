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


def get_spdx_downloads(file_path: str) -> list[str]:
    results = []
    find_word = re.compile(rb"SPDX-PackageDownloadLocation\s*:\s*(\S+)", re.IGNORECASE)
    try:
        if os.path.getsize(file_path) > 0:
            with open(file_path, "r") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmap_obj:
                    for word in find_word.findall(mmap_obj):
                        results.append(word.decode('utf-8'))
    except Exception as ex:
        logger.warning(f"Failed to extract SPDX download location. {file_path}, {ex}")
    return results
