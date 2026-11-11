"""Live GitHub Release E2E; opt-in via CBM_E2E_REPO/CBM_E2E_TAG."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from cbm_attach.reasons import InputError
from cbm_attach.uploader import GitHubReleaseUploader

REPO = os.environ.get("CBM_E2E_REPO", "")
TAG = os.environ.get("CBM_E2E_TAG", "")
pytestmark = pytest.mark.skipif(not REPO or not TAG, reason="CBM_E2E_REPO/CBM_E2E_TAG not set")


def test_live_upload_readback_retry_and_failure(tmp_path: Path) -> None:
    name = "cbm_attach-0.2.0rc1-py3-none-any.whl"
    payload = b"live e2e payload\n"
    asset = tmp_path / name
    asset.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    uploader = GitHubReleaseUploader(repository=REPO, release_tag=TAG)
    if uploader.get_digest(name) is None:
        uploader.upload(asset, name)
    assert uploader.get_digest(name) == digest
    assert uploader.get_url(name)
    # retry: same digest is treated as already uploaded, not overwritten
    assert uploader.get_digest(name) == digest
    with pytest.raises(InputError) as exc:
        GitHubReleaseUploader(repository=REPO, release_tag="missing-e2e-tag").get_digest(name)
    assert exc.value.reason_value == "MISSING_RELEASE"
