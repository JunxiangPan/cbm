"""Zip-bundle build-once support and negative samples."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from cbm_attach import cli
from cbm_attach.artifacts import verify_build_once
from cbm_attach.reasons import GateError, InputError

from tests.helpers import make_artifact, make_cbe, make_cbp, read_json, verify_args


def _make_bundle(tmp_path: Path, *, tamper: bool = False):
    root = tmp_path / "bundle"
    dist = root / "dist"
    dist.mkdir(parents=True)
    archive = dist / "cbm-0.2.0rc1.zip"
    manifest = {"schema": 2, "entries": [{"path": "src/app.py", "sha256": "a" * 64}]}
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("update-manifest.json", json.dumps(manifest))
        handle.writestr("src/app.py", "print('ok')\n")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (root / "BUNDLE_SHA256").write_text(f"{digest}  dist/{archive.name}\n", encoding="utf-8")
    (root / "RELEASE_ASSETS.sha256").write_text(
        f"{digest}  dist/{archive.name}\n", encoding="utf-8"
    )
    (root / "bundle-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    if tamper:
        archive.write_bytes(b"changed")
    return root, archive, digest, manifest


def test_zip_bundle_is_accepted_and_manifest_recorded(tmp_path: Path) -> None:
    root, archive, digest, manifest = _make_bundle(tmp_path)
    artifact = verify_build_once(root, artifact_type="zip-bundle")
    assert artifact.artifact_type == "zip-bundle"
    assert artifact.name == archive.name
    assert artifact.sha256 == digest
    assert artifact.bundle_manifest == manifest
    assert artifact.bundle_manifest_sha256


def test_zip_bundle_tamper_is_rejected(tmp_path: Path) -> None:
    root, _archive, _digest, _manifest = _make_bundle(tmp_path, tamper=True)
    with pytest.raises(GateError) as exc:
        verify_build_once(root, artifact_type="zip-bundle")
    assert exc.value.reason_value == "ARTIFACT_HASH_MISMATCH"


def test_zip_bundle_needs_inventory_entry(tmp_path: Path) -> None:
    root, archive, _digest, _manifest = _make_bundle(tmp_path)
    (root / "RELEASE_ASSETS.sha256").write_text(
        f"{'0' * 64}  dist/{archive.name}\n", encoding="utf-8"
    )
    with pytest.raises(GateError):
        verify_build_once(root, artifact_type="zip-bundle")


def test_cli_verifies_zip_bundle(tmp_path: Path) -> None:
    root, archive, digest, _manifest = _make_bundle(tmp_path)
    cbe = make_cbe()
    cbp = make_cbp(digest, artifact_hashes={archive.name: digest})
    argv, report_path, body_path, decision_path = verify_args(
        tmp_path, cbe=cbe, cbp=cbp, artifact_root=root
    )
    argv += ["--artifact-type", "zip-bundle"]
    code = cli.main(argv)
    assert code == 0
    report = read_json(report_path)
    assert report["artifact_type"] == "zip-bundle"
    assert report["artifact_sha256"] == digest
    assert report["bundle_manifest_sha256"]
    assert report["schema_version"] == "2"
    assert report_path.is_file() and body_path.is_file() and decision_path.is_file()
