"""Pluggable evidence adapter test with no CBE/CBP import."""
from __future__ import annotations

import json
from pathlib import Path

from cbm_attach.evidence import EvidenceInput, load_generic, register_adapter


def _demo(path: str | Path) -> EvidenceInput:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return EvidenceInput(
        kind="demo", path=p, package_id=data["subject"], producer_id=data.get("producer"),
        version=data["version"], tag=data.get("tag"), sha256="a" * 64, data=data,
    )


def test_pluggable_adapter_does_not_require_cbe_or_cbp(tmp_path: Path) -> None:
    p = tmp_path / "demo.json"
    p.write_text(json.dumps({"subject": "anything", "producer": "demo", "version": "v9"}), encoding="utf-8")
    register_adapter("demo", _demo)
    item = load_generic(p, "demo")
    assert item.kind == "demo"
    assert item.package_id == "anything"
    assert item.producer_id == "demo"
