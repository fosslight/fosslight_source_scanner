#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import re
import hashlib
import fosslight_util.constant as constant
from fosslight_util.oss_item import FileItem, OssItem, get_checksum_sha1

logger = logging.getLogger(constant.LOGGER_NAME)
replace_word = ["-only", "-old-style", "-or-later", "licenseref-scancode-", "licenseref-"]
_notice_filename = ['licen[cs]e[s]?', 'notice[s]?', 'legal', 'copyright[s]?', 'copying*', 'patent[s]?', 'unlicen[cs]e', 'eula',
                    '[a,l]?gpl[-]?[1-3]?[.,-,_]?[0-1]?', 'mit', 'bsd[-]?[0-4]?', 'bsd[-]?[0-4][-]?clause[s]?',
                    'apache[-,_]?[1-2]?[.,-,_]?[0-2]?']
_manifest_filename = [
    r'.*\.pom$',
    r'package\.json$',
    r'setup\.py$',
    r'setup\.cfg$',
    r'pyproject\.toml$',
    r'.*\.podspec$',
    r'Cargo\.toml$',
    r'huggingface_hub_metadata\.json$',
]
MAX_LICENSE_LENGTH = 200
MAX_LICENSE_TOTAL_LENGTH = 600
SUBSTRING_LICENSE_COMMENT = "Maximum character limit (License)"
DEFAULT_KB_URL = "http://fosslight-kb.lge.com/"


def resolve_kb_config(kb_url: str = "", kb_token: str = "") -> tuple[str, str]:
    url = (kb_url or os.environ.get("KB_URL", DEFAULT_KB_URL)).strip() or DEFAULT_KB_URL

    token = (kb_token or "").strip()
    if not token:
        token = (os.environ.get("KB_TOKEN") or "").strip()

    return f"{url.rstrip('/')}/", token


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
        self.kb_origin_url = ""  # URL from OSS KB
        self.kb_evidence = ""   # Evidence from KB API (exact_match or code snippet)
        self._cached_kb_md5 = ""  # MD5 precomputed for KB lookup (set by _collect_kb_file_hashes)

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

    def _get_hash(self, path_to_scan: str = "") -> tuple:
        wfp = ""
        md5_hex = ""
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
                md5_hex = md5_hash.hexdigest()
                try:
                    from scanoss.winnowing import Winnowing
                    wfp = Winnowing().wfp_for_file(file_path, self.source_name_or_path) or ""
                except Exception as e:
                    logger.debug(f"Failed to get WFP for {self.source_name_or_path}: {e}")
        except FileNotFoundError:
            logger.debug(f"File not found: {self.source_name_or_path}")
        except PermissionError:
            logger.debug(f"Permission denied: {self.source_name_or_path}")
        except Exception as e:
            logger.debug(f"Failed to compute MD5 for {self.source_name_or_path}: {e}")
        return md5_hex, wfp

    def _apply_kb_origin_url(self, origin_url: str) -> tuple[str, str, str]:
        """Apply KB origin URL and return (oss_name, oss_version, download_url)."""
        self.kb_origin_url = origin_url
        self.kb_evidence = "exact_match"
        extracted_name, extracted_version, repo_url = self._extract_oss_info_from_url(origin_url)
        if extracted_name:
            self.oss_name = extracted_name
        if extracted_version:
            self.oss_version = extracted_version
        download_url = repo_url if repo_url else origin_url
        self.download_location = [download_url]
        return self.oss_name, self.oss_version, download_url

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

    def set_oss_item(
        self,
        path_to_scan: str = "",
        kb_origin_urls: dict[str, str] | None = None,
    ) -> None:
        self.oss_items = []
        if self.download_location:
            for url in self.download_location:
                item = OssItem(self.oss_name, self.oss_version, self.licenses, url)
                item.copyright = "\n".join(self.copyright)
                item.comment = self.comment
                self.oss_items.append(item)
        else:
            item = OssItem(self.oss_name, self.oss_version, self.licenses)
            if kb_origin_urls and not self.is_license_text:
                md5_hash = self._cached_kb_md5
                if not md5_hash:
                    md5_hash, _wfp = self._get_hash(path_to_scan)
                if md5_hash:
                    origin_url = kb_origin_urls.get(md5_hash, "")
                    if origin_url:
                        oss_name, oss_version, download_url = self._apply_kb_origin_url(origin_url)
                        item = OssItem(oss_name, oss_version, self.licenses, download_url)

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


def is_notice_file(file_path: str) -> bool:
    pattern = r"({})(?<!w)".format("|".join(_notice_filename))
    filename = os.path.basename(file_path)
    return bool(re.match(pattern, filename, re.IGNORECASE))


def is_manifest_file(file_path: str) -> bool:
    pattern = r"({})$".format("|".join(_manifest_filename))
    filename = os.path.basename(file_path)
    return bool(re.match(pattern, filename, re.IGNORECASE))
