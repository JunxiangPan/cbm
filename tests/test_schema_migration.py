"""0.1.1 reports remain readable under the frozen v1 schema."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_011_report_matches_v1_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    report = json.loads((ROOT / "release/0.1.1/smoke/verify-report.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas/cbm-report-v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(report, schema)
    assert report["schema_version"] == "1"
    assert "artifact_type" not in report


def test_v2_schema_is_distinct_and_requires_new_fields() -> None:
    schema = json.loads((ROOT / "schemas/cbm-report.schema.json").read_text(encoding="utf-8"))
    v1 = json.loads((ROOT / "schemas/cbm-report-v1.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["schema_version"]["const"] == "2"
    assert v1["properties"]["schema_version"]["const"] == "1"
    assert "artifact_type" in schema["required"]
    assert "artifact_type" not in v1["required"]
