# Copyright (c) 2018 nexB Inc. and others.
# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Vendored from scancode-ignore-binaries (aboutcode-org/scancode-plugins)
# so PyPI installs do not need a GitHub git dependency.
# SPDX-PackageDownloadLocation: https://github.com/aboutcode-org/scancode-plugins/tree/main/misc/scancode-ignore-binaries

from plugincode.pre_scan import PreScanPlugin
from plugincode.pre_scan import pre_scan_impl
from commoncode.cliutils import PluggableCommandLineOption
from commoncode.cliutils import PRE_SCAN_GROUP
from typecode.contenttype import get_type


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

    def process_codebase(self, codebase, ignore_binaries, **kwargs):
        """
        Remove binary Resources from the resource tree.
        """
        if not ignore_binaries:
            return

        resources_to_remove = []
        for resource in codebase.walk():
            if not resource.is_file:
                continue
            if is_binary(resource.location):
                resources_to_remove.append(resource)

        for resource in resources_to_remove:
            resource.remove(codebase)


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
