"""F6 / P2-04 body rendering: NOT_UPLOADED is visible and never PASS."""
from __future__ import annotations

from cbm_attach import body


def _report(**overrides):
    data = {
        "cbm_gate_status": "FAIL",
        "upload_status": "NOT_UPLOADED",
        "reason": "CBE_NOT_PASS",
        "reason_detail": "CBE gate_status=FAIL exit_code=3",
        "declared_attached": True,
        "cbe_report_hash": "a" * 64,
        "cbp_report_hash": "b" * 64,
        "artifact_name": "cbm-0.1.0-py3-none-any.whl",
        "artifact_sha256": "c" * 64,
        "uploaded_asset_digest": None,
        "uploaded_asset_url": None,
    }
    data.update(overrides)
    return data


def test_claimed_failure_contains_exact_phrase_and_no_pass() -> None:
    text = body.render(_report())
    assert "## NOT_UPLOADED" in text
    assert "CBM: NOT_UPLOADED" in text
    assert body.P2_04_PHRASE in text
    assert "声明附带但未上传" in text
    assert "CBM: PASS" not in text
    assert "cbm_gate_status: `PASS`" not in text
    assert _report()["cbe_report_hash"] in text
    assert _report()["cbp_report_hash"] in text


def test_not_claimed_has_no_declared_phrase() -> None:
    text = body.render(
        _report(
            cbm_gate_status="NOT_UPLOADED",
            reason="NOT_CLAIMED",
            declared_attached=False,
        )
    )
    assert "## NOT_UPLOADED" in text
    assert body.P2_04_PHRASE not in text
    assert "not claimed" in text


def test_infra_section_is_dedicated_and_not_pass() -> None:
    text = body.render(
        _report(
            cbm_gate_status="SKIPPED_INFRA",
            reason="UPSTREAM_SKIPPED_INFRA",
        )
    )
    assert "## Infrastructure failures" in text
    assert "CBM: NOT_UPLOADED" in text
    assert "SKIPPED_INFRA" in text
    assert "CBM: PASS" not in text
    assert body.P2_04_PHRASE in text


def test_uploaded_section_uses_verified_status() -> None:
    text = body.render(
        _report(
            cbm_gate_status="PASS",
            upload_status="UPLOADED_VERIFIED",
            reason="UPLOADED_VERIFIED",
            uploaded_asset_digest="c" * 64,
        )
    )
    assert "## Optional component attachments" in text
    assert "UPLOADED_VERIFIED" in text
    assert "cbm_gate_status: `PASS`" in text
    assert "NOT_UPLOADED" not in text


def test_unverified_upload_is_not_pass() -> None:
    text = body.render(
        _report(
            cbm_gate_status="FAIL",
            upload_status="UPLOADED_UNVERIFIED",
            reason="UPLOAD_VERIFY_FAILED",
            uploaded_asset_digest="f" * 64,
        )
    )
    assert "## Upload verification failures" in text
    assert "UPLOADED_UNVERIFIED" in text
    assert "CBM: PASS" not in text
    assert "cbm_gate_status: `PASS`" not in text
    assert "must not be treated as PASS" in text


def test_marker_block_replacement_is_idempotent() -> None:
    original = "before\n" + body.wrap_marker(body.render(_report())) + "\nafter\n"
    uploaded = body.render(
        _report(
            cbm_gate_status="PASS",
            upload_status="UPLOADED_VERIFIED",
            reason="UPLOADED_VERIFIED",
            uploaded_asset_digest="c" * 64,
        )
    )
    once = body.replace_marker_block(original, uploaded)
    assert once is not None
    twice = body.replace_marker_block(once, uploaded)
    assert twice is not None
    assert once == twice
    assert once.count(body.MARKER_START) == 1
    assert once.count(body.MARKER_END) == 1
    assert once.startswith("before\n")
    assert once.rstrip().endswith("after")
    assert "UPLOADED_VERIFIED" in once


def test_missing_marker_returns_none() -> None:
    assert body.replace_marker_block("no markers here\n", "x") is None


def test_rendered_fragment_is_marker_delimited() -> None:
    text = body.render_marked(_report())
    assert text.startswith(body.MARKER_START)
    assert text.rstrip().endswith(body.MARKER_END)
