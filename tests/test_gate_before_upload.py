"""P2-02: no upload may occur unless CBE and CBP both passed."""
from __future__ import annotations

import json
from pathlib import Path

from cbm_attach import cli

from tests.helpers import (
    MockUploader,
    make_artifact,
    make_cbe,
    make_cbp,
    read_json,
    upload_args,
    verify_args,
)


def _verify(tmp_path: Path, *, cbe=None, cbp=None):
    root, wheel, digest = make_artifact(tmp_path)
    argv, report, _body, decision = verify_args(
        tmp_path,
        cbe=make_cbe() if cbe is None else cbe,
        cbp=make_cbp(digest) if cbp is None else cbp,
        artifact_root=root,
    )
    code = cli.main(argv)
    return code, root, wheel, report, decision


def _upload(tmp_path: Path, root: Path, report: Path, decision: Path, monkeypatch, mock):
    monkeypatch.setattr(cli, "load_uploader", lambda *args, **kwargs: mock)
    argv, final_report, final_body = upload_args(
        tmp_path,
        report=report,
        decision=decision,
        artifact_root=root,
    )
    code = cli.main(argv)
    return code, read_json(final_report), final_body.read_text(encoding="utf-8")


def test_gate_failure_never_loads_the_uploader(tmp_path: Path, monkeypatch) -> None:
    code, root, _wheel, report_path, decision_path = _verify(
        tmp_path,
        cbe=make_cbe(gate_status="FAIL", exit_code=3),
    )
    assert code == 3
    assert read_json(decision_path)["decision"] == "NO_UPLOAD"

    mock = MockUploader()
    code, final, body_text = _upload(
        tmp_path, root, report_path, decision_path, monkeypatch, mock
    )
    assert code == 3
    assert mock.calls == []
    assert mock.upload_calls == 0
    assert final["cbm_gate_status"] == "FAIL"
    assert final["upload_status"] == "NOT_UPLOADED"
    assert "CBM: PASS" not in body_text


def test_no_upload_decision_refuses_before_uploader(tmp_path: Path, monkeypatch) -> None:
    code, root, _wheel, report_path, decision_path = _verify(tmp_path)
    assert code == 0
    decision = read_json(decision_path)
    decision["decision"] = "NO_UPLOAD"
    decision_path.write_text(json.dumps(decision), encoding="utf-8")

    mock = MockUploader()
    code, final, _ = _upload(
        tmp_path, root, report_path, decision_path, monkeypatch, mock
    )
    assert code == 3
    assert mock.calls == []
    assert final["reason"] == "UPLOAD_NOT_APPROVED"


def test_tampered_artifact_is_refused_before_uploader(tmp_path: Path, monkeypatch) -> None:
    code, root, wheel, report_path, decision_path = _verify(tmp_path)
    assert code == 0
    wheel.write_bytes(b"tampered after approval\n")

    mock = MockUploader()
    code, final, _ = _upload(
        tmp_path, root, report_path, decision_path, monkeypatch, mock
    )
    assert code == 3
    assert mock.calls == []
    assert final["reason"] == "ARTIFACT_HASH_MISMATCH"


def test_upload_happens_only_after_approval(tmp_path: Path, monkeypatch) -> None:
    code, root, _wheel, report_path, decision_path = _verify(tmp_path)
    assert code == 0

    mock = MockUploader()
    code, final, body_text = _upload(
        tmp_path, root, report_path, decision_path, monkeypatch, mock
    )
    assert code == 0
    assert mock.upload_calls == 1
    assert final["cbm_gate_status"] == "PASS"
    assert final["upload_status"] == "UPLOADED_VERIFIED"
    assert final["uploaded_asset_digest"] == final["artifact_sha256"]
    assert "UPLOADED_VERIFIED" in body_text
    assert "cbm_gate_status: `PASS`" in body_text


def test_same_digest_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    code, root, _wheel, report_path, decision_path = _verify(tmp_path)
    assert code == 0
    report = read_json(report_path)

    mock = MockUploader(existing={report["artifact_name"]: report["artifact_sha256"]})
    code, final, _ = _upload(
        tmp_path, root, report_path, decision_path, monkeypatch, mock
    )
    assert code == 0
    assert mock.upload_calls == 0
    assert final["cbm_gate_status"] == "PASS"
    assert final["upload_status"] == "UPLOADED_VERIFIED"


def test_conflicting_digest_is_not_overwritten(tmp_path: Path, monkeypatch) -> None:
    code, root, _wheel, report_path, decision_path = _verify(tmp_path)
    assert code == 0
    report = read_json(report_path)

    mock = MockUploader(existing={report["artifact_name"]: "f" * 64})
    code, final, body_text = _upload(
        tmp_path, root, report_path, decision_path, monkeypatch, mock
    )
    assert code == 3
    assert mock.upload_calls == 0
    assert final["reason"] == "ASSET_DIGEST_CONFLICT"
    assert "CBM: PASS" not in body_text


def test_tampered_report_is_refused_before_uploader(tmp_path: Path, monkeypatch) -> None:
    code, root, _wheel, report_path, decision_path = _verify(tmp_path)
    assert code == 0
    report = read_json(report_path)
    report["reason_detail"] = "tampered after approval"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    mock = MockUploader()
    code, final, _ = _upload(
        tmp_path, root, report_path, decision_path, monkeypatch, mock
    )
    assert code == 3
    assert mock.calls == []
    assert final["reason"] == "EVIDENCE_INVALID"


def test_decision_must_be_bound_to_the_report(tmp_path: Path, monkeypatch) -> None:
    code, root, _wheel, report_path, decision_path = _verify(tmp_path)
    assert code == 0
    decision = read_json(decision_path)
    decision["report_sha256"] = "0" * 64
    decision_path.write_text(json.dumps(decision), encoding="utf-8")

    mock = MockUploader()
    code, final, _ = _upload(
        tmp_path, root, report_path, decision_path, monkeypatch, mock
    )
    assert code == 3
    assert mock.calls == []
    assert final["reason"] == "EVIDENCE_INVALID"
