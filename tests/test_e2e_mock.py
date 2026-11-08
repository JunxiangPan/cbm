"""Mock end-to-end: verify -> upload -> finalize, with no network."""
from __future__ import annotations

from pathlib import Path

from cbm_attach import body, cli

from tests.helpers import (
    MockUploader,
    make_artifact,
    make_cbe,
    make_cbp,
    read_json,
    upload_args,
    verify_args,
    write_json,
)


def _finalize_args(
    input_dir: Path,
    output: Path,
    body_path: Path,
    *,
    declared: str = "true",
    upload_result: str = "failure",
) -> list[str]:
    return [
        "finalize",
        "--input",
        str(input_dir),
        "--output",
        str(output),
        "--body",
        str(body_path),
        "--declared-attached",
        declared,
        "--version",
        "v0.1.0",
        "--tag",
        "v0.1.0",
        "--release-tag",
        "v1.7.0",
        "--upload-result",
        upload_result,
        "--now",
        "2026-11-08T12:10:00Z",
    ]


def test_end_to_end_verify_upload_finalize(tmp_path: Path, monkeypatch) -> None:
    root, _wheel, digest = make_artifact(tmp_path)
    argv, report_path, verify_body, decision_path = verify_args(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert cli.main(argv) == 0
    verify_report = read_json(report_path)
    assert verify_report["reason"] == "UPLOAD_PENDING"
    assert "CBM: NOT_UPLOADED" in verify_body.read_text(encoding="utf-8")

    mock = MockUploader()
    monkeypatch.setattr(cli, "load_uploader", lambda *args, **kwargs: mock)
    upload_argv, final_report_path, final_body_path = upload_args(
        tmp_path,
        report=report_path,
        decision=decision_path,
        artifact_root=root,
    )
    assert cli.main(upload_argv) == 0
    final = read_json(final_report_path)
    assert final["cbm_gate_status"] == "PASS"
    assert final["upload_status"] == "UPLOADED_VERIFIED"
    assert final["uploaded_asset_digest"] == digest
    assert mock.upload_calls == 1
    assert "UPLOADED_VERIFIED" in final_body_path.read_text(encoding="utf-8")

    finalize_output = tmp_path / "finalized" / "cbm-report.json"
    finalize_body = tmp_path / "finalized" / "cbm-body.md"
    assert (
        cli.main(
            _finalize_args(
                tmp_path / "final",
                finalize_output,
                finalize_body,
                upload_result="success",
            )
        )
        == 0
    )
    assert read_json(finalize_output)["upload_status"] == "UPLOADED_VERIFIED"
    assert "UPLOADED_VERIFIED" in finalize_body.read_text(encoding="utf-8")


def test_gate_failure_never_uploads(tmp_path: Path, monkeypatch) -> None:
    root, _wheel, digest = make_artifact(tmp_path)
    argv, report_path, _body_path, decision_path = verify_args(
        tmp_path,
        cbe=make_cbe(gate_status="FAIL", exit_code=3),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert cli.main(argv) == 3
    assert read_json(decision_path)["decision"] == "NO_UPLOAD"

    mock = MockUploader()
    monkeypatch.setattr(cli, "load_uploader", lambda *args, **kwargs: mock)
    upload_argv, _final_report, _final_body = upload_args(
        tmp_path,
        report=report_path,
        decision=decision_path,
        artifact_root=root,
    )
    assert cli.main(upload_argv) == 3
    assert mock.calls == []


def test_finalize_without_report_is_skipped_infra(tmp_path: Path) -> None:
    output = tmp_path / "out" / "cbm-report.json"
    body_path = tmp_path / "out" / "cbm-body.md"
    code = cli.main(
        _finalize_args(tmp_path / "empty", output, body_path, declared="true")
    )
    assert code == 0
    report = read_json(output)
    assert report["cbm_gate_status"] == "SKIPPED_INFRA"
    assert report["reason"] == "WORKFLOW_FAILED_BEFORE_EVIDENCE"
    assert report["upload_status"] == "NOT_UPLOADED"
    assert "## Infrastructure failures" in body_path.read_text(encoding="utf-8")
    assert body.P2_04_PHRASE in body_path.read_text(encoding="utf-8")


def test_finalize_after_failed_upload_rewrites_pending(tmp_path: Path) -> None:
    root, _wheel, digest = make_artifact(tmp_path)
    argv, report_path, _verify_body, _decision = verify_args(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert cli.main(argv) == 0
    assert read_json(report_path)["reason"] == "UPLOAD_PENDING"

    output = tmp_path / "finalized" / "cbm-report.json"
    body_path = tmp_path / "finalized" / "cbm-body.md"
    assert (
        cli.main(
            _finalize_args(
                report_path.parent,
                output,
                body_path,
                upload_result="failure",
            )
        )
        == 0
    )
    report = read_json(output)
    assert report["cbm_gate_status"] == "FAIL"
    assert report["reason"] == "UPLOAD_FAILED"
    assert report["upload_status"] == "NOT_UPLOADED"


def test_finalize_rejects_pass_without_upload(tmp_path: Path) -> None:
    report = {
        "schema_version": "1",
        "package_id": "cbm",
        "version": "v0.1.0",
        "tag": "v0.1.0",
        "release_tag": "v1.7.0",
        "cbm_gate_status": "PASS",
        "exit_code": 0,
        "cbe_report_hash": None,
        "cbp_report_hash": None,
        "upload_status": "NOT_UPLOADED",
        "reason": "UPLOAD_PENDING",
        "reason_detail": "",
        "declared_attached": True,
        "upstream_gate_status": {"cbe": None, "cbp": None},
        "artifact_name": "cbm-0.1.0-py3-none-any.whl",
        "artifact_sha256": "a" * 64,
        "cbp_artifact_sha256": "a" * 64,
        "build_once_run_id": "1",
        "ci_commit_sha": None,
        "upload_target": "github-release",
        "uploaded_asset_url": None,
        "uploaded_asset_digest": None,
        "verified_at": "2026-11-08T12:00:00Z",
    }
    sealed = cli._seal(report)
    write_json(tmp_path / "evidence" / "cbm-report.final.json", sealed)

    output = tmp_path / "out" / "cbm-report.json"
    body_path = tmp_path / "out" / "cbm-body.md"
    assert (
        cli.main(
            _finalize_args(
                tmp_path / "evidence",
                output,
                body_path,
                upload_result="success",
            )
        )
        == 0
    )
    final = read_json(output)
    assert final["cbm_gate_status"] == "FAIL"
    assert final["reason"] == "EVIDENCE_INVALID"
    assert final["upload_status"] == "NOT_UPLOADED"


def test_finalize_exports_github_outputs(tmp_path: Path, monkeypatch) -> None:
    output_file = tmp_path / "github-output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    output = tmp_path / "out" / "cbm-report.json"
    body_path = tmp_path / "out" / "cbm-body.md"
    assert cli.main(_finalize_args(tmp_path / "empty", output, body_path)) == 0
    text = output_file.read_text(encoding="utf-8")
    assert "cbm_gate_status=SKIPPED_INFRA" in text
    assert "upload_status=NOT_UPLOADED" in text
    assert "cbe_report_hash=\n" in text


def test_verify_missing_input_writes_evidence(tmp_path: Path) -> None:
    output = tmp_path / "out" / "cbm-report.json"
    body_path = tmp_path / "out" / "cbm-body.md"
    decision = tmp_path / "out" / "cbm-decision.json"
    code = cli.main(
        [
            "verify",
            "--output",
            str(output),
            "--body",
            str(body_path),
            "--decision",
            str(decision),
        ]
    )
    assert code == 2
    report = read_json(output)
    assert report["cbm_gate_status"] == "PRECONDITION_FAIL"
    assert report["reason"] == "MISSING_ARGUMENT"
    assert body_path.is_file()
    assert decision.is_file()
