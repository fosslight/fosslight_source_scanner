#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from pathlib import Path


def init_log(file_name_suffix, log_dir):

    logger = logging.getLogger('fosslight_source')
    log_level = logging.WARNING
    formatter = logging.Formatter('%(message)s')
    log_file = os.path.join(log_dir,
                            "fosslight_src_log_" + file_name_suffix + ".txt")

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    file_hanlder = logging.FileHandler(log_file)
    file_hanlder.setLevel(log_level)
    file_hanlder.setFormatter(formatter)
    file_hanlder.propagate = False

    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(formatter)
    console.propagate = False

    logger.addHandler(file_hanlder)
    logger.addHandler(console)
    logger.propagate = False

    return logger
