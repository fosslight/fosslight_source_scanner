# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

"""Opt-in, allowlisted evidence for cross-platform result comparisons."""

import hashlib
import json
import logging
import os
import platform
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)
ENV_NAME = "FOSSLIGHT_SOURCE_DIAGNOSTICS"
_PACKAGES = (
    "fosslight_source", "fosslight_util", "scancode-toolkit", "scanoss",
    "click", "pluggy", "XlsxWriter", "PyYAML", "lxml", "truststore",
    "fingerprints", "normality", "setuptools", "pyparsing", "wheel",
    "intbitset", "cryptography", "psycopg2-binary", "tomli", "tqdm", "requests", "urllib3",
)


def enabled() -> bool:
    return os.environ.get(ENV_NAME) == "1"


def record(event: str, **fields) -> None:
    if enabled():
        logger.debug("[DIAGNOSTIC] %s", json.dumps(
            {"schema": 1, "event": event, **fields}, ensure_ascii=True, sort_keys=True,
        ))


@contextmanager
def timing(stage: str) -> Iterator[None]:
    started = time.perf_counter()
    try:
        yield
    finally:
        seconds = time.perf_counter() - started
        logger.debug("[TIMING] %s: %.4fs", stage, seconds)
        record("timing", stage=stage, seconds=seconds)


def text_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="surrogatepass")).hexdigest()


def safe_url(value: str) -> str:
    try:
        parts = urlsplit(value)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            return "<non-http-url>" if value else ""
        return urlunsplit((parts.scheme, parts.netloc.rsplit("@", 1)[-1], parts.path, "", ""))
    except ValueError:
        return "<invalid-url>"


def error_summary(messages) -> list[dict]:
    if not messages:
        return []
    if not isinstance(messages, (list, tuple)):
        messages = [messages]
    summaries = []
    for message in messages:
        text = str(message)
        lower = text.lower()
        if "timeout" in lower or "timed out" in lower:
            kind = "timeout"
        elif "rate limit" in lower or "rate-limit" in lower:
            kind = "rate_limited"
        elif "no match" in lower:
            kind = "no_match"
        elif "not found" in lower:
            kind = "not_found"
        else:
            kind = "reported_error"
        summaries.append({"kind": kind, "sha256": text_digest(text)})
    return summaries


def record_runtime(**settings) -> None:
    if not enabled():
        return
    logger.info("Diagnostic tracing enabled; structured records are included in the scan log.")
    versions = {}
    for package in _PACKAGES:
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = "<not-installed>"
    record("runtime", python=sys.version, os=platform.system(), os_release=platform.release(),
           architecture=platform.machine(), cpu_count=os.cpu_count(), packages=versions, settings=settings)
    for package, root in (
        ("fosslight_source", Path(__file__).parent),
        ("fosslight_util", Path(constant.__file__).parent),
    ):
        files = {}
        try:
            for path in sorted(root.rglob("*.py")):
                files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as error:
            logger.warning("Cannot fingerprint diagnostic source for %s: %s", package, type(error).__name__)
            record("source_fingerprint_error", package=package, error_type=type(error).__name__, errno=error.errno)
        else:
            record("source_fingerprint", package=package, files=files,
                   sha256=text_digest(json.dumps(files, sort_keys=True)))


