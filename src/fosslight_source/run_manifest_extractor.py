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
        if value.upper().startswith('SEE LICENSE IN'):
            return []
        licenses.extend(_split_spdx_expression(value))
    elif isinstance(license_field, dict):
        type_val = license_field.get('type')
        if isinstance(type_val, str):
            type_val = type_val.strip()
            if type_val:
                licenses.append(type_val)

    if not licenses:
        legacy = data.get('licenses')
        if isinstance(legacy, list):
            for item in legacy:
                if isinstance(item, str):
                    token = item.strip()
                    if token:
                        licenses.append(token)
                elif isinstance(item, dict):
                    t = item.get('type')
                    if isinstance(t, str):
                        t = t.strip()
                        if t:
                            licenses.append(t)

    unique: list[str] = []
    for lic in licenses:
        if lic not in unique:
            unique.append(lic)
    return unique


def get_licenses_from_setup_cfg(file_path: str) -> list[str]:
    try:
        import configparser
        parser = configparser.ConfigParser()
        parser.read(file_path, encoding='utf-8')
        if parser.has_section('metadata'):
            license_value = parser.get('metadata', 'license', fallback='').strip()
            if license_value:
                return _split_spdx_expression(license_value)
    except Exception as ex:
        logger.info(f"Failed to parse setup.cfg with configparser for {file_path}: {ex}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        meta_match = re.search(r'^\s*\[metadata\]\s*(.*?)(?=^\s*\[|\Z)', content, flags=re.MULTILINE | re.DOTALL)
        if not meta_match:
            return []
        block = meta_match.group(1)
        m = re.search(r'^\s*license\s*=\s*(.+)$', block, flags=re.MULTILINE)
        if not m:
            return []
        val = m.group(1).strip()
        if (len(val) >= 2) and ((val[0] == val[-1]) and val[0] in ('"', "'")):
            val = val[1:-1].strip()
        if not val:
            return []
        return _split_spdx_expression(val)
    except Exception as ex:
        logger.info(f"Failed to parse setup.cfg {file_path} via regex fallback: {ex}")
        return []


def get_licenses_from_setup_py(file_path: str) -> list[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as ex:
        logger.info(f"Failed to read setup.py {file_path}: {ex}")
        return []

    match = re.search(r'license\s*=\s*([\'"]{1,3})(.+?)\1', content, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return []
    value = match.group(2).strip()
    if not value:
        return []

    return _split_spdx_expression(value)


def get_licenses_from_podspec(file_path: str) -> list[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as ex:
        logger.info(f"Failed to read podspec {file_path}: {ex}")
        return []

    m = re.search(r'\blicense\s*=\s*([\'"])(.+?)\1', content, flags=re.IGNORECASE)
    if m:
        value = m.group(2).strip()
        if value:
            return _split_spdx_expression(value)

    m = re.search(r'\blicense\s*=\s*\{[^}]*?:type\s*=>\s*([\'"])(.+?)\1', content, flags=re.IGNORECASE | re.DOTALL)
    if m:
        value = m.group(2).strip()
        if value:
            return _split_spdx_expression(value)

    m = re.search(r'\blicense\s*=\s*\{[^}]*?:type\s*=>\s*:(\w+)', content, flags=re.IGNORECASE | re.DOTALL)
    if m:
        value = m.group(1).strip()
        if value:
            return _split_spdx_expression(value)

    m = re.search(r'\blicense\s*=\s*:(\w+)', content, flags=re.DOTALL | re.IGNORECASE)
    if m:
        value = m.group(1).strip()
        if value:
            return _split_spdx_expression(value)

    return []


def get_licenses_from_cargo_toml(file_path: str) -> list[str]:
    try:
        data = None
        try:
            import tomllib as toml_loader  # Python 3.11+
            with open(file_path, 'rb') as f:
                data = toml_loader.load(f)
        except Exception:
            try:
                import tomli as toml_loader  # Backport
                with open(file_path, 'rb') as f:
                    data = toml_loader.load(f)
            except Exception:
                data = None

        if isinstance(data, dict):
            package_tbl = data.get('package') or {}
            license_value = package_tbl.get('license')
            if isinstance(license_value, str) and license_value.strip():
                return _split_spdx_expression(license_value.strip())
            if package_tbl.get('license-file'):
                return []
    except Exception as ex:
        logger.info(f"Failed to parse Cargo.toml via toml parser for {file_path}: {ex}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pkg_match = re.search(r'^\s*\[package\]\s*(.*?)(?=^\s*\[|\Z)', content, flags=re.MULTILINE | re.DOTALL)
        if not pkg_match:
            return []
        block = pkg_match.group(1)
        m = re.search(r'^\s*license\s*=\s*(?P<q>"""|\'\'\'|"|\')(?P<val>.*?)(?P=q)', block, flags=re.MULTILINE | re.DOTALL)
        if m:
            val = m.group('val').strip()
            if val:
                return _split_spdx_expression(val)
        m2 = re.search(r'^\s*license-file\s*=\s*(?:"""|\'\'\'|"|\')(.*?)(?:"""|\'\'\'|"|\')', block,
                       flags=re.MULTILINE | re.DOTALL)
        if m2:
            return []
    except Exception as ex:
        logger.info(f"Failed to parse Cargo.toml {file_path}: {ex}")
        return []
    return []


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
    elif os.path.basename(file_path).lower().endswith('.podspec'):
        try:
            return get_licenses_from_podspec(file_path)
        except Exception as ex:
            logger.info(f"Failed to extract license from podspec {file_path}: {ex}")
            return []
    elif os.path.basename(file_path).lower() == 'cargo.toml':
        try:
            return get_licenses_from_cargo_toml(file_path)
        except Exception as ex:
            logger.info(f"Failed to extract license from Cargo.toml {file_path}: {ex}")
            return []
