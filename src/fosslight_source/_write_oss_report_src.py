#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import xlsxwriter
import csv
import time
import logging
import fosslight_util.constant as constant

_SRC_HEADER = ['ID', 'Source Name or Path', 'OSS Name',
               'OSS Version', 'License',  'Download Location',
               'Homepage', 'Copyright Text',  'License Text',
               'Exclude', 'Comment']

logger = logging.getLogger(__name__)


def write_result_to_csv(output_file, sheet_list):
    try:
        row_num = 1
        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(_SRC_HEADER)
            for sheet_name, sheet_contents in sheet_list.items():
                # Sorting
                sheet_contents = sorted(
                    sheet_contents, key=lambda row: (''.join(row.licenses)))
                for item_info in sheet_contents:
                    item_to_print = item_info.get_row_to_print()
                    item_to_print.insert(0, row_num)
                    writer.writerow(item_to_print)
                    row_num += 1
    except Exception as ex:
        logger.warn('* Error :' + str(ex))


def write_result_to_excel(out_file_name, sheet_list):
    try:
        workbook = xlsxwriter.Workbook(out_file_name)
        for sheet_name, sheet_contents in sheet_list.items():
            worksheet_src = create_worksheet(workbook, sheet_name, _SRC_HEADER)
            write_result_to_sheet(worksheet_src, sheet_contents)
        workbook.close()
    except Exception as ex:
        logger.warn('* Error :' + str(ex))


def write_result_to_sheet(worksheet, list_to_print):
    row = 1  # Start from the first cell.
    # Sorting
    list_to_print = sorted(
        list_to_print, key=lambda row: (''.join(row.licenses)))
    for item_info in list_to_print:
        row_item = item_info.get_row_to_print()
        worksheet.write(row, 0, row)
        for col_num, value in enumerate(row_item):
            worksheet.write(row, col_num + 1, value)
        row += 1


def create_worksheet(workbook, sheet_name, header_row):
    if len(sheet_name) > 31:
        current_time = str(time.time())
        logger.warn('* Sheet name: '+sheet_name + ' -> '+current_time)
        sheet_name = current_time
    worksheet = workbook.add_worksheet(sheet_name)
    for col_num, value in enumerate(header_row):
        worksheet.write(0, col_num, value)
    return worksheet
