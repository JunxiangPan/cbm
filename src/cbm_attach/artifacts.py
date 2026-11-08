"""Build-once artifact handling and GitHub artifact download.

Hard rule: CBM never builds the package.  It downloads the artifact produced by
the build-once job, verifies every hash in ``WHEEL_SHA256`` and
``RELEASE_ASSETS.sha256``, and only then may the uploader see the file.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .reasons import GateError, InfraError, InputError, Reason
from .reports import Report, find_report_file, load_report


HEX64_RE = re.compile(r"^[a-fA-F0-9]{64}$")
MAX_EXTRACT_BYTES = 512 * 1024 * 1024


@dataclass(frozen=True)
class Artifact:
    name: str
    path: Path
    sha256: str
    assets: dict[str, str]


def _normalise_hash(value: str) -> str:
    value = value.strip()
    if value.startswith("sha256:"):
        value = value[len("sha256:") :]
    return value.lower()


def _safe_relative(raw: str) -> PurePosixPath:
    text = raw.replace("\\", "/").strip()
    if not text:
        raise InputError("empty path in hash manifest", reason=Reason.SCHEMA_VIOLATION)
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or any(":" in part for part in path.parts)
    ):
        raise InputError(
            f"unsafe path in hash manifest: {raw!r}",
            reason=Reason.SCHEMA_VIOLATION,
        )
    return path


def _parse_hash_manifest(path: Path) -> dict[str, str]:
    """Parse ``<sha256>  <path>`` lines, allowing a ``sha256:`` prefix."""
    if not path.is_file():
        raise InputError(
            f"{path}: hash manifest not found",
            reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
        )
    result: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        parts = text.split(None, 1)
        digest = _normalise_hash(parts[0])
        if not HEX64_RE.fullmatch(digest):
            raise InputError(
                f"{path}:{line_number}: invalid sha256 {parts[0]!r}",
                reason=Reason.SCHEMA_VIOLATION,
            )
        if len(parts) == 1:
            key = ""
        else:
            raw_path = parts[1].strip().lstrip("*").strip()
            key = str(_safe_relative(raw_path))
        if key in result and result[key] != digest:
            raise InputError(
                f"{path}:{line_number}: conflicting digests for {key!r}",
                reason=Reason.REPORT_INCONSISTENT,
            )
        result[key] = digest
    if not result:
        raise InputError(
            f"{path}: no hash entries",
            reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
        )
    return result


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _lookup(mapping: dict[str, str], wheel: Path, root: Path) -> str | None:
    candidates = []
    try:
        candidates.append(str(wheel.resolve().relative_to(root.resolve())).replace("\\", "/"))
    except ValueError:
        pass
    candidates.extend([wheel.name, f"dist/{wheel.name}", f"./{wheel.name}"])
    for key in candidates:
        if key in mapping:
            return mapping[key]
    return mapping.get("")


def locate_build_once_root(root: str | Path) -> Path:
    """Find the directory containing ``WHEEL_SHA256`` inside an artifact zip."""
    base = Path(root)
    direct = base / "WHEEL_SHA256"
    if direct.is_file():
        return base
    matches = sorted(base.rglob("WHEEL_SHA256"))
    if len(matches) == 1:
        return matches[0].parent
    raise InputError(
        f"{base}: expected exactly one WHEEL_SHA256, found {len(matches)}",
        reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
    )


def verify_build_once(directory: str | Path) -> Artifact:
    """Verify the build-once directory and return the single wheel."""
    root = Path(directory)
    if not root.is_dir():
        raise InputError(
            f"{root}: build-once artifact directory not found",
            reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
        )

    wheel_hashes = _parse_hash_manifest(root / "WHEEL_SHA256")
    asset_hashes = _parse_hash_manifest(root / "RELEASE_ASSETS.sha256")

    search_root = root / "dist" if (root / "dist").is_dir() else root
    wheels = sorted(search_root.glob("*.whl"))
    if len(wheels) != 1:
        raise InputError(
            f"{root}: expected exactly one .whl, found {len(wheels)}",
            reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
        )
    wheel = wheels[0]
    if wheel.is_symlink():
        raise InputError(f"{wheel}: symlink is not allowed", reason=Reason.SCHEMA_VIOLATION)

    actual = _hash_file(wheel)
    expected = _lookup(wheel_hashes, wheel, root)
    if expected is None:
        raise InputError(
            f"{wheel.name}: not listed in WHEEL_SHA256",
            reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
        )
    if actual != expected:
        raise GateError(
            f"{wheel.name}: sha256 {actual} != WHEEL_SHA256 {expected}",
            reason=Reason.ARTIFACT_HASH_MISMATCH,
        )

    release_expected = _lookup(asset_hashes, wheel, root)
    if release_expected is None:
        raise GateError(
            f"{wheel.name}: not listed in RELEASE_ASSETS.sha256",
            reason=Reason.ARTIFACT_HASH_MISMATCH,
        )
    if release_expected != actual:
        raise GateError(
            f"{wheel.name}: sha256 {actual} != RELEASE_ASSETS.sha256 {release_expected}",
            reason=Reason.ARTIFACT_HASH_MISMATCH,
        )

    for relative, expected_hash in asset_hashes.items():
        if not relative:
            continue
        # §11: the inventory lists published assets except itself.  A manifest
        # that still self-lists must not be self-hashed.
        if relative == "RELEASE_ASSETS.sha256":
            continue
        parts = _safe_relative(relative).parts
        candidate = root.joinpath(*parts)
        if not candidate.is_file() and len(parts) == 1 and (root / "dist").is_dir():
            # §11 uses bare basenames; the wheel may live under dist/.
            candidate = root / "dist" / parts[0]
        resolved_root = root.resolve()
        resolved_candidate = candidate.resolve()
        if (
            resolved_root != resolved_candidate
            and resolved_root not in resolved_candidate.parents
        ):
            raise InputError(
                f"{candidate}: listed path escapes the build-once directory",
                reason=Reason.SCHEMA_VIOLATION,
            )
        if not candidate.is_file():
            raise InputError(
                f"{candidate}: listed in RELEASE_ASSETS.sha256 but missing",
                reason=Reason.MISSING_BUILD_ONCE_ARTIFACT,
            )
        if candidate.is_symlink():
            raise InputError(
                f"{candidate}: symlink is not allowed",
                reason=Reason.SCHEMA_VIOLATION,
            )
        if _hash_file(candidate) != expected_hash:
            raise GateError(
                f"{candidate}: sha256 mismatch against RELEASE_ASSETS.sha256",
                reason=Reason.ARTIFACT_HASH_MISMATCH,
            )

    return Artifact(
        name=wheel.name,
        path=wheel,
        sha256=actual,
        assets=asset_hashes,
    )


def extract_zip(zip_path: str | Path, destination: str | Path) -> Path:
    """Extract an artifact zip without path traversal or symlinks."""
    archive = Path(zip_path)
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    if not zipfile.is_zipfile(archive):
        raise InputError(
            f"{archive}: not a zip archive",
            reason=Reason.SCHEMA_VIOLATION,
        )
    total = 0
    with zipfile.ZipFile(archive) as handle:
        for info in handle.infolist():
            name = info.filename.replace("\\", "/")
            relative = _safe_relative(name)
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise InputError(
                    f"{archive}: symlink member is not allowed: {name!r}",
                    reason=Reason.SCHEMA_VIOLATION,
                )
            total += max(0, info.file_size)
            if total > MAX_EXTRACT_BYTES:
                raise InputError(
                    f"{archive}: extracted size exceeds {MAX_EXTRACT_BYTES} bytes",
                    reason=Reason.SCHEMA_VIOLATION,
                )
            target = root.joinpath(*relative.parts)
            resolved_root = root.resolve()
            resolved_target = target.resolve()
            if resolved_root != resolved_target and resolved_root not in resolved_target.parents:
                raise InputError(
                    f"{archive}: path escapes destination: {name!r}",
                    reason=Reason.SCHEMA_VIOLATION,
                )
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with handle.open(info) as source, target.open("wb") as sink:
                shutil.copyfileobj(source, sink)
    return root


def _classify_gh_error(stderr: str, *, missing_reason: Reason) -> Exception:
    text = stderr.lower()
    if "http 404" in text or "not found" in text:
        return InputError(f"artifact not found: {stderr.strip()}", reason=missing_reason)
    if "http 403" in text or "http 401" in text or "forbidden" in text:
        return InputError(
            f"artifact access forbidden: {stderr.strip()}",
            reason=Reason.ARTIFACT_FORBIDDEN,
        )
    return InfraError(
        f"artifact fetch failed: {stderr.strip()[:500]}",
        reason=Reason.INFRA_FETCH_FAILED,
    )


def fetch_artifact(
    *,
    repository: str,
    run_id: str,
    artifact_name: str,
    destination: str | Path,
    missing_reason: Reason,
    gh_bin: str = "gh",
) -> Path:
    """Download one run artifact through ``gh api`` and extract it."""
    if not re.fullmatch(r"[0-9]+", str(run_id)):
        raise InputError(f"invalid run id: {run_id!r}", reason=Reason.MISSING_ARGUMENT)
    if not artifact_name:
        raise InputError("empty artifact name", reason=Reason.MISSING_ARGUMENT)

    try:
        listed = subprocess.run(
            [
                gh_bin,
                "api",
                f"repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except FileNotFoundError as exc:
        raise InfraError(
            f"{gh_bin}: command not found",
            reason=Reason.INFRA_FETCH_FAILED,
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise InfraError(
            f"{gh_bin} timed out listing artifacts",
            reason=Reason.INFRA_FETCH_FAILED,
        ) from exc

    if listed.returncode != 0:
        raise _classify_gh_error(listed.stderr, missing_reason=missing_reason)

    try:
        payload: dict[str, Any] = json.loads(listed.stdout)
    except json.JSONDecodeError as exc:
        raise InfraError(
            f"cannot parse artifact listing: {exc}",
            reason=Reason.INFRA_FETCH_FAILED,
        ) from exc
    match = None
    for item in payload.get("artifacts", []):
        if isinstance(item, dict) and item.get("name") == artifact_name:
            match = item
            break
    if match is None:
        raise InputError(
            f"run {run_id}: artifact {artifact_name!r} not found",
            reason=missing_reason,
        )
    artifact_id = match.get("id")
    if not isinstance(artifact_id, int):
        raise InfraError(
            f"run {run_id}: artifact {artifact_name!r} has no id",
            reason=Reason.INFRA_FETCH_FAILED,
        )

    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as handle:
        zip_path = Path(handle.name)
    try:
        with zip_path.open("wb") as sink:
            download = subprocess.run(
                [
                    gh_bin,
                    "api",
                    f"repos/{repository}/actions/artifacts/{artifact_id}/zip",
                ],
                stdout=sink,
                stderr=subprocess.PIPE,
                timeout=300,
                check=False,
            )
        if download.returncode != 0:
            stderr = download.stderr.decode("utf-8", "replace") if download.stderr else ""
            raise _classify_gh_error(stderr, missing_reason=missing_reason)
        return extract_zip(zip_path, root)
    finally:
        zip_path.unlink(missing_ok=True)


def fetch_report(
    *,
    repository: str,
    run_id: str,
    artifact_name: str,
    kind: str,
    destination: str | Path,
    gh_bin: str = "gh",
) -> Report:
    """Fetch an artifact and load the single report JSON it contains."""
    missing = Reason.MISSING_CBE_REPORT if kind == "cbe" else Reason.MISSING_CBP_REPORT
    root = fetch_artifact(
        repository=repository,
        run_id=run_id,
        artifact_name=artifact_name,
        destination=destination,
        missing_reason=missing,
        gh_bin=gh_bin,
    )
    report_path = find_report_file(root, kind)
    return load_report(report_path, kind)
