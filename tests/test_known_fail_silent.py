"""KNOWN_FAIL_SILENT: current CBS body generator hides a completely missing CBM.

This test is deliberately green while the upstream defect exists. It asserts the
current CBS behavior (`- none`) and the absence of `CBM: NOT_UPLOADED` /
`EVIDENCE_ABSENT`. It is not an acceptance of the defect; when CBS implements
`docs/CBS_BODY_REQUIREMENT.md`, this test must be updated to assert the fixed
behavior and this marker removed.

The probe imports the real CBS `tools/release_body_v17.py` when the CBS checkout
is available (set `CBS_REPO`, or use the sibling `public-release` directory).
When it is not available, the test uses a minimal mock that reproduces the
current `not_uploaded ... or ['- none']` behavior, so a CBM-only checkout still
records the known gap instead of skipping it.

Proof in this workspace (2026-11-08): the real CBS file was loaded and the
assertions passed with `- none`, no `CBM`, no `EVIDENCE_ABSENT`.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest


KNOWN_FAIL_SILENT = True
ROOT = Path(__file__).resolve().parents[2]
CBS_REPO = Path(os.environ.get("CBS_REPO", ROOT / "public-release")).resolve()
CBS_BODY = CBS_REPO / "tools" / "release_body_v17.py"

pytestmark = pytest.mark.known_fail_silent


def _load_cbs_build():
    spec = importlib.util.spec_from_file_location("cbs_release_body_v17", CBS_BODY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build


def _mock_cbs_build(report: dict, wheel: Path) -> str:
    """Reproduce the audited CBS lines: not_uploaded or '- none'."""
    not_uploaded = report.get("not_uploaded", [])
    lines = ["## NOT_UPLOADED", ""]
    lines += [f"- {item}" for item in not_uploaded] or ["- none"]
    return "\n".join(lines) + "\n"


def _build_factory():
    if CBS_BODY.is_file():
        return _load_cbs_build(), "cbs"
    return _mock_cbs_build, "mock"


def test_known_fail_silent_cbs_body_omits_missing_cbm(tmp_path: Path) -> None:
    build, source = _build_factory()
    assert source in {"cbs", "mock"}
    wheel = tmp_path / "pkg.whl"
    wheel.write_bytes(b"wheel")

    # A report with no CBM entry at all: exactly the "CBM never ran" case.
    report = {
        "version": "v1.7.0",
        "gate_status": "PASS",
        "applicable_gate_count": 4,
        "skip_count": 0,
        "skip_ratio": 0.0,
        "blocking_skip": False,
        "gates": [],
        "not_uploaded": [],
    }
    text = build(report, wheel)

    assert KNOWN_FAIL_SILENT is True
    assert "## NOT_UPLOADED" in text
    assert "- none" in text, source
    assert "CBM" not in text, source
    assert "CBM: NOT_UPLOADED" not in text, source
    assert "EVIDENCE_ABSENT" not in text, source
