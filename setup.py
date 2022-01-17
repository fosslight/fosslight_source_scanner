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
        version='1.6.6',
        package_dir={"": "src"},
        packages=find_packages(where='src'),
        description='FOSSLight Source Scanner',
        long_description=readme,
        long_description_content_type='text/markdown',
        license='Apache-2.0',
        author='LG Electronics',
        url='https://github.com/fosslight/fosslight_source_scanner',
        download_url='https://github.com/fosslight/fosslight_source_scanner',
        classifiers=['License :: OSI Approved :: Apache Software License',
                     "Programming Language :: Python :: 3",
                     "Programming Language :: Python :: 3.6",
                     "Programming Language :: Python :: 3.7",
                     "Programming Language :: Python :: 3.8",
                     "Programming Language :: Python :: 3.9", ],
        install_requires=required,
        extras_require={":python_version>'3.6'": ["scanoss>=0.7.0"]},
        entry_points={
            "console_scripts": [
                "fosslight_convert = fosslight_source.convert_scancode:main",
                "fosslight_source = fosslight_source.cli:main",
                "convert_scancode = fosslight_source.convert_scancode:main",
                "run_scancode = fosslight_source.run_scancode:main"
            ]
        }
    )
