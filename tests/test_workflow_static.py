"""Static audit of the reusable workflow: no hiding, no rebuild, no clobber."""
from __future__ import annotations

import re
from pathlib import Path

import yaml


WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "cbm-attach.yml"
TEXT = WORKFLOW.read_text(encoding="utf-8")


def _load():
    return yaml.load(TEXT, Loader=yaml.BaseLoader)


def _uses(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "uses":
                yield value
            else:
                yield from _uses(value)
    elif isinstance(node, list):
        for item in node:
            yield from _uses(item)


def test_workflow_is_parseable_and_has_only_three_jobs() -> None:
    data = _load()
    assert set(data["jobs"]) == {"verify", "upload", "finalize"}
    assert "publish" not in data["jobs"]


def test_upload_requires_explicit_verify_decision() -> None:
    data = _load()
    assert data["jobs"]["upload"]["if"] == (
        "needs.verify.result == 'success' && needs.verify.outputs.decision == 'UPLOAD'"
    )


def test_finalize_runs_after_failure_but_not_on_cancel() -> None:
    data = _load()
    jobs = data["jobs"]
    assert jobs["finalize"]["needs"] == ["verify", "upload"]
    assert "!cancelled()" in jobs["finalize"]["if"]


def test_verify_artifact_step_runs_on_failure() -> None:
    data = _load()
    verify_steps = data["jobs"]["verify"]["steps"]
    artifact_steps = [
        step for step in verify_steps if step.get("uses", "").startswith("actions/upload-artifact")
    ]
    assert len(artifact_steps) == 1
    assert "!cancelled()" in artifact_steps[0]["if"]


def test_every_workflow_call_input_is_optional() -> None:
    data = _load()
    inputs = data["on"]["workflow_call"]["inputs"]
    assert inputs
    assert all(value.get("required") == "false" for value in inputs.values())


def test_secrets_are_optional_and_scoped() -> None:
    data = _load()
    secrets = data["on"]["workflow_call"]["secrets"]
    assert set(secrets) == {"artifact_token", "release_token"}
    assert all(value.get("required") == "false" for value in secrets.values())


def test_no_error_hiding_constructs() -> None:
    forbidden = [
        "continue-on-error",
        "|| true",
        "|| exit 0",
        "--clobber",
        "--skip-existing",
        "always()",
    ]
    for token in forbidden:
        assert token not in TEXT, token


def test_no_rebuild_commands() -> None:
    forbidden = [
        "python -m build",
        "pip wheel",
        "python setup.py",
        "npm run build",
        "pnpm build",
        "cargo build",
        "go build",
    ]
    for token in forbidden:
        assert token not in TEXT, token


def test_all_actions_are_sha_pinned() -> None:
    data = _load()
    uses = [value for value in _uses(data) if not str(value).startswith("./")]
    assert uses
    for value in uses:
        assert re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", value), value


def test_permissions_are_least_privilege() -> None:
    data = _load()
    assert data["permissions"]["contents"] == "read"
    assert data["permissions"]["actions"] == "read"
    assert data["jobs"]["upload"]["permissions"]["contents"] == "write"


def test_finalize_recovers_evidence_even_when_no_artifact_exists() -> None:
    data = _load()
    steps = data["jobs"]["finalize"]["steps"]
    assert steps[0]["uses"].startswith("actions/checkout")
    run_text = "\n".join(step.get("run", "") for step in steps)
    assert "actions/runs/${GITHUB_RUN_ID}/artifacts?per_page=100" in run_text
    assert 'startswith("cbm-evidence")' in run_text
    assert "CBM_EVIDENCE_ABSENT" in run_text


def test_no_manual_release_body_edit_step() -> None:
    forbidden = [
        "gh release edit",
        "gh release upload",
    ]
    for token in forbidden:
        assert token not in TEXT, token
