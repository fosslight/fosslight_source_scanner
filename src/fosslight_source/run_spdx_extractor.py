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


def get_spdx_metadata(file_path: str) -> tuple[list[str], list[str]]:
    downloads = []
    licenses = []
    download_pattern = re.compile(rb"SPDX-PackageDownloadLocation\s*:\s*(\S+)", re.IGNORECASE)
    license_pattern = re.compile(rb"SPDX-License-Identifier\s*:\s*([^\r\n]+)", re.IGNORECASE)
    try:
        if os.path.getsize(file_path) > 0:
            with open(file_path, "rb") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmap_obj:
                    downloads = [word.decode('utf-8').strip() for word in download_pattern.findall(mmap_obj)]
                    licenses = [word.decode('utf-8').strip() for word in license_pattern.findall(mmap_obj)]
    except Exception as ex:
        logger.warning(f"Failed to extract SPDX metadata. {file_path}, {ex}")
    return downloads, licenses
