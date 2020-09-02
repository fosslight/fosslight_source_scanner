#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: LicenseRef-LGE-Proprietary

import xlsxwriter


def write_result_to_excel(out_file_name, sheet_list):
    try:
        workbook = xlsxwriter.Workbook(out_file_name)
        for sheet_name, sheet_contents in sheet_list.items():
            worksheet_src = create_worksheet(workbook, sheet_name,
                                             ['ID', 'Source Name or Path', 'OSS Name', 'OSS Version', 'License',
                                              'Download Location', 'Homepage',
                                              'Copyright Text',
                                              'License Text', 'Exclude', 'Comment'])
            write_result_to_sheet(worksheet_src, sheet_contents)
        workbook.close()
    except Exception as ex:
        print('* Error :' + str(ex))


def write_result_to_sheet(worksheet, list_to_print):
    row = 1  # Start from the first cell.
    for item_info in list_to_print:
        row_item = item_info.get_row_to_print()
        worksheet.write(row, 0, row)
        for col_num, value in enumerate(row_item):
            worksheet.write(row, col_num + 1, value)
        row += 1


def create_worksheet(workbook, sheet_name, header_row):
    worksheet = workbook.add_worksheet(sheet_name)
    for col_num, value in enumerate(header_row):
        worksheet.write(0, col_num, value)
    return worksheet
