"""in-toto Statement and generic evidence adapter tests."""
from __future__ import annotations

import json
from pathlib import Path

from cbm_attach import cli
from cbm_attach.evidence import identity_errors_for, load_evidence
from cbm_attach.intoto import PREDICATE_TYPE, STATEMENT_TYPE, build_statement

from tests.helpers import (
    make_artifact,
    make_cbe,
    make_cbp,
    read_json,
    verify_args,
    write_json,
)


def test_verify_writes_in_toto_statement(tmp_path: Path) -> None:
    root, _, digest = make_artifact(tmp_path)
    argv, report_path, _, _ = verify_args(
        tmp_path,
        cbe=make_cbe(),
        cbp=make_cbp(digest),
        artifact_root=root,
    )
    assert cli.main(argv) == 0
    statement_path = report_path.with_name(report_path.stem + ".statement.json")
    statement = read_json(statement_path)
    report = read_json(report_path)
    assert statement["_type"] == STATEMENT_TYPE
    assert statement["predicateType"] == PREDICATE_TYPE
    assert statement["subject"][0]["digest"]["sha256"] == digest
    assert statement["predicate"]["report"]["artifact_sha256"] == digest
    assert report["evidence_sha256"] == statement["predicate"]["report"]["evidence_sha256"]


def test_statement_command_reads_report(tmp_path: Path) -> None:
    report = {
        "artifact_name": "x.whl",
        "artifact_sha256": "a" * 64,
        "cbm_gate_status": "PASS",
        "upload_status": "NOT_UPLOADED",
    }
    source = write_json(tmp_path / "report.json", report)
    output = tmp_path / "out.json"
    assert cli.main(["statement", "--report", str(source), "--output", str(output)]) == 0
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["predicateType"] == PREDICATE_TYPE
    assert written["subject"][0]["name"] == "x.whl"


def test_generic_evidence_identity_is_not_hardcoded_to_cbm(tmp_path: Path) -> None:
    cbe = load_evidence(write_json(tmp_path / "cbe.json", make_cbe(package_id="demo")), "cbe")
    cbp = load_evidence(write_json(tmp_path / "cbp.json", make_cbp("a" * 64, package_id="demo")), "cbp")
    assert identity_errors_for(
        [cbe, cbp], subject_package_id="demo", producers={"cbe", "cbp"}
    ) == []
    errors = identity_errors_for(
        [cbe, cbp], subject_package_id="other", producers={"cbe", "cbp"}
    )
    assert len(errors) == 2
    assert cbe.sha256 and cbp.sha256
