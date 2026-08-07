#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import re
import fosslight_util.constant as constant
from ._license_matched import MatchedLicense
from ._scan_item import SourceItem
from ._scan_item import replace_word
from ._scan_item import is_notice_file
from typing import Tuple

logger = logging.getLogger(constant.LOGGER_NAME)
REMOVE_LICENSE = ["warranty-disclaimer"]
find_word = re.compile(rb"SPDX-PackageDownloadLocation\s*:\s*(\S+)", re.IGNORECASE)
SPDX_LICENSE_IDENTIFIER_PATTERN = re.compile(
    r'SPDX-License-Identifier\s*:\s*([^\r\n]+)', re.IGNORECASE
)
LICENSE_REF_PREFIX_PATTERN = re.compile(r'^LicenseRef-', re.IGNORECASE)
# Trailing closers from block/HTML comments, e.g. "MIT */" or "MIT -->"
SPDX_COMMENT_TRAILER_PATTERN = re.compile(r'\s*(?:\*/|-->)\s*$')
KEYWORD_SPDX_ID = r'SPDX-License-Identifier\s*[\S]+'
KEYWORD_DOWNLOAD_LOC = r'DownloadLocation\s*[\S]+'
KEYWORD_SCANCODE_UNKNOWN = "unknown-spdx"
KEYWORD_UNKNOWN_LICENSE_REFERENCE = "unknown-license-reference"
SPDX_REPLACE_WORDS = ["(", ")"]
KEY_AND_OR = re.compile(r"(?<=\s)(?:and|or)(?=\s)", re.IGNORECASE)
KEY_AND_OR_CAPTURE = re.compile(r"(?<=\s)(and|or)(?=\s)", re.IGNORECASE)
GPL_LICENSE_PATTERN = r'((a|l)?gpl|gfdl)'  # GPL, LGPL, AGPL, GFDL
SOURCE_EXTENSIONS = [
    '.java', '.cpp', '.c', '.cc', '.cxx', '.c++', '.h', '.hh', '.hpp', '.hxx', '.h++',
    '.cs', '.py', '.pyw', '.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx',
    '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.kts', '.scala', '.sc',
    '.m', '.mm', '.dart', '.lua', '.pl', '.pm', '.r', '.R',
    '.hs', '.clj', '.cljs', '.ex', '.exs', '.groovy', '.gradle',
    '.vue', '.svelte', '.asm', '.s', '.i', '.ii'
]


def is_gpl_family_license(licenses: list) -> bool:
    if not licenses:
        return False

    for license_name in licenses:
        if not license_name:
            continue

        license_lower = license_name.lower()
        if re.search(GPL_LICENSE_PATTERN, license_lower):
            logger.debug(f"GPL family license detected: {license_name}")
            return True

    return False


def should_remove_copyright_for_gpl_license_text(licenses: list, is_license_text: bool) -> bool:
    return is_license_text and is_gpl_family_license(licenses)


def _expression_has_non_unknown_license_reference(license_expression: str) -> bool:
    if not license_expression:
        return False
    for token in split_spdx_expression(license_expression.lower()):
        token = token.strip()
        if token and KEYWORD_UNKNOWN_LICENSE_REFERENCE not in token:
            return True
    return False


def _matched_texts_with_other_licenses(matches: list) -> set:
    """matched_text values that also produced a non-unknown-license-reference license."""
    texts = set()
    for matched_lic in matches or []:
        matched_txt = matched_lic.get("matched_text") or ""
        license_expression = matched_lic.get("license_expression") or ""
        if matched_txt and _expression_has_non_unknown_license_reference(license_expression):
            texts.add(matched_txt)
    return texts


def get_error_from_header(header_item: list) -> Tuple[bool, str]:
    has_error = False
    str_error = ""
    key_error = "errors"

    try:
        for header in header_item:
            if key_error in header:
                errors = header[key_error]
                error_cnt = len(errors)
                if error_cnt > 0:
                    has_error = True
                    str_error = '{}...({})'.format(errors[0], error_cnt)
                    break
    except Exception as ex:
        logger.debug(f"Error_parsing_header: {ex}")
    return has_error, str_error


