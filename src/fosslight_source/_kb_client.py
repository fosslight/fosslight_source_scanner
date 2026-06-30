#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Dict, List, NamedTuple, Optional

import fosslight_util.constant as constant

logger = logging.getLogger(constant.LOGGER_NAME)

_SCAN_JOB_POLL_INTERVAL_SEC = 1.0
_SCAN_JOB_POLL_MAX_INTERVAL_SEC = 10.0
_SCAN_JOB_REQUEST_TIMEOUT_SEC = 30
_SCAN_JOB_MIN_WAIT_SEC = 300
_SCAN_JOB_PER_HASH_SEC = 35


def _kb_request(
    kb_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    kb_token: str = "",
    timeout: int = _SCAN_JOB_REQUEST_TIMEOUT_SEC,
) -> dict:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(f"{kb_url.rstrip('/')}/{path.lstrip('/')}", data=data, method=method)
    request.add_header("Accept", "application/json")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    if kb_token:
        request.add_header("Authorization", f"Bearer {kb_token}")

    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode()
        return json.loads(body) if body else {}


def _estimate_job_wait_timeout(file_hash_count: int) -> float:
    return float(max(_SCAN_JOB_MIN_WAIT_SEC, file_hash_count * _SCAN_JOB_PER_HASH_SEC))


def _coerce_count(value, default: int) -> int:
    if value is None:
        return default
    try:
        count = int(value)
    except (TypeError, ValueError):
        return default
    return count if count >= 0 else default


def _extract_response_message(response_body: dict) -> Optional[str]:
    message = response_body.get("message")
    if isinstance(message, str):
        message = message.strip()
        if message:
            return message
    return None


def _scan_job_failure_message(response_body: dict) -> Optional[str]:
    """Return server message when a scan/jobs response indicates failure."""
    message = _extract_response_message(response_body)
    if not message:
        return None

    status = response_body.get("status")
    if status is None or str(status).lower() == "failed":
        return message

    if not response_body.get("job_id"):
        return message

    return None


def _parse_http_error_body(error: urllib.error.HTTPError) -> dict:
    try:
        raw = error.read().decode()
        return json.loads(raw) if raw else {}
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return {}


class KbScanJobResult(NamedTuple):
    origin_urls: Dict[str, str]
    failure_message: Optional[str]
    requested_count: int
    returned_count: int


def _kb_scan_job_result(
    origin_urls: Dict[str, str],
    failure_message: Optional[str],
    requested_count: int,
) -> KbScanJobResult:
    return KbScanJobResult(
        origin_urls=origin_urls,
        failure_message=failure_message,
        requested_count=requested_count,
        returned_count=len(origin_urls),
    )


