#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Version 1.0
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: LicenseRef-LGE-Proprietary

import getopt
import hashlib
import os
import sys
import json
import xlsxwriter
from datetime import datetime

_replace_word = ["-only", "-old-style", "-or-later"]


class ScanCodeItem:
    file = ""
    licenses = []
    copyright = ""

    def __init__(self, value):
        self.file = value
        self.copyright = []
        self.licenses = []
        self.comment = ""

    def __del__(self):
        pass

    def set_comment(self, value):
        self.comment = value

    def set_file(self, value):
        self.file = value

    def set_copyright(self, value):
        self.copyright.extend(value)
        if len(self.copyright) > 0:
            self.copyright = list(set(self.copyright))

    def set_licenses(self, value):
        self.licenses.extend(value)
        if len(self.licenses) > 0:
            self.licenses = list(set(self.licenses))

    def get_row_to_print(self):
        print_rows = [self.file, "", "", ','.join(self.licenses), "", "", ','.join(self.copyright), "", "",
                      self.comment]
        return print_rows


def convert_json_to_excel(scancode_result_json):
    try:
        start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        sheet_list = {}
        if os.path.isfile(scancode_result_json):
            file_list = get_detected_licenses_from_scancode(scancode_result_json)
            if len(file_list) > 0:
                sheet_list["SRC"] = file_list
        elif os.path.isdir(scancode_result_json):
            for root, dirs, files in os.walk(scancode_result_json):
                for file in files:
                    if file.endswith(".json"):
                        try:
                            result_file = os.path.join(root, file)
                            file_list = get_detected_licenses_from_scancode(result_file)
                            if len(file_list) > 0:
                                file_name = os.path.basename(file)
                                sheet_list["SRC_" + file_name] = file_list
                        except:
                            pass

        if len(sheet_list) > 0:
            oss_report_name = "OSS_Report-" + start_time + ".xlsx"
            write_result_to_excel(oss_report_name, sheet_list)
        else:
            print("Nothing to print.")


    except Exception as ex:
        print(str(ex))


def get_detected_licenses_from_scancode(scancode_json_file):
    file_list = []
    try:
        print("Start parsing " + scancode_json_file)
        with open(scancode_json_file, "r") as st_json:
            st_python = json.load(st_json)
            for file in st_python["files"]:
                is_binary = file["is_binary"]
                is_dir = file["type"] == "directory"
                if not is_binary and not is_dir:
                    file_path = file["path"]
                    licenses = file["licenses"]
                    copyright_list = file["copyrights"]

                    result_item = ScanCodeItem(file_path)
                    copyright_value_list = [x["value"] for x in copyright_list]
                    result_item.set_copyright(copyright_value_list)

                    license_expression_list = file["license_expressions"]
                    license_expression_list = [x.lower() for x in license_expression_list]

                    license_detected = []
                    for lic_item in licenses:
                        license_value = ""
                        key = lic_item["key"].lower()
                        spdx = lic_item["spdx_license_key"].lower()
                        if key in license_expression_list:
                            license_expression_list.remove(key)
                        if spdx != "":
                            license_value = spdx
                        else:
                            license_value = key
                        if license_value != "":
                            for word in _replace_word:
                                if word in license_value:
                                    license_value = license_value.replace(word, "")
                            license_detected.append(license_value)
                    if len(license_detected) > 0:
                        result_item.set_licenses(license_detected)

                        if len(license_expression_list) > 0:
                            license_expression_list = list(set(license_expression_list))
                            result_item.set_comment(','.join(license_expression_list))
                        file_list.append(result_item)
    except:
        pass
    print("|---Number of files detected: "+str(len(file_list)))
    return file_list


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


def main():
    convert_json_to_excel("test_scancode_result")


if __name__ == "__main__":
    main()