def parsing_scancode_32_earlier(
    scancode_file_list: list, has_error: bool = False, ui_mode: bool = False
) -> Tuple[bool, list, list, dict]:
    rc = True
    msg = []
    scancode_file_item = []
    license_list = {}  # Key :[license]+[matched_text], value: MatchedLicense()

    if scancode_file_list:
        for file in scancode_file_list:
            try:
                is_dir = False
                file_path = file.get("path", "")
                if not file_path:
                    continue
                is_binary = file.get("is_binary", False)
                if "type" in file:
                    is_dir = file["type"] == "directory"
                if not is_binary and not is_dir:
                    licenses = file.get("licenses", [])
                    copyright_list = file.get("copyrights", [])

                    result_item = SourceItem(file_path)

                    if has_error and "scan_errors" in file:
                        error_msg = file.get("scan_errors", [])
                        if len(error_msg) > 0:
                            result_item.comment = ",".join(error_msg)
                            scancode_file_item.append(result_item)
                            continue
                    copyright_value_list = []
                    for x in copyright_list:
                        latest_key_data = x.get("copyright", "")
                        if latest_key_data:
                            copyright_data = latest_key_data
                        else:
                            copyright_data = x.get("value", "")
                        if copyright_data:
                            try:
                                copyright_data = re.sub(KEYWORD_SPDX_ID, '', copyright_data, flags=re.I)
                                copyright_data = re.sub(KEYWORD_DOWNLOAD_LOC, '', copyright_data, flags=re.I).strip()
                            except Exception:
                                pass
                            copyright_value_list.append(copyright_data)

                    # Set the license value
                    license_detected = []
                    if not licenses:
                        licenses = []
                    # Keep license and/or copyright findings; UI keeps finding-less files too.
                    if not licenses and not copyright_value_list and not ui_mode:
                        continue

                    license_expression_list = file.get("license_expressions", {})
                    if len(license_expression_list) > 0:
                        license_expression_list = [
                            x.lower() for x in license_expression_list
                            if x is not None]

                    matched_texts_with_other_licenses = {
                        (lic_item.get("matched_text") or "")
                        for lic_item in licenses
                        if (lic_item.get("matched_text") or "")
                        and (lic_item.get("key") or "")
                        and KEYWORD_UNKNOWN_LICENSE_REFERENCE not in (lic_item.get("key") or "").lower()
                    }

                    for lic_item in licenses:
                        license_value = ""
                        key = lic_item.get("key", "")
                        if key in REMOVE_LICENSE:
                            if key in license_expression_list:
                                license_expression_list.remove(key)
                            continue
                        spdx = lic_item.get("spdx_license_key", "")
                        # logger.debug("LICENSE_KEY:"+str(key)+",SPDX:"+str(spdx))

                        if key is not None and key != "":
                            key = key.lower()
                            license_value = key
                            if key in license_expression_list:
                                license_expression_list.remove(key)
                        if spdx is not None and spdx != "":
                            # Print SPDX instead of Key.
                            license_value = spdx.lower()

                        if license_value != "":
                            matched_txt = lic_item.get("matched_text", "")
                            if (
                                KEYWORD_UNKNOWN_LICENSE_REFERENCE in (key or "")
                                and matched_txt in matched_texts_with_other_licenses
                            ):
                                continue
                            if KEYWORD_SCANCODE_UNKNOWN in (key or ""):
                                declared = _extract_spdx_declared_expression(matched_txt)
                                if declared:
                                    license_value = declared

                            for word in replace_word:
                                if word in license_value:
                                    license_value = license_value.replace(word, "")
                            license_detected.append(license_value)

                            # Add matched licenses
                            if "category" in lic_item:
                                lic_category = lic_item["category"]
                                if matched_txt:
                                    lic_matched_key = license_value + matched_txt
                                    if lic_matched_key in license_list:
                                        license_list[lic_matched_key].set_files(file_path)
                                    else:
                                        lic_info = MatchedLicense(license_value, lic_category, matched_txt, file_path)
                                        license_list[lic_matched_key] = lic_info

                        matched_rule = lic_item.get("matched_rule", {})
                        result_item.is_license_text = matched_rule.get("is_license_text", False)

                    if len(license_detected) > 0:
                        result_item.licenses = license_detected

                        # Remove copyright info for license text file of GPL family
                        if should_remove_copyright_for_gpl_license_text(license_detected, result_item.is_license_text):
                            logger.debug(f"Removing copyright for GPL family license text file: {file_path}")
                            result_item.copyright = []
                        else:
                            result_item.copyright = copyright_value_list

                        if len(license_expression_list) > 0:
                            license_expression_list = list(
                                set(license_expression_list))
                            result_item.comment = ','.join(license_expression_list)

                        scancode_file_item.append(result_item)
                    elif copyright_value_list or ui_mode:
                        result_item.copyright = copyright_value_list
                        scancode_file_item.append(result_item)
            except Exception as ex:
                msg.append(f"Error Parsing item: {ex}")
                rc = False
    msg = list(set(msg))
    return rc, scancode_file_item, msg, license_list


