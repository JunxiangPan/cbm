"""Optional semantic-verdict/v1 sidecar attachment.

This module only loads, validates and copies an external verdict. It never runs
a semantic model and never imports CBF, CBP or CBE. The verdict is a standalone
artifact; the CBM 0.1.1/0.2.0 sidecar report contract is unchanged.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SEMANTIC_SCHEMA = "semantic-verdict/v1"
ATTACHMENT_SCHEMA = "cbm-semantic-attachment/v1"
HEX64 = re.compile(r"^[a-fA-F0-9]{64}$")
VERDICTS = {"PASS", "FAIL", "NOT_RUN"}


class SemanticVerdictError(ValueError):
    """Raised when a semantic verdict is missing, malformed or tampered."""


def canonical_semantic_sha256(data: dict[str, Any]) -> str:
    body = {key: value for key, value in data.items() if key != "evidence_sha256"}
    payload = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_semantic(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["semantic verdict must be a JSON object"]
    if data.get("schema") != SEMANTIC_SCHEMA:
        errors.append(f"schema must be {SEMANTIC_SCHEMA!r}")
    if data.get("verdict") not in VERDICTS:
        errors.append("verdict must be PASS, FAIL or NOT_RUN")
    subject = data.get("subject")
    if not isinstance(subject, dict):
        errors.append("subject must be an object")
    else:
        if not isinstance(subject.get("package_id"), str) or not subject["package_id"]:
            errors.append("subject.package_id is required")
        if not isinstance(subject.get("artifact_sha256"), str) or not HEX64.fullmatch(subject["artifact_sha256"]):
            errors.append("subject.artifact_sha256 must be a 64-hex string")
    if not isinstance(data.get("generated_at"), str) or not data["generated_at"]:
        errors.append("generated_at is required")
    declared = data.get("evidence_sha256")
    if not isinstance(declared, str) or not HEX64.fullmatch(declared):
        errors.append("evidence_sha256 must be a 64-hex string")
    elif declared.lower() != canonical_semantic_sha256(data):
        errors.append("evidence_sha256 does not match canonical semantic verdict JSON")
    if "findings" in data and not isinstance(data["findings"], list):
        errors.append("findings must be an array when present")
    return errors


@dataclass(frozen=True)
class SemanticVerdict:
    path: Path
    data: dict[str, Any]
    sha256: str

    @property
    def verdict(self) -> str:
        return str(self.data["verdict"])

    @property
    def subject(self) -> dict[str, Any]:
        return dict(self.data["subject"])


def load_semantic(path: str | Path) -> SemanticVerdict:
    source = Path(path)
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise SemanticVerdictError(f"{source}: cannot read semantic verdict: {exc}") from exc
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise SemanticVerdictError(f"{source}: invalid semantic verdict JSON: {exc}") from exc
    errors = validate_semantic(data)
    if errors:
        raise SemanticVerdictError(f"{source}: " + "; ".join(errors))
    return SemanticVerdict(path=source, data=data, sha256=canonical_semantic_sha256(data))


def attach_semantic(verdict_path: str | Path, output_dir: str | Path) -> tuple[Path, Path]:
    """Copy a verified verdict and write a standalone attachment manifest."""
    verdict = load_semantic(verdict_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    verdict_copy = output / "semantic-verdict.json"
    verdict_copy.write_bytes(verdict.path.read_bytes())
    manifest = {
        "schema": ATTACHMENT_SCHEMA,
        "semantic_verdict": verdict_copy.name,
        "semantic_verdict_sha256": verdict.sha256,
        "raw_sha256": hashlib.sha256(verdict_copy.read_bytes()).hexdigest(),
        "verdict": verdict.verdict,
        "subject": verdict.subject,
    }
    manifest_path = output / "semantic-attachment.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return verdict_copy, manifest_path
