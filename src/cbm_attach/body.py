"""Release-body fragments for CBM.

CBM never writes the whole CBS Release body.  It emits one marker-delimited
fragment.  The CBS body generator merges it after publish; an asynchronous CBM
run may replace exactly this marker block only after a verified upload, using a
read-modify-write against the latest body.  Failure leaves the body untouched.
"""
from __future__ import annotations

import re
from typing import Any


MARKER_START = "<!-- CBM:START -->"
MARKER_END = "<!-- CBM:END -->"
P2_04_PHRASE = "declared as attached but not uploaded"


def _text(value: Any, *, fallback: str = "not available") -> str:
    if value is None:
        return fallback
    text = str(value).replace("`", "'").replace("\r", " ").replace("\n", " ").strip()
    return text or fallback


def _hash(value: Any) -> str:
    return _text(value, fallback="not available")


def _declared(report: dict[str, Any]) -> bool:
    return report.get("declared_attached") is True


def render_not_uploaded(report: dict[str, Any]) -> str:
    declared = _declared(report)
    lines = [
        "## NOT_UPLOADED",
        "",
        "- CBM: NOT_UPLOADED",
        f"  - cbm_gate_status: `{_text(report.get('cbm_gate_status'))}`",
        "  - upload_status: `NOT_UPLOADED`",
        f"  - reason: `{_text(report.get('reason'))}`",
        f"  - declared_attached: `{str(declared).lower()}`",
        f"  - cbe_report_hash: `{_hash(report.get('cbe_report_hash'))}`",
        f"  - cbp_report_hash: `{_hash(report.get('cbp_report_hash'))}`",
        f"  - cbp_release_body_hash: `{_hash(report.get('cbp_release_body_hash'))}`",
        f"  - cbp_body_hash_scope: `{_text(report.get('cbp_body_hash_scope'))}`",
        "- Skip accounting: `NOT_UPLOADED` is not counted in the SKIP ratio (F6).",
    ]
    if declared:
        lines += [
            "- Publish impact: `NOT_UPLOADED` does not block the CBS main package by itself (F6).",
            "",
            "CBM is declared as attached in this release train but was not uploaded:",
            f"{P2_04_PHRASE}（声明附带但未上传）。",
        ]
    else:
        lines += [
            "- Publish impact: CBM is not claimed by this release train; the CBS main package is unaffected (F6).",
        ]
    detail = report.get("reason_detail")
    if detail:
        lines += ["", f"> {_text(detail)}"]
    return "\n".join(lines) + "\n"


def render_infra(report: dict[str, Any]) -> str:
    declared = _declared(report)
    lines = [
        "## Infrastructure failures",
        "",
        "- CBM: NOT_UPLOADED",
        f"  - cbm_gate_status: `{_text(report.get('cbm_gate_status'))}`",
        "  - upload_status: `NOT_UPLOADED`",
        f"  - reason: `{_text(report.get('reason'))}`",
        f"  - cbe_report_hash: `{_hash(report.get('cbe_report_hash'))}`",
        f"  - cbp_report_hash: `{_hash(report.get('cbp_report_hash'))}`",
        f"  - cbp_release_body_hash: `{_hash(report.get('cbp_release_body_hash'))}`",
        f"  - cbp_body_hash_scope: `{_text(report.get('cbp_body_hash_scope'))}`",
        "- Skip accounting: `SKIPPED_INFRA` is not counted in the SKIP ratio (F5).",
        "- Publish impact: CBM upload is blocked; the CBS main package is not blocked by CBM (F6).",
    ]
    detail = report.get("reason_detail")
    if detail:
        lines += ["", f"> {_text(detail)}"]
    if declared:
        lines += [
            "",
            "CBM is declared as attached in this release train but was not uploaded:",
            f"{P2_04_PHRASE}（声明附带但未上传）。",
        ]
    return "\n".join(lines) + "\n"


def render_unverified(report: dict[str, Any]) -> str:
    lines = [
        "## Upload verification failures",
        "",
        "- CBM: UPLOADED_UNVERIFIED",
        f"  - cbm_gate_status: `{_text(report.get('cbm_gate_status'))}`",
        "  - upload_status: `UPLOADED_UNVERIFIED`",
        f"  - reason: `{_text(report.get('reason'))}`",
        f"  - asset: `{_text(report.get('artifact_name'))}`",
        f"  - artifact_sha256: `{_hash(report.get('artifact_sha256'))}`",
        f"  - uploaded_asset_digest: `{_hash(report.get('uploaded_asset_digest'))}`",
        f"  - cbe_report_hash: `{_hash(report.get('cbe_report_hash'))}`",
        f"  - cbp_report_hash: `{_hash(report.get('cbp_report_hash'))}`",
        f"  - cbp_release_body_hash: `{_hash(report.get('cbp_release_body_hash'))}`",
        f"  - cbp_body_hash_scope: `{_text(report.get('cbp_body_hash_scope'))}`",
        "",
        "This asset must not be treated as PASS.  Re-run the upload or regenerate the release asset.",
    ]
    detail = report.get("reason_detail")
    if detail:
        lines += ["", f"> {_text(detail)}"]
    return "\n".join(lines) + "\n"


def render_uploaded(report: dict[str, Any]) -> str:
    lines = [
        "## Optional component attachments",
        "",
        "- CBM: UPLOADED_VERIFIED",
        "  - cbm_gate_status: `PASS`",
        "  - upload_status: `UPLOADED_VERIFIED`",
        f"  - asset: `{_text(report.get('artifact_name'))}`",
        f"  - artifact_sha256: `{_hash(report.get('artifact_sha256'))}`",
        f"  - uploaded_asset_digest: `{_hash(report.get('uploaded_asset_digest'))}`",
        f"  - cbe_report_hash: `{_hash(report.get('cbe_report_hash'))}`",
        f"  - cbp_report_hash: `{_hash(report.get('cbp_report_hash'))}`",
        f"  - cbp_release_body_hash: `{_hash(report.get('cbp_release_body_hash'))}`",
        f"  - cbp_body_hash_scope: `{_text(report.get('cbp_body_hash_scope'))}`",
    ]
    url = report.get("uploaded_asset_url")
    if url:
        lines.append(f"  - uploaded_asset_url: {_text(url)}")
    return "\n".join(lines) + "\n"


def render(report: dict[str, Any]) -> str:
    """Render the body section for this report, without markers."""
    status = report.get("upload_status")
    if status == "UPLOADED_VERIFIED":
        return render_uploaded(report)
    if status == "UPLOADED_UNVERIFIED":
        return render_unverified(report)
    if report.get("cbm_gate_status") == "SKIPPED_INFRA":
        return render_infra(report)
    return render_not_uploaded(report)


def wrap_marker(text: str) -> str:
    return f"{MARKER_START}\n{text.rstrip()}\n{MARKER_END}\n"


def render_marked(report: dict[str, Any]) -> str:
    return wrap_marker(render(report))


def replace_marker_block(existing: str, block: str) -> str | None:
    """Replace exactly one marker block.  Return None when markers are absent.

    The caller must not append a second section by guesswork.  A missing marker
    means the CBS body generator did not reserve the block; regenerate the body
    instead of risking duplicate or stale evidence.
    """
    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        re.DOTALL,
    )
    if not pattern.search(existing):
        return None
    return pattern.sub(lambda _match: wrap_marker(block).rstrip(), existing, count=1)