def split_spdx_expression(spdx_string: str) -> list:
    for replace in SPDX_REPLACE_WORDS:
        spdx_string = spdx_string.replace(replace, "")
    return [part.strip() for part in KEY_AND_OR.split(spdx_string) if part.strip()]


def split_spdx_expression_with_ops(spdx_string: str) -> tuple[list[str], list[str]]:
    """Return (tokens, ops) where ops[i] is AND/OR between tokens[i] and tokens[i+1]."""
    for replace in SPDX_REPLACE_WORDS:
        spdx_string = spdx_string.replace(replace, "")
    parts = KEY_AND_OR_CAPTURE.split(spdx_string)
    tokens = []
    ops = []
    for idx, part in enumerate(parts):
        part = part.strip()
        if idx % 2 == 0:
            if part:
                tokens.append(part)
        else:
            ops.append(part.upper())
    # Drop trailing ops if last token was empty / missing
    if len(ops) >= len(tokens):
        ops = ops[: max(len(tokens) - 1, 0)]
    return tokens, ops


def join_licenses_with_ops(licenses: list[str], ops: list[str]) -> str:
    if not licenses:
        return ""
    result = licenses[0]
    for idx, license_name in enumerate(licenses[1:], start=0):
        op = ops[idx] if idx < len(ops) else "AND"
        result = f"{result} {op} {license_name}"
    return result


def _merge_ops_across_skip(ops_between: list[str]) -> str:
    """
    When intermediate tokens are skipped and parentheses are not considered,
    keep the operator immediately before the next kept token (직전 연산자).

    SPDX AND/OR are left-associative with equal precedence, so
    ``A OR B AND C`` means ``(A OR B) AND C``. Removing B yields ``A AND C``.
    """
    normalized = [op.upper() for op in ops_between if op]
    if not normalized:
        return "AND"
    return normalized[-1]


def _kept_tokens_with_merged_ops(
    tokens: list[str], ops: list[str]
) -> tuple[list[str], list[str]]:
    """Keep non-empty tokens; use the 직전 operator across skipped positions."""
    kept_tokens = []
    kept_ops = []
    last_kept_idx = None
    for idx, token in enumerate(tokens):
        token = (token or "").strip()
        if not token:
            continue
        if last_kept_idx is not None:
            # ops[i] sits between tokens[i] and tokens[i+1]
            kept_ops.append(_merge_ops_across_skip(ops[last_kept_idx:idx]))
        kept_tokens.append(token)
        last_kept_idx = idx
    return kept_tokens, kept_ops


_LICENSE_EXPR_TOKEN_PATTERN = re.compile(
    r"\(|\)|(?i:\band\b)|(?i:\bor\b)|[^\s()]+"
)


class _LicenseLeaf:
    def __init__(self, value: str) -> None:
        self.value = value


