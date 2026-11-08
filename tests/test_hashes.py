"""Raw-byte report hashes, evidence hashes, and build-once tamper checks."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from cbm_attach.artifacts import extract_zip, verify_build_once
from cbm_attach.cli import _canonical_sha256
from cbm_attach.reasons import GateError, InputError
from cbm_attach.reports import load_report

from tests.helpers import WHEEL_NAME, make_artifact, make_cbe, write_json


def test_report_hash_is_raw_bytes(tmp_path: Path) -> None:
    data = make_cbe()
    path = write_json(tmp_path / "cbe.json", data)
    report = load_report(path, "cbe")
    assert report.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()


def test_whitespace_changes_report_hash(tmp_path: Path) -> None:
    data = make_cbe()
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps(data, indent=2), encoding="utf-8")
    second.write_text(json.dumps(data), encoding="utf-8")
    assert load_report(first, "cbe").sha256 != load_report(second, "cbe").sha256


def test_evidence_hash_ignores_key_order() -> None:
    left = {"a": 1, "b": 2, "evidence_sha256": "x"}
    right = {"b": 2, "evidence_sha256": "x", "a": 1}
    assert _canonical_sha256(left) == _canonical_sha256(right)


def test_evidence_hash_changes_with_content() -> None:
    assert _canonical_sha256({"a": 1}) != _canonical_sha256({"a": 2})


def test_report_hash_is_not_the_evidence_field(tmp_path: Path) -> None:
    data = make_cbe(evidence_sha256="b" * 64)
    report = load_report(write_json(tmp_path / "cbe.json", data), "cbe")
    assert report.sha256 != "b" * 64


def test_artifact_hash_prefix_and_star_are_accepted(tmp_path: Path) -> None:
    root, wheel, digest = make_artifact(tmp_path)
    (root / "WHEEL_SHA256").write_text(
        f"sha256:{digest} *dist/{wheel.name}\n", encoding="utf-8"
    )
    artifact = verify_build_once(root)
    assert artifact.sha256 == digest
    assert artifact.name == WHEEL_NAME


def test_artifact_tamper_is_detected(tmp_path: Path) -> None:
    root, wheel, _ = make_artifact(tmp_path)
    wheel.write_bytes(b"tampered\n")
    with pytest.raises(GateError) as captured:
        verify_build_once(root)
    assert captured.value.reason_value == "ARTIFACT_HASH_MISMATCH"


def test_release_assets_extra_tamper_is_detected(tmp_path: Path) -> None:
    root, _wheel, digest = make_artifact(tmp_path)
    extra = root / "dist" / "notes.txt"
    extra.write_text("x", encoding="utf-8")
    with (root / "RELEASE_ASSETS.sha256").open("a", encoding="utf-8") as handle:
        handle.write(f"{'0' * 64}  dist/notes.txt\n")
    with pytest.raises(GateError) as captured:
        verify_build_once(root)
    assert captured.value.reason_value == "ARTIFACT_HASH_MISMATCH"
    assert digest


def test_missing_wheel_sha_is_input_error(tmp_path: Path) -> None:
    root, _wheel, _ = make_artifact(tmp_path)
    (root / "WHEEL_SHA256").unlink()
    with pytest.raises(InputError) as captured:
        verify_build_once(root)
    assert captured.value.reason_value == "MISSING_BUILD_ONCE_ARTIFACT"


def test_zip_slip_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "evil.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../evil.txt", "x")
    with pytest.raises(InputError):
        extract_zip(archive, tmp_path / "out")


def test_zip_symlink_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "link.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        info = zipfile.ZipInfo("link")
        info.external_attr = (0o120777 << 16)
        handle.writestr(info, "target")
    with pytest.raises(InputError):
        extract_zip(archive, tmp_path / "out")


def test_safe_zip_extracts(tmp_path: Path) -> None:
    archive = tmp_path / "safe.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("build-once/WHEEL_SHA256", "x")
    out = extract_zip(archive, tmp_path / "out")
    assert (out / "build-once" / "WHEEL_SHA256").is_file()



def test_release_assets_basename_only_is_accepted(tmp_path: Path) -> None:
    root, wheel, digest = make_artifact(tmp_path)
    text = chr(10).join([f"{digest}  {wheel.name}", ""])
    (root / "RELEASE_ASSETS.sha256").write_text(text, encoding="utf-8")
    artifact = verify_build_once(root)
    assert artifact.sha256 == digest


def test_release_assets_self_entry_is_not_self_hashed(tmp_path: Path) -> None:
    root, wheel, digest = make_artifact(tmp_path)
    text = chr(10).join(
        [f"{digest}  {wheel.name}", f"{'0' * 64}  RELEASE_ASSETS.sha256", ""]
    )
    (root / "RELEASE_ASSETS.sha256").write_text(text, encoding="utf-8")
    artifact = verify_build_once(root)
    assert artifact.sha256 == digest
