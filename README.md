# Scancode analysis in OSS_Report format
## When you first set up your environment -linux
$ pip install virtualenv     
$ virtualenv -p /usr/bin/python3.6 venv     
$ source venv/bin/activate        
$ pip install -r requirements.txt        
$ git clone https://github.com/nexB/scancode-toolkit.git      
$ git checkout bce3557006fe8e3104d97cf2ad26ca2ea60e87df       
$ python setup.py clean      
$ python setup.py build      
$ python setup.py install        

## How to run the script - Source code analysis with Scancode
### Print result to OSS Report
$ ./run_scancode.py -p [Path_to_scan]
### Print result to OSS Report and json file
$ ./run_scancode.py -p [Path_to_scan] -j
## How to run the script - Converting scancode json result to OSS report
$ ./convert_scancode.py -p [Path_of_scancode_json_files]