class _LicenseBinOp:
    def __init__(self, op: str, left, right) -> None:
        self.op = op
        self.left = left
        self.right = right


def _tokenize_license_expression(expression: str) -> list[str]:
    return _LICENSE_EXPR_TOKEN_PATTERN.findall(expression or "")


def _parse_license_expression_tokens(tokens: list[str]):
    """
    Parse SPDX-like license expression.

    AND/OR have equal precedence and are left-associative.
    Parentheses change grouping.
    """
    pos = 0

    def primary():
        nonlocal pos
        if pos >= len(tokens):
            return None
        if tokens[pos] == "(":
            pos += 1
            node = parse_expr()
            if pos < len(tokens) and tokens[pos] == ")":
                pos += 1
            return node
        token = tokens[pos]
        pos += 1
        return _LicenseLeaf(token)

    def parse_expr():
        nonlocal pos
        node = primary()
        while pos < len(tokens) and tokens[pos].upper() in ("AND", "OR"):
            op = tokens[pos].upper()
            pos += 1
            right = primary()
            if right is None:
                break
            node = _LicenseBinOp(op, node, right)
        return node

    return parse_expr()


def _transform_license_expr_node(
    node,
    replacements: list[str],
    repl_idx: list[int],
    suppress_ulr: bool,
):
    if node is None:
        return None
    if isinstance(node, _LicenseLeaf):
        token = node.value
        token_lower = token.lower()
        if KEYWORD_UNKNOWN_LICENSE_REFERENCE in token_lower:
            return None if suppress_ulr else _LicenseLeaf(token)
        if KEYWORD_SCANCODE_UNKNOWN in token_lower:
            if repl_idx[0] < len(replacements):
                replacement = replacements[repl_idx[0]]
                repl_idx[0] += 1
                return _parse_license_expression_tokens(
                    _tokenize_license_expression(replacement)
                )
            return None
        output = _normalize_license_token(token) or token
        if not output or output.lower() in REMOVE_LICENSE:
            return None
        return _LicenseLeaf(output)

    left = _transform_license_expr_node(node.left, replacements, repl_idx, suppress_ulr)
    right = _transform_license_expr_node(node.right, replacements, repl_idx, suppress_ulr)
    if left is None:
        return right
    if right is None:
        return left
    return _LicenseBinOp(node.op, left, right)


def _serialize_license_expr_node(node, is_right_child: bool = False) -> str:
    if node is None:
        return ""
    if isinstance(node, _LicenseLeaf):
        return node.value
    left = _serialize_license_expr_node(node.left, False)
    right = _serialize_license_expr_node(node.right, True)
    rendered = f"{left} {node.op} {right}"
    # Equal-precedence left-assoc: parenthesize right BinOp groups.
    if is_right_child and isinstance(node, _LicenseBinOp):
        return f"({rendered})"
    return rendered


def _omit_parens_for_two_license_expression(expression: str) -> str:
    """
    Drop parentheses when the expression only connects two licenses.

    Example: ``(Apache-2.0 OR MIT)`` -> ``Apache-2.0 OR MIT``.
    Keep parentheses when three or more licenses need grouping.
    """
    expr = (expression or "").strip()
    if not expr or "(" not in expr:
        return expr
    tokens = _tokenize_license_expression(expr)
    license_tokens = [
        token for token in tokens
        if token not in ("(", ")") and token.upper() not in ("AND", "OR")
    ]
    if len(license_tokens) != 2:
        return expr
    return " ".join(
        token for token in tokens if token not in ("(", ")")
    )


def _clean_spdx_declaration(raw: str) -> str:
    """Strip whitespace and trailing comment terminators from a captured declaration."""
    cleaned = (raw or "").strip()
    if not cleaned:
        return ""
    return SPDX_COMMENT_TRAILER_PATTERN.sub('', cleaned).strip()


def _strip_license_ref_prefix(token: str) -> str:
    return LICENSE_REF_PREFIX_PATTERN.sub('', (token or "").strip())


