#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics
# SPDX-License-Identifier: Apache-2.0
from codecs import open
from setuptools import setup, find_packages

with open('README.md', 'r', 'utf-8') as f:
    readme = f.read()

with open('requirements.txt', 'r', 'utf-8') as f:
    required = f.read().splitlines()

if __name__ == "__main__":
    setup(
        name='fosslight_source',
        version='1.4.0',
        package_dir={"": "src"},
        packages=find_packages(where='src'),
        description='FOSSLight Source',
        long_description=readme,
        long_description_content_type='text/markdown',
        license='Apache-2.0',
        author='LG Electronics',
        url='https://github.com/fosslight/fosslight_source',
        download_url='https://github.com/fosslight/fosslight_source',
        classifiers=['Programming Language :: Python :: 3.6',
                     'License :: OSI Approved :: Apache Software License'],
        install_requires=required,
        entry_points={
            "console_scripts": [
                "fosslight_convert = fosslight_source.convert_scancode:main",
                "fosslight_source = fosslight_source.run_scancode:main",
                "convert_scancode = fosslight_source.convert_scancode:main",
                "run_scancode = fosslight_source.run_scancode:main"
            ]
        }
    )
