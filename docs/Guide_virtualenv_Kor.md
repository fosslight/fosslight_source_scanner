# 환경 세팅 가이드

Python package를 실행하기 위한 virtualenv 환경 세팅하는 가이드입니다. <br>
Anaconda (또는 miniconda) 를 통해 Python + virtualenv 환경을 한번에 세팅하는 방법을 소개합니다.

## Contents

- [virtualenv 세팅하는 법](#virtualenv)
- [Python + Virtualenv 한번에 설치하는 법](#setup)
- [Anaconda 설치 방법](#howto)
- [참고 사항](#note)


## 📋 <a name="virtualenv"></a>virtualenv 생성하고 활성화하는 법

```
$ pip3 install virtualenv
$ virtualenv -p /usr/bin/python3.6 venv
$ source venv/bin/activate
```
자세한 virtualenv 설명: [Python virtaulenv page][venv]

[venv]: https://docs.python.org/3.6/library/venv.html

## 🚀 <a name="setup"></a>Python과 Virtualenv를 한번에 설치 : Anaconda | Miniconda

[Anaconda][anaconda]를 이용하면 다양한 Python 버전으로 virtualenv 환경을 활성화할 수 있습니다.

[anaconda]: https://www.anaconda.com/products/individual


### <a name="howto"></a>Anaconda 이용하여 python 3.6 environment 세팅하는 법
1. Anaconda 설치
```
$ wget https://repo.anaconda.com/archive/Anaconda3-2020.07-Linux-x86_64.sh 
$ bash Anaconda3-2020.07-Linux-x86_64.sh
$ source  ~/anaconda3/etc/profile.d/conda.sh
```
2. python 3.6 환경 생성 <br>
ex) py36: virtual environment name, python=3.6 : Python version to use
```
$ conda create --name py36 python=3.6
```
3. python 3.6 환경 활성화
```
$ conda activate py36
```
4. Shell 연결하면 자동으로 활성화하는 옵션 끄기
```
$ conda config --set auto_activate_base false
```
## 📄 <a name="note"></a>Note

### Miniconda에 대하여

Anaconda 설치시 추가로 설치되는 Python package가 불필요한 경우, Anaconda 대신 conda를 위한 최소한의 installer인 [Miniconda][mini]를 활용할 수 있습니다. 

[mini]: https://docs.conda.io/en/latest/miniconda.html

### virtualenv 와 conda 명령어 차이

| Command description  | virtualenv | conda |
| ------------- | ------------- | ------------- |
| 가상환경 생성 | virtualenv -p [python_version] [env_name] | conda create --name [env_name] python=[python_version] | 
| 가상환경 활성화 | source [env_name]/bin/activate |conda activate [env_name]
| 가상환경 비활성화 | deactivate | conda deactivate | 