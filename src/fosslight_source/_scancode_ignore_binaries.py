# Copyright (c) 2018 nexB Inc. and others.
# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Vendored from scancode-ignore-binaries (aboutcode-org/scancode-plugins)
# so PyPI installs do not need a GitHub git dependency.
# SPDX-PackageDownloadLocation: https://github.com/aboutcode-org/scancode-plugins/tree/main/misc/scancode-ignore-binaries

import logging
import multiprocessing

from plugincode.pre_scan import PreScanPlugin
from plugincode.pre_scan import pre_scan_impl
from commoncode.cliutils import PluggableCommandLineOption
from commoncode.cliutils import PRE_SCAN_GROUP
from typecode.contenttype import get_type

logger = logging.getLogger(__name__)

# Detection costs one get_type() call per file, which reads from disk. On large
# trees that dominates the pre-scan stage, so spread it over the scan processes.
PARALLEL_MIN_FILES = 2000
CHUNK_SIZE = 256


@pre_scan_impl
class IgnoreBinaries(PreScanPlugin):
    """
    Ignore binary files.
    """

    options = [
        PluggableCommandLineOption(
            ('--ignore-binaries',),
            is_flag=True,
            help='Ignore binary files.',
            sort_order=10,
            help_group=PRE_SCAN_GROUP,
        )
    ]

    def is_enabled(self, ignore_binaries, **kwargs):
        return ignore_binaries

    def process_codebase(self, codebase, ignore_binaries, processes=1, **kwargs):
        """
        Remove binary Resources from the resource tree.
        """
        if not ignore_binaries:
            return

        # Collect first: removing while walking would invalidate the walk.
        candidates = [
            (resource.path, resource.location)
            for resource in codebase.walk()
            if resource.is_file
        ]
        if not candidates:
            return

        locations = [location for _path, location in candidates]
        flags = _detect_binaries(locations, processes)

        for (path, _location), binary in zip(candidates, flags):
            if not binary:
                continue
            resource = codebase.get_resource(path)
            if resource is not None:
                resource.remove(codebase)


def _detect_binaries(locations, processes):
    """
    Return a list of booleans, one per location, telling whether it is binary.
    """
    if processes and processes > 1 and len(locations) >= PARALLEL_MIN_FILES:
        try:
            pool = multiprocessing.Pool(processes)
        except Exception as ex:
            logger.debug(f"Parallel binary detection unavailable, using one process: {ex}")
        else:
            with pool:
                return pool.map(is_binary, locations, chunksize=CHUNK_SIZE)

    return [is_binary(location) for location in locations]


def is_binary(location):
    """
    Return True if the resource at location is a binary file.
    """
    t = get_type(location)
    return (
        t.is_binary
        or t.is_archive
        or t.is_media
        or t.is_office_doc
        or t.is_compressed
        or t.is_filesystem
        or t.is_winexe
        or t.is_elf
        or t.is_java_class
        or t.is_data
    )
