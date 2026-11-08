"""KNOWN_FAIL_SILENT: current CBS body generator hides a completely missing CBM.

This is a **conditional green** canary, not an acceptance:

- CBS output `- none`, no CBM, no `EVIDENCE_ABSENT` -> KNOWN_FAIL_SILENT (green).
- CBS output `CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT`, no `- none` ->
  B5_MAYBE_FIXED. The CLI exits 0 with a prominent message; this pytest canary
  fails so the flip is not forgotten.
- CBS file missing -> skip with `SKIP_REASON=CBS_BODY_GENERATOR_NOT_FOUND`.
- CBS file exists but cannot import/build -> FAIL with
  `FAIL_REASON=CBS_BODY_GENERATOR_UNIMPORTABLE` (not skip).
- Anything else -> UNEXPECTED_OUTPUT, a failure.

When B5 is fixed, flip the assertions to require `CBM: NOT_UPLOADED` and
`EVIDENCE_ABSENT`, and remove the `known_fail_silent` marker.
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

pytestmark = pytest.mark.known_fail_silent


def test_known_fail_silent_cbs_body_omits_missing_cbm(tmp_path: Path) -> None:
    # Probe maintenance contract: all four classifications are exercised even
    # when the real CBS checkout is absent.
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

    # Real CBS checkout: current defect or a call to flip the canary.
    result = probe(CBS_REPO)
    if result.status == CBS_BODY_GENERATOR_NOT_FOUND:
        pytest.skip(f"SKIP_REASON={CBS_BODY_GENERATOR_NOT_FOUND}")
    if result.status == CBS_BODY_GENERATOR_UNIMPORTABLE:
        pytest.fail(f"FAIL_REASON={CBS_BODY_GENERATOR_UNIMPORTABLE}: {result.detail}")
    if result.status == B5_MAYBE_FIXED:
        pytest.fail(
            "B5_MAYBE_FIXED: CBS no longer hides a missing CBM. "
            "Flip this test to require CBM: NOT_UPLOADED + EVIDENCE_ABSENT "
            "and remove the known_fail_silent marker."
        )
    assert result.status == KNOWN_FAIL_SILENT, result.status
    assert "- none" in result.text
    assert "CBM" not in result.text
    assert "CBM: NOT_UPLOADED" not in result.text
    assert "EVIDENCE_ABSENT" not in result.text
