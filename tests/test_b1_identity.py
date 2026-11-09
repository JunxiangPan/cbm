"""B1 consumer readiness: §5.1 subject/producer identity.

These tests prove the consumer rules for the future reports; they do **not**
claim B1 is applied or that real CBM-scoped reports exist. B1 remains blocked on
CONTRACT.md §5.1 and CBE/CBP implementation.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cbm_attach import cli
from cbm_attach.reports import identity_errors, load_report

from tests.helpers import (
    make_artifact,
    make_cbe,
    make_cbp,
    read_json,
    verify_args,
    write_json,
)


def _reports(tmp_path: Path, cbe_data: dict, cbp_data: dict):
    cbe = load_report(write_json(tmp_path / "cbe.json", cbe_data), "cbe")
    cbp = load_report(write_json(tmp_path / "cbp.json", cbp_data), "cbp")
    return cbe, cbp


def test_b1_subject_and_producer_identity_are_accepted(tmp_path: Path) -> None:
    cbe, cbp = _reports(tmp_path, make_cbe(), make_cbp("a" * 64))
    assert identity_errors(cbe, cbp, version="v0.1.0", tag="v0.1.0") == []
    assert cbe.package_id == "cbm" and cbe.producer_id == "cbe"
    assert cbp.package_id == "cbm" and cbp.producer_id == "cbp"


@pytest.mark.parametrize(
    ("cbe_patch", "cbp_patch"),
    [
        ({"package_id": "cbe"}, {}),
        ({}, {"package_id": "cbp"}),
    ],
)
def test_b1_old_package_id_mixed_reports_are_rejected(
    tmp_path: Path, cbe_patch: dict, cbp_patch: dict
) -> None:
    cbe, cbp = _reports(
        tmp_path,
        make_cbe(**cbe_patch),
        make_cbp("a" * 64, **cbp_patch),
    )
    errors = identity_errors(cbe, cbp, version="v0.1.0", tag="v0.1.0")
    assert any("package_id" in error for error in errors)


def test_b1_cbe_producer_id_mismatch_is_rejected(tmp_path: Path) -> None:
    cbe, cbp = _reports(
        tmp_path,
        make_cbe(producer_id="cbp"),
        make_cbp("a" * 64),
    )
    errors = identity_errors(cbe, cbp, version="v0.1.0", tag="v0.1.0")
    assert any("CBE producer_id" in error for error in errors)


def test_b1_cbp_producer_id_mismatch_is_rejected(tmp_path: Path) -> None:
    cbe, cbp = _reports(
        tmp_path,
        make_cbe(),
        make_cbp("a" * 64, producer_id="cbe"),
    )
    errors = identity_errors(cbe, cbp, version="v0.1.0", tag="v0.1.0")
    assert any("CBP producer_id" in error for error in errors)


def test_b1_mixed_reports_exit_3_report_identity_mismatch(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    argv, report_path, _body, decision_path = verify_args(
        tmp_path,
        cbe=make_cbe(package_id="cbe", producer_id="cbe"),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    code = cli.main(argv)
    report = read_json(report_path)
    assert code == 3
    assert report["cbm_gate_status"] == "FAIL"
    assert report["reason"] == "REPORT_IDENTITY_MISMATCH"
    assert report["upload_status"] == "NOT_UPLOADED"
    assert read_json(decision_path)["decision"] == "NO_UPLOAD"
