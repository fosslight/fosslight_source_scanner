#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.help import PrintHelpMsg

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
            -j\t\t\t\t   Generate additional result of executing ScanCode in json format
            -m\t\t\t\t   Print the Matched text for each license on a separate sheet
            -o <file_name>\t\t   Output file name"""

_HELP_MESSAGE_CONVERT = """
    Usage: fosslight_convert [option1] <arg1> [option2] <arg2>...

    FOSSLigtht_convert converts the result of executing ScanCode in json format into FOSSLight Report format.

    Options:
        Mandatory
            -p <path_dir>\t\t   Path of ScanCode json files

        Optional
            -h\t\t\t\t   Print help message
            -m\t\t\t\t   Print the Matched text for each license on a separate sheet
            -o <file_name>\t\t   Output file name"""


def print_help_msg_source():
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_SOURCE)
    helpMsg.print_help_msg(True)


def print_help_msg_convert():
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_CONVERT)
    helpMsg.print_help_msg(True)