def fetch_origin_urls_via_scan_job(
    file_hashes: List[str],
    kb_url: str,
    kb_token: str,
) -> KbScanJobResult:
    """
    Create a POST /scan/jobs request, poll until completion, and return a file_hash -> origin_url map.
    :param file_hashes: list of MD5 file hashes to look up.
    :param kb_url: KB API base URL.
    :param kb_token: KB API bearer token.
    :return: origin URLs, optional failure message, and requested/returned file_hash counts.
    """
    unique_hashes = list(dict.fromkeys(h for h in file_hashes if h))
    requested_count = len(unique_hashes)
    if not unique_hashes:
        return _kb_scan_job_result({}, None, 0)

    create_payload = {"file_hashes": unique_hashes}
    try:
        created = _kb_request(kb_url, "scan/jobs", method="POST", payload=create_payload, kb_token=kb_token)
    except urllib.error.HTTPError as e:
        failure_message = _scan_job_failure_message(_parse_http_error_body(e))
        if not failure_message:
            failure_message = f"HTTP {e.code} {e.reason}"
        logger.warning(f"KB scan job create failed: {failure_message}")
        return _kb_scan_job_result({}, failure_message, requested_count)
    except urllib.error.URLError as e:
        failure_message = str(e)
        logger.warning(f"KB scan job create failed: {failure_message}")
        return _kb_scan_job_result({}, failure_message, requested_count)
    except Exception as e:
        failure_message = str(e)
        logger.warning(f"KB scan job create failed: {failure_message}")
        return _kb_scan_job_result({}, failure_message, requested_count)

    failure_message = _scan_job_failure_message(created)
    if failure_message:
        logger.warning(f"KB scan job create failed: {failure_message}")
        return _kb_scan_job_result({}, failure_message, requested_count)

    if str(created.get("status", "")).lower() == "failed":
        failure_message = "scan job create failed"
        logger.warning(f"KB scan job create failed: {failure_message}")
        return _kb_scan_job_result({}, failure_message, requested_count)

    job_id = created.get("job_id", "")
    if not job_id:
        failure_message = "scan job create response missing job_id"
        logger.warning(f"KB scan job create failed: {failure_message}")
        return _kb_scan_job_result({}, failure_message, requested_count)

    fallback_count = len(unique_hashes)
    accepted = _coerce_count(
        created.get("accepted"),
        _coerce_count(created.get("total"), fallback_count),
    )
    skipped = _coerce_count(created.get("skipped"), 0)
    logger.info(
        f"KB scan job created: job_id={job_id}, total={created.get('total', fallback_count)}, "
        f"accepted={accepted}, skipped={skipped}"
    )
    if skipped:
        logger.warning(f"KB scan job rate-limited: {skipped} file_hash(es) skipped by server")
    if accepted == 0:
        failure_message = (
            f"rate-limited: {skipped} file_hash(es) skipped by server"
            if skipped
            else "scan job accepted no file_hashes"
        )
        return _kb_scan_job_result({}, failure_message, requested_count)

    deadline = time.monotonic() + _estimate_job_wait_timeout(accepted)
    interval = _SCAN_JOB_POLL_INTERVAL_SEC
    origin_urls: Dict[str, str] = {}

    while time.monotonic() < deadline:
        try:
            status = _kb_request(kb_url, f"scan/jobs/{job_id}", kb_token=kb_token)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.warning(f"KB scan job not found: {job_id}")
                return _kb_scan_job_result(origin_urls, "scan job not found", requested_count)
            failure_message = _scan_job_failure_message(_parse_http_error_body(e))
            if failure_message:
                logger.warning(f"KB scan job status failed: {failure_message}")
                return _kb_scan_job_result(origin_urls, failure_message, requested_count)
            logger.warning(f"KB scan job status failed: HTTP {e.code}")
            time.sleep(interval)
            interval = min(interval * 1.5, _SCAN_JOB_POLL_MAX_INTERVAL_SEC)
            continue
        except urllib.error.URLError as e:
            logger.warning(f"KB scan job status failed: {e}")
            time.sleep(interval)
            interval = min(interval * 1.5, _SCAN_JOB_POLL_MAX_INTERVAL_SEC)
            continue
        except Exception as e:
            logger.warning(f"KB scan job status parse failed: {e}")
            time.sleep(interval)
            interval = min(interval * 1.5, _SCAN_JOB_POLL_MAX_INTERVAL_SEC)
            continue

        job_status = status.get("status", "")
        if job_status == "completed":
            for row in status.get("results", []):
                if not isinstance(row, dict):
                    continue
                file_hash = row.get("file_hash", "")
                if row.get("success") and row.get("output") and file_hash:
                    origin_urls[file_hash] = row["output"]
            logger.info(
                f"KB scan job completed: job_id={job_id}, "
                f"matched={len(origin_urls)}, failed={status.get('failed', 0)}"
            )
            return _kb_scan_job_result(origin_urls, None, requested_count)

        if job_status == "failed":
            failure_message = _scan_job_failure_message(status)
            if failure_message:
                logger.warning(f"KB scan job failed: job_id={job_id}, message={failure_message}")
            else:
                logger.warning(f"KB scan job failed: job_id={job_id}")
            return _kb_scan_job_result(origin_urls, failure_message or "scan job failed", requested_count)

        time.sleep(interval)
        interval = min(interval * 1.5, _SCAN_JOB_POLL_MAX_INTERVAL_SEC)

    logger.warning(f"KB scan job timed out: job_id={job_id}")
    return _kb_scan_job_result(origin_urls, "scan job timed out", requested_count)
