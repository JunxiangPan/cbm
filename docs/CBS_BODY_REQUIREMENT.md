# CBS body generator requirement: CBM evidence absence must be visible

Status: **v1.7 release-train hard blocker (B5)**. CBM cannot implement this in
its own repository; this document records the exact gap and the minimum
expected behavior.

## Why this exists

CBM can fail before it writes any evidence: a runner/checkout outage, a GitHub
API outage, or the CBM workflow never being dispatched. If the CBS Release body
then omits CBM entirely, the failure is not fail-closed; it is fail-silent. F6
requires `NOT_UPLOADED` to be visible in the body.

## Audited state (2026-11-08, CBS HEAD `dab2c53`)

- `public-release/tools/release_body_v17.py` reads
  `not_uploaded = report.get("not_uploaded", [])` (line 20).
- It renders `- none` when that list is empty:
  `lines += [f"- {item}" for item in not_uploaded] or ["- none"]` (line 39).
- `public-release/.github/workflows/reusable-v17-release.yml` has no CBM job and
  uploads only `v17-mock-artifact`.
- Therefore a missing CBM report currently produces `## NOT_UPLOADED` with
  `- none`. CBM is invisible; this is the fail-silent case.

## Required behavior

If no CBM report/evidence is available to the body generator, it must synthesize
one visible entry (not a PASS, not `- none`):

```markdown
## NOT_UPLOADED

- CBM: NOT_UPLOADED
  - cbm_gate_status: `NOT_UPLOADED`
  - upload_status: `NOT_UPLOADED`
  - reason: `EVIDENCE_ABSENT`
  - declared_attached: `true` | `false`
- Skip accounting: NOT_UPLOADED is not counted in the SKIP ratio (F6).
- Publish impact: CBM NOT_UPLOADED does not block the CBS main package by itself (F6).
```

If the release train declares CBM attached, the body must also contain the exact
phrase:

```text
declared as attached but not uploaded
```

If a CBM report **is** present, the generator must use its `upload_status`,
`cbm_gate_status`, `reason`, and hashes instead of the default. A report that
says `UPLOADED_VERIFIED` must not be downgraded to `NOT_UPLOADED`; a report that
says `NOT_UPLOADED` must not become PASS.

## Proposed CBS change (for the CBS owner, not applied by CBM)

Make the `not_uploaded` input structured and add a default only when CBM is
absent:

```python
def _with_cbm_default(report: dict, *, declared_attached: bool) -> list[dict]:
    items = [item for item in report.get("not_uploaded", []) if isinstance(item, dict)]
    if not any(str(item.get("component", "")).lower() == "cbm" for item in items):
        items.append(
            {
                "component": "cbm",
                "cbm_gate_status": "NOT_UPLOADED",
                "upload_status": "NOT_UPLOADED",
                "reason": "EVIDENCE_ABSENT",
                "declared_attached": declared_attached,
            }
        )
    return items
```

The renderer must then emit the exact phrase when `declared_attached` is true.

## Proposed CBS test

```python
def test_missing_cbm_report_is_not_silent(tmp_path):
    text = build(
        {
            "version": "v1.7.0",
            "gate_status": "PASS",
            "not_uploaded": [],
            "declared_components": ["cbm"],
        },
        wheel,
    )
    assert "CBM: NOT_UPLOADED" in text
    assert "EVIDENCE_ABSENT" in text
    assert "declared as attached but not uploaded" in text
```

## CBM-side evidence (what CBM can prove)

When `cbm_attach finalize` runs but finds no evidence artifact, it writes a
visible report/fragment:

- `cbm_gate_status = SKIPPED_INFRA`
- `reason = EVIDENCE_ABSENT`
- `reason_detail` contains `WORKFLOW_FAILED_BEFORE_EVIDENCE`
- `upload_status = NOT_UPLOADED`
- body includes `CBM: NOT_UPLOADED` and the exact phrase if claimed

This covers "CBM ran but lost its evidence". It does **not** cover "CBM never
ran"; only the CBS body generator can cover that case.

The canary test `tests/test_known_fail_silent.py` proves the current CBS output
is `- none` with no CBM entry; it loads the real CBS `release_body_v17.py` when
available, otherwise a mock that reproduces the audited lines. It is marked
`KNOWN_FAIL_SILENT` and must be flipped when CBS implements this document.
