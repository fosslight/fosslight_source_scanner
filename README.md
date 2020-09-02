# Scancode analysis in OSS_Report format
## When you first set up your environment -linux
$ pip install virtualenv     
$ virtualenv -p /usr/bin/python3.6 venv     
$ source venv/bin/activate        
$ pip install http://mod.lge.com/code/rest/archive/latest/projects/OSC/repos/scancode_to_excel/archive?format=zip        

<hr />     

## How to run the script - Source code analysis with Scancode
### Print result to OSS Report
$ ./run_scancode.py -p [Path_to_scan]
### Print result to OSS Report and json file
$ ./run_scancode.py -p [Path_to_scan] -j
## How to run the script - Converting scancode json result to OSS report
$ ./convert_scancode.py -p [Path_of_scancode_json_files]
<hr />       

## How to run it by command
### Print result to OSS Report
$ run_scancode -p [Path_to_scan]
### Print result to OSS Report and json file
$ run_scancode -p [Path_to_scan] -j
## How to run the script - Converting scancode json result to OSS report
$ convert_scancode -p [Path_of_scancode_json_files]

<hr />     

## How to make a wheel file
$ python setup.py bdist_wheel
