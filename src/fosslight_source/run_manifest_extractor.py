#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import json
import re
import logging
from fosslight_util.get_pom_license import get_license_from_pom
import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)


def _split_spdx_expression(value: str) -> list[str]:
    parts = re.split(r'\s+(?:OR|AND)\s+|[|]{2}|&&', value, flags=re.IGNORECASE)
    tokens: list[str] = []
    for part in parts:
        token = part.strip().strip('()')
        if token:
            tokens.append(token)
    # de-dup preserve order
    unique: list[str] = []
    for t in tokens:
        if t not in unique:
            unique.append(t)
    return unique


def get_licenses_from_package_json(file_path: str) -> list[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as ex:
        logger.info(f"Failed to read package.json {file_path}: {ex}")
        return []

    if not isinstance(data, dict):
        return []

    licenses: list[str] = []
    license_field = data.get('license')

    if isinstance(license_field, str):
        value = license_field.strip()
        if value.upper() == 'UNLICENSED':
            return []
        if value.upper().startswith('SEE LICENSE IN'):
            # e.g. "SEE LICENSE IN LICENSE" - we do not attempt to read the file here
            return []
        licenses.extend(_split_spdx_expression(value))
    elif isinstance(license_field, dict):
        type_val = license_field.get('type')
        if isinstance(type_val, str):
            type_val = type_val.strip()
            if type_val and type_val.upper() != 'UNLICENSED':
                licenses.append(type_val)

    # Legacy "licenses": [...]
    if not licenses:
        legacy = data.get('licenses')
        if isinstance(legacy, list):
            for item in legacy:
                if isinstance(item, str):
                    token = item.strip()
                    if token and token.upper() != 'UNLICENSED':
                        licenses.append(token)
                elif isinstance(item, dict):
                    t = item.get('type')
                    if isinstance(t, str):
                        t = t.strip()
                        if t and t.upper() != 'UNLICENSED':
                            licenses.append(t)

    # De-duplicate while preserving order
    unique: list[str] = []
    for lic in licenses:
        if lic not in unique:
            unique.append(lic)
    return unique


def get_licenses_from_setup_cfg(file_path: str) -> list[str]:
    try:
        import configparser
        parser = configparser.ConfigParser()
        # Preserve case for values; option names are case-insensitive
        parser.read(file_path, encoding='utf-8')
    except Exception as ex:
        logger.info(f"Failed to read setup.cfg {file_path}: {ex}")
        return []

    if not parser.has_section('metadata'):
        return []

    license_value = parser.get('metadata', 'license', fallback='').strip()
    if not license_value:
        return []

    # Follow SPDX expression style per PyPA guidance (PEP 639)
    return _split_spdx_expression(license_value)


def get_licenses_from_setup_py(file_path: str) -> list[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as ex:
        logger.info(f"Failed to read setup.py {file_path}: {ex}")
        return []

    # Simple heuristic: look for license="...", license='...', or triple-quoted strings.
    match = re.search(r'license\s*=\s*([\'"]{1,3})(.+?)\1', content, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return []
    value = match.group(2).strip()
    if not value:
        return []

    # Split SPDX-like expressions; preserve WITH exceptions.
    return _split_spdx_expression(value)


def get_manifest_licenses(file_path: str) -> list[str]:
    if file_path.endswith('.pom'):
        try:
            pom_licenses = get_license_from_pom(group_id='', artifact_id='', version='', pom_path=file_path, check_parent=True)
            if not pom_licenses:
                return []
            return [x.strip() for x in pom_licenses.split(', ') if x.strip()]
        except Exception as ex:
            logger.info(f"Failed to extract license from POM {file_path}: {ex}")
            return []
    elif os.path.basename(file_path).lower() == 'package.json':
        try:
            return get_licenses_from_package_json(file_path)
        except Exception as ex:
            logger.info(f"Failed to extract license from package.json {file_path}: {ex}")
            return []
    elif os.path.basename(file_path).lower() == 'setup.cfg':
        try:
            return get_licenses_from_setup_cfg(file_path)
        except Exception as ex:
            logger.info(f"Failed to extract license from setup.cfg {file_path}: {ex}")
            return []
    elif os.path.basename(file_path).lower() == 'setup.py':
        try:
            return get_licenses_from_setup_py(file_path)
        except Exception as ex:
            logger.info(f"Failed to extract license from setup.py {file_path}: {ex}")
            return []
