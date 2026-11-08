"""Upload adapters.

Both adapters are idempotent and refuse to overwrite an existing asset.  They
never pass ``--clobber`` or ``--skip-existing``: a same-digest asset is treated
as already uploaded, a different-digest asset is a hard failure.
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Protocol

from .reasons import InfraError, InputError, Reason, UploadError


HEX64_RE = re.compile(r"^[a-fA-F0-9]{64}$")


def normalise_digest(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.startswith("sha256:"):
        text = text[len("sha256:") :]
    return text.lower() if HEX64_RE.fullmatch(text) else None


class Uploader(Protocol):
    def get_digest(self, name: str) -> str | None: ...

    def upload(self, path: Path, name: str) -> None: ...

    def get_url(self, name: str) -> str | None: ...


def _classify_command_error(stderr: str, *, missing_release: bool = False) -> Exception:
    text = stderr.lower()
    if missing_release and ("http 404" in text or "not found" in text):
        return InputError(f"release not found: {stderr.strip()}", reason=Reason.MISSING_RELEASE)
    if "http 404" in text or "not found" in text:
        return InputError(f"release not found: {stderr.strip()}", reason=Reason.MISSING_RELEASE)
    if "http 5" in text or "timeout" in text or "connection" in text or "timed out" in text:
        return InfraError(
            f"upload infrastructure failure: {stderr.strip()[:500]}",
            reason=Reason.INFRA_UPLOAD_FAILED,
        )
    return UploadError(f"upload failed: {stderr.strip()[:500]}", reason=Reason.UPLOAD_FAILED)


class GitHubReleaseUploader:
    def __init__(
        self,
        *,
        repository: str,
        release_tag: str,
        gh_bin: str = "gh",
        timeout: int = 180,
    ) -> None:
        self.repository = repository
        self.release_tag = release_tag
        self.gh_bin = gh_bin
        self.timeout = timeout

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [self.gh_bin, *args],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise InfraError(
                f"{self.gh_bin}: command not found",
                reason=Reason.INFRA_UPLOAD_FAILED,
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise InfraError(
                f"{self.gh_bin} timed out",
                reason=Reason.INFRA_UPLOAD_FAILED,
            ) from exc

    def _assets(self) -> list[dict]:
        result = self._run(
            [
                "release",
                "view",
                self.release_tag,
                "--repo",
                self.repository,
                "--json",
                "assets",
            ]
        )
        if result.returncode != 0:
            raise _classify_command_error(result.stderr, missing_release=True)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise InfraError(
                f"cannot parse release assets: {exc}",
                reason=Reason.INFRA_UPLOAD_FAILED,
            ) from exc
        assets = payload.get("assets", [])
        return assets if isinstance(assets, list) else []

    def _asset(self, name: str) -> dict | None:
        for asset in self._assets():
            if isinstance(asset, dict) and asset.get("name") == name:
                return asset
        return None

    def get_digest(self, name: str) -> str | None:
        asset = self._asset(name)
        if asset is None:
            return None
        digest = normalise_digest(asset.get("digest"))
        if digest is None:
            raise UploadError(
                f"asset {name!r} exists but its remote digest is unavailable",
                reason=Reason.REMOTE_DIGEST_UNAVAILABLE,
            )
        return digest

    def get_url(self, name: str) -> str | None:
        asset = self._asset(name)
        if asset is None:
            return None
        url = asset.get("url")
        return url if isinstance(url, str) else None

    def upload(self, path: Path, name: str) -> None:
        result = self._run(
            [
                "release",
                "upload",
                self.release_tag,
                str(path),
                "--repo",
                self.repository,
            ]
        )
        if result.returncode != 0:
            text = result.stderr.lower()
            if "422" in text or "already exists" in text:
                raise UploadError(
                    f"asset {name!r} already exists; refusing to overwrite",
                    reason=Reason.ASSET_DIGEST_CONFLICT,
                )
            raise _classify_command_error(result.stderr)


class PypiUploader:
    """Minimal PyPI adapter using the JSON API for digest checks and twine to upload."""

    def __init__(
        self,
        *,
        project: str,
        version: str,
        twine_bin: str = "twine",
        timeout: int = 180,
    ) -> None:
        self.project = project
        self.version = version
        self.twine_bin = twine_bin
        self.timeout = timeout

    @property
    def _json_url(self) -> str:
        return f"https://pypi.org/pypi/{self.project}/{self.version}/json"

    def _metadata(self) -> dict | None:
        try:
            with urllib.request.urlopen(self._json_url, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise InfraError(
                f"PyPI JSON API HTTP {exc.code}",
                reason=Reason.INFRA_UPLOAD_FAILED,
            ) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise InfraError(
                f"PyPI JSON API failed: {exc}",
                reason=Reason.INFRA_UPLOAD_FAILED,
            ) from exc

    def get_digest(self, name: str) -> str | None:
        payload = self._metadata()
        if payload is None:
            return None
        urls = payload.get("urls", [])
        if not isinstance(urls, list):
            return None
        for item in urls:
            if isinstance(item, dict) and item.get("filename") == name:
                digests = item.get("digests")
                digest = normalise_digest(digests.get("sha256")) if isinstance(digests, dict) else None
                if digest is None:
                    raise UploadError(
                        f"PyPI file {name!r} exists but has no sha256 digest",
                        reason=Reason.REMOTE_DIGEST_UNAVAILABLE,
                    )
                return digest
        return None

    def get_url(self, name: str) -> str | None:
        return self._json_url if self.get_digest(name) is not None else None

    def upload(self, path: Path, name: str) -> None:
        try:
            result = subprocess.run(
                [self.twine_bin, "upload", str(path)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise InfraError(
                f"{self.twine_bin}: command not found",
                reason=Reason.INFRA_UPLOAD_FAILED,
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise InfraError(
                f"{self.twine_bin} timed out",
                reason=Reason.INFRA_UPLOAD_FAILED,
            ) from exc
        if result.returncode != 0:
            text = result.stderr.lower()
            if "already exists" in text or "file already exists" in text:
                raise UploadError(
                    f"PyPI file {name!r} already exists; refusing to overwrite",
                    reason=Reason.ASSET_DIGEST_CONFLICT,
                )
            raise _classify_command_error(result.stderr)


def load_uploader(
    target: str,
    *,
    repository: str,
    release_tag: str,
    wheel_name: str,
    gh_bin: str = "gh",
    twine_bin: str = "twine",
) -> Uploader:
    if target == "github-release":
        if not repository or not release_tag:
            raise InputError(
                "github-release upload requires repository and release_tag",
                reason=Reason.MISSING_ARGUMENT,
            )
        return GitHubReleaseUploader(
            repository=repository,
            release_tag=release_tag,
            gh_bin=gh_bin,
        )
    if target == "pypi":
        match = re.match(r"^(?P<project>[^-]+)-(?P<version>[^-]+)-", wheel_name)
        if not match:
            raise InputError(
                f"cannot derive PyPI project/version from {wheel_name!r}",
                reason=Reason.SCHEMA_VIOLATION,
            )
        return PypiUploader(
            project=match.group("project"),
            version=match.group("version"),
            twine_bin=twine_bin,
        )
    raise InputError(
        f"unsupported upload target: {target!r}",
        reason=Reason.UNSUPPORTED_UPLOAD_TARGET,
    )
