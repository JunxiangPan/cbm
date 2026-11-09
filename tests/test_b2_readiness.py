"""B2 readiness: schema/identity for a synthetic CBM-scoped CBE report.

The CBE report in this test is synthetic and explicitly marked
`not_upstream_evidence`; it proves the consumer's schema/identity path only.
B2 remains blocked until a real CBE report with `package_id: "cbm"` exists.
"""
from __future__ import annotations

import json
from pathlib import Path

from cbm_attach.reports import identity_errors, load_report


FIXTURES = Path(__file__).with_name("fixtures")
CBE = FIXTURES / "cbe-cbm-scoped.synthetic.json"
CBE_META = FIXTURES / "cbe-cbm-scoped.synthetic.meta.json"
CBP = FIXTURES / "cbp-1.2.0-cbm-manifest.json"


def test_b2_synthetic_cbm_scoped_report_schema_is_accepted() -> None:
    report = load_report(CBE, "cbe")
    assert report.package_id == "cbm"
    assert report.producer_id == "cbe"
    assert report.data["tag"] == "v0.1.0"
    assert report.gate_status == "PASS"


def test_b2_readiness_identity_accepts_synthetic_cbe_and_real_cbp() -> None:
    cbe = load_report(CBE, "cbe")
    cbp = load_report(CBP, "cbp")
    assert identity_errors(cbe, cbp, version="v0.1.0", tag="v0.1.0") == []


def test_b2_fixture_is_marked_synthetic_not_upstream_evidence() -> None:
    meta = json.loads(CBE_META.read_text(encoding="utf-8"))
    assert meta["synthetic"] is True
    assert meta["not_upstream_evidence"] is True
    # This is the B2 blocked state, not a PASS:
    assert "real CBE report" in meta["purpose"]


def test_b2_real_cbp_manifest_is_object_shape() -> None:
    """The CBP 1.2.2 side is real and object-shaped; the CBE side is not."""
    cbp = load_report(CBP, "cbp")
    assert cbp.data["schema_version"] == "1"
    assert isinstance(cbp.data["artifact_repository"], dict)
    assert cbp.data["artifact_repository"]["repository"] == "JunxiangPan/cbm"
    assert cbp.gate_status == "PASS"
