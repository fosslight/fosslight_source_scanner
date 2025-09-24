#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import subprocess
import pytest
import shutil
import sys

# Add project root to sys.path for importing FL Source modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import after sys.path modification to access our custom GPL license functions
# flake8: noqa E402
from fosslight_source._parsing_scancode_file_item import (
    is_gpl_family_license, should_remove_copyright_for_gpl_license_text
)

remove_directories = ["test_scan", "test_scan2", "test_scan3"]


@pytest.fixture(scope="module", autouse=True)
def setup_test_result_dir():
    print("==============setup==============")
    for dir in remove_directories:
        if os.path.exists(dir):
            shutil.rmtree(dir)

    yield


def run_command(command):
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    success = (process.returncode == 0)
    return success, process.stdout if success else process.stderr


def test_is_gpl_family_license():
    gpl_licenses = [
        ["gpl-2.0"],
        ["gpl-3.0"],
        ["lgpl-2.1"],
        ["lgpl-3.0"],
        ["agpl-3.0"],
        ["GPL-2.0"],
        ["LGPL-2.1"],
        ["AGPL-3.0"],
        ["gpl-2.0-only"],
        ["lgpl-2.1-only"],
        ["agpl-3.0-only"],
        ["gfdl-1.3"],
        ["gpl-2.0", "mit"],
        ["mit", "lgpl-3.0"]
    ]

    non_gpl_licenses = [
        ["mit"],
        ["apache-2.0"],
        ["bsd-3-clause"],
        ["mozilla-2.0"],
        ["isc"],
        [],
        ["mit", "apache-2.0"]
    ]

    for licenses in gpl_licenses:
        assert is_gpl_family_license(licenses), \
            f"Should detect GPL family license: {licenses}"

    for licenses in non_gpl_licenses:
        assert not is_gpl_family_license(licenses), \
            f"Should not detect GPL family license: {licenses}"


def test_should_remove_copyright_for_gpl_license_text():
    assert should_remove_copyright_for_gpl_license_text(["gpl-2.0"], True), \
        "Should remove copyright for GPL license text file"
    assert should_remove_copyright_for_gpl_license_text(["lgpl-3.0"], True), \
        "Should remove copyright for LGPL license text file"
    assert should_remove_copyright_for_gpl_license_text(["agpl-3.0"], True), \
        "Should remove copyright for AGPL license text file"

    assert not should_remove_copyright_for_gpl_license_text(["gpl-2.0"], False), \
        "Should NOT remove copyright for GPL source file"
    assert not should_remove_copyright_for_gpl_license_text(["lgpl-3.0"], False), \
        "Should NOT remove copyright for LGPL source file"

    assert not should_remove_copyright_for_gpl_license_text(["mit"], True), \
        "Should NOT remove copyright for MIT license text file"
    assert not should_remove_copyright_for_gpl_license_text(["apache-2.0"], True), \
        "Should NOT remove copyright for Apache license text file"

    assert not should_remove_copyright_for_gpl_license_text(["mit"], False), \
        "Should NOT remove copyright for MIT source file"

    assert not should_remove_copyright_for_gpl_license_text([], True), \
        "Should NOT remove copyright for empty license list"
    assert not should_remove_copyright_for_gpl_license_text([], False), \
        "Should NOT remove copyright for empty license list"


def test_run():
    scan_success, _ = run_command("fosslight_source -p tests/test_files -j -m -o test_scan")
    scan_exclude_success, _ = run_command("fosslight_source -p tests -e test_files/test cli_test.py -j -m -o test_scan2")
    scan_files = os.listdir("test_scan")
    scan2_files = os.listdir('test_scan2')

    assert scan_success is True, "Test Run: Scan command failed"
    assert scan_exclude_success is True, "Test Run: Exclude command failed"
    assert len(scan_files) > 0, "Test Run: No scan files created in test_scan directory"
    assert len(scan2_files) > 0, "Test Run: No scan files created in test_scan2 directory"


def test_help_command():
    success, msg = run_command("fosslight_source -h")
    assert success is True, f"Test Release: Help command failed :{msg}"


def test_scan_command():
    success, _ = run_command("fosslight_source -p tests/test_files -o test_scan/scan_result.csv")
    assert success is True, "Test Release: Failed to generate scan result CSV file"

    assert os.path.exists("test_scan/scan_result.csv"), "Test Release: scan_result.csv file not generated"

    with open("test_scan/scan_result.csv", 'r') as file:
        content = file.read()

    assert len(content) > 0, "Test Release: scan_result.csv is empty"
    print(f"Content of scan_result.csv:\n{content}")


def test_exclude_command():
    success, _ = run_command(
        "fosslight_source -p tests -e test_files/test cli_test.py -j -m -o test_scan2/scan_exclude_result.csv"
    )
    assert success is True, "Test release: Exclude scan failded"

    assert os.path.exists("test_scan2/scan_exclude_result.csv"), "Test Release: scan_exclude_result.csv file not generated"

    with open("test_scan2/scan_exclude_result.csv", 'r') as file:
        content = file.read()

    assert len(content) > 0, "Test Release: scan_exclude_result.csv is empty"
    print(f"Content of scan_exclude_result.csv:\n{content}")


def test_json_command():
    success, _ = run_command("fosslight_source -p tests/test_files -m -j -o test_scan3/")
    assert success is True, "Test release: Failed to generate JSON files"


def test_ls_test_scan3_command():
    files_in_test_scan3 = os.listdir("test_scan3")
    assert len(files_in_test_scan3) > 0, "Test Release: test_scan3 is empty"
    print(f"Files in test_scan3: {files_in_test_scan3}")


def test_flake8():
    success, _ = run_command("flake8 -j 4")
    assert success is True, "Flake8: Style check failed"
