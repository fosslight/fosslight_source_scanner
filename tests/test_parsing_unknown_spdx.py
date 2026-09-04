# Copyright (c) 2026 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for unknown-spdx restoration and SPDX declaration cleanup."""

import pytest

from fosslight_source._parsing_scancode_file_item import (
    _extract_spdx_declared_expression,
    _declared_licenses_from_matched_text,
    build_comment_from_detected_expression,
    parsing_scancode,
    _matched_texts_with_other_licenses,
)


@pytest.mark.parametrize(
    ("matched_text", "expected"),
    [
        ("// SPDX-License-Identifier: MIT", "MIT"),
        ("// SPDX-License-Identifier-MIT", "MIT"),
        ("// SPDX-License-Identifier, MIT", "MIT"),
        ("// SPDX-License-Identifier MIT", "MIT"),
        ('        "SPDX-license-identifier-BSD",', "BSD"),
        ('        "SPDX-license-identifier-OFL", // by exception only', "OFL"),
        ("/* SPDX-License-Identifier: MIT */", "MIT"),
        ("<!-- SPDX-License-Identifier: MIT -->", "MIT"),
        ("# SPDX-License-Identifier: LicenseRef-MIT-like", "MIT-like"),
        (
            "# SPDX-License-Identifier: LicenseRef-Foo AND LicenseRef-Bar",
            "Foo AND Bar",
        ),
        (
            "/* SPDX-License-Identifier: LicenseRef-Foo OR LicenseRef-Bar */",
            "Foo OR Bar",
        ),
    ],
)
def test_extract_spdx_declared_expression(matched_text, expected):
    assert _extract_spdx_declared_expression(matched_text) == expected


def test_declared_licenses_strips_licenseref_per_token():
    tokens, ops = _declared_licenses_from_matched_text(
        "# SPDX-License-Identifier: LicenseRef-Foo AND LicenseRef-Bar"
    )
    assert tokens == ["Foo", "Bar"]
    assert ops == ["AND"]


@pytest.mark.parametrize(
    ("matched_text", "expected_license"),
    [
        ("// SPDX-License-Identifier: UNLICENSED", "UNLICENSED"),
        ("// SPDX-License-Identifier: LicenseRef-MIT-like", "MIT-like"),
        ("/* SPDX-License-Identifier: MIT */", "MIT"),
        ("<!-- SPDX-License-Identifier: Apache-2.0 -->", "Apache-2.0"),
    ],
)
def test_unknown_spdx_uses_declared_identifier(matched_text, expected_license):
    scancode_file_list = [{
        "path": "example.sol",
        "type": "file",
        "license_detections": [{
            "matches": [{
                "license_expression": "unknown-spdx",
                "matched_text": matched_text,
            }],
        }],
        "copyrights": [],
    }]

    success, results, _messages, _license_list = parsing_scancode(scancode_file_list)

    assert success is True
    assert results[0].licenses == [expected_license]


def test_unknown_spdx_in_compound_expression_splits_and_or():
    scancode_file_list = [{
        "path": "dual.txt",
        "type": "file",
        "detected_license_expression": "gpl-2.0 OR unknown-spdx",
        "license_detections": [{
            "matches": [{
                "license_expression": "gpl-2.0 OR unknown-spdx",
                "matched_text": "# SPDX-License-Identifier: GPL-2.0 or MIT-like",
            }],
        }],
        "copyrights": [],
    }]

    success, results, _messages, _ = parsing_scancode(scancode_file_list)

    assert success is True
    assert results[0].licenses == ["GPL-2.0", "MIT-like"]
    assert results[0].comment == "GPL-2.0 OR MIT-like"


