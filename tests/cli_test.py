#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
from datetime import datetime
import logging
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from fosslight_source.run_scancode import run_scan
from fosslight_source.run_scanoss import run_scanoss_py

logger = logging.getLogger(constant.LOGGER_NAME)


def main():
    global logger

    path_to_find_bin = os.path.abspath("tests/test_files/test")
    _start_time = datetime.now().strftime('%y%m%d_%H%M')
    output_file_name = ""

    fosslight_report_name = "test_result_func_call/result"
    output_dir = os.path.dirname(os.path.abspath(output_file_name))

    logger, result_item = init_log(os.path.join(output_dir, "fosslight_log_"+_start_time+".txt"))

    ret = run_scan(path_to_find_bin, fosslight_report_name, True, -1, True, True, "", False)
    ret_scanoss = run_scanoss_py(path_to_find_bin, fosslight_report_name, "", False, True, -1)

    logger.warning("[Scan] Result: %s" % (ret[0]))
    logger.warning("[Scan] Result_msg: %s" % (ret[1]))

    if len(ret) > 2:
        try:
            for scan_item in ret[2]:
                logger.warning(scan_item.get_row_to_print())
        except Exception as ex:
            logger.error("Error:"+str(ex))
    if ret_scanoss:
        for scan_item in ret_scanoss:
            logger.warning(scan_item.get_row_to_print())


if __name__ == '__main__':
    main()
