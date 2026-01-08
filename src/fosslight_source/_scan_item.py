#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import re
import json
import hashlib
import urllib.request
import urllib.error
import fosslight_util.constant as constant
from fosslight_util.oss_item import FileItem, OssItem, get_checksum_sha1

logger = logging.getLogger(constant.LOGGER_NAME)
replace_word = ["-only", "-old-style", "-or-later", "licenseref-scancode-", "licenseref-"]
_notice_filename = ['licen[cs]e[s]?', 'notice[s]?', 'legal', 'copyright[s]?', 'copying*', 'patent[s]?', 'unlicen[cs]e', 'eula',
                    '[a,l]?gpl[-]?[1-3]?[.,-,_]?[0-1]?', 'mit', 'bsd[-]?[0-4]?', 'bsd[-]?[0-4][-]?clause[s]?',
                    'apache[-,_]?[1-2]?[.,-,_]?[0-2]?']
_manifest_filename = [r'.*\.pom$', r'package\.json$', r'setup\.py$', r'pubspec\.yaml$', r'.*\.podspec$', r'Cargo\.toml$']
_exclude_filename = ["changelog", "config.guess", "config.sub", "changes", "ltmain.sh",
                     "configure", "configure.ac", "depcomp", "compile", "missing", "makefile"]
_exclude_extension = [".m4", ".in", ".po"]
_exclude_directory = ["test", "tests", "doc", "docs"]
_exclude_directory = [os.path.sep + dir_name +
                      os.path.sep for dir_name in _exclude_directory]
_exclude_directory.append("/.")
_package_directory = ["node_modules", "venv", "Pods", "Carthage"]
MAX_LICENSE_LENGTH = 200
MAX_LICENSE_TOTAL_LENGTH = 600
SUBSTRING_LICENSE_COMMENT = "Maximum character limit (License)"
KB_URL = "http://fosslight-kb.lge.com/query"


class SourceItem(FileItem):

    def __init__(self, value: str) -> None:
        super().__init__("")
        self.source_name_or_path = value
        self.is_license_text = False
        self.is_manifest_file = False
        self.license_reference = ""
        self.scanoss_reference = {}
        self.matched_lines = ""  # Only for SCANOSS results
        self.fileURL = ""  # Only for SCANOSS results
        self.download_location = []
        self.copyright = []
        self._licenses = []
        self.oss_name = ""
        self.oss_version = ""

        self.checksum = get_checksum_sha1(value)

    def __del__(self) -> None:
        pass

    def __hash__(self) -> int:
        return hash(self.file)

    @property
    def licenses(self) -> list:
        return self._licenses

    @licenses.setter
    def licenses(self, value: list) -> None:
        if value:
            max_length_exceed = False
            for new_lic in value:
                if new_lic:
                    if len(new_lic) > MAX_LICENSE_LENGTH:
                        new_lic = new_lic[:MAX_LICENSE_LENGTH]
                        max_length_exceed = True
                    if new_lic not in self._licenses:
                        self._licenses.append(new_lic)
                        if len(",".join(self._licenses)) > MAX_LICENSE_TOTAL_LENGTH:
                            self._licenses.remove(new_lic)
                            max_length_exceed = True
                            break
            if max_length_exceed and (SUBSTRING_LICENSE_COMMENT not in self.comment):
                self.comment = f"{self.comment}/ {SUBSTRING_LICENSE_COMMENT}" if self.comment else SUBSTRING_LICENSE_COMMENT
        else:
            self._licenses = value

    def _get_md5_hash(self, path_to_scan: str = "") -> str:
        try:
            file_path = self.source_name_or_path
            if path_to_scan and not os.path.isabs(file_path):
                file_path = os.path.join(path_to_scan, file_path)
            file_path = os.path.normpath(file_path)

            if os.path.isfile(file_path):
                md5_hash = hashlib.md5()
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5_hash.update(chunk)
                return md5_hash.hexdigest()
        except FileNotFoundError:
            logger.warning(f"File not found: {self.source_name_or_path}")
        except PermissionError:
            logger.warning(f"Permission denied: {self.source_name_or_path}")
        except Exception as e:
            logger.warning(f"Failed to compute MD5 for {self.source_name_or_path}: {e}")
        return ""

    def _get_origin_url_from_md5_hash(self, md5_hash: str) -> str:
        try:
            request = urllib.request.Request(KB_URL, data=json.dumps({"file_hash": md5_hash}).encode('utf-8'), method='POST')
            request.add_header('Accept', 'application/json')
            request.add_header('Content-Type', 'application/json')

            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode())
                if isinstance(data, dict):
                    # Only extract output if return_code is 0 (success)
                    return_code = data.get('return_code', -1)
                    if return_code == 0:
                        output = data.get('output', '')
                        if output:
                            return output
        except urllib.error.URLError as e:
            logger.warning(f"Failed to fetch origin_url from API for MD5 hash {md5_hash}: {e}")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse API response for MD5 hash {md5_hash}: {e}")
        except Exception as e:
            logger.warning(f"Error getting origin_url for MD5 hash {md5_hash}: {e}")
        return ""

    def _extract_oss_info_from_url(self, url: str) -> tuple:
        """
        Extract OSS name, version, and repository URL from GitHub URL.

        Supported patterns:
        - https://github.com/{owner}/{repo}/archive/{version}.zip
        - https://github.com/{owner}/{repo}/archive/{tag}/{version}.zip
        - https://github.com/{owner}/{repo}/releases/download/{version}/{filename}

        :param url: GitHub URL to extract information from
        :return: tuple of (repo_name, version, repo_url)
        """
        try:
            repo_match = re.search(r'github\.com/([^/]+)/([^/]+)/', url)
            if not repo_match:
                return "", "", ""

            owner = repo_match.group(1)
            repo_name = repo_match.group(2)
            repo_url = f"https://github.com/{owner}/{repo_name}"
            version = ""
            # Extract version from releases pattern first: /releases/download/{version}/
            releases_match = re.search(r'/releases/download/([^/]+)/', url)
            if releases_match:
                version = releases_match.group(1)
            else:
                # Extract version from archive pattern: /archive/{version}.zip or /archive/{tag}/{version}.zip
                # For pattern with tag, take the last segment before .zip
                archive_match = re.search(r'/archive/(.+?)(?:\.zip|\.tar\.gz)?(?:[?#]|$)', url)
                if archive_match:
                    version_path = archive_match.group(1)
                    version = version_path.split('/')[-1] if '/' in version_path else version_path
            if re.match(r'^[0-9a-f]{7,40}$', version, re.IGNORECASE):
                version = ""
            return repo_name, version, repo_url
        except Exception as e:
            logger.debug(f"Failed to extract OSS info from URL {url}: {e}")
            return "", "", ""

    def set_oss_item(self, path_to_scan: str = "", run_kb: bool = False) -> None:
        self.oss_items = []
        if self.download_location:
            for url in self.download_location:
                item = OssItem(self.oss_name, self.oss_version, self.licenses, url)
                item.copyright = "\n".join(self.copyright)
                item.comment = self.comment
                self.oss_items.append(item)
        else:
            item = OssItem(self.oss_name, self.oss_version, self.licenses)
            if run_kb and not self.is_license_text:
                md5_hash = self._get_md5_hash(path_to_scan)
                if md5_hash:
                    origin_url = self._get_origin_url_from_md5_hash(md5_hash)
                    if origin_url:
                        extracted_name, extracted_version, repo_url = self._extract_oss_info_from_url(origin_url)
                        if extracted_name:
                            self.oss_name = extracted_name
                        if extracted_version:
                            self.oss_version = extracted_version
                        download_url = repo_url if repo_url else origin_url
                        self.download_location = [download_url]
                        item = OssItem(self.oss_name, self.oss_version, self.licenses, download_url)

            item.copyright = "\n".join(self.copyright)
            item.comment = self.comment
            self.oss_items.append(item)

    def get_print_array(self) -> list:
        print_rows = []
        for item in self.oss_items:
            print_rows.append([self.source_name_or_path, item.name, item.version, ",".join(item.license),
                               item.download_location, "",
                               item.copyright, "Exclude" if self.exclude else "", item.comment,
                               self.license_reference])
        return print_rows

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.source_name_or_path == other
        else:
            return self.source_name_or_path == other.source_name_or_path


