# Virtualenv setting guide

Guides how to set up virtualenv environment to run Python Package.

## Contents
- [How to install Python](#python)
- [Set up virtualenv](#virtualenv)
- [Virtualenv command](#command)

## 💻 <a name="python"></a>How to install Python

- Refer to the [Installation Guide][install] for how to install Python.

[install]: https://realpython.com/installing-python

## 📋 <a name="virtualenv"></a>Create and activate virtualenv

See the [Python virtaulenv page][venv] for details.
```
$ pip3 install virtualenv
$ virtualenv -p /usr/bin/python3.6 venv
$ source venv/bin/activate
```

[venv]: https://docs.python.org/3.6/library/venv.html

## ⌨️ <a name="command"></a>Virtualenv commands

| Command description  | command |
| ------------- | ------------- |
| Create a virtual environment. | virtualenv -p [python_version] [env_name] |
| Activate a virtual environment. | source [env_name]/bin/activate |
| Deactivate a virtual environment | deactivate | conda deactivate |