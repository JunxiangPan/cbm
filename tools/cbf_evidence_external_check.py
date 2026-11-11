"""External CBF evidence attachment check using released cbm-attach 0.2.0.

This is not a CBF gate and does not run a semantic model. It only exercises the
0.2.0 generic evidence adapter/identity interface and records the real result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from cbm_attach.evidence import EvidenceInput, identity_errors_for, register_adapter


def _load(path: Path) -> EvidenceInput:
    data = json.loads(path.read_bytes().decode("utf-8-sig"))
    return EvidenceInput(
        kind="cbf",
        path=path,
        package_id=str(data.get("project", "")),
        producer_id=str(data.get("tool", "")) or None,
        version=str(data.get("version", "")),
        tag=None,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        data=data,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    path = Path(args.evidence)
    register_adapter("cbf", _load)
    item = _load(path)
    schema_ok = item.data.get("schema") == "cbf-evidence/v1"
    identity = identity_errors_for([item], subject_package_id=item.package_id, producers={"cbf"})
    result = {
        "tool": "cbm-attach",
        "version": "0.2.0",
        "evidence": str(path),
        "evidence_schema": item.data.get("schema"),
        "source_result": item.data.get("result"),
        "evidence_sha256": item.data.get("evidence_sha256"),
        "raw_sha256": item.sha256,
        "subject": {"package_id": item.package_id, "producer_id": item.producer_id, "version": item.version},
        "checks": {
            "schema_read": "PASS" if schema_ok else "FAIL",
            "generic_attachment_read": "PASS",
            "identity": "PASS" if not identity else "FAIL",
            "cbf_gate": "NOT_RUN",
            "semantic_model": "NOT_RUN",
            "hash_verification": "NOT_RUN",
        },
        "notes": [
            "CBF gate was not run; CBF 0.1.0 is not released.",
            "No semantic model was run.",
            "The cbf-evidence/v1 source_result is reported separately and is not a CBM CBF PASS.",
        ],
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if all(v != "FAIL" for v in result["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