def is_exclude_dir(dir_path: str) -> bool:
    if dir_path:
        dir_path = dir_path.lower()
        dir_path = dir_path if dir_path.endswith(
            os.path.sep) else dir_path + os.path.sep
        dir_path = dir_path if dir_path.startswith(
            os.path.sep) else os.path.sep + dir_path
        return any(dir_name in dir_path for dir_name in _exclude_directory)
    return False


def is_exclude_file(file_path: str, prev_dir: str = None, prev_dir_exclude_value: bool = None) -> bool:
    file_path = file_path.lower()
    filename = os.path.basename(file_path)
    if os.path.splitext(filename)[1] in _exclude_extension:
        return True
    if filename.startswith('.') or filename in _exclude_filename:
        return True

    dir_path = os.path.dirname(file_path)
    if prev_dir is not None:  # running ScanCode
        if dir_path == prev_dir:
            return prev_dir_exclude_value
        else:
            # There will be no execution of this else statement.
            # Because scancode json output results are sorted by path,
            # most of them will match the previous if statement.
            return is_exclude_dir(dir_path)
    else:  # running SCANOSS
        return is_exclude_dir(dir_path)
    return False


def is_notice_file(file_path: str) -> bool:
    pattern = r"({})(?<!w)".format("|".join(_notice_filename))
    filename = os.path.basename(file_path)
    return bool(re.match(pattern, filename, re.IGNORECASE))


def is_manifest_file(file_path: str) -> bool:
    pattern = r"({})$".format("|".join(_manifest_filename))
    filename = os.path.basename(file_path)
    return bool(re.match(pattern, filename, re.IGNORECASE))


def is_package_dir(dir_path: str) -> bool:
    # scancode and scanoss use '/' as path separator regardless of OS
    dir_path = dir_path.replace('\\', '/')
    path_parts = dir_path.split('/')

    for pkg_dir in _package_directory:
        if pkg_dir in path_parts:
            pkg_index = path_parts.index(pkg_dir)
            pkg_path = '/'.join(path_parts[:pkg_index + 1])
            return True, pkg_path
    return False, ""


def _has_parent_in_exclude_list(rel_path: str, path_to_exclude: list) -> bool:
    path_parts = rel_path.replace('\\', '/').split('/')
    for i in range(1, len(path_parts)):
        parent_path = '/'.join(path_parts[:i])
        if parent_path in path_to_exclude:
            return True
    return False


def get_excluded_paths(path_to_scan: str, custom_excluded_paths: list = []) -> list:
    path_to_exclude = custom_excluded_paths.copy()
    abs_path_to_scan = os.path.abspath(path_to_scan)

    for root, dirs, files in os.walk(path_to_scan):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            rel_path = os.path.relpath(dir_path, abs_path_to_scan)
            if not _has_parent_in_exclude_list(rel_path, path_to_exclude):
                if dir_name in _package_directory:
                    path_to_exclude.append(rel_path)
                elif is_exclude_dir(rel_path):
                    path_to_exclude.append(rel_path)

    return path_to_exclude
