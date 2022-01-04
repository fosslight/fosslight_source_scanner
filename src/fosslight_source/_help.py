#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.help import PrintHelpMsg, print_package_version

_HELP_MESSAGE_SOURCE = """
    Usage: fosslight_source [option1] <arg1> [option2] <arg2>...

    FOSSLight Source uses ScanCode, a source code scanner, to detect the copyright and license phrases
    contained in the file. Some files (ex- build script), binary files, directory and files in specific
    directories (ex-test) are excluded from the result.
    And removes words such as “-only” and “-old-style” from the license name to be printed.
    The output result is generated in Excel format.

    Options:
        Mandatory
            -p <source_path>\t\t   Path to analyze source

        Optional
            -h\t\t\t\t   Print help message
            -v\t\t\t\t   Print FOSSLight Source Scanner version
            -j\t\t\t\t   Generate raw result of scanners in json format
            -m\t\t\t\t   Print the Matched text for each license on a separate sheet (Scancode Only)
            -o <output_path>\t\t   Output path
            \t\t\t\t    (If you want to generate the specific file name, add the output path with file name.)
            -f <format>\t\t\t   Output file format (excel, csv, opossum)
            -s <scanner>\t\t   Select which scanner to be run (scancode, scanoss, all)"""

_HELP_MESSAGE_CONVERT = """
    Usage: fosslight_convert [option1] <arg1> [option2] <arg2>...

    FOSSLigtht_convert converts the result of executing ScanCode in json format into FOSSLight Report format.

    Options:
        Mandatory
            -p <path_dir>\t\t   Path of ScanCode json files

        Optional
            -h\t\t\t\t   Print help message
            -v\t\t\t\t   Print FOSSLight Source Scanner version
            -m\t\t\t\t   Print the Matched text for each license on a separate sheet
            -o <output_path>\t\t   Output path
            \t\t\t\t    (If you want to generate the specific file name, add the output path with file name.)
            -f <format>\t\t\t   Output file format (excel, csv, opossum)"""


def print_version(pkg_name):
    print_package_version(pkg_name, "FOSSLight Source Scanner Version")


def print_help_msg_source():
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_SOURCE)
    helpMsg.print_help_msg(True)


def print_help_msg_convert():
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_CONVERT)
    helpMsg.print_help_msg(True)
