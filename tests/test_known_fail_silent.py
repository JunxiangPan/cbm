"""B5 FIXED: the old KNOWN_FAIL_SILENT canary is flipped.

CBS v1.7.0-integration `fa1740f` now renders a missing CBM as a visible
`CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT` section. This test asserts the fixed
behavior (and the exact phrase when CBM is declared attached), so it must stay
green. The historical KNOWN_FAIL_SILENT classification is retained only to test
the probe's detector, not as an accepted CBM state.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from tools.check_b5 import (
    B5_MAYBE_FIXED,
    CBS_BODY_GENERATOR_NOT_FOUND,
    CBS_BODY_GENERATOR_UNIMPORTABLE,
    KNOWN_FAIL_SILENT,
    UNEXPECTED_OUTPUT,
    classify_body_output,
    probe,
)


ROOT = Path(__file__).resolve().parents[2]
CBS_REPO = Path(os.environ.get("CBS_REPO", ROOT / "public-release")).resolve()


def test_b5_fixed_cbs_body_emits_not_uploaded(tmp_path: Path) -> None:
    # Probe detector maintenance: the old defect still classifies as KNOWN,
    # the fixed output as B5_MAYBE_FIXED, and an unknown shape is flagged.
    assert classify_body_output("## NOT_UPLOADED\n- none\n") == KNOWN_FAIL_SILENT
    assert (
        classify_body_output("CBM: NOT_UPLOADED\nEVIDENCE_ABSENT\n")
        == B5_MAYBE_FIXED
    )
    assert classify_body_output("something unexpected\n") == UNEXPECTED_OUTPUT

    missing = probe(tmp_path / "missing-cbs")
    assert missing.status == CBS_BODY_GENERATOR_NOT_FOUND

    unimportable = tmp_path / "bad_body.py"
    unimportable.write_text("def build(:\n", encoding="utf-8")
    bad = probe(unimportable)
    assert bad.status == CBS_BODY_GENERATOR_UNIMPORTABLE

    # Real fixed CBS: must emit the visible CBM section, never `- none`.
    result = probe(CBS_REPO)
    if result.status == CBS_BODY_GENERATOR_NOT_FOUND:
        pytest.skip(f"SKIP_REASON={CBS_BODY_GENERATOR_NOT_FOUND}")
    if result.status == CBS_BODY_GENERATOR_UNIMPORTABLE:
        pytest.fail(f"FAIL_REASON={CBS_BODY_GENERATOR_UNIMPORTABLE}: {result.detail}")
    assert result.status == B5_MAYBE_FIXED, result.status
    assert "CBM: NOT_UPLOADED" in result.text
    assert "EVIDENCE_ABSENT" in result.text
    assert "- none" not in result.text

    declared = probe(CBS_REPO, declared_components=["cbm"])
    assert declared.status == B5_MAYBE_FIXED
    assert "declared_attached: `true`" in declared.text
    assert "declared as attached but not uploaded" in declared.text
