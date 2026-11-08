"""CBM attach CLI: verify | upload | finalize.

Every coded path writes a CBM report before exiting.  The exit code and the
report status are one decision, made in one place, so a caller cannot see exit 3
with a PASS report or exit 0 with a FAIL report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import body
from .artifacts import (
    Artifact,
    fetch_artifact,
    fetch_report,
    locate_build_once_root,
    verify_build_once,
)
from .gates import Evaluation, evaluate, upstream_summary
from .reasons import (
    CbmError,
    GateError,
    InputError,
    Reason,
    UploadError,
    VerifyError,
)
from .reports import Report, artifact_hash_from_cbp, load_report
from .uploader import load_uploader


HEX40_RE = re.compile(r"^[a-fA-F0-9]{40}$")
REPO_RE = re.compile(r"^[^/\s]+/[^/\s]+$")
TAG_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
VERSION_RE = re.compile(r"^v?[0-9]+\.[0-9]+\.[0-9]+$")

DEFAULT_REPORT = "cbm-evidence/cbm-report.json"
DEFAULT_BODY = "cbm-evidence/cbm-body.md"
DEFAULT_DECISION = "cbm-evidence/cbm-decision.json"
DEFAULT_FINAL_REPORT = "cbm-evidence/cbm-report.final.json"
DEFAULT_FINAL_BODY = "cbm-evidence/cbm-body.final.md"


@dataclass
class ReportContext:
    now: str
    version: str | None = None
    tag: str | None = None
    release_tag: str | None = None
    declared_attached: bool = False
    cbm_gate_status: str = "PRECONDITION_FAIL"
    exit_code: int = 2
    upload_status: str = "NOT_UPLOADED"
    reason: str = Reason.SCHEMA_VIOLATION.value
    reason_detail: str = ""
    cbe: Report | None = None
    cbp: Report | None = None
    artifact: Artifact | None = None
    upload_target: str | None = None
    build_once_run_id: str | None = None
    ci_commit_sha: str | None = None
    uploaded_asset_url: str | None = None
    uploaded_asset_digest: str | None = None


def _now(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _canonical_sha256(report: dict[str, Any]) -> str:
    payload = {key: value for key, value in report.items() if key != "evidence_sha256"}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _seal(report: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(report)
    sealed.pop("evidence_sha256", None)
    sealed["evidence_sha256"] = _canonical_sha256(sealed)
    return sealed


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _write_evidence(
    output: Path,
    body_path: Path,
    decision_path: Path,
    report: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    _write_json(output, report)
    _write_text(body_path, body.render_marked(report))
    _write_json(decision_path, decision)


def _decision(report: dict[str, Any], choice: str, artifact: Artifact | None) -> dict[str, Any]:
    return {
        "decision": choice,
        "reason": report.get("reason"),
        "cbm_gate_status": report.get("cbm_gate_status"),
        "upload_status": report.get("upload_status"),
        "report_sha256": report.get("evidence_sha256"),
        "artifact": (
            {
                "name": artifact.name,
                "sha256": artifact.sha256,
            }
            if artifact is not None
            else None
        ),
    }


def _require(value: str | None, name: str) -> str:
    if value is None or not str(value).strip():
        raise InputError(f"{name} is required", reason=Reason.MISSING_ARGUMENT)
    return str(value).strip()


def _parse_bool(value: str | None, name: str, *, required: bool) -> bool:
    if value is None or not str(value).strip():
        if required:
            raise InputError(f"{name} is required", reason=Reason.MISSING_DECLARED_ATTACHED)
        return False
    text = str(value).strip().lower()
    if text not in {"true", "false"}:
        raise InputError(
            f"{name} must be 'true' or 'false', got {value!r}",
            reason=Reason.SCHEMA_VIOLATION,
        )
    return text == "true"


def _parse_version(value: str | None, *, required: bool) -> str | None:
    if value is None or not str(value).strip():
        if required:
            raise InputError("version is required", reason=Reason.MISSING_ARGUMENT)
        return None
    text = str(value).strip()
    if not VERSION_RE.fullmatch(text):
        raise InputError(
            f"invalid version {text!r}; expected vX.Y.Z",
            reason=Reason.SCHEMA_VIOLATION,
        )
    return text


def _parse_tag(value: str | None, name: str, *, required: bool) -> str | None:
    if value is None or not str(value).strip():
        if required:
            raise InputError(f"{name} is required", reason=Reason.MISSING_ARGUMENT)
        return None
    text = str(value).strip()
    if not TAG_RE.fullmatch(text):
        raise InputError(
            f"invalid {name} {text!r}; expected vX.Y.Z",
            reason=Reason.SCHEMA_VIOLATION,
        )
    return text


def _parse_repo(value: str | None, *, required: bool) -> str | None:
    if value is None or not str(value).strip():
        if required:
            raise InputError("repository is required", reason=Reason.MISSING_ARGUMENT)
        return None
    text = str(value).strip()
    if not REPO_RE.fullmatch(text):
        raise InputError(
            f"invalid repository {text!r}; expected owner/name",
            reason=Reason.SCHEMA_VIOLATION,
        )
    return text


def _parse_target(value: str | None, *, required: bool) -> str | None:
    if value is None or not str(value).strip():
        if required:
            raise InputError("upload_target is required", reason=Reason.MISSING_ARGUMENT)
        return None
    text = str(value).strip()
    if text not in {"github-release", "pypi"}:
        raise InputError(
            f"unsupported upload_target {text!r}",
            reason=Reason.UNSUPPORTED_UPLOAD_TARGET,
        )
    return text


def _parse_ci_commit(value: str | None) -> str | None:
    if value is None or not str(value).strip():
        return None
    text = str(value).strip()
    if not HEX40_RE.fullmatch(text):
        raise InputError(
            f"invalid ci_commit_sha {text!r}; expected 40 hex characters",
            reason=Reason.SCHEMA_VIOLATION,
        )
    return text.lower()


def _report_dict(ctx: ReportContext) -> dict[str, Any]:
    cbp_artifact_sha = None
    if ctx.cbp is not None and ctx.artifact is not None:
        cbp_artifact_sha = artifact_hash_from_cbp(ctx.cbp, ctx.artifact.name)
    return {
        "schema_version": "1",
        "package_id": "cbm",
        "version": ctx.version,
        "tag": ctx.tag,
        "release_tag": ctx.release_tag,
        "cbm_gate_status": ctx.cbm_gate_status,
        "exit_code": ctx.exit_code,
        "cbe_report_hash": ctx.cbe.sha256 if ctx.cbe is not None else None,
        "cbp_report_hash": ctx.cbp.sha256 if ctx.cbp is not None else None,
        "cbp_release_body_hash": (
            ctx.cbp.data.get("release_body_hash") if ctx.cbp is not None else None
        ),
        "cbp_body_hash_scope": (
            ctx.cbp.data.get("body_hash_scope") if ctx.cbp is not None else None
        ),
        "upload_status": ctx.upload_status,
        "reason": ctx.reason,
        "reason_detail": ctx.reason_detail,
        "declared_attached": ctx.declared_attached,
        "upstream_gate_status": upstream_summary(ctx.cbe, ctx.cbp),
        "artifact_name": ctx.artifact.name if ctx.artifact is not None else None,
        "artifact_sha256": ctx.artifact.sha256 if ctx.artifact is not None else None,
        "cbp_artifact_sha256": cbp_artifact_sha,
        "build_once_run_id": ctx.build_once_run_id,
        "ci_commit_sha": ctx.ci_commit_sha,
        "upload_target": ctx.upload_target,
        "uploaded_asset_url": ctx.uploaded_asset_url,
        "uploaded_asset_digest": ctx.uploaded_asset_digest,
        "verified_at": ctx.now,
    }


def _apply_error(ctx: ReportContext, error: CbmError) -> None:
    ctx.cbm_gate_status = error.cbm_gate_status
    ctx.upload_status = error.upload_status
    ctx.reason = error.reason_value
    ctx.reason_detail = error.detail
    ctx.exit_code = error.exit_code


def _load_inputs(
    args: argparse.Namespace,
    workspace: Path,
) -> tuple[Report | None, Report | None, Artifact | None]:
    cbe: Report | None = None
    cbp: Report | None = None
    artifact: Artifact | None = None

    if args.fetch:
        artifact_repository = _require(
            args.artifact_repository or args.repository,
            "artifact_repository",
        )
        if args.build_once_run_id and args.build_once_artifact:
            fetched = fetch_artifact(
                repository=artifact_repository,
                run_id=args.build_once_run_id,
                artifact_name=args.build_once_artifact,
                destination=workspace / "build-once",
                missing_reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
                gh_bin=args.gh_bin,
            )
            artifact = verify_build_once(locate_build_once_root(fetched))
        if args.cbe_run_id and args.cbe_report_artifact:
            cbe = fetch_report(
                repository=artifact_repository,
                run_id=args.cbe_run_id,
                artifact_name=args.cbe_report_artifact,
                kind="cbe",
                destination=workspace / "cbe",
                gh_bin=args.gh_bin,
            )
        if args.cbp_run_id and args.cbp_report_artifact:
            cbp = fetch_report(
                repository=artifact_repository,
                run_id=args.cbp_run_id,
                artifact_name=args.cbp_report_artifact,
                kind="cbp",
                destination=workspace / "cbp",
                gh_bin=args.gh_bin,
            )
    else:
        if args.build_once_dir:
            artifact = verify_build_once(args.build_once_dir)
        if args.cbe_report:
            cbe = load_report(args.cbe_report, "cbe")
        if args.cbp_report:
            cbp = load_report(args.cbp_report, "cbp")
    return cbe, cbp, artifact


def _verify(args: argparse.Namespace) -> int:
    ctx = ReportContext(now=_now(args.now))
    try:
        ctx.version = _parse_version(args.version, required=True)
        ctx.tag = _parse_tag(args.tag, "tag", required=True)
        ctx.release_tag = _parse_tag(args.release_tag, "release_tag", required=True)
        ctx.declared_attached = _parse_bool(
            args.declared_attached, "declared_attached", required=True
        )
        ctx.upload_target = _parse_target(args.upload_target, required=True)
        ctx.build_once_run_id = args.build_once_run_id or None
        ctx.ci_commit_sha = _parse_ci_commit(args.ci_commit_sha)

        workspace = Path(args.workdir or ".cbm-incoming")
        cbe, cbp, artifact = _load_inputs(args, workspace)
        ctx.cbe, ctx.cbp, ctx.artifact = cbe, cbp, artifact

        if ctx.declared_attached:
            if cbe is None:
                raise InputError(
                    "declared_attached=true but no CBE report was supplied",
                    reason=Reason.MISSING_CBE_REPORT,
                )
            if cbp is None:
                raise InputError(
                    "declared_attached=true but no CBP manifest was supplied",
                    reason=Reason.MISSING_CBP_REPORT,
                )
            if artifact is None:
                raise InputError(
                    "declared_attached=true but no build-once artifact was supplied",
                    reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
                )

        evaluation: Evaluation = evaluate(
            cbe,
            cbp,
            version=ctx.version,
            tag=ctx.tag,
            declared_attached=ctx.declared_attached,
            wheel_name=artifact.name if artifact is not None else None,
            artifact_sha256=artifact.sha256 if artifact is not None else None,
        )
        ctx.cbm_gate_status = evaluation.cbm_gate_status
        ctx.upload_status = evaluation.upload_status
        ctx.reason = evaluation.reason
        ctx.reason_detail = evaluation.reason_detail
        ctx.exit_code = evaluation.exit_code

        report = _seal(_report_dict(ctx))
        decision = _decision(
            report,
            "UPLOAD" if evaluation.upload_allowed else "NO_UPLOAD",
            artifact,
        )
        _write_evidence(
            Path(args.output),
            Path(args.body),
            Path(args.decision),
            report,
            decision,
        )
        print(
            "CBM_VERIFY "
            f"decision={decision['decision']} "
            f"cbm_gate_status={report['cbm_gate_status']} "
            f"upload_status={report['upload_status']} "
            f"reason={report['reason']}"
        )
        return evaluation.exit_code
    except CbmError as error:
        _apply_error(ctx, error)
        report = _seal(_report_dict(ctx))
        decision = _decision(report, "NO_UPLOAD", ctx.artifact)
        _write_evidence(
            Path(args.output),
            Path(args.body),
            Path(args.decision),
            report,
            decision,
        )
        print(f"{error.reason_value}: {error.detail}", file=sys.stderr)
        return error.exit_code
    except Exception as error:  # noqa: BLE001 - evidence must survive unknown failures
        ctx.cbm_gate_status = "FAIL"
        ctx.exit_code = 3
        ctx.upload_status = "NOT_UPLOADED"
        ctx.reason = Reason.INTERNAL_ERROR.value
        ctx.reason_detail = f"{type(error).__name__}: {error}"
        report = _seal(_report_dict(ctx))
        decision = _decision(report, "NO_UPLOAD", ctx.artifact)
        _write_evidence(
            Path(args.output),
            Path(args.body),
            Path(args.decision),
            report,
            decision,
        )
        traceback.print_exc()
        return 3


def _load_json(path: str | Path, *, what: str) -> dict[str, Any]:
    candidate = Path(path)
    if not candidate.is_file():
        raise InputError(f"{candidate}: {what} not found", reason=Reason.MISSING_EVIDENCE)
    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InputError(
            f"{candidate}: cannot read {what}: {error}",
            reason=Reason.INVALID_JSON,
        ) from error
    if not isinstance(data, dict):
        raise InputError(f"{candidate}: {what} must be a JSON object", reason=Reason.INVALID_JSON)
    return data


def _check_upload_approval(report: dict[str, Any], decision: dict[str, Any]) -> None:
    if not _evidence_hash_ok(report):
        raise GateError(
            "report evidence_sha256 does not match its contents",
            reason=Reason.EVIDENCE_INVALID,
        )
    if decision.get("report_sha256") != report.get("evidence_sha256"):
        raise GateError(
            "decision is not bound to this report",
            reason=Reason.EVIDENCE_INVALID,
        )
    if decision.get("decision") != "UPLOAD":
        raise GateError(
            f"decision={decision.get('decision')!r}; upload is not approved",
            reason=Reason.UPLOAD_NOT_APPROVED,
        )
    if report.get("cbm_gate_status") != "NOT_UPLOADED":
        raise GateError(
            f"cbm_gate_status={report.get('cbm_gate_status')!r}; upload is not approved",
            reason=Reason.UPLOAD_NOT_APPROVED,
        )
    if report.get("upload_status") != "NOT_UPLOADED":
        raise GateError(
            f"upload_status={report.get('upload_status')!r}; upload is not approved",
            reason=Reason.UPLOAD_NOT_APPROVED,
        )
    if report.get("reason") != Reason.UPLOAD_PENDING.value:
        raise GateError(
            f"reason={report.get('reason')!r}; upload is not approved",
            reason=Reason.UPLOAD_NOT_APPROVED,
        )
    if report.get("artifact_sha256") is None:
        raise GateError(
            "report has no artifact_sha256",
            reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
        )


def _verify_artifact_against_report(report: dict[str, Any], artifact: Artifact) -> None:
    expected = report.get("artifact_sha256")
    if expected != artifact.sha256:
        raise GateError(
            f"build-once parser saw {artifact.sha256} but the approved report says {expected}",
            reason=Reason.ARTIFACT_HASH_MISMATCH,
        )
    cbp_expected = report.get("cbp_artifact_sha256")
    if cbp_expected is not None and cbp_expected != artifact.sha256:
        raise GateError(
            f"build-once parser saw {artifact.sha256} but CBP said {cbp_expected}",
            reason=Reason.ARTIFACT_HASH_MISMATCH,
        )


def _upload(args: argparse.Namespace) -> int:
    report = _load_json(args.report, what="CBM report")
    decision = _load_json(args.decision, what="CBM decision")
    now = _now(args.now)
    try:
        _check_upload_approval(report, decision)
        if args.fetch:
            artifact_repository = _require(
                args.artifact_repository or args.repository,
                "artifact_repository",
            )
            run_id = args.build_once_run_id or report.get("build_once_run_id")
            artifact_name = args.build_once_artifact or f"cbm-build-once"
            if not run_id:
                raise InputError(
                    "build_once_run_id is required to fetch the artifact",
                    reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
                )
            fetched = fetch_artifact(
                repository=artifact_repository,
                run_id=str(run_id),
                artifact_name=artifact_name,
                destination=Path(args.workdir or ".cbm-incoming") / "upload-build-once",
                missing_reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
                gh_bin=args.gh_bin,
            )
            artifact = verify_build_once(locate_build_once_root(fetched))
        else:
            if not args.build_once_dir:
                raise InputError(
                    "build_once_dir is required to re-verify the artifact",
                    reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
                )
            artifact = verify_build_once(args.build_once_dir)

        _verify_artifact_against_report(report, artifact)

        target = _parse_target(
            args.upload_target or report.get("upload_target"),
            required=True,
        )
        repository = _parse_repo(args.repository, required=target == "github-release")
        release_tag = _parse_tag(
            args.release_tag or report.get("release_tag"),
            "release_tag",
            required=target == "github-release",
        )
        uploader = load_uploader(
            target,
            repository=repository or "",
            release_tag=release_tag or "",
            wheel_name=artifact.name,
            gh_bin=args.gh_bin,
            twine_bin=args.twine_bin,
        )

        existing = uploader.get_digest(artifact.name)
        if existing == artifact.sha256:
            remote = existing
            uploaded_url = uploader.get_url(artifact.name)
        elif existing is not None:
            raise UploadError(
                f"remote asset {artifact.name!r} has sha256 {existing}, not {artifact.sha256}",
                reason=Reason.ASSET_DIGEST_CONFLICT,
            )
        else:
            uploader.upload(artifact.path, artifact.name)
            remote = uploader.get_digest(artifact.name)
            if remote != artifact.sha256:
                report["uploaded_asset_digest"] = remote
                raise VerifyError(
                    f"remote digest {remote!r} != local {artifact.sha256}",
                    reason=Reason.UPLOAD_VERIFY_FAILED,
                )
            uploaded_url = uploader.get_url(artifact.name)

        report["cbm_gate_status"] = "PASS"
        report["upload_status"] = "UPLOADED_VERIFIED"
        report["reason"] = Reason.UPLOADED_VERIFIED.value
        report["reason_detail"] = "uploaded asset digest verified"
        report["exit_code"] = 0
        report["uploaded_asset_digest"] = remote
        report["uploaded_asset_url"] = uploaded_url
        report["verified_at"] = now
        sealed = _seal(report)
        _write_json(Path(args.output), sealed)
        _write_text(Path(args.body), body.render_marked(sealed))
        print(
            "CBM_UPLOAD "
            f"cbm_gate_status=PASS upload_status=UPLOADED_VERIFIED "
            f"asset={artifact.name} sha256={artifact.sha256}"
        )
        return 0
    except CbmError as error:
        report["cbm_gate_status"] = error.cbm_gate_status
        report["upload_status"] = error.upload_status
        report["reason"] = error.reason_value
        report["reason_detail"] = error.detail
        report["exit_code"] = error.exit_code
        report["verified_at"] = now
        if error.upload_status != "UPLOADED_VERIFIED":
            report["uploaded_asset_url"] = None
        sealed = _seal(report)
        _write_json(Path(args.output), sealed)
        _write_text(Path(args.body), body.render_marked(sealed))
        print(f"{error.reason_value}: {error.detail}", file=sys.stderr)
        return error.exit_code
    except Exception as error:  # noqa: BLE001
        report["cbm_gate_status"] = "FAIL"
        report["upload_status"] = "NOT_UPLOADED"
        report["reason"] = Reason.INTERNAL_ERROR.value
        report["reason_detail"] = f"{type(error).__name__}: {error}"
        report["exit_code"] = 3
        report["verified_at"] = now
        sealed = _seal(report)
        _write_json(Path(args.output), sealed)
        _write_text(Path(args.body), body.render_marked(sealed))
        traceback.print_exc()
        return 3


def _evidence_hash_ok(report: dict[str, Any]) -> bool:
    stored = report.get("evidence_sha256")
    if not isinstance(stored, str):
        return False
    return _canonical_sha256(report) == stored


def _consistent_pass(report: dict[str, Any]) -> bool:
    gate = report.get("cbm_gate_status")
    upload = report.get("upload_status")
    if gate == "PASS" and upload != "UPLOADED_VERIFIED":
        return False
    if upload == "UPLOADED_VERIFIED" and gate != "PASS":
        return False
    return True


def _failure_report(
    ctx: ReportContext,
    *,
    reason: Reason,
    detail: str,
    status: str = "FAIL",
    exit_code: int = 3,
) -> dict[str, Any]:
    ctx.cbm_gate_status = status
    ctx.exit_code = exit_code
    ctx.upload_status = "NOT_UPLOADED"
    ctx.reason = reason.value
    ctx.reason_detail = detail
    ctx.uploaded_asset_url = None
    ctx.uploaded_asset_digest = None
    return _seal(_report_dict(ctx))


def _finalize(args: argparse.Namespace) -> int:
    now = _now(args.now)
    ctx = ReportContext(now=now)
    try:
        ctx.version = _parse_version(args.version, required=False)
        ctx.tag = _parse_tag(args.tag, "tag", required=False)
        ctx.release_tag = _parse_tag(args.release_tag, "release_tag", required=False)
        ctx.declared_attached = _parse_bool(
            args.declared_attached, "declared_attached", required=False
        )
    except CbmError as error:
        _apply_error(ctx, error)
        report = _failure_report(
            ctx,
            reason=error.reason,
            detail=error.detail,
            status=error.cbm_gate_status,
            exit_code=error.exit_code,
        )
        _write_json(Path(args.output), report)
        _write_text(Path(args.body), body.render_marked(report))
        _export_outputs(report)
        print(f"{error.reason_value}: {error.detail}", file=sys.stderr)
        return 0

    input_dir = Path(args.input)
    candidates = (
        [path for path in input_dir.rglob("cbm-report*.json") if path.is_file()]
        if input_dir.is_dir()
        else []
    )
    chosen: Path | None = None
    for preferred in ("cbm-report.final.json", "cbm-report.json"):
        matches = [path for path in candidates if path.name == preferred]
        if matches:
            chosen = max(matches, key=lambda path: path.stat().st_mtime)
            break
    if chosen is None and candidates:
        chosen = max(candidates, key=lambda path: path.stat().st_mtime)

    report: dict[str, Any]
    if chosen is None:
        report = _failure_report(
            ctx,
            reason=Reason.EVIDENCE_ABSENT,
            detail="no CBM report was produced before finalization; WORKFLOW_FAILED_BEFORE_EVIDENCE",
            status="SKIPPED_INFRA",
            exit_code=3,
        )
    else:
        try:
            base = _load_json(chosen, what="CBM report")
        except CbmError as error:
            report = _failure_report(
                ctx,
                reason=error.reason,
                detail=error.detail,
                status="FAIL",
                exit_code=3,
            )
        else:
            if not _evidence_hash_ok(base):
                report = _failure_report_from_base(
                    base,
                    now,
                    reason=Reason.EVIDENCE_INVALID,
                    detail="evidence_sha256 does not match the report contents",
                )
            elif not _consistent_pass(base):
                report = _failure_report_from_base(
                    base,
                    now,
                    reason=Reason.EVIDENCE_INVALID,
                    detail="PASS/upload status contradiction",
                )
            else:
                report = dict(base)
                upload_result = (args.upload_result or "").lower()
                if upload_result and report.get("reason") == Reason.UPLOAD_PENDING.value:
                    report = _failure_report_from_base(
                        report,
                        now,
                        reason=Reason.UPLOAD_FAILED,
                        detail=f"upload job result={upload_result}",
                    )
                report["verified_at"] = report.get("verified_at") or now
                report = _seal(report)

    _write_json(Path(args.output), report)
    _write_text(Path(args.body), body.render_marked(report))
    _export_outputs(report)
    print(
        "CBM_FINALIZE "
        f"cbm_gate_status={report.get('cbm_gate_status')} "
        f"upload_status={report.get('upload_status')} "
        f"reason={report.get('reason')}"
    )
    return 0


def _failure_report_from_base(
    base: dict[str, Any],
    now: str,
    *,
    reason: Reason,
    detail: str,
) -> dict[str, Any]:
    report = dict(base)
    report["cbm_gate_status"] = "FAIL"
    report["exit_code"] = 3
    report["upload_status"] = "NOT_UPLOADED"
    report["reason"] = reason.value
    report["reason_detail"] = detail
    report["uploaded_asset_url"] = None
    report["uploaded_asset_digest"] = None
    report["verified_at"] = now
    return _seal(report)


def _export_outputs(report: dict[str, Any]) -> None:
    destination = os.environ.get("GITHUB_OUTPUT")
    if not destination:
        return
    values = {
        "cbm_gate_status": report.get("cbm_gate_status") or "",
        "upload_status": report.get("upload_status") or "",
        "cbe_report_hash": report.get("cbe_report_hash") or "",
        "cbp_report_hash": report.get("cbp_report_hash") or "",
    }
    with open(destination, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cbm_attach")
    sub = parser.add_subparsers(dest="command")

    verify = sub.add_parser("verify", help="consume CBE/CBP and decide upload")
    verify.add_argument("--version")
    verify.add_argument("--tag")
    verify.add_argument("--release-tag")
    verify.add_argument("--declared-attached")
    verify.add_argument("--upload-target")
    verify.add_argument("--repository")
    verify.add_argument("--artifact-repository")
    verify.add_argument("--cbm-repository")
    verify.add_argument("--ci-commit-sha")
    verify.add_argument("--cbe-report")
    verify.add_argument("--cbp-report")
    verify.add_argument("--build-once-dir")
    verify.add_argument("--cbe-run-id")
    verify.add_argument("--cbe-report-artifact")
    verify.add_argument("--cbp-run-id")
    verify.add_argument("--cbp-report-artifact")
    verify.add_argument("--build-once-run-id")
    verify.add_argument("--build-once-artifact")
    verify.add_argument("--fetch", action="store_true")
    verify.add_argument("--workdir", default=".cbm-incoming")
    verify.add_argument("--gh-bin", default="gh")
    verify.add_argument("--output", default=DEFAULT_REPORT)
    verify.add_argument("--body", default=DEFAULT_BODY)
    verify.add_argument("--decision", default=DEFAULT_DECISION)
    verify.add_argument("--now")

    upload = sub.add_parser("upload", help="upload the approved build-once asset")
    upload.add_argument("--report", default=DEFAULT_REPORT)
    upload.add_argument("--decision", default=DEFAULT_DECISION)
    upload.add_argument("--build-once-dir")
    upload.add_argument("--build-once-run-id")
    upload.add_argument("--build-once-artifact", default="cbm-build-once")
    upload.add_argument("--fetch", action="store_true")
    upload.add_argument("--workdir", default=".cbm-incoming")
    upload.add_argument("--repository")
    upload.add_argument("--artifact-repository")
    upload.add_argument("--release-tag")
    upload.add_argument("--upload-target")
    upload.add_argument("--gh-bin", default="gh")
    upload.add_argument("--twine-bin", default="twine")
    upload.add_argument("--output", default=DEFAULT_FINAL_REPORT)
    upload.add_argument("--body", default=DEFAULT_FINAL_BODY)
    upload.add_argument("--now")

    finalize = sub.add_parser("finalize", help="emit the final report and body fragment")
    finalize.add_argument("--input", default="cbm-evidence")
    finalize.add_argument("--output", default="cbm-evidence-out/cbm-report.json")
    finalize.add_argument("--body", default="cbm-evidence-out/cbm-body.md")
    finalize.add_argument("--declared-attached")
    finalize.add_argument("--version")
    finalize.add_argument("--tag")
    finalize.add_argument("--release-tag")
    finalize.add_argument("--upload-result")
    finalize.add_argument("--now")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help(sys.stderr)
        return 2
    try:
        if args.command == "verify":
            return _verify(args)
        if args.command == "upload":
            return _upload(args)
        if args.command == "finalize":
            return _finalize(args)
        parser.print_help(sys.stderr)
        return 2
    except OSError as error:
        print(f"CBM_EVIDENCE_WRITE_FAILED: {error}", file=sys.stderr)
        return 3
