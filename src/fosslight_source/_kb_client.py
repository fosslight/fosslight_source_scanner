#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Dict, List

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


def fetch_origin_urls_via_scan_job(
    file_hashes: List[str],
    kb_url: str,
    kb_token: str,
) -> Dict[str, str]:
    """
    POST /scan/jobs 후 완료될 때까지 polling하여 file_hash -> origin_url 맵을 반환합니다.
    """
    unique_hashes = list(dict.fromkeys(h for h in file_hashes if h))
    if not unique_hashes:
        return {}

    create_payload = {"file_hashes": unique_hashes}
    try:
        created = _kb_request(kb_url, "scan/jobs", method="POST", payload=create_payload, kb_token=kb_token)
    except urllib.error.HTTPError as e:
        logger.warning(f"KB scan job create failed: HTTP {e.code} {e.reason}")
        return {}
    except urllib.error.URLError as e:
        logger.warning(f"KB scan job create failed: {e}")
        return {}
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"KB scan job create failed: {e}")
        return {}

    job_id = created.get("job_id", "")
    if not job_id:
        logger.warning("KB scan job create response missing job_id")
        return {}

    accepted = created.get("accepted", created.get("total", len(unique_hashes)))
    skipped = created.get("skipped", 0)
    logger.info(
        f"KB scan job created: job_id={job_id}, total={created.get('total', len(unique_hashes))}, "
        f"accepted={accepted}, skipped={skipped}"
    )
    if skipped:
        logger.warning(f"KB scan job rate-limited: {skipped} file_hash(es) skipped by server")

    deadline = time.monotonic() + _estimate_job_wait_timeout(int(accepted))
    interval = _SCAN_JOB_POLL_INTERVAL_SEC
    origin_urls: Dict[str, str] = {}

    while time.monotonic() < deadline:
        try:
            status = _kb_request(kb_url, f"scan/jobs/{job_id}", kb_token=kb_token)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.warning(f"KB scan job not found: {job_id}")
                return {}
            logger.warning(f"KB scan job status failed: HTTP {e.code}")
            time.sleep(interval)
            interval = min(interval * 1.5, _SCAN_JOB_POLL_MAX_INTERVAL_SEC)
            continue
        except urllib.error.URLError as e:
            logger.warning(f"KB scan job status failed: {e}")
            time.sleep(interval)
            interval = min(interval * 1.5, _SCAN_JOB_POLL_MAX_INTERVAL_SEC)
            continue
        except (json.JSONDecodeError, Exception) as e:
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
            return origin_urls

        if job_status == "failed":
            logger.warning(f"KB scan job failed: job_id={job_id}")
            return {}

        time.sleep(interval)
        interval = min(interval * 1.5, _SCAN_JOB_POLL_MAX_INTERVAL_SEC)

    logger.warning(f"KB scan job timed out: job_id={job_id}")
    return origin_urls
