"""Consume CBE/CBP reports and decide whether CBM may upload.

This module does not run any CBE or CBP check.  It reads the reports those
gates produced, verifies their structural consistency, enforces the F2/F3 skip
rules, and binds the CBP artifact hash to the build-once wheel.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .reasons import (
    BLOCKING_CBP_GATES,
    SKIP_LIMIT,
    GateError,
    InputError,
    Reason,
)
from .reports import Report, artifact_hash_from_cbp, evidence_hash_matches, identity_errors


@dataclass(frozen=True)
class Evaluation:
    exit_code: int
    cbm_gate_status: str
    upload_status: str
    reason: str
    reason_detail: str
    upload_allowed: bool
    upstream: dict[str, Any] = field(default_factory=dict)


def _cbp_derived_exit(status: str) -> int:
    return {"PASS": 0, "FAIL": 3, "SKIPPED_INFRA": 3, "PRECONDITION_FAIL": 2}.get(status, 3)


def upstream_summary(
    cbe: Report | None,
    cbp: Report | None,
) -> dict[str, Any]:
    """Build the non-authoritative summary embedded in the CBM report.

    The authoritative values remain the raw report bytes identified by
    ``cbe_report_hash`` / ``cbp_report_hash``.  This summary exists so the
    Release body and P2 checkers do not need to parse two more files.
    """
    def one(report: Report | None, kind: str) -> dict[str, Any] | None:
        if report is None:
            return None
        return {
            "gate_status": report.gate_status,
            "exit_code": report.exit_code if kind == "cbe" else _cbp_derived_exit(report.gate_status),
            "skip_ratio": report.skip_ratio,
            "blocking_skip": report.blocking_skip,
            "producer_id": report.producer_id,
            "producer_version": report.producer_version,
        }

    return {"cbe": one(cbe, "cbe"), "cbp": one(cbp, "cbp")}


def _fail_reasons(cbe: Report, cbp: Report) -> tuple[Reason, str]:
    failed = []
    if cbe.gate_status == "FAIL":
        failed.append("CBE")
    if cbp.gate_status == "FAIL":
        failed.append("CBP")
    if len(failed) == 2:
        return Reason.CBE_NOT_PASS, "CBE and CBP both FAIL"
    if failed == ["CBE"]:
        return Reason.CBE_NOT_PASS, "CBE gate_status=FAIL"
    return Reason.CBP_NOT_PASS, "CBP gate_status=FAIL"


def _check_cbp_gates(cbp: Report) -> None:
    """Reject a PASS report that contradicts its own gate list."""
    gates = cbp.data.get("gates", [])
    if not isinstance(gates, list):
        return
    for gate in gates:
        if not isinstance(gate, dict):
            continue
        name = gate.get("name")
        status = gate.get("status")
        if status == "FAIL":
            raise GateError(
                f"CBP gate {name!r} is FAIL while the manifest claims {cbp.gate_status}",
                reason=Reason.CBP_NOT_PASS,
            )
        if name in BLOCKING_CBP_GATES and status == "SKIPPED":
            raise GateError(
                f"CBP blocking gate {name!r} is SKIPPED (F3)",
                reason=Reason.BLOCKING_SKIP,
            )


def _check_evidence_hash(report: Report) -> None:
    if not evidence_hash_matches(report.data):
        raise GateError(
            f"{report.kind.upper()} evidence_sha256 does not match canonical JSON",
            reason=Reason.EVIDENCE_HASH_MISMATCH,
        )


def evaluate(
    cbe: Report | None,
    cbp: Report | None,
    *,
    version: str,
    tag: str,
    declared_attached: bool,
    wheel_name: str | None = None,
    artifact_sha256: str | None = None,
    expected_artifact_repository: str | None = None,
) -> Evaluation:
    """Return the CBM gate decision or raise a typed :class:`CbmError`."""
    # Trust root: both upstream reports must carry a canonical evidence hash.
    # A format-only hash is not accepted.
    for report in (cbe, cbp):
        if report is not None:
            _check_evidence_hash(report)

    # Identity is checked whenever both reports are supplied, even when the
    # train does not claim CBM.  A producer name in package_id is never a
    # subject identity, and CBM must not silently consume the wrong report.
    if cbe is not None and cbp is not None:
        errors = identity_errors(cbe, cbp, version=version, tag=tag)
        if errors:
            raise GateError(
                "; ".join(errors),
                reason=Reason.REPORT_IDENTITY_MISMATCH,
            )

    if not declared_attached:
        # Nothing was claimed.  If reports were supplied, validate them and
        # record their hashes, but do not turn an optional component into a
        # blocker.  No SKIPPED status is emitted: the reason is NOT_CLAIMED.
        return Evaluation(
            exit_code=0,
            cbm_gate_status="NOT_UPLOADED",
            upload_status="NOT_UPLOADED",
            reason=Reason.NOT_CLAIMED.value,
            reason_detail="release train does not claim CBM",
            upload_allowed=False,
            upstream=upstream_summary(cbe, cbp),
        )

    if cbe is None:
        raise InputError(
            "declared_attached=true but the CBE report is missing",
            reason=Reason.MISSING_CBE_REPORT,
        )
    if cbp is None:
        raise InputError(
            "declared_attached=true but the CBP quality manifest is missing",
            reason=Reason.MISSING_CBP_REPORT,
        )

    # B4: one artifact repository.  A consumer must not accept a manifest that
    # names a different repository.  This is an input/precondition failure
    # (exit 2), not a PASS and not a soft warning.
    if expected_artifact_repository is not None:
        raw_repository = cbp.data.get("artifact_repository")
        actual_repository = (
            raw_repository.get("repository")
            if isinstance(raw_repository, dict)
            else raw_repository
        )
        if (
            not isinstance(actual_repository, str)
            or not actual_repository.strip()
            or actual_repository.strip().lower() != expected_artifact_repository.strip().lower()
        ):
            raise InputError(
                f"CBP artifact_repository={raw_repository!r} expected "
                f"{expected_artifact_repository!r} (cross-repository artifact)",
                reason=Reason.ARTIFACT_REPOSITORY_MISMATCH,
            )

    # Exit-code propagation.  A real FAIL wins over an infra SKIP so the
    # failure is not hidden; both are listed in the body.
    statuses = (cbe.gate_status, cbp.gate_status)
    if "PRECONDITION_FAIL" in statuses:
        raise InputError(
            "upstream report says PRECONDITION_FAIL",
            reason=Reason.UPSTREAM_PRECONDITION_FAIL,
        )
    if "FAIL" in statuses:
        reason, detail = _fail_reasons(cbe, cbp)
        raise GateError(detail, reason=reason)
    if "SKIPPED_INFRA" in statuses:
        raise GateError(
            "upstream gate is SKIPPED_INFRA",
            reason=Reason.UPSTREAM_SKIPPED_INFRA,
            cbm_gate_status="SKIPPED_INFRA",
            exit_code=3,
        )
    if cbe.blocking_skip or cbp.blocking_skip:
        raise GateError(
            "blocking_skip=true (F2/F3)",
            reason=Reason.BLOCKING_SKIP,
            exit_code=3,
        )
    if cbe.skip_ratio > SKIP_LIMIT or cbp.skip_ratio > SKIP_LIMIT:
        raise GateError(
            f"skip ratio above {SKIP_LIMIT:.0%} (CBE={cbe.skip_ratio:.2%}, CBP={cbp.skip_ratio:.2%})",
            reason=Reason.SKIP_RATIO_EXCEEDED,
            exit_code=4,
        )
    for name, report in (("CBE", cbe), ("CBP", cbp)):
        if report.gate_status != "PASS":
            raise GateError(
                f"{name} gate_status={report.gate_status!r} is not PASS",
                reason=Reason.CBE_NOT_PASS if name == "CBE" else Reason.CBP_NOT_PASS,
            )

    _check_cbp_gates(cbp)

    if wheel_name is not None:
        cbp_hash = artifact_hash_from_cbp(cbp, wheel_name)
        if cbp_hash is None:
            raise GateError(
                f"CBP artifact_hashes has no unambiguous digest for {wheel_name!r}",
                reason=Reason.CBP_ARTIFACT_HASH_MISSING,
            )
        if artifact_sha256 is not None and cbp_hash != artifact_sha256.lower():
            raise GateError(
                f"build-once wheel sha256 {artifact_sha256} != CBP artifact_hashes {cbp_hash}",
                reason=Reason.ARTIFACT_HASH_MISMATCH,
            )

    return Evaluation(
        exit_code=0,
        cbm_gate_status="NOT_UPLOADED",
        upload_status="NOT_UPLOADED",
        reason=Reason.UPLOAD_PENDING.value,
        reason_detail="CBE/CBP PASS; upload authorised, not yet uploaded",
        upload_allowed=True,
        upstream=upstream_summary(cbe, cbp),
    )
