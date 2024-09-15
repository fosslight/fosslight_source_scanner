import os
import subprocess

def run_command(command):
    process=subprocess.run(command, shell=True, capture_output=True, text=True)
    print(process.stdout)
    if process.returncode !=0:
        print(process.stderr)
        raise Exception(f"Command failed: {command}")

def test_run():
    run_command("rm -rf test_scan")
    run_command("fosslight_source -p test/test_files -j -m -o test_scan")
    run_command("fosslight_source -p tests -e test_files/test cli_test.py -j -m -o test_scan2")

def test_release():
    run_command("fosslight_source -h")
    run_command("fosslight_source -p tests/test_files -o test_scan/scan_result.csv")
    run_command("fosslight_source -p tests -e test_files/test cli_test.py -j -m -o test_scan2/scan_exclude_result.csv")
    run_command("fosslight_source -p tests/test_files -m -j -o test_scan3/")   
    run_command("python tests/cli_test.py")    
    run_command("pytest -v --flake8")

def test_flake8():
    run_command("flake8")