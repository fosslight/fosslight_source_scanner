# Virtualenv 세팅 가이드

Python package를 설치 및 실행하기 위한 virtualenv 환경 세팅하는 가이드입니다.

## Contents
- [Python 설치 방법](#python)
- [virtualenv 세팅하는 법](#virtualenv)
- [virtualenv 명령어](#command)

## 💻 <a name="python"></a>Python 설치 방법

- Python 설치 방법은 [설치 가이드][install] 링크를 참조하세요

[install]: https://realpython.com/installing-python

## 📋 <a name="virtualenv"></a>virtualenv 생성하고 활성화하는 법

```
$ pip3 install virtualenv
$ virtualenv -p /usr/bin/python3.6 venv
$ source venv/bin/activate
```
자세한 virtualenv 설명: [Python virtaulenv page][venv]

[venv]: https://docs.python.org/3.6/library/venv.html

## ⌨️ <a name="command"></a>virtualenv 명령어

| Command description  | command |
| ------------- | ------------- |
| 가상환경 생성 | virtualenv -p [python_version] [env_name] |
| 가상환경 활성화 | source [env_name]/bin/activate |
| 가상환경 비활성화 | deactivate |