<p align="center">
  <a href="https://github.com/fosslight/fosslight_source">
    <img alt="fosslight" src="docs/img/fosslight_source.png">
  </a>
</p>
<p align="center">
  <strong>Detect the license for the source code.</strong><br>
  Use Source Code Scanner to detect copyright text and license text in the file.
</p>

<p align="center">
    <img src="https://img.shields.io/badge/license-Apache--2.0-orange.svg" alt="FOSSLight Source is released under the Apache-2.0 License." />
    <img src="https://img.shields.io/badge/pypi-1.4.0-brightgreen.svg" alt="Current python package version." />
    <img src="https://img.shields.io/badge/python-3.6+-blue.svg" />
</p>

**FOSSLight Source** uses [ScanCode][sc], a source code scanner, to detect the copyright and license phrases contained in the file. Some files (ex- build script), binary files, directory and files in specific directories (ex-test) are excluded from the result. And removes words such as "-only" and "-old-style" from the license name to be printed. The output result is generated in Excel format.

[sc]: https://github.com/nexB/scancode-toolkit

## Contents

- [Prerequisite](#-prerequisite)
- [How to install](#-how-to-install)
- [How to run](#-how-to-run)
- [Result](#-result)
- [How to report issue](#-how-to-report-issue)
- [License](#-license)


## 📋 Prerequisite

FOSSLight Source needs a Python 3.6+.    
For windows, you need to install [Microsoft Visual C++ Build Tools][ms_build].

[ms_build]: https://visualstudio.microsoft.com/vs/older-downloads/

## 🎉 How to install

It can be installed using pip3. It is recommended to install it in the [python 3.6 + virtualenv](docs/Guide_virtualenv.md) environment.

```
$ pip3 install fosslight_source
```

## 🚀 How to run

There are two commands for FOSSLight Scanner. 

### 1. fosslight_source
After executing ScanCode, the source code scanner, print the OSS Report.

| Parameter  | Argument | Description |
| ------------- | ------------- | ------------- |
| h | None | Print help message. | 
| p | String | Path to detect source. | 
| j | None | As an output, the result of executing ScanCode in json format other than OSS Report is additionally generated. | 
| o | String | Output file name without file extension. | 

#### Ex. Print result to OSS Report and json file
```
$ fosslight_source -p /home/source_path -j
```

### 2. fosslight_convert
Converts the result of executing ScanCode in json format into OSS Report format.    
| Parameter  | Argument | Description |
| ------------- | ------------- | ------------- |
| h | None | Print help message. | 
| p | String | Path of ScanCode json files. | 
| o | String | Output file name without file extension. | 
   
#### Ex. Converting scancode json result to OSS report
```
$ fosslight_convert -p /home/jsonfile_dir
```

## 📁 Result

```
$ tree
.
├── OSS-Report_2021-03-21_20-44-34.xlsx
├── fosslight_src_log_2021-03-21_20-44-34.txt
├── result_2021-03-21_20-44-34.csv
└── scancode_2021-03-21_20-44-34.json

```
- OSS_Report-[datetime].xlsx : FOSSLight Source result in OSS Report format.
- result_[datetime].csv : Excluding windows, this is the result of outputting the OSS Report in csv format.
- fosslight_src_log_[datetime].txt: This is the file where the execution log is saved.
- scancode_[datetime].json : This is the ScanCode result when the -j option is given with the fosslight_source command.


## 👏 How to report issue

Please report any ideas or bugs to improve by creating an issue in [Git Repository][repo]. Then there will be quick bug fixes and upgrades. Ideas to improve are always welcome.

[repo]: https://github.com/fosslight/fosslight_source/issues

## 📄 License

FOSSLight Source is Apache-2.0, as found in the [LICENSE][l] file.

[l]: https://github.com/fosslight/fosslight_source/blob/main/LICENSE