def record_inputs(path_to_scan: str, excluded_files: set) -> None:
    if not enabled():
        return

    def walk_error(error: OSError) -> None:
        logger.warning("Diagnostic input traversal failed: %s", type(error).__name__)
        record("input_error", error_type=type(error).__name__, errno=error.errno)

    count = 0
    for root, dirs, files in os.walk(path_to_scan, onerror=walk_error):
        dirs[:] = [name for name in dirs if name not in (".git", ".hg", ".svn")]
        for name in files:
            path = os.path.join(root, name)
            native_path = os.path.relpath(path, path_to_scan)
            rel_path = native_path.replace("\\", "/")
            if rel_path in excluded_files:
                record("input_excluded", path=rel_path, reason="scanner_exclusion")
                continue
            md5 = hashlib.md5()
            sha256 = hashlib.sha256()
            size = crlf = cr = lf = 0
            previous_cr = False
            try:
                with open(path, "rb") as source:
                    for chunk in iter(lambda: source.read(65536), b""):
                        md5.update(chunk)
                        sha256.update(chunk)
                        size += len(chunk)
                        cr += chunk.count(b"\r")
                        lf += chunk.count(b"\n")
                        crlf += chunk.count(b"\r\n") + int(previous_cr and chunk.startswith(b"\n"))
                        previous_cr = chunk.endswith(b"\r")
            except OSError as error:
                logger.warning("Cannot read diagnostic input %s: %s", rel_path, type(error).__name__)
                record("input_error", path=rel_path, error_type=type(error).__name__, errno=error.errno)
                continue
            record("input", path=rel_path, native_path=native_path,
                   size=size, md5=md5.hexdigest(), sha256=sha256.hexdigest(),
                   crlf=crlf, bare_lf=lf - crlf, bare_cr=cr - crlf)
            count += 1
    record("input_summary", hashed_files=count)


def record_kb_target(path: str, reason: str, *, md5: str = "", source: str = "") -> None:
    if not any(part in (".git", ".hg", ".svn") for part in path.replace("\\", "/").split("/")):
        record("kb_target", path=path, reason=reason, md5=md5, source=source)


def record_kb_response(job_id: str, status: dict, requested_hashes: list[str]) -> None:
    if not enabled():
        return
    seen = set()
    rows = status.get("results") or []
    if not isinstance(rows, list):
        record("kb_response_invalid_results", job_id=job_id, value_type=type(rows).__name__)
        rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            record("kb_response_invalid_row", job_id=job_id, index=index, value_type=type(row).__name__)
            continue
        file_hash = row.get("file_hash", "")
        if not isinstance(file_hash, str):
            record("kb_response_invalid_row", job_id=job_id, index=index,
                   value_type=type(file_hash).__name__, reason="invalid_hash_type")
            continue
        output = row.get("output") or ""
        output_text = output if isinstance(output, str) else json.dumps(output, sort_keys=True)
        success = row.get("success")
        record("kb_response", job_id=job_id, index=index, md5=file_hash,
               success=success if isinstance(success, bool) else None, success_type=type(success).__name__,
               applied=bool(success and output and file_hash),
               origin_url=safe_url(output_text), origin_sha256=text_digest(output_text),
               output_type=type(output).__name__,
               duplicate=file_hash in seen, errors=error_summary(row.get("message") or row.get("error")))
        seen.add(file_hash)
    for file_hash in requested_hashes:
        if file_hash not in seen:
            record("kb_response_missing", job_id=job_id, md5=file_hash)


def record_items(stage: str, items: list) -> None:
    if not enabled():
        return
    record("result_summary", stage=stage, items=len(items))
    for index, item in enumerate(items):
        oss_rows = []
        for oss in item.oss_items:
            oss_rows.append({
                "name": oss.name, "version": oss.version, "licenses": list(oss.license),
                "download": safe_url(oss.download_location or ""),
                "download_sha256": text_digest(oss.download_location or ""),
                "copyright_sha256": text_digest(oss.copyright or ""),
                "comment": error_summary(oss.comment),
            })
        downloads = item.download_location
        if isinstance(downloads, str):
            downloads = [downloads]
        record("result", stage=stage, index=index, path=item.source_name_or_path,
               md5=getattr(item, "_cached_kb_md5", None),
               license_text=getattr(item, "is_license_text", False),
               manifest=getattr(item, "is_manifest_file", False),
               excluded=item.exclude, name=item.oss_name, version=item.oss_version,
               licenses=list(item.licenses), downloads=[safe_url(url) for url in downloads],
               download_sha256=[text_digest(url) for url in downloads],
               comment=error_summary(item.comment), oss=oss_rows)
