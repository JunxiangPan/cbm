"""Read CBE reports and CBP quality manifests without trusting them.

The report hash is always the SHA-256 of the *raw bytes* that were consumed.
It is not the report's own ``evidence_sha256`` field and it is not a
canonicalised JSON hash.  This distinction matters: ``evidence_sha256`` is
evidence produced by the upstream gate, while ``cbe_report_hash`` /
``cbp_report_hash`` prove exactly which document CBM read.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .reasons import InputError, Reason


VERSION_RE = re.compile(r"^v?[0-9]+\.[0-9]+\.[0-9]+$")
TAG_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
HEX64_RE = re.compile(r"^[a-fA-F0-9]{64}$")
STATUS_EXIT = {
    "PASS": {0},
    "FAIL": {3},
    "SKIPPED_INFRA": {3},
    "PRECONDITION_FAIL": {2, 3},
}

CBE_REQUIRED = (
    "schema_version",
    "package_id",
    "version",
    "tag",
    "gate_status",
    "exit_code",
    "applicable_count",
    "skip_count",
    "skip_ratio",
    "blocking_skip",
    "warn_count",
    "rules_manifest_hash",
    "sarif_paths",
    "evidence_sha256",
)

CBP_REQUIRED = (
    "schema_version",
    "package_id",
    "version",
    "gate_status",
    "applicable_gate_count",
    "skip_count",
    "skip_ratio",
    "blocking_skip",
    "gates",
    "artifact_hashes",
    "release_body_hash",
    "body_hash_scope",
    "evidence_sha256",
)


@dataclass(frozen=True)
class Report:
    kind: str
    path: Path
    raw: bytes
    data: dict[str, Any]
    sha256: str

    @property
    def package_id(self) -> str:
        return str(self.data.get("package_id", ""))

    @property
    def version(self) -> str:
        return str(self.data.get("version", ""))

    @property
    def gate_status(self) -> str:
        return str(self.data.get("gate_status", ""))

    @property
    def exit_code(self) -> int:
        value = self.data.get("exit_code", 0)
        return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0

    @property
    def skip_ratio(self) -> float:
        value = self.data.get("skip_ratio", 0.0)
        return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0

    @property
    def blocking_skip(self) -> bool:
        return self.data.get("blocking_skip") is True

    @property
    def producer_id(self) -> str | None:
        value = self.data.get("producer_id")
        return value if isinstance(value, str) and value else None

    @property
    def producer_version(self) -> str | None:
        value = self.data.get("producer_version")
        return value if isinstance(value, str) and value else None


def _is_hex64(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if value.startswith("sha256:"):
        value = value[len("sha256:") :]
    return bool(HEX64_RE.fullmatch(value))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require(data: dict[str, Any], key: str, errors: list[str]) -> Any:
    if key not in data:
        errors.append(f"{key}: missing")
        return None
    return data[key]


def _check_str(data: dict[str, Any], key: str, errors: list[str], *, allow_empty: bool = False) -> None:
    value = _require(data, key, errors)
    if value is None:
        return
    if not isinstance(value, str):
        errors.append(f"{key}: must be a string")
    elif not allow_empty and not value:
        errors.append(f"{key}: must not be empty")


def _check_int(data: dict[str, Any], key: str, errors: list[str], *, minimum: int | None = None) -> None:
    value = _require(data, key, errors)
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{key}: must be an integer")
    elif minimum is not None and value < minimum:
        errors.append(f"{key}: must be >= {minimum}")


def _check_bool(data: dict[str, Any], key: str, errors: list[str]) -> None:
    value = _require(data, key, errors)
    if value is not None and not isinstance(value, bool):
        errors.append(f"{key}: must be a boolean")


def _check_ratio(data: dict[str, Any], key: str, errors: list[str]) -> None:
    value = _require(data, key, errors)
    if value is None:
        return
    if not _is_number(value):
        errors.append(f"{key}: must be a number")
    elif not 0.0 <= float(value) <= 1.0:
        errors.append(f"{key}: must be between 0 and 1")


def _check_hex64(data: dict[str, Any], key: str, errors: list[str]) -> None:
    value = _require(data, key, errors)
    if value is not None and not _is_hex64(value):
        errors.append(f"{key}: must be 64 hex characters (an optional sha256: prefix is accepted)")


def _check_version(data: dict[str, Any], key: str, errors: list[str], pattern: re.Pattern[str]) -> None:
    value = _require(data, key, errors)
    if value is None:
        return
    if not isinstance(value, str) or not pattern.fullmatch(value):
        errors.append(f"{key}: must match {pattern.pattern}")


def _check_status_exit(data: dict[str, Any], errors: list[str], *, has_exit: bool) -> None:
    status = data.get("gate_status")
    if status not in STATUS_EXIT:
        errors.append("gate_status: must be PASS, FAIL, SKIPPED_INFRA, or PRECONDITION_FAIL")
        return
    if has_exit:
        exit_code = data.get("exit_code")
        if isinstance(exit_code, int) and not isinstance(exit_code, bool):
            if exit_code not in STATUS_EXIT[status]:
                errors.append(
                    f"exit_code: {exit_code} does not match gate_status {status}"
                )


def _check_counts(
    data: dict[str, Any],
    errors: list[str],
    *,
    applicable_key: str,
) -> None:
    applicable = data.get(applicable_key)
    skip_count = data.get("skip_count")
    skip_ratio = data.get("skip_ratio")
    if not isinstance(applicable, int) or isinstance(applicable, bool):
        return
    if applicable <= 0:
        errors.append(f"{applicable_key}: must be > 0 (F2/F3)")
        return
    if isinstance(skip_count, int) and not isinstance(skip_count, bool):
        if skip_count < 0:
            errors.append("skip_count: must be >= 0")
        elif skip_count > applicable:
            errors.append("skip_count: must not exceed the applicable count")
    if _is_number(skip_ratio) and isinstance(skip_count, int) and not isinstance(skip_count, bool):
        expected = skip_count / applicable
        if abs(float(skip_ratio) - expected) > 1e-6:
            errors.append(
                f"skip_ratio: {float(skip_ratio):.6f} does not match {skip_count}/{applicable}"
            )


def validate_cbe(data: Any) -> list[str]:
    """Return every structural error in a CBE report."""
    if not isinstance(data, dict):
        return ["report: must be a JSON object"]
    errors: list[str] = []
    for key in CBE_REQUIRED:
        _require(data, key, errors)
    if errors:
        return errors

    if data.get("schema_version") != "1":
        errors.append("schema_version: must be '1'")
    _check_str(data, "package_id", errors)
    _check_str(data, "version", errors)
    _check_version(data, "version", errors, VERSION_RE)
    _check_version(data, "tag", errors, TAG_RE)
    _check_status_exit(data, errors, has_exit=True)
    exit_code = data.get("exit_code")
    if (
        isinstance(exit_code, bool)
        or not isinstance(exit_code, int)
        or exit_code not in {0, 2, 3, 4}
    ):
        errors.append("exit_code: must be one of 0, 2, 3, 4")
    _check_int(data, "applicable_count", errors, minimum=0)
    _check_int(data, "skip_count", errors, minimum=0)
    _check_ratio(data, "skip_ratio", errors)
    _check_bool(data, "blocking_skip", errors)
    _check_int(data, "warn_count", errors, minimum=0)
    _check_hex64(data, "rules_manifest_hash", errors)
    _check_hex64(data, "evidence_sha256", errors)

    sarif_paths = data.get("sarif_paths")
    if not isinstance(sarif_paths, list) or any(not isinstance(item, str) for item in sarif_paths):
        errors.append("sarif_paths: must be a list of strings")

    if "producer_id" in data and not isinstance(data["producer_id"], str):
        errors.append("producer_id: must be a string when present")
    if "producer_version" in data and not isinstance(data["producer_version"], str):
        errors.append("producer_version: must be a string when present")

    _check_counts(data, errors, applicable_key="applicable_count")
    return errors


def validate_cbp(data: Any) -> list[str]:
    """Return every structural error in a CBP quality manifest."""
    if not isinstance(data, dict):
        return ["report: must be a JSON object"]
    errors: list[str] = []
    for key in CBP_REQUIRED:
        _require(data, key, errors)
    if errors:
        return errors

    if data.get("schema_version") != "1":
        errors.append("schema_version: must be '1'")
    _check_str(data, "package_id", errors)
    _check_str(data, "version", errors)
    _check_version(data, "version", errors, VERSION_RE)
    _check_status_exit(data, errors, has_exit=False)
    _check_int(data, "applicable_gate_count", errors, minimum=0)
    _check_int(data, "skip_count", errors, minimum=0)
    _check_ratio(data, "skip_ratio", errors)
    _check_bool(data, "blocking_skip", errors)
    _check_hex64(data, "release_body_hash", errors)
    _check_hex64(data, "evidence_sha256", errors)

    scope = data.get("body_hash_scope")
    if "body_hash_scope" not in data:
        errors.append("body_hash_scope: missing")
    elif not isinstance(scope, str):
        errors.append("body_hash_scope: must be a string")
    elif scope != "base":
        errors.append("body_hash_scope: only 'base' is supported")

    gates = data.get("gates")
    if not isinstance(gates, list):
        errors.append("gates: must be a list")
    else:
        for index, gate in enumerate(gates):
            if not isinstance(gate, dict):
                errors.append(f"gates[{index}]: must be an object")
                continue
            if not isinstance(gate.get("name"), str) or not gate.get("name"):
                errors.append(f"gates[{index}].name: must be a non-empty string")
            if gate.get("status") not in {"PASS", "FAIL", "SKIPPED"}:
                errors.append(f"gates[{index}].status: must be PASS, FAIL, or SKIPPED")
            if "reason" in gate and not isinstance(gate["reason"], str):
                errors.append(f"gates[{index}].reason: must be a string")

    hashes = data.get("artifact_hashes")
    if not isinstance(hashes, dict):
        errors.append("artifact_hashes: must be an object")
    else:
        for name, digest in hashes.items():
            if not isinstance(name, str) or not name:
                errors.append("artifact_hashes: keys must be non-empty strings")
            if not _is_hex64(digest):
                errors.append(f"artifact_hashes[{name!r}]: must be 64 hex characters")

    if "producer_id" in data and not isinstance(data["producer_id"], str):
        errors.append("producer_id: must be a string when present")
    if "producer_version" in data and not isinstance(data["producer_version"], str):
        errors.append("producer_version: must be a string when present")

    _check_counts(data, errors, applicable_key="applicable_gate_count")
    return errors


def parse_report_bytes(raw: bytes, *, kind: str, source: Path | str) -> Report:
    """Parse and validate already-downloaded report bytes."""
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError(
            f"{source}: invalid JSON: {exc}",
            reason=Reason.INVALID_JSON,
        ) from exc
    if kind == "cbp" and isinstance(data, dict):
        if not data.get("release_body_hash"):
            raise InputError(
                f"{source}: CBP quality manifest is missing release_body_hash",
                reason=Reason.MISSING_RELEASE_BODY_HASH,
            )
        scope = data.get("body_hash_scope")
        if scope is None or scope == "":
            raise InputError(
                f"{source}: CBP quality manifest is missing body_hash_scope",
                reason=Reason.MISSING_BODY_HASH_SCOPE,
            )
        if scope != "base":
            raise InputError(
                f"{source}: body_hash_scope={scope!r}; only 'base' is supported",
                reason=Reason.BODY_HASH_SCOPE_UNSUPPORTED,
            )
    errors = validate_cbe(data) if kind == "cbe" else validate_cbp(data)
    if errors:
        raise InputError(
            f"{source}: " + "; ".join(errors),
            reason=Reason.SCHEMA_VIOLATION,
        )
    return Report(
        kind=kind,
        path=Path(source),
        raw=raw,
        data=data,
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def load_report(path: str | Path, kind: str) -> Report:
    """Read a local report file and return its raw-byte hash."""
    report_path = Path(path)
    if not report_path.is_file():
        reason = Reason.MISSING_CBE_REPORT if kind == "cbe" else Reason.MISSING_CBP_REPORT
        raise InputError(f"{report_path}: report not found", reason=reason)
    try:
        raw = report_path.read_bytes()
    except OSError as exc:
        reason = Reason.MISSING_CBE_REPORT if kind == "cbe" else Reason.MISSING_CBP_REPORT
        raise InputError(f"{report_path}: cannot read: {exc}", reason=reason) from exc
    return parse_report_bytes(raw, kind=kind, source=report_path)


def identity_errors(cbe: Report, cbp: Report, *, version: str, tag: str) -> list[str]:
    """F1/F5 identity: reports must describe the CBM subject, not the producer."""
    errors: list[str] = []
    if cbe.package_id != "cbm":
        errors.append(f"CBE package_id={cbe.package_id!r} expected 'cbm'")
    if cbp.package_id != "cbm":
        errors.append(f"CBP package_id={cbp.package_id!r} expected 'cbm'")
    if cbe.version != version:
        errors.append(f"CBE version={cbe.version!r} expected {version!r}")
    if cbp.version != version:
        errors.append(f"CBP version={cbp.version!r} expected {version!r}")
    if cbe.data.get("tag") != tag:
        errors.append(f"CBE tag={cbe.data.get('tag')!r} expected {tag!r}")

    # §5.1 producer_id: optional for pre-clause reports, but when present it
    # must be the producer, not the subject. A mixed old/new report is rejected.
    cbe_producer = cbe.data.get("producer_id")
    if cbe_producer is not None and cbe_producer != "cbe":
        errors.append(f"CBE producer_id={cbe_producer!r} expected 'cbe'")
    cbp_producer = cbp.data.get("producer_id")
    if cbp_producer is not None and cbp_producer != "cbp":
        errors.append(f"CBP producer_id={cbp_producer!r} expected 'cbp'")
    return errors


def find_report_file(root: str | Path, kind: str) -> Path:
    """Locate the report JSON inside a downloaded artifact directory."""
    base = Path(root)
    preferred = (
        ("cbe-report.json", "report.json", "cbe.json")
        if kind == "cbe"
        else ("quality-manifest.json", "manifest.json", "cbp.json")
    )
    for name in preferred:
        matches = sorted(base.rglob(name))
        if matches:
            return matches[0]
    candidates = [
        path
        for path in sorted(base.rglob("*.json"))
        if not path.name.endswith(".schema.json") and not path.name.startswith("cbm-")
    ]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise InputError(
            f"{base}: no {kind.upper()} report JSON found",
            reason=Reason.MISSING_CBE_REPORT if kind == "cbe" else Reason.MISSING_CBP_REPORT,
        )
    raise InputError(
        f"{base}: ambiguous report JSON: {[str(path) for path in candidates]}",
        reason=Reason.SCHEMA_VIOLATION,
    )


def artifact_hash_from_cbp(cbp: Report, wheel_name: str) -> str | None:
    """Find the wheel digest in CBP's artifact_hashes.

    Accepts exact name, basename, and ``dist/<name>``.  If several different
    digests match the same basename, treat it as ambiguous and return None.
    """
    hashes = cbp.data.get("artifact_hashes")
    if not isinstance(hashes, dict):
        return None
    candidates = {
        wheel_name,
        Path(wheel_name).name,
        f"dist/{Path(wheel_name).name}",
        f"./{wheel_name}",
    }
    found: set[str] = set()
    for key, value in hashes.items():
        if not isinstance(key, str) or not _is_hex64(value):
            continue
        normalised = key.replace("\\", "/").lstrip("./")
        if normalised in {candidate.replace("\\", "/").lstrip("./") for candidate in candidates}:
            digest = value[len("sha256:") :] if value.startswith("sha256:") else value
            found.add(digest.lower())
    if len(found) != 1:
        return None
    return next(iter(found))
