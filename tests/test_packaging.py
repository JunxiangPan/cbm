"""Packaging and CLI entrypoint checks (no network/build dependency)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_has_distribution_license_and_console_script() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "cbm-attach"' in text
    assert "Apache-2.0" in text
    assert 'cbm-attach = "cbm_attach.cli:main"' in text
    assert "readme = \"README.md\"" in text
    assert "Homepage" in text and "Repository" in text


def test_apache_license_is_present() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text
    assert "Version 2.0" in license_text


def test_readme_quickstart_and_scope() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "pip install cbm-attach" in text
    assert "cbm-attach --help" in text
    assert "sidecar attachment" in text
    assert "No A-F live E2E" in text
    assert "No tag, GitHub Release" not in text


def test_module_help_runs() -> None:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    result = subprocess.run(
        [sys.executable, "-m", "cbm_attach.cli", "--help"],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert result.returncode == 0
    assert "verify" in result.stdout
    assert "upload" in result.stdout
