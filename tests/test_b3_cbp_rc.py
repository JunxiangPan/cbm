"""B3 field-level evidence from the official CBP 1.2.0 CBM manifest.

The manifest is `package_id: "cbm"` / `producer_id: "cbp"` / `version: "v0.1.0"`,
`gate_status: "PASS"`, and carries `body_hash_scope: "base"`, `release_body_hash`, two artifact hashes
and `evidence_sha256`. This proves B3 field-level handling on a real CBM-scoped
manifest. B2 remains blocked: there is still no real CBE report with
`package_id: "cbm"`, so CBM's full identity check cannot pass.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cbm_attach.reasons import InputError
from cbm_attach.reports import load_report


FIXTURE = Path(__file__).with_name("fixtures") / "cbp-1.2.0-cbm-manifest.json"


def _data() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_b3_rc_manifest_base_scope_is_accepted() -> None:
    report = load_report(FIXTURE, "cbp")
    assert report.package_id == "cbm"
    assert report.producer_id == "cbp"
    assert report.version == "v0.1.0"
    assert report.data["body_hash_scope"] == "base"
    assert report.data["gate_status"] == "PASS"
    assert report.data["release_body_hash"] == (
        "0db00009e0f711b965ec670a003a72ee9cffb13e7016bcb14211e2768c1cd288"
    )
    assert report.data["artifact_hashes"] == {
        "cbm_attach-0.1.0-py3-none-any.whl": "e43acd41c3ec75ae77f48221f65d92e86ebb5f413abc10360b2f2a4bc46fa621",
        "cbm_attach-0.1.0.tar.gz": "0a9f07d09cfc6ae990dfe52b830bdd532dfdae3d5559101997029051aec31fad",
    }
    assert report.data["evidence_sha256"] == (
        "ec07d0ec1acd3502b0e4aa4845598cecbcd6a6be38dc01a5c2b626e1ea498fc5"
    )


@pytest.mark.parametrize(
    ("scope", "reason"),
    [
        (None, "MISSING_BODY_HASH_SCOPE"),
        ("full", "BODY_HASH_SCOPE_UNSUPPORTED"),
    ],
)
def test_b3_scope_variants_exit_2(tmp_path: Path, scope, reason: str) -> None:
    data = _data()
    if scope is None:
        data.pop("body_hash_scope")
    else:
        data["body_hash_scope"] = scope
    path = tmp_path / "cbp-quality-manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(InputError) as captured:
        load_report(path, "cbp")
    assert captured.value.exit_code == 2
    assert captured.value.reason_value == reason


def test_b3_manifest_is_cbm_scoped_but_b2_is_blocked() -> None:
    report = load_report(FIXTURE, "cbp")
    assert report.package_id == "cbm"
    assert report.producer_id == "cbp"
    # B2: the CBE side is still missing; this test must not claim full verify.
    assert report.version == "v0.1.0"
