#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.help import PrintHelpMsg, print_package_version
from fosslight_util.output_format import SUPPORT_FORMAT

_HELP_MESSAGE_SOURCE_SCANNER = f"""
    📖 Usage
    ────────────────────────────────────────────────────────────────────
    fosslight_source [options] <arguments>

    📝 Description
    ────────────────────────────────────────────────────────────────────
    FOSSLight Source Scanner analyzes source code to detect copyright and
    license information using several modes.

    Note: Build scripts, binary files, and test directories are automatically
          excluded from analysis.

    📚 Guide: https://fosslight.org/fosslight-guide/scanner/2_source.html

    ⚙️  General Options
    ────────────────────────────────────────────────────────────────────
    -p <path>              Source path to analyze (default: current directory)
    -o <path>              Output file path or directory
    -f <format>            Output formats: {', '.join(SUPPORT_FORMAT)}
                           (multiple formats can be specified, separated by space)
    -e <pattern>           Exclude paths from analysis (files and directories)
                           ⚠️  IMPORTANT: Always wrap in quotes to avoid shell expansion
                           Example: fosslight_source -e "dev/" "tests/" "*.jar"
    -m                     Generate detailed scan results on separate sheets
    -h                     Show this help message
    -v                     Show version information

    🔍 Scanner-Specific Options
    ────────────────────────────────────────────────────────────────────
    -s <mode>              Choose mode: scancode, scanoss, kb, or all(default)
    -c <number>            Number of CPU cores/threads to use for scanning
    -t <seconds>           Timeout in seconds for ScanCode scanning
    -j                     Generate raw scanner results in JSON format
    --no_correction        Skip OSS information correction with sbom-info.yaml
    --correct_fpath <path> Path to custom sbom-info.yaml file

    💡 Examples
    ────────────────────────────────────────────────────────────────────
    # Scan current directory
    fosslight_source

    # Scan specific path with exclusions
    fosslight_source -p /path/to/source -e "test/" "node_modules/"

    # Generate output in specific format
    fosslight_source -f excel -o results/

    # Generate raw scanner results in JSON format
    fosslight_source -p /path/to/source -j
"""


def print_version(pkg_name: str) -> None:
    print_package_version(pkg_name, "FOSSLight Source Scanner Version:")


def print_help_msg_source_scanner() -> None:
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_SOURCE_SCANNER)
    helpMsg.print_help_msg(True)
