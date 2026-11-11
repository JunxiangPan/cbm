"""Optional semantic-verdict/v1 attachment and verification."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cbm_attach import cli
from cbm_attach.semantic import (
    SemanticVerdictError,
    attach_semantic,
    canonical_semantic_sha256,
    load_semantic,
    validate_semantic,
)


def _verdict() -> dict:
    data = {
        "schema": "semantic-verdict/v1",
        "verdict": "NOT_RUN",
        "subject": {"package_id": "cbm", "version": "0.2.0", "artifact_sha256": "a" * 64},
        "generated_at": "2026-11-12T00:00:00Z",
        "findings": [],
    }
    data["evidence_sha256"] = canonical_semantic_sha256(data)
    return data


def _write(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "semantic.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_semantic_verdict_validates_schema_and_hash(tmp_path: Path) -> None:
    data = _verdict()
    path = _write(tmp_path, data)
    verdict = load_semantic(path)
    assert verdict.verdict == "NOT_RUN"
    assert verdict.sha256 == data["evidence_sha256"]
    assert validate_semantic(data) == []


def test_semantic_verdict_tamper_or_schema_is_rejected(tmp_path: Path) -> None:
    data = _verdict()
    data["verdict"] = "PASS"
    with pytest.raises(SemanticVerdictError):
        load_semantic(_write(tmp_path, data))
    bad = _verdict()
    bad["schema"] = "semantic-verdict/v2"
    bad["evidence_sha256"] = canonical_semantic_sha256(bad)
    with pytest.raises(SemanticVerdictError):
        load_semantic(_write(tmp_path, bad))


def test_attach_semantic_writes_standalone_attachment(tmp_path: Path) -> None:
    verdict_path = _write(tmp_path, _verdict())
    copy, manifest = attach_semantic(verdict_path, tmp_path / "out")
    assert copy.read_bytes() == verdict_path.read_bytes()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["schema"] == "cbm-semantic-attachment/v1"
    assert data["semantic_verdict_sha256"] == _verdict()["evidence_sha256"]
    assert data["verdict"] == "NOT_RUN"


def test_semantic_cli_verify_and_attach(tmp_path: Path) -> None:
    path = _write(tmp_path, _verdict())
    assert cli.main(["verify-semantic", "--verdict", str(path)]) == 0
    assert cli.main(["attach-semantic", "--verdict", str(path), "--output-dir", str(tmp_path / "o")]) == 0
    assert (tmp_path / "o" / "semantic-verdict.json").is_file()
    assert (tmp_path / "o" / "semantic-attachment.json").is_file()


def test_semantic_module_does_not_import_cbe_cbp_cbf() -> None:
    text = (Path(__file__).resolve().parents[1] / "src/cbm_attach/semantic.py").read_text(encoding="utf-8")
    assert "import cbe" not in text
    assert "import cbp" not in text
    assert "import cbf" not in text


def test_semantic_verdict_matches_schema() -> None:
    import json
    import pytest
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/semantic-verdict-v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(_verdict(), schema)
