<!--
Copyright (c) 2021 LG Electronics
SPDX-License-Identifier: Apache-2.0
 -->
<p align='right'>
  <a href="https://github.com/fosslight/fosslight_source_scanner/blob/main/docs/README_Kor.md">
    [Korean]
 </a>
</p>

# FOSSLight Source Scanner

<img src="https://img.shields.io/pypi/l/fosslight_source" alt="FOSSLight Source Scanner is released under the Apache-2.0 License." /> <img src="https://img.shields.io/pypi/v/fosslight_source" alt="Current python package version." /> <img src="https://img.shields.io/pypi/pyversions/fosslight_source" /> [![REUSE status](https://api.reuse.software/badge/github.com/fosslight/fosslight_source_scanner)](https://api.reuse.software/info/github.com/fosslight/fosslight_source_scanner)
</p>

```note
Detect the license for the source code.
Use Source Code Scanner and process the scanner results.
```

**FOSSLight Source Scanner** uses [ScanCode][sc], a source code scanner, to detect the copyright and license phrases contained in the file. Some files (ex- build script), binary files, directory and files in specific directories (ex-test) are excluded from the result. And removes words such as "-only" and "-old-style" from the license name to be printed. The output result is generated in Excel format.


[sc]: https://github.com/nexB/scancode-toolkit

## Contents

- [Prerequisite](#-prerequisite)
- [How to install](#-how-to-install)
- [How to run](#-how-to-run)
- [Result](#-result)
- [How to report issue](#-how-to-report-issue)
- [License](#-license)


## 📋 Prerequisite

FOSSLight Source Scanner needs a Python 3.6+.    
For windows, you need to install [Microsoft Visual C++ Build Tools][ms_build].

[ms_build]: https://visualstudio.microsoft.com/vs/older-downloads/

## 🎉 How to install

It can be installed using pip3. It is recommended to install it in the [python 3.6 + virtualenv](https://github.com/fosslight/fosslight_source_scanner/blob/main/docs/Guide_virtualenv.md) environment.

```
$ pip3 install fosslight_source
```

## 🚀 How to run

There are two commands for FOSSLight Source Scanner. 

### 1. fosslight_source
After executing ScanCode, the source code scanner, print the FOSSLight Report.

| Parameter  | Argument | Description |
| ------------- | ------------- | ------------- |
| h | None | Print help message. | 
| p | String | Path to detect source. | 
| j | None | As an output, the result of executing ScanCode in json format other than FOSSLight Report is additionally generated. | 
| o | String | Output file name without file extension. | 

#### Ex. Print result to FOSSLight Report and json file
```
$ fosslight_source -p /home/source_path -j
```

### 2. fosslight_convert
Converts the result of executing ScanCode in json format into FOSSLight Report format.  

| Parameter  | Argument | Description |
| ------------- | ------------- | ------------- |
| h | None | Print help message. | 
| p | String | Path of ScanCode json files. | 
| o | String | Output file name without file extension. | 

#### Ex. Converting scancode json result to FOSSLight report
```
$ fosslight_convert -p /home/jsonfile_dir
```

## 📁 Result

```
$ tree
.
├── FOSSLight-Report_2021-05-03_00-39-49.csv
├── FOSSLight-Report_2021-05-03_00-39-49.xlsx
├── scancode_2021-05-03_00-39-49.json
└── fosslight_src_log_2021-05-03_00-39-49.txt

```
- FOSSLight-Report_[datetime].xlsx : FOSSLight Source Scanner result in OSS Report format.
- FOSSLight-Report_[datetime].csv : FOSSLight Source Scanner result in csv format. (Except Windows)
- fosslight_src_log_[datetime].txt : The execution log.
- scancode_[datetime].json : The ScanCode result in case of -j option.


## 👏 How to report issue

Please report any ideas or bugs to improve by creating an issue in [Git Repository][repo]. Then there will be quick bug fixes and upgrades. Ideas to improve are always welcome.

[repo]: https://github.com/fosslight/fosslight_source_scanner/issues

## 📄 License

FOSSLight Source Scanner is Apache-2.0, as found in the [LICENSE][l] file.

[l]: https://github.com/fosslight/fosslight_source_scanner/blob/main/LICENSE
