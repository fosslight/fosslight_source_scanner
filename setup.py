#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LicenseRef-LGE-Proprietary
from codecs import open
from setuptools import setup, find_packages

with open('README.md', 'r', 'utf-8') as f:
    readme = f.read()


if __name__ == "__main__":
    setup(
        name             = 'fosslight_source',
        version          = '1.0',
        packages         = find_packages(),
        description      = 'Scancode analysis in OSS Report format',
        long_description = readme,
        long_description_content_type = 'text/markdown',
        license          = 'LGE-Proprietary',
        author           = 'Soim Kim',
        author_email     = 'soim.kim@lge.com',
        url              = 'http://mod.lge.com/code/projects/OSC/repos/fosslight_source',
        download_url     = 'http://mod.lge.com/code/rest/archive/latest/projects/OSC/repos/fosslight_source/archive?format=zip',
        classifiers      = ['Programming Language :: Python :: 3.6',
                        'License :: OSI Approved :: Closed Sorce Software'],
        install_requires = [
            'scancode-toolkit==3.2.0',
            'XlsxWriter'
        ],
        entry_points = {
            "console_scripts": [
                "fosslight_convert = fosslight_source.convert_scancode:main",
                "fosslight_source = fosslight_source.run_scancode:main",
                "convert_scancode = fosslight_source.convert_scancode:main",
                "run_scancode = fosslight_source.run_scancode:main"
                ]
            }
    )