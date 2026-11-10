"""Static guard for the trusted-publisher PyPI workflow."""
from __future__ import annotations

from pathlib import Path

import yaml


WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "pypi-publish.yml"
TEXT = WORKFLOW.read_text(encoding="utf-8")


def test_trusted_publisher_shape() -> None:
    data = yaml.load(TEXT, Loader=yaml.BaseLoader)
    assert data["name"] == "pypi-publish"
    assert data["on"]["workflow_dispatch"]["inputs"]["tag"]["default"] == "v0.1.1"
    assert data["permissions"]["id-token"] == "write"
    assert data["permissions"]["contents"] == "read"
    job = data["jobs"]["publish"]
    assert job["environment"] == "pypi"
    assert job["runs-on"] == "ubuntu-latest"


def test_release_asset_pattern_is_underscore() -> None:
    assert "-p 'cbm_attach-*'" in TEXT
    assert "cbm-attach-*" not in TEXT


def test_publish_action_and_no_token() -> None:
    assert "pypa/gh-action-pypi-publish@release/v1" in TEXT
    assert "packages-dir: dist/" in TEXT
    assert "password:" not in TEXT
    assert "TWINE_PASSWORD" not in TEXT