def test_unknown_spdx_comment_preserves_and_or_from_detected_expression():
    matched_same = "# The code is not licensed under GPL-2.0."
    scancode_file_list = [{
        "path": "dual_unknow.py",
        "type": "file",
        "detected_license_expression": (
            "(unknown-spdx OR unknown-spdx) AND unknown-license-reference AND gpl-2.0"
        ),
        "license_detections": [{
            "matches": [
                {
                    "license_expression": "unknown-spdx OR unknown-spdx",
                    "matched_text": "# SPDX-License-Identifier: NEW OR DApache-2.0",
                },
                {
                    "license_expression": "unknown-license-reference",
                    "matched_text": matched_same,
                },
                {
                    "license_expression": "gpl-2.0",
                    "matched_text": matched_same,
                },
            ],
        }],
        "copyrights": [],
    }]

    success, results, _messages, _ = parsing_scancode(scancode_file_list)

    assert success is True
    assert results[0].licenses == ["DApache-2.0", "GPL-2.0", "NEW"]
    assert "unknown-license-reference" not in [lic.lower() for lic in results[0].licenses]
    assert results[0].comment == "NEW OR DApache-2.0 AND GPL-2.0"


def test_unknown_license_reference_suppressed_when_same_matched_text_has_other_license():
    matched_same = "# The code is not licensed under GPL-2.0."
    scancode_file_list = [{
        "path": "sample.py",
        "type": "file",
        "license_detections": [{
            "matches": [
                {
                    "license_expression": "unknown-license-reference",
                    "matched_text": matched_same,
                },
                {
                    "license_expression": "gpl-2.0",
                    "matched_text": matched_same,
                },
            ],
        }],
        "copyrights": [],
    }]

    success, results, _messages, _ = parsing_scancode(scancode_file_list)

    assert success is True
    assert results[0].licenses == ["GPL-2.0"]


def test_licenseref_tokens_stripped_from_unknown_spdx_and_expression():
    scancode_file_list = [{
        "path": "refs.py",
        "type": "file",
        "detected_license_expression": "unknown-spdx AND unknown-spdx",
        "license_detections": [{
            "matches": [{
                "license_expression": "unknown-spdx AND unknown-spdx",
                "matched_text": (
                    "# SPDX-License-Identifier: LicenseRef-NEW AND LicenseRef-TEST"
                ),
            }],
        }],
        "copyrights": [],
    }]

    success, results, _messages, _ = parsing_scancode(scancode_file_list)

    assert success is True
    assert results[0].licenses == ["NEW", "TEST"]
    assert not results[0].comment


def test_build_comment_from_detected_expression_helper():
    matched_same = "# The code is not licensed under GPL-2.0."
    matches = [
        {
            "license_expression": "unknown-spdx OR unknown-spdx",
            "matched_text": "# SPDX-License-Identifier: NEW OR DApache-2.0",
        },
        {
            "license_expression": "unknown-license-reference",
            "matched_text": matched_same,
        },
        {
            "license_expression": "gpl-2.0",
            "matched_text": matched_same,
        },
    ]
    other_texts = _matched_texts_with_other_licenses(matches)
    comment = build_comment_from_detected_expression(
        "(unknown-spdx OR unknown-spdx) AND unknown-license-reference AND gpl-2.0",
        matches,
        other_texts,
    )
    assert comment == "NEW OR DApache-2.0 AND GPL-2.0"


def test_comment_without_parens_uses_operator_before_kept_token():
    """A OR B AND C is (A OR B) AND C; removing B yields A AND C."""
    matched_same = "not a license reference text"
    matches = [
        {"license_expression": "mit", "matched_text": "MIT"},
        {"license_expression": "unknown-license-reference", "matched_text": matched_same},
        {"license_expression": "apache-2.0", "matched_text": matched_same},
    ]
    comment = build_comment_from_detected_expression(
        "mit OR unknown-license-reference AND apache-2.0",
        matches,
        {matched_same},
    )
    assert comment == "MIT AND Apache-2.0"


def test_comment_with_parens_preserves_or_group():
    """A OR (B AND C) removing B yields A OR C."""
    matched_same = "not a license reference text"
    matches = [
        {"license_expression": "mit", "matched_text": "MIT"},
        {"license_expression": "unknown-license-reference", "matched_text": matched_same},
        {"license_expression": "apache-2.0", "matched_text": matched_same},
    ]
    comment = build_comment_from_detected_expression(
        "mit OR (unknown-license-reference AND apache-2.0)",
        matches,
        {matched_same},
    )
    assert comment == "MIT OR Apache-2.0"


