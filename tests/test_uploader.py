"""Uploader adapter tests: GitHub/twine success, failure, digest and timeout."""
from __future__ import annotations

import json
import subprocess
import urllib.error
from pathlib import Path
from types import SimpleNamespace

import pytest

from cbm_attach import uploader
from cbm_attach.reasons import InfraError, InputError, UploadError


class _Response:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self._payload


def _completed(returncode: int = 0, stdout: str = "", stderr: str = ""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_github_asset_digest_url_and_missing_digest(monkeypatch) -> None:
    release = {"assets": [{"name": "a.whl", "digest": "sha256:" + "a" * 64, "url": "u"}]}
    monkeypatch.setattr(uploader.subprocess, "run", lambda *a, **k: _completed(stdout=json.dumps(release)))
    gh = uploader.GitHubReleaseUploader(repository="o/r", release_tag="v1")
    assert gh.get_digest("a.whl") == "a" * 64
    assert gh.get_url("a.whl") == "u"
    assert gh.get_digest("missing") is None
    release["assets"][0]["digest"] = ""
    with pytest.raises(UploadError) as exc:
        gh.get_digest("a.whl")
    assert exc.value.reason_value == "REMOTE_DIGEST_UNAVAILABLE"


def test_github_missing_release_and_malformed_assets(monkeypatch) -> None:
    gh = uploader.GitHubReleaseUploader(repository="o/r", release_tag="v1")
    monkeypatch.setattr(uploader.subprocess, "run", lambda *a, **k: _completed(returncode=1, stderr="HTTP 404"))
    with pytest.raises(InputError) as exc:
        gh.get_digest("a.whl")
    assert exc.value.reason_value == "MISSING_RELEASE"
    monkeypatch.setattr(uploader.subprocess, "run", lambda *a, **k: _completed(stdout="not json"))
    with pytest.raises(InfraError):
        gh.get_digest("a.whl")


def test_github_upload_success_conflict_and_failure(monkeypatch, tmp_path: Path) -> None:
    gh = uploader.GitHubReleaseUploader(repository="o/r", release_tag="v1")
    monkeypatch.setattr(uploader.subprocess, "run", lambda *a, **k: _completed())
    gh.upload(tmp_path / "a.whl", "a.whl")
    monkeypatch.setattr(uploader.subprocess, "run", lambda *a, **k: _completed(returncode=1, stderr="422 already exists"))
    with pytest.raises(UploadError) as exc:
        gh.upload(tmp_path / "a.whl", "a.whl")
    assert exc.value.reason_value == "ASSET_DIGEST_CONFLICT"
    monkeypatch.setattr(uploader.subprocess, "run", lambda *a, **k: _completed(returncode=1, stderr="HTTP 500"))
    with pytest.raises(InfraError):
        gh.upload(tmp_path / "a.whl", "a.whl")


def test_github_timeout_and_missing_binary(monkeypatch, tmp_path: Path) -> None:
    gh = uploader.GitHubReleaseUploader(repository="o/r", release_tag="v1")
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("gh", 1)
    monkeypatch.setattr(uploader.subprocess, "run", timeout)
    with pytest.raises(InfraError):
        gh.get_digest("a.whl")
    def missing(*args, **kwargs):
        raise FileNotFoundError("gh")
    monkeypatch.setattr(uploader.subprocess, "run", missing)
    with pytest.raises(InfraError):
        gh.upload(tmp_path / "a.whl", "a.whl")


def _pypi_payload(filename: str = "cbm_attach-0.1.0-py3-none-any.whl"):
    return json.dumps({"urls": [{"filename": filename, "digests": {"sha256": "b" * 64}}]}).encode()


def test_pypi_metadata_digest_and_url(monkeypatch) -> None:
    monkeypatch.setattr(uploader.urllib.request, "urlopen", lambda *a, **k: _Response(_pypi_payload()))
    pypi = uploader.PypiUploader(project="cbm-attach", version="0.1.0")
    assert pypi.get_digest("cbm_attach-0.1.0-py3-none-any.whl") == "b" * 64
    assert pypi.get_url("cbm_attach-0.1.0-py3-none-any.whl") is not None


def test_pypi_404_and_http_error(monkeypatch) -> None:
    def not_found(*args, **kwargs):
        raise urllib.error.HTTPError("u", 404, "not found", {}, None)
    monkeypatch.setattr(uploader.urllib.request, "urlopen", not_found)
    pypi = uploader.PypiUploader(project="cbm-attach", version="0.1.0")
    assert pypi.get_digest("x") is None
    def server_error(*args, **kwargs):
        raise urllib.error.HTTPError("u", 500, "server", {}, None)
    monkeypatch.setattr(uploader.urllib.request, "urlopen", server_error)
    with pytest.raises(InfraError):
        pypi.get_digest("x")


def test_pypi_missing_digest_and_bad_json(monkeypatch) -> None:
    payload = json.dumps({"urls": [{"filename": "x", "digests": {}}]}).encode()
    monkeypatch.setattr(uploader.urllib.request, "urlopen", lambda *a, **k: _Response(payload))
    pypi = uploader.PypiUploader(project="p", version="1")
    with pytest.raises(UploadError):
        pypi.get_digest("x")
    monkeypatch.setattr(uploader.urllib.request, "urlopen", lambda *a, **k: _Response(b"{"))
    with pytest.raises(InfraError):
        pypi.get_digest("x")


def test_pypi_upload_success_conflict_failure_timeout(monkeypatch, tmp_path: Path) -> None:
    pypi = uploader.PypiUploader(project="p", version="1")
    monkeypatch.setattr(uploader.subprocess, "run", lambda *a, **k: _completed())
    pypi.upload(tmp_path / "x.whl", "x.whl")
    monkeypatch.setattr(uploader.subprocess, "run", lambda *a, **k: _completed(returncode=1, stderr="file already exists"))
    with pytest.raises(UploadError):
        pypi.upload(tmp_path / "x.whl", "x.whl")
    monkeypatch.setattr(uploader.subprocess, "run", lambda *a, **k: _completed(returncode=1, stderr="HTTP 500"))
    with pytest.raises(InfraError):
        pypi.upload(tmp_path / "x.whl", "x.whl")
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("twine", 1)
    monkeypatch.setattr(uploader.subprocess, "run", timeout)
    with pytest.raises(InfraError):
        pypi.upload(tmp_path / "x.whl", "x.whl")


def test_load_uploader_validation() -> None:
    with pytest.raises(InputError):
        uploader.load_uploader("github-release", repository="", release_tag="v1", wheel_name="x")
    with pytest.raises(InputError):
        uploader.load_uploader("pypi", repository="", release_tag="", wheel_name="invalid")
    with pytest.raises(InputError):
        uploader.load_uploader("other", repository="", release_tag="", wheel_name="x")
