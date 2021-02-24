#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: LicenseRef-LGE-Proprietary

import logging
import os

def init_log(file_name_suffix, log_dir):
    log_level = logging.WARNING
    log_file = os.path.join(log_dir, "fosslight_src_log_" + file_name_suffix + ".txt")
    logging.basicConfig(filename=log_file, level=log_level,
                        format='%(message)s')
    # set up logging to console
    console = logging.StreamHandler()
    console.setLevel(log_level)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    logger = logging.getLogger('fosslight_source')

    return logger