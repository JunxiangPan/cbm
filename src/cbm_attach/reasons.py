"""Status enums, reason codes, and typed errors for CBM attach.

CBM is a sidecar attestation workflow.  It consumes CBE/CBP reports and never
re-runs their gates.  The status values below are deliberately split into two
axes:

* ``cbm_gate_status``  -- what the CBM gate decided (PASS / FAIL / ...)
* ``upload_status``    -- whether an uploaded, digest-verified asset exists

F6 requires ``NOT_UPLOADED`` to be visible and never written as PASS.  Keeping
the two axes separate means a real gate failure is not laundered into a neutral
NOT_UPLOADED state, while the Release body can still label the attachment as
NOT_UPLOADED.
"""
from __future__ import annotations

from enum import Enum


SKIP_LIMIT = 0.20

CBM_GATE_STATUSES = frozenset(
    {"PASS", "FAIL", "NOT_UPLOADED", "SKIPPED_INFRA", "PRECONDITION_FAIL"}
)
UPSTREAM_GATE_STATUSES = frozenset(
    {"PASS", "FAIL", "SKIPPED_INFRA", "PRECONDITION_FAIL"}
)
UPLOAD_STATUSES = frozenset(
    {"UPLOADED_VERIFIED", "UPLOADED_UNVERIFIED", "NOT_UPLOADED"}
)
DECISIONS = frozenset({"UPLOAD", "NO_UPLOAD"})

# F3: these CBP gates may not SKIP.
BLOCKING_CBP_GATES = frozenset(
    {"claims", "binary", "encoding", "docs", "custom"}
)


class Reason(str, Enum):
    """Machine-readable reason codes written into the CBM report."""

    # input / format
    MISSING_CBE_REPORT = "MISSING_CBE_REPORT"
    MISSING_CBP_REPORT = "MISSING_CBP_REPORT"
    MISSING_BUILD_ONCE_ARTIFACT = "MISSING_BUILD_ONCE_ARTIFACT"
    MISSING_DECLARED_ATTACHED = "MISSING_DECLARED_ATTACHED"
    MISSING_ARGUMENT = "MISSING_ARGUMENT"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    MISSING_RELEASE = "MISSING_RELEASE"
    MISSING_RELEASE_BODY_HASH = "MISSING_RELEASE_BODY_HASH"
    MISSING_BODY_HASH_SCOPE = "MISSING_BODY_HASH_SCOPE"
    BODY_HASH_SCOPE_UNSUPPORTED = "BODY_HASH_SCOPE_UNSUPPORTED"
    ARTIFACT_FORBIDDEN = "ARTIFACT_FORBIDDEN"
    INVALID_JSON = "INVALID_JSON"
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    REPORT_INCONSISTENT = "REPORT_INCONSISTENT"

    # identity / gate
    REPORT_IDENTITY_MISMATCH = "REPORT_IDENTITY_MISMATCH"
    CBE_NOT_PASS = "CBE_NOT_PASS"
    CBP_NOT_PASS = "CBP_NOT_PASS"
    UPSTREAM_PRECONDITION_FAIL = "UPSTREAM_PRECONDITION_FAIL"
    UPSTREAM_SKIPPED_INFRA = "UPSTREAM_SKIPPED_INFRA"
    SKIP_RATIO_EXCEEDED = "SKIP_RATIO_EXCEEDED"
    BLOCKING_SKIP = "BLOCKING_SKIP"

    # artifact / upload
    CBP_ARTIFACT_HASH_MISSING = "CBP_ARTIFACT_HASH_MISSING"
    ARTIFACT_HASH_MISMATCH = "ARTIFACT_HASH_MISMATCH"
    UPLOAD_FAILED = "UPLOAD_FAILED"
    UPLOAD_VERIFY_FAILED = "UPLOAD_VERIFY_FAILED"
    ASSET_DIGEST_CONFLICT = "ASSET_DIGEST_CONFLICT"
    REMOTE_DIGEST_UNAVAILABLE = "REMOTE_DIGEST_UNAVAILABLE"
    UNSUPPORTED_UPLOAD_TARGET = "UNSUPPORTED_UPLOAD_TARGET"
    UPLOAD_NOT_APPROVED = "UPLOAD_NOT_APPROVED"

    # infrastructure
    INFRA_FETCH_FAILED = "INFRA_FETCH_FAILED"
    INFRA_UPLOAD_FAILED = "INFRA_UPLOAD_FAILED"

    # non-upload / evidence
    NOT_CLAIMED = "NOT_CLAIMED"
    UPLOAD_PENDING = "UPLOAD_PENDING"
    EVIDENCE_ABSENT = "EVIDENCE_ABSENT"
    EVIDENCE_INVALID = "EVIDENCE_INVALID"
    EVIDENCE_WRITE_FAILED = "EVIDENCE_WRITE_FAILED"
    WORKFLOW_FAILED_BEFORE_EVIDENCE = "WORKFLOW_FAILED_BEFORE_EVIDENCE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UPLOADED_VERIFIED = "UPLOADED_VERIFIED"


class CbmError(Exception):
    """Base class for every coded failure path.

    Every subclass carries the exact values that must be written to the report
    before the process exits.  Callers never invent a status at the call site.
    """

    exit_code = 3
    cbm_gate_status = "FAIL"
    upload_status = "NOT_UPLOADED"
    reason = Reason.UPLOAD_FAILED

    def __init__(
        self,
        detail: str = "",
        *,
        reason: Reason | None = None,
        cbm_gate_status: str | None = None,
        upload_status: str | None = None,
        exit_code: int | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        if reason is not None:
            self.reason = reason
        if cbm_gate_status is not None:
            self.cbm_gate_status = cbm_gate_status
        if upload_status is not None:
            self.upload_status = upload_status
        if exit_code is not None:
            self.exit_code = exit_code

    @property
    def reason_value(self) -> str:
        return self.reason.value if isinstance(self.reason, Reason) else str(self.reason)


class InputError(CbmError):
    """Missing or malformed input.  Exit 2, PRECONDITION_FAIL."""

    exit_code = 2
    cbm_gate_status = "PRECONDITION_FAIL"
    upload_status = "NOT_UPLOADED"
    reason = Reason.SCHEMA_VIOLATION


class GateError(CbmError):
    """CBE/CBP or identity gate failure.  Exit 3 by default, FAIL."""

    exit_code = 3
    cbm_gate_status = "FAIL"
    upload_status = "NOT_UPLOADED"
    reason = Reason.CBE_NOT_PASS


class InfraError(CbmError):
    """Runner/network/provider failure.  Exit 3, SKIPPED_INFRA."""

    exit_code = 3
    cbm_gate_status = "SKIPPED_INFRA"
    upload_status = "NOT_UPLOADED"
    reason = Reason.INFRA_UPLOAD_FAILED


class UploadError(CbmError):
    """Upload-side failure after the gate allowed an upload."""

    exit_code = 3
    cbm_gate_status = "FAIL"
    upload_status = "NOT_UPLOADED"
    reason = Reason.UPLOAD_FAILED


class VerifyError(UploadError):
    """Upload happened, but the remote digest did not match."""

    upload_status = "UPLOADED_UNVERIFIED"
    reason = Reason.UPLOAD_VERIFY_FAILED