def _extract_spdx_declared_expression(matched_txt: str) -> str:
    """
    Extract SPDX-License-Identifier value from matched_text.

    - Removes trailing comment closers (*/ , -->)
    - Strips LicenseRef- from each AND/OR token
    """
    matched = SPDX_LICENSE_IDENTIFIER_PATTERN.search(matched_txt or "")
    if not matched:
        return ""
    declared = _clean_spdx_declaration(matched.group(1))
    if not declared:
        return ""
    tokens, ops = split_spdx_expression_with_ops(declared)
    cleaned_tokens = [_strip_license_ref_prefix(token) for token in tokens]
    kept_tokens, kept_ops = _kept_tokens_with_merged_ops(cleaned_tokens, ops)
    if not kept_tokens:
        return ""
    return join_licenses_with_ops(kept_tokens, kept_ops)


def _normalize_license_token(token: str) -> str:
    token = (token or "").strip()
    if not token:
        return ""
    license_expression_spdx = get_license_expression_spdx(token)
    token = license_expression_spdx if license_expression_spdx else token
    for word in replace_word:
        token = token.replace(word, "")
    return token


def _declared_licenses_from_matched_text(matched_txt: str) -> tuple[list[str], list[str]]:
    declared = _extract_spdx_declared_expression(matched_txt)
    if not declared:
        return [], []
    return split_spdx_expression_with_ops(declared)


def _build_unknown_spdx_replacement_queue(matches: list) -> list[str]:
    """Ordered replacements for each unknown-spdx token in match order."""
    queue = []
    for matched_lic in matches or []:
        expr = (matched_lic.get("license_expression") or "").lower()
        if KEYWORD_SCANCODE_UNKNOWN not in expr:
            continue
        match_tokens, _ = split_spdx_expression_with_ops(expr)
        declared_tokens, declared_ops = _declared_licenses_from_matched_text(
            matched_lic.get("matched_text") or ""
        )
        if not declared_tokens:
            continue

        unknown_indexes = [
            idx for idx, token in enumerate(match_tokens)
            if KEYWORD_SCANCODE_UNKNOWN in token
        ]
        if not unknown_indexes:
            continue

        if len(match_tokens) == len(declared_tokens):
            for idx in unknown_indexes:
                queue.append(_normalize_license_token(declared_tokens[idx]) or declared_tokens[idx])
            continue

        if all(KEYWORD_SCANCODE_UNKNOWN in token for token in match_tokens):
            if len(match_tokens) == 1:
                norms = [_normalize_license_token(token) or token for token in declared_tokens]
                queue.append(join_licenses_with_ops(norms, declared_ops))
            else:
                for i, _ in enumerate(unknown_indexes):
                    declared = declared_tokens[i] if i < len(declared_tokens) else declared_tokens[-1]
                    queue.append(_normalize_license_token(declared) or declared)
            continue

        # Mixed known + unknown tokens with different declared length:
        # drop declared tokens that correspond to known match tokens, then assign the rest.
        unused = list(declared_tokens)
        for token in match_tokens:
            if KEYWORD_SCANCODE_UNKNOWN in token:
                continue
            token_norm = (_normalize_license_token(token) or token).lower()
            for idx, declared in enumerate(unused):
                declared_norm = (_normalize_license_token(declared) or declared).lower()
                if declared_norm == token_norm or declared.lower() == token.lower():
                    unused.pop(idx)
                    break
        for _ in unknown_indexes:
            if not unused:
                break
            declared = unused.pop(0)
            queue.append(_normalize_license_token(declared) or declared)
    return queue


def _should_suppress_unknown_license_reference(
    matches: list, matched_texts_with_other_licenses: set
) -> bool:
    for matched_lic in matches or []:
        expr = (matched_lic.get("license_expression") or "").lower()
        matched_txt = matched_lic.get("matched_text") or ""
        if (
            KEYWORD_UNKNOWN_LICENSE_REFERENCE in expr
            and matched_txt in matched_texts_with_other_licenses
        ):
            return True
    return False


