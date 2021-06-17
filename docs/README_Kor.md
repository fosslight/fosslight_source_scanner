<p align='right'>
  <a href="https://github.com/fosslight/fosslight_source_scanner/blob/main/README.md">
    [English]
 </a>
</p>

# FOSSLight Source Scanner

<img src="https://img.shields.io/pypi/l/fosslight_source" alt="FOSSLight Source is released under the Apache-2.0 License." /> <img src="https://img.shields.io/pypi/v/fosslight_source" alt="Current python package version." /> <img src="https://img.shields.io/pypi/pyversions/fosslight_source" /> [![REUSE status](https://api.reuse.software/badge/github.com/fosslight/fosslight_source_scanner)](https://api.reuse.software/info/github.com/fosslight/fosslight_source_scanner)
</p>

```note
Source Code의 License를 검출합니다
Source Code 스캐너를 이용하고 결과를 가공합니다
```

**FOSSLight Source Scanner** 소스 코드 스캐너인 [ScanCode][sc]를 이용하여, 파일 안에 포함된 Copyright과 License 문구를 검출합니다. Build Script, Binary, Directory, 특정 Directory (ex-test) 안의 파일을 제외시킵니다. 그리고 License 이름에서 "-only", "-old-style"와 같은 문구를 제거합니다. 결과는 Excel 형태로 출력됩니다.

[sc]: https://github.com/nexB/scancode-toolkit

## Contents

- [Prerequisite](#-prerequisite)
- [How to install](#-how-to-install)
- [How to run](#-how-to-run)
- [Result](#-result)
- [How to report issue](#-how-to-report-issue)
- [License](#-license)


## 📋 Prerequisite

FOSSLight Source Scanner는 Python 3.6+ 기반에서 동작합니다..    
Windows의 경우 [Microsoft Visual C++ Build Tools][ms_build]를 추가로 설치해야 합니다.

[ms_build]: https://visualstudio.microsoft.com/vs/older-downloads/

## 🎉 How to install

FOSSLight Source Scanner는 pip3를 이용하여 설치할 수 있습니다. [python 3.6 + virtualenv](Guide_virtualenv_Kor.md) 환경에서 설치할 것을 권장합니다.

```
$ pip3 install fosslight_source
```

## 🚀 How to run

FOSSLight Source Scanner에는 하기 두 가지 명령어가 있습니다. 

### 1. fosslight_source     
Source Code 분석을 실행한 후 FOSSLight Report 형식으로 출력합니다.

| Parameter  | Argument | Description |
| ------------- | ------------- | ------------- |
| h | None | Print help message. | 
| p | String | Path to analyze source. | 
| j | None | As an output, the result of executing ScanCode in json format other than FOSSLight Report is additionally generated. | 
| o | String | Output file name without file extension. | 

#### Ex. Source Code 분석 후 FOSSLight Report와 json 형태의 ScanCode 결과 출력
```
$ fosslight_source -p /home/source_path -j
```
### 2. fosslight_convert     
json형태인 ScanCode 결과를 FOSSLight Report 형식으로 변환합니다.

| Parameter  | Argument | Description |
| ------------- | ------------- | ------------- |
| h | None | Print help message. | 
| p | String | Path of ScanCode json files. | 
| o | String | Output file name without file extension. | 

#### Ex. json 형태의 ScanCode 결과를 FOSSLight Report 형식으로 변환
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
- FOSSLight-Report_[datetime].xlsx : FOSSLight Report형태의 Source Code 분석 결과
- FOSSLight-Report_[datetime].csv : FOSSLight Report를 csv로 출력한 결과 (Windows 제외)
- fosslight_src_log_[datetime].txt: 실행 로그가 저장된 파일
- scancode_[datetime].json : ScanCode 실행 결과 (fosslight_source명령어에 -j 옵션이 포함된 경우에만 생성)


## 👏 How to report issue

개선 사항이나 버그는 [Git Repository][repo]에 이슈를 생성하여 리포트해주시기 바랍니다. 이슈 리포트는 FOSSLight Source Scanner 업그레이드에 많은 도움이 됩니다.

[repo]: https://github.com/fosslight/fosslight_source_scanner/issues

## 📄 License

FOSSLight Source Scanner는 Apache-2.0입니다. License 원문 파일 [LICENSE][l]를 참고하십시오.

[l]: https://github.com/fosslight/fosslight_source_scanner/blob/main/LICENSE