def test_comment_with_parens_preserves_and_after_group():
    """(A OR B) AND C removing B yields A AND C."""
    matched_same = "not a license reference text"
    matches = [
        {"license_expression": "mit", "matched_text": "MIT"},
        {"license_expression": "unknown-license-reference", "matched_text": matched_same},
        {"license_expression": "apache-2.0", "matched_text": matched_same},
    ]
    comment = build_comment_from_detected_expression(
        "(mit OR unknown-license-reference) AND apache-2.0",
        matches,
        {matched_same},
    )
    assert comment == "MIT AND Apache-2.0"


def test_two_license_comment_omits_outer_parentheses():
    from fosslight_source._parsing_scancode_file_item import (
        _omit_parens_for_two_license_expression,
    )

    assert _omit_parens_for_two_license_expression("(Apache-2.0 OR MIT)") == "Apache-2.0 OR MIT"
    assert _omit_parens_for_two_license_expression("((Apache-2.0 OR MIT))") == "Apache-2.0 OR MIT"
    # three licenses: keep grouping parentheses
    assert (
        _omit_parens_for_two_license_expression("GPL-2.0 AND (Apache-2.0 OR MIT)")
        == "GPL-2.0 AND (Apache-2.0 OR MIT)"
    )

    scancode_file_list = [{
        "path": "dual.txt",
        "type": "file",
        "detected_license_expression": "(unknown-spdx OR unknown-spdx)",
        "license_detections": [{
            "matches": [{
                "license_expression": "unknown-spdx OR unknown-spdx",
                "matched_text": "# SPDX-License-Identifier: Apache-2.0 OR MIT",
            }],
        }],
        "copyrights": [],
    }]
    success, results, _messages, _ = parsing_scancode(scancode_file_list)
    assert success is True
    assert results[0].licenses == ["Apache-2.0", "MIT"]
    assert results[0].comment == "Apache-2.0 OR MIT"


def test_android_bp_soong_license_kinds_without_line_comment_in_license():
    scancode_file_list = [{
        "path": "Android.bp",
        "type": "file",
        "detected_license_expression": (
            "(apache-2.0 AND unknown-license-reference) AND (unknown-spdx AND mit)"
        ),
        "license_detections": [
            {
                "license_expression": "apache-2.0 AND unknown-license-reference",
                "matches": [
                    {
                        "license_expression": "apache-2.0",
                        "matched_text": (
                            "// Licensed under the Apache License, Version 2.0 (the \"License\");\n"
                            "// limitations under the License."
                        ),
                    },
                    {
                        "license_expression": "unknown-license-reference",
                        "matched_text": "// *** THIS PACKAGE HAS SPECIAL LICENSING CONDITIONS.  PLEASE",
                    },
                ],
            },
            {
                "license_expression": "unknown-spdx AND mit",
                "matches": [
                    {
                        "license_expression": "unknown-spdx",
                        "matched_text": '        "SPDX-license-identifier-BSD",',
                    },
                    {
                        "license_expression": "mit",
                        "matched_text": '        "SPDX-license-identifier-MIT",',
                    },
                    {
                        "license_expression": "unknown-spdx",
                        "matched_text": (
                            '        "SPDX-license-identifier-OFL", // by exception only'
                        ),
                    },
                ],
            },
        ],
        "copyrights": [],
    }]

    success, results, _messages, _ = parsing_scancode(scancode_file_list)

    assert success is True
    licenses = results[0].licenses
    assert licenses == [
        "Apache-2.0",
        "BSD",
        "MIT",
        "OFL",
        "unknown-license-reference",
    ]
    assert all("//" not in lic for lic in results[0].licenses)
    assert all('"' not in lic for lic in results[0].licenses)
