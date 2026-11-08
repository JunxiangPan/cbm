"""Keep the CBM report schema, the CLI writer and the reason enum in lockstep."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cbm_attach import cli
from cbm_attach.reasons import CBM_GATE_STATUSES, UPLOAD_STATUSES, Reason


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "cbm-report.schema.json"


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_report_keys_match_schema_required_and_properties() -> None:
    report = cli._seal(cli._report_dict(cli.ReportContext(now="2026-11-08T12:00:00Z")))
    schema = _schema()
    assert set(report) == set(schema["required"])
    assert all(key in schema["properties"] for key in report)
    assert schema["additionalProperties"] is False


def test_every_reason_value_is_in_the_schema_enum() -> None:
    schema = _schema()
    assert {reason.value for reason in Reason} <= set(schema["properties"]["reason"]["enum"])


def test_status_enums_are_in_lockstep() -> None:
    schema = _schema()
    assert CBM_GATE_STATUSES <= set(schema["properties"]["cbm_gate_status"]["enum"])
    assert UPLOAD_STATUSES <= set(schema["properties"]["upload_status"]["enum"])


def test_package_id_is_cbm() -> None:
    assert _schema()["properties"]["package_id"]["const"] == "cbm"


def test_generated_reports_validate_against_the_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = _schema()
    for context in (
        cli.ReportContext(now="2026-11-08T12:00:00Z"),
        cli.ReportContext(
            now="2026-11-08T12:00:00Z",
            version="v0.1.0",
            tag="v0.1.0",
            release_tag="v1.7.0",
            cbm_gate_status="FAIL",
            exit_code=3,
            upload_status="NOT_UPLOADED",
            reason="CBE_NOT_PASS",
            declared_attached=True,
            upload_target="github-release",
        ),
        cli.ReportContext(
            now="2026-11-08T12:00:00Z",
            version="v0.1.0",
            tag="v0.1.0",
            release_tag="v1.7.0",
            cbm_gate_status="PASS",
            exit_code=0,
            upload_status="UPLOADED_VERIFIED",
            reason="UPLOADED_VERIFIED",
            declared_attached=True,
            upload_target="github-release",
            uploaded_asset_digest="a" * 64,
        ),
    ):
        report = cli._seal(cli._report_dict(context))
        jsonschema.validate(report, schema)
