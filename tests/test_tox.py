#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import subprocess
import pytest
import shutil

remove_directories = ["test_scan", "test_scan2", "test_scan3"]


@pytest.fixture(scope="module", autouse=True)
def setup_test_result_dir_and_teardown():
    print("==============setup==============")
    for dir in remove_directories:
        if os.path exists(dir):
            shutil.rmtree(dir)

    yield

    print("==============tearDown==============")
    for dir in remove_directories:
        if os.path.exists(dir):
            shutil.rmtree(dir)


def run_command(command):
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    success = (process.returncode == 0)
    return success, process.stdout if success else process.stderr


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
    success, _ = run_command("fosslight_source -h")
    assert success is True, "Test Release: Help command failed "


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
