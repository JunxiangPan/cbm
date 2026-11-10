"""in-toto Statement output for the CBM sidecar attachment predicate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PREDICATE_TYPE = "https://cbm.dev/attachment/v1"
STATEMENT_TYPE = "https://in-toto.io/Statement/v1"


def build_statement(report: dict[str, Any]) -> dict[str, Any]:
    """Build a v1 in-toto Statement while preserving the CBM report fields."""
    name = report.get("artifact_name") or "cbm-attach"
    digest = report.get("artifact_sha256")
    subject = []
    if isinstance(digest, str) and len(digest) == 64:
        subject.append({"name": name, "digest": {"sha256": digest}})
    predicate = {
        "scope": "sidecar attachment",
        "cbm_gate_status": report.get("cbm_gate_status"),
        "upload_status": report.get("upload_status"),
        "reason": report.get("reason"),
        "reason_detail": report.get("reason_detail"),
        "report": report,
    }
    return {
        "_type": STATEMENT_TYPE,
        "subject": subject,
        "predicateType": PREDICATE_TYPE,
        "predicate": predicate,
    }


def write_statement(report: dict[str, Any], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_statement(report), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
