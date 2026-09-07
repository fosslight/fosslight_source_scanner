# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

"""Source-scanner filename excludes (not applied to dependency discovery)."""

from fosslight_util.exclude import is_excluded_filename

# Build/package config noise for license scans.
EXCLUDE_FILENAME_SOURCE = frozenset({
    "changelog", "config.guess", "config.sub", "changes", "ltmain.sh",
    "configure", "configure.ac", "depcomp", "compile", "missing", "makefile",
    "makefile.am",
    "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "gradlew", "gradlew.bat",
    "vite.config.ts", "vite.config.js", "vite.config.mts", "vite.config.mjs",
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml",
})


def is_excluded_source_filename(file_path: str) -> bool:
    return is_excluded_filename(file_path, EXCLUDE_FILENAME_SOURCE)
