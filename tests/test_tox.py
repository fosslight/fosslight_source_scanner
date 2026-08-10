#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import shlex
import subprocess
import pytest
import shutil
import sys
import csv
import glob

# Add project root to sys.path for importing FL Source modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import after sys.path modification to access our custom GPL license functions
# flake8: noqa E402
from fosslight_source._parsing_scancode_file_item import (
    filter_fsf_copyright_from_gpl_license_text,
)

remove_directories = ["test_scan", "test_scan2", "test_scan3"]
TEST_FILES_SCAN_DIR = "test_scan"


def _parse_license_tokens(license_value: str) -> set[str]:
    return {token.strip().lower() for token in (license_value or "").split(",") if token.strip()}


def _read_src_csv_rows(csv_path: str) -> list[dict]:
    with open(csv_path, "r", encoding="utf-8") as file:
        return list(csv.DictReader(file, delimiter="\t"))


def _rows_for_source(rows: list[dict], source_name: str) -> list[dict]:
    return [row for row in rows if row.get("Source Path") == source_name]


def _find_scan_csv(output_dir: str) -> str:
    csv_files = sorted(glob.glob(os.path.join(output_dir, "*.csv")))
    assert csv_files, f"No CSV report found under {output_dir}"
    return csv_files[-1]


@pytest.fixture(scope="module", autouse=True)
def setup_test_result_dir():
    print("==============setup==============")
    for dir in remove_directories:
        if os.path.exists(dir):
            shutil.rmtree(dir)

    yield


def run_command(command):
    command = command.strip()
    if command.startswith("fosslight_source"):
        args = shlex.split(command, posix=(os.name != "nt"))[1:]
        if os.environ.get("FOSSLIGHT_USE_LOCAL_SRC"):
            src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
            env = os.environ.copy()
            existing = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = src_path if not existing else f"{src_path}{os.pathsep}{existing}"
            cmd = [sys.executable, "-m", "fosslight_source.cli", *args]
            process = subprocess.run(cmd, capture_output=True, text=True, env=env)
        else:
            cmd = ["fosslight_source", *args]
            process = subprocess.run(cmd, capture_output=True, text=True)
    else:
        process = subprocess.run(command, shell=True, capture_output=True, text=True)
    success = process.returncode == 0
    return success, process.stdout if success else process.stderr


def test_filter_fsf_copyright_from_gpl_license_text():
    fsf = "Copyright (c) 2007 Free Software Foundation, Inc."
    other = "Copyright (c) 2020 LG Electronics Inc."
    copyrights = [fsf, other]

    # GPL-family license text: drop FSF boilerplate, keep others
    for licenses in (["gpl-2.0"], ["lgpl-3.0"], ["agpl-3.0"], ["gfdl-1.3"], ["mit", "gpl-3.0"]):
        assert filter_fsf_copyright_from_gpl_license_text(copyrights, licenses, True) == [other]

    # Non-GPL license text, or not license text: keep all
    assert filter_fsf_copyright_from_gpl_license_text(copyrights, ["mit"], True) == copyrights
    assert filter_fsf_copyright_from_gpl_license_text(copyrights, ["gpl-2.0"], False) == copyrights
    assert filter_fsf_copyright_from_gpl_license_text(copyrights, [], True) == copyrights


def test_run():
    scan_success, _ = run_command("fosslight_source -p tests/test_files -j -m -o test_scan")
    scan_exclude_success, _ = run_command("fosslight_source -p tests -e test_files/test cli_test.py -j -m -o test_scan2")
    scan_files = os.listdir("test_scan")
    scan2_files = os.listdir('test_scan2')

    assert scan_success is True, "Test Run: Scan command failed"
    assert scan_exclude_success is True, "Test Run: Exclude command failed"
    assert len(scan_files) > 0, "Test Run: No scan files created in test_scan directory"
    assert len(scan2_files) > 0, "Test Run: No scan files created in test_scan2 directory"


def test_test_files_scan_results():
    os.makedirs(TEST_FILES_SCAN_DIR, exist_ok=True)

    success, msg = run_command(
        f"fosslight_source -p tests/test_files -s scancode -f csv -o {TEST_FILES_SCAN_DIR}/"
    )
    assert success is True, f"Test Run: test_files scan failed: {msg}"

    csv_path = _find_scan_csv(TEST_FILES_SCAN_DIR)
    rows = _read_src_csv_rows(csv_path)

    sample_rows = _rows_for_source(rows, "sample.cpp")
    assert sample_rows, "Test Run: sample.cpp not found in scan result"
    for row in sample_rows:
        licenses = _parse_license_tokens(row.get("License", ""))
        assert "apache-2.0" in licenses, f"sample.cpp missing Apache-2.0 license: {row.get('License')}"
        assert "mit" in licenses, f"sample.cpp missing MIT license: {row.get('License')}"

    temp_rows = _rows_for_source(rows, "temp.cpp")
    assert temp_rows, "Test Run: temp.cpp not found in scan result"
    temp_row = temp_rows[0]
    temp_licenses = _parse_license_tokens(temp_row.get("License", ""))
    assert "apache-2.0" in temp_licenses, f"temp.cpp missing Apache-2.0 license: {temp_row.get('License')}"
    assert (temp_row.get("Copyright Text") or "").strip(), "Test Run: temp.cpp copyright not extracted"


def test_help_command():
    success, msg = run_command("fosslight_source -h")
    assert success is True, f"Test Release: Help command failed :{msg}"


def test_scan_command():
    os.makedirs("test_scan", exist_ok=True)

    success, _ = run_command("fosslight_source -p tests/test_files -o test_scan/scan_result.csv")
    assert success is True, "Test Release: Failed to generate scan result CSV file"

    assert os.path.exists("test_scan/scan_result.csv"), "Test Release: scan_result.csv file not generated"

    with open("test_scan/scan_result.csv", 'r') as file:
        content = file.read()

    assert len(content) > 0, "Test Release: scan_result.csv is empty"
    print(f"Content of scan_result.csv:\n{content}")


def test_exclude_command():
    os.makedirs("test_scan2", exist_ok=True)

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
    os.makedirs("test_scan3", exist_ok=True)

    success, _ = run_command("fosslight_source -p tests/test_files -m -j -o test_scan3/")
    assert success is True, "Test release: Failed to generate JSON files"


def test_ls_test_scan3_command():
    files_in_test_scan3 = os.listdir("test_scan3")
    assert len(files_in_test_scan3) > 0, "Test Release: test_scan3 is empty"
    print(f"Files in test_scan3: {files_in_test_scan3}")


def test_flake8():
    success, _ = run_command("flake8 -j 4")
    assert success is True, "Flake8: Style check failed"