def build_comment_from_detected_expression(
    detected_expression: str,
    matches: list,
    matched_texts_with_other_licenses: set,
) -> str:
    """
    Rebuild comment from detected expression.

    Preserves AND/OR and parentheses. SPDX AND/OR are left-associative with
    equal precedence, so without parentheses ``A OR B AND C`` means
    ``(A OR B) AND C``. Removing ``B`` therefore yields ``A AND C`` (직전 연산자).
    Explicit parentheses are honored, e.g.
    ``A OR (B AND C)`` with ``B`` removed becomes ``A OR C``.
    """
    if not detected_expression:
        return ""

    expr = detected_expression
    if KEYWORD_SCANCODE_UNKNOWN not in expr.lower():
        expr = re.sub(
            r'licenseref-scancode-unknown-spdx',
            KEYWORD_SCANCODE_UNKNOWN,
            expr,
            flags=re.IGNORECASE,
        )
        expr = re.sub(
            r'licenseref-scancode-unknown-license-reference',
            KEYWORD_UNKNOWN_LICENSE_REFERENCE,
            expr,
            flags=re.IGNORECASE,
        )

    replacements = _build_unknown_spdx_replacement_queue(matches)
    suppress_ulr = _should_suppress_unknown_license_reference(
        matches, matched_texts_with_other_licenses
    )
    tree = _parse_license_expression_tokens(_tokenize_license_expression(expr))
    if tree is None:
        return ""
    transformed = _transform_license_expr_node(
        tree, replacements, [0], suppress_ulr
    )
    return _omit_parens_for_two_license_expression(
        _serialize_license_expr_node(transformed)
    )


def get_license_expression_spdx(license_expression: str) -> str:
    if not license_expression or not license_expression.strip():
        return ""
    try:
        from licensedcode.cache import build_spdx_license_expression
        result = build_spdx_license_expression(license_expression.strip())
        if result is None:
            return ""
        if isinstance(result, str) and result.lower().startswith("licenseref-"):
            return ""
        return result
    except Exception:
        return ""


