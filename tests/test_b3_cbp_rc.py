"""B3 field-level evidence from the real CBP 1.2.0 RC CBM manifest.

The manifest is `package_id: "cbm"` / `producer_id: "cbp"` / `version: "v0.1.0"`
and carries `body_hash_scope: "base"`, `release_body_hash`, two artifact hashes
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
    assert report.data["release_body_hash"] == (
        "b4fa95034d31a84d5fc60a9773852e5ffd002624987947b903ad99ff21e3f077"
    )
    assert report.data["artifact_hashes"] == {
        "cbm_attach-0.1.0-py3-none-any.whl": "a6a812cf6e99a51211ac30b4ef3574ecc7851ff05d3095406a325d1aa8596362",
        "cbm_attach-0.1.0.tar.gz": "3fdb074f7739ff9e14b1bb51b6d43561a9e01b5f1395ac6fc1536295ff690d50",
    }
    assert report.data["evidence_sha256"] == (
        "0edf31e8757d7c6f577efa2a3472c7b33836db9bdc14685634264c201b07732a"
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
