"""B3 field-level evidence from a real CBP 1.2.0 RC-era manifest.

Important: this manifest is `package_id: "cbp"` and `version: "v1.2.0"`, not a
CBM-scoped or attested CBM manifest. It proves CBM's body_hash_scope handling
on real CBP output; full B3 remains blocked by B1/B2.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cbm_attach.reasons import InputError
from cbm_attach.reports import identity_errors, load_report


FIXTURE = Path(__file__).with_name("fixtures") / "cbp-1.2.0-rc-quality-manifest.json"


def _data() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_b3_rc_manifest_base_scope_is_accepted() -> None:
    report = load_report(FIXTURE, "cbp")
    assert report.data["body_hash_scope"] == "base"
    assert report.data["release_body_hash"] == (
        "6cca0e560af9a1239b619bb6cb8d1d2b90e102e51cd058fbb83f00114da8a09b"
    )
    assert len(report.data["artifact_hashes"]) >= 1


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


def test_b3_manifest_is_not_cbm_scoped() -> None:
    report = load_report(FIXTURE, "cbp")
    assert report.package_id == "cbp"
    assert report.version == "v1.2.0"
    errors = identity_errors(report, report, version="v0.1.0", tag="v0.1.0")
    assert errors
