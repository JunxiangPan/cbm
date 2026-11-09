"""Shared fixtures for the CBM test suite."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


WHEEL_NAME = "cbm-0.1.0-py3-none-any.whl"


def make_cbe(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": "1",
        "package_id": "cbm",
        "producer_id": "cbe",
        "producer_version": "1.7.0",
        "version": "v0.1.0",
        "tag": "v0.1.0",
        "gate_status": "PASS",
        "exit_code": 0,
        "applicable_count": 4,
        "skip_count": 0,
        "skip_ratio": 0.0,
        "blocking_skip": False,
        "warn_count": 0,
        "rules_manifest_hash": "a" * 64,
        "sarif_paths": [],
        "evidence_sha256": "b" * 64,
    }
    data.update(overrides)
    return data


def make_cbp(artifact_sha: str, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": "1",
        "package_id": "cbm",
        "producer_id": "cbp",
        "producer_version": "1.0.8",
        "version": "v0.1.0",
        "gate_status": "PASS",
        "applicable_gate_count": 9,
        "skip_count": 0,
        "skip_ratio": 0.0,
        "blocking_skip": False,
        "gates": [
            {"name": name, "status": "PASS", "reason": ""}
            for name in (
                "coverage",
                "encoding",
                "dependency",
                "comments",
                "docs",
                "binary",
                "claims",
                "custom",
                "upgrade",
            )
        ],
        "artifact_hashes": {WHEEL_NAME: artifact_sha},
        "release_body_hash": "c" * 64,
        "body_hash_scope": "base",
        "artifact_repository": "owner/repo",
        "evidence_sha256": "d" * 64,
    }
    data.update(overrides)
    return data


def make_artifact(
    tmp_path: Path,
    *,
    subdir: str = "build-once",
    name: str = WHEEL_NAME,
    content: bytes = b"fake wheel\n",
) -> tuple[Path, Path, str]:
    root = tmp_path / subdir
    dist = root / "dist"
    dist.mkdir(parents=True)
    wheel = dist / name
    wheel.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    (root / "WHEEL_SHA256").write_text(f"{digest}  dist/{name}\n", encoding="utf-8")
    (root / "RELEASE_ASSETS.sha256").write_text(
        f"{digest}  dist/{name}\n", encoding="utf-8"
    )
    return root, wheel, digest


def write_json(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_args(
    tmp_path: Path,
    *,
    cbe: dict[str, Any] | None,
    cbp: dict[str, Any] | None,
    artifact_root: Path | None,
    declared: str = "true",
    output_dir: str = "out",
) -> tuple[list[str], Path, Path, Path]:
    cbe_path = write_json(tmp_path / "cbe.json", cbe) if cbe is not None else None
    cbp_path = write_json(tmp_path / "cbp.json", cbp) if cbp is not None else None
    out = tmp_path / output_dir
    report = out / "cbm-report.json"
    body = out / "cbm-body.md"
    decision = out / "cbm-decision.json"
    argv = [
        "verify",
        "--version",
        "v0.1.0",
        "--tag",
        "v0.1.0",
        "--release-tag",
        "v1.7.0",
        "--declared-attached",
        declared,
        "--upload-target",
        "github-release",
        "--artifact-repository",
        "owner/repo",
        "--output",
        str(report),
        "--body",
        str(body),
        "--decision",
        str(decision),
        "--now",
        "2026-11-08T12:00:00Z",
    ]
    if cbe_path is not None:
        argv += ["--cbe-report", str(cbe_path)]
    if cbp_path is not None:
        argv += ["--cbp-report", str(cbp_path)]
    if artifact_root is not None:
        argv += ["--build-once-dir", str(artifact_root)]
    return argv, report, body, decision


def upload_args(
    tmp_path: Path,
    *,
    report: Path,
    decision: Path,
    artifact_root: Path,
    output_dir: str = "final",
) -> tuple[list[str], Path, Path]:
    out = tmp_path / output_dir
    final_report = out / "cbm-report.final.json"
    final_body = out / "cbm-body.final.md"
    argv = [
        "upload",
        "--report",
        str(report),
        "--decision",
        str(decision),
        "--build-once-dir",
        str(artifact_root),
        "--upload-target",
        "github-release",
        "--repository",
        "owner/repo",
        "--release-tag",
        "v1.7.0",
        "--output",
        str(final_report),
        "--body",
        str(final_body),
        "--now",
        "2026-11-08T12:05:00Z",
    ]
    return argv, final_report, final_body


class MockUploader:
    """Records calls and never touches the network."""

    def __init__(
        self,
        *,
        existing: dict[str, str] | None = None,
        upload_digest: str | None = None,
        fail: Exception | None = None,
    ) -> None:
        self.existing = dict(existing or {})
        self.upload_digest = upload_digest
        self.fail = fail
        self.calls: list[tuple[str, str]] = []
        self.upload_calls = 0

    def get_digest(self, name: str) -> str | None:
        self.calls.append(("get_digest", name))
        return self.existing.get(name)

    def upload(self, path: Path, name: str) -> None:
        self.upload_calls += 1
        self.calls.append(("upload", name))
        if self.fail is not None:
            raise self.fail
        digest = self.upload_digest or hashlib.sha256(path.read_bytes()).hexdigest()
        self.existing[name] = digest

    def get_url(self, name: str) -> str | None:
        self.calls.append(("get_url", name))
        return f"https://example.invalid/{name}"
