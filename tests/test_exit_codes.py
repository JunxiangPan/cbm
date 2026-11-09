"""Exit-code and status mapping tests (F1/F2/F3/F6)."""
from __future__ import annotations

from pathlib import Path

from cbm_attach import cli

from tests.helpers import (
    WHEEL_NAME,
    make_artifact,
    make_cbe,
    make_cbp,
    read_json,
    verify_args,
    write_json,
)


def _run(tmp_path: Path, **kwargs):
    argv, report_path, body_path, decision_path = verify_args(tmp_path, **kwargs)
    code = cli.main(argv)
    return code, read_json(report_path), body_path.read_text(encoding="utf-8"), read_json(decision_path)


def test_pass_authorises_upload_but_does_not_claim_pass(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, body_text, decision = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert code == 0
    assert decision["decision"] == "UPLOAD"
    assert report["cbm_gate_status"] == "NOT_UPLOADED"
    assert report["upload_status"] == "NOT_UPLOADED"
    assert report["reason"] == "UPLOAD_PENDING"
    assert report["cbe_report_hash"] is not None
    assert report["cbp_report_hash"] is not None
    assert "CBM: PASS" not in body_text
    assert "CBM: NOT_UPLOADED" in body_text


def test_cbe_fail_exits_3_and_never_authorises(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, body_text, decision = _run(
        tmp_path,
        cbe=make_cbe(gate_status="FAIL", exit_code=3),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert code == 3
    assert decision["decision"] == "NO_UPLOAD"
    assert report["cbm_gate_status"] == "FAIL"
    assert report["upload_status"] == "NOT_UPLOADED"
    assert report["reason"] == "CBE_NOT_PASS"
    assert "declared as attached but not uploaded" in body_text


def test_cbp_fail_exits_3(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, decision = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp(digest, gate_status="FAIL"),
        artifact_root=root,
    )
    assert code == 3
    assert decision["decision"] == "NO_UPLOAD"
    assert report["reason"] == "CBP_NOT_PASS"


def test_upstream_skipped_infra_exits_3_with_infra_section(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, body_text, _ = _run(
        tmp_path,
        cbe=make_cbe(gate_status="SKIPPED_INFRA", exit_code=3),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert code == 3
    assert report["cbm_gate_status"] == "SKIPPED_INFRA"
    assert report["upload_status"] == "NOT_UPLOADED"
    assert "## Infrastructure failures" in body_text
    assert "SKIPPED_INFRA" in body_text


def test_skip_ratio_over_threshold_exits_4(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, decision = _run(
        tmp_path,
        cbe=make_cbe(
            applicable_count=100,
            skip_count=21,
            skip_ratio=0.21,
        ),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert code == 4
    assert decision["decision"] == "NO_UPLOAD"
    assert report["cbm_gate_status"] == "FAIL"
    assert report["reason"] == "SKIP_RATIO_EXCEEDED"


def test_blocking_skip_exits_3(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(blocking_skip=True),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert code == 3
    assert report["reason"] == "BLOCKING_SKIP"


def test_not_claimed_without_reports_exits_0(tmp_path: Path) -> None:
    code, report, body_text, decision = _run(
        tmp_path,
        cbe=None,
        cbp=None,
        artifact_root=None,
        declared="false",
    )
    assert code == 0
    assert decision["decision"] == "NO_UPLOAD"
    assert report["cbm_gate_status"] == "NOT_UPLOADED"
    assert report["upload_status"] == "NOT_UPLOADED"
    assert report["reason"] == "NOT_CLAIMED"
    assert report["cbe_report_hash"] is None
    assert report["cbp_report_hash"] is None
    assert "declared as attached but not uploaded" not in body_text
    assert "CBM: NOT_UPLOADED" in body_text


def test_identity_mismatch_exits_3(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, decision = _run(
        tmp_path,
        cbe=make_cbe(package_id="cbe"),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert code == 3
    assert decision["decision"] == "NO_UPLOAD"
    assert report["reason"] == "REPORT_IDENTITY_MISMATCH"


def test_pass_with_nonzero_exit_code_is_input_error(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(exit_code=3),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert code == 2
    assert report["cbm_gate_status"] == "PRECONDITION_FAIL"
    assert report["reason"] == "SCHEMA_VIOLATION"


def test_missing_cbe_report_claimed_exits_2(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, _ = _run(
        tmp_path,
        cbe=None,
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert code == 2
    assert report["cbm_gate_status"] == "PRECONDITION_FAIL"
    assert report["reason"] == "MISSING_CBE_REPORT"


def test_missing_declared_attached_exits_2(tmp_path: Path) -> None:
    code, report, _, _ = _run(
        tmp_path,
        cbe=None,
        cbp=None,
        artifact_root=None,
        declared="",
    )
    assert code == 2
    assert report["cbm_gate_status"] == "PRECONDITION_FAIL"
    assert report["reason"] == "MISSING_DECLARED_ATTACHED"


def test_cbp_artifact_hash_missing_exits_3(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    cbp = make_cbp(digest)
    cbp["artifact_hashes"] = {}
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=cbp,
        artifact_root=root,
    )
    assert code == 3
    assert report["reason"] == "CBP_ARTIFACT_HASH_MISSING"


def test_cbp_artifact_hash_mismatch_exits_3(tmp_path: Path) -> None:
    root, _, _ = make_artifact(tmp_path)
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp("e" * 64),
        artifact_root=root,
    )
    assert code == 3
    assert report["reason"] == "ARTIFACT_HASH_MISMATCH"


def test_invalid_json_exits_2(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    bad = tmp_path / "bad-cbe.json"
    bad.write_text("{not json", encoding="utf-8")
    argv, report_path, body_path, decision_path = verify_args(
        tmp_path,
        cbe=None,
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    argv += ["--cbe-report", str(bad)]
    code = cli.main(argv)
    report = read_json(report_path)
    assert code == 2
    assert report["reason"] == "INVALID_JSON"
    assert report_path.is_file()
    assert body_path.is_file()
    assert decision_path.is_file()


def test_cbp_top_level_pass_with_failed_gate_exits_3(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    cbp = make_cbp(digest)
    cbp["gates"][0]["status"] = "FAIL"
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=cbp,
        artifact_root=root,
    )
    assert code == 3
    assert report["reason"] == "CBP_NOT_PASS"


def test_cbp_blocking_gate_skipped_exits_3(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    cbp = make_cbp(digest)
    cbp["gates"][0] = {"name": "claims", "status": "SKIPPED", "reason": "n/a"}
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=cbp,
        artifact_root=root,
    )
    assert code == 3
    assert report["reason"] == "BLOCKING_SKIP"


def test_gate_status_skipped_is_schema_error(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(gate_status="SKIPPED"),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert code == 2
    assert report["reason"] == "SCHEMA_VIOLATION"


def test_claimed_without_artifact_exits_2(tmp_path: Path) -> None:
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp("a" * 64),
        artifact_root=None,
    )
    assert code == 2
    assert report["reason"] == "MISSING_BUILD_ONCE_ARTIFACT"


def test_cbp_identity_mismatch_exits_3(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, decision = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp(digest, package_id="cbp"),
        artifact_root=root,
    )
    assert code == 3
    assert decision["decision"] == "NO_UPLOAD"
    assert report["reason"] == "REPORT_IDENTITY_MISMATCH"


def test_producer_id_is_recorded_but_not_subject_identity(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert code == 0
    assert report["upstream_gate_status"]["cbe"]["producer_id"] == "cbe"
    assert report["upstream_gate_status"]["cbp"]["producer_id"] == "cbp"


def test_missing_producer_id_is_allowed(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    cbe = make_cbe()
    cbe.pop("producer_id")
    cbe.pop("producer_version")
    cbp = make_cbp(digest)
    cbp.pop("producer_id")
    cbp.pop("producer_version")
    code, report, _, _ = _run(
        tmp_path,
        cbe=cbe,
        cbp=cbp,
        artifact_root=root,
    )
    assert code == 0
    assert report["upstream_gate_status"]["cbe"]["producer_id"] is None
    assert report["upstream_gate_status"]["cbp"]["producer_id"] is None


def test_cbp_artifact_hash_with_dist_prefix_is_accepted(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    cbp = make_cbp(digest)
    cbp["artifact_hashes"] = {f"dist/{WHEEL_NAME}": digest}
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=cbp,
        artifact_root=root,
    )
    assert code == 0
    assert report["cbp_artifact_sha256"] == digest


def test_not_claimed_with_wrong_identity_reports_exits_3(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, decision = _run(
        tmp_path,
        cbe=make_cbe(package_id="cbe"),
        cbp=make_cbp(digest, package_id="cbp"),
        artifact_root=root,
        declared="false",
    )
    assert code == 3
    assert decision["decision"] == "NO_UPLOAD"
    assert report["cbm_gate_status"] == "FAIL"
    assert report["reason"] == "REPORT_IDENTITY_MISMATCH"


def test_not_claimed_with_valid_identity_reports_exits_0(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, decision = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp(digest),
        artifact_root=root,
        declared="false",
    )
    assert code == 0
    assert decision["decision"] == "NO_UPLOAD"
    assert report["reason"] == "NOT_CLAIMED"
    assert report["cbe_report_hash"] is not None
    assert report["cbp_report_hash"] is not None


def test_missing_release_body_hash_exits_2(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    cbp = make_cbp(digest)
    cbp.pop("release_body_hash")
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=cbp,
        artifact_root=root,
    )
    assert code == 2
    assert report["cbm_gate_status"] == "PRECONDITION_FAIL"
    assert report["reason"] == "MISSING_RELEASE_BODY_HASH"


def test_missing_body_hash_scope_exits_2(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    cbp = make_cbp(digest)
    cbp.pop("body_hash_scope")
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=cbp,
        artifact_root=root,
    )
    assert code == 2
    assert report["reason"] == "MISSING_BODY_HASH_SCOPE"


def test_full_body_hash_scope_exits_2(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp(digest, body_hash_scope="full"),
        artifact_root=root,
    )
    assert code == 2
    assert report["reason"] == "BODY_HASH_SCOPE_UNSUPPORTED"


def test_cbp_body_hash_fields_are_recorded(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert code == 0
    assert report["cbp_release_body_hash"] == "c" * 64
    assert report["cbp_body_hash_scope"] == "base"


def test_cbs_report_is_not_reused(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, decision = _run(
        tmp_path,
        cbe=make_cbe(package_id="cbs"),
        cbp=make_cbp(digest, package_id="cbs"),
        artifact_root=root,
    )
    assert code == 3
    assert decision["decision"] == "NO_UPLOAD"
    assert report["cbm_gate_status"] == "FAIL"
    assert report["reason"] == "REPORT_IDENTITY_MISMATCH"


def test_cross_repository_artifact_exits_2(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp(digest, artifact_repository="other/repo"),
        artifact_root=root,
    )
    assert code == 2
    assert report["cbm_gate_status"] == "PRECONDITION_FAIL"
    assert report["reason"] == "ARTIFACT_REPOSITORY_MISMATCH"


def test_missing_artifact_repository_exits_2(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    cbp = make_cbp(digest)
    cbp.pop("artifact_repository")
    code, report, _, _ = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=cbp,
        artifact_root=root,
    )
    assert code == 2
    assert report["reason"] == "ARTIFACT_REPOSITORY_MISMATCH"


def test_same_artifact_repository_continues(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    code, report, _, decision = _run(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert code == 0
    assert decision["decision"] == "UPLOAD"
    assert report["reason"] == "UPLOAD_PENDING"
    assert report["cbp_artifact_repository"] == "owner/repo"
