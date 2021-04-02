# Environment setting guide

Guides how to set up virtualenv environment to run Python Package. <br>
Introducing Anaconda (or miniconda) that can install Python + virtualenv environment at once.

## Contents

- [Set up virtualenv](#virtualenv)
- [Set up Python and Virtualenv at once](#setup)
- [How to install Anaconda](#howto)
- [Note](#note)


## 📋 <a name="virtualenv"></a>Create and activate virtualenv

See the [Python virtaulenv page][venv] for details.
```
$ pip3 install virtualenv
$ virtualenv -p /usr/bin/python3.6 venv
$ source venv/bin/activate
```

[venv]: https://docs.python.org/3.6/library/venv.html

## 🚀 <a name="setup"></a>How to set up Python and Virtualenv at once : Anaconda | Miniconda

With [Anaconda][anaconda], you can activate the virtualenv environment with various Python versions.
Anaconda is a tool that makes it easy to manage and configure library packages for Python or R programs.

[anaconda]: https://www.anaconda.com/products/individual


### <a name="howto"></a>How to set up python 3.6 environment with Ananconda     
1. Install anaconda
```
$ wget https://repo.anaconda.com/archive/Anaconda3-2020.07-Linux-x86_64.sh 
$ bash Anaconda3-2020.07-Linux-x86_64.sh
$ source  ~/anaconda3/etc/profile.d/conda.sh
```
2. Create the python 3.6 environment. <br>
ex) py36: virtual environment name, python=3.6 : Python version to use
```
$ conda create --name py36 python=3.6
```
3. Activate python environment.
```
$ conda activate py36
```
4. Turn off the activation of the python environment setting called base automatically when connecting to the shell.
(To ensure that the existing Python version is not changed.)
```
$ conda config --set auto_activate_base false
```
## 📄 <a name="note"></a>Note

### About Miniconda
If you don't need the Python package that is additionally installed when installing Anaconda, you can use [Miniconda][mini], a minimal installer for conda. 

[mini]: https://docs.conda.io/en/latest/miniconda.html

### Difference between virtualenv and conda commands

| Command description  | virtualenv | conda |
| ------------- | ------------- | ------------- |
| Create a virtual environment. | virtualenv -p [python_version] [env_name] | conda create --name [env_name] python=[python_version] | 
| Activate a virtual environment. | source [env_name]/bin/activate |conda activate [env_name]
| Deactivate a virtual environment | deactivate | conda deactivate | 