def parsing_scancode_32_later(
    scancode_file_list: list, has_error: bool = False, ui_mode: bool = False
) -> Tuple[bool, list, list, dict]:
    rc = True
    msg = []
    scancode_file_item = []
    license_list = {}  # Key :[license]+[matched_text], value: MatchedLicense()

    if scancode_file_list:
        for file in scancode_file_list:
            try:
                file_path = file.get("path", "")
                is_binary = file.get("is_binary", False)
                is_dir = file.get("type", "") == "directory"
                if (not file_path) or is_binary or is_dir:
                    logger.info(f"Skipping {file_path} because it is binary or directory")
                    continue
                result_item = SourceItem(file_path)
                if has_error:
                    error_msg = file.get("scan_errors", [])
                    if error_msg:
                        result_item.comment = ",".join(error_msg)
                        scancode_file_item.append(result_item)
                        continue
                copyright_value_list = []
                for x in file.get("copyrights", []):
                    copyright_data = x.get("copyright", "")
                    if copyright_data:
                        try:
                            copyright_data = re.sub(KEYWORD_SPDX_ID, '', copyright_data, flags=re.I)
                            copyright_data = re.sub(KEYWORD_DOWNLOAD_LOC, '', copyright_data, flags=re.I).strip()
                        except Exception:
                            pass
                        copyright_value_list.append(copyright_data)
                license_detected = []
                resolved_unknown_spdx = False
                licenses = file.get("license_detections", [])
                # Keep license and/or copyright findings; UI keeps finding-less files too.
                if not licenses and not copyright_value_list and not ui_mode:
                    continue
                all_matches = []
                for lic in licenses or []:
                    all_matches.extend(lic.get("matches") or [])
                matched_texts_with_other_licenses = _matched_texts_with_other_licenses(all_matches)
                for lic in licenses or []:
                    matched_lic_list = lic.get("matches", [])
                    for matched_lic in matched_lic_list:
                        found_lic_list = matched_lic.get("license_expression", "")
                        matched_txt = matched_lic.get("matched_text", "")
                        if found_lic_list:
                            found_lic_list = found_lic_list.lower()
                            if KEYWORD_SCANCODE_UNKNOWN in found_lic_list:
                                declared = _extract_spdx_declared_expression(matched_txt)
                                if declared:
                                    found_lic_list = declared
                                    resolved_unknown_spdx = True
                            for found_lic in split_spdx_expression(found_lic_list):
                                if found_lic:
                                    found_lic = found_lic.strip()
                                    if found_lic in REMOVE_LICENSE:
                                        continue
                                    if (
                                        KEYWORD_UNKNOWN_LICENSE_REFERENCE in found_lic.lower()
                                        and matched_txt in matched_texts_with_other_licenses
                                    ):
                                        continue
                                    if KEYWORD_SCANCODE_UNKNOWN in found_lic.lower():
                                        declared = _extract_spdx_declared_expression(matched_txt)
                                        if declared:
                                            found_lic = declared
                                            resolved_unknown_spdx = True
                                    found_lic = _strip_license_ref_prefix(found_lic)
                                    found_lic = _normalize_license_token(found_lic) or found_lic
                                    if not found_lic:
                                        continue
                                    if matched_txt:
                                        lic_matched_key = found_lic + matched_txt
                                        if lic_matched_key in license_list:
                                            license_list[lic_matched_key].set_files(file_path)
                                        else:
                                            lic_info = MatchedLicense(found_lic, "", matched_txt, file_path)
                                            license_list[lic_matched_key] = lic_info
                                    license_detected.append(found_lic)
                result_item.licenses = license_detected
                file_ext = os.path.splitext(file_path)[1].lower()
                is_source_file = file_ext and file_ext in SOURCE_EXTENSIONS
                result_item.is_license_text = is_notice_file(file_path) or (
                    file.get("percentage_of_license_text", 0) > 90 and not is_source_file
                )

                # Remove copyright info for license text file of GPL family
                if should_remove_copyright_for_gpl_license_text(license_detected, result_item.is_license_text):
                    logger.debug(f"Removing copyright for GPL family license text file: {file_path}")
                    result_item.copyright = []
                else:
                    result_item.copyright = copyright_value_list

                if len(license_detected) > 1:
                    detected_expression = file.get("detected_license_expression", "") or ""
                    detected_expression_spdx = file.get("detected_license_expression_spdx", "") or ""
                    if (
                        resolved_unknown_spdx
                        or KEYWORD_SCANCODE_UNKNOWN in detected_expression.lower()
                        or "licenseref-scancode-unknown-spdx" in detected_expression_spdx.lower()
                    ):
                        # Prefer non-SPDX expression so unknown-spdx tokens map cleanly.
                        source_expression = detected_expression or detected_expression_spdx
                        result_item.comment = build_comment_from_detected_expression(
                            source_expression,
                            all_matches,
                            matched_texts_with_other_licenses,
                        )
                    else:
                        license_expression = detected_expression_spdx or detected_expression
                        if license_expression and "OR" in license_expression:
                            result_item.comment = _omit_parens_for_two_license_expression(
                                license_expression
                            )

                scancode_file_item.append(result_item)
            except Exception as ex:
                msg.append(f"Error Parsing item: {ex}")
                rc = False

    return rc, scancode_file_item, msg, license_list


def parsing_file_item(
    scancode_file_list: list, has_error: bool, need_matched_license: bool = False,
    ui_mode: bool = False
) -> Tuple[bool, list, list, dict]:

    rc = True
    msg = []

    first_item = next(iter(scancode_file_list or []), {})
    if "licenses" in first_item:
        rc, scancode_file_item, msg, license_list = parsing_scancode_32_earlier(
            scancode_file_list, has_error, ui_mode
        )
    else:
        rc, scancode_file_item, msg, license_list = parsing_scancode_32_later(
            scancode_file_list, has_error, ui_mode
        )
    if not need_matched_license:
        license_list = {}
    return rc, scancode_file_item, msg, license_list
